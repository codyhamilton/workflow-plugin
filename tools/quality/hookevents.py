"""Hook events in the quality ledger: ingest (raw hook payloads or normalised hooklog rows), query, and join to plans
through the harness conversation id (hook session_id == scores.session_id == executions/events.conversation_id)."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooklog"))
import hooklog  # noqa: E402
import quality as q  # noqa: E402
from lifecycle import Bad  # noqa: E402

COLS = ("ts", "harness", "session_id", "hook_event", "kind", "cwd", "agent_id", "generation_id", "tool_name", "tool_use_id", "ok", "text", "input", "output")
KINDS = ("user_prompt", "tool_call", "batch_end", "step", "agent_text", "stop", "event")  # event = opencode bus and Claude lifecycle rows (data in extra)
MAX_ROWS = 5000


def _js(v: Any) -> str | None:
    return None if v is None else json.dumps(hooklog.clip(v), ensure_ascii=False, default=str)


def need(qs: dict[str, str], key: str) -> str:
    if not qs.get(key):
        raise Bad(f"{key} required")
    return qs[key]


def rows_of(body: dict[str, Any]) -> list[dict[str, Any]]:
    """Accepts {rows:[...]}, {payload:{...}, harness?} (a raw hook payload, normalised here), or one normalised row."""
    if isinstance(body.get("rows"), list):
        return body["rows"]
    if isinstance(body.get("payload"), dict):
        h = body.get("harness") or "auto"
        h = hooklog.detect_harness(body["payload"]) if h == "auto" else h
        r = hooklog.normalize(h, body["payload"])
        return [r] if r else []
    return [body] if body.get("kind") else []


def ingest(rows: list[dict[str, Any]]) -> dict[str, int]:
    if len(rows) > MAX_ROWS:
        raise Bad(f"at most {MAX_ROWS} rows per request")
    out = {"inserted": 0, "duplicate": 0, "rejected": 0}
    with q.db() as c:
        for r in rows:
            if not isinstance(r, dict) or r.get("kind") not in KINDS or not r.get("session_id") or not r.get("harness") or not isinstance(r.get("ts"), (int, float)):
                out["rejected"] += 1
                continue
            key = hashlib.sha1(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()
            extra = {k: v for k, v in r.items() if k not in COLS and k != "v"}
            vals = [r.get("ts"), r["harness"], str(r["session_id"]), r.get("hook_event"), r["kind"], r.get("cwd"), r.get("agent_id"), r.get("generation_id"),
                    r.get("tool_name"), r.get("tool_use_id"), None if r.get("ok") is None else int(bool(r["ok"])),
                    hooklog.scrub(str(r["text"]), hooklog.MAX_PROMPT) if r.get("text") is not None else None, _js(r.get("input")), _js(r.get("output"))]
            cur = c.execute(f"INSERT OR IGNORE INTO hook_events({','.join(COLS)},extra,row_key) VALUES({','.join('?' * (len(COLS) + 2))})",
                            (*vals, _js(extra) if extra else None, key))
            out["inserted" if cur.rowcount else "duplicate"] += 1
    return out


def post(body: dict[str, Any]) -> dict[str, int]:
    return ingest(rows_of(body))


def events(session_id: str, kind: str | None = None, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
    sql, args = "SELECT * FROM hook_events WHERE session_id=?", [session_id]
    if kind:
        sql, args = sql + " AND kind=?", args + [kind]
    with q.db() as c:
        return [dict(r) for r in c.execute(sql + " ORDER BY ts, id LIMIT ? OFFSET ?", (*args, min(int(limit), 5000), int(offset)))]


def session(session_id: str) -> dict[str, Any]:
    """Hook activity for one conversation plus the plan artifacts and executions tied to it."""
    with q.db() as c:
        st = c.execute("SELECT MIN(ts) t0, MAX(ts) t1, COUNT(*) n, SUM(kind='user_prompt') prompts, SUM(kind='tool_call') tools, SUM(kind='tool_call' AND ok=0) tool_failures,"
                       " SUM(kind='step' OR kind='batch_end' OR kind='stop') boundaries, MIN(harness) harness, MIN(cwd) cwd FROM hook_events WHERE session_id=? AND agent_id IS NULL", (session_id,)).fetchone()
        top = c.execute("SELECT tool_name, COUNT(*) n FROM hook_events WHERE session_id=? AND kind='tool_call' GROUP BY 1 ORDER BY 2 DESC LIMIT 8", (session_id,)).fetchall()
        arts = c.execute("SELECT DISTINCT a.id, a.kind, a.project, a.plan, a.path FROM scores s JOIN artifacts a ON a.id=s.artifact_id WHERE s.session_id=?"
                         " UNION SELECT DISTINCT a.id, a.kind, a.project, a.plan, a.path FROM events e JOIN artifacts a ON a.id=e.artifact_id WHERE e.conversation_id=?",
                         (session_id, session_id)).fetchall()
        ex = c.execute("SELECT id, brief_id, started, ended, outcome, cost_usd FROM executions WHERE conversation_id=?", (session_id,)).fetchall()
    return {"session_id": session_id, "activity": dict(st), "top_tools": [dict(r) for r in top], "artifacts": [dict(r) for r in arts], "executions": [dict(r) for r in ex]}


def execution_activity(exec_id: int) -> dict[str, Any]:
    """Hook events inside an execution's window in its conversation (prompts, tool calls, failures, interventions)."""
    with q.db() as c:
        e = c.execute("SELECT id, brief_id, conversation_id, started, ended FROM executions WHERE id=?", (exec_id,)).fetchone()
        if not e:
            raise Bad(f"no execution {exec_id}")
        if not e["conversation_id"]:
            return {"execution": dict(e), "activity": None, "note": "execution has no conversation_id"}
        st = c.execute("SELECT COUNT(*) n, SUM(kind='user_prompt') prompts, SUM(kind='tool_call') tools, SUM(kind='tool_call' AND ok=0) tool_failures"
                       " FROM hook_events WHERE session_id=? AND agent_id IS NULL AND ts>=? AND ts<=?", (e["conversation_id"], e["started"], e["ended"] or time.time())).fetchone()
    return {"execution": dict(e), "activity": dict(st)}


def plan_sessions(project: str, plan: str) -> dict[str, Any]:
    """Conversations that scored artifacts or ran executions for a plan, with their hook activity."""
    with q.db() as c:
        ids = {r[0] for r in c.execute(
            "SELECT s.session_id FROM scores s JOIN artifacts a ON a.id=s.artifact_id WHERE a.project=? AND a.plan=?"
            " UNION SELECT e.conversation_id FROM executions e JOIN artifacts a ON a.id=e.brief_id WHERE a.project=? AND a.plan=?"
            " UNION SELECT ev.conversation_id FROM events ev JOIN artifacts a ON a.id=ev.artifact_id WHERE a.project=? AND a.plan=?", (project, plan) * 3) if r[0] and r[0] != "unknown"}
    return {"project": project, "plan": plan, "sessions": [session(i) for i in sorted(ids)]}
