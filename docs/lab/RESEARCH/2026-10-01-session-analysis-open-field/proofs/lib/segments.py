"""Segments for open-field dry-run (stats cards → Jev state)."""

from __future__ import annotations

from typing import Any

from import_paths import ensure_import_paths

ensure_import_paths()

from early_window import early_window_end
from pack_io import pack_row_to_jev_state

from stats_card import build_stats_card


def stats_card_to_pack_row(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "worker_id": card["worker_id"],
        "checkpoint_turn": card["checkpoint_turn"],
        "schedule": {"first_at": 75, "interval": 15},
        "brief_anchor": card.get("brief_anchor") or "",
        "cumulative": card.get("cumulative") or {},
        "delta_since_prior": {},
        "tail": [],
    }


def segment_from_stats_card(card: dict[str, Any]) -> dict[str, Any]:
    T = int(card["T"])
    ewe = early_window_end(T)
    end = int(card["checkpoint_turn"])
    row = stats_card_to_pack_row(card)
    return {
        "segment_id": f"{card['worker_id']}:stats_card:{end}",
        "worker_id": card["worker_id"],
        "T": T,
        "early_window_end": ewe,
        "start": 1,
        "end": end,
        "evidence_class": card.get("evidence_class") or "stats_only",
        "state": pack_row_to_jev_state(row),
        "card_hash": card["card_hash"],
    }


def segments_for_workers(worker_ids: tuple[str, ...], T_by_worker: dict[str, int]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for wid in worker_ids:
        card = build_stats_card(wid, T=T_by_worker[wid])
        out.append(segment_from_stats_card(card))
    return out
