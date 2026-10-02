import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import runner  # noqa: E402

Q = {"present": {"type": "score", "instructions": "x", "criteria": ["no", "maybe", "likely", "yes"]}}
REG = {
    "marker": {"mk-a": {"spec": {"signal": "sig-a", "polarity": "higher_means_present", "question": Q}},
               "mk-b": {"spec": {"signal": "sig-b", "polarity": "higher_means_absent", "question": Q}}},
    "state": {"st-1": {"spec": {"window": {"unit": "batches", "n": 3}, "user_prompts": "none", "tool_inputs": "names",
                                "max_tokens": 500}}},
}
CELL = {"cell_id": "c1", "round": "r1", "panel": "pn-1", "state": "st-1", "markers": ["mk-a", "mk-b"],
        "session": "s1", "split": "discovery", "checkpoint": 1}


def corpus():
    p = Path(tempfile.mkdtemp()) / "s.jsonl"
    p.write_text(json.dumps({"role": "assistant", "message": {"content": [{"type": "tool_use", "name": "Shell", "input": {}}]}}))
    return {"s1": {"harness": "cursor", "path": str(p), "split": "discovery"}}


class TestRunner(unittest.TestCase):
    def test_request_namespaces_questions(self):
        req = runner.build_request(CELL, REG, {"text": "hi"})
        self.assertEqual(sorted(req["questions"]), ["mk-a__present", "mk-b__present"])
        self.assertEqual(req["state"], {"snapshot": "hi"})

    def test_rows_split_per_marker_with_polarity(self):
        resp = {"answers": {"mk-a__present": {"score": 3}, "mk-b__present": {"score": 3}}, "usage": {"cost_usd": 0.02}}
        rows = runner.rows_for(CELL, REG, {"tokens_est": 5, "truncated": False}, resp, 0.01, None, 0.1)
        self.assertEqual([r["score"] for r in rows], [1.0, 0.0])
        self.assertTrue(all(r["parse_ok"] and not r["cost_estimated"] for r in rows))
        self.assertAlmostEqual(rows[0]["cost_usd"], 0.01)

    def test_missing_answer_is_parse_failure(self):
        resp = {"answers": {"mk-a__present": {"score": 2}}}
        rows = runner.rows_for(CELL, REG, {"tokens_est": 5, "truncated": False}, resp, 0.01, None, 0.1)
        self.assertTrue(rows[0]["parse_ok"])
        self.assertFalse(rows[1]["parse_ok"])
        self.assertTrue(rows[1]["cost_estimated"])

    def test_run_writes_ledger_and_survives_errors(self):
        led = Path(tempfile.mkdtemp()) / "l.jsonl"
        calls = []

        def poster(req):
            calls.append(req)
            raise SystemExit("HTTP 500")
        st = runner.run([CELL], REG, corpus(), led, 0.01, poster)
        self.assertEqual((st["calls"], st["errors"]), (1, 1))
        rows = [json.loads(l) for l in led.read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertFalse(rows[0]["parse_ok"])
        self.assertIn("HTTP 500", rows[0]["error"])

    def test_hide_next_prompt_keeps_outcome_out_of_state(self):
        d = Path(tempfile.mkdtemp())
        p = d / "s.jsonl"
        rows = [{"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>first ask</user_query>"}]}},
                {"role": "assistant", "message": {"content": [{"type": "tool_use", "name": "Shell", "input": {}}]}},
                {"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>OUTCOME SENTINEL</user_query>"}]}}]
        p.write_text("\n".join(json.dumps(r) for r in rows))
        corp = {"s1": {"harness": "cursor", "path": str(p), "split": "discovery"}}
        reg = {"marker": REG["marker"], "state": {"st-1": {"spec": dict(REG["state"]["st-1"]["spec"], user_prompts="all")}}}
        seen = []
        for hide in (False, True):
            led = d / f"l{hide}.jsonl"
            runner.run([dict(CELL, hide_next_prompt=hide)], reg, corp, led, 0.01, lambda r: seen.append(json.dumps(r)) or 1 / 0)
        self.assertIn("OUTCOME SENTINEL", seen[0])
        self.assertNotIn("OUTCOME SENTINEL", seen[1])
        self.assertIn("first ask", seen[1])

    def test_dry_run_makes_no_calls(self):
        led = Path(tempfile.mkdtemp()) / "l.jsonl"
        runner.run([CELL], REG, corpus(), led, 0.01, lambda r: 1 / 0, dry_run=True)
        self.assertFalse(led.exists())


if __name__ == "__main__":
    unittest.main()
