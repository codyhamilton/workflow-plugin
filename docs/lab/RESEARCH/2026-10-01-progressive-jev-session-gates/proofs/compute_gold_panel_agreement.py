#!/usr/bin/env python3
"""Compute A0 and Krippendorff nominal alpha for three-seat gold checkout panels.

Lab analysis only — not wired into run_proofs.sh. Uses the `krippendorff` package when
installed; otherwise a stdlib binary nominal implementation (same coincidence-matrix
definition for complete 3-coder units).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

PROOFS = Path(__file__).resolve().parent
GOLD = PROOFS / "validated" / "gold"

SEAT_FILES = {
    "sonnet": "expansion-checkout-verdicts-sonnet-20261001.jsonl",
    "composer": "expansion-checkout-verdicts-composer-20261001.jsonl",
    "grok": "expansion-checkout-verdicts-grok-20261001.jsonl",
}


def _load_sonnet_p0(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("signed") and row.get("role") == "reviewer_final":
            rows.append(row)
    return rows


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _unit_key(row: dict[str, Any]) -> tuple[str, int]:
    return (row["worker_id"], int(row["checkpoint_turn"]))


def build_matrix(
    seat_rows: dict[str, list[dict[str, Any]]],
    seat_order: tuple[str, ...],
) -> tuple[list[tuple[str, int]], list[list[int]]]:
    by_unit: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)
    for seat in seat_order:
        for row in seat_rows[seat]:
            by_unit[_unit_key(row)][seat] = int(row["checkout_recommended"])
    keys = sorted(by_unit.keys())
    matrix = [[by_unit[k][s] for s in seat_order] for k in keys]
    return keys, matrix


def a0_unanimous(keys: list[tuple[str, int]], matrix: list[list[int]]) -> dict[str, int | None]:
    workers = sorted({k[0] for k in keys})
    out: dict[str, int | None] = {}
    for worker in workers:
        gold: int | None = None
        for (wid, turn), vals in zip(keys, matrix):
            if wid != worker:
                continue
            if all(v == 1 for v in vals):
                gold = turn
                break
        out[worker] = gold
    return out


def earliest_checkout_by_seat(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, dict[str, int | None]]:
    workers = sorted({k[0] for k in keys})
    out: dict[str, dict[str, int | None]] = {s: {} for s in seat_order}
    for seat_idx, seat in enumerate(seat_order):
        for worker in workers:
            earliest: int | None = None
            for (wid, turn), vals in zip(keys, matrix):
                if wid != worker:
                    continue
                if vals[seat_idx] == 1:
                    earliest = turn
                    break
            out[seat][worker] = earliest
    return out


def checkout_positive_counts(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, int]:
    counts = {s: 0 for s in seat_order}
    for vals in matrix:
        for seat_idx, seat in enumerate(seat_order):
            counts[seat] += vals[seat_idx]
    return counts


def cohen_kappa_binary(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    p1 = sum(a) / n
    p2 = sum(b) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    if pe >= 1.0:
        return 0.0
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal_binary(matrix: list[list[int]]) -> float:
    """Nominal alpha for binary labels; units with <2 coders are skipped."""
    try:
        import krippendorff  # type: ignore
        import numpy as np

        arr = np.array(matrix, dtype=float)
        return float(
            krippendorff.alpha(
                reliability_data=arr.T,
                level_of_measurement="nominal",
            )
        )
    except ImportError:
        pass

    # Stdlib fallback: coincidence matrix for values 0 and 1 (V=2).
    value_counts: list[tuple[int, int]] = []
    for row in matrix:
        n1 = sum(row)
        n0 = len(row) - n1
        if n0 + n1 < 2:
            continue
        value_counts.append((n0, n1))
    if not value_counts:
        return float("nan")

    def coincidences(n0: int, n1: int) -> list[list[float]]:
        pairable = max(n0 + n1, 2)
        denom = pairable * (pairable - 1)
        o00 = n0 * (n0 - 1) / denom
        o11 = n1 * (n1 - 1) / denom
        o01 = 2 * n0 * n1 / denom
        return [[o00, o01], [o01, o11]]

    o = [[0.0, 0.0], [0.0, 0.0]]
    for n0, n1 in value_counts:
        c = coincidences(n0, n1)
        for i in range(2):
            for j in range(2):
                o[i][j] += c[i][j]

    n_v = [o[0][0] + o[0][1], o[1][0] + o[1][1]]
    n_total = n_v[0] + n_v[1]
    if n_total <= 0:
        return float("nan")
    e = [
        [n_v[0] * (n_v[0] - 1) / (n_total - 1), n_v[0] * n_v[1] / (n_total - 1)],
        [n_v[1] * n_v[0] / (n_total - 1), n_v[1] * (n_v[1] - 1) / (n_total - 1)],
    ]
    d_nominal = [[0.0, 1.0], [1.0, 0.0]]
    do = sum(o[i][j] * d_nominal[i][j] for i in range(2) for j in range(2))
    de = sum(e[i][j] * d_nominal[i][j] for i in range(2) for j in range(2))
    if de == 0:
        return 1.0
    return 1.0 - do / de


def pairwise_metrics(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, Any]:
    cols = {seat: [row[i] for row in matrix] for i, seat in enumerate(seat_order)}
    pairs: dict[str, Any] = {}
    for s1, s2 in combinations(seat_order, 2):
        a, b = cols[s1], cols[s2]
        n = len(a)
        agree = sum(x == y for x, y in zip(a, b)) / n if n else float("nan")
        pairs[f"{s1}_vs_{s2}"] = {
            "overall_pct": round(100 * agree, 2),
            "cohen_kappa": round(cohen_kappa_binary(a, b), 4),
        }
    return pairs


def expansion_panel() -> dict[str, Any]:
    seat_order = ("sonnet", "composer", "grok")
    seat_rows = {seat: _load_jsonl(GOLD / fname) for seat, fname in SEAT_FILES.items()}
    keys, matrix = build_matrix(seat_rows, seat_order)
    alpha = krippendorff_alpha_nominal_binary(matrix)
    pos = checkout_positive_counts(keys, matrix, seat_order)
    workers = sorted({k[0] for k in keys})
    worker_cps = {w: sum(1 for k in keys if k[0] == w) for w in workers}
    return {
        "generated_for": "experiment (c) corpus-expand-hybrid-panel-original",
        "panel": {
            "seats": list(seat_order),
            "sources": {s: SEAT_FILES[s] for s in seat_order},
            "schedule": "P0 first_at=75 interval=15",
        },
        "n_checkpoints": len(keys),
        "workers": worker_cps,
        "earliest_checkout_recommended_by_seat": earliest_checkout_by_seat(keys, matrix, seat_order),
        "a0_unanimous_checkout": {
            "rule": "Earliest checkpoint turn c where sonnet, composer, and grok all have checkout_recommended=true at that prefix",
            "by_worker": a0_unanimous(keys, matrix),
        },
        "krippendorff_alpha": {
            "scale": "nominal",
            "variable": "checkout_recommended (binary)",
            "coders": 3,
            "units": len(keys),
            "value": round(alpha, 4),
            "h5_floor": 0.4,
            "h5_pass": bool(alpha >= 0.4),
            "alpha_method": "krippendorff",
        },
        "checkout_positive_counts": {**pos, "total_true_labels": sum(pos.values())},
        "pairwise_agreement": pairwise_metrics(keys, matrix, seat_order),
        "notes": [
            "Expansion workers: 0aab88c525de, 036ff3ed4a89, 0853bc21d3aa (20 pooled prefixes).",
            "A0 null on all three — no unanimous checkout even though raw agreement is high (prevalence of not_yet).",
            "H5 fails on expansion-only α; usable gold for A0 tuning still blocked. No Jev sweep.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=GOLD / "expansion-panel-agreement-20261001.json",
        help="Write machine-readable agreement JSON",
    )
    parser.add_argument("--print-alpha", action="store_true", help="Print nominal alpha to stdout")
    args = parser.parse_args()
    report = expansion_panel()
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if args.print_alpha:
        print(report["krippendorff_alpha"]["value"])


if __name__ == "__main__":
    main()
