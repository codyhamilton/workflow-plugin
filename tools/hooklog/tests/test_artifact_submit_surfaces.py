"""Replay native write envelopes through shipped registrations and the real HTTP handler."""
import json
import os
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/quality/tests"))
from test_artifact_submit import ArtifactServiceFixture
import artifact_submit as submit


class ArtifactSurfaceTests(ArtifactServiceFixture, unittest.TestCase):
    def commands(self, harness, event, file=None):
        configs = {"claude": "hooks/hooks.json", "cursor": "hooks/cursor.json",
                   "codex": "tools/hooklog/codex-hooks.example.json"}
        if harness == "opencode":
            return [f'python3 "{ROOT}/tools/quality/artifact_submit.py" hook --harness opencode']
        config = json.loads((ROOT / (file or configs[harness])).read_text())
        groups = config["hooks"][event]
        hooks = groups if harness == "cursor" else groups[0]["hooks"]
        return [hook["command"].replace("/ABS/PATH/workflow-plugin", str(ROOT)) for hook in hooks]

    def replay(self, harness, payload, file=None):
        responses = []
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT), CURSOR_PLUGIN_ROOT=str(ROOT),
                   WORKFLOW_HOOKLOG="on")
        for command in self.commands(harness, payload["hook_event_name"], file):
            result = subprocess.run(command, shell=True, input=json.dumps(payload), text=True,
                                    capture_output=True, env=env, cwd=self.repo, timeout=8)
            self.assertEqual(result.returncode, 0, result.stderr)
            if result.stdout:
                responses.append(json.loads(result.stdout))
        return responses

    def test_each_native_fixture_posts_once_then_zero_and_preserves_files(self):
        brief = self.design.parent / "briefs/01.md"
        brief.parent.mkdir()
        brief.write_text("# Brief\n\n## Goal\nFixture replay.\n")
        fixtures = json.loads((Path(__file__).parent / "fixtures/artifact_writes.json").read_text())
        original = (self.design.read_bytes(), brief.read_bytes())
        for fixture in fixtures:
            harness, payload = fixture["harness"], fixture["payload"]
            payload["cwd"] = str(self.repo)
            with self.subTest(harness=harness, payload=payload):
                self.requests.clear()
                responses = self.replay(harness, payload)
                posts = [path for method, path, _ in self.requests if method == "POST" and path in ("/v1/designs", "/v1/briefs")]
                self.assertEqual(len(posts), 1, self.requests)
                self.requests.clear()
                self.replay(harness, payload)
                self.assertFalse(any(method == "POST" and path in ("/v1/designs", "/v1/briefs") for method, path, _ in self.requests))
                if payload["hook_event_name"] == "afterFileEdit":
                    self.assertTrue(all(response == {} for response in responses))
                elif harness == "cursor":
                    self.assertIn("posted", responses[-1]["additionalContext"])
                elif harness == "claude":
                    self.assertIn("posted", responses[-1]["hookSpecificOutput"]["additionalContext"])
                else:
                    self.assertEqual(responses, [])
        self.assertEqual((self.design.read_bytes(), brief.read_bytes()), original)
        self.assertFalse(Path(os.environ["WORKFLOW_QUALITY_DIR"]).exists())

    def test_registrations_follow_hooklog_only_on_signed_surfaces(self):
        for harness, file, expected in [
            ("claude", "hooks/hooks.json", {"PostToolUse"}),
            ("cursor", "hooks/cursor.json", {"postToolUse", "afterFileEdit"}),
            ("cursor", "tools/hooklog/cursor-hooks.example.json", {"postToolUse", "afterFileEdit"}),
            ("codex", "tools/hooklog/codex-hooks.example.json", {"PostToolUse"}),
        ]:
            config = json.loads((ROOT / file).read_text())
            submitted_events = set()
            for event, groups in config["hooks"].items():
                hooks = groups if harness == "cursor" else [hook for group in groups for hook in group["hooks"]]
                commands = [hook["command"] for hook in hooks]
                if any("artifact_submit.py" in command for command in commands):
                    submitted_events.add(event)
                    self.assertEqual(len(hooks), 2)
                    self.assertIn("spool.sh", commands[0])
                    self.assertIn("artifact_submit.py", commands[1])
                    self.assertEqual(hooks[1]["timeout"], 5)
                self.assertFalse(any("quality.py" in command for command in commands))
            self.assertEqual(submitted_events, expected, file)

    def test_unlisted_events_read_tools_and_bus_do_not_submit(self):
        for harness, event, tool, source in [
            ("claude", "FileChanged", "Write", None), ("claude", "PostToolUseFailure", "Edit", None),
            ("claude", "PreToolUse", "Write", None), ("codex", "FileChanged", "Write", None),
            ("cursor", "afterTabFileEdit", "Edit", None), ("cursor", "postToolUseFailure", "Edit", None),
            ("opencode", "file.edited", "write", "bus"), ("opencode", "tool.execute.after", "write", "bus"),
            ("claude", "PostToolUse", "Read", None), ("cursor", "postToolUse", "Bash", None),
        ]:
            with self.subTest(harness=harness, event=event, tool=tool):
                payload = self.payload(harness, hook_event_name=event, tool_name=tool, source=source,
                                       file_path=str(self.design))
                submit.run_hook(payload, harness)
        self.assertEqual(self.requests, [])

    def test_cursor_two_surfaces_and_multiedit_deduplicate(self):
        payload = self.payload("cursor")
        submit.run_hook(payload, "cursor")
        submit.run_hook({**payload, "hook_event_name": "afterFileEdit", "file_path": str(self.design)}, "cursor")
        self.assertEqual(sum(method == "POST" and path == "/v1/designs" for method, path, _ in self.requests), 1)
        self.requests.clear()
        payload = self.payload("claude", session_id="multi", tool_name="MultiEdit",
                               tool_input={"file_path": str(self.design), "edits": [{"file_path": str(self.design)}]})
        submit.run_hook(payload, "claude")
        self.assertEqual(sum(method == "POST" and path == "/v1/designs" for method, path, _ in self.requests), 1)

    def test_legacy_quality_hook_delegates_without_local_scoring(self):
        payload = self.payload()
        result = subprocess.run([sys.executable, str(ROOT / "tools/quality/quality.py"), "hook"],
                                input=json.dumps(payload), text=True, capture_output=True, env=dict(os.environ), cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("posted design_id=", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])
        self.assertFalse(Path(os.environ["WORKFLOW_QUALITY_DIR"]).exists())
        self.assertEqual(sum(method == "POST" and path == "/v1/designs" for method, path, _ in self.requests), 1)

    def test_shipped_claude_command_fails_open_when_service_is_unavailable(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        original = self.design.read_bytes()
        with patch.dict(os.environ, {"WORKFLOW_QUALITY_URL": f"http://127.0.0.1:{port}"}):
            responses = self.replay("claude", self.payload())
        self.assertIn("posting still owed", responses[-1]["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.design.read_bytes(), original)
        spool = Path(os.environ["WORKFLOW_HOOKLOG_DIR"]) / "claude/session.jsonl"
        rows = [json.loads(line) for line in spool.read_text().splitlines()]
        self.assertEqual(rows[-1]["tool_name"], "artifact_submit")
        self.assertFalse(rows[-1]["ok"])


if __name__ == "__main__":
    unittest.main()
