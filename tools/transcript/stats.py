#!/usr/bin/env python3
"""Summary statistics from normalized session JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

from lib.cli import add_format_arg, add_tool_arg, load_normalized_json, setup_path

setup_path()


def compute_stats(data: dict) -> dict:
    session = data.get("session", {})
    spawns = data.get("agent_spawns", [])
    subagents = data.get("subagents", [])

    model_counter: Counter = Counter()
    for s in spawns:
        m = s.get("model", "unknown") or "unknown"
        model_counter[m] += 1

    sub_tool_totals: Counter = Counter()
    for sa in subagents:
        for tool, cnt in sa.get("tool_counts", {}).items():
            sub_tool_totals[tool] += cnt

    tool_turns = [sa.get("total_tool_turns", 0) for sa in subagents]
    parent_turns = session.get("parent_tool_turns", 0)
    total_turns = parent_turns + sum(tool_turns)

    wall_seconds = session.get("wall_seconds")
    parent_api_calls = session.get("parent_api_calls", session.get("api_calls"))
    subagent_api_calls = session.get("subagent_api_calls", 0)
    parent_token_usage = session.get("parent_token_usage", session.get("token_usage"))
    subagent_token_usage = session.get("subagent_token_usage")

    return {
        "source": data.get("source", ""),
        "session_id": session.get("id", ""),
        "project_path": session.get("project_path"),
        "external_url": session.get("external_url"),
        "subagent_count": session.get("subagent_count", 0),
        "spawn_count": len(spawns),
        "parent_tool_counts": session.get("parent_tool_counts", {}),
        "parent_tool_counts_raw": session.get("parent_tool_counts_raw", {}),
        "parent_tool_turns": parent_turns,
        "model_breakdown": dict(model_counter.most_common()),
        "subagent_tool_totals": dict(sub_tool_totals.most_common()),
        "subagent_tool_turn_stats": {
            "total": sum(tool_turns),
            "min": min(tool_turns) if tool_turns else 0,
            "max": max(tool_turns) if tool_turns else 0,
            "avg": round(sum(tool_turns) / len(tool_turns)) if tool_turns else 0,
        },
        "total_tool_turns": total_turns,
        "api_calls": session.get("api_calls"),
        "parent_api_calls": parent_api_calls,
        "subagent_api_calls": subagent_api_calls,
        "context_estimate": session.get("context_estimate"),
        "token_usage": session.get("token_usage"),
        "parent_token_usage": parent_token_usage,
        "subagent_token_usage": subagent_token_usage,
        "wall_time_seconds": wall_seconds,
        "wall_time_human": _format_duration(wall_seconds),
        "start_time_iso": session.get("start_time_iso"),
        "end_time_iso": session.get("end_time_iso"),
    }


def _format_duration(seconds: int | float | None) -> str:
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
    print(f"  Source        : {stats['source']}")
    print(f"  Session ID    : {stats['session_id']}")
    if stats.get("external_url"):
        print(f"  External URL  : {stats['external_url']}")
    if stats.get("project_path"):
        print(f"  Project       : {stats['project_path']}")
    print(f"  Spawns        : {stats['spawn_count']}")
    print(f"  Subagents     : {stats['subagent_count']}")
    print(f"  Start         : {stats.get('start_time_iso', 'unknown')}")
    print(f"  End           : {stats.get('end_time_iso', 'unknown')}")
    print(f"  Wall time     : {stats['wall_time_human']}")
    if stats.get("api_calls") is not None:
        print(f"  API calls     : {stats['api_calls']}")
        if stats.get("subagent_api_calls"):
            print(
                f"    parent      : {stats.get('parent_api_calls', 0)}"
            )
            print(f"    subagents   : {stats['subagent_api_calls']}")
    if stats.get("context_estimate") is not None:
        print(
            f"  Context est.  : {stats['context_estimate']:,} tokens"
            " (first response only)"
        )
    if stats.get("token_usage"):
        tu = stats["token_usage"]
        cache_read = tu.get("cache_read_input_tokens", 0)
        print(f"  Token usage   : {sum(tu.values()):,} billed tokens")
        if stats.get("subagent_token_usage"):
            ptu = stats["parent_token_usage"] or {}
            stu = stats["subagent_token_usage"] or {}
            print(
                f"    parent      : {sum(ptu.values()):,}"
                f" ({ptu.get('cache_read_input_tokens', 0):,} cache read)"
            )
            print(
                f"    subagents   : {sum(stu.values()):,}"
                f" ({stu.get('cache_read_input_tokens', 0):,} cache read)"
            )
        elif cache_read:
            print(f"    cache read  : {cache_read:,}")
    print()

    print("PARENT TOOL DISTRIBUTION (canonical)")
    print("-" * 40)
    for tool, count in sorted(
        stats["parent_tool_counts"].items(), key=lambda x: -x[1]
    ):
        print(f"  {tool:<22} {count:>6}")
    print()

    if stats["model_breakdown"]:
        print("MODEL BREAKDOWN (spawns)")
        print("-" * 40)
        for model, count in stats["model_breakdown"].items():
            print(f"  {model:<35} {count:>4}")
        print()

    if stats["subagent_tool_totals"]:
        print("SUBAGENT TOOL DISTRIBUTION (aggregated)")
        print("-" * 40)
        for tool, count in sorted(
            stats["subagent_tool_totals"].items(), key=lambda x: -x[1]
        )[:20]:
            print(f"  {tool:<22} {count:>6}")
        print()

    tt = stats["subagent_tool_turn_stats"]
    print("TOOL TURN TOTALS")
    print("-" * 40)
    print(f"  Parent           : {stats['parent_tool_turns']}")
    print(f"  Subagents (sum)  : {tt['total']}")
    print(f"  Combined         : {stats['total_tool_turns']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summary statistics from normalized session JSON."
    )
    parser.add_argument(
        "--session",
        metavar="REF",
        help="Re-extract from this session instead of reading stdin",
    )
    parser.add_argument(
        "--project",
        dest="project_flag",
        metavar="PATH",
        help="Project path (with --session; default: cwd)",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project path (with --session; default: cwd)",
    )
    add_tool_arg(parser)
    add_format_arg(parser)
    args = parser.parse_args()

    project = args.project_flag or args.project_path or (os.getcwd() if args.session else None)
    data = load_normalized_json(args.session, project, args.tool)
    stats = compute_stats(data)

    if args.format == "json":
        print(json.dumps(stats, indent=2))
    else:
        print_text(stats)


if __name__ == "__main__":
    main()
