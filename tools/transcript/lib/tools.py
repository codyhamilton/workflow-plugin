"""Canonical tool-name mapping across harnesses."""

from __future__ import annotations

from collections import Counter

# Harness-native name -> canonical name
_CANONICAL: dict[str, str] = {
    # shell
    "Bash": "shell",
    "Shell": "shell",
    # spawn
    "Agent": "spawn",
    "Task": "spawn",
    # read
    "Read": "read",
    "Glob": "glob",
    "Grep": "grep",
    # write / edit
    "Write": "write",
    "Edit": "edit",
    "StrReplace": "edit",
    "Delete": "delete",
    # search / web
    "WebSearch": "web_search",
    "WebFetch": "web_fetch",
    # misc
    "TodoWrite": "todo",
    "AskQuestion": "ask",
    "SwitchMode": "switch_mode",
}

# Aliases for --tool flag
_TOOL_ALIASES: dict[str, str] = {
    "all": "all",
    "claude": "claude-code",
    "claude-code": "claude-code",
    "cursor": "cursor",
}


def canonical_name(raw: str) -> str:
    return _CANONICAL.get(raw, raw.lower().replace(" ", "_"))


def normalize_counts(raw_counts: dict[str, int]) -> dict[str, int]:
    out: Counter[str] = Counter()
    for name, count in raw_counts.items():
        out[canonical_name(name)] += count
    return dict(out)


def resolve_tool_flag(value: str | None) -> str:
    if not value or value == "all":
        return "all"
    key = value.lower().strip()
    if key not in _TOOL_ALIASES:
        raise ValueError(f"Unknown tool '{value}'. Use: all, claude-code, cursor")
    return _TOOL_ALIASES[key]
