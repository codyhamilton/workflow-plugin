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
import lifecycle as lc  # noqa: E402
import quality as q  # noqa: E402
from urllib.parse import parse_qs, urlparse  # noqa: E402

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
_CTX = {"harness": {"type": "string"}, "workflow_version": {"type": "string"}, "model": {"type": "string"}, "conversation_id": {"type": "string"},
        "initiator_type": {"enum": list(lc.INITIATORS)}, "initiator_id": {"type": "string"}, "repo": {"type": "string"},
        "design_stage": {"type": "string"}, "execution_stage": {"type": "string"}}


def _t(name, desc, props, req=()):
    return {"name": name, "description": desc, "inputSchema": {"type": "object", "required": list(req), "properties": {**props, **_CTX}}}


_ART = {"text": {"type": "string"}, "project": {"type": "string"}, "repo_path": {"type": "string"}, "plan": {"type": "string"}, "path": {"type": "string"},
        "name": {"type": "string"}, "work_type": {"type": "string"}, "use_jev": {"type": "boolean"}}
_COST = {k: {"type": "number"} for k in lc.COST}
TOOLS += [
    _t("post_design", "Create or re-version a design (scored, logged, tagged).", _ART, ("text",)),
    _t("patch_design", "Update a design: new text is re-scored; stages and work type are updated.", {"id": {"type": "integer"}, **_ART}, ("id",)),
    _t("post_brief", "Create or re-version a brief; design_id links it to its design.", {**_ART, "design_id": {"type": "integer"}}, ("text",)),
    _t("patch_brief", "Update a brief: new text is re-scored; stages and design link are updated.", {"id": {"type": "integer"}, "design_id": {"type": "integer"}, **_ART}, ("id",)),
    _t("start_execution", "Log that an agent started executing a brief.", {"brief_id": {"type": "integer"}, "head": {"type": "string"}}, ("brief_id",)),
    _t("patch_execution", "Add findings, adjustments or gaps (items) and cost to a running execution. Gaps back-reference the brief as missing_scope.",
       {"id": {"type": "integer"}, **_COST, "items": {"type": "array", "items": {"type": "object", "required": ["kind", "text"], "properties": {
           "kind": {"enum": list(lc.ITEM_KINDS)}, "text": {"type": "string"}, "category": {"type": "string"}, "severity": {"type": "string"}, "scope": {"enum": ["brief", "design"]}}}}}, ("id",)),
    _t("complete_execution", "Log completion of an execution with outcome, summary and cost.", {"id": {"type": "integer"}, "outcome": {"enum": list(lc.EXEC_OUTCOMES)}, "summary": {"type": "string"}, "metrics": {"type": "object"}, **_COST, "items": {"type": "array"}}, ("id", "outcome")),
    {"name": "outcomes", "description": "Up-front brief rating vs realised execution (done rate, cost, gaps, adjustments), sliced.",
     "inputSchema": {"type": "object", "properties": {"by": {"enum": sorted(lc.SLICES)}}}},
    {"name": "plan_cost", "description": "A plan's design/brief ratings mapped to executions and cost.",
     "inputSchema": {"type": "object", "required": ["project", "plan"], "properties": {"project": {"type": "string"}, "plan": {"type": "string"}}}},
]


def lifecycle_call(name: str, a: dict):
    if name in ("post_design", "post_brief"):
        return lc.put_artifact(name.split("_")[1], a)
    if name in ("patch_design", "patch_brief"):
        return lc.put_artifact(name.split("_")[1], {**a, "_patch": True}, int(a["id"]))
    if name == "start_execution":
        return lc.start_execution(int(a["brief_id"]), a)
    if name == "patch_execution":
        return lc.patch_execution(int(a["id"]), a)
    if name == "complete_execution":
        return lc.complete_execution(int(a["id"]), a)
    if name == "outcomes":
        return lc.outcomes(a.get("by", "project"))
    if name == "plan_cost":
        return lc.plan_cost(a["project"], a["plan"])
    raise KeyError(name)


LIFECYCLE = {"post_design", "patch_design", "post_brief", "patch_brief", "start_execution", "patch_execution", "complete_execution", "outcomes", "plan_cost"}


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
    if name in LIFECYCLE:
        return json.dumps(lifecycle_call(name, a), default=str)
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
            except (Exception, SystemExit) as e:  # includes lifecycle.Bad
                res = {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
        elif m == "ping":
            res = {}
        else:
            return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": f"method not found: {m}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": i, "error": {"code": -32603, "message": str(e)}}
    return {"jsonrpc": "2.0", "id": i, "result": res}


ROUTES = [  # (method, pattern, handler(body, query, *ids))
    ("POST", r"/v1/(design|brief)s", lambda b, qs, k: lc.put_artifact(k, b)),
    ("PATCH", r"/v1/(design|brief)s/(\d+)", lambda b, qs, k, i: lc.put_artifact(k, {**b, "_patch": True}, int(i))),
    ("GET", r"/v1/(design|brief)s/(\d+)", lambda b, qs, k, i: lc.get(k, int(i))),
    ("POST", r"/v1/briefs/(\d+)/executions", lambda b, qs, i: lc.start_execution(int(i), b)),
    ("PATCH", r"/v1/executions/(\d+)", lambda b, qs, i: lc.patch_execution(int(i), b)),
    ("POST", r"/v1/executions/(\d+)/complete", lambda b, qs, i: lc.complete_execution(int(i), b)),
    ("GET", r"/v1/executions/(\d+)", lambda b, qs, i: lc.get("execution", int(i))),
    ("GET", r"/v1/outcomes", lambda b, qs: lc.outcomes(qs.get("by", "project"))),
    ("GET", r"/v1/plans/([^/]+)/([^/]+)/cost", lambda b, qs, p, n: lc.plan_cost(p, n)),
]


class NotFound(Exception):
    pass


def route(method: str, path: str, body: dict, qs: dict):
    import re
    for m, pat, fn in ROUTES:
        mm = re.fullmatch(pat, path)
        if m == method and mm:
            return fn(body, qs, *mm.groups())
    raise NotFound(path)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code: int, body: bytes = b"", ctype: str = "application/json"):
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def _auth(self) -> bool:
        tok = os.environ.get("WORKFLOW_QUALITY_TOKEN")
        if tok and self.headers.get("Authorization") != f"Bearer {tok}":
            self._send(401, b'{"error":"unauthorized"}')
            return False
        return True

    def _rest(self, method: str):
        if not self._auth():
            return
        u = urlparse(self.path)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}") if method in ("POST", "PATCH") else {}
            res = route(method, u.path.rstrip("/"), body, {k: v[0] for k, v in parse_qs(u.query).items()})
        except json.JSONDecodeError:
            return self._send(400, b'{"error":"bad json"}')
        except lc.Bad as e:
            return self._send(400, json.dumps({"error": str(e)}).encode())
        except NotFound:
            return self._send(404, b'{"error":"not found"}')
        except Exception as e:  # keep the service up; report the failure to the caller
            return self._send(500, json.dumps({"error": f"{type(e).__name__}: {e}"}).encode())
        self._send(201 if method == "POST" else 200, json.dumps(res, default=str).encode())

    def do_PATCH(self):
        self._rest("PATCH")

    def do_POST(self):
        if self.path.startswith("/v1/"):
            return self._rest("POST")
        if not self._auth():
            return
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
        if self.path.startswith("/v1/"):
            return self._rest("GET")
        self._send(405)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    print(f"workflow-quality MCP on http://{a.host}:{a.port}/mcp  ledger={q.store_dir()}  jev={'on' if os.environ.get('TYPESAFE_API_KEY') else 'off'}", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
