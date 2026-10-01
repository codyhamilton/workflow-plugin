#!/usr/bin/env python3
"""Spike 1 — schema dry-run under state guard."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from bootstrap import ensure_progressive_proofs
from classify import checkout_y_full_request_from_state, classify, questions_text_from_request
from paths import proofs_out_dir
from schemas import framing_id as make_framing_id, state_json_len
from trial_segments import prose_segment_if_mounted, stats_segment_turn75


def main() -> int:
    out_dir = proofs_out_dir("spike-1")
    out_dir.mkdir(parents=True, exist_ok=True)
    stats_seg = stats_segment_turn75()
    prose_seg = prose_segment_if_mounted()

    schema_runs = {}
    for schema_id, slug in (
        ("shape-v0", "shape-v0-default"),
        ("phase-sketch-v0", "phase-v0-default"),
        ("early-signal-v0", "signal-v0-default"),
    ):
        schema_runs[schema_id] = classify(
            schema_id=schema_id,
            framing_slug=slug,
            state=stats_seg["state"],
            evidence_class=stats_seg["evidence_class"],
        )

    ensure_progressive_proofs()
    from session_checkout import session_checkout_questions  # type: ignore

    builder_q = session_checkout_questions("Y_full")
    harness_req = checkout_y_full_request_from_state(stats_seg["state"])
    questions_match = questions_text_from_request(harness_req) == json.dumps(
        builder_q, ensure_ascii=False, sort_keys=True
    )

    edited = copy.deepcopy(builder_q)
    edited["checkout_now"]["instructions"] += " [spike1-edit]"
    edited_fid = make_framing_id("Y_full-edited", edited)
    y_full_fid = make_framing_id("Y_full", builder_q)

    unregistered = classify(
        schema_id="early-signal-v0",
        framing_slug="not-registered-slug",
        state=stats_seg["state"],
        evidence_class="stats_only",
    )

    phase_on_stats = schema_runs["phase-sketch-v0"]
    early_q = (schema_runs["early-signal-v0"].get("request") or {}).get("questions") or {}
    stats_question_ids = set(early_q.keys())
    forbidden = {"no_checkable_step", "anchor_divergence", "compaction_cycle"} & stats_question_ids

    state_len = state_json_len(stats_seg["state"])
    checks = {
        "state_under_12k": state_len <= 12000,
        "y_full_questions_match_builder": questions_match,
        "edited_framing_differs": edited_fid != y_full_fid and not edited_fid.startswith("Y_full#"),
        "unregistered_framing": unregistered.get("reason") == "unregistered_framing",
        "stats_early_signal_dry_run": schema_runs["early-signal-v0"]["decision"] == "dry_run",
        "stats_no_prose_questions": forbidden == set(),
        "phase_sketch_prose_required": phase_on_stats.get("reason") == "prose_required",
        "shape_stats_dry_run": schema_runs["shape-v0"]["decision"] == "dry_run",
    }

    if prose_seg:
        prose_run = classify(
            schema_id="early-signal-v0",
            framing_slug="signal-v0-default",
            state=prose_seg["state"],
            evidence_class="prose",
        )
        checks["prose_segment_dry_run"] = prose_run["decision"] == "dry_run"
    else:
        checks["no_raw_mount"] = True

    checks["all_pass"] = all(v for k, v in checks.items() if k != "all_pass")

    payload = {
        "schema_runs": schema_runs,
        "y_full": {"match": questions_match, "edited_framing_id": edited_fid, "y_full_framing_id": y_full_fid},
        "unregistered": unregistered,
        "state_chars": state_len,
        "checks": checks,
    }
    (out_dir / "spike1_requests.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out_dir / "SPIKE-RESULT.md").write_text(_md(checks, prose_seg is not None), encoding="utf-8")
    print(json.dumps({"gate_pass": checks["all_pass"]}, indent=2))
    return 0 if checks["all_pass"] else 1


def _md(checks: dict, prose: bool) -> str:
    lines = [
        "# Spike 1 — schema dry-run",
        "",
        f"**Gate:** {'PASS' if checks['all_pass'] else 'FAIL'}",
        "",
        f"Raw prose mount: {'yes' if prose else 'no'}",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        if k == "all_pass":
            continue
        lines.append(f"- `{k}`: {'pass' if v else '**fail**'}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
