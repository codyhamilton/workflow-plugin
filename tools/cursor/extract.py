#!/usr/bin/env python3
"""
extract.py — Extract structured data from a Cursor agent-transcript session.

Usage:
    python tools/cursor/extract.py SESSION_ID [PROJECT_PATH]

SESSION_ID: the UUID of the session (first few chars are enough if unambiguous)
PROJECT_PATH: path to the project directory (default: cwd)

Outputs a JSON document to stdout with:
  - session:      id, project_hash, parent_tool_counts, total_messages
  - task_calls:   ordered list of Task tool invocations found in parent
  - user_queries: genuine user queries (filtered from Cursor system messages)
  - subagents:    ordered-by-mtime list of subagent summaries

Pipe to other tools:
    python extract.py SESSION_ID | python stats.py
    python extract.py SESSION_ID | python iterate_analysis.py
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

CURSOR_PROJECTS = os.path.expanduser("~/.cursor/projects")


def project_hash(project_path: str) -> str:
    path = os.path.abspath(os.path.expanduser(project_path))
    return path.lstrip("/").replace("/", "-")


def resolve_session(phash: str, session_prefix: str) -> str:
    """Resolve a full session UUID from a prefix. Exits if ambiguous or missing."""
    transcripts_dir = os.path.join(CURSOR_PROJECTS, phash, "agent-transcripts")
    if not os.path.isdir(transcripts_dir):
        sys.exit(f"No agent-transcripts directory found: {transcripts_dir}")

    matches = [
        d for d in os.listdir(transcripts_dir)
        if os.path.isdir(os.path.join(transcripts_dir, d))
        and d.startswith(session_prefix)
    ]
    if not matches:
        sys.exit(f"No session matching '{session_prefix}' in {transcripts_dir}")
    if len(matches) > 1:
        sys.exit(f"Ambiguous session prefix '{session_prefix}': matches {matches}")
    return matches[0]


def _extract_text_from_content(content: list) -> str:
    """Concatenate all text items from a message content list."""
    parts = []
    for item in content:
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
        elif item.get("type") == "tool_result":
            # tool_result content may itself be a list
            inner = item.get("content", [])
            if isinstance(inner, list):
                for sub in inner:
                    if sub.get("type") == "text":
                        parts.append(sub.get("text", ""))
            elif isinstance(inner, str):
                parts.append(inner)
    return "\n".join(parts)


def _extract_user_query(text: str) -> str | None:
    """
    Extract the genuine user query from a Cursor user message.
    Returns None if this looks like a Cursor system message (subagent result report).
    """
    # Try to find <user_query> tag
    match = re.search(r"<user_query>(.*?)</user_query>", text, re.DOTALL)
    if match:
        query = match.group(1).strip()
        # Filter out Cursor's "The beginning of the above subagent result is..." auto-messages
        if query.startswith("The beginning of the above subagent result"):
            return None
        if query.startswith("Briefly inform the user about the task result"):
            return None
        return query

    # No tag - check if it's a skill attachment or raw query
    # Messages with <manually_attached_skills> are user-initiated (with skill context)
    if "<manually_attached_skills>" in text:
        # Extract content after the skills block
        after = re.split(r"</manually_attached_skills>", text, maxsplit=1)
        if len(after) > 1:
            query_part = after[1].strip()
            if query_part:
                return query_part[:500]
        # The skills block IS the message (user triggered with skill, no extra query)
        return "[skill attachment]"

    # Skip empty or very short messages
    stripped = text.strip()
    if len(stripped) < 10:
        return None

    return stripped


def parse_parent_jsonl(jsonl_path: str) -> dict:
    """Parse the parent JSONL and return structured data."""
    if not os.path.isfile(jsonl_path):
        sys.exit(f"Parent JSONL not found: {jsonl_path}")

    with open(jsonl_path, encoding="utf-8") as f:
        lines = f.readlines()

    tool_counts: Counter = Counter()
    task_calls: list[dict] = []
    user_queries: list[dict] = []
    total_messages = len(lines)
    task_seq = 0

    for msg_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = msg.get("role", "")
        content = msg.get("message", {}).get("content", [])

        if role == "user":
            text = _extract_text_from_content(content)
            query = _extract_user_query(text)
            if query:
                user_queries.append({"msg_idx": msg_idx, "text": query})

        elif role == "assistant":
            for item in content:
                if item.get("type") != "tool_use":
                    continue
                name = item.get("name", "")
                tool_counts[name] += 1

                if name == "Task":
                    inp = item.get("input", {})
                    prompt = inp.get("prompt", "")
                    desc = inp.get("description", "")
                    model = inp.get("model", "")
                    task_calls.append(
                        {
                            "seq": task_seq,
                            "msg_idx": msg_idx,
                            "description": desc,
                            "model": model,
                            "subagent_type": inp.get("subagent_type", ""),
                            "readonly": inp.get("readonly", None),
                            "prompt_len": len(prompt),
                            "prompt_first_200": prompt[:200],
                        }
                    )
                    task_seq += 1

    return {
        "tool_counts": dict(tool_counts),
        "task_calls": task_calls,
        "user_queries": user_queries,
        "total_messages": total_messages,
    }


def parse_subagent_jsonl(jsonl_path: str) -> dict:
    """Parse a subagent JSONL file and return a summary."""
    if not os.path.isfile(jsonl_path):
        return {}

    with open(jsonl_path, encoding="utf-8") as f:
        lines = f.readlines()

    tool_counts: Counter = Counter()
    msg_count = 0
    direction_text = ""  # first user message text (the direction/prompt)
    has_task_calls = False

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_count += 1
        role = msg.get("role", "")
        content = msg.get("message", {}).get("content", [])

        if role == "user" and not direction_text:
            direction_text = _extract_text_from_content(content)

        elif role == "assistant":
            for item in content:
                if item.get("type") == "tool_use":
                    name = item.get("name", "")
                    tool_counts[name] += 1
                    if name == "Task":
                        has_task_calls = True

    total_tool_turns = sum(tool_counts.values())

    return {
        "msg_count": msg_count,
        "tool_counts": dict(tool_counts),
        "total_tool_turns": total_tool_turns,
        "direction_preview": direction_text[:300],
        "has_task_calls": has_task_calls,
    }


def extract_session(session_id: str, project_path: str) -> dict:
    """Extract full structured data for a session."""
    phash = project_hash(project_path)
    full_session_id = resolve_session(phash, session_id)
    session_dir = os.path.join(
        CURSOR_PROJECTS, phash, "agent-transcripts", full_session_id
    )

    parent_jsonl = os.path.join(session_dir, f"{full_session_id}.jsonl")
    parent_data = parse_parent_jsonl(parent_jsonl)

    # Subagents sorted by mtime
    subagents_dir = os.path.join(session_dir, "subagents")
    subagent_entries = []
    if os.path.isdir(subagents_dir):
        for fname in os.listdir(subagents_dir):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(subagents_dir, fname)
            stat = os.stat(fpath)
            subagent_entries.append(
                {
                    "id": fname[:-6],  # strip .jsonl
                    "path": fpath,
                    "mod_time": stat.st_mtime,
                    "mod_time_iso": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                    "file_size": stat.st_size,
                }
            )

    subagent_entries.sort(key=lambda e: e["mod_time"])

    subagents = []
    for entry in subagent_entries:
        data = parse_subagent_jsonl(entry["path"])
        subagents.append(
            {
                "id": entry["id"],
                "mod_time": entry["mod_time"],
                "mod_time_iso": entry["mod_time_iso"],
                "file_size": entry["file_size"],
                "msg_count": data.get("msg_count", 0),
                "tool_counts": data.get("tool_counts", {}),
                "total_tool_turns": data.get("total_tool_turns", 0),
                "direction_preview": data.get("direction_preview", ""),
                "has_task_calls": data.get("has_task_calls", False),
            }
        )

    # Session time range
    all_mtimes = [e["mod_time"] for e in subagent_entries]
    if os.path.isfile(parent_jsonl):
        all_mtimes.append(os.path.getmtime(parent_jsonl))

    start_time = min(all_mtimes) if all_mtimes else 0
    end_time = max(all_mtimes) if all_mtimes else 0

    return {
        "session": {
            "id": full_session_id,
            "project_hash": phash,
            "project_path": os.path.abspath(os.path.expanduser(project_path)),
            "session_dir": session_dir,
            "start_time": start_time,
            "start_time_iso": datetime.fromtimestamp(
                start_time, tz=timezone.utc
            ).isoformat() if start_time else None,
            "end_time": end_time,
            "end_time_iso": datetime.fromtimestamp(
                end_time, tz=timezone.utc
            ).isoformat() if end_time else None,
            "parent_tool_counts": parent_data["tool_counts"],
            "total_messages": parent_data["total_messages"],
            "subagent_count": len(subagents),
        },
        "task_calls": parent_data["task_calls"],
        "user_queries": parent_data["user_queries"],
        "subagents": subagents,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract structured data from a Cursor agent-transcript session."
    )
    parser.add_argument(
        "session_id",
        help="Session UUID (or unambiguous prefix)",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to the project directory (default: cwd)",
    )
    args = parser.parse_args()

    data = extract_session(args.session_id, args.project_path)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
