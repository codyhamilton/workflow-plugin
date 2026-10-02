#!/usr/bin/env python3
"""Build the descriptive Soft HOLD comparison for the TypeSafe probes."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
OUT_JSON = BATCH / "TYPESAFE-SOFT-HOLD-ANALYSIS.json"
OUT_MD = BATCH / "TYPESAFE-SOFT-HOLD-ANALYSIS.md"
PREFERRED = (
    ("markers_focus", "dependency_wait"),
    ("markers_focus", "context_thrash_compact"),
    ("markers_focus", "idle_tool_spin"),
    ("recent_delta_brief", "brief_abandon"),
    ("recent_delta_brief", "docs_only_drift"),
    ("recent_delta_brief", "scope_creep_silent"),
    ("recent_delta_brief", "edit_churn"),
    ("recent_delta_brief", "bash_retry_storm"),
    ("recent_delta_brief", "parallel_agent_thrash"),
    ("markers_focus", "test_flake_loop"),
    ("recent_delta_brief", "speculative_rewrite"),
    ("recent_delta_brief", "deliverable_orphan"),
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def baseline() -> dict:
    meters = read_json(BATCH / "typesafe-scenario-sweep/meters.json")
    by_pair = {}
    for state, question in PREFERRED:
        key = f"state.{state}|q.{question}"
        by_pair[key] = meters.get("outcomes_by_scenario", {}).get(key, {
            "n_sessions": 0, "fire_count": 0, "fire_rate": None,
        })
    return {
        "source": "TypeSafe #110 growth-fill-v1 preferred scenario meters",
        "source_commit": "44764b9",
        "n_distinct_scenarios": meters.get("n_distinct_scenarios"),
        "n_sessions_swept": meters.get("n_sessions_swept"),
        "n_cells_incidental": meters.get("n_cells_incidental"),
        "errors": meters.get("errors"),
        "preferred_pairs": by_pair,
        "preferred_cells": sum(value.get("n_sessions", 0) for value in by_pair.values()),
        "preferred_fires": sum(value.get("fire_count", 0) for value in by_pair.values()),
    }


def probe_tables() -> tuple[dict, dict]:
    flip_meters = read_json(BATCH / "typesafe-diagnostic-state-flip/meters.json")
    flip_rows = read_rows(BATCH / "typesafe-diagnostic-state-flip/results.jsonl")
    flip_by_axis = defaultdict(lambda: {"n": 0, "fire": 0})
    for row in flip_rows:
        if row.get("http") != 200:
            continue
        key = f"{row.get('state_selection')}|{row.get('question_format')}|{row.get('response_class')}"
        flip_by_axis[key]["n"] += 1
        flip_by_axis[key]["fire"] += row.get("fire") is True
    for value in flip_by_axis.values():
        value["fire_rate"] = round(value["fire"] / value["n"], 4) if value["n"] else None

    miss_meters = read_json(BATCH / "typesafe-miss-identifiability/meters.json")
    miss_rows = read_rows(BATCH / "typesafe-miss-identifiability/results.jsonl")
    miss_by_axis = defaultdict(lambda: {"n": 0, "fire": 0, "population": Counter()})
    for row in miss_rows:
        if row.get("http") != 200:
            continue
        key = f"{row.get('state_selection')}|{row.get('question_format')}"
        miss_by_axis[key]["n"] += 1
        miss_by_axis[key]["fire"] += row.get("fire") == "fire"
        population = row.get("population")
        if not population:
            population = "labeled_exact_key" if row.get("session_id") else "unknown"
        miss_by_axis[key]["population"][population] += 1
    miss_table = {}
    for key, value in miss_by_axis.items():
        miss_table[key] = {
            "n": value["n"],
            "fire": value["fire"],
            "fire_rate": round(value["fire"] / value["n"], 4) if value["n"] else None,
            "population": dict(value["population"]),
        }
    return (
        {
            "meters": flip_meters,
            "by_axis": dict(flip_by_axis),
            "rows": len(flip_rows),
        },
        {
            "meters": miss_meters,
            "by_axis": miss_table,
            "rows": len(miss_rows),
        },
    )


def main() -> int:
    base = baseline()
    flip, miss = probe_tables()
    flip_fire = sum(value["fire"] for value in flip["by_axis"].values())
    miss_fire = sum(value["fire"] for value in miss["by_axis"].values())
    analysis = {
        "scope": "Soft HOLD docs/trials/evidence only",
        "baseline": base,
        "diagnostic_state_flip": flip,
        "miss_identifiability": miss,
        "comparison_rules": [
            "Fire rates are descriptive judge-output distributions, not precision, recall, FP, miss, or unlock evidence.",
            "The #110 preferred denominator is 12 pairs × 16 tail-valid sessions; the new diagnostic denominator is 12 pairs × 7 non-label-ready representatives × 2 state variants × 2 response classes.",
            "The miss probe joins outcome labels only after capture and excludes three positive label keys whose snapshots have no tail evidence.",
            "The non-Maps holdout is independent of the exact tail-gated selection; any sidecar overlap is post-hoc and remains descriptive.",
        ],
        "open_gaps": [
            "Only one runaway_like=yes checkpoint key is state-valid after the tail gate; three of four positive label keys remain missing-state gated.",
            "No validated decision-window or negative-control protocol supports an FP/miss scoreboard.",
            "The response-class/state flip is diagnostic and does not establish a preferred representation.",
            "H2 and non-Maps holdout coverage remain exploratory; a future labeled non-Maps corpus is still needed.",
        ],
        "hold": {
            "soft_standard_hold": True,
            "product_wiring": False,
            "hooks": False,
            "local_llama_8080": False,
        },
    }
    OUT_JSON.write_text(json.dumps(analysis, indent=2) + "\n")

    base_rate = (
        f"{base['preferred_fires']}/{base['preferred_cells']} "
        f"({base['preferred_fires'] / base['preferred_cells']:.4f})"
        if base["preferred_cells"] else "n/a"
    )
    flip_m = flip["meters"]
    miss_m = miss["meters"]
    lines = [
        "# TypeSafe Soft HOLD analysis — diagnostic and miss-identifiability axes",
        "",
        "**Evidence only.** No behavior, hooks, Standard unlock, or local `:8080` llama path.",
        "",
        "## Comparison against #110",
        "",
        "| corpus | scenarios / keys | cells | successful | fires | interpretation |",
        "|---|---:|---:|---:|---:|---|",
        f"| #110 preferred TypeSafe (`44764b9`) | 12 pairs × 16 sessions | "
        f"{base['preferred_cells']} | {base['preferred_cells']} | {base['preferred_fires']} | "
        "prior preferred scenario distribution |",
        f"| diagnostic state flip | 24 state×question scenarios × 7 reps × 2 classes | "
        f"{flip_m['n_cells_planned']} | {flip_m['n_cells_successful']} | {flip_fire} | "
        "non-label-ready representation contrast |",
        f"| miss-identifiability + holdout | 52 exact keys + 25 non-Maps keys | "
        f"{miss_m['n_cells_planned']} | {miss_m['n_cells_successful']} | {miss_fire} | "
        "post-hoc risk probe; no scoreboard |",
        "",
        f"#110 preferred fire distribution: **{base_rate}**. "
        "The denominators and representative populations differ, so this is not a treatment comparison.",
        "",
        "## 12×7 diagnostic extension",
        "",
        f"- **{flip_m['n_cells_successful']}/{flip_m['n_cells_planned']}** HTTP-200 cells",
        f"- state flip: `markers_focus` vs `phase_hints_focus`",
        f"- response classes: `binary_fire` and `four_class`",
        f"- leak hits: **{flip_m['leak_spotcheck_hits']}**; cell collisions: **{flip_m['cell_id_collisions']}**",
        "",
        "| state × response class | n | fires | rate |",
        "|---|---:|---:|---:|",
    ]
    for key, value in flip["by_axis"].items():
        lines.append(f"| `{key}` | {value['n']} | {value['fire']} | {value['fire_rate']} |")
    lines += [
        "",
        "The four classes are diagnostic output formats. The seven representatives remain",
        "non-label-ready, so these rates are not joins to gold outcomes.",
        "",
        "## Miss-identifiability probe",
        "",
        f"- **{miss_m['n_cells_successful']}/{miss_m['n_cells_planned']}** HTTP-200 cells",
        f"- exact sidecar keys with usable tail: **{miss_m['n_exact_label_keys_planned']}**",
        f"- non-Maps holdout: **{miss_m['n_holdout_cells_successful']} cells / "
        f"{miss_m['n_non_maps_holdout_keys_successful']} keys** "
        f"({miss_m['n_non_maps_labeled_holdout_keys']} sidecar-labeled; "
        f"{miss_m['n_non_maps_unlabeled_holdout_keys']} without sidecar rows)",
        f"- sidecar `runaway_like=yes` keys: **{miss_m['runaway_positive_label_keys_total']} total**, "
        f"**{miss_m['runaway_positive_unique_keys']} state-valid**, "
        f"**{miss_m['runaway_positive_label_keys_gated_no_tail']} gated for missing tail**",
        f"- HTTP success: **{miss_m['http_success_rate']}**; leak hits: **{miss_m['leak_spotcheck_hits']}**; "
        f"collisions: **{miss_m['cell_id_collisions']}**; prior-ID overlap: "
        f"**{miss_m['overlap_with_prior_result_cell_ids']}**",
        "",
        "| state × question | n | fires | rate |",
        "|---|---:|---:|---:|",
    ]
    for key, value in miss["by_axis"].items():
        lines.append(f"| `{key}` | {value['n']} | {value['fire']} | {value['fire_rate']} |")
    lines += [
        "",
        "The probe found a state-valid positive key and produced descriptive fire coverage",
        "on it, but that is not a miss rate: three other positive label keys are not",
        "state-eligible, and there is no validated decision window or negative-control set.",
        "The non-Maps rows are a holdout population; sidecar overlap is not treated as a",
        "false-positive label or a miss score.",
        "",
        "## Remaining open",
        "",
        "- Add tail-bearing labeled positive prefixes for the three currently gated keys.",
        "- Establish a labeled non-Maps holdout and a pre-specified decision-window protocol.",
        "- Keep H2 nulls/never-fire baselines and markers-vs-phase-hints as exploratory axes.",
        "- Keep all future meters descriptive until those joins are independently validated.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "analysis_json": str(OUT_JSON),
        "analysis_md": str(OUT_MD),
        "baseline_preferred": base_rate,
        "diagnostic_cells": flip_m["n_cells_successful"],
        "miss_cells": miss_m["n_cells_successful"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
