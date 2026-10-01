"""Local segment grid for segment-swarm-arbiter (pack checkpoints ≤ early_window_end)."""

from __future__ import annotations

from typing import Any

from paths import AGREEMENT_MATRIX, STRATIFIED_EIGHT
from segments import segment_from_stats_card
from stats_card import build_stats_card_at_checkpoint, rows_for_worker, worker_T_from_matrix
from paths import SHAPE_QUAL_PACK


def swarm_cells_for_worker(worker_id: str, T: int) -> list[dict[str, Any]]:
    """One local completion per pack checkpoint row ≤ min(120, T)."""
    ewe = min(120, T)
    cells: list[dict[str, Any]] = []
    for row in rows_for_worker(SHAPE_QUAL_PACK, worker_id):
        cp = int(row["checkpoint_turn"])
        if cp > ewe:
            continue
        card = build_stats_card_at_checkpoint(worker_id, T=T, checkpoint_turn=cp)
        seg = segment_from_stats_card(card)
        cells.append(
            {
                "worker_id": worker_id,
                "checkpoint_turn": cp,
                "segment_id": seg["segment_id"],
                "early_window_end": ewe,
                "theme_guess_slot": "{thrash_bundle,poll_monitor,productive,unknown}",
                "phase_tags_slot": "cheap-analysis closed phase tags",
                "cache": "bypass",
                "backend": "local",
                "local_url_env": "WORKFLOW_LOCAL_LLM_URL",
                "default_url": "http://127.0.0.1:8080/v1",
            }
        )
    return cells


def pilot_swarm_plan() -> dict[str, Any]:
    T_map = worker_T_from_matrix(AGREEMENT_MATRIX)
    cells: list[dict[str, Any]] = []
    for wid in STRATIFIED_EIGHT:
        cells.extend(swarm_cells_for_worker(wid, T_map[wid]))
    return {
        "workers": list(STRATIFIED_EIGHT),
        "expected_local_completions_mid": 24,
        "note": "Actual cell_count depends on pack checkpoints ≤ 120 per worker",
        "cell_count": len(cells),
        "flash_arbiter_cap": 4,
        "kill_conflict_workers_gt": 4,
        "cells": cells,
    }
