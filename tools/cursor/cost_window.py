#!/usr/bin/env python3
"""
cost_window.py — Attribute usage-CSV tokens to a session by time window.

The Cursor usage export (`usage-events-*.csv`) has no session/agent join key
(the `Cloud Agent ID` and `Automation ID` columns are empty), so a session can
only be tied to its token cost by correlating the session's wall-clock window
with the event timestamps. This script does that correlation and reports how
trustworthy it is, by flagging models that appear in the window but were NOT
used by the session per the transcript ("foreign" models = other work bleeding
into the window).

Note: the export's `Cost` column is subscription accounting ("Included"/"Free"),
not a dollar amount. "Cost" here means tokens consumed, useful for comparing
runs, not for billing.

Usage:
    # Window taken from the extracted session (recommended):
    python3 tools/cursor/extract.py SESSION_ID PROJECT | \
        python3 tools/cursor/cost_window.py --csv usage-events-2026-06-26.csv

    # Or specify an explicit window (no extract needed):
    python3 tools/cursor/cost_window.py --csv FILE \
        --start 2026-06-25T12:37 --end 2026-06-25T23:37

Options:
    --csv FILE        usage export CSV (required)
    --start ISO       window start (prefix-compared, e.g. 2026-06-25T12:37)
    --end ISO         window end   (prefix-compared, inclusive-ish upper bound)
    --pad-minutes N   widen the session window by N minutes each side (default 1)
    --format text|json
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone


def _to_int(s: str) -> int:
    try:
        return int(s)
    except (TypeError, ValueError):
        return 0


def load_window(args) -> tuple[str, str, set[str], str]:
    """Resolve (start, end, session_models, session_id) from stdin or flags."""
    session_models: set[str] = set()
    session_id = ""
    if args.start and args.end:
        return args.start, args.end, session_models, session_id

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(
            "No window: pipe extract.py output, or pass --start and --end.\n"
            "  e.g. extract.py SESSION_ID PROJECT | cost_window.py --csv FILE"
        )
    data = json.loads(raw)
    session = data.get("session", {})
    session_id = session.get("id", "")
    start_iso = session.get("start_time_iso")
    end_iso = session.get("end_time_iso")
    if not (start_iso and end_iso):
        sys.exit("Extracted session has no start/end time; pass --start/--end.")

    # Pad the window — subagent mtimes can sit just outside the parent's span.
    pad = timedelta(minutes=args.pad_minutes)
    start_dt = datetime.fromisoformat(start_iso) - pad
    end_dt = datetime.fromisoformat(end_iso) + pad
    # Compare on the CSV's textual ISO prefix; minute granularity is enough.
    start = start_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    end = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M")

    # Models the session actually used, from its Task calls — the ground truth
    # for separating this session's spend from foreign work in the same window.
    for t in data.get("task_calls", []):
        m = t.get("model") or ""
        if m:
            session_models.add(m)
    return start, end, session_models, session_id


_COMPONENTS = ("fresh_in", "cache_write", "cache_read", "output")
# token-component name -> rate key in pricing.json
_RATE_KEY = {"fresh_in": "input", "cache_write": "cache_write",
             "cache_read": "cache_read", "output": "output"}


def _cost(tokens: dict, rates: dict) -> dict:
    """Dollar cost of a token-component dict under a per-Mtok rate dict."""
    return {k: tokens[k] * rates[_RATE_KEY[k]] / 1_000_000 for k in _COMPONENTS}


def compute(
    csv_path: str,
    start: str,
    end: str,
    session_models: set[str],
    pricing: dict | None = None,
    substitute: tuple[str, str] | None = None,
) -> dict:
    if not os.path.exists(csv_path):
        sys.exit(f"CSV not found: {csv_path}")
    by_model: dict[str, dict] = defaultdict(
        lambda: {
            "total": 0, "output": 0, "cache_read": 0, "cache_write": 0,
            "fresh_in": 0, "events": 0,
        }
    )
    in_window = 0
    cost_labels: dict[str, int] = defaultdict(int)
    with open(csv_path, newline="") as fh:
        for r in csv.DictReader(fh):
            date = r.get("Date", "")
            if not (start <= date <= end + "￿"):
                continue
            in_window += 1
            m = r.get("Model", "unknown") or "unknown"
            b = by_model[m]
            b["total"] += _to_int(r.get("Total Tokens", ""))
            b["output"] += _to_int(r.get("Output Tokens", ""))
            b["cache_read"] += _to_int(r.get("Cache Read", ""))
            b["cache_write"] += _to_int(r.get("Input (w/ Cache Write)", ""))
            b["fresh_in"] += _to_int(r.get("Input (w/o Cache Write)", ""))
            b["events"] += 1
            cost_labels[r.get("Cost", "") or "(blank)"] += 1

    # --- Dollar cost (only if pricing supplied) ---
    cost = None
    if pricing:
        priced, unpriced = {}, []
        for m, b in by_model.items():
            rates = pricing.get(m)
            if not rates:
                unpriced.append(m)
                continue
            split = _cost(b, rates)
            priced[m] = {
                "split": split,
                "total": sum(split.values()),
                "cache_read_share": round(100 * split["cache_read"] / sum(split.values()), 1)
                if sum(split.values()) else 0.0,
                "output_share": round(100 * split["output"] / sum(split.values()), 1)
                if sum(split.values()) else 0.0,
            }
        grand = sum(p["total"] for p in priced.values())
        cost = {
            "by_model": dict(sorted(priced.items(), key=lambda kv: -kv[1]["total"])),
            "grand_total": grand,
            "unpriced_models": sorted(unpriced),
        }
        # What-if: re-run model A's tokens at model B's rates.
        if substitute:
            src, dst = substitute
            if src in by_model and dst in pricing:
                cur = priced.get(src, {}).get("total", 0.0)
                new_split = _cost(by_model[src], pricing[dst])
                new_total = sum(new_split.values())
                cost["substitution"] = {
                    "from": src, "to": dst,
                    "current_cost": cur, "new_cost": new_total,
                    "saving": cur - new_total,
                    "saving_pct": round(100 * (cur - new_total) / cur, 1) if cur else 0.0,
                    "new_grand_total": grand - cur + new_total,
                }

    total_tokens = sum(b["total"] for b in by_model.values())
    foreign = sorted(m for m in by_model if session_models and m not in session_models)
    foreign_tokens = sum(by_model[m]["total"] for m in foreign)
    return {
        "window_start": start,
        "window_end": end,
        "in_window_events": in_window,
        "total_tokens": total_tokens,
        "session_models": sorted(session_models),
        "by_model": {
            m: by_model[m] for m in sorted(by_model, key=lambda k: -by_model[k]["total"])
        },
        "foreign_models": foreign,
        "foreign_tokens": foreign_tokens,
        "foreign_pct": round(100 * foreign_tokens / total_tokens, 1) if total_tokens else 0.0,
        "attribution_confidence_pct": round(100 - (100 * foreign_tokens / total_tokens), 1)
        if total_tokens
        else None,
        "cost_labels": dict(cost_labels),
        "cost": cost,
    }


def print_text(c: dict) -> None:
    print("=" * 64)
    print("COST WINDOW (timestamp-correlated — no session join key exists)")
    print("=" * 64)
    print(f"  Window        : {c['window_start']}  ->  {c['window_end']}")
    print(f"  Events        : {c['in_window_events']}")
    print(f"  Total tokens  : {c['total_tokens']:,}")
    print()
    print("TOKENS BY MODEL")
    print("-" * 64)
    sess = set(c["session_models"])
    for m, b in c["by_model"].items():
        flag = "" if (not sess or m in sess) else "  << FOREIGN"
        print(
            f"  {m:<34} {b['total']:>14,} tok  {b['events']:>3} ev{flag}"
        )
    print()
    print("ATTRIBUTION CONFIDENCE")
    print("-" * 64)
    if not sess:
        print("  No session model list (used --start/--end without a piped session).")
        print("  Cannot separate this session's spend from other in-window work.")
    elif c["foreign_models"]:
        print(
            f"  Foreign models : {', '.join(c['foreign_models'])} "
            f"({c['foreign_pct']}% of window tokens)"
        )
        print(
            f"  Confidence     : ~{c['attribution_confidence_pct']}% of window tokens "
            f"belong to models this session used"
        )
    else:
        print("  Every in-window model was used by the session — window is clean (~100%).")
    print()
    print("COST COLUMN (Cursor subscription accounting, not dollars)")
    print("-" * 64)
    for label, n in sorted(c["cost_labels"].items(), key=lambda x: -x[1]):
        print(f"  {label:<12} {n:>4} events")

    cost = c.get("cost")
    if cost:
        print()
        print("DOLLAR COST (computed from pricing.json — what this would meter at)")
        print("-" * 64)
        print(f"  {'model':<28} {'$total':>8}  {'cache_rd':>8} {'fresh_in':>8} "
              f"{'cache_wr':>8} {'output':>7}   cr%  out%")
        for m, p in cost["by_model"].items():
            s = p["split"]
            print(f"  {m:<28} {p['total']:>8.2f}  {s['cache_read']:>8.2f} {s['fresh_in']:>8.2f} "
                  f"{s['cache_write']:>8.2f} {s['output']:>7.2f}  {p['cache_read_share']:>4.0f} "
                  f"{p['output_share']:>4.0f}")
        print("-" * 64)
        print(f"  {'GRAND TOTAL':<28} {cost['grand_total']:>8.2f}")
        if cost["unpriced_models"]:
            print(f"  (unpriced, excluded: {', '.join(cost['unpriced_models'])})")
        sub = cost.get("substitution")
        if sub:
            print()
            print(f"  WHAT-IF: run {sub['from']} tokens at {sub['to']} rates")
            print(f"    {sub['from']:<22} ${sub['current_cost']:.2f}  ->  "
                  f"{sub['to']}: ${sub['new_cost']:.2f}   "
                  f"saves ${sub['saving']:.2f} ({sub['saving_pct']:.0f}%)")
            print(f"    session grand total: ${cost['grand_total']:.2f} -> "
                  f"${sub['new_grand_total']:.2f}")


def load_pricing(path: str | None) -> dict | None:
    if path is None:
        default = os.path.join(os.path.dirname(__file__), "pricing.json")
        path = default if os.path.exists(default) else None
    if not path:
        return None
    if not os.path.exists(path):
        sys.exit(f"Pricing file not found: {path}")
    data = json.load(open(path))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def main() -> None:
    p = argparse.ArgumentParser(
        description="Attribute usage-CSV tokens to a session by time window."
    )
    p.add_argument("--csv", required=True, help="usage export CSV path")
    p.add_argument("--start", help="window start ISO prefix (with --end, skips stdin)")
    p.add_argument("--end", help="window end ISO prefix")
    p.add_argument(
        "--pad-minutes", type=int, default=1, help="widen session window each side (default 1)"
    )
    p.add_argument(
        "--pricing", default=None,
        help="pricing JSON (default: tools/cursor/pricing.json if present; omit to skip $ cost)",
    )
    p.add_argument(
        "--no-pricing", action="store_true", help="force token-only output (skip dollar cost)"
    )
    p.add_argument(
        "--substitute", metavar="FROM:TO",
        help="what-if: cost FROM model's tokens at TO model's rates (e.g. glm-5.2-high:kimi-k2.5)",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    start, end, session_models, _ = load_window(args)
    pricing = None if args.no_pricing else load_pricing(args.pricing)
    sub = None
    if args.substitute:
        if ":" not in args.substitute:
            sys.exit("--substitute must be FROM:TO, e.g. glm-5.2-high:kimi-k2.5")
        sub = tuple(args.substitute.split(":", 1))
    result = compute(args.csv, start, end, session_models, pricing=pricing, substitute=sub)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)


if __name__ == "__main__":
    main()
