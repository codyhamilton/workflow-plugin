#!/usr/bin/env python3
"""Local HTTP MCP service for workflow quality ratings (stdlib only).

Clients pass a design or brief (text + repo metadata); the service holds TYPESAFE_API_KEY, runs the
Jev criteria, logs to the SQLite ledger and returns the relative rating. Tools: rate_artifact,
link_artifacts, quality_report. Binds 127.0.0.1; set WORKFLOW_QUALITY_TOKEN to require a bearer token.

  python3 tools/quality/server.py [--port 8765]     # MCP endpoint: POST http://127.0.0.1:8765/mcp
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooklog"))
import quality as q  # noqa: E402

PROTOCOL = "2025-03-26"
TOOLS = [
    {"name": "rate_artifact",
     "description": "Score a workflow brief or DESIGN.md against the stable quality criteria, log it to the central ledger and return its relative rating (informational).",
     "inputSchema": {"type": "object", "required": ["kind", "text"], "properties": {
         "kind": {"enum": ["brief", "design"]}, "text": {"type": "string", "description": "full document text"},
         "path": {"type": "string", "description": "repo-relative path, e.g. docs/plans/x/briefs/01.md"},
         "repo_path": {"type": "string", "description": "local checkout, used for owned-path checks and project name"},
         "project": {"type": "string"}, "plan": {"type": "string"}, "session": {"type": "string"}, "harness": {"type": "string"},
         "use_jev": {"type": "boolean", "default": True}}}},
    {"name": "link_artifacts",
     "description": "Back-reference later work (rework, missing_scope, defect, supersedes) to a prior scored brief or design.",
     "inputSchema": {"type": "object", "required": ["to", "type"], "properties": {
         "to": {"type": "string", "description": "path of the prior artifact"}, "from": {"type": "string"},
         "type": {"enum": list(q.LINK_TYPES)}, "note": {"type": "string"}, "evidence": {"type": "string"}}}},
    {"name": "quality_report",
     "description": "Relative quality by project or plan (mean composite, weakest criterion).",
     "inputSchema": {"type": "object", "properties": {"kind": {"enum": ["brief", "design"]}, "by": {"enum": ["project", "plan"]}}}},
]


def rate_artifact(a: dict) -> str:
    kind = a["kind"]
    if kind not in ("brief", "design"):
        raise ValueError("kind must be brief or design")
    repo = Path(a["repo_path"]).expanduser() if a.get("repo_path") else Path("/nonexistent-repo")
    path = Path(a.get("path") or f"docs/plans/{a.get('plan') or 'unknown'}/{'DESIGN.md' if kind == 'design' else 'briefs/unnamed.md'}")
    if not path.is_absolute() and a.get("repo_path"):
        path = repo / path
    row = q.score_content(kind, a["text"], path, repo, a.get("use_jev", True), True, a.get("harness") or "mcp", a.get("session") or "unknown",
                          project=a.get("project"), plan=a.get("plan"))
    return q.summary(row) + "\n" + json.dumps({k: row[k] for k in ("composite", "composite_det", "rating", "criteria", "jev_error")}, default=str)


def call(name: str, a: dict) -> str:
    if name == "rate_artifact":
        return rate_artifact(a)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if name == "link_artifacts":
            q.cmd_link(a.get("from"), a["to"], a["type"], a.get("note", ""), a.get("evidence", ""))
        elif name == "quality_report":
            q.cmd_report(a.get("kind"), a.get("by", "project"))
        else:
            raise ValueError(f"unknown tool {name}")
    return buf.getvalue()


def handle(msg: dict) -> dict | None:
    m, i = msg.get("method"), msg.get("id")
    if i is None:
        return None  # notification
    try:
        if m == "initialize":
            res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "workflow-quality", "version": "0.1.0"}}
        elif m == "tools/list":
            res = {"tools": TOOLS}
        elif m == "tools/call":
            p = msg.get("params") or {}
            try:
                res = {"content": [{"type": "text", "text": call(p.get("name", ""), p.get("arguments") or {})}]}
            except (Exception, SystemExit) as e:
                res = {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
        elif m == "ping":
            res = {}
        else:
            return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": f"method not found: {m}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": i, "error": {"code": -32603, "message": str(e)}}
    return {"jsonrpc": "2.0", "id": i, "result": res}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code: int, body: bytes = b"", ctype: str = "application/json"):
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        tok = os.environ.get("WORKFLOW_QUALITY_TOKEN")
        if tok and self.headers.get("Authorization") != f"Bearer {tok}":
            return self._send(401, b'{"error":"unauthorized"}')
        if self.path.rstrip("/") != "/mcp":
            return self._send(404)
        try:
            msg = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, b'{"error":"bad json"}')
        out = [r for r in (handle(m) for m in (msg if isinstance(msg, list) else [msg])) if r]
        if not out:
            return self._send(202)
        self._send(200, json.dumps(out if isinstance(msg, list) else out[0]).encode())

    def do_GET(self):
        self._send(405)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    print(f"workflow-quality MCP on http://{a.host}:{a.port}/mcp  ledger={q.store_dir()}  jev={'on' if os.environ.get('TYPESAFE_API_KEY') else 'off'}", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
