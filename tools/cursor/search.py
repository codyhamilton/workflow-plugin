#!/usr/bin/env python3
"""
search.py — Search message text across a Cursor agent-transcript session.

Usage:
    python tools/cursor/search.py SESSION_ID PROJECT_PATH PATTERN [options]

Arguments:
    SESSION_ID    Session UUID (or unambiguous prefix)
    PROJECT_PATH  Path to project directory (default: cwd if omitted before PATTERN)
    PATTERN       Search string (substring by default, regex with --regex)

Options:
    --regex           Treat PATTERN as a Python regex
    --agent AGENT_ID  Search only in this subagent's transcript
    --role user|assistant  Filter by message role
    --context N       Print N lines of context around each match (default: 1)
    --format text|json

Output (text): matched messages with agent_id, msg_idx, role, snippet.
Output (json): list of match objects.
"""

import argparse
import json
import os
import re
import sys


CURSOR_PROJECTS = os.path.expanduser("~/.cursor/projects")


def project_hash(project_path: str) -> str:
    path = os.path.abspath(os.path.expanduser(project_path))
    return path.lstrip("/").replace("/", "-")


def resolve_session(phash: str, session_prefix: str) -> str:
    transcripts_dir = os.path.join(CURSOR_PROJECTS, phash, "agent-transcripts")
    if not os.path.isdir(transcripts_dir):
        sys.exit(f"No agent-transcripts directory: {transcripts_dir}")
    matches = [
        d for d in os.listdir(transcripts_dir)
        if os.path.isdir(os.path.join(transcripts_dir, d))
        and d.startswith(session_prefix)
    ]
    if not matches:
        sys.exit(f"No session matching '{session_prefix}'")
    if len(matches) > 1:
        sys.exit(f"Ambiguous session prefix '{session_prefix}': {matches}")
    return matches[0]


def _content_texts(content: list) -> list[str]:
    """Extract all text strings from a message content list."""
    texts = []
    for item in content:
        if item.get("type") == "text":
            texts.append(item.get("text", ""))
        elif item.get("type") == "tool_use":
            # Include tool name and description/input text
            inp = item.get("input", {})
            text_parts = [f"[tool:{item.get('name','')}]"]
            for k, v in inp.items():
                if isinstance(v, str) and v:
                    text_parts.append(f"{k}: {v[:400]}")
            texts.append(" ".join(text_parts))
        elif item.get("type") == "tool_result":
            inner = item.get("content", [])
            if isinstance(inner, list):
                for sub in inner:
                    if sub.get("type") == "text":
                        texts.append(sub.get("text", ""))
            elif isinstance(inner, str):
                texts.append(inner)
    return texts


def _snippet(text: str, pattern: re.Pattern, context_chars: int = 200) -> str:
    """Return a snippet around the first match of pattern in text."""
    m = pattern.search(text)
    if not m:
        return ""
    start = max(0, m.start() - context_chars // 2)
    end = min(len(text), m.end() + context_chars // 2)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet.replace("\n", " ")


def search_jsonl(
    jsonl_path: str,
    agent_id: str,
    pattern: re.Pattern,
    role_filter: str | None,
    context_chars: int = 200,
) -> list[dict]:
    matches = []
    if not os.path.isfile(jsonl_path):
        return matches

    with open(jsonl_path, encoding="utf-8") as f:
        lines = f.readlines()

    for msg_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = msg.get("role", "")
        if role_filter and role != role_filter:
            continue

        content = msg.get("message", {}).get("content", [])
        texts = _content_texts(content)

        for text in texts:
            if pattern.search(text):
                snippet = _snippet(text, pattern, context_chars)
                matches.append(
                    {
                        "agent_id": agent_id,
                        "msg_idx": msg_idx,
                        "role": role,
                        "text_snippet": snippet,
                    }
                )
                break  # one match per message

    return matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search message text across a Cursor session."
    )
    parser.add_argument("session_id", help="Session UUID (or unambiguous prefix)")
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Project directory path (default: cwd)",
    )
    parser.add_argument("pattern", help="Search pattern (substring or regex)")
    parser.add_argument(
        "--regex", action="store_true", help="Treat pattern as Python regex"
    )
    parser.add_argument(
        "--agent", metavar="AGENT_ID", help="Search only in this subagent's transcript"
    )
    parser.add_argument(
        "--role",
        choices=["user", "assistant"],
        help="Filter by message role",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=200,
        metavar="N",
        help="Characters of context around match (default: 200)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    args = parser.parse_args()

    phash = project_hash(args.project_path)
    session_id = resolve_session(phash, args.session_id)
    session_dir = os.path.join(
        CURSOR_PROJECTS, phash, "agent-transcripts", session_id
    )

    # Compile pattern
    flags = re.IGNORECASE
    if args.regex:
        try:
            compiled = re.compile(args.pattern, flags)
        except re.error as e:
            sys.exit(f"Invalid regex '{args.pattern}': {e}")
    else:
        compiled = re.compile(re.escape(args.pattern), flags)

    all_matches: list[dict] = []

    if args.agent:
        # Search one specific agent
        subagent_path = os.path.join(session_dir, "subagents", f"{args.agent}.jsonl")
        if not os.path.isfile(subagent_path):
            sys.exit(f"Subagent file not found: {subagent_path}")
        all_matches.extend(
            search_jsonl(subagent_path, args.agent, compiled, args.role, args.context)
        )
    else:
        # Search parent
        parent_path = os.path.join(session_dir, f"{session_id}.jsonl")
        all_matches.extend(
            search_jsonl(parent_path, "parent", compiled, args.role, args.context)
        )

        # Search all subagents
        subagents_dir = os.path.join(session_dir, "subagents")
        if os.path.isdir(subagents_dir):
            for fname in sorted(os.listdir(subagents_dir)):
                if not fname.endswith(".jsonl"):
                    continue
                agent_id = fname[:-6]
                fpath = os.path.join(subagents_dir, fname)
                all_matches.extend(
                    search_jsonl(fpath, agent_id, compiled, args.role, args.context)
                )

    if args.format == "json":
        print(json.dumps(all_matches, indent=2))
        return

    # Text output
    if not all_matches:
        print(f"No matches for '{args.pattern}'")
        return

    print(f"Found {len(all_matches)} match(es) for '{args.pattern}':\n")
    for m in all_matches:
        agent_label = f"[{m['agent_id'][:8]}]" if m["agent_id"] != "parent" else "[parent]"
        print(f"{agent_label} msg={m['msg_idx']} role={m['role']}")
        print(f"  {m['text_snippet']}")
        print()


if __name__ == "__main__":
    main()
