"""Build a compact Jev snapshot from normalized extract JSON."""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

FIRST_USER_MAX = 800
TAIL_USER_MAX = 800
TAIL_USER_COUNT = 3
SPAWN_MAX = 10
SPAWN_DESC_MAX = 120
SNAPSHOT_TOKEN_HARD_CAP = 8000

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}", re.I),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|password)\s*[:=]\s*\S+"),
)


def _redact_secrets(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def _truncate(text: str, max_len: int) -> str:
    text = _redact_secrets(text.strip())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _project_basename(project_path: str | None) -> str:
    if not project_path:
        return ""
    return os.path.basename(project_path.rstrip(os.sep)) or project_path


def _tool_histogram(data: dict[str, Any]) -> dict[str, int]:
    session = data.get("session", {})
    hist: dict[str, int] = dict(session.get("parent_tool_counts") or {})
    for sa in data.get("subagents") or []:
        for tool, cnt in (sa.get("tool_counts") or {}).items():
            hist[tool] = hist.get(tool, 0) + int(cnt)
    return dict(sorted(hist.items(), key=lambda x: -x[1]))


def _spawn_skim(spawns: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for s in spawns[:SPAWN_MAX]:
        desc = _truncate(str(s.get("description") or ""), SPAWN_DESC_MAX)
        if not desc:
            continue
        entry: dict[str, str] = {"description": desc}
        model = s.get("model")
        if model:
            entry["model"] = str(model)
        out.append(entry)
    return out


def build_snapshot_state(data: dict[str, Any]) -> dict[str, Any]:
    """Return Jev `state` object from normalized extract JSON."""
    session = data.get("session", {})
    queries = data.get("user_queries") or []
    spawns = data.get("agent_spawns") or []

    first_user = ""
    if queries:
        first_user = _truncate(str(queries[0].get("text") or ""), FIRST_USER_MAX)

    tail: list[str] = []
    for q in queries[1 : 1 + TAIL_USER_COUNT]:
        t = _truncate(str(q.get("text") or ""), TAIL_USER_MAX)
        if t:
            tail.append(t)

    state: dict[str, Any] = {
        "source": data.get("source", ""),
        "session_id": session.get("id", ""),
        "wall_seconds": session.get("wall_seconds"),
        "project": _project_basename(session.get("project_path")),
        "first_user_message": first_user,
        "user_messages_tail": tail,
        "tool_histogram": _tool_histogram(data),
        "spawn_descriptions": [s["description"] for s in _spawn_skim(spawns)],
        "counts": {
            "user_queries": len(queries),
            "parent_tool_turns": int(session.get("parent_tool_turns") or 0),
            "subagents": int(session.get("subagent_count") or len(data.get("subagents") or [])),
            "api_calls": session.get("api_calls"),
        },
    }

    _enforce_token_cap(state)
    return state


def estimate_snapshot_tokens(state: dict[str, Any]) -> int:
    """Rough token estimate for budgeting (chars / 4)."""
    return max(1, len(json.dumps(state, ensure_ascii=False)) // 4)


def _enforce_token_cap(state: dict[str, Any]) -> None:
    while estimate_snapshot_tokens(state) > SNAPSHOT_TOKEN_HARD_CAP:
        if state.get("user_messages_tail"):
            state["user_messages_tail"] = state["user_messages_tail"][:-1]
            continue
        if len(state.get("spawn_descriptions") or []) > 1:
            state["spawn_descriptions"] = state["spawn_descriptions"][:-1]
            continue
        first = state.get("first_user_message") or ""
        if len(first) > 200:
            state["first_user_message"] = _truncate(first, len(first) // 2)
            continue
        break


def snapshot_hash(state: dict[str, Any]) -> str:
    payload = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
