#!/usr/bin/env python3
"""Read-only phase status from Workflow-Phase trailers and DESIGN.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resolve import ResolveError, resolve_plan_folder
from run_record import merge_status_with_record, resolve_record_path, summarize


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
    parser.add_argument(
        "--run-record",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Merge rollup from external run record JSONL (DRIVER_RUN_RECORD if unset). "
            "Open phase still comes from git only."
        ),
    )
    parser.add_argument(
        "--no-run-record",
        action="store_true",
        help="Do not read run record even when DRIVER_RUN_RECORD is set.",
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

    payload = status.to_json_dict()
    record_path = None if args.no_run_record else resolve_record_path(args.run_record)
    if record_path is not None:
        try:
            plan_path = payload["plan"]
        except KeyError:
            plan_path = str(args.plan_folder)
        summary = summarize(record_path, plan=plan_path)
        payload = merge_status_with_record(payload, summary)

    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
