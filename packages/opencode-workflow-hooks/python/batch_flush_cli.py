#!/usr/bin/env python3
"""Stdin JSON PostToolBatch-shaped payload → batch aggregator flush (plugin spawn target)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from batch_aggregator import OpenCodeBatchAggregator, repo_root

DEFAULT_LOG = repo_root() / "tools" / "driver" / ".jev-signal-log.jsonl"


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return
    payload = json.loads(raw)
    log_path = Path(os.environ.get("WORKFLOW_JEV_SIGNAL_LOG", DEFAULT_LOG))
    agg = OpenCodeBatchAggregator(log_path=log_path, cwd=payload.get("cwd"))
    session_id = str(payload.get("session_id") or "")
    transcript_path = str(payload.get("transcript_path") or "")
    for tc in payload.get("tool_calls") or []:
        agg.on_tool_execute_after(
            session_id=session_id,
            tool=str(tc.get("tool_name") or "unknown"),
            call_id=str(tc.get("tool_use_id") or ""),
            output=str(tc.get("tool_response") or ""),
        )
    agg.flush_step(session_id=session_id, transcript_path=transcript_path)


if __name__ == "__main__":
    main()
