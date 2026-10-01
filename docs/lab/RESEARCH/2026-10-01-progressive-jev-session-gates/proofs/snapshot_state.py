"""hybrid_v0 Jev state and the larger gold-judge bundle.

State JSON is ``len(json.dumps(state, ensure_ascii=False))`` and must stay
within 12_000 characters (TERMS §5). The judge bundle is a different object,
capped at 60_000 characters. Jev never receives the judge bundle.
"""

from __future__ import annotations

import json
import re
from typing import Any

from turn_index import IndexedTranscript, first_user_text, is_compaction_row

JEV_MODEL = "jev-1.13.0"
STATE_CHAR_LIMIT = 12_000
REQUEST_CHAR_SOFT = 16_000
GOLD_BUNDLE_CHAR_LIMIT = 60_000
BRIEF_CAP = 500
HYBRID_TAIL_N = 8
HYBRID_EXCERPT = 400
GOLD_TAIL_N = 30
GOLD_EXCERPT = 700
TOOL_HISTOGRAM_CAP = 8
REREAD_MIN = 3
REREAD_CAP = 8
TAIL_TOOL_CAP = 32

# Same patterns as tools/transcript/lib/snapshot.py. Copied so this proof
# does not import the transcript package.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}", re.I),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|password)\s*[:=]\s*\S+"),
)


class StateOverBudget(ValueError):
    """State JSON exceeds the guard. Callers must not POST it."""


def state_json_len(state: dict[str, Any]) -> int:
    return len(json.dumps(state, ensure_ascii=False))


def assert_state_within_budget(state: dict[str, Any], limit: int = STATE_CHAR_LIMIT) -> None:
    size = state_json_len(state)
    if size > limit:
        raise StateOverBudget(f"state JSON length {size} exceeds budget {limit}")


def redact_secrets(text: str) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _clip(text: str, limit: int) -> str:
    redacted = redact_secrets(text)
    if len(redacted) <= limit:
        return redacted
    return redacted[:limit]


def _top_counts(counts: dict[str, int], cap: int) -> dict[str, int]:
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return {name: count for name, count in ordered[:cap]}


