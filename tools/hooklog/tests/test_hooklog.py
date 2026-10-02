import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hooklog as hl  # noqa: E402

SCRIPT = Path(hl.__file__)


def run(harness, payload, d):
    env = dict(os.environ, WORKFLOW_HOOKLOG_DIR=d)
    return subprocess.run([sys.executable, str(SCRIPT), "record", "--harness", harness], input=payload,
                          capture_output=True, text=True, env=env)


class T(unittest.TestCase):
    def test_claude_prompt_and_tool(self):
        with tempfile.TemporaryDirectory() as d:
            run("claude", json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "fix it", "cwd": "/w"}), d)
            run("claude", json.dumps({"hook_event_name": "PostToolUse", "session_id": "s1", "tool_name": "Bash", "tool_use_id": "t1",
                                      "tool_input": {"command": "pytest"}, "tool_response": {"stdout": "3 passed"}}), d)
            rows = hl.read_session(Path(d) / "claude" / "s1.jsonl")
            self.assertEqual([r["kind"] for r in rows], ["user_prompt", "tool_call"])
            self.assertEqual(rows[1]["tool_name"], "Bash")
            self.assertEqual(rows[1]["output"]["stdout"], "3 passed")

    def test_cursor_events_and_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            r = run("cursor", json.dumps({"hook_event_name": "afterShellExecution", "conversation_id": "c1", "command": "ls", "output": "a"}), d)
            self.assertEqual(r.returncode, 0)
            self.assertIn('"continue": true', r.stdout)
            rows = hl.read_session(Path(d) / "cursor" / "c1.jsonl")
            self.assertEqual((rows[0]["tool_name"], rows[0]["input"]["command"]), ("Shell", "ls"))

    def test_redaction_and_truncation(self):
        row = hl.normalize("claude", {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Bash",
                                      "tool_input": {"command": "curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz'"},
                                      "tool_response": "x" * 5000})
        self.assertIn("[REDACTED]", row["input"]["command"])
        self.assertLess(len(row["output"]), 2100)

    def test_cursor_real_shapes(self):
        row = hl.normalize("cursor", {"hook_event_name": "postToolUse", "conversation_id": "c", "tool_name": "Shell", "tool_use_id": "u",
                                      "tool_input": "{\"command\": \"ls\"}", "tool_output": "{\"output\":\"a\\n\",\"exitCode\":0}"})
        self.assertEqual((row["input"]["command"], row["output"]["exitCode"]), ("ls", 0))
        step = hl.normalize("cursor", {"hook_event_name": "afterAgentThought", "conversation_id": "c",
                                       "generation_id": "9ecc107f-081f-4fdc-9e61-24a99b5a70f4-2-3bkg", "text": "t"})
        self.assertEqual((step["kind"], step["step"]), ("step", 2))

    def test_garbage_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ("", "not json", "[]", '{"hook_event_name":"Unknown"}'):
                self.assertEqual(run("claude", bad, d).returncode, 0)
            self.assertEqual(list(Path(d).glob("*/*")), [])

    def test_torn_line_tolerated(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.jsonl"
            f.write_text('{"kind":"stop"}\n{"kind":"user_pr')
            self.assertEqual(len(hl.read_session(f)), 1)


if __name__ == "__main__":
    unittest.main()
