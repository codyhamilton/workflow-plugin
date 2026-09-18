#!/usr/bin/env python3
"""Discover sessions across Claude Code and Cursor."""

from __future__ import annotations

import argparse
import json
import sys

from lib.cli import add_format_arg, add_tool_arg, get_parsers, setup_path

setup_path()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List agent sessions across registered harnesses."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project directory (omit with --all for global search)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Search all projects (ignore project_path)",
    )
    parser.add_argument("--match", metavar="TEXT", help="Filter by substring match")
    parser.add_argument("--limit", type=int, help="Max sessions to return")
    parser.add_argument("--since", metavar="ISO", help="Only sessions after ISO timestamp")
    parser.add_argument(
        "--min-subagents", type=int, metavar="N", help="Minimum subagent count"
    )
    add_tool_arg(parser)
    add_format_arg(parser)
    args = parser.parse_args()

    parsers = get_parsers(args.tool)
    sessions = []
    for p in parsers:
        if args.all or not args.project_path:
            sessions.extend(
                p.discover_all(
                    match=args.match,
                    since=args.since,
                    min_subagents=args.min_subagents,
                )
            )
        else:
            sessions.extend(
                p.discover(
                    args.project_path,
                    match=args.match,
                    since=args.since,
                    min_subagents=args.min_subagents,
                )
            )

    sessions.sort(key=lambda s: s.start_time_iso, reverse=True)
    if args.limit:
        sessions = sessions[: args.limit]

    if not sessions:
        print("No sessions found.", file=sys.stderr)
        sys.exit(0)

    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "source": s.source,
                        "session_id": s.session_id,
                        "external_url": s.external_url,
                        "project_path": s.project_path,
                        "start_time_iso": s.start_time_iso,
                        "subagent_count": s.subagent_count,
                        "bytes": s.bytes,
                    }
                    for s in sessions
                ],
                indent=2,
            )
        )
        return

    header = (
        f"{'SOURCE':<12} {'SESSION_ID':<38} {'START':<26} "
        f"{'SUBAGENTS':>9} {'BYTES':>10}"
    )
    print(header)
    print("-" * len(header))
    for s in sessions:
        print(
            f"{s.source:<12} {s.session_id:<38} {s.start_time_iso:<26} "
            f"{s.subagent_count:>9} {s.bytes:>10}"
        )
        if s.external_url:
            print(f"             {s.external_url}")
        if s.project_path:
            print(f"             {s.project_path}")
    print(f"\n{len(sessions)} session(s)")


if __name__ == "__main__":
    main()
