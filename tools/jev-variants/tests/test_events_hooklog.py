import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import events  # noqa: E402


class T(unittest.TestCase):
    def test_batches_from_timing(self):
        rows = [{"kind": "user_prompt", "text": "go", "ts": 0},
                {"kind": "tool_call", "tool_name": "Read", "input": {}, "ts": 10.0},
                {"kind": "tool_call", "tool_name": "Grep", "input": {}, "ts": 10.2},
                {"kind": "tool_call", "tool_name": "Bash", "input": {}, "output": {"stdout": "ok"}, "ts": 20.0}]
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.jsonl"
            f.write_text("\n".join(json.dumps(r) for r in rows))
            ev = events.load_events("hooklog", f)
        batches = [e for e in ev if e["kind"] == "tool_batch"]
        self.assertEqual([len(b["calls"]) for b in batches], [2, 1])
        self.assertEqual(events.total_turns(ev), 2)
        self.assertIn('"stdout"', batches[1]["calls"][0]["output"])

    def _turns(self, rows):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.jsonl"
            f.write_text("\n".join(json.dumps(r) for r in rows))
            return events.total_turns(events.load_events("hooklog", f))

    def test_markers_define_turns_not_timing(self):
        rows = [{"kind": "user_prompt", "text": "go", "ts": 0},
                {"kind": "tool_call", "tool_name": "A", "ts": 1}, {"kind": "tool_call", "tool_name": "B", "ts": 9},
                {"kind": "batch_end", "ts": 9.1},
                {"kind": "agent_text", "ts": 12}, {"kind": "tool_call", "tool_name": "C", "ts": 13}, {"kind": "batch_end", "ts": 13.1},
                {"kind": "agent_text", "ts": 20}, {"kind": "stop", "ts": 20.1}]
        self.assertEqual(self._turns(rows), 3)  # batch(A,B), batch(C), final text turn

    def test_text_only_reply_counts_once_at_stop_and_idle_stop_is_free(self):
        self.assertEqual(self._turns([{"kind": "user_prompt", "text": "q", "ts": 0}, {"kind": "agent_text", "ts": 1}, {"kind": "stop", "ts": 2}]), 1)
        self.assertEqual(self._turns([{"kind": "user_prompt", "text": "q", "ts": 0}, {"kind": "stop", "ts": 2}]), 0)

    def test_subagent_rows_excluded(self):
        rows = [{"kind": "user_prompt", "text": "q", "ts": 0},
                {"kind": "tool_call", "tool_name": "A", "ts": 1, "agent_id": "sub"}, {"kind": "batch_end", "ts": 2, "agent_id": "sub"},
                {"kind": "tool_call", "tool_name": "B", "ts": 3}, {"kind": "batch_end", "ts": 4}]
        self.assertEqual(self._turns(rows), 1)

    def test_cursor_steps_are_turns(self):
        # shape captured from a real `agent -p` run: afterAgentThought per model step, tools between
        rows = [{"kind": "step", "step": 0, "ts": 1}, {"kind": "tool_call", "tool_name": "Read", "ts": 2},
                {"kind": "tool_call", "tool_name": "Read", "ts": 9},  # far apart, but same step
                {"kind": "step", "step": 1, "ts": 10}, {"kind": "tool_call", "tool_name": "Shell", "ts": 11},
                {"kind": "step", "step": 2, "ts": 12}, {"kind": "stop", "ts": 13}]
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.jsonl"
            f.write_text("\n".join(json.dumps(r) for r in rows))
            ev = events.load_events("hooklog", f)
        self.assertEqual(events.total_turns(ev), 3)
        self.assertEqual([len(e["calls"]) for e in ev if e["kind"] == "tool_batch"], [2, 1])


if __name__ == "__main__":
    unittest.main()


class TestClaudeLiveShape(unittest.TestCase):
    def test_batches_then_stop_counts_final_reply(self):
        # captured from a real `claude -p --plugin-dir`: 2 parallel reads, Bash, Edit, then a text reply
        import json, tempfile, pathlib
        from events import load_hooklog, total_turns
        rows = [
            {"kind": "user_prompt", "text": "go", "ts": 1},
            {"kind": "tool_call", "tool_name": "Read", "ts": 2}, {"kind": "tool_call", "tool_name": "Read", "ts": 2},
            {"kind": "batch_end", "ts": 3},
            {"kind": "tool_call", "tool_name": "Bash", "ts": 4}, {"kind": "batch_end", "ts": 4},
            {"kind": "tool_call", "tool_name": "Edit", "ts": 5}, {"kind": "batch_end", "ts": 5},
            {"kind": "stop", "ts": 6},
        ]
        p = pathlib.Path(tempfile.mkdtemp()) / "s.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows))
        ev = load_hooklog(p)
        self.assertEqual([len(e.get("calls", [])) for e in ev if e["kind"] == "tool_batch"], [2, 1, 1])
        self.assertEqual(total_turns(ev), 4)
