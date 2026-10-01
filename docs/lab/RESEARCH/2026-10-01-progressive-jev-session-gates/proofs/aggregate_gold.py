#!/usr/bin/env python3
"""Aggregate CHM gold verdicts into ``validated/gold/summary.json``.

Reads verdict JSON under a directory (default ``validated/gold/``). On
``p0-checkout-verdicts-20261001.jsonl``, only ``signed: true`` Sonnet rows
vote. Unsigned Flash drafts are reported and do not set ``gold_exit``.
``grok-4.7-high`` and ``composer`` stay pending seats. Primary ``gold_exit``
stays null until three seats have voted. This script does not invent an exit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gold_panel import aggregate_labels, load_labels

PROOFS = Path(__file__).resolve().parent
DEFAULT_LABELS = PROOFS / "validated" / "gold"
DEFAULT_OUT = DEFAULT_LABELS / "summary.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate multi-model gold verdicts (A0)")
    parser.add_argument(
        "--labels",
        type=Path,
        default=DEFAULT_LABELS,
        help="Verdict JSON/JSONL file or directory. pending/ is skipped unless --include-pending",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Also read validated/gold/pending stubs (they stay null and do not vote)",
    )
    parser.add_argument("--primary-min-judges", type=int, default=3)
    parser.add_argument("--diagnostic-min-judges", type=int, default=2)
    args = parser.parse_args(argv)

    if not args.labels.exists():
        raise SystemExit(f"labels path not found: {args.labels}")
    labels = load_labels(args.labels, include_pending=args.include_pending)
    summary = aggregate_labels(
        labels,
        primary_min_judges=args.primary_min_judges,
        diagnostic_min_judges=args.diagnostic_min_judges,
    )
    summary["labels_path"] = str(args.labels)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(
        json.dumps(
            {
                "status": summary["status"],
                "n_labels_filled": summary["n_labels_filled"],
                "n_labels_pending": summary["n_labels_pending"],
                "alpha": summary["alpha"],
                "h5": summary["h5"],
                "workers": [
                    {
                        "worker_id": row["worker_id"],
                        "panel": row["panel"],
                        "gold_exit": row["gold_exit"],
                        "gold_exit_unanimous_min2": row["gold_exit_unanimous_min2"],
                    }
                    for row in summary["workers"]
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
