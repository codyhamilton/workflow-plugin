"""Usage deduplication and token aggregation."""

from __future__ import annotations

from typing import Any

_USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)


def empty_usage() -> dict[str, int]:
    return {k: 0 for k in _USAGE_KEYS}


def merge_usage(*usages: dict[str, int]) -> dict[str, int]:
    """Sum token buckets across parent and subagent usage dicts."""
    totals = empty_usage()
    for usage in usages:
        for key in _USAGE_KEYS:
            totals[key] += usage.get(key, 0)
    return totals


def dedupe_usage(messages: list[dict[str, Any]]) -> tuple[int, dict[str, int]]:
    """Dedupe assistant usage by message.id; return (api_call_count, token_totals)."""
    seen_ids: set[str] = set()
    api_calls = 0
    totals = empty_usage()

    for msg in messages:
        if msg.get("type") != "assistant" and msg.get("role") != "assistant":
            continue
        inner = msg.get("message", {})
        msg_id = inner.get("id")
        usage = inner.get("usage")
        if not usage:
            continue
        if msg_id:
            if msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)
        api_calls += 1
        totals["input_tokens"] += usage.get("input_tokens", 0)
        totals["output_tokens"] += usage.get("output_tokens", 0)
        totals["cache_read_input_tokens"] += usage.get("cache_read_input_tokens", 0)
        totals["cache_creation_input_tokens"] += usage.get(
            "cache_creation_input_tokens", 0
        )

    return api_calls, totals


def context_estimate_from_messages(messages: list[dict[str, Any]]) -> int | None:
    """First assistant response with usage: input + cache read + cache creation."""
    for msg in messages:
        if msg.get("type") != "assistant" and msg.get("role") != "assistant":
            continue
        usage = msg.get("message", {}).get("usage")
        if usage:
            return (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
            )
    return None
