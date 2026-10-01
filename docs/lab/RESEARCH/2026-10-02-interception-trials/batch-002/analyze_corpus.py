#!/usr/bin/env python3
"""Offline analysis for batch-002 interception lab corpus (Soft HOLD).

Docs/evidence only — does not modify results.jsonl or product hooks.

Usage (from repo root):
  python3 docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/analyze_corpus.py

Outputs under:
  docs/lab/RESEARCH/2026-10-02-interception-steer-to-stop/analysis/
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
BATCH = Path(__file__).resolve().parent
OUT = (
    REPO
    / "docs/lab/RESEARCH/2026-10-02-interception-steer-to-stop/analysis"
)
FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)

# Streams excluded from score evidence (quarantine / allocation bugs)
EXCLUDED_RESULT_GLOBS = {
    "archive-t45-only/results.jsonl",
}

QUARANTINE_NOTE = {
    "batch-001": "T leak — see batch-001/LEAKAGE-NOTE.md",
    "archive-t45-only": "Discarded t=45-only allocation bug — EVIDENCE-LOG.md",
    "typesafe-scenario-sweep/SUPERSEDED-NOTE.json": "Prior cartesian sweep superseded",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def cp_map_get(m: dict[str, Any] | None, t: int) -> str | None:
    if not m:
        return None
    return m.get(str(t), m.get(t))


def ideal_window_contains(isw: Any, t: int) -> bool:
    if isinstance(isw, list) and len(isw) == 2:
        return int(isw[0]) <= t <= int(isw[1])
    return False


def provisional_meter_tags(cell: dict[str, Any], label: dict[str, Any]) -> list[str]:
    """OUTCOME-SHEET join rules — prefixed PROVISIONAL (not scoreboard)."""
    t = int(cell["checkpoint"])
    fire = bool(cell.get("fire"))
    nd = cp_map_get(label.get("near_done_at_checkpoint"), t)
    rw = cp_map_get(label.get("runaway_like_at_checkpoint"), t)
    isw = label.get("ideal_steer_window")
    tags: list[str] = []
    if nd == "yes" and fire:
        tags.append("PROVISIONAL_near_done_fp")
    if fire and ideal_window_contains(isw, t) and isw not in ("none", "ambiguous"):
        tags.append("PROVISIONAL_runaway_hit")
    if not fire and rw == "yes":
        tags.append("PROVISIONAL_runaway_miss_candidate")
    if fire and nd != "yes" and rw != "yes":
        tags.append("PROVISIONAL_productive_interrupt")
    return tags


def is_scored_row(row: dict[str, Any]) -> bool:
    if row.get("error"):
        return False
    if row.get("rating") is not None or row.get("label") is not None:
        return True
    if row.get("answers"):
        return row.get("http") == 200
    return False


def scenario_fire_from_row(row: dict[str, Any]) -> bool:
    """TypeSafe scenario sweep stores fire as choice string."""
    if isinstance(row.get("fire"), bool):
        return row["fire"]
    if row.get("fire") == "fire":
        return True
    if row.get("fire") == "defer":
        return False
    ans = row.get("answers") or {}
    ch = (ans.get("fire_now") or {}).get("choice")
    if ch == "fire":
        return True
    if ch == "defer":
        return False
    return bool(row.get("fire"))


def summarize_stream(rel: str, path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    scored = [r for r in rows if is_scored_row(r)]
    fire_n = sum(1 for r in scored if scenario_fire_from_row(r))
    sessions = {r.get("session_id") for r in rows if r.get("session_id")}
    sample_keys = sorted(rows[0].keys()) if rows else []
    drivers = Counter(r.get("driver") for r in rows if r.get("driver"))
    return {
        "path": str(path.relative_to(REPO)),
        "rel_under_batch": rel,
        "row_count": len(rows),
        "scored_count": len(scored),
        "fire_count": fire_n,
        "fire_rate_scored": round(fire_n / len(scored), 6) if scored else None,
        "n_sessions": len(sessions),
        "drivers": dict(drivers),
        "key_fields": sample_keys,
        "excluded_from_score_evidence": rel in EXCLUDED_RESULT_GLOBS,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Artifact inventory ---
    inventory: list[dict[str, Any]] = []
    for path in sorted(BATCH.rglob("results.jsonl")):
        rel = str(path.relative_to(BATCH))
        inventory.append(summarize_stream(rel, path))

    sidecar = BATCH / "outcome-labels.jsonl"
    labels = load_jsonl(sidecar) if sidecar.exists() else []
    label_by_session = {r["session_id"]: r for r in labels}

    meters_files = sorted(BATCH.rglob("meters.json"))
    meters_inventory = [
        {
            "path": str(p.relative_to(REPO)),
            "bytes": p.stat().st_size,
            "top_keys": list(json.loads(p.read_text()).keys())[:12],
        }
        for p in meters_files
    ]

    inventory_doc = {
        "soft_standard_hold": True,
        "generated_at": generated_at,
        "batch_dir": str(BATCH.relative_to(REPO)),
        "quarantine_notes": QUARANTINE_NOTE,
        "outcome_labels": {
            "path": str(sidecar.relative_to(REPO)),
            "row_count": len(labels),
            "label_status": dict(Counter(r.get("label_status") for r in labels)),
            "labeler": labels[0].get("labeler") if labels else None,
            "protocol_rev": labels[0].get("protocol_rev") if labels else None,
        },
        "result_streams": inventory,
        "meters_json_files": meters_inventory,
        "cells_plan_files": [
            str(p.relative_to(REPO))
            for p in sorted(BATCH.rglob("cells_plan.json"))
        ],
    }
    (OUT / "ARTIFACT-INVENTORY.json").write_text(
        json.dumps(inventory_doc, indent=2) + "\n"
    )

    # --- Scenario sweep rankings ---
    sweep_path = BATCH / "typesafe-scenario-sweep/results.jsonl"
    scenario_stats: dict[str, dict[str, Any]] = {}
    by_state: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_question: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_session: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    if sweep_path.exists():
        for row in load_jsonl(sweep_path):
            sid = row["scenario_id"]
            st = row.get("state_selection", sid.split("|")[0].replace("state.", ""))
            q = row.get("question_format", sid.split("|")[1].replace("q.", ""))
            fired = int(scenario_fire_from_row(row))
            if sid not in scenario_stats:
                scenario_stats[sid] = {"fire": 0, "n": 0, "state": st, "question": q}
            scenario_stats[sid]["fire"] += fired
            scenario_stats[sid]["n"] += 1
            by_state[st][0] += fired
            by_state[st][1] += 1
            by_question[q][0] += fired
            by_question[q][1] += 1
            sess = row.get("session_id")
            if sess:
                by_session[sess][0] += fired
                by_session[sess][1] += 1

    rankings = []
    for sid, st in scenario_stats.items():
        rate = st["fire"] / st["n"] if st["n"] else 0.0
        rankings.append(
            {
                "scenario_id": sid,
                "state_selection": st["state"],
                "question_format": st["question"],
                "n_sessions": st["n"],
                "fire_count": st["fire"],
                "fire_rate": round(rate, 6),
            }
        )
    rankings.sort(key=lambda x: (-x["fire_rate"], -x["fire_count"]))

    scenario_doc = {
        "soft_standard_hold": True,
        "provisional": True,
        "generated_at": generated_at,
        "source": str(sweep_path.relative_to(REPO)),
        "n_distinct_scenarios": len(rankings),
        "overall_fire_rate": round(
            sum(r["fire_count"] for r in rankings)
            / sum(r["n_sessions"] for r in rankings),
            6,
        )
        if rankings
        else None,
        "by_state_selection": {
            k: {
                "fire_rate": round(v[0] / v[1], 6),
                "fire_count": v[0],
                "n_cells": v[1],
            }
            for k, v in sorted(by_state.items())
        },
        "by_question_format_top": sorted(
            [
                {
                    "question_format": k,
                    "fire_rate": round(v[0] / v[1], 6),
                    "fire_count": v[0],
                    "n_cells": v[1],
                }
                for k, v in by_question.items()
            ],
            key=lambda x: -x["fire_rate"],
        )[:20],
        "rankings": rankings,
        "often_fires": [r for r in rankings if r["fire_rate"] > 0][:25],
        "never_fires": [r for r in rankings if r["fire_count"] == 0],
    }
    (OUT / "scenario-fire-rankings.json").write_text(
        json.dumps(scenario_doc, indent=2) + "\n"
    )

    # --- Wave-0 Flash join (labeled sessions only) ---
    wave0 = BATCH / "results.jsonl"
    join_rows: list[dict[str, Any]] = []
    tag_totals: Counter[str] = Counter()

    if wave0.exists():
        for cell in load_jsonl(wave0):
            lab = label_by_session.get(cell["session_id"])
            tags = provisional_meter_tags(cell, lab) if lab else []
            for t in tags:
                tag_totals[t] += 1
            join_rows.append(
                {
                    "provisional": True,
                    "soft_standard_hold": True,
                    "not_scoreboard": True,
                    "cell_id": cell.get("cell_id"),
                    "session_id": cell["session_id"],
                    "checkpoint": cell["checkpoint"],
                    "state_variant": cell.get("state_variant"),
                    "question_variant": cell.get("question_variant"),
                    "response_class": cell.get("response_class"),
                    "rating": cell.get("rating"),
                    "fire": cell.get("fire"),
                    "window_status_in_results": cell.get("window_status"),
                    "label_status": lab.get("label_status") if lab else None,
                    "near_done_at_cp": cp_map_get(
                        (lab or {}).get("near_done_at_checkpoint"),
                        int(cell["checkpoint"]),
                    ),
                    "runaway_like_at_cp": cp_map_get(
                        (lab or {}).get("runaway_like_at_checkpoint"),
                        int(cell["checkpoint"]),
                    ),
                    "ideal_steer_window_session": (lab or {}).get(
                        "ideal_steer_window"
                    ),
                    "provisional_meter_tags": tags,
                }
            )

    join_path = OUT / "PROVISIONAL-join-wave0-flash.jsonl"
    with join_path.open("w") as f:
        for row in join_rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")

    join_summary = {
        "soft_standard_hold": True,
        "provisional": True,
        "not_fp_miss_scoreboard": True,
        "generated_at": generated_at,
        "join_spec": "OUTCOME-SHEET.md checkpoint join; tags prefixed PROVISIONAL_",
        "why_window_status_unidentified": (
            "R2: results.jsonl is frozen at emit time with window_status=unidentified "
            "until a batch-wide label pass and documented meter regeneration. Sidecar "
            "outcome-labels.jsonl (20 sessions) is not merged back into results.jsonl "
            "by design (no silent backfill). FP/miss leaderboard rows are derived-only."
        ),
        "wave0_cells": len(join_rows),
        "labeled_sessions_in_join": len(
            {r["session_id"] for r in join_rows if r["label_status"] == "labeled"}
        ),
        "provisional_tag_counts": dict(tag_totals),
        "ideal_steer_window_not_none": [
            {
                "session_id": r["session_id"],
                "ideal_steer_window": r.get("ideal_steer_window"),
                "pattern_tags": r.get("pattern_tags"),
            }
            for r in labels
            if r.get("ideal_steer_window") not in (None, "none", "ambiguous")
        ],
        "next_measured_join_steps": [
            "Add ideal_steer_window_by_cp when per-checkpoint adjudication exists.",
            "Regenerate METERS.md from join with session-clustered CIs (not point rates).",
            "Cross-driver join on session_id+checkpoint for Flash/Luna/TypeSafe lever waves.",
            "Scenario sweep: join only at representative checkpoint — do not claim window FP/miss.",
        ],
        "output_join_table": str(join_path.relative_to(REPO)),
    }
    (OUT / "PROVISIONAL-join-summary.json").write_text(
        json.dumps(join_summary, indent=2) + "\n"
    )

    # --- Wave-0 lever combo table ---
    combo_stats: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    for cell in load_jsonl(wave0) if wave0.exists() else []:
        key = (
            cell.get("state_variant"),
            cell.get("question_variant"),
            cell.get("response_class"),
        )
        combo_stats[key][1] += 1
        if cell.get("fire"):
            combo_stats[key][0] += 1

    lever_doc = {
        "generated_at": generated_at,
        "note": "Only 4/12 planned lever combos executed in Wave-0 Flash (240-cell cap).",
        "combos": [
            {
                "state_variant": k[0],
                "question_variant": k[1],
                "response_class": k[2],
                "n_cells": v[1],
                "fire_count": v[0],
                "fire_rate": round(v[0] / v[1], 4),
            }
            for k, v in sorted(combo_stats.items(), key=lambda x: -x[1][0])
        ],
    }
    (OUT / "wave0-lever-combos.json").write_text(
        json.dumps(lever_doc, indent=2) + "\n"
    )

    # Console summary for CI/logs
    print(f"Wrote analysis artifacts to {OUT.relative_to(REPO)}")
    print(f"  streams inventoried: {len(inventory)}")
    print(f"  scenario rankings: {len(rankings)} scenarios")
    print(f"  provisional join rows: {len(join_rows)}")
    print(f"  provisional tags: {dict(tag_totals)}")


if __name__ == "__main__":
    main()
