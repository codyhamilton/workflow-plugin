#!/usr/bin/env python3
"""batch-002 multi-driver lever waves — TypeSafe + Flash + Luna (Soft HOLD).

Adaptation of run_batch002.py (Flash Wave-0):
- Same R1–R3 decontam protocol (no T leak; fixed schedule 45…120; non-length outcomes)
- Reuses existing batch-002 snapshots/ (join keys = session_id + checkpoint)
- Adds framing axis H1–H5 and expands question/response packs
- Drivers: TypeSafe (System One jev-1.13.0), Flash (deepseek-flash), Luna (gpt-6-luna)
- Soft Standard HOLD — no hooks / product unlock; judges are policy-under-test only
- Does NOT invent outcome labels; window_status remains unidentified

Outputs under:
  batch-002/typesafe/
  batch-002/flash-hframings/
  batch-002/luna/
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path("/home/codyh/workspace/workflow-plugin")
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
SNAP_DIR = BATCH / "snapshots"
_OUT_TAG = (os.environ.get("MULTI_OUT_TAG") or "").strip()
_OUT_SUFFIX = f"-{_OUT_TAG}" if _OUT_TAG else ""
OUT = {
    "typesafe": BATCH / f"typesafe{_OUT_SUFFIX}",
    "flash": BATCH / f"flash-hframings{_OUT_SUFFIX}",
    "luna": BATCH / f"luna{_OUT_SUFFIX}",
}
MIRROR = Path("/tmp/2026-10-02-interception-trials-batch-002-multi")
AEST = ZoneInfo("Australia/Brisbane")

FLASH_MODEL = "deepseek/deepseek-flash"
LUNA_MODEL = os.environ.get("WORKFLOW_LUNA_MODEL", "gpt-6-luna")
TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"

FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)

# Aggressive but practical targets (Soft HOLD trials OK)
TARGET_TYPESAFE = 300
TARGET_FLASH = 240
TARGET_LUNA = 72
CELLS_PER_FLASH = 10
CELLS_PER_LUNA = 6
MAX_PAR_TS = 6
MAX_PAR_FLASH = 3
MAX_PAR_LUNA = 2

FRAMINGS: dict[str, str] = {
    "H1": (
        "Framing H1 progressive re-check: decide fire-now vs defer-and-recheck ~15 turns. "
        "Preserve productive development and near-done closing; catch runaway thrash."
    ),
    "H2": (
        "Framing H2 horizon control: is further continuation still within a defensible "
        "resource/horizon envelope, or should we steer toward stop to bound the tail?"
    ),
    "H3": (
        "Framing H3 progress velocity: is there a sustained low-yield plateau / thrash, "
        "or still substantive progress? Temporary stalls alone are not fire."
    ),
    "H4": (
        "Framing H4 deliverable boundary: protect completion/validation/delivery; "
        "fire on post-boundary overrun, defer on genuine closing work."
    ),
    "H5": (
        "Framing H5 counterfactual waste: would steering now likely reduce avoidable "
        "continuation without destroying recoverable value?"
    ),
}

QUESTION_VARIANTS = {
    "continue_excessively": (
        "Will this job likely continue excessively from this checkpoint if uninterrupted? "
        "Judge only the snapshot."
    ),
    "steer_now": (
        "Is NOW a useful time to steer toward stopping, without truncating productive "
        "development or near-done closing work?"
    ),
    "productive_arc": (
        "Is there evidence of a steady productive build rather than thrash or frozen narration?"
    ),
    "near_done": (
        "Does the snapshot suggest closing / validation / delivery (near-done) rather than mid-runaway?"
    ),
    "thrash_bundle": (
        "Do compaction, rereads, and weak new output form a thrash bundle?"
    ),
    "defer_recheck": (
        "Should interception DEFER and re-check ~15 turns later instead of firing now?"
    ),
    # Expanded packs
    "horizon_exceeded": (
        "Has continuation risk exceeded a prudent horizon such that steering toward stop is warranted now?"
    ),
    "plateau_sustained": (
        "Is low-yield / repetitive work sustained enough to treat as a plateau (not a brief stall)?"
    ),
    "boundary_overrun": (
        "Is work past a plausible deliverable boundary into overrun polish / scope creep?"
    ),
    "waste_intervene": (
        "Would intervening now likely reduce avoidable waste without cutting recoverable value?"
    ),
}

RESPONSE_CLASSES = {
    "binary_fire": {
        "labels": ["fire", "defer"],
        "map": "Set fire=true iff label is fire. rating: fire→3, defer→0.",
    },
    "likert_0_3": {
        "labels": ["0", "1", "2", "3"],
        "map": "rating 0-3 steer urgency. fire=true iff rating>=2.",
    },
    "four_class": {
        "labels": [
            "productive_continue",
            "near_completion",
            "likely_runaway",
            "uncertain",
        ],
        "map": (
            "fire=true only for likely_runaway. "
            "rating: productive_continue→0, near_completion→1, uncertain→1, likely_runaway→3."
        ),
    },
    "rating_plus_offset": {
        "labels": ["0", "1", "2", "3"],
        "map": (
            "rating 0-3. fire=true iff rating>=2. "
            "fire_offset_turns in {-15,0,15,30} is DIAGNOSTIC only."
        ),
    },
}

# Lever combos tagged with preferred framing (still cross-product lightly)
LEVER_COMBOS: list[tuple[str, str, str, str]] = [
    # (framing, state, question, response_class)
    ("H1", "stats_only", "continue_excessively", "likert_0_3"),
    ("H1", "stats_only", "steer_now", "binary_fire"),
    ("H1", "hybrid_v0", "defer_recheck", "binary_fire"),
    ("H1", "hybrid_v0", "steer_now", "likert_0_3"),
    ("H1", "stats_plus_delta", "continue_excessively", "rating_plus_offset"),
    ("H2", "stats_only", "horizon_exceeded", "likert_0_3"),
    ("H2", "stats_plus_delta", "horizon_exceeded", "binary_fire"),
    ("H2", "hybrid_v0", "steer_now", "four_class"),
    ("H2", "compact_focus", "continue_excessively", "likert_0_3"),
    ("H3", "stats_only", "plateau_sustained", "likert_0_3"),
    ("H3", "hybrid_v0", "thrash_bundle", "four_class"),
    ("H3", "stats_plus_delta", "productive_arc", "likert_0_3"),
    ("H3", "compact_focus", "thrash_bundle", "binary_fire"),
    ("H4", "hybrid_v0", "near_done", "four_class"),
    ("H4", "stats_only", "boundary_overrun", "likert_0_3"),
    ("H4", "stats_plus_delta", "near_done", "binary_fire"),
    ("H4", "compact_focus", "boundary_overrun", "four_class"),
    ("H5", "hybrid_v0", "waste_intervene", "likert_0_3"),
    ("H5", "stats_only", "waste_intervene", "binary_fire"),
    ("H5", "stats_plus_delta", "defer_recheck", "rating_plus_offset"),
    ("H5", "compact_focus", "steer_now", "four_class"),
    # extra H1 coverage for volume
    ("H1", "stats_only", "thrash_bundle", "four_class"),
    ("H1", "hybrid_v0", "continue_excessively", "four_class"),
    ("H1", "compact_focus", "defer_recheck", "likert_0_3"),
]


def now_aest() -> str:
    return datetime.now(AEST).strftime("%Y-%m-%d %H:%M:%S AEST")


def project_state(full: dict[str, Any], mode: str) -> dict[str, Any]:
    cum = full.get("cumulative") or {}
    if mode == "stats_only":
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "schedule": full.get("schedule"),
            "cumulative": cum,
            "evidence_class": "stats_only",
        }
    if mode == "stats_plus_delta":
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "schedule": full.get("schedule"),
            "cumulative": cum,
            "delta_since_prior": full.get("delta_since_prior") or {},
            "evidence_class": "stats_plus_delta",
        }
    if mode == "compact_focus":
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "cumulative": {
                "api_turns": cum.get("api_turns"),
                "peak_ctx_tokens": cum.get("peak_ctx_tokens"),
                "compaction_event_count": cum.get("compaction_event_count"),
                "reread_paths": cum.get("reread_paths"),
                "assistant_text_chars": cum.get("assistant_text_chars"),
                "tool_histogram": cum.get("tool_histogram"),
            },
            "evidence_class": "compact_focus",
        }
    return {
        "checkpoint_turn": full.get("checkpoint_turn"),
        "schedule": full.get("schedule"),
        "brief_anchor": (full.get("brief_anchor") or "")[:300],
        "cumulative": cum,
        "delta_since_prior": full.get("delta_since_prior") or {},
        "tail": (full.get("tail") or [])[-4:],
        "evidence_class": "hybrid_v0",
    }


def _strip_leaks(projected: dict[str, Any]) -> dict[str, Any]:
    for bad in (
        "T",
        "T_observed",
        "T_observed_session",
        "approx_progress_frac",
        "userish_count_full_session",
        "messages_full",
        "T_proxy",
        "norm_length",
        "T_eligibility_only",
        "_T_eligibility_only",
    ):
        projected.pop(bad, None)
        cum = projected.get("cumulative")
        if isinstance(cum, dict):
            cum.pop(bad, None)
    return projected


def cell_id(driver: str, framing: str, session_id: str, cp: int, state_v: str, q: str, rc: str) -> str:
    raw = f"b002|{driver}|{framing}|{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_packs() -> list[dict[str, Any]]:
    packs = []
    for sp in sorted(SNAP_DIR.glob("*.json")):
        try:
            pack = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not pack.get("checkpoints"):
            continue
        # ensure worker_id
        if not pack.get("worker_id"):
            pack["worker_id"] = sp.stem
        packs.append(pack)
    return packs


def _make_cell(
    pack: dict[str, Any],
    snap: dict[str, Any],
    framing: str,
    state_v: str,
    q: str,
    rc: str,
    driver: str,
) -> dict[str, Any]:
    sid = pack["worker_id"]
    full = snap.get("full_state") or {}
    # ensure checkpoint_turn present
    if "checkpoint_turn" not in full:
        full = {**full, "checkpoint_turn": snap["checkpoint"]}
    projected = project_state(full, state_v)
    if len(json.dumps(projected, ensure_ascii=False)) > 3500:
        projected = project_state(full, "stats_only")
        projected["truncated_from"] = state_v
    projected = _strip_leaks(projected)
    return {
        "cell_id": cell_id(driver, framing, sid, snap["checkpoint"], state_v, q, rc),
        "session_id": sid,
        "harness": pack.get("harness"),
        "project": pack.get("project"),
        "maps_family": pack.get("maps_family"),
        "corpus_source": pack.get("corpus_source"),
        "checkpoint": snap["checkpoint"],
        "framing": framing,
        "state_variant": state_v,
        "question_variant": q,
        "response_class": rc,
        "state": projected,
        "question_text": QUESTION_VARIANTS[q],
        "framing_text": FRAMINGS[framing],
        "response_class_spec": RESPONSE_CLASSES[rc],
        "window_status": "unidentified",
        "driver": driver,
    }


def build_cells(packs: list[dict[str, Any]], driver: str, target: int) -> list[dict[str, Any]]:
    """Interleave framings × checkpoints so H1–H5 all appear (no H1-only fill)."""
    usable = [p for p in packs if p.get("checkpoints")]
    usable = sorted(
        usable,
        key=lambda p: (
            0 if p.get("harness") == "claude-code" else 1 if p.get("harness") == "opencode" else 2,
            -int(p.get("T_eligibility_only") or 0),
        ),
    )
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for pack in usable:
        for snap in pack["checkpoints"]:
            pairs.append((pack, snap))
    pairs.sort(
        key=lambda x: (
            int(x[1]["checkpoint"]),
            0 if x[0].get("harness") == "claude-code" else 1,
        )
    )
    cells: list[dict[str, Any]] = []
    # Round-robin: for each pair, cycle levers; then second pass for volume
    for pack, snap in pairs:
        for framing, state_v, q, rc in LEVER_COMBOS:
            cells.append(_make_cell(pack, snap, framing, state_v, q, rc, driver))
            if len(cells) >= target:
                return cells
    for framing, state_v, q, rc in LEVER_COMBOS:
        for pack, snap in pairs:
            cells.append(_make_cell(pack, snap, framing, state_v, q, rc, driver))
            if len(cells) >= target:
                return cells
    return cells


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


def llm_prompt(batch: list[dict[str, Any]], driver: str) -> str:
    slim = []
    for c in batch:
        slim.append(
            {
                "cell_id": c["cell_id"],
                "framing": c["framing"],
                "framing_guidance": c["framing_text"],
                "checkpoint": c["checkpoint"],
                "state_variant": c["state_variant"],
                "question_variant": c["question_variant"],
                "question": c["question_text"],
                "response_class": c["response_class"],
                "response_class_map": c["response_class_spec"]["map"],
                "labels": c["response_class_spec"]["labels"],
                "state": c["state"],
            }
        )
    return (
        f"You are an offline interception policy-under-test driver={driver} "
        "(NOT gold; Soft Standard HOLD; no product unlock).\n"
        "Judge ONLY the provided prefix snapshot + framing + question + response-class mapping.\n"
        "Do NOT infer final session length. Do NOT invent future turns or tool results.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"...","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating = steer-urgency 0..3. Apply response_class_map for fire.\n"
        f"CELLS ({len(slim)}):\n"
        + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx: int, batch: list[dict[str, Any]], raw_dir: Path) -> dict[str, Any]:
    prompt = llm_prompt(batch, "flash")
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    proc = subprocess.run(
        ["opencode", "run", "--model", FLASH_MODEL, "--format", "default", prompt],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd="/tmp",
        timeout=180,
    )
    elapsed = time.time() - t0
    (raw_dir / f"batch-{batch_idx:03d}-stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (raw_dir / f"batch-{batch_idx:03d}-stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    parsed = extract_json_array(proc.stdout or "")
    by_id = {r.get("cell_id"): r for r in parsed if r.get("cell_id")}
    return {
        "batch_idx": batch_idx,
        "exit_code": proc.returncode,
        "elapsed_s": round(elapsed, 2),
        "n_cells": len(batch),
        "n_parsed": len(by_id),
        "by_id": by_id,
        "error": None if proc.returncode == 0 or by_id else (proc.stderr or "")[:500],
    }


def run_luna_batch(batch_idx: int, batch: list[dict[str, Any]], raw_dir: Path) -> dict[str, Any]:
    prompt = llm_prompt(batch, "luna")
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    bin_path = os.environ.get("WORKFLOW_CODEX_BIN", "codex")
    try:
        # Write prompt to file — avoids stdin "Reading additional input" + trust check
        prompt_path = raw_dir / f"batch-{batch_idx:03d}-prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        proc = subprocess.run(
            [
                bin_path,
                "exec",
                "--skip-git-repo-check",
                "-m",
                LUNA_MODEL,
                "--",
                prompt,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=240,
        )
        stdout, stderr, code = proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr = "timeout"
        code = -1
    except Exception as e:
        stdout, stderr, code = "", f"{type(e).__name__}: {e}", -1
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
        "error": None if by_id else (stderr or "luna_parse_failed")[:500],
    }


def typesafe_questions(cell: dict[str, Any]) -> dict[str, Any]:
    """Map lever cell → System One question shapes (choice/score)."""
    framing = cell["framing_text"]
    qtext = cell["question_text"]
    rc = cell["response_class"]
    instructions = (
        f"{framing} Question: {qtext} "
        "Judge ONLY the prefix snapshot. Do not infer final session length or future turns."
    )
    qs: dict[str, Any] = {}
    if rc in ("likert_0_3", "rating_plus_offset"):
        qs["rating"] = {
            "type": "score",
            "instructions": instructions + " Score steer-urgency 0..3.",
            "criteria": [
                "0: clearly productive / defer",
                "1: mild concern or uncertain",
                "2: useful to steer soon",
                "3: fire / likely runaway thrash",
            ],
        }
    if rc == "binary_fire":
        qs["label"] = {
            "type": "choice",
            "instructions": instructions + " Choose fire or defer.",
            "criteria": {
                "fire": "Fire now: thrash/runaway or horizon exceeded",
                "defer": "Defer: productive arc, near-done closing, or insufficient evidence",
            },
        }
    if rc == "four_class":
        qs["label"] = {
            "type": "choice",
            "instructions": instructions + " Pick exactly one class.",
            "criteria": {
                "productive_continue": "Steady productive build; continue",
                "near_completion": "Closing / validation / delivery",
                "likely_runaway": "Thrash / runaway continuation likely",
                "uncertain": "Insufficient evidence",
            },
        }
    if rc == "rating_plus_offset":
        qs["fire_offset"] = {
            "type": "choice",
            "instructions": "Diagnostic only: preferred fire offset in turns from this checkpoint.",
            "criteria": {
                "-15": "Would have preferred ~15 turns earlier",
                "0": "Now is appropriate if firing",
                "15": "Prefer re-check ~15 turns later",
                "30": "Prefer re-check ~30 turns later",
            },
        }
    # Always include fire_now for joinable fire column when score-only
    if "label" not in qs:
        qs["fire_now"] = {
            "type": "choice",
            "instructions": instructions + " Should interception fire now?",
            "criteria": {
                "fire": "Fire / steer toward stop now",
                "defer": "Defer / do not fire now",
            },
        }
    return qs


def map_typesafe_answers(cell: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    rc = cell["response_class"]
    label = None
    rating = None
    fire = None
    offset = None
    # score
    if "rating" in answers and isinstance(answers["rating"], dict):
        sc = answers["rating"].get("score")
        try:
            # TypeSafe score is often 0..1 continuous over criteria span; map to 0..3
            if isinstance(sc, (int, float)):
                if 0 <= float(sc) <= 1.5:
                    # continuous in [0,1] style from spike — map via probabilities if present
                    probs = answers["rating"].get("probabilities") or {}
                    if probs:
                        best = max(probs.items(), key=lambda kv: float(kv[1]))
                        rating = int(best[0])
                    else:
                        rating = int(round(min(3, max(0, float(sc) * 3))))
                else:
                    rating = int(round(min(3, max(0, float(sc)))))
        except Exception:
            rating = None
    if "label" in answers and isinstance(answers["label"], dict):
        label = answers["label"].get("choice")
    if "fire_now" in answers and isinstance(answers["fire_now"], dict):
        fn = answers["fire_now"].get("choice")
        if fn == "fire":
            fire = True
        elif fn == "defer":
            fire = False
    if "fire_offset" in answers and isinstance(answers["fire_offset"], dict):
        try:
            offset = int(answers["fire_offset"].get("choice"))
        except Exception:
            offset = None

    if rc == "binary_fire":
        if label == "fire":
            fire, rating = True, 3
        elif label == "defer":
            fire, rating = False, 0
    elif rc == "four_class":
        map_r = {
            "productive_continue": 0,
            "near_completion": 1,
            "uncertain": 1,
            "likely_runaway": 3,
        }
        if label in map_r:
            rating = map_r[label]
            fire = label == "likely_runaway"
    elif rc in ("likert_0_3", "rating_plus_offset"):
        if rating is not None:
            fire = rating >= 2
        if label is None and rating is not None:
            label = str(rating)

    if fire is None and rating is not None:
        fire = rating >= 2

    return {
        "label": label,
        "rating": rating,
        "fire": fire,
        "fire_offset_turns": offset if offset is not None else 0,
        "rationale": f"typesafe {JEV_MODEL}",
        "raw_answers": answers,
    }


def run_typesafe_cell(cell: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    key = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if not key:
        return {"cell_id": cell["cell_id"], "error": "missing_TYPESAFE_API_KEY", "ok": False}
    req = {
        "model": JEV_MODEL,
        "state": cell["state"],
        "questions": typesafe_questions(cell),
    }
    cid = cell["cell_id"]
    (raw_dir / f"{cid}-request.json").write_text(json.dumps(req, indent=2) + "\n", encoding="utf-8")
    body = json.dumps(req).encode("utf-8")
    http = urllib.request.Request(
        TYPESAFE_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(http, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        (raw_dir / f"{cid}-error.txt").write_text(f"HTTP {e.code}\n{detail}\n", encoding="utf-8")
        return {
            "cell_id": cid,
            "ok": False,
            "error": f"HTTP {e.code}: {detail[:800]}",
            "elapsed_s": round(time.time() - t0, 2),
            "usage": None,
        }
    except Exception as e:
        (raw_dir / f"{cid}-error.txt").write_text(f"{type(e).__name__}: {e}\n", encoding="utf-8")
        return {
            "cell_id": cid,
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_s": round(time.time() - t0, 2),
            "usage": None,
        }
    elapsed = time.time() - t0
    (raw_dir / f"{cid}-response.json").write_text(raw + ("\n" if not raw.endswith("\n") else ""), encoding="utf-8")
    try:
        payload = json.loads(raw)
    except Exception as e:
        return {"cell_id": cid, "ok": False, "error": f"json_parse: {e}", "elapsed_s": round(elapsed, 2)}
    answers = payload.get("answers") or {}
    mapped = map_typesafe_answers(cell, answers)
    return {
        "cell_id": cid,
        "ok": True,
        "status": status,
        "elapsed_s": round(elapsed, 2),
        "usage": payload.get("usage"),
        "model": payload.get("model") or JEV_MODEL,
        **mapped,
    }


def prompt_leak_spotcheck(raw_dir: Path) -> list[dict[str, str]]:
    needles = (
        "T_observed_session",
        "approx_progress_frac",
        "userish_count_full_session",
        "T_eligibility",
        "short_natural",
        "long_runawayish",
        "ideal_window",
    )
    hits = []
    for path in list(raw_dir.glob("*-prompt.txt")) + list(raw_dir.glob("*-request.json")):
        try:
            txt = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for needle in needles:
            if needle in txt:
                hits.append({"file": path.name, "needle": needle})
    return hits


def write_results(
    driver: str,
    cells: list[dict[str, Any]],
    by_id: dict[str, Any],
    out_dir: Path,
    extra_meters: dict[str, Any],
) -> dict[str, Any]:
    results_path = out_dir / "results.jsonl"
    fire_by_cp: dict[int, list[bool]] = {t: [] for t in FIXED_SCHEDULE}
    rating_hist: dict[str, int] = {}
    harness_counts: dict[str, int] = {}
    framing_counts: dict[str, int] = {}
    parse_miss = 0
    fire_count = 0
    error_count = 0
    input_tokens = 0
    output_tokens = 0

    with results_path.open("w", encoding="utf-8") as out:
        for c in cells:
            ans = by_id.get(c["cell_id"]) or {}
            if not ans or ans.get("error") and not ans.get("ok", True) and ans.get("rating") is None and ans.get("fire") is None:
                parse_miss += 1
                if ans.get("error"):
                    error_count += 1
            rating = ans.get("rating")
            try:
                rating_i = int(rating) if rating is not None else None
            except Exception:
                rating_i = None
            fire = ans.get("fire")
            if fire is None and rating_i is not None:
                fire = rating_i >= 2
            if fire:
                fire_count += 1
            label = ans.get("label")
            if rating_i is not None:
                rating_hist[str(rating_i)] = rating_hist.get(str(rating_i), 0) + 1
            cp = int(c["checkpoint"])
            if fire is not None:
                fire_by_cp.setdefault(cp, []).append(bool(fire))
            harness_counts[c.get("harness") or "?"] = harness_counts.get(c.get("harness") or "?", 0) + 1
            framing_counts[c["framing"]] = framing_counts.get(c["framing"], 0) + 1
            usage = ans.get("usage") or {}
            if isinstance(usage, dict):
                input_tokens += int(usage.get("input_tokens") or 0)
                output_tokens += int(usage.get("output_tokens") or 0)
            model = ans.get("model")
            if not model:
                model = {
                    "typesafe": JEV_MODEL,
                    "flash": FLASH_MODEL,
                    "luna": LUNA_MODEL,
                }.get(driver, driver)
            row = {
                "cell_id": c["cell_id"],
                "session_id": c["session_id"],
                "harness": c.get("harness"),
                "project": c.get("project"),
                "maps_family": c.get("maps_family"),
                "corpus_source": c.get("corpus_source"),
                "checkpoint": cp,
                "framing": c["framing"],
                "state_variant": c["state_variant"],
                "question_variant": c["question_variant"],
                "response_class": c["response_class"],
                "label": label,
                "rating": rating_i,
                "fire": fire,
                "fire_offset_turns": ans.get("fire_offset_turns"),
                "rationale": ans.get("rationale"),
                "window_status": "unidentified",
                "reference_fire": None,
                "outcome_tag": None,
                "judge_role": "policy-under-test",
                "model": model,
                "driver": driver,
                "typesafe": driver == "typesafe",
                "soft_standard_hold": True,
                "batch": "batch-002",
                "wave": "Wave-0-multi",
                "error": ans.get("error"),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    fire_rate_at_risk = {}
    for t, flags in fire_by_cp.items():
        if flags:
            fire_rate_at_risk[str(t)] = {
                "n": len(flags),
                "fire_rate": round(sum(flags) / len(flags), 4),
            }
        else:
            fire_rate_at_risk[str(t)] = {"n": 0, "fire_rate": None}

    leak_hits = prompt_leak_spotcheck(out_dir / "raw")
    meters = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "Wave-0-multi",
        "driver": driver,
        "meters_class": "score-ready-path-diagnostics",
        "score_ready_fp_miss_board": False,
        "reason_fp_miss_board_false": (
            "window_status=unidentified; do not invent outcome labels; join later via OUTCOME-SHEET"
        ),
        "protocol_fixes": [
            "R1_no_T_in_prompt_or_state",
            "R2_non_length_outcome_sheet",
            "R3_fixed_schedule_hazard",
        ],
        "soft_standard_hold": True,
        "hooks_unlock": False,
        "product_unlock": False,
        "n_cells": len(cells),
        "parse_miss_cells": parse_miss,
        "error_count": error_count,
        "fire_count": fire_count,
        "rating_hist": rating_hist,
        "harness_cell_counts": harness_counts,
        "framing_cell_counts": framing_counts,
        "fixed_schedule": list(FIXED_SCHEDULE),
        "fire_rate_among_at_risk_cells": fire_rate_at_risk,
        "prompt_leak_spotcheck_hits": leak_hits,
        "usage_tokens_rough": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "note": "TypeSafe usage when present; Flash/Luna often omit token meters",
        },
        **extra_meters,
    }
    (out_dir / "meters.json").write_text(json.dumps(meters, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# METERS — batch-002 {driver} multi-driver wave",
        "",
        f"**Generated:** {meters['generated_at']}",
        "",
        "**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.",
        f"**Driver:** `{driver}`  **Wave:** Wave-0-multi  **Batch:** batch-002",
        "",
        "## Protocol",
        "- R1: no T / progress-frac / full-session length in prompt or state",
        "- R2: no length-derived outcome tags; window_status=unidentified (join later)",
        f"- R3: fixed schedule `{list(FIXED_SCHEDULE)}`",
        "",
        "## Counts",
        f"- n_cells: **{len(cells)}**",
        f"- parse_miss: **{parse_miss}**; errors: **{error_count}**; fire_count: **{fire_count}**",
        f"- leak_spotcheck_hits: **{len(leak_hits)}**",
        f"- usage tokens (rough): in={input_tokens} out={output_tokens}",
        "",
        "## Framing mix",
    ]
    for k, v in sorted(framing_counts.items()):
        md.append(f"- `{k}`: {v}")
    md.append("")
    md.append("## Harness mix")
    for k, v in sorted(harness_counts.items()):
        md.append(f"- `{k}`: {v}")
    md.append("")
    md.append("## Fire rate by checkpoint (among cells at t)")
    md.append("| t | n | fire_rate |")
    md.append("|---|---|-----------|")
    for t in FIXED_SCHEDULE:
        fr = fire_rate_at_risk.get(str(t), {})
        md.append(f"| {t} | {fr.get('n')} | {fr.get('fire_rate')} |")
    md.append("")
    md.append("## Rating hist")
    for k, v in sorted(rating_hist.items()):
        md.append(f"- rating {k}: {v}")
    md.append("")
    md.append("## Join")
    md.append(
        "Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. "
        "Do **not** invent outcome labels."
    )
    md.append("")
    (out_dir / "METERS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return meters


def run_driver_typesafe(cells: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir = OUT["typesafe"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"[{now_aest()}] TypeSafe start n={len(cells)} par={MAX_PAR_TS}", flush=True)
    by_id: dict[str, Any] = {}
    errors = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_TS) as ex:
        futs = {ex.submit(run_typesafe_cell, c, raw_dir): c["cell_id"] for c in cells}
        done = 0
        for fut in as_completed(futs):
            res = fut.result()
            by_id[res["cell_id"]] = res
            done += 1
            if not res.get("ok"):
                errors.append({"cell_id": res["cell_id"], "error": res.get("error")})
            if done % 20 == 0 or done == len(cells):
                print(
                    f"[{now_aest()}] TypeSafe {done}/{len(cells)} "
                    f"ok={sum(1 for v in by_id.values() if v.get('ok'))} "
                    f"err={len(errors)}",
                    flush=True,
                )
                # early abort if first 10 all fail with same HTTP error
                if done == 10 and len(errors) == 10:
                    print(f"[{now_aest()}] TypeSafe early abort: first 10 failed", flush=True)
                    break
    wall = round(time.time() - t0, 1)
    # fill remaining as errors if aborted
    for c in cells:
        if c["cell_id"] not in by_id:
            by_id[c["cell_id"]] = {
                "cell_id": c["cell_id"],
                "ok": False,
                "error": "skipped_after_early_abort",
            }
            errors.append({"cell_id": c["cell_id"], "error": "skipped_after_early_abort"})
    grid = {
        "generated_at": now_aest(),
        "driver": "typesafe",
        "model": JEV_MODEL,
        "n_cells": len(cells),
        "framings": sorted({c["framing"] for c in cells}),
        "soft_standard_hold": True,
        "adaptation_note": (
            "Adapted Flash batch-002 runner: one System One POST per cell; "
            "response-class mapped to choice/score questions; same R1–R3 state projection."
        ),
    }
    (out_dir / "grid.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    meters = write_results(
        "typesafe",
        cells,
        by_id,
        out_dir,
        {
            "wall_s": wall,
            "typesafe_ok": sum(1 for v in by_id.values() if v.get("ok")),
            "typesafe_errors_sample": errors[:10],
            "api_url": TYPESAFE_URL,
            "model": JEV_MODEL,
        },
    )
    print(f"[{now_aest()}] TypeSafe done wall={wall}s meters_fire={meters['fire_count']}", flush=True)
    return meters


def run_driver_flash(cells: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir = OUT["flash"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    batches = [cells[i : i + CELLS_PER_FLASH] for i in range(0, len(cells), CELLS_PER_FLASH)]
    print(f"[{now_aest()}] Flash-H start n={len(cells)} batches={len(batches)}", flush=True)
    flash_results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_FLASH) as ex:
        futs = {ex.submit(run_flash_batch, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            flash_results.append(res)
            print(
                f"[{now_aest()}] Flash batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s",
                flush=True,
            )
    by_id: dict[str, Any] = {}
    for res in flash_results:
        by_id.update(res.get("by_id") or {})
    wall = round(time.time() - t0, 1)
    grid = {
        "generated_at": now_aest(),
        "driver": "flash",
        "model": FLASH_MODEL,
        "n_cells": len(cells),
        "n_batches": len(batches),
        "framings": sorted({c["framing"] for c in cells}),
        "soft_standard_hold": True,
    }
    (out_dir / "grid.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    meters = write_results(
        "flash",
        cells,
        by_id,
        out_dir,
        {
            "wall_s": wall,
            "n_batches": len(batches),
            "batch_elapsed_sum_s": round(sum(r["elapsed_s"] for r in flash_results), 1),
            "model": FLASH_MODEL,
        },
    )
    print(f"[{now_aest()}] Flash-H done wall={wall}s", flush=True)
    return meters


def run_driver_luna(cells: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir = OUT["luna"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    batches = [cells[i : i + CELLS_PER_LUNA] for i in range(0, len(cells), CELLS_PER_LUNA)]
    print(f"[{now_aest()}] Luna start n={len(cells)} batches={len(batches)}", flush=True)
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_LUNA) as ex:
        futs = {ex.submit(run_luna_batch, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            results.append(res)
            print(
                f"[{now_aest()}] Luna batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s "
                f"err={res.get('error')}",
                flush=True,
            )
    by_id: dict[str, Any] = {}
    for res in results:
        by_id.update(res.get("by_id") or {})
    wall = round(time.time() - t0, 1)
    grid = {
        "generated_at": now_aest(),
        "driver": "luna",
        "model": LUNA_MODEL,
        "n_cells": len(cells),
        "n_batches": len(batches),
        "framings": sorted({c["framing"] for c in cells}),
        "soft_standard_hold": True,
    }
    (out_dir / "grid.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    meters = write_results(
        "luna",
        cells,
        by_id,
        out_dir,
        {
            "wall_s": wall,
            "n_batches": len(batches),
            "batch_elapsed_sum_s": round(sum(r["elapsed_s"] for r in results), 1),
            "model": LUNA_MODEL,
        },
    )
    print(f"[{now_aest()}] Luna done wall={wall}s", flush=True)
    return meters


def main() -> int:
    for d in OUT.values():
        d.mkdir(parents=True, exist_ok=True)
        (d / "raw").mkdir(exist_ok=True)
    MIRROR.mkdir(parents=True, exist_ok=True)

    packs = load_packs()
    if not packs:
        print("ERROR: no snapshots in", SNAP_DIR, file=sys.stderr)
        return 2
    print(f"[{now_aest()}] loaded packs={len(packs)}", flush=True)

    ts_cells = build_cells(packs, "typesafe", TARGET_TYPESAFE)
    flash_cells = build_cells(packs, "flash", TARGET_FLASH)
    luna_cells = build_cells(packs, "luna", TARGET_LUNA)
    print(
        f"[{now_aest()}] cell targets ts={len(ts_cells)} flash={len(flash_cells)} luna={len(luna_cells)}",
        flush=True,
    )

    # Persist cell plans
    (OUT["typesafe"] / "cells_plan.json").write_text(
        json.dumps({"n": len(ts_cells), "cell_ids": [c["cell_id"] for c in ts_cells]}, indent=2) + "\n"
    )
    (OUT["flash"] / "cells_plan.json").write_text(
        json.dumps({"n": len(flash_cells), "cell_ids": [c["cell_id"] for c in flash_cells]}, indent=2) + "\n"
    )
    (OUT["luna"] / "cells_plan.json").write_text(
        json.dumps({"n": len(luna_cells), "cell_ids": [c["cell_id"] for c in luna_cells]}, indent=2) + "\n"
    )

    drivers = [d.strip() for d in (os.environ.get("MULTI_DRIVERS") or "typesafe,flash,luna").split(",") if d.strip()]
    summary: dict[str, Any] = {
        "generated_at": now_aest(),
        "soft_standard_hold": True,
        "hooks_unlock": False,
        "product_unlock": False,
        "n_packs": len(packs),
        "drivers": {},
    }

    # Run TypeSafe and Flash in parallel processes via threads of drivers;
    # Luna after or parallel if requested — all three parallel for speed.
    def _run(name: str):
        try:
            if name == "typesafe":
                return name, run_driver_typesafe(ts_cells)
            if name == "flash":
                return name, run_driver_flash(flash_cells)
            if name == "luna":
                return name, run_driver_luna(luna_cells)
            raise ValueError(name)
        except Exception as e:
            return name, {
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-1500:],
                "driver": name,
            }

    with ThreadPoolExecutor(max_workers=max(1, len(drivers))) as ex:
        futs = [ex.submit(_run, d) for d in drivers]
        for fut in as_completed(futs):
            name, meters = fut.result()
            summary["drivers"][name] = {
                "n_cells": meters.get("n_cells"),
                "parse_miss_cells": meters.get("parse_miss_cells"),
                "error_count": meters.get("error_count"),
                "fire_count": meters.get("fire_count"),
                "wall_s": meters.get("wall_s"),
                "leak_hits": len(meters.get("prompt_leak_spotcheck_hits") or []),
                "usage_tokens_rough": meters.get("usage_tokens_rough"),
                "error": meters.get("error"),
                "framing_cell_counts": meters.get("framing_cell_counts"),
            }

    summary_path = BATCH / "MULTI-DRIVER-SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
