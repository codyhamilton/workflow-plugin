#!/usr/bin/env python3
"""Definition checks and dry-run replay. Not a scientific result."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
import urllib.error
from pathlib import Path

PROOFS = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOFS))

from replay_progressive_gates import (  # noqa: E402
    DEFAULT_CORPUS,
    build_corpus_manifest,
    replay_transcript,
)
from session_checkout import (  # noqa: E402
    apply_rule,
    build_jev_request,
    outcome_vs_gold,
    session_checkout_questions,
)
from snapshot_state import (  # noqa: E402
    STATE_CHAR_LIMIT,
    StateOverBudget,
    prepare_hybrid_state,
    shrink_gold_bundle,
    shrink_hybrid_state,
    state_json_len,
)
from synthetic_fixture import write_synthetic  # noqa: E402
from turn_index import checkpoints, index_rows, index_transcript  # noqa: E402

SYNTHETIC = PROOFS / "fixtures" / "synthetic_worker_90.jsonl"
MAPS_MANIFEST = DEFAULT_CORPUS / "manifest.json"


class ScheduleTests(unittest.TestCase):
    def test_published_lengths(self) -> None:
        turns_296 = checkpoints(75, 15, 296)
        self.assertEqual(len(turns_296), 15)
        self.assertEqual(turns_296[0], 75)
        self.assertEqual(turns_296[-1], 285)
        self.assertEqual(turns_296, list(range(75, 286, 15)))
        self.assertEqual(checkpoints(75, 15, 154), [75, 90, 105, 120, 135, 150])
        self.assertEqual(checkpoints(75, 15, 70), [])

    def test_overshoot_signs(self) -> None:
        imagined = [
            (296, 105, 105, 0, False, False, 105),
            (296, 105, 285, 180, False, True, 285),
            (296, 105, None, None, False, True, 296),
            (296, None, 75, None, True, False, 75),
            (154, 150, 135, -15, True, False, 135),
        ]
        for T, gold, gate, overshoot, early, late, allowed in imagined:
            got = outcome_vs_gold(T=T, gate_exit=gate, gold_exit=gold)
            self.assertEqual(got["overshoot"], overshoot)
            self.assertEqual(got["false_early"], early)
            self.assertEqual(got["false_late"], late)
            self.assertEqual(got["max_allowed_turns"], allowed)


class RuleTests(unittest.TestCase):
    def test_confidence_three_fires_two_does_not(self) -> None:
        high = apply_rule(choice="checkout", confidence=3, confidence_min=3)
        low = apply_rule(choice="checkout", confidence=2, confidence_min=3)
        self.assertTrue(high["fires"])
        self.assertEqual(high["decision"], "checkout")
        self.assertFalse(low["fires"])
        self.assertEqual(low["decision"], "checkout")

    def test_inconclusive_and_missing_stay_open(self) -> None:
        inconclusive = apply_rule(choice="inconclusive", confidence=3, on_uncertain="open")
        missing = apply_rule(choice=None, confidence=None, missing=True, on_uncertain="open")
        self.assertFalse(inconclusive["fires"])
        self.assertFalse(missing["fires"])
        self.assertEqual(missing["decision"], "missing")
        self.assertNotEqual(missing["decision"], "continue")

    def test_state_guard_rejects_12001_before_request(self) -> None:
        probe = {"blob": "a"}
        overhead = state_json_len(probe) - 1
        state = {"blob": "a" * (12_001 - overhead)}
        self.assertEqual(state_json_len(state), 12_001)
        with self.assertRaises(StateOverBudget):
            build_jev_request(state)


class IndexTests(unittest.TestCase):
    def test_duplicate_message_id_counts_once(self) -> None:
        rows = [
            {
                "type": "assistant",
                "isSidechain": True,
                "message": {"id": "m1", "content": [{"type": "text", "text": "a"}]},
            },
            {
                "type": "assistant",
                "isSidechain": True,
                "message": {"id": "m1", "content": [{"type": "text", "text": "b"}]},
            },
            {
                "type": "assistant",
                "isSidechain": True,
                "message": {"id": "m2", "content": [{"type": "tool_use", "name": "Read", "id": "t", "input": {"file_path": "a.py"}}]},
            },
        ]
        indexed = index_rows(rows, worker_id="sub")
        self.assertEqual(indexed.sidechain_mode, "subagent_file")
        self.assertEqual(indexed.T, 2)
        self.assertEqual(indexed.turns[0].text, "a\nb")

    def test_parent_file_drops_sidechain(self) -> None:
        rows = [
            {"type": "assistant", "isSidechain": False, "message": {"id": "main", "content": [{"type": "text", "text": "main"}]}},
            {"type": "assistant", "isSidechain": True, "message": {"id": "side", "content": [{"type": "text", "text": "side"}]}},
        ]
        indexed = index_rows(rows)
        self.assertEqual(indexed.sidechain_mode, "parent_exclude_sidechain")
        self.assertEqual(indexed.T, 1)
        self.assertEqual(indexed.turns[0].text, "main")

    def test_prefix_stops_before_next_turn(self) -> None:
        rows = [
            {"type": "user", "message": {"content": [{"type": "text", "text": "brief"}]}},
            {"type": "assistant", "message": {"id": "a", "content": [{"type": "text", "text": "one"}]}},
            {"type": "user", "message": {"content": [{"type": "text", "text": "between"}]}},
            {"type": "assistant", "message": {"id": "b", "content": [{"type": "text", "text": "two"}]}},
            {"type": "user", "message": {"content": [{"type": "text", "text": "after"}]}},
        ]
        indexed = index_rows(rows)
        indexes = indexed.prefix_indexes(1)
        texts = []
        for index in indexes:
            message = indexed.rows[index].get("message") or {}
            content = message.get("content")
            if isinstance(content, list):
                texts.extend(block.get("text") for block in content if isinstance(block, dict))
        self.assertIn("brief", texts)
        self.assertIn("one", texts)
        self.assertIn("between", texts)
        self.assertNotIn("two", texts)
        self.assertNotIn("after", texts)


class ShrinkTests(unittest.TestCase):
    def test_drop_tail_until_it_fits(self) -> None:
        tail = [{"turn": n, "excerpt": "x" * 2500, "tool_names": ["Read"]} for n in range(1, 9)]
        state = {
            "question_id": "session-checkout",
            "tail": tail,
            "cumulative": {"reread_paths": []},
            "delta_since_prior": {},
        }
        self.assertGreater(state_json_len(state), STATE_CHAR_LIMIT)
        shrunk, steps = shrink_hybrid_state(state)
        self.assertIsNotNone(shrunk)
        assert shrunk is not None
        self.assertLessEqual(state_json_len(shrunk), STATE_CHAR_LIMIT)
        self.assertLessEqual(len(shrunk["tail"]), 4)
        self.assertTrue(steps)
        self.assertNotIn("state_over_budget", steps)

    def test_unshrinkable_is_missing(self) -> None:
        state = {
            "tail": [],
            "cumulative": {"reread_paths": []},
            "delta_since_prior": {},
            "pad": "p" * 13_000,
        }
        shrunk, steps = shrink_hybrid_state(state)
        self.assertIsNone(shrunk)
        self.assertIn("state_over_budget", steps)

    def test_gold_bundle_can_be_unlabelable(self) -> None:
        bundle = {"brief_anchor": "x", "tail": [], "pad": "p" * 70_000}
        shrunk, steps = shrink_gold_bundle(bundle)
        self.assertIsNone(shrunk)
        self.assertIn("unlabelable", steps)


class SyntheticReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        write_synthetic(SYNTHETIC, turns=90)

    def test_dry_run_schedule_and_redaction(self) -> None:
        def boom(request: dict, key: str) -> dict:
            raise AssertionError("dry-run posted")

        result = replay_transcript(
            SYNTHETIC,
            first_at=75,
            interval=15,
            dry_run=True,
            call_jev=False,
            gold_exit=None,
            gold_exit_provided=False,
            poster=boom,
        )
        metrics = result["metrics"]
        self.assertEqual(metrics["T"], 90)
        self.assertEqual(metrics["checkpoints"], [75, 90])
        self.assertIsNone(metrics["first_checkout_turn"])
        self.assertEqual(metrics["max_allowed_turns"], 90)
        self.assertEqual(metrics["worker_policy"], "continue")
        self.assertEqual(metrics["peak_ctx_tokens"], 9000)
        self.assertEqual(metrics["schema_budget_p0"]["n_over_budget"], 0)
        for row in result["rows"]:
            self.assertLessEqual(row["state_chars"], STATE_CHAR_LIMIT)
            self.assertEqual(row["decision"], "missing")
            self.assertNotEqual(row["decision"], "continue")
            self.assertFalse(row["fires"])
            self.assertIsNone(row["answers"])
            self.assertLess(row["request_chars"], 16_000)
        first = result["rows"][0]["state"]
        self.assertEqual(first["checkpoint_turn"], 75)
        self.assertEqual(first["cumulative"]["api_turns"], 75)
        self.assertEqual(first["cumulative"]["peak_ctx_tokens"], 7500)
        self.assertGreaterEqual(first["cumulative"]["compaction_event_count"], 1)
        self.assertNotIn("supersecret", first["brief_anchor"])
        self.assertIn("[REDACTED]", first["brief_anchor"])
        rereads = {entry["path"]: entry["count"] for entry in first["cumulative"]["reread_paths"]}
        self.assertGreaterEqual(rereads.get("src/repeat.py", 0), 3)
        turn_75 = next(item for item in first["tail"] if item["turn"] == 75)
        self.assertNotIn("supersecret", turn_75["excerpt"])
        self.assertIn("Read", turn_75["tool_names"])
        indexed = index_transcript(SYNTHETIC)
        self.assertIn("continued", indexed.turns[0].text)

    def test_cli_dry_run(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(PROOFS / "replay_progressive_gates.py"),
                "--transcript",
                str(SYNTHETIC),
                "--schedule",
                "75:15",
                "--dry-run",
            ],
            cwd=str(PROOFS),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        rows = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual([row["checkpoint_turn"] for row in rows], [75, 90])
        metrics = json.loads(proc.stderr)
        self.assertEqual(metrics["workers"][0]["max_allowed_turns"], 90)
        self.assertIsNone(metrics["workers"][0]["first_checkout_turn"])

    def test_fail_open_only_confidence_three_checks_out(self) -> None:
        def answer(confidence: int):
            def poster(request: dict, key: str) -> dict:
                self.assertEqual(request["model"], "jev-1.13.0")
                self.assertIn("checkout_now", request["questions"])
                return {
                    "answers": {
                        "checkout_now": "checkout",
                        "checkout_confidence": confidence,
                        "runaway_pattern": 0,
                        "progress_since_prior": 3,
                        "scope_drift": 1,
                    }
                }

            return poster

        stopped = replay_transcript(
            SYNTHETIC,
            first_at=75,
            interval=15,
            dry_run=False,
            call_jev=True,
            gold_exit=90,
            gold_exit_provided=True,
            api_key="test-key",
            poster=answer(3),
        )
        self.assertEqual(stopped["metrics"]["first_checkout_turn"], 75)
        self.assertEqual(stopped["metrics"]["max_allowed_turns"], 75)
        self.assertEqual(stopped["metrics"]["worker_policy"], "checkout")
        self.assertEqual(stopped["metrics"]["overshoot"], -15)
        self.assertTrue(stopped["rows"][0]["ungrounded_choice"])

        continued = replay_transcript(
            SYNTHETIC,
            first_at=75,
            interval=15,
            dry_run=False,
            call_jev=True,
            gold_exit=None,
            gold_exit_provided=False,
            api_key="test-key",
            poster=answer(2),
        )
        self.assertFalse(continued["rows"][0]["fires"])
        self.assertEqual(continued["rows"][0]["decision"], "checkout")
        self.assertEqual(continued["metrics"]["worker_policy"], "continue")
        self.assertEqual(continued["metrics"]["max_allowed_turns"], 90)

    def test_api_error_is_missing_not_continue(self) -> None:
        def poster(request: dict, key: str) -> dict:
            raise urllib.error.URLError("offline")

        result = replay_transcript(
            SYNTHETIC,
            first_at=75,
            interval=15,
            dry_run=False,
            call_jev=True,
            gold_exit=None,
            gold_exit_provided=False,
            api_key="test-key",
            poster=poster,
        )
        self.assertEqual(result["rows"][0]["decision"], "missing")
        self.assertEqual(result["rows"][0]["reason"], "api_error")
        self.assertFalse(result["rows"][0]["fires"])
        self.assertEqual(result["metrics"]["worker_policy"], "continue")

    def test_question_sets(self) -> None:
        full = session_checkout_questions("Y_full")
        self.assertEqual(
            list(full),
            [
                "runaway_pattern",
                "progress_since_prior",
                "scope_drift",
                "checkout_now",
                "checkout_confidence",
            ],
        )
        legacy = session_checkout_questions("Y_legacy")
        self.assertEqual(set(legacy), {"progress_vs_scope", "handoff_recommended"})


class MapsCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        if not DEFAULT_CORPUS.is_dir():
            self.skipTest("maps-5h-workers fixtures are not on this checkout")

    def test_manifest_matches_published_counts(self) -> None:
        published = json.loads(MAPS_MANIFEST.read_text(encoding="utf-8"))
        manifest = build_corpus_manifest(DEFAULT_CORPUS)
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["priority_mismatch"], [])
        self.assertEqual(manifest["priority_found"], {"92a48e004519": True, "bb6165018de0": True})
        self.assertGreaterEqual(manifest["n_workers_ge_75"], 2)
        by_id = {row["worker_id"]: row for row in manifest["workers"]}
        by_id.update({row["worker_id"]: row for row in manifest["negative_control"]})
        by_id.update({row["worker_id"]: row for row in manifest["excluded_under_75"]})
        for expected in published["workers"]:
            got = by_id[expected["short_id"]]
            self.assertEqual(got["T"], expected["api_turns"], msg=expected["short_id"])
            self.assertEqual(got["peak_ctx_tokens"], expected["peak_ctx"], msg=expected["short_id"])
            self.assertEqual(got["sidechain_mode"], "subagent_file")

    def test_dry_replay_smoking_guns_and_control(self) -> None:
        smoking = replay_transcript(
            DEFAULT_CORPUS / "92a48e004519.jsonl",
            first_at=75,
            interval=15,
            dry_run=True,
            call_jev=False,
            gold_exit=None,
            gold_exit_provided=False,
        )
        self.assertEqual(smoking["metrics"]["T"], 296)
        self.assertEqual(len(smoking["metrics"]["checkpoints"]), 15)
        self.assertEqual(smoking["metrics"]["max_allowed_turns"], 296)
        self.assertIsNone(smoking["metrics"]["first_checkout_turn"])
        for row in smoking["rows"]:
            self.assertLessEqual(row["state_chars"], STATE_CHAR_LIMIT)
            self.assertEqual(row["decision"], "missing")
            self.assertIsNotNone(row["gold_bundle_chars"])
            self.assertLessEqual(row["gold_bundle_chars"], 60_000)

        second = replay_transcript(
            DEFAULT_CORPUS / "bb6165018de0.jsonl",
            first_at=75,
            interval=15,
            dry_run=True,
            call_jev=False,
            gold_exit=None,
            gold_exit_provided=False,
        )
        self.assertEqual(second["metrics"]["T"], 154)
        self.assertEqual(second["metrics"]["checkpoints"], [75, 90, 105, 120, 135, 150])

        control = replay_transcript(
            DEFAULT_CORPUS / "6c87c96bd9bb.jsonl",
            first_at=75,
            interval=15,
            dry_run=True,
            call_jev=False,
            gold_exit=None,
            gold_exit_provided=False,
        )
        self.assertEqual(control["metrics"]["T"], 70)
        self.assertEqual(control["metrics"]["checkpoints"], [])
        self.assertEqual(control["metrics"]["max_allowed_turns"], 70)
        self.assertEqual(control["rows"], [])

        indexed = index_transcript(DEFAULT_CORPUS / "92a48e004519.jsonl")
        state, steps = prepare_hybrid_state(
            indexed, 75, first_at=75, interval=15, prior=None
        )
        self.assertIsNotNone(state)
        assert state is not None
        self.assertLessEqual(state_json_len(state), STATE_CHAR_LIMIT)
        self.assertEqual(steps, [])


if __name__ == "__main__":
    unittest.main()
