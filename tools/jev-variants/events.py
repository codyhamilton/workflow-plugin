"""Normalize a Claude Code or Cursor JSONL transcript into an ordered event stream.

Event kinds:
  {"kind": "user_prompt", "turn": N, "text": str}
  {"kind": "tool_batch", "turn": N, "calls": [{"name": str, "input": dict, "output": str|None}]}
`turn` is the 1-based count of assistant turns seen so far (Claude: distinct assistant message
ids; Cursor: assistant rows), so a prefix at checkpoint T is every event with turn <= T.
Cursor transcripts carry no tool results, so `output` is None there (HARNESS_FEATURES).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HARNESS_FEATURES: dict[str, set[str]] = {
    "claude": {"user_prompts", "tool_names", "tool_args", "tool_output_text", "assistant_text",
               "turn_index", "context_size", "repeat_counts", "file_targets"},
    "cursor": {"user_prompts", "tool_names", "tool_args", "assistant_text",
               "turn_index", "context_size", "repeat_counts", "file_targets"},
    # hooklog rows (tools/hooklog): outputs present where the harness hook supplies them; no assistant text
    "hooklog": {"user_prompts", "tool_names", "tool_args", "tool_output_text", "turn_index", "repeat_counts", "file_targets"},
}

_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
_QUERY = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
_SKIP_PREFIX = ("<command-name>", "<local-command", "<command-message>", "Caveat:")


def _clean_prompt(text: str) -> str:
    m = _QUERY.search(text)
    if m:
        text = m.group(1)
    return _REMINDER.sub("", text).strip()


def _result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def load_claude(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    turn = 0
    seen_ids: set[str] = set()
    batch_by_msg: dict[str, dict[str, Any]] = {}
    pending: dict[str, dict[str, Any]] = {}
    for line in path.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain"):
            continue
        t = d.get("type")
        msg = d.get("message") or {}
        content = msg.get("content")
        if t == "assistant":
            mid = msg.get("id") or d.get("uuid")
            if mid not in seen_ids:
                seen_ids.add(mid)
                turn += 1
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    batch = batch_by_msg.get(mid)
                    if batch is None:
                        batch = {"kind": "tool_batch", "turn": turn, "calls": []}
                        batch_by_msg[mid] = batch
                        events.append(batch)
                    call = {"name": b.get("name", ""), "input": b.get("input") or {}, "output": None}
                    batch["calls"].append(call)
                    pending[b.get("id", "")] = call
        elif t == "user":
            if isinstance(content, str):
                texts = [content]
            else:
                texts = []
                for b in content if isinstance(content, list) else []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        call = pending.get(b.get("tool_use_id", ""))
                        if call is not None:
                            call["output"] = _result_text(b.get("content"))
                    elif b.get("type") == "text":
                        texts.append(b.get("text", ""))
            for text in texts:
                if text.lstrip().startswith(_SKIP_PREFIX):
                    continue
                clean = _clean_prompt(text)
                if clean:
                    events.append({"kind": "user_prompt", "turn": turn, "text": clean})
    return _close(events, turn)


def _close(events: list[dict[str, Any]], turn: int) -> list[dict[str, Any]]:
    """Trailing text-only turns carry no event; mark the last so total_turns is exact."""
    if turn > max((e["turn"] for e in events), default=0):
        events.append({"kind": "final_reply", "turn": turn})
    return events


def load_cursor(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    turn = 0
    for line in path.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = d.get("role")
        content = (d.get("message") or {}).get("content") or []
        if role == "user":
            text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            clean = _clean_prompt(text)
            if clean:
                events.append({"kind": "user_prompt", "turn": turn, "text": clean})
        elif role == "assistant":
            turn += 1
            calls = [{"name": b.get("name", ""), "input": b.get("input") or {}, "output": None}
                     for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
            if calls:
                events.append({"kind": "tool_batch", "turn": turn, "calls": calls})
    return _close(events, turn)


BATCH_GAP_S = 1.5  # fallback only, for logs with no batch_end markers


def load_hooklog(path: Path) -> list[dict[str, Any]]:
    """Turn = one model response. Counted from hook boundaries:
      - `batch_end` (Claude PostToolBatch) closes a tool-calling turn; tool calls since the previous
        boundary belong to it;
      - `stop` closes the final text-only turn (verified live: Claude emits PostToolBatch per tool turn, then Stop after a final text reply that has no hook of its own);
      - `agent_text` alone is NOT a turn (a reply that precedes tool calls shares their turn);
      - Cursor `afterAgentThought` (kind `step`) fires once per model response, so each is a turn and
        the tool calls after it belong to it (verified against a real `agent -p` run);
      - logs with neither marker (including Codex) fall back to a time gap > BATCH_GAP_S between tool calls.
    Lifecycle/event and pre-tool rows are observations, not turn boundaries. Cursor's specific
    shell/MCP/edit hooks are ignored when the canonical postToolUse surface is present.
    Subagent rows (agent_id set) are excluded, as sidechains are for Claude transcripts."""
    rows = []
    for line in path.read_text(errors="ignore").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not r.get("agent_id"):
            rows.append(r)
    has_markers = any(r.get("kind") == "batch_end" for r in rows)
    has_steps = any(r.get("kind") == "step" for r in rows)
    cursor_has_post = any(r.get("harness") == "cursor" and r.get("hook_event", "").lower()
                          in ("posttooluse", "posttoolusefailure") for r in rows)
    events: list[dict[str, Any]] = []
    turn = 0
    pending: list[dict[str, Any]] = []   # tool calls awaiting a boundary
    active = False                        # anything since last boundary (for stop)
    last_ts: float | None = None

    def call(r: dict[str, Any]) -> dict[str, Any]:
        out = r.get("output")
        return {"name": r.get("tool_name") or "", "input": r.get("input") or {},
                "output": out if isinstance(out, str) else (json.dumps(out) if out is not None else None)}

    def flush() -> None:
        nonlocal turn, pending
        if pending:
            if not has_steps:
                turn += 1
            else:
                turn = max(turn, 1)  # tools before any step marker still belong to a turn
            events.append({"kind": "tool_batch", "turn": turn, "calls": pending})
            pending = []

    for r in rows:
        k = r.get("kind")
        if k == "user_prompt":
            flush()
            active = False
            if r.get("text"):
                events.append({"kind": "user_prompt", "turn": turn, "text": r["text"]})
        elif k == "tool_call":
            if r.get("harness") == "cursor" and r.get("hook_event", "").lower() == "aftertabfileedit":
                continue  # inline completions are not agent model turns
            if cursor_has_post and r.get("harness") == "cursor" and r.get("hook_event", "").lower() in (
                    "aftershellexecution", "aftermcpexecution", "afterfileedit"):
                continue
            ts = r.get("ts", 0.0)
            if not (has_markers or has_steps) and pending and last_ts is not None and ts - last_ts > BATCH_GAP_S:
                flush()
            pending.append(call(r))
            last_ts, active = ts, True
        elif k == "batch_end":
            flush()
            active = False
        elif k == "step":
            # Cursor afterAgentThought: one per model response; the tool calls that follow belong to it
            flush()
            turn += 1
            events.append({"kind": "step", "turn": turn})
            active = False
        elif k == "agent_text":
            active = True
        elif k == "stop":
            flush()
            if (active or has_markers) and not has_steps:  # Stop always follows a final model response
                turn += 1  # final text-only response
                events.append({"kind": "final_reply", "turn": turn})
            active = False
    flush()
    return events


def load_events(harness: str, path: str | Path) -> list[dict[str, Any]]:
    return {"claude": load_claude, "cursor": load_cursor, "hooklog": load_hooklog}[harness](Path(path))


def total_turns(events: list[dict[str, Any]]) -> int:
    return max((e["turn"] for e in events), default=0)
