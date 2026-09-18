#!/usr/bin/env python3
"""Emit cost-comparison.md schema section from normalized session JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys

from lib.cli import add_format_arg, add_tool_arg, load_normalized_json, setup_path

setup_path()


def _format_tool_breakdown(counts: dict[str, int], raw: dict[str, int] | None) -> str:
    if raw:
        parts = [f"{k}: {v}" for k, v in sorted(raw.items(), key=lambda x: -x[1])]
    else:
        parts = [f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])]
    return ", ".join(parts) if parts else "none"


def _format_agents_spawned(spawns: list[dict], subagents: list[dict]) -> str:
    if spawns:
        from collections import Counter

        parts = []
        model_type: Counter[tuple[str, str]] = Counter()
        for s in spawns:
            model = s.get("model") or "unknown"
            atype = s.get("agent_type") or "unknown"
            model_type[(model, atype)] += 1
        for (model, atype), count in model_type.most_common():
            parts.append(f"{count} × {model} ({atype})")
        return ", ".join(parts)
    if subagents:
        return f"{len(subagents)} subagent(s) (model not recorded in transcript)"
    return "0"


def _format_wall_time(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def format_markdown(data: dict, label: str) -> str:
    session = data.get("session", {})
    spawns = data.get("agent_spawns", [])
    subagents = data.get("subagents", [])
    source = data.get("source", "")

    parent_raw = session.get("parent_tool_counts_raw", {})
    parent_canon = session.get("parent_tool_counts", {})
    parent_turns = session.get("parent_tool_turns", 0)

    lines = [f"## {label}", ""]
    lines.append(f"- Agents spawned: {_format_agents_spawned(spawns, subagents)}")
    lines.append("- Tool use turns (per agent):")
    lines.append(
        f"  - parent: {parent_turns} turns ({_format_tool_breakdown(parent_canon, parent_raw)})"
    )

    for i, sa in enumerate(subagents, 1):
        sa_raw = sa.get("tool_counts_raw", sa.get("tool_counts", {}))
        sa_canon = sa.get("tool_counts", {})
        turns = sa.get("total_tool_turns", 0)
        atype = sa.get("agent_type", "unknown")
        model = sa.get("model", "unknown")
        lines.append(
            f"  - agent-{i} [{atype}, {model}]: {turns} turns "
            f"({_format_tool_breakdown(sa_canon, sa_raw)})"
        )

    sub_total = sum(sa.get("total_tool_turns", 0) for sa in subagents)
    total = parent_turns + sub_total
    lines.append(f"- Tool use turns (total): {total}")

    ctx = session.get("context_estimate")
    if ctx is not None:
        lines.append(
            f"- Context estimate: {ctx:,} tokens (approximate — first response only, {source})"
        )
    else:
        lines.append(
            f"- Context estimate: not available (source: {source} — no usage data in transcript)"
        )

    lines.append(f"- Wall time: {_format_wall_time(session.get('wall_seconds'))}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit cost-comparison.md schema section."
    )
    parser.add_argument(
        "--label",
        required=True,
        choices=["Baseline", "Candidate"],
        help="Section label for cost-comparison.md",
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

    if args.format == "json":
        print(json.dumps({"label": args.label, "section": format_markdown(data, args.label)}))
    else:
        print(format_markdown(data, args.label))


if __name__ == "__main__":
    main()
