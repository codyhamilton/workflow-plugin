"""Project-hash conventions and storage roots."""

from __future__ import annotations

import os

CLAUDE_ROOT = os.path.expanduser("~/.claude/projects")
CURSOR_ROOT = os.path.expanduser("~/.cursor/projects")


def claude_project_hash(project_path: str) -> str:
    """Claude: cwd path with every '/' replaced by '-' (leading / -> leading -)."""
    return os.path.abspath(os.path.expanduser(project_path)).replace("/", "-")


def cursor_project_hash(project_path: str) -> str:
    """Cursor: strip leading '/', then replace '/' with '-'."""
    path = os.path.abspath(os.path.expanduser(project_path))
    return path.lstrip("/").replace("/", "-")


def reverse_claude_hash(hash_name: str) -> str | None:
    """Best-effort reverse of claude_project_hash. Unreliable when path segments contain hyphens."""
    if not hash_name.startswith("-"):
        return None
    return "/" + hash_name[1:].replace("-", "/")


def reverse_cursor_hash(hash_name: str) -> str | None:
    if hash_name.startswith("-"):
        return None
    return "/" + hash_name.replace("-", "/")


def guess_project_path_from_hash(hash_name: str) -> str | None:
    return reverse_claude_hash(hash_name) or reverse_cursor_hash(hash_name)
