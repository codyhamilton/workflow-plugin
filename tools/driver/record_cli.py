#!/usr/bin/env python3
"""Summarize an external driver run record JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_record import DEFAULT_RUN_RECORD, summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize per-invocation driver run record (JSONL outside plan folder).",
    )
    parser.add_argument(
        "--record",
        default=DEFAULT_RUN_RECORD,
        help=f"Path to JSONL run record (default: {DEFAULT_RUN_RECORD})",
    )
    parser.add_argument(
        "--plan-folder",
        type=Path,
        default=None,
        help="Filter entries to this plan path (as stored in the record)",
    )
    parser.add_argument(
        "--plan",
        default=None,
        help="Plan path string filter (alternative to --plan-folder)",
    )
    args = parser.parse_args(argv)

    plan_filter = args.plan
    if plan_filter is None and args.plan_folder is not None:
        plan_filter = str(args.plan_folder).rstrip("/")

    summary = summarize(args.record, plan=plan_filter)
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
