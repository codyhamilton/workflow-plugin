#!/usr/bin/env python3
"""Exploratory Cox PH sketch — Alternate E (concordance gate ≤0.70 documented as future kill)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from lifelines import CoxPHFitter  # type: ignore

LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB.parent))

from theme_strata import THRASH_CONSENSUS  # noqa: E402

# Event time proxy for lab sketch only (standing agreement themes, not new gold).
# Uncensored at T for thrash_consensus; censored at T for all others.
EVENT_WORKERS = THRASH_CONSENSUS

COVARIATES = [
    "compaction_last_le120",
    "edit_write_absent",
    "reread_max",
]


def build_survival_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for r in rows:
        m = r["markers"]
        wid = r["worker_id"]
        duration = float(r["T"])
        if wid in EVENT_WORKERS:
            event = 1
            # Use last early checkpoint as observed event time (≤120), not full T.
            event_time = float(m["last_checkpoint_le120"])
        else:
            event = 0
            event_time = duration
        records.append(
            {
                "worker_id": wid,
                "duration": event_time,
                "event": event,
                "compaction_last_le120": float(m["compaction_last_le120"]),
                "edit_write_absent": 1.0 if m["no_mutation"] else 0.0,
                "reread_max": float(m["reread_max"]),
            }
        )
    return pd.DataFrame.from_records(records)


def run_sketch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    df = build_survival_frame(rows)
    n_events = int(df["event"].sum())
    cph = CoxPHFitter()
    note = (
        "Lab sketch only. Event = thrash_consensus theme (2 workers); "
        "all others right-censored at T. Not identified for 3 covariates; "
        "concordance is exploratory. Future gate: concordance ≤ 0.70 → kill Alternate E."
    )
    if n_events < 2:
        return {
            "status": "refused",
            "reason": "insufficient_events",
            "n_events": n_events,
            "note": note,
            "censoring": {
                "event_definition": "thrash_consensus stratum (ca977, 92a48e)",
                "censored_definition": "T with event=0 for residual/poll/weak",
            },
        }
    fit_df = df[["duration", "event", *COVARIATES]].copy()
    try:
        cph.fit(fit_df, duration_col="duration", event_col="event")
        concordance = float(cph.concordance_index_)
        summary = cph.summary.to_dict()
    except Exception as exc:  # noqa: BLE001 — lab sketch surfaces fit failures
        return {
            "status": "fit_failed",
            "error": str(exc),
            "n_events": n_events,
            "note": note,
        }
    future_kill = concordance <= 0.70
    return {
        "status": "exploratory_ok",
        "concordance_index": concordance,
        "future_gate_concordance_le_0_70": "KILL Alternate E if held on proper gold",
        "future_kill_would_fire": future_kill,
        "n_workers": len(df),
        "n_events": n_events,
        "covariates": COVARIATES,
        "censoring": {
            "event_definition": "thrash_consensus; event_time = last checkpoint ≤120",
            "censored_definition": "event=0; duration=T (productive / no theme event)",
        },
        "coefficients": {k: summary[k] for k in summary},
        "note": note,
    }


def main() -> int:
    features_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not features_path or not out_path:
        print("usage: run_cox_sketch.py marker_features.jsonl cox_sketch.json", file=sys.stderr)
        return 2
    rows = [json.loads(line) for line in features_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = run_sketch(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "concordance": result.get("concordance_index")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
