"""Submission contracts exercised over HTTP against the real server handler."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artifact_submit as submit
import bodies
import hookevents
import lifecycle
import quality as q
import server

ROOT = Path(__file__).resolve().parents[3]


class SubmitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "fixture"
        self.design = self.repo / "docs/plans/example/DESIGN.md"
        self.design.parent.mkdir(parents=True)
        self.design.write_text("# Design\n\n## Intent\nTest hook submission.\n")
        self.store = Path(self.temp.name) / "service-store"
        self.requests = []
        owner = self

        class Handler(server.H):
            def _rest(self, method):
                owner.requests.append((method, self.path, self.headers.get("Authorization")))
                super()._rest(method)

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.env = patch.dict(os.environ, {
            "WORKFLOW_QUALITY_URL": f"http://127.0.0.1:{self.srv.server_port}",
            "WORKFLOW_QUALITY_TOKEN": "test-bearer", "WORKFLOW_QUALITY_TIMEOUT": "0.5",
            "WORKFLOW_QUALITY_DIR": str(Path(self.temp.name) / "decoy"),
            "WORKFLOW_HOOKLOG_DIR": str(Path(self.temp.name) / "spool"),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        store_patch = patch.object(q, "store_dir", return_value=self.store)
        store_patch.start()
        self.addCleanup(store_patch.stop)
        jev_patch = patch.object(q, "jev_scores", return_value=({}, None))
        jev_patch.start()
        self.addCleanup(jev_patch.stop)

    def close_server(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join()

    def artifact(self, file=None):
        return submit.read_artifact(file or self.design)

    def post(self, conversation="session", file=None):
        result = submit.ensure_posted(self.artifact(file), conversation, "claude")
        self.assertTrue(result["ok"], result)
        return result

    def payload(self, harness="claude", file=None, **changes):
        event = {"claude": "PostToolUse", "codex": "PostToolUse", "cursor": "postToolUse",
                 "opencode": "tool.execute.after"}[harness]
        return {"hook_event_name": event, "tool_name": "Write", "session_id": "session",
                "cwd": str(self.repo), "tool_input": {"file_path": str(file or self.design)}, **changes}

    def test_design_frontmatter_hash_and_idempotence(self):
        artifact = self.artifact()
        self.assertFalse(submit.is_submitted(artifact, "session"))
        first = self.post()
        self.assertTrue(first["posted"])
        self.assertEqual(first["response"]["artifact"]["path"], artifact.path)
        original = self.design.read_text()
        self.design.write_text(first["response"]["frontmatter"] + original)
        self.assertEqual(self.artifact().sha, artifact.sha)
        self.assertTrue(submit.is_submitted(self.artifact(), "session"))
        self.assertFalse(self.post()["posted"])
        self.assertEqual(len(q.rows("design")), 1)
        self.assertTrue(all(r[2] == "Bearer test-bearer" for r in self.requests))

    def test_new_conversation_reposts_without_rescoring(self):
        first = self.post("first")
        self.assertFalse(submit.is_submitted(self.artifact(), "second"))
        second = self.post("second")
        self.assertTrue(second["posted"])
        self.assertEqual(second["response"]["id"], first["response"]["id"])
        self.assertFalse(second["response"]["scored"])
        self.assertTrue(submit.is_submitted(self.artifact(), "second"))
        self.assertEqual(len(q.rows("design")), 1)

    def test_brief_parent_from_design_or_own_frontmatter(self):
        design = self.post()["response"]
        self.design.write_text(design["frontmatter"] + self.design.read_text())
        for name, frontmatter in [("01.md", ""), ("02.md", f"---\ndesign_id: {design['id']}\n---\n")]:
            brief = self.design.parent / "briefs" / name
            brief.parent.mkdir(exist_ok=True)
            brief.write_text(frontmatter + "# Brief\n\n## Goal\nTest parent binding.\n")
            posted = self.post(file=brief)
            self.assertEqual(posted["response"]["artifact"]["parent_id"], design["id"])
            self.assertTrue(submit.is_submitted(self.artifact(brief), "session"))
            self.assertFalse(self.post(file=brief)["posted"])

    def test_fabricated_frontmatter_alone_is_not_submission(self):
        self.design.write_text("---\ndesign_id: 999999\n---\n# Design\n")
        self.assertFalse(submit.is_submitted(self.artifact(), "session"))
        result = submit.ensure_posted(self.artifact(), "session", "claude")
        # Existing API rejects nonexistent typed IDs; the hook must still attempt the post.
        self.assertFalse(result["ok"])
        self.assertIn(("POST", "/v1/designs", "Bearer test-bearer"), self.requests)

    def test_score_bind_and_post_patch_event_evidence(self):
        aid = self.post("original")["response"]["id"]
        with q.db() as c:
            c.execute("UPDATE scores SET session_id='score-only' WHERE artifact_id=?", (aid,))
            lifecycle.event(c, "patched_design", {"conversation_id": "patch-only"}, aid)
        hookevents.post({"kind": "tool_call", "ts": 1, "harness": "claude", "session_id": "bind-only",
                         "tool_name": "mcp__workflow-quality__post_design", "ok": True, "output": {"id": aid}})
        for conversation in ("original", "score-only", "patch-only", "bind-only"):
            self.assertTrue(submit.is_submitted(self.artifact(), conversation), conversation)
        self.design.write_text(self.design.read_text() + "Changed body.\n")
        self.assertFalse(submit.is_submitted(self.artifact(), "bind-only"))

    def test_execution_only_join_is_not_submission(self):
        aid = self.post()["response"]["id"]
        with q.db() as c:
            lifecycle.event(c, "execution_started", {"conversation_id": "execution-only"}, aid)
        session = hookevents.session("execution-only")
        self.assertEqual(session["artifacts"][0]["id"], aid)
        self.assertFalse(session["artifacts"][0]["submission_bound"])
        self.assertFalse(submit.is_submitted(self.artifact(), "execution-only"))

    def test_latest_stored_body_and_reversion(self):
        original = self.design.read_text()
        aid = self.post()["response"]["id"]
        self.design.write_text(original + "Version two.\n")
        self.post()
        self.design.write_text(original)
        self.assertFalse(submit.is_submitted(self.artifact(), "session"))
        reverted = self.post()
        self.assertFalse(reverted["response"]["scored"])
        self.assertEqual(bodies.get(aid)["sha"], self.artifact().sha)
        self.assertTrue(submit.is_submitted(self.artifact(), "session"))

    def test_same_http_store_ignores_local_decoy(self):
        decoy = Path(os.environ["WORKFLOW_QUALITY_DIR"])
        with patch.object(q, "store_dir", return_value=decoy):
            artifact = self.artifact()
            lifecycle.put_artifact("design", {"text": artifact.text, "project": artifact.project,
                                  "path": artifact.path, "conversation_id": "session", "use_jev": False})
        self.assertFalse(submit.is_submitted(artifact, "session"))
        self.assertTrue(self.post()["posted"])

    def test_rate_artifact_without_stored_body_does_not_suppress_post(self):
        artifact = self.artifact()
        q.score_content("design", artifact.text, artifact.file, artifact.repo, False, True,
                        "claude", "session")
        result = self.post()
        self.assertTrue(result["posted"])
        self.assertTrue(submit.is_submitted(artifact, "session"))

    def test_exact_paths_and_non_artifacts_have_no_side_effects(self):
        for path in ("DESIGN.md", "docs/plans/PLAN.md", "docs/plans/example/PLAN.md",
                     "docs/plans/example/deeper/DESIGN.md", "docs/plans/example/briefs/deeper/a.md"):
            with self.subTest(path=path):
                self.assertIsNone(submit.read_artifact(path, self.repo))
        self.assertEqual(self.requests, [])

    def test_hook_success_records_outcome_and_never_mutates_file(self):
        original = self.design.read_bytes()
        response = submit.run_hook(self.payload(), "claude")
        self.assertIn("posted design_id=", response["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.design.read_bytes(), original)
        rows = hookevents.events("session")
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["tool_name"], rows[0]["ok"]), ("artifact_submit", 1))
        self.assertTrue(hookevents.session("session")["artifacts"])
        self.assertTrue(hookevents.plan_sessions(self.artifact().project, "example")["sessions"])

    def test_check_error_still_attempts_post(self):
        client = submit.Client()
        real_request = client.request
        def request(method, path, body=None):
            if method == "GET":
                raise TimeoutError("check timed out")
            return real_request(method, path, body)
        with patch.object(client, "request", side_effect=request):
            result = submit.ensure_posted(self.artifact(), "session", "claude", client)
        self.assertTrue(result["posted"])
        self.assertIn("timed out", result["check_error"])

    def test_offline_hook_is_advisory_and_spools_failure(self):
        # No listeners on this ephemeral socket after close; never touch live services.
        import socket
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        original = self.design.read_bytes()
        with patch.dict(os.environ, {"WORKFLOW_QUALITY_URL": f"http://127.0.0.1:{port}"}):
            response = submit.run_hook(self.payload(), "claude")
        self.assertIn("posting still owed", response["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.design.read_bytes(), original)
        spool = Path(os.environ["WORKFLOW_HOOKLOG_DIR"]) / "claude/session.jsonl"
        row = json.loads(spool.read_text())
        self.assertFalse(row["ok"])
        self.assertEqual(row["tool_name"], "artifact_submit")

    def test_http_errors_fail_open_and_record_failure(self):
        for error in ("401", "500", "timeout"):
            with self.subTest(error=error), patch.object(submit.Client, "request", side_effect=TimeoutError(error)):
                result = submit.ensure_posted(self.artifact(), "session", "claude")
                self.assertFalse(result["ok"])
                self.assertIn(error, result["reason"])
        client = submit.Client()
        client.token = "wrong-token"
        result = submit.ensure_posted(self.artifact(), "session", "claude", client)
        self.assertFalse(result["ok"])
        self.assertIn("401", result["reason"])

    def test_cli_always_exits_zero_for_bad_payload_and_config(self):
        for payload in ("not json", "[]", "null", "{}"):
            env = dict(os.environ, WORKFLOW_QUALITY_TIMEOUT="invalid")
            result = subprocess.run([sys.executable, str(ROOT / "tools/quality/artifact_submit.py"),
                                     "hook", "--harness", "cursor"], input=payload, text=True,
                                    capture_output=True, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
