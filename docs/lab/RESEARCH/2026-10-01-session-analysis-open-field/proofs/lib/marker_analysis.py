"""Rank tables, Spearman, poll overlap, kill check for marker-screen phase 1a."""

from __future__ import annotations

import math
from typing import Any

from scipy import stats  # type: ignore

from theme_strata import POLL_LABELS, THRASH_CONSENSUS

NUMERIC_FAMILIES = [
    "compaction_last_le120",
    "compaction_delta_le120",
    "reread_max",
    "text_growth",
    "peak_ctx_first",
    "assistant_text_chars_last",
    "checkpoints_seen_le120",
    "monitor_count_first",
]

BOOLEAN_FAMILIES = [
    "frozen_text",
    "no_mutation",
    "bash_read_monopoly",
    "monitor_present_first",
    "mutation_present_first",
    "reread_cluster",
    "thrash_screen_strict",
]


def _percentile_rank(values: list[float], target: float) -> float:
    """Percentile 0–100 where higher = larger value (ties averaged)."""
    n = len(values)
    below = sum(1 for v in values if v < target)
    equal = sum(1 for v in values if v == target)
    return 100.0 * (below + 0.5 * equal) / n


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    rho, _ = stats.spearmanr(xs, ys)
    if math.isnan(rho):
        return None
    return float(rho)


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_worker = {r["worker_id"]: r for r in rows}
    T_vals = [float(r["T"]) for r in rows]

    numeric_analysis: dict[str, Any] = {}
    for fam in NUMERIC_FAMILIES:
        pairs: list[tuple[str, float]] = []
        for r in rows:
            val = r["markers"].get(fam)
            if val is None:
                continue
            pairs.append((r["worker_id"], float(val)))
        if len(pairs) < 3:
            numeric_analysis[fam] = {"skipped": "insufficient non-null values"}
            continue
        values = [p[1] for p in pairs]
        thrash_pct = {
            wid: _percentile_rank(values, by_worker[wid]["markers"][fam])
            for wid in THRASH_CONSENSUS
            if by_worker[wid]["markers"].get(fam) is not None
        }
        # Extreme cell: same boolean side as both prototypes for rank — top decile
        # where both prototypes sit (use max percentile of the two as anchor).
        anchor_pct = max(thrash_pct.values()) if thrash_pct else None
        extreme_workers: list[str] = []
        if anchor_pct is not None:
            for wid, val in pairs:
                pct = _percentile_rank(values, val)
                if pct >= anchor_pct - 1e-9:
                    extreme_workers.append(wid)
        poll_overlap = sorted(extreme_workers and (set(extreme_workers) & POLL_LABELS))

        xs = [float(by_worker[w]["markers"][fam]) for w, _ in pairs]
        ys = [float(by_worker[w]["T"]) for w, _ in pairs]
        xs_no_thrash = [
            float(by_worker[w]["markers"][fam])
            for w, _ in pairs
            if w not in THRASH_CONSENSUS
        ]
        ys_no_thrash = [
            float(by_worker[w]["T"]) for w, _ in pairs if w not in THRASH_CONSENSUS
        ]
        numeric_analysis[fam] = {
            "thrash_consensus_percentile": thrash_pct,
            "extreme_cell_workers": sorted(extreme_workers),
            "poll_label_overlap": poll_overlap,
            "spearman_vs_T": _spearman(xs, ys),
            "spearman_vs_T_without_thrash_prototypes": _spearman(
                xs_no_thrash, ys_no_thrash
            ),
        }

    boolean_analysis: dict[str, Any] = {}
    for fam in BOOLEAN_FAMILIES:
        thrash_vals = {
            wid: by_worker[wid]["markers"].get(fam) for wid in THRASH_CONSENSUS
        }
        if any(v is None for v in thrash_vals.values()):
            boolean_analysis[fam] = {"skipped": "null on thrash prototype"}
            continue
        if thrash_vals["ca977b9ca0dd"] != thrash_vals["92a48e004519"]:
            boolean_analysis[fam] = {
                "skipped": "thrash prototypes disagree",
                "values": thrash_vals,
            }
            continue
        target = thrash_vals["ca977b9ca0dd"]
        cell = sorted(
            r["worker_id"]
            for r in rows
            if r["markers"].get(fam) is not None and r["markers"][fam] == target
        )
        poll_overlap = sorted(set(cell) & POLL_LABELS)
        boolean_analysis[fam] = {
            "thrash_consensus_value": target,
            "extreme_cell_workers": cell,
            "poll_label_overlap": poll_overlap,
            "n_in_cell": len(cell),
        }

    # Combined strict thrash cell (thrash-screen shape at last cp ≤ 120).
    strict_cell = sorted(
        r["worker_id"] for r in rows if r["markers"].get("thrash_screen_strict")
    )
    poll_in_strict = sorted(set(strict_cell) & POLL_LABELS)
    kill_fired = len(poll_in_strict) > 0
    kill_status = "KILL" if kill_fired else "PASS"

    # Text growth quartiles among workers with checkpoints_seen >= 2
    growth_rows = [
        r
        for r in rows
        if r["markers"].get("text_growth") is not None
        and r["markers"]["checkpoints_seen_le120"] >= 2
    ]
    growth_vals = sorted(float(r["markers"]["text_growth"]) for r in growth_rows)
    n_g = len(growth_vals)
    q1_idx = n_g // 4
    q3_idx = (3 * n_g) // 4
    q1_cut = growth_vals[q1_idx] if n_g else None
    q3_cut = growth_vals[q3_idx] if n_g else None
    bottom = [
        r for r in growth_rows if float(r["markers"]["text_growth"]) <= q1_cut
    ] if q1_cut is not None else []
    top = [
        r for r in growth_rows if float(r["markers"]["text_growth"]) >= q3_cut
    ] if q3_cut is not None else []

    def median_t(sub: list[dict[str, Any]]) -> float | None:
        if not sub:
            return None
        ts = sorted(int(r["T"]) for r in sub)
        mid = len(ts) // 2
        if len(ts) % 2:
            return float(ts[mid])
        return (ts[mid - 1] + ts[mid]) / 2.0

    quartile_table = {
        "n_with_text_growth": n_g,
        "q1_cut": q1_cut,
        "q3_cut": q3_cut,
        "median_T_bottom_quartile": median_t(bottom),
        "median_T_top_quartile": median_t(top),
        "bottom_quartile_workers": [r["worker_id"] for r in bottom],
        "top_quartile_workers": [r["worker_id"] for r in top],
    }

    return {
        "numeric_families": numeric_analysis,
        "boolean_families": boolean_analysis,
        "combined_thrash_screen_strict": {
            "cell_workers": strict_cell,
            "poll_label_overlap": poll_in_strict,
            "kill_check": kill_status,
            "kill_criterion": (
                "Extreme thrash cell (thrash_screen_strict) must not contain poll-label workers"
            ),
        },
        "text_growth_quartiles": quartile_table,
    }
