"""Field capture JSONL layout (dry-twin and live share the same row shape)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_jsonl(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def jev_request_row(
    *,
    cell_index: int,
    arm: str,
    worker_id: str,
    framing_slug: str,
    framing_id: str,
    segment_id: str,
    schema_id: str,
    mode: str,
    classify_result: dict[str, Any],
    registration_id: str,
) -> dict[str, Any]:
    """One JSONL row for requests.jsonl (dry_run or live)."""
    req = classify_result.get("request") or {}
    return {
        "ts": utc_now_iso(),
        "registration_id": registration_id,
        "mode": mode,
        "cell_index": cell_index,
        "arm": arm,
        "worker_id": worker_id,
        "framing_slug": framing_slug,
        "framing_id": framing_id,
        "segment_id": segment_id,
        "schema_id": schema_id,
        "model": classify_result.get("model"),
        "decision": classify_result.get("decision"),
        "cache_key": classify_result.get("cache_key"),
        "would_post": classify_result.get("would_post", False),
        "request_body": req,
    }


def jev_response_row(
    *,
    cell_index: int,
    mode: str,
    registration_id: str,
    request_cache_key: str | None,
    response_body: dict[str, Any] | None,
    input_tokens: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "ts": utc_now_iso(),
        "registration_id": registration_id,
        "mode": mode,
        "cell_index": cell_index,
        "cache_key": request_cache_key,
        "response_body": response_body,
        "input_tokens": input_tokens,
        "error": error,
    }


def write_meters(path: Path, meters: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": utc_now_iso(), **meters}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
