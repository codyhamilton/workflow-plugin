"""Build segment records with Jev state for spikes 1–2."""

from __future__ import annotations

from typing import Any

from bootstrap import ensure_progressive_proofs
from early_window import early_window_end
from pack_io import iter_pack_rows, pack_row_to_jev_state
from paths import JUDGE_PACK_BY_WORKER, WORKERS_T_GE_75


def stats_segment_turn75() -> dict[str, Any]:
    worker = "92a48e004519"
    pack = JUDGE_PACK_BY_WORKER[worker]
    row = next(iter_pack_rows(pack, worker))
    if int(row["checkpoint_turn"]) != 75:
        raise RuntimeError("expected first pack row at turn 75")
    T = 296
    state = pack_row_to_jev_state(row)
    return {
        "segment_id": f"{worker}:grid_15:75:pack",
        "worker_id": worker,
        "T": T,
        "early_window_end": early_window_end(T),
        "start": 1,
        "end": 75,
        "evidence_class": "stats_only",
        "state": state,
    }


def prose_segment_if_mounted() -> dict[str, Any] | None:
    ensure_progressive_proofs()
    from paths import fixture_path
    from turn_index import index_transcript  # type: ignore

    from pack_io import evidence_class_from_fixture_indexed

    worker = "92a48e004519"
    path = fixture_path(worker)
    indexed = index_transcript(path)
    if evidence_class_from_fixture_indexed(indexed) != "prose":
        return None
    ensure_progressive_proofs()
    from snapshot_state import prepare_hybrid_state  # type: ignore

    state, _ = prepare_hybrid_state(indexed, 75, first_at=75, interval=15, prior=None)
    if state is None:
        return None
    return {
        "segment_id": f"{worker}:grid_15:75:fixture-prose",
        "worker_id": worker,
        "T": indexed.T,
        "early_window_end": early_window_end(indexed.T),
        "start": 1,
        "end": 75,
        "evidence_class": "prose",
        "state": state,
    }


def segments_for_spike2() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for worker in WORKERS_T_GE_75:
        T = {"92a48e004519": 296, "bb6165018de0": 154, "0aab88c525de": 192, "036ff3ed4a89": 161}[
            worker
        ]
        ewe = early_window_end(T)
        pack = JUDGE_PACK_BY_WORKER[worker]
        early_row = None
        for pack_row in iter_pack_rows(pack, worker):
            if int(pack_row["checkpoint_turn"]) == ewe:
                early_row = pack_row
                break
        if early_row is None:
            early_row = max(
                iter_pack_rows(pack, worker),
                key=lambda r: int(r["checkpoint_turn"]),
            )
        out.append(
            {
                "segment_id": f"{worker}:early_120",
                "worker_id": worker,
                "T": T,
                "early_window_end": ewe,
                "start": 1,
                "end": ewe,
                "evidence_class": "stats_only",
                "state": pack_row_to_jev_state(early_row),
            }
        )
        for pack_row in iter_pack_rows(pack, worker):
            cp = int(pack_row["checkpoint_turn"])
            if cp > ewe:
                continue
            out.append(
                {
                    "segment_id": f"{worker}:grid_15:{cp}",
                    "worker_id": worker,
                    "T": T,
                    "early_window_end": ewe,
                    "start": 1,
                    "end": cp,
                    "evidence_class": "stats_only",
                    "state": pack_row_to_jev_state(pack_row),
                }
            )
    return out
