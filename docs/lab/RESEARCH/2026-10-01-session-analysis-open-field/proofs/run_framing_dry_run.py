#!/usr/bin/env python3
"""Phase 1b — framing registry dry-run batch (0 live POSTs)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from import_paths import ensure_import_paths

ensure_import_paths()

from batch_trial import batch_trial  # noqa: E402
from classify import classify  # noqa: E402
from framing_pool import OPEN_FIELD_FRAMING_SLUGS, registry_rows, unregistered_framing_demo  # noqa: E402
from paths import (  # noqa: E402
    AGREEMENT_MATRIX,
    STRATIFIED_EIGHT,
    validated_dir,
)
from schemas import FRAMING_REGISTRY  # noqa: E402
from segments import segments_for_workers  # noqa: E402
from stats_card import worker_T_from_matrix  # noqa: E402

DUMMY_KEY = "typesafe-dummy-key-open-field-phase-1b-not-real"
TOURNAMENT_FRAMINGS = (
    "tournament-binary-foreshadow",
    "tournament-likert-collapsed",
    "tournament-monitor-called-out",
    "tournament-no-story-beyond-counts",
)
SEARCH_POOL_SLUGS = tuple(OPEN_FIELD_FRAMING_SLUGS.keys())


def main() -> int:
    out_dir = validated_dir("phase-1b-1c")
    out_dir.mkdir(parents=True, exist_ok=True)
    framing_dir = ROOT / "framing"
    framing_dir.mkdir(parents=True, exist_ok=True)

    # Merge open-field slugs into registry for classify()
    early = FRAMING_REGISTRY.setdefault("early-signal-v0", {})
    for slug, questions in OPEN_FIELD_FRAMING_SLUGS.items():
        if questions is not None:
            early[slug] = questions

    registry = registry_rows(FRAMING_REGISTRY)
    (framing_dir / "registry.json").write_text(
        json.dumps({"schema_id": "early-signal-v0", "rows": registry}, indent=2) + "\n",
        encoding="utf-8",
    )

    T_map = worker_T_from_matrix(AGREEMENT_MATRIX)
    segments = segments_for_workers(STRATIFIED_EIGHT, T_map)
    dup_seg = segments[0]["segment_id"]

    dry = batch_trial(
        schema_id="early-signal-v0",
        framing_slugs=list(TOURNAMENT_FRAMINGS),
        segments=segments,
        live=False,
        confirm_live=False,
        duplicate_cells=[(dup_seg, TOURNAMENT_FRAMINGS[0])],
    )

    os.environ["TYPESAFE_API_KEY"] = DUMMY_KEY
    capped = batch_trial(
        schema_id="early-signal-v0",
        framing_slugs=list(TOURNAMENT_FRAMINGS),
        segments=segments,
        live=True,
        confirm_live=True,
        max_calls=1,
    )

    unreg_seg = segments[1]
    unreg = classify(
        schema_id="early-signal-v0",
        framing_slug="never-registered-slug",
        state=unreg_seg["state"],
        evidence_class=unreg_seg["evidence_class"],
    )
    _ = unregistered_framing_demo()  # documented example blob; not in registry

    baseline_arm_slots = 8
    search_arm_slots = 24
    split_doc = {
        "frozen_card_search_budget_split": {
            "baseline_arm_calls": baseline_arm_slots,
            "search_arm_calls": search_arm_slots,
            "baseline_draw": "random slug from registry pool (≥8 blobs)",
            "search_arm_default": "6 workers × 4 tournament framings (24 cells)",
            "hold_out_workers": "26 workers not in STRATIFIED_EIGHT",
        },
        "pool_slugs": list(SEARCH_POOL_SLUGS),
        "registered_blob_count": len(registry),
    }

    combined = json.dumps({"dry": dry, "capped": capped, "unregistered_demo": unreg, "split": split_doc})
    leak = DUMMY_KEY in combined

    expected_unique = len(TOURNAMENT_FRAMINGS) * len(segments)
    checks = {
        "dry_run_decisions": all(c.get("decision") == "dry_run" for c in dry["cells"]),
        "cartesian_32_unique_plus_dedupe_row": dry["unique_cell_count"] == 32
        and len(dry["cells"]) == 33,
        "cartesian_unique_count": dry["unique_cell_count"] == expected_unique,
        "duplicate_input_once": sum(1 for c in dry["cells"] if c.get("reason") == "duplicate_input") == 1,
        "duplicate_post_rate_zero": dry["duplicate_post_rate"] == 0.0,
        "registry_at_least_8_blobs": len(registry) >= 8,
        "unregistered_framing_missing": unreg.get("reason") == "unregistered_framing",
        "no_api_key_leak": not leak,
        "live_shaped_cap": capped["posts"] == 1,
    }
    checks["all_pass"] = all(checks.values())

    log = {
        "phase": "1b",
        "live_posts": 0,
        "dry": dry,
        "capped": capped,
        "unregistered_demo": unreg,
        "budget_split": split_doc,
        "checks": checks,
    }
    log_path = out_dir / "dry_run_batch_log.json"
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

    grep = subprocess.run(["grep", "-F", DUMMY_KEY, str(log_path)], capture_output=True, text=True)
    checks["grep_dummy_key_absent"] = grep.returncode != 0
    checks["all_pass"] = all(checks.values())
    log["checks"] = checks
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"gate_pass": checks["all_pass"], "log": str(log_path.relative_to(ROOT.parents[3]))}))
    return 0 if checks["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
