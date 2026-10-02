#!/usr/bin/env python3
"""Soft HOLD Flash replication of preferred GROWTH cut (#109/#111).

Preferred cut only: 12 scenarios × 9 exact-labeled sessions = 108 cells.
- growth-fill-v1 non-empty state (tail-less harnesses gated)
- empty state = unsupported, never sent as negative evidence
- Soft Standard HOLD — no hooks / product wiring / :8080
- Driver: opencode deepseek/deepseek-flash (policy-under-test)

Outputs: batch-002/flash-growth-preferred/
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path(os.environ.get("WF_REPO", "/tmp/wf-soft-hold-flash-preferred-108"))
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
SNAP_DIRS = [BATCH / "snapshots-mid", BATCH / "snapshots-dense", BATCH / "snapshots"]
OUT = BATCH / "flash-growth-preferred"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "raw").mkdir(exist_ok=True)
AEST = ZoneInfo("Australia/Brisbane")

FLASH_MODEL = "deepseek/deepseek-flash"
OPENCODE = os.environ.get("OPENCODE_BIN", "/home/codyh/.opencode/bin/opencode")
CELLS_PER_FLASH = int(os.environ.get("FLASH_CELLS_PER_BATCH", "6"))
MAX_PAR_FLASH = int(os.environ.get("FLASH_MAX_PAR", "2"))
INCLUDE_DIAG = os.environ.get("FLASH_INCLUDE_DIAG", "").strip() in {"1", "true", "yes"}
FRAMING = "H1"
FRAMING_TEXT = (
    "Framing H1 progressive re-check: decide fire-now vs defer-and-recheck. "
    "Preserve productive development and near-done closing; catch runaway thrash. "
    "Soft Standard HOLD — policy-under-test only."
)
FILL_VERSION = "growth-fill-v1"

# Prefer PATH that includes opencode without printing env secrets
_opath = Path(OPENCODE).parent
if _opath.is_dir():
    os.environ["PATH"] = f"{_opath}:{os.environ.get('PATH', '')}"

sys.path.insert(0, str(BATCH))
import growth_fill as _gf  # noqa: E402

Q_GROWTH = {
    "edit_churn": "Are edit operations churning the same regions without net progress? Snapshot only.",
    "bash_retry_storm": "Are bash/tool retries storming without a corrected approach? Snapshot only.",
    "brief_abandon": "Has the run abandoned the brief for opportunistic side quests? Snapshot only.",
    "parallel_agent_thrash": "Is multi-worker/parallel dispatch thrashing without mergeable progress? Snapshot only.",
    "test_flake_loop": "Is the run stuck in flake/retry test loops without product movement? Snapshot only.",
    "docs_only_drift": "Has work drifted into docs-only polish while core delivery stalls? Snapshot only.",
    "dependency_wait": "Is the prefix blocked on external/dependency wait making steer moot? Snapshot only.",
    "speculative_rewrite": "Is a speculative rewrite discarding working path without evidence of gain? Snapshot only.",
    "context_thrash_compact": "Are compaction/context resets thrashing without recovering trajectory? Snapshot only.",
    "deliverable_orphan": "Are claimed deliverables orphaned (uncommitted/unverified) enough to intervene? Snapshot only.",
    "scope_creep_silent": "Is silent scope creep expanding work without an explicit replan? Snapshot only.",
    "idle_tool_spin": "Are tools spinning idly (list/search/status) without substantive edits? Snapshot only.",
}
LEAK = {
    "t",
    "T",
    "session_length",
    "norm_length",
    "progress_frac",
    "full_length",
    "T_eligibility_only",
    "length_metric",
}
BINARY_SPEC = {
    "map": {"fire": True, "defer": False},
    "labels": ["fire", "defer"],
}


def now_aest() -> str:
    return datetime.now(AEST).isoformat(timespec="seconds")


def strip_leaks(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: strip_leaks(v)
            for k, v in obj.items()
            if k not in LEAK and not str(k).lower().startswith("progress_")
        }
    if isinstance(obj, list):
        return [strip_leaks(x) for x in obj]
    return obj


def load_preferred_pairs() -> list[tuple[str, str]]:
    ranking = json.loads((BATCH / "GROWTH-RANKING.json").read_text())
    pairs = []
    for row in ranking["priority_pairs"]:
        sid = row["scenario_id"]  # state.X|q.Y
        state_part, q_part = sid.split("|", 1)
        state_v = state_part.removeprefix("state.")
        qk = q_part.removeprefix("q.")
        if state_v not in _gf.GROWTH_FIELD:
            raise SystemExit(f"non-growth preferred state: {state_v}")
        if qk not in Q_GROWTH:
            raise SystemExit(f"unknown preferred question: {qk}")
        pairs.append((state_v, qk))
    if len(pairs) != 12:
        raise SystemExit(f"expected 12 preferred pairs, got {len(pairs)}")
    return pairs


def load_packs() -> list[dict[str, Any]]:
    seen: set[str] = set()
    packs: list[dict[str, Any]] = []
    for d in SNAP_DIRS:
        if not d.is_dir():
            continue
        for sp in sorted(d.glob("*.json")):
            try:
                pack = json.loads(sp.read_text())
            except Exception:
                continue
            if not pack.get("checkpoints"):
                continue
            wid = pack.get("worker_id") or sp.stem
            if wid in seen:
                continue
            seen.add(wid)
            pack["worker_id"] = wid
            packs.append(pack)
    return packs


def pick_rep_snap(pack: dict[str, Any]) -> dict[str, Any] | None:
    cps = sorted(pack["checkpoints"], key=lambda s: int(s["checkpoint"]))
    if not cps:
        return None
    return cps[len(cps) // 2]


def project(full: dict[str, Any], mode: str) -> dict[str, Any] | None:
    full = strip_leaks(json.loads(json.dumps(full)))
    full = _gf.fill_growth_fields(full, mode)
    if full is None:
        return None
    cum = full.get("cumulative") or {}
    delta = full.get("delta_since_prior") or {}
    cp = full.get("checkpoint_turn")
    if mode == "markers_focus":
        return {
            "checkpoint_turn": cp,
            "evidence_class": "markers_focus",
            "markers": full.get("markers") or {},
            "cumulative": {
                k: cum.get(k)
                for k in ("api_turns", "compaction_event_count", "reread_paths")
            },
        }
    if mode == "recent_delta_brief":
        return {
            "checkpoint_turn": cp,
            "evidence_class": "recent_delta_brief",
            "brief_anchor": (full.get("brief_anchor") or "")[:200],
            "delta_since_prior": delta,
            "recent": (full.get("recent") or [])[-2:],
        }
    if mode == "phase_hints_focus":
        return {
            "checkpoint_turn": cp,
            "evidence_class": "phase_hints_focus",
            "phase_hints": full.get("phase_hints") or {},
            "cumulative": {
                k: cum.get(k)
                for k in ("api_turns", "assistant_text_chars", "tool_histogram")
            },
        }
    raise ValueError(mode)


def load_labels() -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    path = BATCH / "outcome-labels.jsonl"
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        labels[row["session_id"]] = row
    return labels


def join_eligibility(labels: dict[str, dict[str, Any]], session_id: str, checkpoint: int) -> str:
    label = labels.get(session_id)
    if label is None:
        return "session_unlabeled"
    status = label.get("label_status")
    if status == "excluded":
        return "label_excluded"
    if status != "labeled":
        return "session_not_labeled"
    key = str(checkpoint)
    near = (label.get("near_done_at_checkpoint") or {}).get(key)
    runaway = (label.get("runaway_like_at_checkpoint") or {}).get(key)
    if near is None or runaway is None:
        return "checkpoint_unlabeled"
    return "label_join_exact"


def state_nonempty(state: dict[str, Any], mode: str) -> bool:
    field = _gf.GROWTH_FIELD[mode]
    val = state.get(field)
    if val is None:
        return False
    if isinstance(val, dict):
        return any(v not in (None, "", [], {}) for v in val.values())
    if isinstance(val, list):
        return len(val) > 0
    return bool(val)


def build_cells() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pairs = load_preferred_pairs()
    packs = load_packs()
    labels = load_labels()
    packs = sorted(
        packs, key=lambda p: (0 if p.get("harness") == "claude-code" else 1, p["worker_id"])
    )

    # First pass: classify sessions at representative checkpoint for growth eligibility
    session_meta: list[dict[str, Any]] = []
    gated_no_tail = 0
    for pack in packs:
        snap = pick_rep_snap(pack)
        if not snap:
            continue
        full = snap.get("full_state") or {}
        if not isinstance(full, dict) or not full:
            continue
        cp = int(snap["checkpoint"])
        if "checkpoint_turn" not in full:
            full = {**full, "checkpoint_turn": cp}
        # eligibility uses any growth mode that requires tail
        probe = _gf.derive_growth_fields(strip_leaks(json.loads(json.dumps(full))))
        sid = pack["worker_id"]
        if probe is None:
            gated_no_tail += 1
            session_meta.append(
                {
                    "session_id": sid,
                    "checkpoint": cp,
                    "eligible": False,
                    "gate": "no_tail",
                    "harness": pack.get("harness"),
                    "join": join_eligibility(labels, sid, cp),
                }
            )
            continue
        join = join_eligibility(labels, sid, cp)
        session_meta.append(
            {
                "session_id": sid,
                "checkpoint": cp,
                "eligible": True,
                "gate": None,
                "harness": pack.get("harness"),
                "join": join,
                "pack": pack,
                "full": full,
            }
        )

    exact = [s for s in session_meta if s["eligible"] and s["join"] == "label_join_exact"]
    diag = [
        s
        for s in session_meta
        if s["eligible"] and s["join"] in {"checkpoint_unlabeled", "session_unlabeled"}
    ]
    exact = sorted(exact, key=lambda s: s["session_id"])
    diag = sorted(diag, key=lambda s: s["session_id"])
    if len(exact) != 9:
        # Soft FAIL soft: still proceed with whatever exact set we found, but record
        pass

    selected = list(exact)
    cell_tier = "exact_labeled"
    if INCLUDE_DIAG:
        selected = exact + diag
        cell_tier = "exact_plus_diag"

    cells: list[dict[str, Any]] = []
    for state_v, qk in pairs:
        qtext = Q_GROWTH[qk]
        for sess in selected:
            state = project(sess["full"], state_v)
            if state is None or not state_nonempty(state, state_v):
                # empty = unsupported — skip, do not send
                continue
            sid = sess["session_id"]
            cp = sess["checkpoint"]
            scenario_id = f"state.{state_v}|q.{qk}"
            raw = (
                f"flash-growth-preferred|{scenario_id}|{sid}|rep{cp}|"
                f"{FRAMING}|binary_fire|{FILL_VERSION}"
            )
            cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
            cells.append(
                {
                    "cell_id": cid,
                    "scenario_id": scenario_id,
                    "state_selection": state_v,
                    "state_variant": state_v,
                    "question_format": qk,
                    "question_variant": qk,
                    "question_text": qtext,
                    "session_id": sid,
                    "checkpoint": cp,
                    "checkpoint_role": "session_representative_mid",
                    "framing": FRAMING,
                    "framing_text": FRAMING_TEXT,
                    "response_class": "binary_fire",
                    "response_class_spec": BINARY_SPEC,
                    "state": state,
                    "state_fill": FILL_VERSION,
                    "harness": sess.get("harness"),
                    "project": (sess.get("pack") or {}).get("project"),
                    "label_join_eligibility": sess["join"],
                    "cell_tier": "exact_labeled"
                    if sess["join"] == "label_join_exact"
                    else "diagnostic",
                }
            )

    plan = {
        "generated_at": now_aest(),
        "soft_standard_hold": True,
        "product_wiring": False,
        "hooks_unlock": False,
        "driver": "flash",
        "model": FLASH_MODEL,
        "preferred_pairs": [f"state.{a}|q.{b}" for a, b in pairs],
        "n_preferred_scenarios": len(pairs),
        "n_exact_labeled_sessions": len(exact),
        "n_diagnostic_sessions": len(diag),
        "exact_session_ids": [s["session_id"] for s in exact],
        "diagnostic_session_ids": [s["session_id"] for s in diag],
        "include_diagnostic": INCLUDE_DIAG,
        "n_cells_planned": len(cells),
        "cell_tier": cell_tier,
        "growth_fill_version": FILL_VERSION,
        "gated_no_tail_sessions": gated_no_tail,
        "checkpoint_policy": "one_representative_mid_per_session",
        "window_cartesian": False,
        "empty_state_policy": "unsupported_not_negative",
        "tail_less_policy": "gated",
        "session_meta_summary": {
            "eligible": sum(1 for s in session_meta if s["eligible"]),
            "by_join": dict(Counter(s["join"] for s in session_meta if s["eligible"])),
            "gated_no_tail": gated_no_tail,
        },
    }
    (OUT / "cells_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    return cells, plan


def extract_json_array(text: str) -> list[dict[str, Any]]:
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def llm_prompt(batch: list[dict[str, Any]]) -> str:
    slim = []
    for c in batch:
        slim.append(
            {
                "cell_id": c["cell_id"],
                "scenario_id": c["scenario_id"],
                "framing": c["framing"],
                "framing_guidance": c["framing_text"],
                "checkpoint": c["checkpoint"],
                "state_variant": c["state_variant"],
                "question_variant": c["question_variant"],
                "question": c["question_text"]
                + " Answer fire or defer from the snapshot only.",
                "response_class": c["response_class"],
                "response_class_map": c["response_class_spec"]["map"],
                "labels": c["response_class_spec"]["labels"],
                "state": c["state"],
            }
        )
    return (
        "You are an offline interception policy-under-test driver=flash "
        "(NOT gold; Soft Standard HOLD; no product unlock).\n"
        "Judge ONLY the provided prefix snapshot + framing + question + response-class mapping.\n"
        "Do NOT infer final session length. Do NOT invent future turns or tool results.\n"
        "Empty or missing evidence → defer (insufficient evidence), never invent fire.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"fire|defer","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating = steer-urgency 0..3. Apply response_class_map for fire "
        "(label fire → fire=true; defer → fire=false).\n"
        f"CELLS ({len(slim)}):\n"
        + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx: int, batch: list[dict[str, Any]], raw_dir: Path) -> dict[str, Any]:
    prompt = llm_prompt(batch)
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [OPENCODE, "run", "--model", FLASH_MODEL, "--format", "default", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd="/tmp",
            timeout=240,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        code = proc.returncode
        err = None if code == 0 else (stderr or stdout)[:500]
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr = (e.stderr or "") if isinstance(e.stderr, str) else "timeout"
        code = -1
        err = "timeout"
    elapsed = time.time() - t0
    (raw_dir / f"batch-{batch_idx:03d}-stdout.txt").write_text(stdout, encoding="utf-8")
    (raw_dir / f"batch-{batch_idx:03d}-stderr.txt").write_text(stderr, encoding="utf-8")
    parsed = extract_json_array(stdout)
    by_id = {r.get("cell_id"): r for r in parsed if r.get("cell_id")}
    return {
        "batch_idx": batch_idx,
        "exit_code": code,
        "elapsed_s": round(elapsed, 2),
        "n_cells": len(batch),
        "n_parsed": len(by_id),
        "by_id": by_id,
        "error": err if by_id or code == 0 else (err or "parse_empty"),
    }


def normalize_fire(ans: dict[str, Any]) -> tuple[bool | None, str | None, int | None]:
    label = ans.get("label")
    if isinstance(label, str):
        label = label.strip().lower()
    fire = ans.get("fire")
    rating = ans.get("rating")
    try:
        rating_i = int(rating) if rating is not None else None
    except Exception:
        rating_i = None
    if fire is None and isinstance(label, str):
        if label in {"fire", "true", "yes"}:
            fire = True
        elif label in {"defer", "false", "no"}:
            fire = False
    if fire is None and rating_i is not None:
        fire = rating_i >= 2
    if isinstance(fire, str):
        fire = fire.strip().lower() in {"true", "fire", "yes", "1"}
    if fire is not None:
        fire = bool(fire)
    if label not in {"fire", "defer"}:
        label = "fire" if fire else ("defer" if fire is False else None)
    return fire, label, rating_i


def write_outputs(
    cells: list[dict[str, Any]],
    by_id: dict[str, Any],
    plan: dict[str, Any],
    wall_s: float,
    batch_meta: list[dict[str, Any]],
) -> dict[str, Any]:
    results_path = OUT / "results.jsonl"
    parse_miss = 0
    fire_count = 0
    defer_count = 0
    error_count = 0
    by_scen: dict[str, list[bool]] = defaultdict(list)
    rating_hist: Counter[str] = Counter()

    with results_path.open("w", encoding="utf-8") as out:
        for c in cells:
            ans = by_id.get(c["cell_id"]) or {}
            fire, label, rating_i = normalize_fire(ans)
            if fire is None and not ans:
                parse_miss += 1
            if ans.get("error"):
                error_count += 1
            if fire is True:
                fire_count += 1
            elif fire is False:
                defer_count += 1
            if rating_i is not None:
                rating_hist[str(rating_i)] += 1
            if fire is not None:
                by_scen[c["scenario_id"]].append(fire)
            row = {
                "cell_id": c["cell_id"],
                "scenario_id": c["scenario_id"],
                "state_selection": c["state_selection"],
                "question_format": c["question_format"],
                "session_id": c["session_id"],
                "harness": c.get("harness"),
                "project": c.get("project"),
                "checkpoint": c["checkpoint"],
                "checkpoint_role": c["checkpoint_role"],
                "framing": c["framing"],
                "response_class": c["response_class"],
                "state_fill": c.get("state_fill"),
                "label_join_eligibility": c.get("label_join_eligibility"),
                "cell_tier": c.get("cell_tier"),
                "label": label,
                "rating": rating_i,
                "fire": fire,
                "fire_offset_turns": ans.get("fire_offset_turns"),
                "rationale": ans.get("rationale"),
                "window_status": "unidentified",
                "reference_fire": None,
                "outcome_tag": None,
                "judge_role": "policy-under-test",
                "model": FLASH_MODEL,
                "driver": "flash",
                "soft_standard_hold": True,
                "product_wiring": False,
                "batch": "batch-002",
                "wave": "growth-preferred-flash",
                "capture_tag": "flash-growth-preferred",
                "error": ans.get("error"),
                "ts": now_aest(),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    outcomes = {}
    for sid, flags in sorted(by_scen.items()):
        outcomes[sid] = {
            "n_sessions": len(flags),
            "fire_count": sum(flags),
            "defer_count": len(flags) - sum(flags),
            "fire_rate": round(sum(flags) / len(flags), 4) if flags else None,
        }

    attempted = len(cells)
    meters = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "growth-preferred-flash",
        "driver": "flash",
        "model": FLASH_MODEL,
        "meters_class": "score-ready-path-diagnostics",
        "score_ready_fp_miss_board": False,
        "soft_standard_hold": True,
        "product_wiring": False,
        "hooks_unlock": False,
        "preferred_cut": True,
        "growth_fill_version": FILL_VERSION,
        "n_scenarios": plan["n_preferred_scenarios"],
        "n_exact_labeled_sessions": plan["n_exact_labeled_sessions"],
        "n_cells_attempted": attempted,
        "n_fire": fire_count,
        "n_defer": defer_count,
        "n_parse_miss": parse_miss,
        "n_errors": error_count,
        "fire_rate": round(fire_count / attempted, 4) if attempted else None,
        "rating_hist": dict(rating_hist),
        "outcomes_by_scenario": outcomes,
        "wall_s": wall_s,
        "n_batches": len(batch_meta),
        "batch_elapsed_sum_s": round(sum(b["elapsed_s"] for b in batch_meta), 1),
        "cells_per_batch": CELLS_PER_FLASH,
        "max_par": MAX_PAR_FLASH,
        "checkpoint_policy": "one_representative_mid_per_session",
        "window_cartesian": False,
        "empty_state_policy": "unsupported_not_negative",
        "include_diagnostic": INCLUDE_DIAG,
        "exact_session_ids": plan["exact_session_ids"],
        "note": "Flash often omits token meters; counts are cell-level only.",
    }
    (OUT / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")

    md = [
        "# SOFT-HOLD — Flash preferred GROWTH cut (#109/#111)",
        "",
        f"**Generated:** {meters['generated_at']} (AEST)",
        "",
        "**Soft Standard HOLD** — white-paper evidence only. No hooks, Soft Standard unlock, Pilot, or live Jev. `:8080` unused.",
        "",
        "## Cut",
        f"- Preferred scenarios: **{plan['n_preferred_scenarios']}** (frozen from `GROWTH-RANKING.json`)",
        f"- Exact-labeled sessions: **{plan['n_exact_labeled_sessions']}**",
        f"- Planned cells: **{plan['n_cells_planned']}** (12×9=108 when exact=9)",
        f"- Include diagnostic 7: **{INCLUDE_DIAG}**",
        f"- growth-fill: `{FILL_VERSION}`; empty state = unsupported (gated)",
        f"- Tail-less gated sessions: **{plan['gated_no_tail_sessions']}**",
        "",
        "## Counts",
        f"- attempted: **{attempted}**",
        f"- fire: **{fire_count}**",
        f"- defer: **{defer_count}**",
        f"- parse_miss: **{parse_miss}**",
        f"- errors: **{error_count}**",
        f"- fire_rate: **{meters['fire_rate']}**",
        f"- wall_s: **{wall_s}**",
        "",
        "## Exact sessions",
    ]
    for sid in plan["exact_session_ids"]:
        md.append(f"- `{sid}`")
    md += ["", "## Outcomes by scenario"]
    for sid, o in outcomes.items():
        md.append(
            f"- `{sid}` — n={o['n_sessions']} fire={o['fire_count']} "
            f"defer={o['defer_count']} rate={o['fire_rate']}"
        )
    md += [
        "",
        "## Non-authorization",
        "- Soft HOLD unchanged; no behaviour/hooks ship.",
        "- `window_status=unidentified` at emit; no FP/miss board.",
        "- Replication of preferred analytic cut, not a preregistered product eval.",
        "",
    ]
    (OUT / "SOFT-HOLD.md").write_text("\n".join(md) + "\n")
    (OUT / "grid.json").write_text(
        json.dumps(
            {
                "generated_at": now_aest(),
                "driver": "flash",
                "model": FLASH_MODEL,
                "n_cells": attempted,
                "preferred_pairs": plan["preferred_pairs"],
                "exact_session_ids": plan["exact_session_ids"],
                "soft_standard_hold": True,
            },
            indent=2,
        )
        + "\n"
    )
    return meters


def main() -> int:
    # Refuse if llama endpoint is up (keep unloaded)
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=0.5)
        print("REFUSE: :8080 appears up; keep llama unloaded for this Soft HOLD run", flush=True)
        return 2
    except Exception:
        pass

    cells, plan = build_cells()
    print(json.dumps({"plan": {k: plan[k] for k in plan if k != "session_meta_summary"}, "n_cells": len(cells)}), flush=True)
    if len(cells) == 0:
        print("no cells", flush=True)
        return 1

    raw_dir = OUT / "raw"
    batches = [cells[i : i + CELLS_PER_FLASH] for i in range(0, len(cells), CELLS_PER_FLASH)]
    print(
        f"[{now_aest()}] Flash growth-preferred start n={len(cells)} batches={len(batches)} "
        f"par={MAX_PAR_FLASH}",
        flush=True,
    )
    batch_meta: list[dict[str, Any]] = []
    by_id: dict[str, Any] = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_FLASH) as ex:
        futs = {ex.submit(run_flash_batch, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            batch_meta.append(res)
            by_id.update(res.get("by_id") or {})
            print(
                f"[{now_aest()}] batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s "
                f"err={res.get('error')!r}",
                flush=True,
            )
    wall = round(time.time() - t0, 1)
    meters = write_outputs(cells, by_id, plan, wall, batch_meta)
    print(
        json.dumps(
            {
                "attempted": meters["n_cells_attempted"],
                "fire": meters["n_fire"],
                "defer": meters["n_defer"],
                "parse_miss": meters["n_parse_miss"],
                "errors": meters["n_errors"],
                "wall_s": wall,
                "soft_hold": True,
                "out": str(OUT),
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
