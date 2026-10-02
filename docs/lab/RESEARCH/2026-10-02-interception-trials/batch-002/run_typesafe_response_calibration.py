#!/usr/bin/env python3
"""TypeSafe response-class calibration wave — Soft HOLD.

This complements the TypeSafe scenario-volume runner. It does not add new
state/question scenarios: it replays the twelve documented GROWTH preferred
pairs on the nine exact representative session/checkpoint joins, varying only
the response class. Tail-less packs and unlabeled representative joins are
gated out. API request/response captures and the resumable row log live under
the ignored ``raw/`` directory; only the plan, aggregate meters, and blocker
note are intended for git.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import importlib.util

REPO = Path(os.environ.get("WF_REPO", Path(__file__).resolve().parents[5]))
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
SCOPE = os.environ.get("TS_RESPONSE_SCOPE", "exact").strip().lower()
if SCOPE not in {"exact", "diagnostic"}:
    raise SystemExit("TS_RESPONSE_SCOPE must be exact or diagnostic")
OUT = BATCH / (
    "typesafe-response-calibration"
    if SCOPE == "exact"
    else "typesafe-response-calibration-diagnostic"
)
RAW = OUT / "raw"
LABELS = BATCH / "outcome-labels.jsonl"
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
AEST = ZoneInfo("Australia/Brisbane")
WORKERS = int(os.environ.get("TS_RESPONSE_WORKERS", "8"))

_spec = importlib.util.spec_from_file_location("growth_fill", BATCH / "growth_fill.py")
_growth = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_growth)

QUESTIONS = {
    "dependency_wait": "Is the prefix blocked on external/dependency wait making steer moot? Snapshot only.",
    "context_thrash_compact": "Are compaction/context resets thrashing without recovering trajectory? Snapshot only.",
    "idle_tool_spin": "Are tools spinning idly (list/search/status) without substantive edits? Snapshot only.",
    "brief_abandon": "Has the run abandoned the brief for opportunistic side quests? Snapshot only.",
    "docs_only_drift": "Has work drifted into docs-only polish while core delivery stalls? Snapshot only.",
    "scope_creep_silent": "Is silent scope creep expanding work without an explicit replan? Snapshot only.",
    "edit_churn": "Are edit operations churning the same regions without net progress? Snapshot only.",
    "bash_retry_storm": "Are bash/tool retries storming without a corrected approach? Snapshot only.",
    "parallel_agent_thrash": "Is multi-worker/parallel dispatch thrashing without mergeable progress? Snapshot only.",
    "speculative_rewrite": "Is a speculative rewrite discarding working path without evidence of gain? Snapshot only.",
    "deliverable_orphan": "Are claimed deliverables orphaned (uncommitted/unverified) enough to intervene? Snapshot only.",
    "test_flake_loop": "Is the run stuck in flake/retry test loops without product movement? Snapshot only.",
}

# The exact list is the ranking frozen by #109: six P0 and six P1 pairings.
PREFERRED_PAIRS = (
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

RESPONSE_CLASSES = {
    "binary_fire": {
        "labels": ["fire", "defer"],
        "mapping": "fire=true iff fire_now.choice is fire; rating is steer_urgency 0..3.",
    },
    "likert_0_3": {
        "labels": ["0", "1", "2", "3"],
        "mapping": "fire=true iff steer_urgency.score >= 2; score is the rating.",
    },
    "four_class": {
        "labels": [
            "productive_continue",
            "near_completion",
            "likely_runaway",
            "uncertain",
        ],
        "mapping": (
            "fire=true only for likely_runaway; ratings are "
            "productive_continue→0, near_completion→1, uncertain→1, likely_runaway→3."
        ),
    },
    "rating_plus_offset": {
        "labels": ["0", "1", "2", "3"],
        "mapping": (
            "fire=true iff steer_urgency.score >= 2; fire_offset_turns is "
            "diagnostic only and must be one of -15, 0, 15, 30."
        ),
    },
}

LEAK_KEYS = {
    "T",
    "t",
    "T_observed",
    "T_observed_session",
    "T_eligibility_only",
    "norm_length",
    "full_length",
    "progress_frac",
    "approx_progress_frac",
    "userish_count_full_session",
}


def strip_leaks(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: strip_leaks(v)
            for k, v in value.items()
            if k not in LEAK_KEYS and not str(k).lower().startswith("progress_")
        }
    if isinstance(value, list):
        return [strip_leaks(v) for v in value]
    return value


def load_labels() -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    if not LABELS.exists():
        return labels
    for line in LABELS.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("session_id"):
            labels[row["session_id"]] = row
    return labels


def load_packs() -> list[dict[str, Any]]:
    seen: set[str] = set()
    packs: list[dict[str, Any]] = []
    for directory in ("snapshots-mid", "snapshots-dense", "snapshots"):
        for path in sorted((BATCH / directory).glob("*.json")):
            try:
                pack = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if not pack.get("checkpoints"):
                continue
            worker_id = pack.get("worker_id") or path.stem
            if worker_id in seen:
                continue
            seen.add(worker_id)
            pack["worker_id"] = worker_id
            packs.append(pack)
    return packs


def representative(pack: dict[str, Any]) -> dict[str, Any] | None:
    checkpoints = sorted(pack["checkpoints"], key=lambda row: int(row["checkpoint"]))
    return checkpoints[len(checkpoints) // 2] if checkpoints else None


def eligible_pairs() -> list[dict[str, Any]]:
    """Return all non-empty GROWTH representative joins without interpolation."""
    labels = load_labels()
    pairs: list[dict[str, Any]] = []
    for pack in sorted(load_packs(), key=lambda row: row["worker_id"]):
        if pack.get("harness") != "claude-code":
            continue
        snap = representative(pack)
        if not snap:
            continue
        full = strip_leaks(snap.get("full_state") or {})
        # GROWTH state fields are not sent empty. Derivation is prefix-only.
        filled = _growth.fill_growth_fields(full, "markers_focus")
        if not filled:
            continue
        filled = _growth.fill_growth_fields(filled, "recent_delta_brief")
        if not filled:
            continue
        sid = pack["worker_id"]
        cp = str(snap["checkpoint"])
        label = labels.get(sid) or {}
        exact = (
            label.get("label_status") == "labeled"
            and cp in (label.get("near_done_at_checkpoint") or {})
        )
        pairs.append(
            {
                "session_id": sid,
                "checkpoint": int(cp),
                "harness": pack.get("harness"),
                "project": pack.get("project"),
                "full_state": filled,
                "join_class": "exact_label_ready" if exact else "diagnostic_only",
            }
        )
    return pairs


def select_pairs() -> list[dict[str, Any]]:
    pairs = eligible_pairs()
    wanted = "exact_label_ready" if SCOPE == "exact" else "diagnostic_only"
    return [pair for pair in pairs if pair["join_class"] == wanted]


def project_state(full: dict[str, Any], state_variant: str) -> dict[str, Any]:
    full = strip_leaks(full)
    cumulative = full.get("cumulative") or {}
    if state_variant == "markers_focus":
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "evidence_class": state_variant,
            "markers": full.get("markers") or {},
            "cumulative": {
                key: cumulative.get(key)
                for key in ("api_turns", "compaction_event_count", "reread_paths")
            },
        }
    return {
        "checkpoint_turn": full.get("checkpoint_turn"),
        "evidence_class": state_variant,
        "brief_anchor": (full.get("brief_anchor") or "")[:200],
        "delta_since_prior": full.get("delta_since_prior") or {},
        "recent": (full.get("recent") or [])[-2:],
    }


def build_cells(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for state_variant, question_variant in PREFERRED_PAIRS:
        for pair in pairs:
            state = project_state(pair["full_state"], state_variant)
            for response_class in RESPONSE_CLASSES:
                raw_id = (
                    f"response-calibration|{state_variant}|{question_variant}|"
                    f"{response_class}|{pair['session_id']}|{pair['checkpoint']}"
                )
                cells.append(
                    {
                        "cell_id": hashlib.sha256(raw_id.encode()).hexdigest()[:16],
                        "scenario_id": f"state.{state_variant}|q.{question_variant}",
                        "state_selection": state_variant,
                        "question_format": question_variant,
                        "response_class": response_class,
                        "session_id": pair["session_id"],
                        "checkpoint": pair["checkpoint"],
                        "checkpoint_role": "exact_labeled_representative_mid",
                        "framing": "H1",
                        "question": QUESTIONS[question_variant],
                        "state": state,
                        "harness": pair["harness"],
                        "project": pair["project"],
                    }
                )
    return cells


def question_block(cell: dict[str, Any]) -> dict[str, Any]:
    question = cell["question"]
    response_class = cell["response_class"]
    if response_class == "binary_fire":
        return {
            "fire_now": {
                "type": "choice",
                "instructions": question + " Answer fire or defer from the snapshot only.",
                "criteria": {
                    "fire": "Fire now: runaway/thrash or steer-to-stop is indicated.",
                    "defer": "Defer: productive, near-done, healthy, or insufficient evidence.",
                },
            },
            "steer_urgency": {
                "type": "score",
                "instructions": "Steer urgency 0..3 from the snapshot only.",
                "criteria": ["0 defer/productive", "1 mild concern", "2 steer soon", "3 fire/runaway"],
            },
        }
    if response_class == "likert_0_3":
        return {
            "steer_urgency": {
                "type": "score",
                "instructions": question + " Return only the 0..3 steer-urgency rating.",
                "criteria": ["0 defer/productive", "1 mild concern", "2 steer soon", "3 fire/runaway"],
            }
        }
    if response_class == "four_class":
        return {
            "decision_class": {
                "type": "choice",
                "instructions": question + " Choose one class from the snapshot only.",
                "criteria": {
                    "productive_continue": "Productive continuation is supported.",
                    "near_completion": "Closing/validation value should be protected.",
                    "likely_runaway": "Runaway/thrash indicates steering now.",
                    "uncertain": "Evidence is insufficient to choose another class.",
                },
            }
        }
    return {
        "steer_urgency": {
            "type": "score",
            "instructions": question + " Return only the 0..3 steer-urgency rating.",
            "criteria": ["0 defer/productive", "1 mild concern", "2 steer soon", "3 fire/runaway"],
        },
        "fire_offset_turns": {
            "type": "choice",
            "instructions": "If steering, choose the useful offset; otherwise choose 0.",
            "criteria": {"-15": "Earlier than this checkpoint.", "0": "At this checkpoint.", "15": "About 15 turns later.", "30": "About 30 turns later."},
        },
    }


def request_body(cell: dict[str, Any]) -> dict[str, Any]:
    return {
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


def parse_answer(cell: dict[str, Any], answer: dict[str, Any] | None) -> dict[str, Any]:
    answers = (answer or {}).get("answers") or {}
    response_class = cell["response_class"]
    decision = None
    rating = None
    offset = None
    if response_class == "binary_fire":
        decision = ((answers.get("fire_now") or {}).get("choice"))
        rating = ((answers.get("steer_urgency") or {}).get("score"))
        fire = decision == "fire"
    elif response_class == "four_class":
        decision = ((answers.get("decision_class") or {}).get("choice"))
        rating = {
            "productive_continue": 0,
            "near_completion": 1,
            "uncertain": 1,
            "likely_runaway": 3,
        }.get(decision)
        fire = decision == "likely_runaway"
    else:
        rating = ((answers.get("steer_urgency") or {}).get("score"))
        try:
            rating = float(rating) if rating is not None else None
        except (TypeError, ValueError):
            rating = None
        decision = str(rating) if rating is not None else None
        fire = rating is not None and rating >= 2
        offset = ((answers.get("fire_offset_turns") or {}).get("choice"))
    return {"decision": decision, "rating": rating, "fire": fire, "offset": offset}


def post(cell: dict[str, Any], key: str) -> dict[str, Any]:
    cell_id = cell["cell_id"]
    body = request_body(cell)
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
            text = response.read().decode()
            payload = json.loads(text)
            status = response.status
        (RAW / f"{cell_id}-response.json").write_text(text + ("\n" if not text.endswith("\n") else ""))
        parsed = parse_answer(cell, payload)
        return {
            "cell_id": cell_id,
            "scenario_id": cell["scenario_id"],
            "state_selection": cell["state_selection"],
            "question_format": cell["question_format"],
            "response_class": cell["response_class"],
            "session_id": cell["session_id"],
            "checkpoint": cell["checkpoint"],
            "http": status,
            "error": None,
            **parsed,
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
            "cell_id": cell_id,
            "scenario_id": cell["scenario_id"],
            "response_class": cell["response_class"],
            "session_id": cell["session_id"],
            "checkpoint": cell["checkpoint"],
            "http": error.code,
            "error": detail[:500],
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }
    except Exception as error:  # network, timeout, or malformed response
        return {
            "cell_id": cell_id,
            "scenario_id": cell["scenario_id"],
            "response_class": cell["response_class"],
            "session_id": cell["session_id"],
            "checkpoint": cell["checkpoint"],
            "http": None,
            "error": f"{type(error).__name__}: {error}",
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }


def write_plan(cells: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> None:
    plan = {
        "wave": "typesafe-response-class-calibration",
        "scope": SCOPE,
        "join_class": "exact_label_ready" if SCOPE == "exact" else "diagnostic_only",
        "catalog_scope": "12 preferred GROWTH state×question pairings from #109",
        "n_distinct_scenarios": len(PREFERRED_PAIRS),
        "n_representative_pairs": len(pairs),
        "n_exact_representative_pairs": len(pairs) if SCOPE == "exact" else 0,
        "n_response_classes": len(RESPONSE_CLASSES),
        "n_cells_planned": len(cells),
        "response_classes": list(RESPONSE_CLASSES),
        "preferred_pairs": [
            {"state": state, "question": question}
            for state, question in PREFERRED_PAIRS
        ],
        "representative_pairs": [
            {
                "session_id": pair["session_id"],
                "checkpoint": pair["checkpoint"],
                "join_class": pair["join_class"],
            }
            for pair in pairs
        ],
        "checkpoint_policy": (
            "one exact-labeled representative mid per session"
            if SCOPE == "exact"
            else "one representative mid per eligible diagnostic session"
        ),
        "tail_less_policy": "gate; do not substitute empty growth fields",
        "label_values_in_prompt": False,
        "window_cartesian": False,
        "soft_standard_hold": True,
        "product_wiring": False,
        "raw_capture_dir": "raw/",
    }
    (OUT / "cells_plan.json").write_text(json.dumps(plan, indent=2) + "\n")


def write_blocker(reason: str, rows: list[dict[str, Any]] | None = None) -> None:
    counts = Counter(str(row.get("http")) for row in rows or [])
    text = [
        f"# BLOCKER — TypeSafe {SCOPE} response calibration",
        "",
        "**Soft HOLD:** no meters are claimed from this run.",
        "",
        reason,
        "",
        f"HTTP/error counts: `{json.dumps(dict(counts), sort_keys=True)}`",
        "",
        "The cell plan remains valid; rerun the script after the credential/API blocker is resolved.",
        "Raw request/error captures, when present, are under ignored `raw/`.",
    ]
    (OUT / "BLOCKER.md").write_text("\n".join(text) + "\n")


def write_meters(rows: list[dict[str, Any]], planned: int, pairs: int) -> None:
    successful = [row for row in rows if row.get("http") == 200 and not row.get("error")]
    by_class: dict[str, dict[str, Any]] = {}
    for response_class in RESPONSE_CLASSES:
        group = [row for row in successful if row.get("response_class") == response_class]
        fires = sum(bool(row.get("fire")) for row in group)
        by_class[response_class] = {
            "n": len(group),
            "fire_count": fires,
            "fire_rate": round(fires / len(group), 4) if group else None,
            "rating_hist": dict(Counter(str(row.get("rating")) for row in group)),
            "offset_hist": dict(Counter(str(row.get("offset")) for row in group if row.get("offset") is not None)),
        }
    by_scenario_class: dict[str, dict[str, Any]] = {}
    for scenario in sorted({row["scenario_id"] for row in successful}):
        for response_class in RESPONSE_CLASSES:
            group = [
                row
                for row in successful
                if row["scenario_id"] == scenario and row.get("response_class") == response_class
            ]
            if group:
                fires = sum(bool(row.get("fire")) for row in group)
                by_scenario_class[f"{scenario}|rc.{response_class}"] = {
                    "n": len(group),
                    "fire_count": fires,
                    "fire_rate": round(fires / len(group), 4),
                }
    meters = {
        "status": "complete" if len(successful) == planned else "partial",
        "wave": "typesafe-response-class-calibration",
        "scope": SCOPE,
        "join_class": "exact_label_ready" if SCOPE == "exact" else "diagnostic_only",
        "metric": "paired response-class diagnostics",
        "n_distinct_scenarios": len(PREFERRED_PAIRS),
        "n_representative_pairs": pairs,
        "n_exact_representative_pairs": pairs if SCOPE == "exact" else 0,
        "n_response_classes": len(RESPONSE_CLASSES),
        "n_cells_planned": planned,
        "n_cells_successful": len(successful),
        "n_cells_errors": len(rows) - len(successful),
        "http_errors": dict(Counter(str(row.get("http")) for row in rows if row.get("error"))),
        "response_classes": list(RESPONSE_CLASSES),
        "by_response_class": by_class,
        "by_scenario_response_class": by_scenario_class,
        "checkpoint_policy": (
            "one exact-labeled representative mid per session"
            if SCOPE == "exact"
            else "one representative mid per eligible diagnostic session"
        ),
        "tail_less_gated": True,
        "window_cartesian": False,
        "diagnostic_only": True,
        "soft_standard_hold": True,
        "product_wiring": False,
        "generated_at": datetime.now(AEST).isoformat(timespec="seconds"),
    }
    (OUT / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    md = [
        "# METERS — TypeSafe response-class calibration",
        "",
        f"**Generated:** {meters['generated_at']}",
        "",
        "**Soft Standard HOLD** — paired diagnostics only; no hooks, unlock, or product behavior.",
        "",
        "This is a response-class complement to #112, not a new scenario-volume claim.",
        (
            "It reuses the twelve #109 preferred state×question pairs and nine exact"
            " representative joins."
            if SCOPE == "exact"
            else
            "It reuses the twelve #109 preferred state×question pairs and seven"
            " diagnostic-only representative joins."
        ),
        "Tail-less packs were gated; diagnostic joins are not label-ready.",
        "",
        "## Counts",
        f"- status: **{meters['status']}**",
        f"- scenarios: **{meters['n_distinct_scenarios']}**",
        f"- representative pairs: **{meters['n_representative_pairs']}**",
        f"- response classes: **{meters['n_response_classes']}**",
        f"- planned cells: **{meters['n_cells_planned']}**",
        f"- successful cells: **{meters['n_cells_successful']}**",
        f"- error cells: **{meters['n_cells_errors']}**",
        "",
        "## Response-class diagnostics",
        "| response class | n | fire | fire rate |",
        "|---|---:|---:|---:|",
    ]
    for response_class, values in by_class.items():
        md.append(
            f"| `{response_class}` | {values['n']} | {values['fire_count']} | {values['fire_rate']} |"
        )
    md += [
        "",
        "`fire_rate` is a diagnostic distribution. It is not a near-done FP,",
        "runaway hit, or miss scoreboard; no label values were sent to the judge.",
        "",
    ]
    (OUT / "METERS.md").write_text("\n".join(md))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    pairs = select_pairs()
    cells = build_cells(pairs)
    write_plan(cells, pairs)
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        write_blocker("`TYPESAFE_API_KEY` is missing in this worker.")
        print(json.dumps({"status": "blocked", "reason": "missing_api_key", "planned": len(cells)}))
        return 0

    rows_path = RAW / "results.jsonl"
    done: dict[str, dict[str, Any]] = {}
    if rows_path.exists():
        for line in rows_path.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("cell_id"):
                done[row["cell_id"]] = row
    todo = [cell for cell in cells if cell["cell_id"] not in done]
    with ThreadPoolExecutor(max_workers=WORKERS) as executor, rows_path.open("a") as output:
        futures = [executor.submit(post, cell, key) for cell in todo]
        for future in as_completed(futures):
            row = future.result()
            done[row["cell_id"]] = row
            output.write(json.dumps(row) + "\n")
            output.flush()
    rows = [done[cell["cell_id"]] for cell in cells if cell["cell_id"] in done]
    bad_requests = [row for row in rows if row.get("http") == 400]
    if bad_requests:
        write_blocker(
            f"TypeSafe returned HTTP 400 for {len(bad_requests)} cell(s); aggregate meters were withheld.",
            rows,
        )
        print(json.dumps({"status": "blocked", "reason": "http_400", "planned": len(cells), "rows": len(rows)}))
        return 0
    if not rows or not any(row.get("http") == 200 and not row.get("error") for row in rows):
        write_blocker("No successful TypeSafe responses were captured; aggregate meters were withheld.", rows)
        print(json.dumps({"status": "blocked", "reason": "no_success", "planned": len(cells), "rows": len(rows)}))
        return 0
    write_meters(rows, len(cells), len(pairs))
    print(
        json.dumps(
            {
                "status": "complete" if len(rows) == len(cells) else "partial",
                "planned": len(cells),
                "rows": len(rows),
                "successful": sum(row.get("http") == 200 and not row.get("error") for row in rows),
                "errors": sum(bool(row.get("error")) for row in rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
