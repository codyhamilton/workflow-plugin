#!/usr/bin/env python3
"""Gold bundle, aggregation, and score checks. Not a labeled corpus."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROOFS = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOFS))

from gold_panel import (  # noqa: E402
    aggregate_labels,
    explode_document,
    krippendorff_alpha,
    load_labels,
    score_replay,
)


def _vote(worker: str, turn: int, model: str, checkout: bool | None, guess: int | None = None) -> dict:
    return {
        "worker_id": worker,
        "checkpoint_turn": turn,
        "model": model,
        "checkout_recommended": checkout,
        "rationale": "prefix only",
        "first_checkout_turn_guess": guess,
    }


class AlphaTests(unittest.TestCase):
    def test_nominal_perfect_agreement_is_one(self) -> None:
        units = [["checkout", "checkout"], ["not_yet", "not_yet"], ["checkout", "checkout"]]
        self.assertEqual(krippendorff_alpha(units, level="nominal"), 1.0)

    def test_nominal_systematic_disagreement(self) -> None:
        units = [["checkout", "not_yet"], ["checkout", "not_yet"]]
        alpha = krippendorff_alpha(units, level="nominal")
        self.assertIsNotNone(alpha)
        assert alpha is not None
        self.assertAlmostEqual(alpha, -0.5)

    def test_single_category_is_undefined(self) -> None:
        self.assertIsNone(krippendorff_alpha([["not_yet", "not_yet"]], level="nominal"))

    def test_ordinal_perfect_agreement_is_one(self) -> None:
        self.assertEqual(krippendorff_alpha([[0, 0], [3, 3]], level="ordinal"), 1.0)


class AggregateTests(unittest.TestCase):
    def test_three_judges_wait_for_unanimity(self) -> None:
        labels = []
        for model, bits in {
            "grok": [False, False, True],
            "sonnet": [False, True, True],
            "opus": [False, True, True],
        }.items():
            for turn, bit in zip((75, 90, 105), bits):
                labels.append(_vote("gun", turn, model, bit, guess=75))
        summary = aggregate_labels(labels)
        row = summary["workers"][0]
        self.assertEqual(row["panel"], "powered")
        self.assertEqual(row["gold_exit"], 105)
        self.assertEqual(row["A1"], 90)
        self.assertTrue(row["primary"])
        self.assertNotEqual(row["gold_exit"], 75)
        self.assertGreaterEqual(summary["alpha"], 0.40)
        self.assertEqual(summary["h5"], "pass")
        self.assertEqual(summary["confidence"], "not-high")

    def test_two_judges_stay_diagnostic(self) -> None:
        labels = []
        for model in ("grok", "sonnet"):
            labels.append(_vote("gun", 75, model, False))
            labels.append(_vote("gun", 90, model, True))
        summary = aggregate_labels(labels)
        row = summary["workers"][0]
        self.assertEqual(row["panel"], "underpowered")
        self.assertIsNone(row["gold_exit"])
        self.assertEqual(row["gold_exit_unanimous_min2"], 90)
        self.assertFalse(row["primary"])
        self.assertIsNone(summary["h5_pass"])
        self.assertEqual(summary["h5"], "underpowered")

    def test_pending_null_is_not_a_vote(self) -> None:
        labels = [
            _vote("gun", 75, "grok", None),
            _vote("gun", 75, "sonnet", None),
            _vote("gun", 90, "opus", None),
        ]
        summary = aggregate_labels(labels)
        self.assertEqual(summary["status"], "pending")
        self.assertEqual(summary["n_labels_filled"], 0)
        self.assertIsNone(summary["workers"][0]["gold_exit"])
        self.assertIsNone(summary["workers"][0]["gold_exit_unanimous_min2"])
        self.assertIsNone(summary["alpha"])

    def test_checkout_without_pattern_is_dropped(self) -> None:
        bad = _vote("gun", 75, "grok", True)
        bad["patterns"] = []
        labels = [
            bad,
            _vote("gun", 75, "sonnet", False),
            _vote("gun", 75, "opus", False),
        ]
        summary = aggregate_labels(labels)
        self.assertEqual(summary["n_labels_invalid"], 1)
        self.assertEqual(summary["workers"][0]["n_judges"], 2)
        self.assertIsNone(summary["workers"][0]["gold_exit"])

    def test_chm_shapes(self) -> None:
        flat = _vote("gun", 75, "grok", False, guess=90)
        wrapped = {
            "worker_id": "gun",
            "checkpoint_turn": 75,
            "verdicts": [
                {
                    "model": "sonnet",
                    "checkout_recommended": False,
                    "rationale": "thin",
                    "first_checkout_turn_guess": None,
                }
            ],
        }
        grouped = {
            "worker_id": "gun",
            "T": 296,
            "models": {
                "opus": {
                    "first_checkout_turn_guess": 105,
                    "checkpoints": [
                        {"checkpoint_turn": 75, "checkout_recommended": False, "rationale": "early"},
                        {"checkpoint_turn": 105, "checkout_recommended": True, "rationale": "later"},
                    ],
                }
            },
        }
        terms = {
            "worker_id": "gun",
            "turn": 105,
            "judge": "grok",
            "answer": "checkout",
            "patterns": ["runaway"],
            "rationale": "repeat reads",
        }
        sonnet_later = _vote("gun", 105, "sonnet", True)
        labels = (
            explode_document(flat)
            + explode_document(wrapped)
            + explode_document(grouped)
            + explode_document([terms, sonnet_later])
        )
        self.assertEqual(len(labels), 6)
        summary = aggregate_labels(labels)
        row = summary["workers"][0]
        self.assertEqual(row["n_judges"], 3)
        self.assertEqual(row["gold_exit"], 105)
        self.assertEqual(row["T"], 296)


class ScoreTests(unittest.TestCase):
    def _gold(self, exit_turn: int | None, *, status: str = "established") -> dict:
        primary = status == "established"
        return {
            "workers": [
                {
                    "worker_id": "gun",
                    "T": 296,
                    "panel": "powered" if primary else status,
                    "gold_status": status,
                    "primary": primary,
                    "gold_exit": exit_turn,
                    "gold_exit_unanimous_min2": exit_turn,
                }
            ]
        }

    def test_terms_signs(self) -> None:
        rows = [
            {"worker_id": "gun", "checkpoint_turn": 105, "fires": True, "decision": "checkout"},
            {"worker_id": "gun", "checkpoint_turn": 120, "fires": True, "decision": "checkout"},
        ]
        scored = score_replay(rows, self._gold(105), metrics={"gun": {"T": 296, "interval": 15}})
        row = scored["workers"][0]
        self.assertTrue(row["scored"])
        self.assertEqual(row["overshoot"], 0)
        self.assertFalse(row["false_early"])
        self.assertFalse(row["false_late"])
        self.assertEqual(row["max_allowed_turns"], 105)

        late = score_replay(
            [{"worker_id": "gun", "checkpoint_turn": 75, "fires": False, "decision": "missing"}],
            self._gold(105),
            metrics={"gun": {"T": 296, "interval": 15}},
        )
        self.assertIsNone(late["workers"][0]["overshoot"])
        self.assertTrue(late["workers"][0]["false_late"])
        self.assertFalse(late["workers"][0]["false_early"])
        self.assertEqual(late["workers"][0]["max_allowed_turns"], 296)

        early = score_replay(
            [{"worker_id": "gun", "checkpoint_turn": 75, "fires": True, "decision": "checkout"}],
            self._gold(None),
            metrics={"gun": {"T": 296, "interval": 15}},
        )
        self.assertTrue(early["workers"][0]["false_early"])
        self.assertFalse(early["workers"][0]["false_late"])
        self.assertEqual(early["workers"][0]["max_allowed_turns"], 75)

    def test_pending_gold_does_not_score(self) -> None:
        rows = [{"worker_id": "gun", "checkpoint_turn": 75, "fires": False, "decision": "missing"}]
        scored = score_replay(rows, self._gold(None, status="pending"), metrics={"gun": {"T": 296, "interval": 15}})
        row = scored["workers"][0]
        self.assertFalse(row["scored"])
        self.assertIsNone(row["false_early"])
        self.assertIsNone(row["false_late"])
        self.assertIsNone(row["overshoot"])
        self.assertEqual(row["max_allowed_turns"], 296)
        self.assertEqual(scored["status"], "blocked_no_gold")

    def test_min2_exit_is_not_primary(self) -> None:
        gold = self._gold(90, status="underpowered")
        gold["workers"][0]["gold_exit"] = None
        gold["workers"][0]["gold_exit_unanimous_min2"] = 90
        scored = score_replay(
            [{"worker_id": "gun", "checkpoint_turn": 75, "fires": True, "decision": "checkout"}],
            gold,
            metrics={"gun": {"T": 296, "interval": 15}},
        )
        row = scored["workers"][0]
        self.assertFalse(row["scored"])
        self.assertIsNone(row["false_early"])
        self.assertEqual(row["diagnostic_gold_exit_min2"], 90)
        self.assertEqual(row["max_allowed_turns"], 75)


class CliTests(unittest.TestCase):
    def test_directory_of_chm_verdicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gun.json").write_text(
                json.dumps(
                    [
                        _vote("gun", 60, "grok", False),
                        _vote("gun", 60, "sonnet", False),
                        _vote("gun", 60, "opus", False),
                        _vote("gun", 75, "grok", True),
                        _vote("gun", 75, "sonnet", True),
                        _vote("gun", 75, "opus", True),
                    ]
                ),
                encoding="utf-8",
            )
            labels = load_labels(root)
            summary = aggregate_labels(labels)
            self.assertEqual(summary["workers"][0]["gold_exit"], 75)


class SignedSonnetJsonlTests(unittest.TestCase):
    """The committed P0 JSONL. Flash drafts do not vote. Gold exits stay null."""

    VERDICTS = PROOFS / "validated" / "gold" / "p0-checkout-verdicts-20261001.jsonl"

    def test_signed_sonnet_panel_has_null_gold_exit(self) -> None:
        if not self.VERDICTS.is_file():
            self.skipTest("P0 verdict JSONL is absent")
        labels = load_labels(self.VERDICTS)
        summary = aggregate_labels(labels)
        self.assertEqual(summary["n_labels_filled"], 21)
        self.assertEqual(summary["n_labels_draft"], 21)
        self.assertEqual(summary["draft_review"]["n_draft_checkout"], 20)
        self.assertEqual(summary["draft_review"]["n_corrected_to_not_yet"], 20)
        self.assertEqual(summary["draft_review"]["n_agree_not_yet"], 1)
        self.assertEqual(summary["draft_review"]["n_agree_checkout"], 0)
        seats = {row["seat"]: row["status"] for row in summary["seats"]}
        self.assertEqual(seats["claude-sonnet"], "filled")
        self.assertEqual(seats["grok-4.7-high"], "pending")
        self.assertEqual(seats["composer"], "pending")
        self.assertEqual(summary["h5"], "underpowered")
        self.assertIsNone(summary["h5_pass"])
        by_id = {row["worker_id"]: row for row in summary["workers"]}
        self.assertEqual(set(by_id), {"92a48e004519", "bb6165018de0"})
        for row in by_id.values():
            self.assertEqual(row["panel"], "underpowered")
            self.assertIsNone(row["gold_exit"])
            self.assertIsNone(row["gold_exit_unanimous_min2"])
            self.assertIsNone(row["a0_if_drafts_voted"])
            self.assertEqual(row["judges"], ["claude-sonnet-5-5"])
            self.assertIn("claude-sonnet-5-5", row["never_checkout"])
            self.assertFalse(row["primary"])

    def test_score_does_not_treat_null_as_an_exit(self) -> None:
        if not self.VERDICTS.is_file():
            self.skipTest("P0 verdict JSONL is absent")
        summary = aggregate_labels(load_labels(self.VERDICTS))
        replay = PROOFS / "validated" / "ubuntu-raw" / "92a48e004519-dry-run-checkpoints-20261001-194107.omit-state.jsonl"
        metrics_path = PROOFS / "validated" / "ubuntu-raw" / "92a48e004519-dry-run-metrics-20261001-194107.json"
        if not replay.is_file():
            self.skipTest("ubuntu-raw dry-run is absent")
        from gold_panel import load_metrics_T, load_replay_rows

        scored = score_replay(
            load_replay_rows([replay]),
            summary,
            metrics=load_metrics_T([metrics_path]),
        )
        row = next(item for item in scored["workers"] if item["worker_id"] == "92a48e004519")
        self.assertEqual(scored["status"], "blocked_no_gold")
        self.assertFalse(row["scored"])
        self.assertIsNone(row["gold_exit"])
        self.assertIsNone(row["false_early"])
        self.assertIsNone(row["false_late"])
        self.assertIsNone(row["overshoot"])
        self.assertEqual(row["max_allowed_turns"], 296)


if __name__ == "__main__":
    unittest.main()
