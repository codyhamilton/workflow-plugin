#!/usr/bin/env python3
"""Pilot field-proof — live Jev capture (96 cells, TypeSafe POSTs). Lab only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from import_paths import ensure_import_paths

ensure_import_paths()

from capture_io import jev_request_row, jev_response_row, write_jsonl, write_meters  # noqa: E402
from classify import classify  # noqa: E402
from framing_pool import OPEN_FIELD_FRAMING_SLUGS  # noqa: E402
from paths import (  # noqa: E402
    AGREEMENT_MATRIX,
    REPO_ROOT,
    STRATIFIED_EIGHT,
    capture_jev_dir,
    capture_root,
)
from pilot_wave import (  # noqa: E402
    BUDGET_TOKENS,
    MAX_CALLS,
    MODEL_PIN,
    PILOT_POOL_SLUGS,
    REGISTRATION_ID,
    SCHEMA_ID,
    TOKEN_ASSUMPTION_MID,
    pilot_jev_cell_plan,
)
from schemas import FRAMING_REGISTRY  # noqa: E402
from segments import segments_for_workers  # noqa: E402
from stats_card import worker_T_from_matrix  # noqa: E402

_TRANSCRIPT_LIB = REPO_ROOT / "tools/transcript"
if str(_TRANSCRIPT_LIB) not in sys.path:
    sys.path.insert(0, str(_TRANSCRIPT_LIB))
from lib.jev_client import JEV_MODEL, post_systemone  # noqa: E402


def _require_live_flags(confirm_live: bool) -> None:
    if not confirm_live:
        raise SystemExit("Refusing live capture without --confirm-live")


def _require_api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise SystemExit("TYPESAFE_API_KEY is not set or empty (required for live pilot capture)")
    return key


def _load_cell_plan(reg_dir: Path) -> dict[str, Any]:
    plan_path = reg_dir / "jev_cell_plan.json"
    if plan_path.is_file():
        return json.loads(plan_path.read_text(encoding="utf-8"))
    return pilot_jev_cell_plan()


def _ensure_framing_registry() -> None:
    early = FRAMING_REGISTRY.setdefault("early-signal-v0", {})
    for slug, questions in OPEN_FIELD_FRAMING_SLUGS.items():
        if questions is not None:
            early[slug] = questions


def _usage_input_tokens(response_body: dict[str, Any] | None) -> int | None:
    if not response_body:
        return None
    usage = response_body.get("usage")
    if not isinstance(usage, dict):
        return None
    raw = usage.get("input_tokens")
    return int(raw) if raw is not None else None


def _post_systemone_safe(request: dict[str, Any], api_key: str) -> tuple[dict[str, Any] | None, str | None]:
    """Call repo jev_client.post_systemone; return (body, error) without exiting the wave."""
    try:
        return post_systemone(request, api_key=api_key), None
    except SystemExit as exc:
        return None, str(exc)


def _assert_model_pin(request: dict[str, Any]) -> None:
    model = request.get("model")
    if model != MODEL_PIN:
        raise SystemExit(f"Hard kill: request model {model!r} != pin {MODEL_PIN}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pilot field-proof live Jev capture (lab only).")
    parser.add_argument(
        "--confirm-live",
        action="store_true",
        help="Required flag to allow TypeSafe POSTs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N cells (smoke tests; default all 96)",
    )
    args = parser.parse_args()

    _require_live_flags(args.confirm_live)
    api_key = _require_api_key()

    if MODEL_PIN != JEV_MODEL:
        raise SystemExit(f"Hard kill: MODEL_PIN {MODEL_PIN!r} != jev_client {JEV_MODEL!r}")

    _ensure_framing_registry()

    reg_dir = capture_root("pilot-field-proof")
    live_dir = capture_jev_dir("pilot-field-proof", "live")
    live_dir.mkdir(parents=True, exist_ok=True)

    plan = _load_cell_plan(reg_dir)
    all_cells = plan.get("cells") or []
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    cell_limit = args.limit if args.limit is not None else len(all_cells)

    T_map = worker_T_from_matrix(AGREEMENT_MATRIX)
    segment_by_worker = {s["worker_id"]: s for s in segments_for_workers(STRATIFIED_EIGHT, T_map)}

    request_rows: list[dict[str, Any]] = []
    response_rows: list[dict[str, Any]] = []
    live_posts = 0
    errors = 0
    input_tokens_observed = 0
    stopped_reason: str | None = None

    for idx, cell in enumerate(all_cells):
        if idx >= cell_limit:
            break
        wid = cell["worker_id"]
        slug = cell["framing_slug"]
        seg = segment_by_worker[wid]
        result = classify(
            schema_id=SCHEMA_ID,
            framing_slug=slug,
            state=seg["state"],
            evidence_class=seg["evidence_class"],
            live=True,
            confirm_live=True,
        )

        decision = result.get("decision")
        would_post = bool(result.get("would_post"))
        request_body = result.get("request")
        response_body: dict[str, Any] | None = None
        row_error: str | None = None
        input_tokens: int | None = None

        if decision == "missing":
            would_post = False
        elif would_post and decision != "missing":
            if live_posts >= MAX_CALLS:
                decision = "missing"
                would_post = False
                result = {**result, "decision": decision, "reason": "cap"}
            elif input_tokens_observed + TOKEN_ASSUMPTION_MID > BUDGET_TOKENS:
                stopped_reason = "budget_tokens"
                decision = "missing"
                would_post = False
                result = {**result, "decision": decision, "reason": "budget_tokens"}
            else:
                assert request_body is not None
                _assert_model_pin(request_body)
                response_body, row_error = _post_systemone_safe(request_body, api_key)
                if row_error:
                    errors += 1
                    decision = "error"
                else:
                    live_posts += 1
                    decision = "live"
                    input_tokens = _usage_input_tokens(response_body)
                    if input_tokens is not None:
                        input_tokens_observed += input_tokens
                    else:
                        input_tokens_observed += TOKEN_ASSUMPTION_MID

        request_rows.append(
            jev_request_row(
                cell_index=idx,
                arm=cell["arm"],
                worker_id=wid,
                framing_slug=slug,
                framing_id=result.get("framing_id") or slug,
                segment_id=seg["segment_id"],
                schema_id=SCHEMA_ID,
                mode="live",
                classify_result={**result, "decision": decision, "would_post": would_post},
                registration_id=REGISTRATION_ID,
            )
        )
        response_rows.append(
            jev_response_row(
                cell_index=idx,
                mode="live",
                registration_id=REGISTRATION_ID,
                request_cache_key=result.get("cache_key"),
                response_body=response_body,
                input_tokens=input_tokens,
                error=row_error,
            )
        )

        if stopped_reason == "budget_tokens":
            break

    write_jsonl(live_dir / "requests.jsonl", iter(request_rows))
    write_jsonl(live_dir / "responses.jsonl", iter(response_rows))

    summary = {
        "registration_id": REGISTRATION_ID,
        "model": MODEL_PIN,
        "schema_id": SCHEMA_ID,
        "max_calls": MAX_CALLS,
        "budget_tokens": BUDGET_TOKENS,
        "live_posts": live_posts,
        "errors": errors,
        "mode": "live",
        "cells_planned": min(cell_limit, len(all_cells)),
        "cells_recorded": len(request_rows),
        "stopped_reason": stopped_reason,
        "workers": list(STRATIFIED_EIGHT),
        "framing_slugs": list(PILOT_POOL_SLUGS),
        "input_tokens_observed": input_tokens_observed,
    }
    (live_dir / "batch_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    write_meters(
        live_dir / "meters.json",
        {
            "registration_id": REGISTRATION_ID,
            "mode": "live",
            "jev_posts": live_posts,
            "jev_would_post": sum(1 for r in request_rows if r.get("would_post")),
            "input_tokens_observed": input_tokens_observed,
            "input_tokens_budget": BUDGET_TOKENS,
            "input_tokens_assumed_mid_per_post": TOKEN_ASSUMPTION_MID,
            "flash_calls": 0,
            "local_completions": 0,
        },
    )

    capture_rel = str(live_dir.relative_to(ROOT.parents[3]))
    print(
        json.dumps(
            {
                "live_posts": live_posts,
                "errors": errors,
                "capture": capture_rel,
                "registration_id": REGISTRATION_ID,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
