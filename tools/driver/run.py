#!/usr/bin/env python3
"""Phase driver CLI — one phase per invocation with --once (Grok Bot loop owner)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resolve import ResolveError
from run_record import append_record, entry_from_trigger, resolve_record_path
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
    parser.add_argument(
        "--record",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Append one run-record JSON line per invocation (default: DRIVER_RUN_RECORD env). "
            "Does not write inside the plan folder."
        ),
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Do not append to the run record even when DRIVER_RUN_RECORD is set.",
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

    payload = outcome.to_json_dict()
    record_path = None if args.no_record else resolve_record_path(args.record)
    if record_path is not None:
        status = outcome.status
        dispatch = outcome.dispatch
        target = (dispatch or {}).get("target") if dispatch else None
        record_entry = entry_from_trigger(
            plan=status.plan,
            slug=status.slug,
            default_branch=outcome.default_branch,
            skipped=outcome.skipped,
            report=payload.get("report"),
            dispatch_target=target,
            turns=outcome.turns,
            cost_usd=outcome.cost_usd,
            provider=outcome.provider,
            mode=outcome.mode,
        )
        append_record(record_path, record_entry)
        payload["run_record"] = record_entry

    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
