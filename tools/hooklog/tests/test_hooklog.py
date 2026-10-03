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
            self.assertEqual(json.loads(r.stdout), {})
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

    def test_service_down_spools_to_file(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, WORKFLOW_HOOKLOG_DIR=d, WORKFLOW_QUALITY_URL="http://127.0.0.1:9", WORKFLOW_QUALITY_TIMEOUT="0.5")
            r = subprocess.run([sys.executable, str(SCRIPT), "record", "--harness", "claude"], capture_output=True, text=True, env=env,
                               input=json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "s9", "prompt": "hi"}))
            self.assertEqual(r.returncode, 0)
            self.assertEqual(len(hl.read_session(Path(d) / "claude" / "s9.jsonl")), 1)

    def test_garbage_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ("", "not json", "[]"):
                self.assertEqual(run("claude", bad, d).returncode, 0)
            self.assertEqual(list(Path(d).glob("*/*")), [])

    def test_new_and_future_events_are_retained(self):
        for event in ("SessionStart", "InstructionsLoaded", "Interrupt", "workspaceOpen", "FutureHook"):
            row = hl.normalize("codex", {"hook_event_name": event, "reason": "test"})
            self.assertEqual((row["hook_event"], row["kind"], row["data"]["reason"]), (event, "event", "test"))

    def test_pre_tool_and_bus_are_not_completed_calls(self):
        self.assertEqual(hl.normalize("codex", {"hook_event_name": "PreToolUse"})["kind"], "tool_pre")
        self.assertEqual(hl.normalize("opencode", {"hook_event_name": "tool.execute.after", "source": "bus"})["kind"], "event")
        self.assertEqual(hl.normalize("cursor", {"hook_event_name": "sessionEnd"})["kind"], "event")

    def test_lifecycle_headers_and_display_are_scrubbed(self):
        row = hl.normalize("opencode", {"hook_event_name": "chat.headers", "headers": {
            "Authorization": "short-secret", "X-API-Key": "short-key"}, "text": "x" * 5000})
        self.assertEqual(row["data"]["headers"], {"Authorization": "[REDACTED]", "X-API-Key": "[REDACTED]"})
        self.assertLess(len(row["data"]["text"]), 2100)
        encoded = hl.normalize("cursor", {"hook_event_name": "postToolUse", "tool_input":
            '{"password":"short-secret", "input_tokens":123}'})
        self.assertEqual(encoded["data"]["tool_input"], {"password": "[REDACTED]", "input_tokens": 123})
        row = hl.normalize("claude", {"hook_event_name": "MessageDisplay", "text": "password=abcdefgh"})
        self.assertIn("[REDACTED]", row["text"])

    def test_cursor_permissive_responses_on_error_and_disable(self):
        with tempfile.TemporaryDirectory() as d:
            for event in ("preToolUse", "subagentStart", "beforeShellExecution", "beforeMCPExecution",
                          "beforeReadFile", "beforeTabFileRead", "beforeSubmitPrompt"):
                for payload in ("not json", '{"hook_event_name":"wrong"}'):
                    for disabled in ("on", "off"):
                        result = subprocess.run([sys.executable, str(SCRIPT), "record", "--harness", "cursor", "--event", event],
                            input=payload, text=True, capture_output=True,
                            env=dict(os.environ, WORKFLOW_HOOKLOG_DIR=d, WORKFLOW_HOOKLOG=disabled))
                        self.assertEqual(result.returncode, 0)
                        expected = {"continue": True} if event == "beforeSubmitPrompt" else {"permission": "allow"}
                        self.assertEqual(json.loads(result.stdout), expected)

    def test_unwritable_store_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "file"
            path.touch()
            result = run("codex", '{"hook_event_name":"Stop","session_id":"s"}', str(path))
            self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_torn_line_tolerated(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.jsonl"
            f.write_text('{"kind":"stop"}\n{"kind":"user_pr')
            self.assertEqual(len(hl.read_session(f)), 1)


class TestAutoHarness(unittest.TestCase):
    def test_detects_cursor_and_claude(self):
        self.assertEqual(hl.detect_harness({"conversation_id": "c", "cursor_version": "1"}), "cursor")
        self.assertEqual(hl.detect_harness({"session_id": "s", "transcript_path": "/x"}), "claude")

    def test_auto_routes_to_harness_dir(self):
        with tempfile.TemporaryDirectory() as d:
            run("auto", json.dumps({"hook_event_name": "postToolUse", "conversation_id": "c1", "tool_name": "Read"}), d)
            run("auto", json.dumps({"hook_event_name": "PostToolUse", "session_id": "s1", "transcript_path": "/x", "tool_name": "Read"}), d)
            self.assertTrue((Path(d) / "cursor" / "c1.jsonl").exists())
            self.assertTrue((Path(d) / "claude" / "s1.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
