"""Theme strata copied from OPEN-FIELD.md §2 (agreement note, not new labels)."""

from __future__ import annotations

from typing import Any

THRASH_CONSENSUS = frozenset({"ca977b9ca0dd", "92a48e004519"})

POLL_LABELS = frozenset(
    {"87a380bc64ff", "bb6165018de0", "15f24c7ba18c", "8e36f8e80baa"}
)

SHARED_MONITOR_WAIT = frozenset(
    {"87a380bc64ff", "bb6165018de0", "6e06ab86aa72"}
)

WEAK_THRASH = frozenset(
    {"07357f196666", "daf933273c8f", "de5b76cc68a6", "e28a2428b192"}
)


def stratum_for(worker_id: str) -> str:
    if worker_id in THRASH_CONSENSUS:
        return "thrash_consensus"
    if worker_id in POLL_LABELS:
        return "poll_label"
    if worker_id in WEAK_THRASH:
        return "weak_thrash"
    return "residual"


def strata_table() -> dict[str, Any]:
    return {
        "source": "docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/OPEN-FIELD.md §2",
        "thrash_consensus": sorted(THRASH_CONSENSUS),
        "poll_label": sorted(POLL_LABELS),
        "shared_monitor_wait": sorted(SHARED_MONITOR_WAIT),
        "weak_thrash": sorted(WEAK_THRASH),
        "note": "shared_monitor_wait overlaps poll_label; stratum assignment uses priority thrash > poll > weak > residual",
    }
