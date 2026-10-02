import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import events  # noqa: E402
from state_builder import build_state  # noqa: E402


def spec(**kw):
    s = {"window": {"unit": "batches", "n": 5}, "user_prompts": "last_k", "user_prompts_k": 3,
         "tool_inputs": "truncated", "tool_outputs": "none", "counters": [], "max_tokens": 2000}
    s.update(kw)
    return s


def write(rows):
    p = Path(tempfile.mkdtemp()) / "s.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p


CLAUDE = [
    {"type": "user", "message": {"content": "<system-reminder>x</system-reminder>fix the bug"}},
    {"type": "assistant", "message": {"id": "m1", "content": [
        {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "a.py"}},
        {"type": "tool_use", "id": "t2", "name": "Read", "input": {"file_path": "b.py"}}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "AAA"}]}},
    {"type": "assistant", "message": {"id": "m1", "content": [{"type": "text", "text": "hm"}]}},
    {"type": "assistant", "message": {"id": "m2", "content": [
        {"type": "tool_use", "id": "t3", "name": "Bash", "input": {"command": "pytest"}}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t3", "content": [{"type": "text", "text": "ok"}]}]}},
    {"type": "assistant", "isSidechain": True, "message": {"id": "side", "content": []}},
    {"type": "user", "message": {"content": "<command-name>/x</command-name>"}},
    {"type": "user", "message": {"content": "now add tests"}},
]


class TestClaudeLoader(unittest.TestCase):
    def test_turns_batches_outputs_prompts(self):
        ev = events.load_claude(write(CLAUDE))
        self.assertEqual([e["kind"] for e in ev], ["user_prompt", "tool_batch", "tool_batch", "user_prompt"])
        self.assertEqual([e["turn"] for e in ev], [0, 1, 2, 2])
        self.assertEqual(len(ev[1]["calls"]), 2)            # parallel calls share a message id → one batch
        self.assertEqual(ev[1]["calls"][0]["output"], "AAA")
        self.assertEqual(ev[2]["calls"][0]["output"], "ok")  # list-form content
        self.assertEqual(ev[0]["text"], "fix the bug")       # reminder stripped; sidechain and slash command skipped
        self.assertEqual(events.total_turns(ev), 2)


class TestCursorLoader(unittest.TestCase):
    def test_assistant_rows_are_turns_and_no_outputs(self):
        rows = [
            {"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>\nhello\n</user_query>"}]}},
            {"role": "assistant", "message": {"content": [{"type": "tool_use", "name": "Shell", "input": {"command": "ls"}}]}},
            {"role": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}},
        ]
        ev = events.load_cursor(write(rows))
        self.assertEqual(ev[0]["text"], "hello")
        self.assertEqual(ev[1]["calls"][0]["output"], None)
        self.assertEqual(events.total_turns(ev), 2)


class TestStatePrefixOnly(unittest.TestCase):
    def setUp(self):
        self.ev = events.load_claude(write(CLAUDE))

    def test_future_events_never_leak(self):
        s = build_state(spec(), self.ev, 1)["text"]
        self.assertIn("a.py", s)
        self.assertNotIn("pytest", s)
        self.assertNotIn("now add tests", s)

    def test_prefix_state_unchanged_by_later_events(self):
        full = build_state(spec(), self.ev, 1)
        cut = build_state(spec(), [e for e in self.ev if e["turn"] <= 1], 1)
        self.assertEqual(full["text"], cut["text"])

    def test_window_and_outputs(self):
        s = build_state(spec(window={"unit": "batches", "n": 1}, tool_outputs="full"), self.ev, 2)["text"]
        self.assertIn("pytest", s)
        self.assertNotIn("a.py", s)
        self.assertIn("-> ok", s)

    def test_cap_drops_oldest_and_flags(self):
        r = build_state(spec(max_tokens=20, user_prompts="none", tool_inputs="full"), self.ev, 2)
        self.assertTrue(r["truncated"])
        self.assertLessEqual(r["tokens_est"], 20)

    def test_counters(self):
        r = build_state(spec(counters=["tool_calls", "distinct_files", "turn_index"]), self.ev, 2)
        self.assertIn('"tool_calls": 3', r["text"])
        self.assertIn('"turn_index": 2', r["text"])


if __name__ == "__main__":
    unittest.main()
