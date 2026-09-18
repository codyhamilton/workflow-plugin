"""Shared CLI utilities."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from .registry import REGISTRY
from .tools import resolve_tool_flag
from .types import NormalizedSession, SessionRef


def add_tool_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--tool",
        default="all",
        help="Harness filter: all (default), claude-code, cursor",
    )


def add_format_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def get_parsers(tool: str):
    try:
        resolved = resolve_tool_flag(tool)
    except ValueError as e:
        sys.exit(str(e))
    return REGISTRY.parsers_for(resolved)


def resolve_session_ref(
    session_ref: str,
    project_path: str | None,
    tool: str = "all",
) -> SessionRef:
    from .resolve import normalize_session_ref

    ref = normalize_session_ref(session_ref)
    parsers = get_parsers(tool)

    if ref == "latest":
        summaries = []
        for p in parsers:
            if project_path:
                summaries.extend(p.discover(project_path))
            else:
                summaries.extend(p.discover_all())
        if not summaries:
            sys.exit("No sessions found.")
        summaries.sort(key=lambda s: s.start_time_iso, reverse=True)
        best = summaries[0]
        parser = REGISTRY.get(best.source)
        return parser.resolve(best.session_id, best.project_path)

    last_err: Exception | None = None
    for parser in parsers:
        try:
            return parser.resolve(ref, project_path)
        except (SystemExit, KeyError, ValueError, FileNotFoundError) as e:
            last_err = e
            continue
    sys.exit(f"Session not found: {session_ref}" + (f" ({last_err})" if last_err else ""))


def extract_session(
    session_ref: str,
    project_path: str | None,
    tool: str = "all",
) -> NormalizedSession:
    ref = resolve_session_ref(session_ref, project_path, tool)
    parser = REGISTRY.get(ref.source)
    return parser.extract(ref)


def load_normalized_json(session: str | None, project: str | None, tool: str) -> dict:
    if session:
        return extract_session(session, project, tool).to_dict()
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit("No input: pipe extract.py output or use --session")
    return json.loads(raw)


def setup_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    # Ensure parsers are registered
    import parsers  # noqa: F401

    return root
