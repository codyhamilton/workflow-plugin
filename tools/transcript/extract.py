#!/usr/bin/env python3
"""Extract normalized session JSON to stdout."""

from __future__ import annotations

import argparse
import json
import os
import sys

from lib.cli import add_tool_arg, extract_session, setup_path

setup_path()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract normalized session data as JSON."
    )
    parser.add_argument(
        "session_ref",
        nargs="?",
        default="latest",
        help="Session ID, prefix, URL slug, or 'latest' (default)",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project directory (helps resolve ambiguous refs)",
    )
    parser.add_argument(
        "--session",
        dest="session_flag",
        metavar="REF",
        help="Session ref (alternative to positional arg)",
    )
    parser.add_argument(
        "--project",
        dest="project_flag",
        metavar="PATH",
        help="Project path (alternative to positional arg)",
    )
    add_tool_arg(parser)
    args = parser.parse_args()

    session_ref = args.session_flag or args.session_ref
    project_path = args.project_flag or args.project_path
    if project_path:
        project_path = os.path.abspath(os.path.expanduser(project_path))

    data = extract_session(session_ref, project_path, args.tool)
    print(json.dumps(data.to_dict(), indent=2))


if __name__ == "__main__":
    main()
