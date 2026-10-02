#!/usr/bin/env python3
"""Harness-neutral session event log: user prompts and tool calls, one JSONL file per session.

Wired as a hook command (stdin = hook payload JSON). Never blocks or fails the agent: always exits 0.
Store: $WORKFLOW_HOOKLOG_DIR or ~/.local/share/workflow-plugin/hooklog/<harness>/<session_id>.jsonl
Local only. Secrets are pattern-redacted and large fields truncated before writing.

Row (v=1): {v, ts, harness, session_id, hook_event, kind: user_prompt|tool_call|tool_pre|batch_end|step|agent_text|stop|event,
            cwd, text?, tool_name?, tool_use_id?, input?, output?, ok?}
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

MAX_PROMPT = 20000
MAX_FIELD = 2000
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9\-]{10,}"
    r"|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
    r"|(?i:bearer)\s+[A-Za-z0-9._\-]{20,}|(?i:api[_-]?key|token|secret|password)\s*[=:]\s*\S{8,})")
SECRET_KEY = re.compile(r"(?i)(authorization|cookie|api[_-]?key|token$|secret|password|credential)")


def store_dir() -> Path:
    return Path(os.environ.get("WORKFLOW_HOOKLOG_DIR") or Path.home() / ".local/share/workflow-plugin/hooklog")


def scrub(text: str, limit: int) -> str:
    text = SECRET.sub("[REDACTED]", text)
    return text if len(text) <= limit else text[:limit] + f"…[+{len(text) - limit} chars]"


def clip(v: Any, limit: int = MAX_FIELD) -> Any:
    """Truncate every string leaf; keep structure so tool inputs stay inspectable."""
    if isinstance(v, str):
        decoded = _maybe_json(v)
        if isinstance(decoded, (dict, list)):
            return clip(decoded, limit)  # encoded Cursor payloads must not bypass key redaction
        return scrub(v, limit)
    if isinstance(v, dict):
        return {scrub(str(k), limit): "[REDACTED]" if SECRET_KEY.search(str(k)) else clip(x, limit)
                for k, x in list(v.items())[:40]}
    if isinstance(v, list):
        return [clip(x, limit) for x in v[:40]]
    return v


def _first(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return None


_STEP = re.compile(r"-(\d+)-[a-z0-9]+$")


def _maybe_json(v: Any) -> Any:
    """Cursor sends tool_input/tool_output as JSON-encoded strings."""
    if isinstance(v, str) and v[:1] in "{[":
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            pass
    return v


def detect_harness(p: dict[str, Any]) -> str:
    """`--harness auto`: Cursor payloads carry cursor_version / conversation_id / workspace_roots; Claude's carry transcript_path."""
    if p.get("cursor_version") or p.get("conversation_id") or (p.get("workspace_roots") and not p.get("transcript_path")):
        return "cursor"
    return "claude"


