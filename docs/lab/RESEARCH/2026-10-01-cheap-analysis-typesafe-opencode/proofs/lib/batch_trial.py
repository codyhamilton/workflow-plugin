"""analysis.batch_trial — dedupe, caps, dry-run default (no socket)."""

from __future__ import annotations

import os
from typing import Any

from classify import classify

POST_COUNT_CAP_MAX = 256
DEFAULT_MAX_CALLS = 32


def _cell_key(cell: dict[str, Any]) -> tuple[str, str, str]:
    return (cell["framing_id"], cell["segment_id"], cell["schema_id"])


def _live_shaped(live: bool, confirm_live: bool) -> bool:
    return live and confirm_live and bool(os.environ.get("TYPESAFE_API_KEY", "").strip())


def batch_trial(
    *,
    schema_id: str,
    framing_slugs: list[str],
    segments: list[dict[str, Any]],
    backend: str = "typesafe",
    live: bool = False,
    confirm_live: bool = False,
    max_calls: int = DEFAULT_MAX_CALLS,
    budget_tokens: int | None = None,
    hide_outcome_suffix: bool = True,
    duplicate_cells: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    if max_calls > POST_COUNT_CAP_MAX:
        return {
            "cells": [],
            "posts": 0,
            "duplicate_post_rate": 0.0,
            "capped": 0,
            "rejected": True,
            "reason": "max_calls_above_256",
        }

    if max_calls > DEFAULT_MAX_CALLS and budget_tokens is None:
        return {
            "cells": [],
            "posts": 0,
            "duplicate_post_rate": 0.0,
            "capped": 0,
            "rejected": True,
            "reason": "budget_required",
        }

    if not hide_outcome_suffix and schema_id not in ("session-checkout", "trajectory-v0"):
        cells = [
            {
                "model_tier": backend,
                "framing_id": slug,
                "segment_id": seg["segment_id"],
                "schema_id": schema_id,
                "decision": "missing",
                "reason": "suffix_forbidden",
                "cache_key": None,
            }
            for slug in framing_slugs
            for seg in segments
        ]
        return {
            "cells": cells,
            "posts": 0,
            "duplicate_post_rate": 0.0,
            "capped": 0,
            "rejected": False,
        }

    planned: list[dict[str, Any]] = []
    for seg in segments:
        for slug in framing_slugs:
            planned.append({"segment": seg, "framing_slug": slug})
    if duplicate_cells:
        for seg_id, slug in duplicate_cells:
            seg = next(s for s in segments if s["segment_id"] == seg_id)
            planned.append({"segment": seg, "framing_slug": slug})

    cells: list[dict[str, Any]] = []
    post_budget = max_calls if _live_shaped(live, confirm_live) else None
    posts = 0
    capped = 0
    seen_dedupe: set[tuple[str, str, str]] = set()

    for item in planned:
        seg = item["segment"]
        slug = item["framing_slug"]
        ewe = seg["early_window_end"]
        if hide_outcome_suffix and seg["end"] > ewe:
            row = {
                "model_tier": backend,
                "framing_id": slug,
                "segment_id": seg["segment_id"],
                "schema_id": schema_id,
                "decision": "missing",
                "reason": "outcome_suffix",
                "cache_key": None,
            }
            cells.append(row)
            continue

        result = classify(
            schema_id=schema_id,
            framing_slug=slug,
            state=seg["state"],
            evidence_class=seg["evidence_class"],
            live=live,
            confirm_live=confirm_live,
        )
        if result.get("decision") == "missing" and result.get("reason") not in (None, "cap"):
            cells.append(
                {
                    "model_tier": backend,
                    "framing_id": result.get("framing_id") or slug,
                    "segment_id": seg["segment_id"],
                    "schema_id": schema_id,
                    "decision": "missing",
                    "reason": result.get("reason"),
                    "cache_key": result.get("cache_key"),
                }
            )
            continue

        fid = result.get("framing_id") or slug
        dedupe = (fid, seg["segment_id"], schema_id)
        if dedupe in seen_dedupe:
            cells.append(
                {
                    "model_tier": backend,
                    "framing_id": fid,
                    "segment_id": seg["segment_id"],
                    "schema_id": schema_id,
                    "decision": result["decision"],
                    "reason": "duplicate_input",
                    "cache_key": result.get("cache_key"),
                    "deduped": True,
                }
            )
            continue

        if post_budget is not None and result.get("would_post") and posts >= post_budget:
            cells.append(
                {
                    "model_tier": backend,
                    "framing_id": fid,
                    "segment_id": seg["segment_id"],
                    "schema_id": schema_id,
                    "decision": "missing",
                    "reason": "cap",
                    "cache_key": None,
                }
            )
            capped += 1
            continue

        seen_dedupe.add(dedupe)
        row = {
            "model_tier": backend,
            "framing_id": fid,
            "segment_id": seg["segment_id"],
            "schema_id": schema_id,
            "decision": result["decision"],
            "reason": result.get("reason"),
            "cache_key": result.get("cache_key"),
            "deduped": False,
        }
        cells.append(row)
        if result.get("would_post"):
            posts += 1

    duplicate_post_rate = 0.0

    unique_cells = [c for c in cells if not c.get("deduped")]
    return {
        "cells": cells,
        "posts": posts,
        "duplicate_post_rate": duplicate_post_rate,
        "capped": capped,
        "rejected": False,
        "unique_cell_count": len(unique_cells),
        "input_cell_count": len(planned),
    }
