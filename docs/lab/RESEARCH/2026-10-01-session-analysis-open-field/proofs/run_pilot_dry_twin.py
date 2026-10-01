#!/usr/bin/env python3
"""Pilot field-proof — Jev dry-twin (88 cells, capture layout, 0 live POSTs)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from import_paths import ensure_import_paths

ensure_import_paths()

from batch_trial import batch_trial  # noqa: E402
from capture_io import jev_request_row, jev_response_row, write_jsonl, write_meters  # noqa: E402
from classify import classify  # noqa: E402
from framing_pool import OPEN_FIELD_FRAMING_SLUGS, registry_rows  # noqa: E402
from paths import (  # noqa: E402
    AGREEMENT_MATRIX,
    STRATIFIED_EIGHT,
    capture_jev_dir,
    capture_root,
    validated_dir,
)
from pilot_wave import (  # noqa: E402
    BUDGET_TOKENS,
    MAX_CALLS,
    MODEL_PIN,
    PILOT_POOL_SLUGS,
    REGISTRATION_ID,
    SCHEMA_ID,
    pilot_jev_cell_plan,
)
from schemas import FRAMING_REGISTRY  # noqa: E402
from segments import segments_for_workers  # noqa: E402
from stats_card import worker_T_from_matrix  # noqa: E402

DUMMY_KEY = "typesafe-dummy-key-pilot-field-proof-not-real"


def main() -> int:
    reg_dir = capture_root("pilot-field-proof")
    dry_dir = capture_jev_dir("pilot-field-proof", "dry-twin")
    dry_dir.mkdir(parents=True, exist_ok=True)

    early = FRAMING_REGISTRY.setdefault("early-signal-v0", {})
    for slug, questions in OPEN_FIELD_FRAMING_SLUGS.items():
        if questions is not None:
            early[slug] = questions

    registry = registry_rows(FRAMING_REGISTRY)
    framing_dir = ROOT / "framing"
    framing_dir.mkdir(parents=True, exist_ok=True)
    (framing_dir / "registry.json").write_text(
        json.dumps({"schema_id": SCHEMA_ID, "rows": registry}, indent=2) + "\n",
        encoding="utf-8",
    )
    (reg_dir / "framing_hashes.json").write_text(
        json.dumps({"schema_id": SCHEMA_ID, "rows": registry}, indent=2) + "\n",
        encoding="utf-8",
    )

    plan = pilot_jev_cell_plan()
    (reg_dir / "jev_cell_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    T_map = worker_T_from_matrix(AGREEMENT_MATRIX)
    segment_by_worker = {s["worker_id"]: s for s in segments_for_workers(STRATIFIED_EIGHT, T_map)}

    request_rows: list[dict] = []
    response_rows: list[dict] = []
    for idx, cell in enumerate(plan["cells"]):
        wid = cell["worker_id"]
        slug = cell["framing_slug"]
        seg = segment_by_worker[wid]
        result = classify(
            schema_id=SCHEMA_ID,
            framing_slug=slug,
            state=seg["state"],
            evidence_class=seg["evidence_class"],
            live=False,
            confirm_live=False,
        )
        request_rows.append(
            jev_request_row(
                cell_index=idx,
                arm=cell["arm"],
                worker_id=wid,
                framing_slug=slug,
                framing_id=result.get("framing_id") or slug,
                segment_id=seg["segment_id"],
                schema_id=SCHEMA_ID,
                mode="dry-twin",
                classify_result=result,
                registration_id=REGISTRATION_ID,
            )
        )
        response_rows.append(
            jev_response_row(
                cell_index=idx,
                mode="dry-twin",
                registration_id=REGISTRATION_ID,
                request_cache_key=result.get("cache_key"),
                response_body=None,
                input_tokens=None,
                error=None,
            )
        )

    write_jsonl(dry_dir / "requests.jsonl", iter(request_rows))
    write_jsonl(dry_dir / "responses.jsonl", iter(response_rows))

    dry_batch = batch_trial(
        schema_id=SCHEMA_ID,
        framing_slugs=list(PILOT_POOL_SLUGS),
        segments=list(segment_by_worker.values()),
        live=False,
        confirm_live=False,
        max_calls=MAX_CALLS,
        budget_tokens=BUDGET_TOKENS,
    )

    import os

    os.environ["TYPESAFE_API_KEY"] = DUMMY_KEY
    shaped = batch_trial(
        schema_id=SCHEMA_ID,
        framing_slugs=list(PILOT_POOL_SLUGS),
        segments=list(segment_by_worker.values()),
        live=True,
        confirm_live=True,
        max_calls=MAX_CALLS,
        budget_tokens=BUDGET_TOKENS,
    )

    combined = json.dumps({"dry_batch": dry_batch, "shaped": shaped})
    leak = DUMMY_KEY in combined

    checks = {
        "cell_plan_max_calls": len(plan["cells"]) == MAX_CALLS,
        "registry_framing_count": len(registry) == len(PILOT_POOL_SLUGS),
        "dry_twin_all_dry_run": all(r["decision"] == "dry_run" for r in request_rows),
        "batch_unique_max_calls": dry_batch.get("unique_cell_count") == MAX_CALLS,
        "batch_not_rejected": not dry_batch.get("rejected"),
        "budget_tokens_set": BUDGET_TOKENS >= 200_000,
        "shaped_would_post_max_calls": shaped.get("posts") == MAX_CALLS,
        "no_api_key_leak": not leak,
    }
    checks["all_pass"] = all(checks.values())

    summary = {
        "registration_id": REGISTRATION_ID,
        "model": MODEL_PIN,
        "schema_id": SCHEMA_ID,
        "max_calls": MAX_CALLS,
        "budget_tokens": BUDGET_TOKENS,
        "live_posts": 0,
        "mode": "dry-twin",
        "workers": list(STRATIFIED_EIGHT),
        "framing_slugs": list(PILOT_POOL_SLUGS),
        "batch": dry_batch,
        "checks": checks,
    }
    (dry_dir / "batch_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    write_meters(
        dry_dir / "meters.json",
        {
            "registration_id": REGISTRATION_ID,
            "mode": "dry-twin",
            "jev_posts": 0,
            "jev_would_post": MAX_CALLS,
            "input_tokens_observed": 0,
            "input_tokens_budget": BUDGET_TOKENS,
            "input_tokens_assumed_mid_per_post": 2000,
            "flash_calls": 0,
            "local_completions": 0,
        },
    )

    out_validated = validated_dir("pilot-field-proof")
    out_validated.mkdir(parents=True, exist_ok=True)
    (out_validated / "dry_twin_batch_log.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    grep = subprocess.run(["grep", "-F", DUMMY_KEY, str(dry_dir / "batch_summary.json")], capture_output=True)
    checks["grep_dummy_key_absent"] = grep.returncode != 0
    checks["all_pass"] = all(checks.values())
    summary["checks"] = checks
    (dry_dir / "batch_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out_validated / "dry_twin_batch_log.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"gate_pass": checks["all_pass"], "capture": str(dry_dir.relative_to(ROOT.parents[3]))}))
    return 0 if checks["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
