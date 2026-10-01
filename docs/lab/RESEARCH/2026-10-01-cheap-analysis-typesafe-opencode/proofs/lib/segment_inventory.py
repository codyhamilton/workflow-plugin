"""Spike 0 — segment inventory JSONL (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bootstrap import ensure_progressive_proofs
from early_window import early_window_end, label_60_grid, p0_75_grid
from pack_io import (
    evidence_class_from_fixture_indexed,
    evidence_class_from_pack,
    excerpt_nonempty,
    fixture_reread_stats,
    iter_pack_rows,
    max_reread_count,
)
from paths import (
    ALL_SPIKE0_WORKERS,
    CONTROL_WORKER,
    EXPECTED_T,
    JUDGE_PACK_BY_WORKER,
    REPO_ROOT,
    fixture_path,
)


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _segment_row(
    *,
    worker_id: str,
    T: int,
    window_id: str,
    grid: str | None,
    start: int,
    end: int,
    evidence_class: str,
    excerpt_nonempty_flag: bool,
    reread_present: bool,
    max_reread: int,
    compaction_event_count: int,
    source_path: str,
) -> dict[str, Any]:
    return {
        "worker_id": worker_id,
        "T": T,
        "early_window_end": early_window_end(T),
        "window_id": window_id,
        "grid": grid,
        "start": start,
        "end": end,
        "evidence_class": evidence_class,
        "excerpt_nonempty": excerpt_nonempty_flag,
        "reread_present": reread_present,
        "max_reread_count": max_reread,
        "compaction_event_count": compaction_event_count,
        "source_path": source_path,
    }


def _fixture_rows(worker_id: str, path: Path) -> list[dict[str, Any]]:
    ensure_progressive_proofs()
    from turn_index import index_transcript  # type: ignore

    indexed = index_transcript(path)
    T = indexed.T
    if worker_id in EXPECTED_T and T != EXPECTED_T[worker_id]:
        raise ValueError(f"{worker_id}: expected T={EXPECTED_T[worker_id]}, got {T}")
    ev = evidence_class_from_fixture_indexed(indexed)
    rel = _rel(path)
    rows: list[dict[str, Any]] = []
    ewe = early_window_end(T)
    rows.append(
        _segment_row(
            worker_id=worker_id,
            T=T,
            window_id="early_120",
            grid=None,
            start=1,
            end=ewe,
            evidence_class=ev,
            excerpt_nonempty_flag=False,
            reread_present=False,
            max_reread=0,
            compaction_event_count=0,
            source_path=rel,
        )
    )
    for grid_name, points in (
        ("label_60", label_60_grid(T)),
        ("p0_75", p0_75_grid(T)),
    ):
        for cp in points:
            rr_present, max_rr = fixture_reread_stats(indexed, cp)
            rows.append(
                _segment_row(
                    worker_id=worker_id,
                    T=T,
                    window_id="grid_15",
                    grid=grid_name,
                    start=1,
                    end=cp,
                    evidence_class=ev,
                    excerpt_nonempty_flag=False,
                    reread_present=rr_present,
                    max_reread=max_rr,
                    compaction_event_count=0,
                    source_path=rel,
                )
            )
    return rows


def _pack_rows(worker_id: str, pack_path: Path) -> list[dict[str, Any]]:
    T = EXPECTED_T[worker_id]
    rows: list[dict[str, Any]] = []
    for pack_row in iter_pack_rows(pack_path, worker_id):
        cp = int(pack_row["checkpoint_turn"])
        if cp == 60:
            raise ValueError(f"judge pack claims turn-60 checkpoint for {worker_id}")
        cum = pack_row.get("cumulative") or {}
        max_rr = max_reread_count(cum)
        rows.append(
            _segment_row(
                worker_id=worker_id,
                T=T,
                window_id="grid_15",
                grid="p0_75",
                start=1,
                end=cp,
                evidence_class=evidence_class_from_pack(pack_row),
                excerpt_nonempty_flag=excerpt_nonempty(pack_row),
                reread_present=max_rr >= 3,
                max_reread=max_rr,
                compaction_event_count=int(cum.get("compaction_event_count") or 0),
                source_path=_rel(pack_path),
            )
        )
    return rows


def build_inventory() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for worker_id in ALL_SPIKE0_WORKERS:
        fx = fixture_path(worker_id)
        if not fx.is_file():
            raise FileNotFoundError(f"missing fixture {fx}")
        out.extend(_fixture_rows(worker_id, fx))
        if worker_id in JUDGE_PACK_BY_WORKER:
            pack = JUDGE_PACK_BY_WORKER[worker_id]
            if pack.is_file():
                out.extend(_pack_rows(worker_id, pack))
    return out


def validate_inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Done-when checks for spike 0."""
    def pick(worker: str, **kw: Any) -> dict[str, Any] | None:
        for r in rows:
            if r["worker_id"] != worker:
                continue
            if all(r.get(k) == v for k, v in kw.items()):
                return r
        return None

    checks: dict[str, Any] = {}

    gun_early = pick("92a48e004519", window_id="early_120", grid=None)
    checks["92a48e_early_window_end_120"] = gun_early and gun_early["early_window_end"] == 120

    control_early = pick(CONTROL_WORKER, window_id="early_120", grid=None)
    checks["control_early_window_end_70"] = (
        control_early and control_early["early_window_end"] == 70
    )

    pack75 = pick(
        "92a48e004519",
        window_id="grid_15",
        grid="p0_75",
        end=75,
        evidence_class="stats_only",
    )
    checks["turn75_pack_stats_only"] = pack75 and pack75["evidence_class"] == "stats_only"
    checks["turn75_excerpt_empty"] = pack75 and pack75["excerpt_nonempty"] is False
    checks["turn75_reread_present"] = pack75 and pack75["reread_present"] is True
    checks["turn75_max_reread_ge_3"] = pack75 and pack75["max_reread_count"] >= 3

    fx75 = pick(
        "92a48e004519",
        window_id="grid_15",
        grid="label_60",
        end=75,
    )
    if fx75 and "maps-5h-workers" not in fx75["source_path"]:
        fx75 = None
    checks["fixture75_absent"] = fx75 is not None and fx75["evidence_class"] == "absent"
    checks["fixture75_no_reread"] = fx75 and fx75["reread_present"] is False

    label_points = sorted(
        {
            r["end"]
            for r in rows
            if r["worker_id"] == "92a48e004519"
            and r["window_id"] == "grid_15"
            and r["grid"] == "label_60"
            and "maps-5h-workers" in r["source_path"]
        }
    )
    checks["label_60_grid_92a48e"] = label_points == [60, 75, 90, 105, 120]

    p0_points = sorted(
        {
            r["end"]
            for r in rows
            if r["worker_id"] == "92a48e004519"
            and r["window_id"] == "grid_15"
            and r["grid"] == "p0_75"
            and "maps-5h-workers" in r["source_path"]
        }
    )
    checks["p0_75_no_60"] = 60 not in p0_points and p0_points == [75, 90, 105, 120]

    pack60 = [r for r in rows if r.get("end") == 60 and "judge-packs" in r["source_path"]]
    checks["no_pack_turn_60"] = len(pack60) == 0

    checks["all_pass"] = all(checks.values())
    return checks


def write_inventory(out_path: Path) -> dict[str, Any]:
    rows = build_inventory()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    checks = validate_inventory(rows)
    return {"row_count": len(rows), "checks": checks}
