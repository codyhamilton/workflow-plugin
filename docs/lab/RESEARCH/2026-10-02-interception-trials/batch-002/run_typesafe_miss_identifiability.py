#!/usr/bin/env python3
"""Run a post-hoc miss-identifiability probe over exact label keys.

The request contains only prefix-derived state and a risk question.  The
outcome sidecar is used after capture to stratify rows; it is never included
in a prompt or API state.  This is a diagnostic corpus, not a miss score.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path(os.environ.get("WF_REPO", Path(__file__).resolve().parents[5]))
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
OUT = BATCH / "typesafe-miss-identifiability"
RAW = OUT / "raw"
SNAP_DIRS = (BATCH / "snapshots-mid", BATCH / "snapshots-dense", BATCH / "snapshots")
LABELS = BATCH / "outcome-labels.jsonl"
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
AEST = ZoneInfo("Australia/Brisbane")
WORKERS = int(os.environ.get("TS_MISS_WORKERS", "8"))
STATE_VARIANTS = ("markers_focus", "phase_hints_focus")
HOLDOUT_STATE_VARIANT = "stats_only"
QUESTIONS = {
    "late_miss_risk": "Does waiting further risk a late miss on a runaway trajectory?",
    "silent_stall": "Are turns elapsing with near-zero tangible output, rather than recoverable progress?",
    "activity_without_value": "Is there frequent tool activity without checkable progress?",
}
LEAK_TOKENS = {
    "T", "t", "T_observed", "T_observed_session", "progress_frac",
    "full_length", "norm_length", "runaway_like", "near_done",
    "ideal_steer_window", "termination_cause",
}
LEAK_VALUE_RE = re.compile(
    r"\b(?:T_observed_session|T_observed|progress_frac|full_length|"
    r"norm_length|runaway_like|near_done|ideal_steer_window|"
    r"termination_cause)\b"
)

_spec = importlib.util.spec_from_file_location(
    "diagnostic_state_flip",
    BATCH / "run_typesafe_diagnostic_state_flip.py",
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("diagnostic state-flip helper is unavailable")
_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helper)


def load_labels() -> dict[str, dict[str, Any]]:
    labels = {}
    for line in LABELS.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("session_id"):
            labels[row["session_id"]] = row
    return labels


def load_packs() -> dict[str, dict[str, Any]]:
    packs = {}
    for directory in SNAP_DIRS:
        for path in sorted(directory.glob("*.json")):
            try:
                pack = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if not pack.get("checkpoints"):
                continue
            worker_id = pack.get("worker_id") or path.stem
            packs.setdefault(worker_id, {**pack, "worker_id": worker_id})
    return packs


def exact_label_keys() -> list[dict[str, Any]]:
    """Use sidecar key presence only; label values remain post-hoc."""
    labels = load_labels()
    packs = load_packs()
    selected = []
    for session_id, label in sorted(labels.items()):
        pack = packs.get(session_id)
        if not pack or label.get("label_status") != "labeled":
            continue
        label_keys = set((label.get("near_done_at_checkpoint") or {}))
        label_keys |= set((label.get("runaway_like_at_checkpoint") or {}))
        for checkpoint in sorted(label_keys, key=int):
            snap = next(
                (row for row in pack["checkpoints"] if str(row.get("checkpoint")) == checkpoint),
                None,
            )
            if not snap:
                continue
            full = _helper.derive_growth(snap.get("full_state") or {})
            if full is None:
                continue
            selected.append({
                "session_id": session_id,
                "checkpoint": int(checkpoint),
                "full_state": full,
                "harness": pack.get("harness"),
                "project": pack.get("project"),
                "population": "labeled_exact_key",
            })
    return selected


def non_maps_holdout_keys() -> list[dict[str, Any]]:
    """Use non-Maps representative prefixes without inventing tail fields."""
    selected = []
    for session_id, pack in sorted(load_packs().items()):
        project = str(pack.get("project") or "")
        if "open-pajero-maps" in project:
            continue
        checkpoints = sorted(pack.get("checkpoints") or [], key=lambda row: int(row["checkpoint"]))
        if not checkpoints:
            continue
        snap = checkpoints[len(checkpoints) // 2]
        full = _helper.strip_leaks(snap.get("full_state") or {})
        cumulative = full.get("cumulative") or {}
        if not cumulative:
            continue
        selected.append({
            "session_id": session_id,
            "checkpoint": int(snap["checkpoint"]),
            "full_state": full,
            "harness": pack.get("harness"),
            "project": project,
            "population": "non_maps_holdout",
        })
    return selected


def project_holdout(full: dict[str, Any]) -> dict[str, Any]:
    cumulative = full.get("cumulative") or {}
    return {
        "checkpoint_turn": full.get("checkpoint_turn"),
        "evidence_class": HOLDOUT_STATE_VARIANT,
        "cumulative": {
            key: cumulative.get(key)
            for key in ("api_turns", "compaction_event_count", "assistant_text_chars", "tool_histogram")
        },
    }


def build_cells(keys: list[dict[str, Any]], holdout_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells = []
    for state_variant in STATE_VARIANTS:
        for question_variant in QUESTIONS:
            for key in keys:
                scenario_id = f"state.{state_variant}|q.{question_variant}"
                raw = f"miss-identifiability|{scenario_id}|{key['session_id']}|{key['checkpoint']}"
                cells.append({
                    "cell_id": hashlib.sha256(raw.encode()).hexdigest()[:16],
                    "scenario_id": scenario_id,
                    "state_selection": state_variant,
                    "question_format": question_variant,
                    "response_class": "binary_fire",
                    "session_id": key["session_id"],
                    "checkpoint": key["checkpoint"],
                    "checkpoint_role": "exact_label_key_for_posthoc_stratification",
                    "framing": "H2",
                    "question": QUESTIONS[question_variant],
                    "state": _helper.project(key["full_state"], state_variant),
                    "harness": key["harness"],
                    "project": key["project"],
                    "population": key["population"],
                })
    for question_variant in QUESTIONS:
        for key in holdout_keys:
            scenario_id = f"state.{HOLDOUT_STATE_VARIANT}|q.{question_variant}"
            raw = f"miss-identifiability|{scenario_id}|{key['session_id']}|{key['checkpoint']}"
            cells.append({
                "cell_id": hashlib.sha256(raw.encode()).hexdigest()[:16],
                "scenario_id": scenario_id,
                "state_selection": HOLDOUT_STATE_VARIANT,
                "question_format": question_variant,
                "response_class": "binary_fire",
                "session_id": key["session_id"],
                "checkpoint": key["checkpoint"],
                "checkpoint_role": "non_maps_unlabeled_representative_holdout",
                "framing": "H2",
                "question": QUESTIONS[question_variant],
                "state": project_holdout(key["full_state"]),
                "harness": key["harness"],
                "project": key["project"],
                "population": key["population"],
            })
    return cells


def question_block(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "fire_now": {
            "type": "choice",
            "instructions": (
                cell["question"]
                + " Answer fire or defer from the prefix snapshot only. "
                + "Do not infer a final outcome or session length."
            ),
            "criteria": {
                "fire": "Fire now: the current evidence supports steering toward stop.",
                "defer": "Defer: productive, recoverable, or insufficient evidence.",
            },
        },
        "risk_horizon": {
            "type": "choice",
            "instructions": (
                "Classify the risk horizon from the snapshot only: now, soon, "
                "or insufficient_evidence."
            ),
            "criteria": {
                "now": "The evidence supports steering at this checkpoint.",
                "soon": "The evidence suggests a risk if continuation is unchecked.",
                "insufficient_evidence": "The prefix does not support a horizon judgment.",
            },
        },
    }


def post(cell: dict[str, Any], key: str) -> dict[str, Any]:
    body = {
        "model": MODEL,
        "state": {
            "checkpoint_turn": cell["checkpoint"],
            "evidence_class": cell["state_selection"],
            "scenario_id": cell["scenario_id"],
            "framing": cell["framing"],
            "response_class": cell["response_class"],
            "snapshot": cell["state"],
        },
        "questions": question_block(cell),
    }
    cell_id = cell["cell_id"]
    (RAW / f"{cell_id}-request.json").write_text(json.dumps(body, indent=2) + "\n")
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode())
            status = response.status
        (RAW / f"{cell_id}-response.json").write_text(json.dumps(payload) + "\n")
        answers = payload.get("answers") or {}
        fire = (answers.get("fire_now") or {}).get("choice")
        horizon = (answers.get("risk_horizon") or {}).get("choice")
        return {
            **{k: cell[k] for k in (
                "cell_id", "scenario_id", "state_selection", "question_format",
                "response_class", "session_id", "checkpoint", "checkpoint_role",
                "framing", "harness", "project", "population",
            )},
            "fire": fire,
            "risk_horizon": horizon,
            "http": status,
            "error": None,
            "usage": payload.get("usage"),
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        (RAW / f"{cell_id}-error.txt").write_text(f"HTTP {error.code}\n{detail}\n")
        return {
            **{k: cell[k] for k in ("cell_id", "scenario_id", "session_id", "checkpoint")},
            "http": error.code,
            "error": detail[:500],
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }
    except Exception as error:
        return {
            **{k: cell[k] for k in ("cell_id", "scenario_id", "session_id", "checkpoint")},
            "http": None,
            "error": f"{type(error).__name__}: {error}",
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }


def label_at(labels: dict[str, dict[str, Any]], row: dict[str, Any], field: str) -> Any:
    label = labels.get(row.get("session_id")) or {}
    return (label.get(field) or {}).get(str(row.get("checkpoint")))


def existing_cell_ids() -> set[str]:
    ids = set()
    for path in BATCH.glob("*/results.jsonl"):
        if path.parent == OUT:
            continue
        for line in path.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("cell_id"):
                ids.add(row["cell_id"])
    return ids


def leak_hits(cells: list[dict[str, Any]]) -> int:
    hits = 0
    def walk(value: Any) -> None:
        nonlocal hits
        if isinstance(value, dict):
            for key, child in value.items():
                if key in LEAK_TOKENS:
                    hits += 1
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            hits += len(LEAK_VALUE_RE.findall(value))
    for cell in cells:
        walk(cell["state"])
        walk(cell["question"])
    return hits


def write_meters(rows: list[dict[str, Any]], cells: list[dict[str, Any]], keys: list[dict[str, Any]]) -> None:
    labels = load_labels()
    successful = [row for row in rows if row.get("http") == 200 and not row.get("error")]
    by_axis = {}
    for state in (*STATE_VARIANTS, HOLDOUT_STATE_VARIANT):
        for question in QUESTIONS:
            group = [
                row for row in successful
                if row.get("state_selection") == state and row.get("question_format") == question
            ]
            positives = [row for row in group if label_at(labels, row, "runaway_like_at_checkpoint") == "yes"]
            by_axis[f"{state}|{question}"] = {
                "n": len(group),
                "fire_count": sum(row.get("fire") == "fire" for row in group),
                "fire_rate": round(sum(row.get("fire") == "fire" for row in group) / len(group), 4) if group else None,
                "runaway_positive_rows": len(positives),
                "fire_on_runaway_positive_rows": sum(row.get("fire") == "fire" for row in positives),
            }
    unique_keys = {(row.get("session_id"), row.get("checkpoint")) for row in successful}
    labeled_keys = {
        key for key in unique_keys
        if key[0] in labels
        and (
            str(key[1]) in (labels[key[0]].get("near_done_at_checkpoint") or {})
            or str(key[1]) in (labels[key[0]].get("runaway_like_at_checkpoint") or {})
        )
    }
    holdout_keys = unique_keys - labeled_keys
    is_holdout = lambda row: (
        row.get("population") == "non_maps_holdout"
        or row.get("state_selection") == HOLDOUT_STATE_VARIANT
    )
    non_maps_keys = {
        (row.get("session_id"), row.get("checkpoint"))
        for row in successful
        if is_holdout(row)
    }
    non_maps_labeled_keys = non_maps_keys & labeled_keys
    non_maps_unlabeled_keys = non_maps_keys - labeled_keys
    positive_keys = {
        key for key in unique_keys
        if label_at(labels, {"session_id": key[0], "checkpoint": key[1]}, "runaway_like_at_checkpoint") == "yes"
    }
    positive_label_keys_total = {
        (session_id, int(checkpoint))
        for session_id, label in labels.items()
        for checkpoint, value in (label.get("runaway_like_at_checkpoint") or {}).items()
        if value == "yes"
    }
    fire_by_key = defaultdict(int)
    for row in successful:
        if row.get("fire") == "fire":
            fire_by_key[(row.get("session_id"), row.get("checkpoint"))] += 1
    prior_ids = existing_cell_ids()
    cell_ids = [cell["cell_id"] for cell in cells]
    meters = {
        "status": "complete" if len(successful) == len(cells) else "partial",
        "scope": "miss_identifiability_diagnostic",
        "n_exact_label_keys_planned": len(keys),
        "n_unique_keys_successful": len(unique_keys),
        "n_labeled_keys_successful": len(labeled_keys),
        "n_non_maps_holdout_keys_successful": len(non_maps_keys),
        "n_non_maps_labeled_holdout_keys": len(non_maps_labeled_keys),
        "n_non_maps_unlabeled_holdout_keys": len(non_maps_unlabeled_keys),
        "n_holdout_cells_successful": sum(
            is_holdout(row) for row in successful
        ),
        "n_cells_planned": len(cells),
        "n_cells_successful": len(successful),
        "n_cells_errors": len(rows) - len(successful),
        "http_counts": dict(Counter(str(row.get("http")) for row in rows)),
        "http_success_rate": round(len(successful) / len(rows), 4) if rows else None,
        "cell_id_collisions": len(cell_ids) - len(set(cell_ids)),
        "overlap_with_prior_result_cell_ids": len(set(cell_ids) & prior_ids),
        "leak_spotcheck_hits": leak_hits(cells),
        "runaway_positive_unique_keys": len(positive_keys),
        "runaway_positive_label_keys_total": len(positive_label_keys_total),
        "runaway_positive_label_keys_gated_no_tail": len(positive_label_keys_total - unique_keys),
        "runaway_positive_rows": sum(
            label_at(labels, row, "runaway_like_at_checkpoint") == "yes"
            for row in successful
        ),
        "positive_keys_with_any_fire": sum(bool(fire_by_key[key]) for key in positive_keys),
        "all_keys_with_any_fire": sum(bool(fire_by_key[key]) for key in unique_keys),
        "by_state_question": by_axis,
        "label_values_in_prompt": False,
        "posthoc_label_join_only": True,
        "not_a_miss_scoreboard": True,
        "soft_standard_hold": True,
        "product_wiring": False,
        "generated_at": datetime.now(AEST).isoformat(timespec="seconds"),
    }
    (OUT / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    rows_by_harness = Counter(row.get("harness") for row in successful)
    projects = Counter(row.get("project") for row in successful)
    lines = [
        "# METERS — TypeSafe miss-identifiability probe",
        "",
        "**Soft Standard HOLD** — corpus and post-hoc analysis only; no behavior, hooks, unlock, or FP/miss scoreboard.",
        "",
        "This probe repeats exact sidecar checkpoint keys with H2 risk questions and",
        "flips `markers_focus` against `phase_hints_focus`. The sidecar is joined",
        "after capture; no label value is sent to TypeSafe.",
        "",
        f"- exact label keys planned: **{len(keys)}**",
        f"- non-Maps holdout cells: **{meters['n_holdout_cells_successful']}** "
        f"({meters['n_non_maps_labeled_holdout_keys']} sidecar-labeled keys; "
        f"{meters['n_non_maps_unlabeled_holdout_keys']} without sidecar rows)",
        f"- planned cells: **{len(cells)}**",
        f"- successful cells: **{len(successful)}**",
        f"- HTTP counts: `{json.dumps(meters['http_counts'], sort_keys=True)}`",
        f"- HTTP success rate: **{meters['http_success_rate']}**",
        f"- cell-id collisions: **{meters['cell_id_collisions']}**",
        f"- overlap with prior result cell IDs: **{meters['overlap_with_prior_result_cell_ids']}**",
        f"- leak spotcheck hits: **{meters['leak_spotcheck_hits']}**",
        f"- unique `runaway_like=yes` keys: **{meters['runaway_positive_unique_keys']}**",
        f"- total positive label keys: **{meters['runaway_positive_label_keys_total']}** "
        f"(gated for missing tail: **{meters['runaway_positive_label_keys_gated_no_tail']}**)",
        f"- positive keys with any fire: **{meters['positive_keys_with_any_fire']}**",
        "",
        f"Harness mix: `{dict(rows_by_harness)}`",
        f"Project mix: `{dict(projects)}`",
        "",
        "| state × question | n | fire | fire rate | positive rows | fire on positive |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, values in by_axis.items():
        lines.append(
            f"| `{axis}` | {values['n']} | {values['fire_count']} | "
            f"{values['fire_rate']} | {values['runaway_positive_rows']} | "
            f"{values['fire_on_runaway_positive_rows']} |"
        )
    lines += [
        "",
        "`fire_on_runaway_positive_rows` is a descriptive coverage diagnostic.",
        "It is not a miss rate: the corpus is sparse, labels are checkpoint-local,",
        "and no validated decision window or negative control protocol exists.",
    ]
    (OUT / "METERS.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    keys = exact_label_keys()
    holdout_keys = non_maps_holdout_keys()
    cells = build_cells(keys, holdout_keys)
    (OUT / "cells_plan.json").write_text(json.dumps({
        "wave": "typesafe-miss-identifiability",
        "scope": "diagnostic",
        "selection": "tail-bearing exact sidecar keys plus non-Maps representative holdout keys",
        "n_exact_label_keys": len(keys),
        "n_non_maps_holdout_keys": len(holdout_keys),
        "n_state_variants": len(STATE_VARIANTS) + 1,
        "n_questions": len(QUESTIONS),
        "n_cells_planned": len(cells),
        "state_variants": [*STATE_VARIANTS, HOLDOUT_STATE_VARIANT],
        "questions": list(QUESTIONS),
        "framing": "H2",
        "label_values_in_prompt": False,
        "posthoc_label_join_only": True,
        "soft_standard_hold": True,
        "product_wiring": False,
        "raw_capture_dir": "raw/",
    }, indent=2) + "\n")
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        (OUT / "BLOCKER.md").write_text("# BLOCKER\n\n`TYPESAFE_API_KEY` is missing; no meters claimed.\n")
        return 0
    results_path = OUT / "results.jsonl"
    done = {}
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("cell_id"):
                done[row["cell_id"]] = row
    todo = [cell for cell in cells if cell["cell_id"] not in done]
    with ThreadPoolExecutor(max_workers=WORKERS) as executor, results_path.open("a") as output:
        futures = [executor.submit(post, cell, key) for cell in todo]
        for future in as_completed(futures):
            row = future.result()
            done[row["cell_id"]] = row
            output.write(json.dumps(row) + "\n")
            output.flush()
    rows = [done[cell["cell_id"]] for cell in cells if cell["cell_id"] in done]
    write_meters(rows, cells, keys)
    print(json.dumps({
        "planned": len(cells),
        "rows": len(rows),
        "successful": sum(row.get("http") == 200 and not row.get("error") for row in rows),
        "errors": sum(bool(row.get("error")) for row in rows),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
