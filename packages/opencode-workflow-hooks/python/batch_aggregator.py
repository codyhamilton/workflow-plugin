#!/usr/bin/env python3
"""Aggregate OpenCode tool.execute.after into PostToolBatch-shaped probes.

Calls shared Jev `process_hook_input` and optional analytics dual-write.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    override = os.environ.get("WORKFLOW_REPO_ROOT")
    if override:
        return Path(override).resolve()
    # packages/opencode-workflow-hooks/python/this_file.py → repo is parents[3]
    return Path(__file__).resolve().parents[3]


def _ensure_research_paths() -> None:
    root = repo_root()
    jev = root / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs"
    sink = root / "docs/lab/RESEARCH/2026-09-30-durable-analytics-sink/proofs"
    for p in (jev, sink):
        s = str(p)
        if p.is_dir() and s not in sys.path:
            sys.path.insert(0, s)


_ensure_research_paths()

from post_tool_batch_signal import process_hook_input  # noqa: E402
from dual_write_sink import emit_from_jev_signal_row  # noqa: E402


@dataclass
class _SessionBatch:
    tools: list[dict[str, Any]] = field(default_factory=list)

    def record(self, tool: str, call_id: str, *, title: str = "", output_preview: str = "") -> None:
        self.tools.append(
            {
                "tool_name": tool,
                "tool_use_id": call_id,
                "tool_input": {},
                "tool_response": output_preview[:500] if output_preview else title,
            }
        )

    def clear(self) -> None:
        self.tools.clear()


class OpenCodeBatchAggregator:
    """Collect per-tool results; flush once per model step (explicit flush_step)."""

    def __init__(self, *, log_path: Path, cwd: str | None = None) -> None:
        self._log_path = log_path
        self._cwd = cwd or str(Path.cwd())
        self._sessions: dict[str, _SessionBatch] = {}

    def on_tool_execute_after(
        self,
        *,
        session_id: str,
        tool: str,
        call_id: str,
        title: str = "",
        output: str = "",
    ) -> None:
        batch = self._sessions.setdefault(session_id, _SessionBatch())
        batch.record(tool, call_id, title=title, output_preview=output)

    def flush_step(
        self,
        *,
        session_id: str,
        agent_id: str | None = None,
        transcript_path: str = "",
    ) -> dict[str, Any] | None:
        batch = self._sessions.get(session_id)
        if batch is None or not batch.tools:
            return None
        payload: dict[str, Any] = {
            "hook_event_name": "PostToolBatch",
            "session_id": session_id,
            "agent_id": agent_id,
            "transcript_path": transcript_path,
            "cwd": self._cwd,
            "tool_calls": list(batch.tools),
        }
        batch.clear()
        entry = process_hook_input(payload, log_path=self._log_path)
        gate = entry.get("gate") or {}
        if gate.get("band_exit") or gate.get("handoff_signal") or gate.get("escalate"):
            emit_from_jev_signal_row(entry, local_path=None)
        return entry


def simulate_model_steps(
    aggregator: OpenCodeBatchAggregator,
    *,
    session_id: str,
    steps: int,
    tool: str = "bash",
    transcript_path: str = "",
) -> dict[str, Any] | None:
    """One tool per model step — turn proxy equals step count when transcript absent."""
    last: dict[str, Any] | None = None
    for i in range(steps):
        aggregator.on_tool_execute_after(
            session_id=session_id,
            tool=tool,
            call_id=f"call-{i}",
            title=f"tool {tool}",
            output="ok",
        )
        last = aggregator.flush_step(
            session_id=session_id,
            transcript_path=transcript_path,
        )
    return last
