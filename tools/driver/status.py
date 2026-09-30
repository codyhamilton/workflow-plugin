#!/usr/bin/env python3
"""Read-only phase status from Workflow-Phase trailers and DESIGN.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resolve import ResolveError, resolve_plan_folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve open phase, wrap-up, or done from git trailers and DESIGN.md. "
            "Read-only; no network; no IMPLEMENTATION.md."
        ),
    )
    parser.add_argument(
        "plan_folder",
        type=Path,
        help="Path to docs/plans/<NN>-<slug>/",
    )
    parser.add_argument(
        "--default-branch",
        dest="default_branch",
        default=None,
        help="Default branch for git log <default>..HEAD (default: detect origin/HEAD)",
    )
    args = parser.parse_args(argv)

    try:
        status = resolve_plan_folder(
            args.plan_folder,
            default_branch=args.default_branch,
        )
    except ResolveError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(status.to_json_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