def _histogram(turns: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for turn in turns:
        for name in turn.tool_names:
            counts[name] = counts.get(name, 0) + 1
    return _top_counts(counts, TOOL_HISTOGRAM_CAP)


def _read_counts(turns: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for turn in turns:
        for path in turn.read_paths:
            counts[path] = counts.get(path, 0) + 1
    return counts


def _reread_entries(counts: dict[str, int]) -> list[dict[str, Any]]:
    hot = [(path, count) for path, count in counts.items() if count >= REREAD_MIN]
    hot.sort(key=lambda item: (-item[1], item[0]))
    return [{"path": redact_secrets(path), "count": count} for path, count in hot[:REREAD_CAP]]


def _peak(turns: list[Any]) -> int | None:
    values = [turn.context_tokens for turn in turns if turn.context_tokens is not None]
    if not values:
        return None
    return max(values)


def _compaction_count(indexed: IndexedTranscript, indexes: list[int]) -> int:
    return sum(1 for index in indexes if _is_compaction(indexed.rows[index]))


def _is_compaction(row: dict[str, Any]) -> bool:
    return is_compaction_row(row)


def _tail(turns: list[Any], n: int, excerpt: int) -> list[dict[str, Any]]:
    window = turns[-n:] if n > 0 else []
    rows: list[dict[str, Any]] = []
    for turn in window:
        rows.append(
            {
                "turn": turn.number,
                "excerpt": _clip(turn.text, excerpt),
                "tool_names": list(turn.tool_names[:TAIL_TOOL_CAP]),
            }
        )
    return rows


def _cumulative(
    indexed: IndexedTranscript,
    checkpoint: int,
) -> dict[str, Any]:
    turns = indexed.turns[:checkpoint]
    indexes = indexed.prefix_indexes(checkpoint)
    read_counts = _read_counts(turns)
    text_chars = sum(len(turn.text) for turn in turns)
    return {
        "api_turns": checkpoint,
        "peak_ctx_tokens": _peak(turns),
        "prefix_bytes": sum(indexed.row_bytes[index] for index in indexes),
        "tool_histogram": _histogram(turns),
        "reread_paths": _reread_entries(read_counts),
        "distinct_read_paths": len(read_counts),
        "compaction_event_count": _compaction_count(indexed, indexes),
        "assistant_text_chars": text_chars,
    }


def _delta(indexed: IndexedTranscript, checkpoint: int, prior: int | None) -> dict[str, Any]:
    if prior is None:
        return {}
    before = _read_counts(indexed.turns[:prior])
    window = indexed.turns[prior:checkpoint]
    fresh: list[str] = []
    seen: set[str] = set()
    for turn in window:
        for path in turn.read_paths:
            if path in before or path in seen:
                continue
            seen.add(path)
            fresh.append(redact_secrets(path))
    return {
        "new_read_paths": fresh[:REREAD_CAP],
        "tool_histogram_delta": _histogram(window),
    }


def _brief(indexed: IndexedTranscript, checkpoint: int) -> str:
    text = first_user_text(indexed, indexed.prefix_indexes(checkpoint))
    if text is None or not text.strip():
        return "missing"
    return _clip(text.strip(), BRIEF_CAP)


def build_hybrid_v0(
    indexed: IndexedTranscript,
    checkpoint: int,
    *,
    first_at: int,
    interval: int,
    prior: int | None,
    n: int = HYBRID_TAIL_N,
    excerpt: int = HYBRID_EXCERPT,
) -> dict[str, Any]:
    """Unshrunk hybrid_v0 state for ``prefix(checkpoint)``."""
    return {
        "question_id": "session-checkout",
        "jev_model": JEV_MODEL,
        "worker_id": indexed.worker_id,
        "checkpoint_turn": checkpoint,
        "prior_checkpoint_turn": prior,
        "schedule": {"first_at": first_at, "interval": interval},
        "brief_anchor": _brief(indexed, checkpoint),
        "cumulative": _cumulative(indexed, checkpoint),
        "delta_since_prior": _delta(indexed, checkpoint, prior),
        "tail": _tail(indexed.turns[:checkpoint], n, excerpt),
    }


def shrink_hybrid_state(
    state: dict[str, Any],
    *,
    limit: int = STATE_CHAR_LIMIT,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Apply TERMS §5 shrink order. ``None`` means the checkpoint is missing."""
    import copy

    current: dict[str, Any] = copy.deepcopy(state)
    steps: list[str] = []

    def size() -> int:
        return state_json_len(current)

    if size() <= limit:
        return current, steps

    tail: list[dict[str, Any]] = current.get("tail") or []
    while size() > limit and len(tail) > 4:
        tail.pop(0)
        steps.append("drop_oldest_tail")
    while size() > limit and tail:
        tail.pop(0)
        steps.append("drop_oldest_tail")
    current["tail"] = tail

    if size() > limit:
        changed = False
        for item in tail:
            excerpt = str(item.get("excerpt") or "")
            if len(excerpt) > 200:
                item["excerpt"] = excerpt[:200]
                changed = True
        if changed:
            steps.append("excerpt_200")

    if size() > limit:
        paths = (current.get("cumulative") or {}).get("reread_paths") or []
        if any(isinstance(entry, dict) and "path" in entry for entry in paths):
            current["cumulative"]["reread_paths"] = [
                {"count_only": entry.get("count")} for entry in paths if isinstance(entry, dict)
            ]
            steps.append("reread_count_only")

    delta = current.get("delta_since_prior")
    if size() > limit and isinstance(delta, dict) and delta:
        current.pop("delta_since_prior", None)
        steps.append("drop_delta")

    if size() > limit:
        steps.append("state_over_budget")
        return None, steps
    return current, steps


def prepare_hybrid_state(
    indexed: IndexedTranscript,
    checkpoint: int,
    *,
    first_at: int,
    interval: int,
    prior: int | None,
    n: int = HYBRID_TAIL_N,
    excerpt: int = HYBRID_EXCERPT,
) -> tuple[dict[str, Any] | None, list[str]]:
    raw = build_hybrid_v0(
        indexed,
        checkpoint,
        first_at=first_at,
        interval=interval,
        prior=prior,
        n=n,
        excerpt=excerpt,
    )
    return shrink_hybrid_state(raw)


def build_gold_bundle(
    indexed: IndexedTranscript,
    checkpoint: int,
) -> dict[str, Any]:
    """Judge view of ``prefix(checkpoint)``. Not the Jev state."""
    return {
        "brief_anchor": _brief(indexed, checkpoint),
        "api_turns_note": f"api_turns = {checkpoint}",
        "cumulative": _cumulative(indexed, checkpoint),
        "tail": _tail(indexed.turns[:checkpoint], GOLD_TAIL_N, GOLD_EXCERPT),
    }


def shrink_gold_bundle(
    bundle: dict[str, Any],
    *,
    limit: int = GOLD_BUNDLE_CHAR_LIMIT,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Drop oldest tail turns, then cut excerpts to 350. Else unlabelable."""
    import copy

    current: dict[str, Any] = copy.deepcopy(bundle)
    steps: list[str] = []
    tail: list[dict[str, Any]] = current.get("tail") or []

    def size() -> int:
        return state_json_len(current)

    while size() > limit and tail:
        tail.pop(0)
        steps.append("drop_oldest_tail")
    if size() > limit:
        changed = False
        for item in tail:
            excerpt = str(item.get("excerpt") or "")
            if len(excerpt) > 350:
                item["excerpt"] = excerpt[:350]
                changed = True
        if changed:
            steps.append("excerpt_350")
    current["tail"] = tail
    if size() > limit:
        steps.append("unlabelable")
        return None, steps
    return current, steps


def prepare_gold_bundle(
    indexed: IndexedTranscript,
    checkpoint: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    return shrink_gold_bundle(build_gold_bundle(indexed, checkpoint))