def normalize(harness: str, p: dict[str, Any]) -> dict[str, Any] | None:
    """Preserve every named event; lifecycle/unknown shapes become bounded `event` rows."""
    ev = str(_first(p, "hook_event_name", "event") or "")
    if not ev:
        return None
    sid = str(_first(p, "session_id", "conversation_id", "sessionID") or "unknown")
    cwd = _first(p, "cwd") or (p.get("workspace_roots") or [None])[0]
    row: dict[str, Any] = {"v": 1, "ts": time.time(), "harness": harness, "session_id": scrub(sid, MAX_FIELD),
                           "hook_event": scrub(ev, MAX_FIELD), "cwd": clip(cwd)}
    for key in ("agent_id", "generation_id", "turn_id", "source"):
        if p.get(key):
            row[key] = clip(p[key])
    if p.get("subagent_id"):
        row["agent_id"] = clip(p["subagent_id"])
    low = ev.lower()
    if p.get("source") == "bus":
        row.update(kind="event")  # tool/shell callbacks can also appear on the bus
    elif low in ("userpromptsubmit", "beforesubmitprompt", "chat.message"):
        row.update(kind="user_prompt", text=scrub(str(_first(p, "prompt", "text") or ""), MAX_PROMPT))
    elif low in ("pretooluse", "tool.execute.before", "posttooluse", "posttoolusefailure", "tool.execute.after",
                 "afterfileedit", "aftertabfileedit", "aftershellexecution", "aftermcpexecution"):
        name = _first(p, "tool_name")
        inp = _maybe_json(_first(p, "tool_input"))
        out = _maybe_json(_first(p, "tool_response", "tool_output", "result_json", "output", "result"))
        if low == "aftershellexecution":
            name, inp = name or "Shell", inp or {"command": p.get("command")}
        elif low in ("afterfileedit", "aftertabfileedit"):
            name, inp = name or "Edit", inp or {"file_path": p.get("file_path"), "edits": p.get("edits")}
        elif low == "aftermcpexecution":
            name = name or "MCP"
        row.update(kind="tool_pre" if low in ("pretooluse", "tool.execute.before") else "tool_call",
                   tool_name=clip(name), tool_use_id=clip(_first(p, "tool_use_id", "tool_call_id")),
                   input=clip(inp))
        if row["kind"] == "tool_call":
            row["ok"] = low != "posttoolusefailure"
        if out is not None:
            row["output"] = clip(out if isinstance(out, (str, dict, list)) else str(out))
    elif low == "posttoolbatch":
        # turn boundary: one model step's parallel tool calls have all resolved
        ids = [c.get("tool_use_id") for c in (p.get("tool_calls") or []) if isinstance(c, dict)]
        row.update(kind="batch_end", tool_use_ids=clip(ids))
    elif low == "afteragentthought":
        # Cursor: fires once per model step; generation_id ends "-<step>-<rand>", a direct step counter
        m = _STEP.search(str(p.get("generation_id") or ""))
        row.update(kind="step", step=int(m.group(1)) if m else None, text=scrub(str(p.get("text") or ""), 500))
    elif low in ("afteragentresponse", "messagedisplay", "experimental.text.complete"):
        row.update(kind="agent_text", text=scrub(str(p.get("text") or ""), MAX_FIELD))
    elif low == "stop":
        row.update(kind="stop")
    else:
        row.update(kind="event")
    # Keep native details for every surface, including lifecycle, bus and pre-action hooks.
    row["data"] = clip(p)
    return row


def append(row: dict[str, Any]) -> Path:
    d = store_dir() / row["harness"]
    d.mkdir(parents=True, exist_ok=True)
    path = d / (re.sub(r"[^A-Za-z0-9_.\-]", "_", row["session_id"]) + ".jsonl")
    line = json.dumps(row, ensure_ascii=False, default=str) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(line)
    return path


def read_session(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn write must not poison the session
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    rec = sub.add_parser("record", help="read a hook payload on stdin and append it")
    rec.add_argument("--harness", required=True, choices=["auto", "claude", "cursor", "opencode", "codex"])
    rec.add_argument("--event", help="registration event name (also used for Cursor's permissive response)")
    sub.add_parser("ls", help="list sessions with row counts")
    show = sub.add_parser("show", help="print a session's rows")
    show.add_argument("path")
    args = ap.parse_args()
    if args.cmd == "record":
        payload: dict[str, Any] = {}
        try:
            if os.environ.get("WORKFLOW_HOOKLOG", "").lower() in ("0", "off", "false"):
                raise SystemExit(0)
            parsed = json.loads(sys.stdin.read() or "{}")
            if not isinstance(parsed, dict):
                raise ValueError("hook payload must be an object")
            payload = parsed
            if args.event:
                payload["hook_event_name"] = args.event
            if args.harness == "auto":
                args.harness = detect_harness(payload)
            row = normalize(args.harness, payload)
            if row:
                append(row)
        except SystemExit:
            pass
        except Exception as exc:  # never break the agent
            if os.environ.get("WORKFLOW_HOOKLOG_DEBUG"):
                print(f"hooklog: {exc}", file=sys.stderr)
        if args.harness == "cursor":
            ev = str(args.event or payload.get("hook_event_name") or "").lower()
            if ev in ("pretooluse", "subagentstart", "beforeshellexecution", "beforemcpexecution",
                      "beforereadfile", "beforetabfileread"):
                print('{"permission": "allow"}')
            elif ev == "beforesubmitprompt":
                print('{"continue": true}')
            else:
                print('{}')
        return 0
    if args.cmd == "ls":
        for f in sorted(store_dir().glob("*/*.jsonl")):
            print(f"{len(read_session(f)):6d}  {f}")
    elif args.cmd == "show":
        for r in read_session(Path(args.path)):
            print(json.dumps(r, ensure_ascii=False))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
