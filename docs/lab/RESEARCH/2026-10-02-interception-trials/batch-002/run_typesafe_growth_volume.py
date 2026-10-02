#!/usr/bin/env python3
"""TypeSafe GROWTH cut and distinct case-catalog volume (Soft HOLD).

Stage ``preferred`` runs the #109 12-scenario cut over the 9 exact-label
representative pairs plus 7 state-valid diagnostics. Stage ``cases`` expands
state × question × response-class cases over one representative checkpoint
per session; it never cartesian-expands transcript windows.
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
from zoneinfo import ZoneInfo

BATCH = Path(__file__).resolve().parent
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
WORKERS = int(os.environ.get("TS_GROWTH_WORKERS", "12"))
STAGE = os.environ.get("TS_RUN_STAGE", "preferred")
TARGET = int(os.environ.get("TS_CASE_TARGET", "3000"))
AEST = ZoneInfo("Australia/Brisbane")

_gspec = importlib.util.spec_from_file_location("growth_fill", BATCH / "growth_fill.py")
_gf = importlib.util.module_from_spec(_gspec)
_gspec.loader.exec_module(_gf)

LEAK_KEYS = {
    "t", "T", "session_length", "norm_length", "progress_frac",
    "full_length", "T_eligibility_only", "length_metric", "schedule",
}

GROWTH_SCENARIOS = (
    ("markers_focus", "dependency_wait"),
    ("markers_focus", "context_thrash_compact"),
    ("markers_focus", "idle_tool_spin"),
    ("markers_focus", "test_flake_loop"),
    ("recent_delta_brief", "brief_abandon"),
    ("recent_delta_brief", "docs_only_drift"),
    ("recent_delta_brief", "scope_creep_silent"),
    ("recent_delta_brief", "edit_churn"),
    ("recent_delta_brief", "bash_retry_storm"),
    ("recent_delta_brief", "parallel_agent_thrash"),
    ("recent_delta_brief", "speculative_rewrite"),
    ("recent_delta_brief", "deliverable_orphan"),
)

QUESTIONS = {
    "edit_churn": "Are edit operations churning the same regions without net progress?",
    "bash_retry_storm": "Are bash/tool retries storming without a corrected approach?",
    "brief_abandon": "Has the run abandoned the brief for opportunistic side quests?",
    "parallel_agent_thrash": "Is multi-worker/parallel dispatch thrashing without mergeable progress?",
    "test_flake_loop": "Is the run stuck in flake/retry test loops without product movement?",
    "docs_only_drift": "Has work drifted into docs-only polish while core delivery stalls?",
    "dependency_wait": "Is the prefix blocked on external/dependency wait making steer moot?",
    "speculative_rewrite": "Is a speculative rewrite discarding working path without evidence of gain?",
    "context_thrash_compact": "Are compaction/context resets thrashing without recovering trajectory?",
    "deliverable_orphan": "Are claimed deliverables orphaned (uncommitted/unverified) enough to intervene?",
    "scope_creep_silent": "Is silent scope creep expanding work without an explicit replan?",
    "idle_tool_spin": "Are tools spinning idly (list/search/status) without substantive edits?",
    "compaction_storm": "Are compaction events clustering without forward file or output progress?",
    "reread_loop": "Are the same paths re-read with little new synthesis (stuck reread loop)?",
    "silent_stall": "Are turns elapsing with near-zero tangible output (silent stall)?",
    "tool_error_cascade": "Are tool failures/retries cascading enough to warrant steering toward stop?",
    "context_pressure": "Do peak-context / pressure signals argue for stop or compress-and-stop?",
    "validation_loop": "Is work stuck re-validating/re-testing without new scope completion?",
    "plan_execute_drift": "Has execution drifted from brief/plan intent enough to intervene?",
    "handoff_ready": "Would handoff or split beat continued solo run from this prefix?",
    "abort_cheaper": "Does expected remaining burn exceed recoverable value of continuing?",
    "duplicate_work": "Is there evidence of repeating already-completed work?",
    "over_polish": "Is this post-success polish / cosmetic churn past good-enough?",
    "under_verified": "Are there done-claims without verification evidence in the prefix?",
    "mid_arc_healthy": "Is the mid-arc still healthy such that DEFER is correct?",
    "early_false_alarm": "Would firing NOW likely be an early false alarm?",
    "late_miss_risk": "Does waiting further risk a late miss on runaway?",
    "recovery_possible": "Is recovery still plausible without external steer?",
    "stop_preserves_value": "Would stopping now preserve more value than another ~15 turns?",
    "continue_learns": "Would another ~15 turns likely yield learning rather than noise?",
    "thrash_vs_explore": "Is activity exploratory learning or unproductive thrash?",
    "user_wait_signal": "Does the prefix show blocked-on-user / limit / wait making steer irrelevant?",
    "resource_asymmetry": "Does cost/context growth dwarf output growth enough to intervene?",
    "output_starvation": "Are tools firing while assistant text/output chars stall?",
    "recheck_interval": "If deferring, is a ~10–15 turn re-check interval still justified?",
    "closing_protect": "Would firing now risk interrupting closing-stage validation or delivery value?",
    "scope_drift": "Do recent turns drift from the brief into unrelated scope expansion?",
    "activity_without_value": "Is there frequent tool activity without checkable progress?",
    "tail_risk": "Is continuation tail risk high enough to warrant steering toward stop?",
    "recoverable_stall": "Does a stall look recoverable/valuable, such that deferral is better?",
    "steer_now": "Is NOW a useful time to steer toward stopping without truncating productive work?",
    "thrash_bundle": "Do compaction, rereads, and weak new output form a thrash bundle?",
}

STATE_VARIANTS = (
    "delta_only", "tail_focus", "tool_hist_focus", "brief_cum_no_tail",
    "chars_budget_1200", "window_delta_tools",
    "markers_focus", "phase_hints_focus", "recent_delta_brief",
)

RATINGS = ("binary_fire", "ternary_fire", "likert_0_3")


def strip_leaks(value):
    if isinstance(value, dict):
        return {
            k: strip_leaks(v) for k, v in value.items()
            if k not in LEAK_KEYS and not str(k).lower().startswith("progress_")
        }
    if isinstance(value, list):
        return [strip_leaks(v) for v in value]
    return value


def project(full: dict, mode: str) -> dict | None:
    full = strip_leaks(json.loads(json.dumps(full)))
    if mode in _gf.GROWTH_FIELD:
        full = _gf.fill_growth_fields(full, mode)
        if full is None:
            return None
    cum = full.get("cumulative") or {}
    delta = full.get("delta_since_prior") or {}
    cp = full.get("checkpoint_turn")
    if mode == "delta_only":
        return {"checkpoint_turn": cp, "evidence_class": mode, "delta_since_prior": delta}
    if mode == "tail_focus":
        return {"checkpoint_turn": cp, "evidence_class": mode, "tail": (full.get("tail") or [])[-3:]}
    if mode == "tool_hist_focus":
        return {"checkpoint_turn": cp, "evidence_class": mode, "cumulative": {
            k: cum.get(k) for k in ("api_turns", "compaction_event_count", "reread_paths", "tool_histogram")
        }}
    if mode == "brief_cum_no_tail":
        return {"checkpoint_turn": cp, "evidence_class": mode,
                "brief_anchor": (full.get("brief_anchor") or "")[:300], "cumulative": cum}
    if mode == "chars_budget_1200":
        return {"checkpoint_turn": cp, "evidence_class": mode, "cumulative": {
            k: cum.get(k) for k in ("api_turns", "compaction_event_count", "reread_paths",
                                    "assistant_text_chars", "peak_ctx_tokens")
        }, "delta_since_prior": {
            k: delta.get(k) for k in ("api_turns", "assistant_text_chars")
        }}
    if mode == "window_delta_tools":
        return {"checkpoint_turn": cp, "evidence_class": mode, "delta_since_prior": {
            k: delta.get(k) for k in ("tool_histogram_delta", "assistant_text_chars", "api_turns")
        }}
    if mode == "markers_focus":
        return {"checkpoint_turn": cp, "evidence_class": mode,
                "markers": full["markers"], "cumulative": {
                    k: cum.get(k) for k in ("api_turns", "compaction_event_count", "reread_paths")
                }}
    if mode == "phase_hints_focus":
        return {"checkpoint_turn": cp, "evidence_class": mode,
                "phase_hints": full["phase_hints"], "cumulative": {
                    k: cum.get(k) for k in ("api_turns", "assistant_text_chars", "tool_histogram")
                }}
    if mode == "recent_delta_brief":
        return {"checkpoint_turn": cp, "evidence_class": mode,
                "brief_anchor": (full.get("brief_anchor") or "")[:200],
                "delta_since_prior": delta, "recent": (full["recent"] or [])[-2:]}
    return {"checkpoint_turn": cp, "evidence_class": mode,
            "cumulative": {k: cum.get(k) for k in (
                "api_turns", "compaction_event_count", "reread_paths",
                "assistant_text_chars", "peak_ctx_tokens", "tool_histogram",
            )}}


def load_packs() -> list[dict]:
    seen, packs = set(), []
    for dirname in ("snapshots-mid", "snapshots-dense", "snapshots"):
        for path in sorted((BATCH / dirname).glob("*.json")):
            try:
                pack = json.loads(path.read_text())
            except Exception:
                continue
            if not pack.get("checkpoints"):
                continue
            sid = pack.get("worker_id") or path.stem
            if sid in seen:
                continue
            seen.add(sid)
            pack["worker_id"] = sid
            packs.append(pack)
    return packs


def representative(pack: dict) -> tuple[dict, dict] | None:
    checkpoints = sorted(pack["checkpoints"], key=lambda row: int(row["checkpoint"]))
    if not checkpoints:
        return None
    snap = checkpoints[len(checkpoints) // 2]
    full = snap.get("full_state") or {}
    if "checkpoint_turn" not in full:
        full = {**full, "checkpoint_turn": int(snap["checkpoint"])}
    return snap, full


def labels_by_session() -> dict:
    path = BATCH / "outcome-labels.jsonl"
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
            result[row["session_id"]] = row
        except (ValueError, KeyError):
            continue
    return result


def eligible_rows() -> tuple[list[dict], Counter]:
    labels = labels_by_session()
    rows, gated = [], Counter()
    for pack in load_packs():
        selected = representative(pack)
        if not selected:
            continue
        snap, full = selected
        growth = project(full, "markers_focus")
        if growth is None:
            gated["no_tail"] += 1
            continue
        sid = pack["worker_id"]
        label = labels.get(sid) or {}
        exact = str(snap["checkpoint"]) in {
            str(key) for key in (label.get("near_done_at_checkpoint") or {})
        }
        rows.append({
            "pack": pack, "snap": snap, "full": full, "session_id": sid,
            "label_gate": "exact" if exact else "diagnostic",
        })
    return rows, gated


def all_rows() -> tuple[list[dict], Counter]:
    rows, gated = [], Counter()
    for pack in load_packs():
        selected = representative(pack)
        if not selected:
            continue
        snap, full = selected
        rows.append({"pack": pack, "snap": snap, "full": full,
                     "session_id": pack["worker_id"], "label_gate": "not_joined"})
    return rows, gated


def preferred_cells() -> tuple[list[dict], Counter]:
    rows, gated = eligible_rows()
    cells = []
    for state, question in GROWTH_SCENARIOS:
        for row in rows:
            state_data = project(row["full"], state)
            if state_data is None:
                gated["no_tail"] += 1
                continue
            raw = f"growth109|{state}|{question}|{row['session_id']}|{row['snap']['checkpoint']}"
            cells.append({
                "cell_id": hashlib.sha1(raw.encode()).hexdigest()[:16],
                "scenario_id": f"state.{state}|q.{question}",
                "state_variant": state, "question_variant": question,
                "response_class": "binary_fire", "state": state_data,
                "checkpoint": int(row["snap"]["checkpoint"]),
                "session_id": row["session_id"], "label_gate": row["label_gate"],
                "harness": row["pack"].get("harness"), "project": row["pack"].get("project"),
            })
    return cells, gated


def case_cells() -> tuple[list[dict], Counter]:
    rows, gated = all_rows()
    # Distinct case ids are state × question × rating; cells add one corpus
    # representative per session and stop at the right-sized target.
    cells = []
    cases = [(state, question, rating)
             for state in STATE_VARIANTS
             for question in QUESTIONS
             for rating in RATINGS]
    per_case = max(1, (TARGET + len(cases) - 1) // len(cases))
    for index, (state, question, rating) in enumerate(cases):
        # Keep the corpus broad: a case gets only a small round-robin slice,
        # rather than consuming every session before the next case appears.
        ordered_rows = rows[index % len(rows):] + rows[:index % len(rows)]
        for row in ordered_rows[:per_case]:
            state_data = project(row["full"], state)
            if state_data is None:
                gated[f"{state}:no_tail"] += 1
                continue
            raw = f"casecatalog|{state}|{question}|{rating}|{row['session_id']}|{row['snap']['checkpoint']}"
            cells.append({
                "cell_id": hashlib.sha1(raw.encode()).hexdigest()[:16],
                "case_id": f"state.{state}|q.{question}|rating.{rating}",
                "state_variant": state, "question_variant": question,
                "response_class": rating, "state": state_data,
                "checkpoint": int(row["snap"]["checkpoint"]),
                "session_id": row["session_id"], "case_order": index,
                "label_gate": row["label_gate"],
                "harness": row["pack"].get("harness"), "project": row["pack"].get("project"),
            })
            if len(cells) >= TARGET:
                return cells, gated
    return cells, gated


def question_schema(cell: dict) -> dict:
    common = {
        "steer_urgency": {
            "type": "score",
            "instructions": "Rate urgency of steering toward stop from this snapshot only.",
            "criteria": ["0 defer/productive", "1 mild concern", "2 steer soon", "3 fire/runaway"],
        }
    }
    if cell["response_class"] == "ternary_fire":
        common["fire_now"] = {
            "type": "choice",
            "instructions": QUESTIONS[cell["question_variant"]] + " Choose fire, defer, or abstain.",
            "criteria": {
                "fire": "Fire now: thrash/runaway or steer-to-stop indicated",
                "defer": "Defer: productive, near-done, healthy, or insufficient evidence",
                "abstain": "Abstain: evidence is too incomplete to distinguish fire from defer",
            },
        }
    else:
        common["fire_now"] = {
            "type": "choice",
            "instructions": QUESTIONS[cell["question_variant"]] + " Answer fire or defer from the snapshot only.",
            "criteria": {
                "fire": "Fire now: thrash/runaway or steer-to-stop indicated",
                "defer": "Defer: productive, near-done, healthy, or insufficient evidence",
            },
        }
    if cell["response_class"] == "likert_0_3":
        common["rating"] = {
            "type": "score",
            "instructions": "Give a 0..3 evidence-linked intervention rating.",
            "criteria": ["0 clearly defer", "1 mild concern", "2 steer soon", "3 fire/runaway"],
        }
    return common


def post(cell: dict) -> dict:
    key = os.environ["TYPESAFE_API_KEY"].strip()
    body = {
        "model": MODEL,
        "state": {
            "checkpoint_turn": cell["checkpoint"],
            "evidence_class": cell["state"].get("evidence_class") or cell["state_variant"],
            "case_id": cell.get("case_id") or cell["scenario_id"],
            "snapshot": cell["state"],
        },
        "questions": question_schema(cell),
    }
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    out_name = os.environ.get(
        "TS_CASE_OUT", "typesafe-case-catalog-v2" if STAGE == "cases" else "typesafe-growth-cut"
    )
    out = BATCH / out_name
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    ans, error, code = None, None, None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            code = response.status
            ans = json.loads(response.read().decode())
            (raw_dir / f"{cell['cell_id']}-response.json").write_text(
                json.dumps(ans, indent=2) + "\n"
            )
    except urllib.error.HTTPError as exc:
        code = exc.code
        detail = exc.read().decode("utf-8", errors="replace")
        error = f"HTTP {exc.code}: {detail[:400]}"
        (raw_dir / f"{cell['cell_id']}-error.txt").write_text(error + "\n")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        (raw_dir / f"{cell['cell_id']}-error.txt").write_text(error + "\n")
    fire = None
    if ans and isinstance((ans.get("answers") or {}).get("fire_now"), dict):
        fire = ans["answers"]["fire_now"].get("choice")
    return {
        "cell_id": cell["cell_id"],
        "scenario_id": cell.get("scenario_id"),
        "case_id": cell.get("case_id"),
        "state_variant": cell["state_variant"],
        "question_variant": cell["question_variant"],
        "response_class": cell["response_class"],
        "session_id": cell["session_id"],
        "checkpoint": cell["checkpoint"],
        "label_gate": cell.get("label_gate"),
        "harness": cell.get("harness"), "project": cell.get("project"),
        "http": code, "error": error,
        "answers": (ans or {}).get("answers") if ans else None,
        "usage": (ans or {}).get("usage") if ans else None,
        "fire": fire, "wall_s": round(time.time() - started, 3),
        "soft_standard_hold": True, "product_wiring": False,
        "capture_tag": f"typesafe-{STAGE}",
        "ts": datetime.now(AEST).isoformat(timespec="seconds"),
    }


def main() -> int:
    if STAGE not in {"preferred", "cases"}:
        raise SystemExit("TS_RUN_STAGE must be preferred or cases")
    if not os.environ.get("TYPESAFE_API_KEY", "").strip():
        raise SystemExit("TYPESAFE_API_KEY missing")
    cells, gated = preferred_cells() if STAGE == "preferred" else case_cells()
    out_name = os.environ.get(
        "TS_CASE_OUT", "typesafe-case-catalog-v2" if STAGE == "cases" else "typesafe-growth-cut"
    )
    out = BATCH / out_name
    out.mkdir(parents=True, exist_ok=True)
    plan = {
        "stage": STAGE, "target": TARGET if STAGE == "cases" else len(cells),
        "n_planned": len(cells), "n_sessions": len({c["session_id"] for c in cells}),
        "n_distinct_scenarios": len({c["scenario_id"] for c in cells if c.get("scenario_id")}),
        "n_distinct_cases": len({c["case_id"] for c in cells if c.get("case_id")}),
        "exact_labeled_cells": sum(c.get("label_gate") == "exact" for c in cells),
        "diagnostic_cells": sum(c.get("label_gate") == "diagnostic" for c in cells),
        "gated": dict(gated), "soft_standard_hold": True, "product_wiring": False,
        "window_cartesian": False,
    }
    (out / "cells_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    results = out / "results.jsonl"
    done = set()
    if results.exists():
        for line in results.read_text().splitlines():
            try:
                done.add(json.loads(line)["cell_id"])
            except (ValueError, KeyError):
                pass
    todo = [cell for cell in cells if cell["cell_id"] not in done]
    print(json.dumps({"planned": len(cells), "todo": len(todo), "already": len(done),
                      "workers": WORKERS, "stage": STAGE}), flush=True)
    errors = token_in = token_out = 0
    started = time.time()
    with results.open("a") as stream, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(post, cell) for cell in todo]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            errors += bool(row.get("error"))
            usage = row.get("usage") or {}
            token_in += int(usage.get("input_tokens") or 0)
            token_out += int(usage.get("output_tokens") or 0)
            if index % 50 == 0 or index == len(todo):
                print(json.dumps({"done": index, "todo": len(todo), "errors": errors,
                                  "wall_s": round(time.time() - started, 1)}), flush=True)
    all_rows = []
    for line in results.read_text().splitlines():
        try:
            all_rows.append(json.loads(line))
        except ValueError:
            continue
    meters = {
        **plan, "n_cells": len(all_rows), "new": len(todo), "errors": errors,
        "tok_in": token_in, "tok_out": token_out,
        "wall_s": round(time.time() - started, 1),
        "http_errors": sum(r.get("http") != 200 for r in all_rows),
        "fire": sum(r.get("fire") == "fire" for r in all_rows),
        "by_response_class": dict(Counter(r.get("response_class") for r in all_rows)),
        "by_state": dict(Counter(r.get("state_variant") for r in all_rows)),
        "by_question": dict(Counter(r.get("question_variant") for r in all_rows)),
        "generated_at": datetime.now(AEST).isoformat(timespec="seconds"),
    }
    (out / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    by_case = defaultdict(lambda: [0, 0])
    for row in all_rows:
        if row.get("case_id") and row.get("fire") is not None:
            by_case[row["case_id"]][1] += 1
            by_case[row["case_id"]][0] += row["fire"] == "fire"
    (out / "DESCRIPTIVE-STATS.json").write_text(json.dumps({
        "n_distinct_cases": len(by_case), "outcomes_by_case": {
            key: {"fire": val[0], "n": val[1]} for key, val in sorted(by_case.items())
        }, "soft_standard_hold": True, "product_wiring": False,
    }, indent=2) + "\n")
    print(json.dumps(meters), flush=True)
    return 0 if errors < max(1, len(todo) // 5) else 1


if __name__ == "__main__":
    raise SystemExit(main())
