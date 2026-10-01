"""Stats-card placeholder from shape-qual judge packs (phase 1a dependency)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from import_paths import ensure_import_paths

ensure_import_paths()

from early_window import early_window_end
from pack_io import excerpt_nonempty, iter_pack_rows, max_reread_count

from paths import SHAPE_QUAL_PACK


def _canonical_card_json(card: dict[str, Any]) -> str:
    return json.dumps(card, ensure_ascii=False, sort_keys=True)


def card_hash(card: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_card_json(card).encode("utf-8")).hexdigest()


def worker_T_from_matrix(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for row in data.get("workers") or data.get("rows") or []:
        wid = row.get("worker_id")
        t = row.get("T")
        if wid and isinstance(t, int):
            out[str(wid)] = t
    return out


def rows_for_worker(pack: Path, worker_id: str) -> list[dict[str, Any]]:
    return [r for r in iter_pack_rows(pack, worker_id) if int(r["checkpoint_turn"]) <= 120]


def build_stats_card(
    worker_id: str,
    *,
    T: int,
    pack: Path = SHAPE_QUAL_PACK,
) -> dict[str, Any]:
    ewe = early_window_end(T)
    checkpoints: list[dict[str, Any]] = []
    target_row: dict[str, Any] | None = None
    for row in rows_for_worker(pack, worker_id):
        cp = int(row["checkpoint_turn"])
        cum = row.get("cumulative") or {}
        checkpoints.append(
            {
                "checkpoint_turn": cp,
                "compaction_event_count": int(cum.get("compaction_event_count") or 0),
                "assistant_text_chars": int(cum.get("assistant_text_chars") or 0),
                "max_reread_count": max_reread_count(cum),
                "excerpt_nonempty": excerpt_nonempty(row),
            }
        )
        if cp <= ewe and (target_row is None or cp > int(target_row["checkpoint_turn"])):
            target_row = row
    if target_row is None:
        raise ValueError(f"no pack row ≤ {ewe} for {worker_id}")

    cum = target_row.get("cumulative") or {}
    card: dict[str, Any] = {
        "card_kind": "stats_card_placeholder",
        "dependency": "phase_1a_stats_card_extractor_not_merged; built from shape-qual pack rows",
        "worker_id": worker_id,
        "T": T,
        "early_window_end": ewe,
        "checkpoint_turn": int(target_row["checkpoint_turn"]),
        "checkpoints_seen": checkpoints,
        "cumulative": cum,
        "brief_anchor": (target_row.get("brief_anchor") or "")[:500],
        "evidence_class": "stats_only" if not excerpt_nonempty(target_row) else "prose",
    }
    card["card_hash"] = card_hash(card)
    return card


def build_stats_card_at_checkpoint(
    worker_id: str,
    *,
    T: int,
    checkpoint_turn: int,
    pack: Path = SHAPE_QUAL_PACK,
) -> dict[str, Any]:
    """Stats card frozen at one pack checkpoint (for segment-swarm grid)."""
    ewe = early_window_end(T)
    if checkpoint_turn > ewe:
        raise ValueError(f"checkpoint {checkpoint_turn} > early_window_end {ewe}")
    row = next(
        (r for r in rows_for_worker(pack, worker_id) if int(r["checkpoint_turn"]) == checkpoint_turn),
        None,
    )
    if row is None:
        raise ValueError(f"no pack row at cp {checkpoint_turn} for {worker_id}")
    cum = row.get("cumulative") or {}
    card: dict[str, Any] = {
        "card_kind": "stats_card_placeholder",
        "dependency": "phase_1a_stats_card_extractor_not_merged; built from shape-qual pack rows",
        "worker_id": worker_id,
        "T": T,
        "early_window_end": ewe,
        "checkpoint_turn": checkpoint_turn,
        "checkpoints_seen": [
            {
                "checkpoint_turn": checkpoint_turn,
                "compaction_event_count": int(cum.get("compaction_event_count") or 0),
                "assistant_text_chars": int(cum.get("assistant_text_chars") or 0),
                "max_reread_count": max_reread_count(cum),
                "excerpt_nonempty": excerpt_nonempty(row),
            }
        ],
        "cumulative": cum,
        "brief_anchor": (row.get("brief_anchor") or "")[:500],
        "evidence_class": "stats_only" if not excerpt_nonempty(row) else "prose",
    }
    card["card_hash"] = card_hash(card)
    return card


def manifest_all_workers(
    worker_ids: Iterator[str],
    T_by_worker: dict[str, int],
    *,
    pack: Path = SHAPE_QUAL_PACK,
) -> list[dict[str, Any]]:
    return [build_stats_card(wid, T=T_by_worker[wid], pack=pack) for wid in worker_ids]
