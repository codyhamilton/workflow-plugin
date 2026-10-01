"""Marker families + stats-card fields from shape-qual packs (checkpoints ≤ 120 only)."""

from __future__ import annotations

import json
import sys
from typing import Any

from paths import CHEAP_LIB  # noqa: E402

if str(CHEAP_LIB) not in sys.path:
    sys.path.insert(0, str(CHEAP_LIB))

from pack_io import iter_pack_rows, max_reread_count  # noqa: E402

from paths import PACK_REL, SHAPE_QUAL_INVENTORY, SHAPE_QUAL_PACK  # noqa: E402
from theme_strata import stratum_for  # noqa: E402

EARLY_MAX = 120
BASH_READ_MONOPOLY = frozenset({"Bash", "Read", "ToolSearch"})


def _tool_count(hist: dict[str, Any], name: str) -> int:
    return int((hist or {}).get(name) or 0)


def _mutation_count(hist: dict[str, Any]) -> int:
    return _tool_count(hist, "Edit") + _tool_count(hist, "Write")


def _load_inventory() -> dict[str, int]:
    data = json.loads(SHAPE_QUAL_INVENTORY.read_text(encoding="utf-8"))
    return {w["worker_id"]: int(w["T"]) for w in data["workers"]}


def _early_rows(worker_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_pack_rows(SHAPE_QUAL_PACK, worker_id):
        cp = int(row["checkpoint_turn"])
        if cp <= EARLY_MAX:
            rows.append(row)
    rows.sort(key=lambda r: int(r["checkpoint_turn"]))
    return rows


def _round_trip_mismatch(
    first_row: dict[str, Any], last_row: dict[str, Any], features: dict[str, Any]
) -> list[str]:
    first_cum = first_row.get("cumulative") or {}
    last_cum = last_row.get("cumulative") or {}
    mismatches: list[str] = []
    last_pairs = [
        ("compaction_event_count", int(last_cum.get("compaction_event_count") or 0)),
        ("assistant_text_chars", int(last_cum.get("assistant_text_chars") or 0)),
        ("reread_max", max_reread_count(last_cum)),
    ]
    for key, expected in last_pairs:
        if features.get(key) != expected:
            mismatches.append(f"{key}: feature={features.get(key)!r} pack={expected!r}")
    expected_peak = int(first_cum.get("peak_ctx_tokens") or 0)
    if features.get("peak_ctx_first") != expected_peak:
        mismatches.append(
            f"peak_ctx_first: feature={features.get('peak_ctx_first')!r} pack={expected_peak!r}"
        )
    hist = last_cum.get("tool_histogram") or {}
    if features.get("tool_histogram_last") != dict(hist):
        mismatches.append("tool_histogram_last mismatch")
    return mismatches


def build_worker_features(worker_id: str, T: int) -> dict[str, Any]:
    early = _early_rows(worker_id)
    if not early:
        raise ValueError(f"{worker_id}: no pack rows with checkpoint_turn ≤ {EARLY_MAX}")

    first = early[0]
    last = early[-1]
    first_cum = first.get("cumulative") or {}
    last_cum = last.get("cumulative") or {}

    text_chars_series = [
        int((r.get("cumulative") or {}).get("assistant_text_chars") or 0) for r in early
    ]
    compaction_series = [
        int((r.get("cumulative") or {}).get("compaction_event_count") or 0) for r in early
    ]

    checkpoints_seen = len(early)
    frozen_text: bool | None
    if checkpoints_seen < 2:
        frozen_text = None
    else:
        frozen_text = len(set(text_chars_series)) == 1

    text_growth: int | None
    if checkpoints_seen < 2:
        text_growth = None
    else:
        text_growth = text_chars_series[-1] - text_chars_series[0]

    no_mutation = all(
        _mutation_count((r.get("cumulative") or {}).get("tool_histogram") or {}) == 0
        for r in early
    )
    mutation_present = _mutation_count(first_cum.get("tool_histogram") or {}) >= 1

    hist_last = last_cum.get("tool_histogram") or {}
    hist_keys = set(hist_last.keys())
    bash_read_monopoly = bool(hist_keys) and hist_keys <= BASH_READ_MONOPOLY

    monitor_first = _tool_count(first_cum.get("tool_histogram") or {}, "Monitor")
    monitor_present = monitor_first >= 1

    reread_max = max_reread_count(last_cum)
    reread_cluster = reread_max >= 3

    compaction_last = int(last_cum.get("compaction_event_count") or 0)
    compaction_delta = (
        compaction_series[-1] - compaction_series[0] if checkpoints_seen >= 1 else 0
    )

    peak_ctx = int(first_cum.get("peak_ctx_tokens") or 0)

    # Strict thrash-screen shape at last early checkpoint (reference cell, not a rubric).
    thrash_screen_strict = (
        no_mutation
        and reread_max >= 8
        and compaction_last >= 8
    )

    features: dict[str, Any] = {
        "frozen_text": frozen_text,
        "compaction_last_le120": compaction_last,
        "compaction_delta_le120": compaction_delta,
        "no_mutation": no_mutation,
        "reread_max": reread_max,
        "reread_cluster": reread_cluster,
        "bash_read_monopoly": bash_read_monopoly,
        "monitor_present_first": monitor_present,
        "monitor_count_first": monitor_first,
        "text_growth": text_growth,
        "mutation_present_first": mutation_present,
        "checkpoints_seen_le120": checkpoints_seen,
        "peak_ctx_first": peak_ctx,
        "assistant_text_chars_last": int(last_cum.get("assistant_text_chars") or 0),
        "compaction_event_count": compaction_last,
        "assistant_text_chars": int(last_cum.get("assistant_text_chars") or 0),
        "tool_histogram_last": dict(hist_last),
        "last_checkpoint_le120": int(last["checkpoint_turn"]),
        "thrash_screen_strict": thrash_screen_strict,
    }

    mismatches = _round_trip_mismatch(first, last, features)
    features["round_trip_mismatch"] = mismatches

    return {
        "worker_id": worker_id,
        "T": T,
        "early_window_end": min(EARLY_MAX, T),
        "stratum": stratum_for(worker_id),
        "markers": features,
        "source_pack": PACK_REL,
    }


def build_all_features() -> list[dict[str, Any]]:
    inventory = _load_inventory()
    rows = [build_worker_features(wid, T) for wid, T in sorted(inventory.items())]
    if len(rows) != 34:
        raise ValueError(f"expected 34 workers, got {len(rows)}")
    return rows
