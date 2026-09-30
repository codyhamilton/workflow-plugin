#!/usr/bin/env python3
"""Phase driver CLI — one phase per invocation with --once (Grok Bot loop owner)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resolve import ResolveError
from trigger import trigger_once


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Workflow phase driver. Use --once to resolve and dispatch a single fresh "
            "phase agent session (default for Grok Bot). Does not commit."
        ),
    )
    parser.add_argument(
        "plan_folder",
        type=Path,
        help="Path to docs/plans/<NN>-<slug>/",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Dispatch at most one phase or wrap-up session, then exit (required for spike B).",
    )
    parser.add_argument(
        "--default-branch",
        dest="default_branch",
        default=None,
        help="Default branch for git log <default>..HEAD (default: detect origin/HEAD)",
    )
    parser.add_argument(
        "--provider",
        choices=("claude", "cursor", "dry-run"),
        default=None,
        help="Provider override (default: key in environment, else dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run provider (no SDK call; report is incomplete, not a fake close).",
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=None,
        help="Path to a fixture agent final-output file containing a workflow-report block.",
    )
    parser.add_argument(
        "--review",
        dest="review_posture",
        choices=("terminal", "pipeline"),
        default="terminal",
        help="Review posture passed to the phase agent (wrap-up only).",
    )
    args = parser.parse_args(argv)

    if not args.once:
        print(
            "Full loop (run to completion) is not implemented yet. "
            "Use --once for one-phase dispatch; Grok Bot owns the loop.",
            file=sys.stderr,
        )
        return 2

    try:
        outcome = trigger_once(
            args.plan_folder,
            default_branch=args.default_branch,
            provider=args.provider,
            dry_run=args.dry_run,
            fixture_output=args.fixture_output,
            review_posture=args.review_posture,
        )
    except ResolveError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(outcome.to_json_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
