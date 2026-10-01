"""Read judge packs and derive segment metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def iter_pack_rows(path: Path, worker_id: str | None = None) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if worker_id is not None and row.get("worker_id") != worker_id:
                continue
            yield row


def max_reread_count(cumulative: dict[str, Any]) -> int:
    paths = cumulative.get("reread_paths") or []
    best = 0
    for entry in paths:
        if isinstance(entry, dict):
            best = max(best, int(entry.get("count") or 0))
    return best


def excerpt_nonempty(row: dict[str, Any]) -> bool:
    for item in row.get("tail") or []:
        if isinstance(item, dict) and str(item.get("excerpt") or "").strip():
            return True
    return False


def pack_row_to_jev_state(row: dict[str, Any]) -> dict[str, Any]:
    """Map a committed judge-pack row to session-checkout-shaped Jev state."""
    checkpoint = int(row["checkpoint_turn"])
    schedule = row.get("schedule") or {}
    return {
        "question_id": "early-signal-v0",
        "jev_model": "jev-1.13.0",
        "worker_id": row["worker_id"],
        "checkpoint_turn": checkpoint,
        "prior_checkpoint_turn": row.get("prior_checkpoint_turn"),
        "schedule": {
            "first_at": schedule.get("first_at", 75),
            "interval": schedule.get("interval", 15),
        },
        "brief_anchor": row.get("brief_anchor") or "",
        "cumulative": row.get("cumulative") or {},
        "delta_since_prior": row.get("delta_since_prior") or {},
        "tail": row.get("tail") or [],
    }


def evidence_class_from_pack(row: dict[str, Any]) -> str:
    cum = row.get("cumulative") or {}
    has_stats = bool(cum.get("reread_paths")) or int(cum.get("compaction_event_count") or 0) > 0
    if excerpt_nonempty(row):
        return "prose"
    if has_stats:
        return "stats_only"
    return "absent"


def _redacted_placeholder_only(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith("[REDACTED]"):
            return False
    return True


def evidence_class_from_fixture_indexed(indexed: Any) -> str:
    """Redacted JSONL: placeholder text is not prose; empty read paths → absent."""
    from turn_index import IndexedTranscript  # type: ignore

    if not isinstance(indexed, IndexedTranscript):
        raise TypeError("expected IndexedTranscript")
    for turn in indexed.turns:
        if not _redacted_placeholder_only(turn.text):
            return "prose"
    return "absent"


def fixture_reread_stats(indexed: Any, checkpoint: int) -> tuple[bool, int]:
    from turn_index import IndexedTranscript  # type: ignore

    if not isinstance(indexed, IndexedTranscript):
        raise TypeError("expected IndexedTranscript")
    counts: dict[str, int] = {}
    for turn in indexed.turns[:checkpoint]:
        for path in turn.read_paths:
            counts[path] = counts.get(path, 0) + 1
    max_count = max(counts.values()) if counts else 0
    return max_count >= 3, max_count
