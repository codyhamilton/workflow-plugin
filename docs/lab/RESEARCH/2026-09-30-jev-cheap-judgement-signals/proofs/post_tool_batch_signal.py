#!/usr/bin/env python3
"""Opt-in PostToolBatch hook: append signal JSONL (no Jev, exit 0 always).

Install: point a Claude Code PostToolBatch command hook at this script.
See proofs/hooks-settings-snippet.json and run_hook_probe.sh.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gate_thresholds import evaluate_gate

DEFAULT_LOG = Path(__file__).resolve().parents[5] / "tools" / "driver" / ".jev-signal-log.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(session_id: str, agent_id: str | None) -> Path:
    base = Path(
        os.environ.get(
            "WORKFLOW_SIGNAL_STATE_DIR",
            Path.home() / ".cache" / "workflow-plugin" / "signal-state",
        )
    )
    key = f"{session_id}:{agent_id or 'main'}"
    return base / f"{key}.json"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"post_tool_batch_count": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def _peak_ctx_from_transcript(transcript_path: str) -> int | None:
    """Best-effort scan of Claude Code JSONL usage fields (may lag hook)."""
    path = Path(transcript_path)
    if not path.is_file():
        return None
    peak = 0
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                usage = None
                if row.get("type") == "assistant":
                    usage = (row.get("message") or {}).get("usage")
                if not usage and isinstance(row.get("usage"), dict):
                    usage = row["usage"]
                if not usage:
                    continue
                for key in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
                    peak = max(peak, int(usage.get(key) or 0))
    except OSError:
        return None
    return peak or None


def _count_assistant_turns(transcript_path: str) -> int | None:
    path = Path(transcript_path)
    if not path.is_file():
        return None
    count = 0
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("type") == "assistant" and not row.get("isSidechain"):
                    count += 1
    except OSError:
        return None
    return count


def process_hook_input(payload: dict[str, Any], *, log_path: Path) -> dict[str, Any]:
    session_id = str(payload.get("session_id") or "")
    agent_id = payload.get("agent_id")
    transcript_path = str(payload.get("transcript_path") or "")
    tool_calls = payload.get("tool_calls") or []

    state_file = _state_path(session_id, agent_id)
    state = _load_state(state_file)
    batch_count = int(state.get("post_tool_batch_count") or 0) + 1
    state["post_tool_batch_count"] = batch_count
    _save_state(state_file, state)

    transcript_bytes = None
    if transcript_path and Path(transcript_path).is_file():
        transcript_bytes = Path(transcript_path).stat().st_size

    transcript_turns = _count_assistant_turns(transcript_path) if transcript_path else None
    api_turns = transcript_turns if transcript_turns is not None else batch_count
    peak_ctx = _peak_ctx_from_transcript(transcript_path) if transcript_path else None

    gate = evaluate_gate(
        api_turns=api_turns,
        peak_ctx_tokens=peak_ctx,
        transcript_bytes=transcript_bytes,
    )

    entry: dict[str, Any] = {
        "ts": _utc_now(),
        "kind": "post_tool_batch",
        "hook_event_name": payload.get("hook_event_name", "PostToolBatch"),
        "session_id": session_id,
        "agent_id": agent_id,
        "transcript_path": transcript_path or None,
        "transcript_bytes": transcript_bytes,
        "api_turns_proxy": api_turns,
        "api_turns_source": "transcript_assistant" if transcript_turns is not None else "post_tool_batch_count",
        "post_tool_batch_count": batch_count,
        "peak_ctx_tokens_estimate": peak_ctx,
        "tool_calls_in_batch": len(tool_calls),
        "gate": gate.to_dict(),
        "cwd": payload.get("cwd"),
        "permission_mode": payload.get("permission_mode"),
    }

    if gate.band_exit or gate.handoff_signal or gate.escalate:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        print("post_tool_batch_signal: empty stdin", file=sys.stderr)
        sys.exit(0)
    payload = json.loads(raw)
    log_path = Path(os.environ.get("WORKFLOW_JEV_SIGNAL_LOG", DEFAULT_LOG))
    process_hook_input(payload, log_path=log_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
