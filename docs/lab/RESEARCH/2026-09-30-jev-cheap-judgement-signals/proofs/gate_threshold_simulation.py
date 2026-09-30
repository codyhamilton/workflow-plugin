#!/usr/bin/env python3
"""Replay maps fixtures through gate_thresholds; print JSON summary for proofs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from gate_thresholds import BAND_EXIT_TURNS, ESCALATE_TURNS, evaluate_gate, thresholds_documentation

FIXTURE = Path(__file__).parent / "fixtures" / "maps_named_workers.json"


def main() -> int:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    workers = data["workers"]
    agg = data["aggregates"]

    results = []
    for w in workers:
        g = evaluate_gate(
            api_turns=w["api_turns"],
            peak_ctx_tokens=w.get("peak_ctx"),
            transcript_bytes=w.get("jsonl_bytes"),
        )
        first_band_exit_turn = BAND_EXIT_TURNS if w["api_turns"] >= BAND_EXIT_TURNS else None
        first_escalate_turn = ESCALATE_TURNS if w["api_turns"] >= ESCALATE_TURNS else None
        results.append(
            {
                "id": w["id"],
                "api_turns": w["api_turns"],
                "gate": g.to_dict(),
                "first_band_exit_turn": first_band_exit_turn,
                "first_escalate_turn": first_escalate_turn,
                "maps_flags": w.get("flags", []),
            }
        )

    # Lower bound: all workers with turns >= 100 must escalate.
    over_100 = [w for w in workers if w["api_turns"] >= ESCALATE_TURNS]
    escalate_hits = sum(1 for r in results if r["gate"]["escalate"])

    out = {
        "thresholds": thresholds_documentation(),
        "maps_aggregates": agg,
        "workers": results,
        "checks": {
            "all_over_100_workers_escalate": escalate_hits == len(over_100),
            "smoking_gun_band_exit_before_100": any(
                r["id"] == "92a48e004519" and r["gate"]["band_exit"] for r in results
            ),
            "smoking_gun_escalate": any(
                r["id"] == "92a48e004519" and r["gate"]["escalate"] for r in results
            ),
        },
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if all(out["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
