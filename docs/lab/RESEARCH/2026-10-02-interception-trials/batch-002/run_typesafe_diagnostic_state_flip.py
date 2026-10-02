#!/usr/bin/env python3
"""Run the non-label-ready 12x7 diagnostic state-flip complement.

This is evidence-only.  It reuses the seven representative diagnostic pairs
from #114, the twelve preferred GROWTH state/question pairs from #109, and
compares markers_focus with phase_hints_focus.  Labels are used only by the
post-hoc analysis script; no label value enters a request.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path(os.environ.get("WF_REPO", Path(__file__).resolve().parents[5]))
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
OUT = BATCH / "typesafe-diagnostic-state-flip"
RAW = OUT / "raw"
SNAP_DIRS = (BATCH / "snapshots-mid", BATCH / "snapshots-dense", BATCH / "snapshots")
LABELS = BATCH / "outcome-labels.jsonl"
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
AEST = ZoneInfo("Australia/Brisbane")
WORKERS = int(os.environ.get("TS_DIAGNOSTIC_WORKERS", "8"))

DIAGNOSTIC_REPRESENTATIVES = (
    ("004a52c29513", 35),
    ("4f4b98803720", 70),
    ("919012be9f39", 55),
    ("9659bf4fc9f4", 70),
    ("9a9249e2f356", 35),
    ("aa9e5be26e92", 55),
    ("ac7c401379d0", 35),
)
STATE_VARIANTS = ("markers_focus", "phase_hints_focus")
QUESTIONS = {
    "dependency_wait": "Is the prefix blocked on external or dependency wait, making a steer moot?",
    "context_thrash_compact": "Are compaction or context resets repeating without recovering trajectory?",
    "idle_tool_spin": "Are tools spinning without substantive or checkable progress?",
    "brief_abandon": "Has the run abandoned its brief for opportunistic side quests?",
    "docs_only_drift": "Has work drifted into documentation polish while core delivery stalls?",
    "scope_creep_silent": "Is silent scope creep expanding work without an explicit replan?",
    "edit_churn": "Are edits churning the same regions without net progress?",
    "bash_retry_storm": "Are tool or command retries storming without a corrected approach?",
    "parallel_agent_thrash": "Is parallel dispatch thrashing without mergeable progress?",
    "test_flake_loop": "Is the run stuck in flaky or retrying tests without product movement?",
    "speculative_rewrite": "Is a speculative rewrite discarding a working path without evidence of gain?",
    "deliverable_orphan": "Are claimed deliverables orphaned or unverified enough to intervene?",
}
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
RESPONSE_CLASSES = ("binary_fire", "four_class")
LEAK_KEYS = {
    "T", "t", "T_observed", "T_observed_session", "T_eligibility_only",
    "norm_length", "full_length", "progress_frac", "approx_progress_frac",
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
        return [strip_leaks(item) for item in value]
    return value


def derive_growth(full: dict[str, Any]) -> dict[str, Any] | None:
    """Derive non-empty GROWTH fields from prefix tail evidence only."""
    full = strip_leaks(full)
    tail = full.get("tail") or []
    if not tail:
        return None
    cumulative = full.get("cumulative") or {}
    texts = [str(item.get("excerpt") or "").lower() for item in tail]
    tools = [tuple(item.get("tool_names") or ()) for item in tail]
    text = " ".join(texts)
    markers = {
        "tail_turns": len(tail),
        "tool_turns": sum(bool(names) for names in tools),
        "silent_tool_turns": sum(bool(names) and not text for names, text in zip(tools, texts)),
        "text_only_turns": sum(bool(text) and not names for names, text in zip(tools, texts)),
        "max_same_tool_run": max_same_tool_run(tools),
        "error_terms": sum(text.count(term) for term in ("error", "failed", "failure", "timeout")),
        "verify_terms": sum(text.count(term) for term in ("test", "verify", "check", "pass")),
        "delivery_terms": sum(text.count(term) for term in ("commit", "push", "deliver", "done")),
        "wait_terms": sum(text.count(term) for term in ("waiting", "blocked", "dependency", "user")),
        "compaction_event_count": cumulative.get("compaction_event_count"),
        "reread_path_count": len(cumulative.get("reread_paths") or []),
        "delta_new_read_paths": len((full.get("delta_since_prior") or {}).get("new_read_paths") or []),
    }
    classes = {"explore": 0, "edit": 0, "exec": 0, "orchestrate": 0, "user": 0, "other": 0}
    for names in tools:
        for name in names:
            low = str(name).lower()
            if any(word in low for word in ("read", "search", "list", "glob", "find")):
                classes["explore"] += 1
            elif any(word in low for word in ("edit", "write", "patch")):
                classes["edit"] += 1
            elif any(word in low for word in ("bash", "shell", "exec", "terminal")):
                classes["exec"] += 1
            elif any(word in low for word in ("agent", "task", "dispatch")):
                classes["orchestrate"] += 1
            elif "user" in low:
                classes["user"] += 1
            else:
                classes["other"] += 1
    phase_hints = {
        "tail_tool_class_counts": classes,
        "dominant_tail_class": max(classes, key=classes.get),
        "tail_has_edit": classes["edit"] > 0,
        "closing_language": any(word in text for word in ("commit", "push", "deliver", "done", "complete")),
        "heuristic": True,
    }
    recent = [
        {
            "turn": item.get("turn"),
            "tools": item.get("tool_names") or [],
            "text": str(item.get("excerpt") or "")[:160],
        }
        for item in tail[-4:]
    ]
    return {
        **full,
        "markers": full.get("markers") or markers,
        "phase_hints": full.get("phase_hints") or phase_hints,
        "recent": full.get("recent") or recent,
    }


def max_same_tool_run(tools: list[tuple[Any, ...]]) -> int:
    longest = current = 0
    previous: tuple[Any, ...] | None = None
    for names in tools:
        if names and names == previous:
            current += 1
        else:
            current = 1 if names else 0
        longest = max(longest, current)
        previous = names
    return longest


def load_packs() -> dict[str, dict[str, Any]]:
    packs: dict[str, dict[str, Any]] = {}
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


def select_representatives() -> list[dict[str, Any]]:
    packs = load_packs()
    selected = []
    for session_id, checkpoint in DIAGNOSTIC_REPRESENTATIVES:
        pack = packs.get(session_id)
        snap = next(
            (row for row in (pack or {}).get("checkpoints", [])
             if int(row.get("checkpoint", -1)) == checkpoint),
            None,
        )
        if not snap:
            continue
        full = derive_growth(snap.get("full_state") or {})
        if full is not None:
            selected.append({
                "session_id": session_id,
                "checkpoint": checkpoint,
                "full_state": full,
                "harness": pack.get("harness"),
                "project": pack.get("project"),
            })
    return selected


def project(full: dict[str, Any], state_variant: str) -> dict[str, Any]:
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
        "phase_hints": full.get("phase_hints") or {},
        "cumulative": {
            key: cumulative.get(key)
            for key in ("api_turns", "assistant_text_chars", "tool_histogram")
        },
    }


def build_cells(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells = []
    for state_variant in STATE_VARIANTS:
        for preferred_state, question_variant in PREFERRED_PAIRS:
            # The question remains attached to its preferred evidence shape.
            # The state flip intentionally tests the same question through the
            # alternate representation, so it is an adversarial contrast.
            for pair in pairs:
                for response_class in RESPONSE_CLASSES:
                    scenario = f"state.{state_variant}|q.{question_variant}"
                    raw = f"diagnostic-state-flip|{scenario}|{response_class}|{pair['session_id']}|{pair['checkpoint']}"
                    cells.append({
                        "cell_id": hashlib.sha256(raw.encode()).hexdigest()[:16],
                        "scenario_id": scenario,
                        "state_selection": state_variant,
                        "question_format": question_variant,
                        "response_class": response_class,
                        "session_id": pair["session_id"],
                        "checkpoint": pair["checkpoint"],
                        "checkpoint_role": "diagnostic_representative_mid",
                        "framing": "H1",
                        "question": QUESTIONS[question_variant],
                        "state": project(pair["full_state"], state_variant),
                        "harness": pair["harness"],
                        "project": pair["project"],
                    })
    return cells


def question_block(cell: dict[str, Any]) -> dict[str, Any]:
    if cell["response_class"] == "binary_fire":
        return {
            "fire_now": {
                "type": "choice",
                "instructions": cell["question"] + " Answer fire or defer from the snapshot only.",
                "criteria": {
                    "fire": "Fire now: steer-to-stop is indicated.",
                    "defer": "Defer: productive, recoverable, or insufficient evidence.",
                },
            },
            "steer_urgency": {
                "type": "score",
                "instructions": "Return steer urgency 0..3 from the snapshot only.",
                "criteria": ["0 defer/productive", "1 mild concern", "2 steer soon", "3 fire/runaway"],
            },
        }
    return {
        "decision_class": {
            "type": "choice",
            "instructions": cell["question"] + " Choose one class from the snapshot only.",
            "criteria": {
                "productive_continue": "Productive continuation is supported.",
                "near_completion": "Closing or validation value should be protected.",
                "likely_runaway": "Runaway or thrash indicates steering now.",
                "uncertain": "Evidence is insufficient to choose another class.",
            },
        }
    }


def parse_fire(cell: dict[str, Any], payload: dict[str, Any]) -> tuple[Any, bool | None]:
    answers = payload.get("answers") or {}
    if cell["response_class"] == "binary_fire":
        choice = (answers.get("fire_now") or {}).get("choice")
        return choice, choice == "fire"
    choice = (answers.get("decision_class") or {}).get("choice")
    return choice, choice == "likely_runaway"


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
        decision, fire = parse_fire(cell, payload)
        return {
            **{k: cell[k] for k in (
                "cell_id", "scenario_id", "state_selection", "question_format",
                "response_class", "session_id", "checkpoint", "checkpoint_role",
                "framing", "harness", "project",
            )},
            "decision": decision,
            "fire": fire,
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
            **{k: cell[k] for k in ("cell_id", "scenario_id", "response_class", "session_id", "checkpoint")},
            "http": error.code,
            "error": detail[:500],
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }
    except Exception as error:
        return {
            **{k: cell[k] for k in ("cell_id", "scenario_id", "response_class", "session_id", "checkpoint")},
            "http": None,
            "error": f"{type(error).__name__}: {error}",
            "soft_standard_hold": True,
            "product_wiring": False,
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }


def write_plan(cells: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> None:
    (OUT / "cells_plan.json").write_text(json.dumps({
        "wave": "typesafe-diagnostic-state-flip",
        "scope": "diagnostic",
        "join_class": "diagnostic_only",
        "catalog_scope": "12 preferred GROWTH pairs from #109 × 7 #114 diagnostic representatives",
        "n_distinct_scenarios": 24,
        "n_representative_pairs": len(pairs),
        "n_state_variants": len(STATE_VARIANTS),
        "n_response_classes": len(RESPONSE_CLASSES),
        "n_cells_planned": len(cells),
        "state_variants": list(STATE_VARIANTS),
        "response_classes": list(RESPONSE_CLASSES),
        "label_values_in_prompt": False,
        "window_cartesian": False,
        "soft_standard_hold": True,
        "product_wiring": False,
        "raw_capture_dir": "raw/",
    }, indent=2) + "\n")


def write_meters(rows: list[dict[str, Any]], cells: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> None:
    successful = [row for row in rows if row.get("http") == 200 and not row.get("error")]
    by_axis = {}
    for state in STATE_VARIANTS:
        for rc in RESPONSE_CLASSES:
            group = [row for row in successful if row.get("state_selection") == state and row.get("response_class") == rc]
            by_axis[f"{state}|{rc}"] = {
                "n": len(group),
                "fire_count": sum(bool(row.get("fire")) for row in group),
                "fire_rate": round(sum(bool(row.get("fire")) for row in group) / len(group), 4) if group else None,
            }
    cell_ids = [cell["cell_id"] for cell in cells]
    meters = {
        "status": "complete" if len(successful) == len(cells) else "partial",
        "scope": "diagnostic_only",
        "join_class": "diagnostic_only",
        "n_distinct_scenarios": 24,
        "n_representative_pairs": len(pairs),
        "n_cells_planned": len(cells),
        "n_cells_successful": len(successful),
        "n_cells_errors": len(rows) - len(successful),
        "http_counts": dict(Counter(str(row.get("http")) for row in rows)),
        "cell_id_collisions": len(cell_ids) - len(set(cell_ids)),
        "by_state_response_class": by_axis,
        "leak_spotcheck_hits": 0,
        "label_values_in_prompt": False,
        "window_cartesian": False,
        "soft_standard_hold": True,
        "product_wiring": False,
        "generated_at": datetime.now(AEST).isoformat(timespec="seconds"),
    }
    (OUT / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    (OUT / "METERS.md").write_text(
        "\n".join([
            "# METERS — TypeSafe diagnostic state flip",
            "",
            "**Soft Standard HOLD** — diagnostic evidence only; no hooks, behavior, unlock, or FP/miss scoreboard.",
            "",
            "This extends the non-label-ready 12×7 response-calibration stratum from #114.",
            "It compares `markers_focus` with `phase_hints_focus` across the same",
            "twelve preferred pairs and seven diagnostic representative joins.",
            "",
            f"- status: **{meters['status']}**",
            f"- representative pairs: **{len(pairs)}**",
            f"- planned cells: **{len(cells)}**",
            f"- successful cells: **{len(successful)}**",
            f"- HTTP/error rows: `{json.dumps(meters['http_counts'], sort_keys=True)}`",
            f"- cell-id collisions: **{meters['cell_id_collisions']}**",
            "",
            "| state × response class | n | fire | fire rate |",
            "|---|---:|---:|---:|",
            *[
                f"| `{axis}` | {value['n']} | {value['fire_count']} | {value['fire_rate']} |"
                for axis, value in by_axis.items()
            ],
            "",
            "These are response distributions only. The seven representatives are",
            "not label-ready, and no label value entered a request.",
        ]) + "\n"
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    pairs = select_representatives()
    cells = build_cells(pairs)
    write_plan(cells, pairs)
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
    write_meters(rows, cells, pairs)
    print(json.dumps({
        "planned": len(cells),
        "rows": len(rows),
        "successful": sum(row.get("http") == 200 and not row.get("error") for row in rows),
        "errors": sum(bool(row.get("error")) for row in rows),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
