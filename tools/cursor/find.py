#!/usr/bin/env python3
"""
find.py — Discover Cursor agent-transcript sessions for a project.

Usage:
    python tools/cursor/find.py [PROJECT_PATH] [--format text|json]

PROJECT_PATH defaults to cwd. The Cursor project hash is derived from the
project path using the same convention Cursor uses: replace '/' with '-'.

Output columns (text mode):
    SESSION_ID  START_TIME  SUBAGENTS  PARENT_SIZE_BYTES
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


CURSOR_PROJECTS = os.path.expanduser("~/.cursor/projects")


def project_hash(project_path: str) -> str:
    """Derive Cursor project hash from an absolute project path."""
    path = os.path.abspath(os.path.expanduser(project_path))
    # Cursor strips the leading slash and replaces '/' with '-'
    return path.lstrip("/").replace("/", "-")


def find_sessions(project_path: str) -> list[dict]:
    """Return list of session dicts for a project path, sorted by start time."""
    phash = project_hash(project_path)
    transcripts_dir = os.path.join(CURSOR_PROJECTS, phash, "agent-transcripts")

    if not os.path.isdir(transcripts_dir):
        sys.exit(
            f"No Cursor agent-transcripts found for project '{project_path}'\n"
            f"  Expected: {transcripts_dir}\n"
            f"  Project hash: {phash}"
        )

    sessions = []
    for entry in os.scandir(transcripts_dir):
        if not entry.is_dir():
            continue
        session_id = entry.name
        session_dir = entry.path

        # Parent JSONL
        parent_jsonl = os.path.join(session_dir, f"{session_id}.jsonl")
        parent_size = os.path.getsize(parent_jsonl) if os.path.isfile(parent_jsonl) else 0

        # Subagents
        subagents_dir = os.path.join(session_dir, "subagents")
        subagent_files = []
        if os.path.isdir(subagents_dir):
            subagent_files = [
                os.path.join(subagents_dir, f)
                for f in os.listdir(subagents_dir)
                if f.endswith(".jsonl")
            ]

        subagent_count = len(subagent_files)

        # Start time: earliest mtime across all files (parent + subagents)
        all_files = ([parent_jsonl] if parent_size else []) + subagent_files
        if all_files:
            start_mtime = min(os.path.getmtime(f) for f in all_files)
        else:
            start_mtime = os.path.getmtime(session_dir)

        sessions.append(
            {
                "session_id": session_id,
                "project_hash": phash,
                "session_dir": session_dir,
                "start_time": start_mtime,
                "start_time_iso": datetime.fromtimestamp(
                    start_mtime, tz=timezone.utc
                ).isoformat(),
                "subagent_count": subagent_count,
                "parent_size_bytes": parent_size,
                "has_parent_jsonl": parent_size > 0,
            }
        )

    sessions.sort(key=lambda s: s["start_time"])
    return sessions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover Cursor agent-transcript sessions for a project."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to the project directory (default: cwd)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    sessions = find_sessions(args.project_path)

    if not sessions:
        print("No sessions found.", file=sys.stderr)
        sys.exit(0)

    if args.format == "json":
        print(json.dumps(sessions, indent=2))
        return

    # Text output
    header = f"{'SESSION_ID':<38} {'START_TIME':<26} {'SUBAGENTS':>9} {'PARENT_BYTES':>13}"
    print(header)
    print("-" * len(header))
    for s in sessions:
        print(
            f"{s['session_id']:<38} {s['start_time_iso']:<26} "
            f"{s['subagent_count']:>9} {s['parent_size_bytes']:>13}"
        )

    print(f"\n{len(sessions)} session(s) for project hash: {sessions[0]['project_hash']}")


if __name__ == "__main__":
    main()
