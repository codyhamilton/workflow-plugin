#!/usr/bin/env python3
"""Minimal append-only HTTP sink for lab proofs (stdlib only)."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

OUT = Path(__file__).resolve().parent / "validated" / "mock_sink_received.jsonl"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        auth = self.headers.get("Authorization", "")
        try:
            row = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"auth_present": bool(auth), "body": row},
                    ensure_ascii=False,
                )
                + "\n"
            )
        self.send_response(204)
        self.end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18765
    OUT.write_text("", encoding="utf-8")
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"mock_sink_server listening on 127.0.0.1:{port}", flush=True)
    server.handle_request()
    server.server_close()


if __name__ == "__main__":
    main()
