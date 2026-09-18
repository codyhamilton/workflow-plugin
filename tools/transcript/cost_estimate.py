#!/usr/bin/env python3
"""Estimate Cursor session token/cost from transcript structure; reconcile with CSV."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from lib.cli import add_format_arg, add_tool_arg, load_normalized_json, resolve_session_ref, setup_path
from lib.estimate import estimate_from_data, load_estimate_config, reconcile
from cost_window import compute, load_pricing

setup_path()


def _window_from_session(data: dict, pad_minutes: int) -> tuple[str, str]:
    session = data.get("session", {})
    start_iso = session.get("start_time_iso")
    end_iso = session.get("end_time_iso")
    if not (start_iso and end_iso):
        sys.exit("Session has no start/end time; cannot reconcile CSV.")
    pad = timedelta(minutes=pad_minutes)
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00")) - pad
    end_dt = datetime.fromisoformat(end_iso.replace("Z", "+00:00")) + pad
    start = start_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    end = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    return start, end


def print_text(result: dict) -> None:
    est = result["estimate"]
    tu = est["token_usage"]
    total = sum(tu.values())
    print("=" * 64)
    print("COST ESTIMATE (transcript heuristic — ballpark)")
    print("=" * 64)
    print(f"  Fixed context : {est['fixed_context']:,} tokens")
    print(f"  User queries  : {est['user_queries']}")
    print(f"  Asst. steps   : {est['assistant_steps']}")
    print(f"  API calls est.: {est['api_calls']} (one per user query)")
    print(
        f"  Tokens        : {total:,}"
        f"  (fresh {tu['fresh_in']:,}, read {tu['cache_read']:,},"
        f" out {tu['output']:,})"
    )
    if est.get("cost_usd") is not None:
        print(f"  Est. cost     : ${est['cost_usd']:.2f} ({est['model']})")
    print()

    for i, ev in enumerate(est.get("events", []), 1):
        mode = "miss" if ev.get("cache_miss") else "hit "
        ev_total = sum(ev[k] for k in ("fresh_in", "cache_read", "output"))
        print(
            f"  q{i} {mode}  fresh={ev['fresh_in']:>7,}"
            f" read={ev['cache_read']:>9,} out={ev['output']:>5,}"
            f"  ({ev_total:,})"
        )
    print()

    recon = result.get("reconciliation")
    if recon:
        print("RECONCILIATION vs CSV WINDOW")
        print("-" * 64)
        print(f"  CSV events    : {recon['actual_events']}")
        print(f"  Est. events   : {recon['estimated_events']}")
        ratios = recon["ratios_est_over_actual"]
        print(
            f"  Token ratio   : total {ratios.get('total')}x"
            f"  (fresh {ratios.get('fresh_in')}x,"
            f" read {ratios.get('cache_read')}x,"
            f" out {ratios.get('output')}x)"
        )
        if recon.get("usd_ratio") is not None:
            print(
                f"  USD ratio     : {recon['usd_ratio']}x"
                f"  (est ${recon['estimated_usd']:.2f}"
                f" vs csv ${recon['actual_usd']:.2f})"
            )
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate Cursor session tokens from transcript; optionally reconcile with usage CSV."
    )
    parser.add_argument("--session", metavar="REF", help="Re-extract from this session")
    parser.add_argument("--project", dest="project_flag", metavar="PATH")
    parser.add_argument("project_path", nargs="?", default=None)
    parser.add_argument(
        "--reconcile-csv",
        metavar="FILE",
        help="Compare estimate against usage-events CSV in session window",
    )
    parser.add_argument(
        "--pad-minutes",
        type=int,
        default=2,
        help="Pad session window for CSV reconciliation (default 2)",
    )
    parser.add_argument(
        "--model",
        default="composer-2.5",
        help="Pricing model for dollar estimate (default composer-2.5)",
    )
    parser.add_argument("--pricing", default=None, help="pricing JSON path")
    parser.add_argument("--no-pricing", action="store_true")
    add_tool_arg(parser)
    add_format_arg(parser)
    args = parser.parse_args()

    project = args.project_flag or args.project_path or (os.getcwd() if args.session else None)
    data = load_normalized_json(args.session, project, args.tool)
    source = data.get("source", "")
    session = data.get("session", {})

    if session.get("token_usage"):
        print(
            "Session has transcript usage data; use stats.py / pricing on token_usage instead.",
            file=sys.stderr,
        )
        if source != "cursor":
            sys.exit(0)

    if source != "cursor":
        sys.exit("cost_estimate.py is for Cursor sessions (no usage in JSONL).")

    ref = resolve_session_ref(args.session or "latest", project, args.tool)
    cfg = load_estimate_config(session.get("project_path"))
    cfg["default_model"] = args.model
    pricing = None if args.no_pricing else load_pricing(args.pricing)

    estimate = estimate_from_data(
        data,
        ref.storage_path,
        cfg=cfg,
        pricing=pricing,
    )

    result: dict = {"estimate": estimate}
    if args.reconcile_csv:
        start, end = _window_from_session(data, args.pad_minutes)
        exclude = re.compile(r"grok-bot|automation")
        actual = compute(
            args.reconcile_csv,
            start,
            end,
            set(),
            pricing=pricing,
            models={args.model},
            exclude_models=exclude,
        )
        result["reconciliation"] = reconcile(estimate, actual)
        result["csv_window"] = {"start": start, "end": end}

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)


if __name__ == "__main__":
    main()
