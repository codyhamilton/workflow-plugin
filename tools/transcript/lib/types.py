"""Normalized types for transcript parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionSummary:
    source: str
    session_id: str
    external_url: str | None
    project_path: str | None
    start_time_iso: str
    subagent_count: int
    bytes: int


@dataclass
class SessionRef:
    source: str
    session_id: str
    project_path: str | None
    storage_path: str  # parent jsonl or session dir


@dataclass
class SearchHit:
    agent_id: str
    msg_idx: int
    role: str
    text_snippet: str


@dataclass
class NormalizedSession:
    source: str
    session: dict[str, Any]
    agent_spawns: list[dict[str, Any]] = field(default_factory=list)
    subagents: list[dict[str, Any]] = field(default_factory=list)
    user_queries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "session": self.session,
            "agent_spawns": self.agent_spawns,
            "subagents": self.subagents,
            "user_queries": self.user_queries,
        }
