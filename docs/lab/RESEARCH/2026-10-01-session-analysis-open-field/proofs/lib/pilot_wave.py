"""Pilot field-proof wave constants (RESOURCE-BUDGET-AGGRESSIVE Pilot tier)."""

from __future__ import annotations

import hashlib
from typing import Any

from paths import STRATIFIED_EIGHT

REGISTRATION_ID = "pilot-field-proof-wave-001"
MODEL_PIN = "jev-1.13.0"
SCHEMA_ID = "early-signal-v0"
MAX_CALLS = 88
BUDGET_TOKENS = 400_000
TOKEN_ASSUMPTION_MID = 2_000

TOURNAMENT_FRAMINGS = (
    "tournament-binary-foreshadow",
    "tournament-likert-collapsed",
    "tournament-no-story-beyond-counts",
)

# KILL (pilot): tournament-monitor-called-out — poll FP with thrash; not in registry.

PILOT_POOL_SLUGS = (
    *TOURNAMENT_FRAMINGS,
    "pool-likert-foreshadow",
    "pool-echo-guard-reread",
    "pool-phase-hint-stats",
    "pool-anchor-agnostic",
    "pool-thrash-card-anchor",
    "pool-residual-baseline",
    "signal-v0-default",
    "signal-v0-alt",
)

SEARCH_WORKERS = STRATIFIED_EIGHT[:6]
BASELINE_SEED = "pilot-field-proof-wave-001-baseline-v1"


def _full_cartesian() -> list[dict[str, str]]:
    return [
        {"worker_id": wid, "framing_slug": slug}
        for wid in STRATIFIED_EIGHT
        for slug in PILOT_POOL_SLUGS
    ]


def _baseline_pairs(cartesian: list[dict[str, str]], reserved: set[tuple[str, str]]) -> list[dict[str, str]]:
    """Eight reproducible baseline draws from cells not in the search arm."""
    candidates = [c for c in cartesian if (c["worker_id"], c["framing_slug"]) not in reserved]
    out: list[dict[str, str]] = []
    used: set[tuple[str, str]] = set()
    i = 0
    while len(out) < 8 and i < len(candidates) * 4:
        digest = hashlib.sha256(f"{BASELINE_SEED}:{i}".encode()).hexdigest()
        idx = int(digest[:8], 16) % len(candidates)
        cell = candidates[idx]
        key = (cell["worker_id"], cell["framing_slug"])
        if key not in used and key not in reserved:
            out.append(cell)
            used.add(key)
        i += 1
    if len(out) < 8:
        for cell in candidates:
            key = (cell["worker_id"], cell["framing_slug"])
            if key in used or key in reserved:
                continue
            out.append(cell)
            used.add(key)
            if len(out) == 8:
                break
    return out


def pilot_jev_cell_plan() -> dict[str, Any]:
    """88-cell plan: full 8×11 matrix; arms 8 baseline + 18 search + 62 matrix fill."""
    cartesian = _full_cartesian()
    assert len(cartesian) == MAX_CALLS

    search_pairs = {(wid, slug) for wid in SEARCH_WORKERS for slug in TOURNAMENT_FRAMINGS}
    search_cells = [
        {"arm": "search", "worker_id": wid, "framing_slug": slug}
        for wid in SEARCH_WORKERS
        for slug in TOURNAMENT_FRAMINGS
    ]
    baseline_raw = _baseline_pairs(cartesian, search_pairs)
    baseline_cells = [{"arm": "baseline", **c} for c in baseline_raw]
    tagged = search_pairs | {(c["worker_id"], c["framing_slug"]) for c in baseline_raw}

    fill_cells = [
        {"arm": "matrix_fill", "worker_id": c["worker_id"], "framing_slug": c["framing_slug"]}
        for c in cartesian
        if (c["worker_id"], c["framing_slug"]) not in tagged
    ]

    ordered = baseline_cells + search_cells + fill_cells
    assert len(ordered) == MAX_CALLS
    assert len({(c["worker_id"], c["framing_slug"]) for c in ordered}) == MAX_CALLS

    return {
        "registration_id": REGISTRATION_ID,
        "max_calls": MAX_CALLS,
        "budget_tokens": BUDGET_TOKENS,
        "waves": [{"wave_index": 1, "cells": MAX_CALLS, "cap": 256}],
        "baseline_arm_calls": 8,
        "search_arm_calls": 24,
        "matrix_fill_calls": len(fill_cells),
        "framing_pool_size": len(PILOT_POOL_SLUGS),
        "cells": ordered,
    }
