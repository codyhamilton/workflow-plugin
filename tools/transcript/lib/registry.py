"""Extensible parser registry."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import NormalizedSession, SearchHit, SessionRef, SessionSummary


@runtime_checkable
class TranscriptParser(Protocol):
    name: str

    def discover(
        self,
        project_path: str | None,
        *,
        match: str | None = None,
        since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]: ...

    def discover_all(
        self,
        *,
        match: str | None = None,
        since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]: ...

    def resolve(self, session_ref: str, project_path: str | None) -> SessionRef: ...

    def extract(self, ref: SessionRef) -> NormalizedSession: ...

    def search(
        self, ref: SessionRef, pattern: str, **opts: object
    ) -> list[SearchHit]: ...


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, TranscriptParser] = {}
        self._aliases: dict[str, str] = {}

    def register(self, parser: TranscriptParser, *aliases: str) -> None:
        self._parsers[parser.name] = parser
        for alias in aliases:
            self._aliases[alias.lower()] = parser.name

    def get(self, name: str) -> TranscriptParser:
        key = name.lower()
        resolved = self._aliases.get(key, key)
        if resolved not in self._parsers:
            raise KeyError(f"Unknown parser: {name}")
        return self._parsers[resolved]

    def all(self) -> list[TranscriptParser]:
        return list(self._parsers.values())

    def resolve_names(self, tool: str) -> list[str]:
        if tool == "all":
            return list(self._parsers.keys())
        return [self.get(tool).name]

    def parsers_for(self, tool: str) -> list[TranscriptParser]:
        return [self.get(n) for n in self.resolve_names(tool)]


REGISTRY = ParserRegistry()
