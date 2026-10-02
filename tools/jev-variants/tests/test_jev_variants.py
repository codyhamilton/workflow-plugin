import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jev_variants as jv  # noqa: E402

SIG = {"name": "tests-green", "claim": "latest test run passed after edits", "anchor": "tool output containing pass summary",
       "direction": "near_completion", "counterexamples": ["tests passed but user asked for more"],
       "zero_call_detector": "regex on last test command output", "requires_features": ["tool_output_text"]}
ST_OUT = {"source": "hook_events", "window": {"unit": "batches", "n": 5}, "user_prompts": "all",
          "tool_inputs": "names", "tool_outputs": "truncated", "truncate_chars": 300, "counters": ["turn_index"], "max_tokens": 2000}
ST_NOOUT = dict(ST_OUT, tool_outputs="none")
MK = {"signal": "", "polarity": "higher_means_present",
      "question": {"present": {"type": "score", "instructions": "Did the last test run pass?", "criteria": ["no", "unclear", "partly", "yes"]}}}


def put(root, kind, spec, **kw):
    vid = jv.variant_id(kind, spec)
    env = {"kind": kind, "id": vid, "parent": None, "author": "t", "round_proposed": "R1", "rationale": "r",
           "informed_by": ["s1"], "status": "active", "spec": spec}
    env.update(kw)
    d = root / jv.DIRS[kind]
    d.mkdir(exist_ok=True)
    (d / f"{vid}.json").write_text(json.dumps(env))
    return vid


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sig = put(self.root, "signal", SIG)
        self.st1 = put(self.root, "state", ST_OUT)
        self.st2 = put(self.root, "state", ST_NOOUT)
        self.mk = put(self.root, "marker", dict(MK, signal=self.sig))
        self.pn = put(self.root, "panel", {"name": "p1", "markers": [self.mk]})

    def tearDown(self):
        self.tmp.cleanup()

    def rnd(self, **kw):
        r = {"round": "R1", "stage": "A", "test_card": "c.md", "panels": [self.pn], "states": [self.st1, self.st2], "sessions": {"a": "dev", "b": "dev"}, "checkpoints": [60, 75],
             "max_calls": 100, "max_cost_usd": 5, "est_cost_per_call_usd": 0.01, "learned_from": []}
        r.update(kw)
        return r

    def test_registry_valid(self):
        self.assertEqual(jv.validate_registry(self.root), [])

    def test_edited_spec_must_change_id(self):
        f = self.root / "states" / f"{self.st1}.json"
        d = json.loads(f.read_text())
        d["spec"]["max_tokens"] = 9
        f.write_text(json.dumps(d))
        self.assertTrue(any("content hash" in e for e in jv.validate_registry(self.root)))

    def test_missing_counterexample_rejected(self):
        self.assertTrue(jv.validate_spec("signal", dict(SIG, counterexamples=[])))

    def test_bad_jev_question_rejected(self):
        bad = dict(MK, signal="x", question={"q": {"type": "score", "instructions": "i", "criteria": {"a": "b"}}})
        self.assertTrue(jv.validate_spec("marker", bad))

    def test_hook_state_without_assistant_text(self):
        self.assertTrue(jv.validate_spec("state", dict(ST_OUT, assistant_text="full")))

    def test_expand_skips_incompatible_state(self):
        res = jv.expand(self.rnd(), jv.load_registry(self.root), set())
        self.assertEqual(res["to_run"], 1 * 2 * 2)  # only st1 has outputs; 2 sessions x 2 checkpoints
        self.assertEqual(res["markers_dropped_incompatible"], 2)  # st2 x 2 sessions

    def test_panel_one_marker_per_signal_and_known_markers(self):
        mk2 = put(self.root, "marker", dict(MK, signal=self.sig, question={"present": {"type": "score", "instructions": "Zero failures reported?", "criteria": ["no", "yes"]}}))
        put(self.root, "panel", {"name": "dup", "markers": [self.mk, mk2]})
        self.assertTrue(any("at most one marker per signal" in e for e in jv.validate_registry(self.root)))
        self.assertTrue(jv.validate_spec("panel", {"name": "x", "markers": []}))

    def test_corpus_harness_gates_features(self):
        corpus = {"a": {"harness": "cursor", "split": "dev"}, "b": {"harness": "claude", "split": "dev"}}
        res = jv.expand(self.rnd(), jv.load_registry(self.root), set(), corpus)
        self.assertEqual(res["to_run"], 1 * 1 * 2)  # st1 on claude session b only
        self.assertEqual({c["session"] for c in res["cells"]}, {"b"})

    def test_resume_skips_done(self):
        reg = jv.load_registry(self.root)
        first = jv.expand(self.rnd(), reg, set())["cells"]
        res = jv.expand(self.rnd(), reg, {first[0]["cell_id"]})
        self.assertEqual(res["to_run"], 3)

    def test_budget_blocks_cells(self):
        res = jv.expand(self.rnd(max_calls=2), jv.load_registry(self.root), set())
        self.assertTrue(res["over_budget"])
        self.assertEqual(res["cells"], [])

    def test_session_checkpoints_and_hide_flag(self):
        reg = jv.load_registry(self.root)
        rnd = self.rnd(states=[self.st1], session_checkpoints={"a": [3, 9], "b": [4]}, hide_next_prompt=True)
        cells = jv.expand(rnd, reg, set())["cells"]
        self.assertEqual(sorted((c["session"], c["checkpoint"]) for c in cells), [("a", 3), ("a", 9), ("b", 4)])
        self.assertTrue(all(c["hide_next_prompt"] for c in cells))
        plain = jv.expand(self.rnd(states=[self.st1]), reg, set())["cells"]
        self.assertTrue(all("hide_next_prompt" not in c for c in plain))

    def test_heldout_sealed(self):
        reg = jv.load_registry(self.root)
        errs = jv.validate_round(self.rnd(sessions={"a": "heldout"}), reg)
        self.assertTrue(any("sealed" in e for e in errs))
        self.assertEqual(jv.validate_round(self.rnd(sessions={"a": "heldout"}, allow_heldout=True), reg), [])

    def test_digest_counts_sessions_not_calls(self):
        rows = [{"signal": "s", "state": "t", "marker": "m", "session": "a", "parse_ok": True, "cost_usd": 0.01,
                 "state_tokens": 100, "label": True, "score": 0.9} for _ in range(3)]
        d = jv.digest(rows)["signal"]["s"]
        self.assertEqual((d["cells"], d["sessions"], d["label_agreement_at_0.5"]), (3, 1, 1.0))

    def test_examples_are_valid(self):
        for kind in ("signal", "state"):
            self.assertEqual(jv.validate_spec(kind, jv.EXAMPLES[kind]), [], kind)
        self.assertEqual(jv.validate_spec("marker", dict(jv.EXAMPLES["marker"], signal=self.sig)), [])

    def test_near_duplicate_marker_rejected(self):
        reg = jv.load_registry(self.root)
        para = json.loads(json.dumps(dict(MK, signal=self.sig)))
        para["question"]["present"]["instructions"] = "Did the last test run pass?!"
        self.assertEqual(jv.near_duplicate("marker", para, reg), self.mk)
        other = json.loads(json.dumps(para))
        other["question"]["present"]["instructions"] = "Quote the line proving the build output reported zero failures"
        self.assertIsNone(jv.near_duplicate("marker", other, reg))

    def test_brief_is_self_contained(self):
        out = jv.brief("marker-writer", self.root, 3, [], self.sig, "flash", "R2")
        for needle in ("jev_variants.py new marker", self.sig, "max 3 tries", "Existing marker"):
            self.assertIn(needle, out)

    def test_provenance_rejects_invented_session_ids(self):
        reg = jv.load_registry(self.root)
        errs = jv.check_provenance("state", self.root, ["ses_abc"], self.st1, reg)
        self.assertTrue(any("not a registry id" in e for e in errs))
        self.assertEqual(jv.check_provenance("state", self.root, [self.st1], self.st1, reg), [])

    def test_parent_required_when_peers_exist(self):
        reg = jv.load_registry(self.root)
        self.assertTrue(any("--parent" in e for e in jv.check_provenance("state", self.root, [self.st1], None, reg)))
        self.assertTrue(any("--parent" in e for e in jv.check_provenance("marker", self.root, [self.sig], None, reg, self.sig)))
        self.assertEqual(jv.check_provenance("marker", self.root, [self.sig], None, reg, "sig-other"), [])

    def test_signal_must_cite_listed_discovery_session(self):
        (self.root / "discovery_sessions.txt").write_text("d1 d2\n")
        reg = jv.load_registry(self.root)
        self.assertTrue(jv.check_provenance("signal", self.root, [self.sig], None, reg))
        self.assertEqual(jv.check_provenance("signal", self.root, ["d1"], None, reg), [])


if __name__ == "__main__":
    unittest.main()
