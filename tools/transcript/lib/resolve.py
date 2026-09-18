"""Session ref normalization helpers."""

from __future__ import annotations

import os
import re

SESSION_URL_RE = re.compile(
    r"(?:https?://)?claude\.ai/code/(session_[A-Za-z0-9]+)"
)
SESSION_SLUG_RE = re.compile(r"^(session_[A-Za-z0-9]+)$")
BRIDGE_ID_RE = re.compile(r"^(cse_[A-Za-z0-9]+)$")


def normalize_session_ref(ref: str) -> str:
    ref = ref.strip()
    if ref == "latest":
        return "latest"
    m = SESSION_URL_RE.search(ref)
    if m:
        return m.group(1)
    return ref


def extract_url_slug(text: str) -> str | None:
    m = SESSION_URL_RE.search(text)
    return m.group(1) if m else None


def scan_claude_sessions_for_slug(
    claude_root: str, slug: str
) -> list[tuple[str, str]]:
    """Return list of (session_id, jsonl_path) matching a session_01 slug."""
    matches: list[tuple[str, str]] = []
    if not os.path.isdir(claude_root):
        return matches
    for proj in os.listdir(claude_root):
        proj_dir = os.path.join(claude_root, proj)
        if not os.path.isdir(proj_dir):
            continue
        for fname in os.listdir(proj_dir):
            if not fname.endswith(".jsonl"):
                continue
            path = os.path.join(proj_dir, fname)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if slug in line:
                            session_id = fname[:-6]
                            matches.append((session_id, path))
                            break
            except OSError:
                continue
    return matches


def scan_claude_sessions_for_bridge(
    claude_root: str, bridge_id: str
) -> list[tuple[str, str]]:
    """Return list of (session_id, jsonl_path) matching a cse_ bridge ID."""
    matches: list[tuple[str, str]] = []
    if not os.path.isdir(claude_root):
        return matches
    needle = f'"bridgeSessionId":"{bridge_id}"'
    for proj in os.listdir(claude_root):
        proj_dir = os.path.join(claude_root, proj)
        if not os.path.isdir(proj_dir):
            continue
        for fname in os.listdir(proj_dir):
            if not fname.endswith(".jsonl"):
                continue
            path = os.path.join(proj_dir, fname)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    head = f.read(4096)
                    if needle in head or bridge_id in head:
                        session_id = fname[:-6]
                        matches.append((session_id, path))
            except OSError:
                continue
    return matches
