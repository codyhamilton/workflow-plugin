#!/usr/bin/env python3
"""Opt-in SubagentStop hook: log unit-complete row (no Jev). Exit 0 always."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG = Path(__file__).resolve().parents[5] / "tools" / "driver" / ".jev-signal-log.jsonl"


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    payload = json.loads(raw)
    agent_path = payload.get("agent_transcript_path") or ""
    agent_bytes = Path(agent_path).stat().st_size if agent_path and Path(agent_path).is_file() else None
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "subagent_stop",
        "session_id": payload.get("session_id"),
        "agent_id": payload.get("agent_id"),
        "agent_type": payload.get("agent_type"),
        "agent_transcript_bytes": agent_bytes,
        "last_assistant_message_chars": len(payload.get("last_assistant_message") or ""),
    }
    log_path = Path(os.environ.get("WORKFLOW_JEV_SIGNAL_LOG", DEFAULT_LOG))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
