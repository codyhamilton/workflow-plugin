"""Unit tests for dual_write_sink (no network except optional egress test)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from dual_write_sink import build_envelope, detect_host, emit_event, post_remote

ROOT = Path(__file__).resolve().parent


class TestHostDetection(unittest.TestCase):
    def test_cursor_cloud(self) -> None:
        with mock.patch.dict(os.environ, {"CURSOR_AGENT": "1"}, clear=False):
            self.assertEqual(detect_host(), ("cloud", "cursor-cloud"))

    def test_opencode(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"WORKFLOW_INSTALL_MODE": "opencode", "CURSOR_AGENT": ""},
            clear=False,
        ):
            self.assertEqual(detect_host()[0], "opencode")


class TestDualWrite(unittest.TestCase):
    def test_local_append_and_remote_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.jsonl"
            env = os.environ.copy()
            env.pop("WORKFLOW_ANALYTICS_URL", None)
            with mock.patch.dict(os.environ, env, clear=True):
                row = {"ts": "t", "kind": "trigger", "record_version": 1}
                envelope = emit_event(
                    kind="driver.trigger",
                    payload={"skipped": True},
                    local_path=path,
                    legacy_row=row,
                )
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["kind"], "trigger")
            self.assertEqual(envelope["_remote_detail"], "skipped:no_url")
            self.assertTrue(envelope["_remote_ok"])

    def test_mock_server_roundtrip(self) -> None:
        port = 18766
        received: list[bytes] = []

        from http.server import BaseHTTPRequestHandler, HTTPServer

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a: object) -> None:
                return

            def do_POST(self) -> None:
                n = int(self.headers.get("Content-Length", 0))
                received.append(self.rfile.read(n))
                self.send_response(204)
                self.end_headers()

        server = HTTPServer(("127.0.0.1", port), H)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        envelope = build_envelope(kind="driver.assert", payload={"pass": True})
        ok, detail = post_remote(envelope, url=f"http://127.0.0.1:{port}/events", token="test")
        thread.join(timeout=2)
        server.server_close()
        self.assertTrue(ok)
        self.assertIn("http:204", detail)
        self.assertEqual(len(received), 1)
        body = json.loads(received[0].decode())
        self.assertEqual(body["kind"], "driver.assert")


if __name__ == "__main__":
    unittest.main()
