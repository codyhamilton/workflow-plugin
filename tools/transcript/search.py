#!/usr/bin/env python3
"""Search message text across a session (parent + subagents)."""

from __future__ import annotations

import argparse
import json
import os
import sys

from lib.cli import add_format_arg, add_tool_arg, resolve_session_ref, setup_path
from lib.registry import REGISTRY

setup_path()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search message text across a session."
    )
    parser.add_argument("session_ref", help="Session ID or prefix")
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project directory (default: cwd)",
    )
    parser.add_argument("pattern", help="Search pattern (substring or regex)")
    parser.add_argument("--regex", action="store_true", help="Treat pattern as regex")
    parser.add_argument("--agent", metavar="ID", help="Search only this subagent (or 'parent')")
    parser.add_argument(
        "--role", choices=["user", "assistant"], help="Filter by message role"
    )
    parser.add_argument(
        "--context",
        type=int,
        default=200,
        metavar="N",
        help="Characters of context around match (default: 200)",
    )
    add_tool_arg(parser)
    add_format_arg(parser)
    args = parser.parse_args()

    project = args.project_path
    if project:
        project = os.path.abspath(os.path.expanduser(project))
    elif not args.session_ref:
        project = os.getcwd()

    ref = resolve_session_ref(args.session_ref, project, args.tool)
    parser_impl = REGISTRY.get(ref.source)
    hits = parser_impl.search(
        ref,
        args.pattern,
        regex=args.regex,
        role=args.role,
        context=args.context,
        agent=args.agent,
    )

    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "agent_id": h.agent_id,
                        "msg_idx": h.msg_idx,
                        "role": h.role,
                        "text_snippet": h.text_snippet,
                    }
                    for h in hits
                ],
                indent=2,
            )
        )
        return

    if not hits:
        print(f"No matches for '{args.pattern}'")
        return

    print(f"Found {len(hits)} match(es) for '{args.pattern}':\n")
    for h in hits:
        label = "[parent]" if h.agent_id == "parent" else f"[{h.agent_id[:8]}]"
        print(f"{label} msg={h.msg_idx} role={h.role}")
        print(f"  {h.text_snippet}")
        print()


if __name__ == "__main__":
    main()
