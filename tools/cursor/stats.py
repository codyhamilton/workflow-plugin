#!/usr/bin/env python3
"""
stats.py — Summary statistics for a Cursor agent-transcript session.

Usage:
    # From pre-extracted JSON (pipe from extract.py):
    python tools/cursor/extract.py SESSION_ID PROJECT_PATH | python tools/cursor/stats.py

    # Re-extract from session:
    python tools/cursor/stats.py --session SESSION_ID [PROJECT_PATH]
        [--format text|json]

Output sections (text mode):
  Session Overview
  Parent Tool Distribution
  Model Breakdown (from Task calls)
  Subagent Tool Distribution (aggregated)
  Prompt Length by Phase
  Wall Time
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone


def load_data(session_id: str | None, project_path: str | None) -> dict:
    if session_id:
        # Import extract from same directory
        sys.path.insert(0, os.path.dirname(__file__))
        from extract import extract_session
        return extract_session(session_id, project_path or os.getcwd())
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit("No input: pipe extract.py output or use --session SESSION_ID")
        return json.loads(raw)


def compute_stats(data: dict) -> dict:
    session = data.get("session", {})
    task_calls = data.get("task_calls", [])
    subagents = data.get("subagents", [])

    # Model breakdown
    model_counter: Counter = Counter()
    for t in task_calls:
        m = t.get("model", "unknown") or "unknown"
        model_counter[m] += 1

    # Subagent tool totals
    sub_tool_totals: Counter = Counter()
    for sa in subagents:
        for tool, cnt in sa.get("tool_counts", {}).items():
            sub_tool_totals[tool] += cnt

    # Prompt length stats by model
    model_prompt_lens: dict[str, list[int]] = {}
    for t in task_calls:
        m = t.get("model", "unknown") or "unknown"
        model_prompt_lens.setdefault(m, []).append(t.get("prompt_len", 0))

    model_prompt_stats = {}
    for m, lens in model_prompt_lens.items():
        model_prompt_stats[m] = {
            "count": len(lens),
            "min": min(lens),
            "max": max(lens),
            "avg": round(sum(lens) / len(lens)),
        }

    # Wall time
    start = session.get("start_time", 0)
    end = session.get("end_time", 0)
    wall_seconds = (end - start) if (start and end) else None

    # Subagent size stats
    sizes = [sa.get("file_size", 0) for sa in subagents]
    msg_counts = [sa.get("msg_count", 0) for sa in subagents]
    tool_turns = [sa.get("total_tool_turns", 0) for sa in subagents]

    return {
        "session_id": session.get("id", ""),
        "project_hash": session.get("project_hash", ""),
        "total_messages": session.get("total_messages", 0),
        "subagent_count": session.get("subagent_count", 0),
        "task_call_count": len(task_calls),
        "parent_tool_counts": session.get("parent_tool_counts", {}),
        "model_breakdown": dict(model_counter.most_common()),
        "model_prompt_stats": model_prompt_stats,
        "subagent_tool_totals": dict(sub_tool_totals.most_common()),
        "subagent_size_stats": {
            "total_bytes": sum(sizes),
            "min_bytes": min(sizes) if sizes else 0,
            "max_bytes": max(sizes) if sizes else 0,
            "avg_bytes": round(sum(sizes) / len(sizes)) if sizes else 0,
        },
        "subagent_msg_stats": {
            "total_msgs": sum(msg_counts),
            "min_msgs": min(msg_counts) if msg_counts else 0,
            "max_msgs": max(msg_counts) if msg_counts else 0,
            "avg_msgs": round(sum(msg_counts) / len(msg_counts)) if msg_counts else 0,
        },
        "subagent_tool_turn_stats": {
            "total": sum(tool_turns),
            "min": min(tool_turns) if tool_turns else 0,
            "max": max(tool_turns) if tool_turns else 0,
            "avg": round(sum(tool_turns) / len(tool_turns)) if tool_turns else 0,
        },
        "wall_time_seconds": wall_seconds,
        "wall_time_human": _format_duration(wall_seconds),
        "start_time_iso": session.get("start_time_iso"),
        "end_time_iso": session.get("end_time_iso"),
    }


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s"


def print_text(stats: dict) -> None:
    print("=" * 60)
    print("SESSION OVERVIEW")
    print("=" * 60)
    print(f"  Session ID    : {stats['session_id']}")
    print(f"  Project hash  : {stats['project_hash']}")
    print(f"  Parent msgs   : {stats['total_messages']}")
    print(f"  Task calls    : {stats['task_call_count']}")
    print(f"  Subagents     : {stats['subagent_count']}")
    print(f"  Start         : {stats.get('start_time_iso', 'unknown')}")
    print(f"  End           : {stats.get('end_time_iso', 'unknown')}")
    print(f"  Wall time     : {stats['wall_time_human']}")
    print()

    print("PARENT TOOL DISTRIBUTION")
    print("-" * 40)
    for tool, count in sorted(
        stats["parent_tool_counts"].items(), key=lambda x: -x[1]
    ):
        print(f"  {tool:<22} {count:>6}")
    print()

    print("MODEL BREAKDOWN (Task calls)")
    print("-" * 40)
    for model, count in stats["model_breakdown"].items():
        pct = count / stats["task_call_count"] * 100 if stats["task_call_count"] else 0
        ps = stats["model_prompt_stats"].get(model, {})
        print(
            f"  {model:<35} {count:>4} ({pct:4.0f}%)  "
            f"prompt avg={ps.get('avg',0):5d} min={ps.get('min',0):5d} max={ps.get('max',0):5d}"
        )
    print()

    print("SUBAGENT TOOL DISTRIBUTION (aggregated)")
    print("-" * 40)
    for tool, count in sorted(
        stats["subagent_tool_totals"].items(), key=lambda x: -x[1]
    )[:20]:
        print(f"  {tool:<22} {count:>6}")
    print()

    print("SUBAGENT SIZE & ACTIVITY")
    print("-" * 40)
    sz = stats["subagent_size_stats"]
    ms = stats["subagent_msg_stats"]
    tt = stats["subagent_tool_turn_stats"]
    print(
        f"  File size (bytes): total={sz['total_bytes']:,}  "
        f"avg={sz['avg_bytes']:,}  min={sz['min_bytes']:,}  max={sz['max_bytes']:,}"
    )
    print(
        f"  Messages         : total={ms['total_msgs']:,}  "
        f"avg={ms['avg_msgs']:,}  min={ms['min_msgs']:,}  max={ms['max_msgs']:,}"
    )
    print(
        f"  Tool turns       : total={tt['total']:,}  "
        f"avg={tt['avg']:,}  min={tt['min']:,}  max={tt['max']:,}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summary statistics for a Cursor agent-transcript session."
    )
    parser.add_argument(
        "--session",
        metavar="SESSION_ID",
        help="Re-extract from this session instead of reading stdin",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project path (only used with --session; default: cwd)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    data = load_data(args.session, args.project_path)
    stats = compute_stats(data)

    if args.format == "json":
        print(json.dumps(stats, indent=2))
    else:
        print_text(stats)


if __name__ == "__main__":
    main()
