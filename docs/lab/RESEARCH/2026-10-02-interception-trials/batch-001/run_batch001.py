#!/usr/bin/env python3
"""Offline Jev lever trials batch-001 — Flash primary, no TypeSafe.

Soft Standard HOLD. Does not kill long-lived OpenCode TUI.
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path("/home/codyh/workspace/workflow-plugin")
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-001"
MIRROR = Path("/tmp/2026-10-02-interception-trials-batch-001")
INVENTORY = REPO / "docs/lab/RESEARCH/2026-10-02-local-session-inventory"
PROG_PROOFS = REPO / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
AEST = ZoneInfo("Australia/Brisbane")

sys.path.insert(0, str(PROG_PROOFS))
from snapshot_state import (  # noqa: E402
    build_hybrid_v0,
    shrink_hybrid_state,
    state_json_len,
)
from turn_index import checkpoints, index_transcript, worker_id_from_path  # noqa: E402

FLASH_MODEL = "deepseek/deepseek-flash"
CELLS_PER_FLASH = 10
MAX_PARALLEL_FLASH = 3
# Target tens–low hundreds; raise if capacity
TARGET_CELLS = 240

STATE_VARIANTS = ("stats_only", "hybrid_v0", "stats_plus_delta", "compact_focus")
QUESTION_VARIANTS = {
    "continue_excessively": (
        "Will this job likely continue excessively from this checkpoint "
        "(toward a long runaway) if uninterrupted?"
    ),
    "steer_now": (
        "Is NOW a useful time to steer the agent toward stopping, without "
        "truncating productive development or near-done closing work?"
    ),
    "productive_arc": (
        "Is there evidence of a steady productive build (mutations, narrowing "
        "decisions) rather than thrash or frozen narration?"
    ),
    "near_done": (
        "Does the snapshot suggest closing / validation / delivery phase "
        "(near-done) rather than mid-runaway?"
    ),
    "thrash_bundle": (
        "Do compaction slope, rereads, and weak new output form a thrash bundle?"
    ),
    "defer_recheck": (
        "Should interception DEFER and re-check ~15 turns later instead of firing now?"
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
            "Also set fire_offset_turns in {-15,0,15,30} as suggested delay before steer."
        ),
    },
}

# Stratified lever combos (multi-approach; not thin single framing)
LEVER_COMBOS: list[tuple[str, str, str]] = [
    ("stats_only", "continue_excessively", "likert_0_3"),
    ("stats_only", "steer_now", "binary_fire"),
    ("stats_only", "thrash_bundle", "four_class"),
    ("hybrid_v0", "steer_now", "likert_0_3"),
    ("hybrid_v0", "near_done", "four_class"),
    ("hybrid_v0", "defer_recheck", "binary_fire"),
    ("stats_plus_delta", "productive_arc", "likert_0_3"),
    ("stats_plus_delta", "continue_excessively", "rating_plus_offset"),
    ("compact_focus", "thrash_bundle", "binary_fire"),
    ("compact_focus", "steer_now", "four_class"),
    ("hybrid_v0", "continue_excessively", "four_class"),  # exploratory
    ("stats_only", "defer_recheck", "rating_plus_offset"),  # exploratory
]


def now_aest() -> str:
    return datetime.now(AEST).strftime("%Y-%m-%d %H:%M:%S AEST")


def shape_bucket(T: int) -> str:
    if T < 90:
        return "short_natural"
    if T < 160:
        return "mid"
    return "long_runawayish"


def ideal_window(T: int) -> tuple[int, int] | None:
    b = shape_bucket(T)
    if b == "short_natural":
        return None
    if b == "mid":
        return (max(60, T - 50), max(max(60, T - 50), T - 15))
    return (max(75, T - 90), max(max(75, T - 90), T - 30))


def score_cell(T: int, checkpoint: int, fire: bool) -> str:
    b = shape_bucket(T)
    win = ideal_window(T)
    if b == "short_natural":
        return "near_done_fp" if fire else "defer_ok"
    assert win is not None
    lo, hi = win
    if fire:
        if checkpoint > T - 20:
            return "near_done_fp"
        if checkpoint < lo:
            return "premature"
        if lo <= checkpoint <= hi:
            return "runaway_hit"
        return "runaway_hit" if checkpoint <= hi + 15 else "near_done_fp"
    # defer
    if b == "long_runawayish" and checkpoint >= lo:
        return "runaway_miss_candidate"
    return "defer_ok"


def load_corpus() -> list[dict[str, Any]]:
    compact = json.loads((INVENTORY / "stats-compact.json").read_text())
    det = compact["deterministic_shortlist"]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(r: dict[str, Any], source: str) -> None:
        path = r.get("path") or ""
        key = path or r.get("session_id") or ""
        if not key or key in seen:
            return
        seen.add(key)
        rows.append({**r, "corpus_source": source})

    for r in det:
        add(r, "deterministic_30")

    # Flash qualitative extras (paths from SHORTLIST) — diversity
    flash_extra = [
        {
            "harness": "opencode",
            "project": "llama.cpp",
            "path": "sqlite:/home/codyh/.local/share/opencode/opencode.db#session/ses_1a6280e0dffeW0FRROYzKNpNV8",
            "length_metric": 109,
            "length_metric_name": "messages",
            "norm_length": 54.5,
            "title": "high RAM when idle",
            "session_id": "ses_1a6280e0dffeW0FRROYzKNpNV8",
        },
        {
            "harness": "opencode",
            "project": "free-frontier",
            "path": "sqlite:/home/codyh/.local/share/opencode/opencode.db#session/ses_42080a163ffer9OHMlFrbh7mID",
            "length_metric": 85,
            "length_metric_name": "messages",
            "norm_length": 42.5,
            "title": "oldest free-frontier",
            "session_id": "ses_42080a163ffer9OHMlFrbh7mID",
        },
        {
            "harness": "codex",
            "project": "garcia-music",
            "path": "/home/codyh/.codex/sessions/2026/04/07/rollout-2026-04-07T04-10-34-019d6622-9229-7f50-85dc-dfcf9b64e188.jsonl",
            "length_metric": 59,
            "length_metric_name": "user_messages",
            "norm_length": 59,
        },
        {
            "harness": "codex",
            "project": "lemmings",
            "path": "/home/codyh/.codex/sessions/2026/04/16/rollout-2026-04-16T15-02-55-019d96d1-0a25-73c1-b327-66727ffc00dc.jsonl",
            "length_metric": 20,
            "length_metric_name": "user_messages",
            "norm_length": 20,
        },
        {
            "harness": "cursor",
            "project": "garcia-music",
            "path": "/home/codyh/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26.jsonl",
            "length_metric": 61,
            "length_metric_name": "user_turns",
            "norm_length": 61,
        },
        {
            "harness": "cursor",
            "project": "garcia-music",
            "path": "/home/codyh/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/87e55915-f481-4dcc-8b6a-54c69392fcf9/87e55915-f481-4dcc-8b6a-54c69392fcf9.jsonl",
            "length_metric": 49,
            "length_metric_name": "user_turns",
            "norm_length": 49,
        },
    ]
    for r in flash_extra:
        add(r, "flash_qualitative_18")

    # Prefer longer: sort by norm_length desc
    rows.sort(key=lambda x: float(x.get("norm_length") or x.get("length_metric") or 0), reverse=True)
    return rows


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
    # hybrid_v0: keep brief + short tail
    out = {
        "checkpoint_turn": full.get("checkpoint_turn"),
        "schedule": full.get("schedule"),
        "brief_anchor": (full.get("brief_anchor") or "")[:300],
        "cumulative": cum,
        "delta_since_prior": full.get("delta_since_prior") or {},
        "tail": (full.get("tail") or [])[-4:],
        "evidence_class": "hybrid_v0",
    }
    return out


def build_cc_snapshots(path: Path, max_cps: int = 5) -> dict[str, Any]:
    indexed = index_transcript(path)
    T = indexed.T
    if T >= 75:
        first_at, interval = 75, 15
    elif T >= 45:
        first_at, interval = max(30, T // 3), max(10, T // 5)
    else:
        first_at, interval = max(10, T // 2), max(5, T // 4)
    cps = checkpoints(first_at, interval, T)
    # Keep early + mid + late coverage, capped
    if len(cps) > max_cps:
        picks = [cps[0]]
        mid = cps[len(cps) // 2]
        late = cps[-1]
        # also one in ideal window if long
        win = ideal_window(T)
        if win:
            in_win = [c for c in cps if win[0] <= c <= win[1]]
            if in_win:
                picks.append(in_win[len(in_win) // 2])
        picks.extend([mid, late])
        # unique preserve order
        seen = set()
        cps2 = []
        for c in picks:
            if c not in seen:
                seen.add(c)
                cps2.append(c)
        # fill from schedule until max_cps
        for c in cps:
            if len(cps2) >= max_cps:
                break
            if c not in seen:
                cps2.append(c)
                seen.add(c)
        cps = sorted(cps2)

    prior = None
    snaps = []
    for cp in cps:
        raw = build_hybrid_v0(
            indexed, cp, first_at=first_at, interval=interval, prior=prior
        )
        shrunk, steps = shrink_hybrid_state(raw)
        state = shrunk if shrunk is not None else raw
        snaps.append(
            {
                "checkpoint": cp,
                "prior": prior,
                "state_chars": state_json_len(state),
                "shrink_steps": steps,
                "full_state": state,
            }
        )
        prior = cp
    return {
        "harness": "claude-code",
        "worker_id": indexed.worker_id,
        "path": str(path),
        "T": T,
        "schedule": {"first_at": first_at, "interval": interval},
        "checkpoints": snaps,
        "shape": shape_bucket(T),
        "ideal_window": ideal_window(T),
    }


def lite_jsonl_stats(path: Path, harness: str, inventory_T: int | float | None = None) -> dict[str, Any]:
    """Light parse for non-CC JSONL — counts only, no bodies in state."""
    n_lines = 0
    roles: dict[str, int] = {}
    userish = 0
    if inventory_T is not None:
        try:
            roles["_inventory_T"] = int(inventory_T)
        except Exception:
            pass
    with path.open() as f:
        for line in f:
            n_lines += 1
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = str(o.get("type") or o.get("role") or "")
            roles[t] = roles.get(t, 0) + 1
            if t in {"user", "user_message", "human"}:
                userish += 1
            msg = o.get("message")
            if isinstance(msg, dict) and msg.get("role") == "user":
                userish += 1
    # Prefer inventory length when provided via roles["_inventory_T"]
    inv_T = roles.pop("_inventory_T", None)
    if inv_T:
        T = int(inv_T)
    elif userish:
        T = userish
    elif harness == "codex":
        # rollout JSONL is tool-heavy; turn_context ≈ user turns better than response_item
        T = roles.get("turn_context") or max(20, n_lines // 40)
    else:
        T = max(roles.values() if roles else [n_lines // 4]) or 20
    # synthetic checkpoints
    if T >= 40:
        cps = sorted({max(10, T // 4), max(15, T // 2), max(20, (3 * T) // 4), T})
    else:
        cps = sorted({max(5, T // 2), T})
    snaps = []
    for cp in cps:
        frac = cp / max(T, 1)
        state = {
            "checkpoint_turn": cp,
            "harness": harness,
            "evidence_class": "lite",
            "cumulative": {
                "api_turns": cp,
                "approx_progress_frac": round(frac, 3),
                "file_lines": n_lines,
                "role_histogram_top": dict(sorted(roles.items(), key=lambda x: -x[1])[:8]),
                "userish_count_full_session": userish,
                "T_observed": T,
                "note": "lite non-CC state; no chat bodies",
            },
        }
        snaps.append({"checkpoint": cp, "prior": None, "state_chars": state_json_len(state), "shrink_steps": [], "full_state": state})
    return {
        "harness": harness,
        "worker_id": path.stem[:24],
        "path": str(path),
        "T": T,
        "schedule": {"first_at": cps[0], "interval": max(1, (cps[-1] - cps[0]) // max(1, len(cps) - 1))},
        "checkpoints": snaps,
        "shape": shape_bucket(T),
        "ideal_window": ideal_window(T),
    }


def lite_opencode(row: dict[str, Any]) -> dict[str, Any]:
    T = int(row.get("length_metric") or row.get("norm_length") or 40)
    # treat messages/2 as rough turn proxy already in norm
    turn_proxy = max(20, int(float(row.get("norm_length") or T // 2)))
    cps = sorted({max(10, turn_proxy // 3), max(15, turn_proxy // 2), turn_proxy})
    snaps = []
    for cp in cps:
        state = {
            "checkpoint_turn": cp,
            "harness": "opencode",
            "evidence_class": "lite_inventory",
            "title": row.get("title"),
            "project": row.get("project"),
            "cumulative": {
                "api_turns": cp,
                "messages_full": T,
                "norm_length": row.get("norm_length"),
                "T_proxy": turn_proxy,
            },
        }
        snaps.append({"checkpoint": cp, "prior": None, "state_chars": state_json_len(state), "shrink_steps": [], "full_state": state})
    return {
        "harness": "opencode",
        "worker_id": (row.get("session_id") or "opencode")[:24],
        "path": row.get("path"),
        "T": turn_proxy,
        "schedule": {"first_at": cps[0], "interval": 15},
        "checkpoints": snaps,
        "shape": shape_bucket(turn_proxy),
        "ideal_window": ideal_window(turn_proxy),
        "maps_family": False,
    }


def prepare_session_pack(row: dict[str, Any]) -> dict[str, Any] | None:
    harness = row.get("harness") or ""
    path = row.get("path") or ""
    try:
        if harness == "claude-code" and path and not path.startswith("sqlite:"):
            pack = build_cc_snapshots(Path(path), max_cps=4)
        elif harness == "opencode" and path.startswith("sqlite:"):
            pack = lite_opencode(row)
        elif harness in {"codex", "cursor"} and path and Path(path).exists():
            inv_len = row.get("length_metric") or row.get("norm_length")
            pack = lite_jsonl_stats(Path(path), harness, inventory_T=inv_len)
        else:
            return None
        pack["project"] = row.get("project")
        pack["corpus_source"] = row.get("corpus_source")
        pack["maps_family"] = "open-pajero-maps" in str(row.get("project") or "") or "pajero-maps" in path
        pack["inventory_rank"] = row.get("rank")
        pack["norm_length"] = row.get("norm_length") or row.get("length_metric")
        return pack
    except Exception as e:
        return {"error": str(e), "path": path, "harness": harness, "trace": traceback.format_exc()[-500:]}


def cell_id(session_id: str, cp: int, state_v: str, q: str, rc: str) -> str:
    raw = f"{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def build_trial_cells(packs: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    """Stratify across sessions — round-robin so long outliers cannot fill the batch."""
    usable = [p for p in packs if "error" not in p and p.get("checkpoints")]
    if not usable:
        return []
    # Prefer longer, but keep harness diversity by soft interleave
    usable = sorted(
        usable,
        key=lambda p: (
            0 if p.get("harness") == "claude-code" else 1 if p.get("harness") == "opencode" else 2,
            -int(p.get("T") or 0),
        ),
    )
    # Precompute per-session candidate cells
    per_sess: list[list[dict[str, Any]]] = []
    for pack in usable:
        sid = pack["worker_id"]
        sess_cells: list[dict[str, Any]] = []
        for snap in pack["checkpoints"]:
            for state_v, q, rc in LEVER_COMBOS:
                cid = cell_id(sid, snap["checkpoint"], state_v, q, rc)
                projected = project_state(snap["full_state"], state_v)
                blob = json.dumps(projected, ensure_ascii=False)
                if len(blob) > 3500:
                    projected = project_state(snap["full_state"], "stats_only")
                    projected["truncated_from"] = state_v
                sess_cells.append(
                    {
                        "cell_id": cid,
                        "session_id": sid,
                        "harness": pack["harness"],
                        "project": pack.get("project"),
                        "maps_family": pack.get("maps_family"),
                        "corpus_source": pack.get("corpus_source"),
                        "T": pack["T"],
                        "shape": pack["shape"],
                        "ideal_window": pack.get("ideal_window"),
                        "checkpoint": snap["checkpoint"],
                        "state_variant": state_v,
                        "question_variant": q,
                        "response_class": rc,
                        "state": projected,
                        "question_text": QUESTION_VARIANTS[q],
                        "response_class_spec": RESPONSE_CLASSES[rc],
                    }
                )
        per_sess.append(sess_cells)

    # Round-robin take until target
    cells: list[dict[str, Any]] = []
    idxs = [0] * len(per_sess)
    while len(cells) < target:
        progressed = False
        for i, sess_cells in enumerate(per_sess):
            if idxs[i] >= len(sess_cells):
                continue
            cells.append(sess_cells[idxs[i]])
            idxs[i] += 1
            progressed = True
            if len(cells) >= target:
                break
        if not progressed:
            break
    return cells


def extract_json_array(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    # strip markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    # find array
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
    # try jsonl lines
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def flash_prompt(batch: list[dict[str, Any]]) -> str:
    slim = []
    for c in batch:
        slim.append(
            {
                "cell_id": c["cell_id"],
                "checkpoint": c["checkpoint"],
                "T_observed_session": c["T"],
                "shape_hint_withheld": True,
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
        "You are an offline interception-trial scorer (NOT gold). Soft Standard HOLD.\n"
        "For each cell, judge ONLY the provided state snapshot + question + response-class mapping.\n"
        "Do NOT use future turns. Do NOT invent tool results not in state.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"...","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating is steer-urgency 0=none .. 3=strong. Apply response_class_map for fire.\n"
        f"CELLS ({len(slim)}):\n"
        + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx: int, batch: list[dict[str, Any]], raw_dir: Path) -> dict[str, Any]:
    prompt = flash_prompt(batch)
    prompt_path = raw_dir / f"batch-{batch_idx:03d}-prompt.txt"
    out_path = raw_dir / f"batch-{batch_idx:03d}-stdout.txt"
    err_path = raw_dir / f"batch-{batch_idx:03d}-stderr.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "opencode",
        "run",
        "--model",
        FLASH_MODEL,
        "--format",
        "default",
        prompt,
    ]
    t0 = time.time()
    # stdin closed per convention
    proc = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd="/tmp",
        timeout=180,
    )
    elapsed = time.time() - t0
    out_path.write_text(proc.stdout or "", encoding="utf-8")
    err_path.write_text(proc.stderr or "", encoding="utf-8")
    parsed = extract_json_array(proc.stdout or "")
    by_id = {r.get("cell_id"): r for r in parsed if r.get("cell_id")}
    return {
        "batch_idx": batch_idx,
        "exit_code": proc.returncode,
        "elapsed_s": round(elapsed, 2),
        "n_cells": len(batch),
        "n_parsed": len(by_id),
        "by_id": by_id,
        "stdout_bytes": len(proc.stdout or ""),
        "prompt_bytes": len(prompt),
    }


def mirror_file(src: Path) -> None:
    MIRROR.mkdir(parents=True, exist_ok=True)
    dest = MIRROR / src.name
    if src.is_file():
        dest.write_bytes(src.read_bytes())


def main() -> int:
    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "raw").mkdir(exist_ok=True)
    (BATCH / "snapshots").mkdir(exist_ok=True)
    MIRROR.mkdir(parents=True, exist_ok=True)
    (MIRROR / "raw").mkdir(exist_ok=True)
    (MIRROR / "snapshots").mkdir(exist_ok=True)

    corpus = load_corpus()
    # Cap sessions for batch-001: longer first, ensure some non-CC
    cc = [r for r in corpus if r.get("harness") == "claude-code"][:14]
    other = [r for r in corpus if r.get("harness") != "claude-code"][:8]
    selected = cc + other

    packs = []
    pack_errors = []
    for row in selected:
        pack = prepare_session_pack(row)
        if pack is None:
            continue
        if "error" in pack:
            pack_errors.append(pack)
            continue
        packs.append(pack)
        snap_path = BATCH / "snapshots" / f"{pack['worker_id']}.json"
        # drop full_state tails excess for disk: keep projected-ready full_state
        slim_pack = {
            **{k: v for k, v in pack.items() if k != "checkpoints"},
            "checkpoints": [
                {
                    "checkpoint": s["checkpoint"],
                    "prior": s["prior"],
                    "state_chars": s["state_chars"],
                    "shrink_steps": s["shrink_steps"],
                    "full_state": s["full_state"],
                }
                for s in pack["checkpoints"]
            ],
        }
        snap_path.write_text(json.dumps(slim_pack, indent=2) + "\n", encoding="utf-8")
        (MIRROR / "snapshots" / snap_path.name).write_text(snap_path.read_text(), encoding="utf-8")

    cells = build_trial_cells(packs, TARGET_CELLS)
    grid = {
        "generated_at": now_aest(),
        "target_cells": TARGET_CELLS,
        "n_cells": len(cells),
        "n_sessions": len(packs),
        "state_variants": list(STATE_VARIANTS),
        "question_variants": list(QUESTION_VARIANTS),
        "response_classes": list(RESPONSE_CLASSES),
        "lever_combos": [{"state": a, "question": b, "response_class": c} for a, b, c in LEVER_COMBOS],
        "soft_standard_hold": True,
        "typesafe_used": False,
        "maps_concentration": {
            "sessions_maps": sum(1 for p in packs if p.get("maps_family")),
            "sessions_total": len(packs),
            "cells_maps": sum(1 for c in cells if c.get("maps_family")),
            "cells_total": len(cells),
        },
        "pack_errors": pack_errors,
    }
    (BATCH / "grid.json").write_text(json.dumps(grid, indent=2) + "\n")
    mirror_file(BATCH / "grid.json")

    # Batch cells for Flash
    batches = [cells[i : i + CELLS_PER_FLASH] for i in range(0, len(cells), CELLS_PER_FLASH)]
    flash_results: list[dict[str, Any]] = []
    print(f"[{now_aest()}] sessions={len(packs)} cells={len(cells)} flash_batches={len(batches)}", flush=True)

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FLASH) as ex:
        futs = {
            ex.submit(run_flash_batch, i, batch, BATCH / "raw"): i
            for i, batch in enumerate(batches)
        }
        for fut in as_completed(futs):
            res = fut.result()
            flash_results.append(res)
            # mirror raw
            for name in (
                f"batch-{res['batch_idx']:03d}-prompt.txt",
                f"batch-{res['batch_idx']:03d}-stdout.txt",
                f"batch-{res['batch_idx']:03d}-stderr.txt",
            ):
                src = BATCH / "raw" / name
                if src.exists():
                    (MIRROR / "raw" / name).write_bytes(src.read_bytes())
            print(
                f"[{now_aest()}] flash batch {res['batch_idx']} exit={res['exit_code']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s",
                flush=True,
            )

    by_id: dict[str, Any] = {}
    for res in flash_results:
        by_id.update(res.get("by_id") or {})

    results_path = BATCH / "results.jsonl"
    outcome_counts: dict[str, int] = {}
    harness_counts: dict[str, int] = {}
    fire_count = 0
    parse_miss = 0
    with results_path.open("w", encoding="utf-8") as out:
        for c in cells:
            ans = by_id.get(c["cell_id"]) or {}
            if not ans:
                parse_miss += 1
            rating = ans.get("rating")
            try:
                rating_i = int(rating) if rating is not None else None
            except Exception:
                rating_i = None
            fire = bool(ans.get("fire")) if "fire" in ans else (rating_i is not None and rating_i >= 2)
            if fire:
                fire_count += 1
            outcome = score_cell(int(c["T"]), int(c["checkpoint"]), fire) if ans or rating_i is not None else "parse_miss"
            if not ans and rating_i is None:
                outcome = "parse_miss"
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            harness_counts[c["harness"]] = harness_counts.get(c["harness"], 0) + 1
            row = {
                "cell_id": c["cell_id"],
                "session_id": c["session_id"],
                "harness": c["harness"],
                "project": c.get("project"),
                "maps_family": c.get("maps_family"),
                "corpus_source": c.get("corpus_source"),
                "T": c["T"],
                "shape": c["shape"],
                "ideal_window": c.get("ideal_window"),
                "checkpoint": c["checkpoint"],
                "state_variant": c["state_variant"],
                "question_variant": c["question_variant"],
                "response_class": c["response_class"],
                "label": ans.get("label"),
                "rating": rating_i,
                "fire": fire if ans else None,
                "fire_offset_turns": ans.get("fire_offset_turns"),
                "rationale": ans.get("rationale"),
                "outcome_tag": outcome,
                "judge": "flash",
                "model": FLASH_MODEL,
                "typesafe": False,
                "soft_standard_hold": True,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Session-level runaway miss rollup
    by_sess: dict[str, list[dict[str, Any]]] = {}
    for line in results_path.read_text().splitlines():
        r = json.loads(line)
        by_sess.setdefault(r["session_id"], []).append(r)
    sess_miss = 0
    sess_hit = 0
    sess_fp = 0
    for sid, rows in by_sess.items():
        T = rows[0]["T"]
        shape = rows[0]["shape"]
        fires = [r for r in rows if r.get("fire")]
        if shape == "long_runawayish":
            win = ideal_window(T)
            if win and any(win[0] <= r["checkpoint"] <= win[1] for r in fires):
                sess_hit += 1
            elif not fires:
                sess_miss += 1
            else:
                # fired but outside window
                if any(r["outcome_tag"] == "premature" for r in fires):
                    pass
                if not any(r["outcome_tag"] == "runaway_hit" for r in fires):
                    sess_miss += 1
        if any(r["outcome_tag"] == "near_done_fp" for r in rows):
            sess_fp += 1

    total_flash_s = sum(r["elapsed_s"] for r in flash_results)
    meters = {
        "generated_at": now_aest(),
        "batch": "batch-001",
        "soft_standard_hold": True,
        "typesafe_used": False,
        "hooks_unlock": False,
        "n_sessions": len(packs),
        "n_cells": len(cells),
        "n_flash_batches": len(flash_results),
        "flash_model": FLASH_MODEL,
        "flash_parallel": MAX_PARALLEL_FLASH,
        "cells_per_flash": CELLS_PER_FLASH,
        "flash_total_elapsed_s": round(total_flash_s, 1),
        "flash_parse_miss_cells": parse_miss,
        "fire_count": fire_count,
        "outcome_counts": outcome_counts,
        "harness_cell_counts": harness_counts,
        "maps_concentration": grid["maps_concentration"],
        "session_rollup": {
            "long_sessions_hit": sess_hit,
            "long_sessions_miss_or_outside": sess_miss,
            "sessions_with_any_near_done_fp_cell": sess_fp,
        },
        "luna_used": False,
        "paths": {
            "batch": str(BATCH),
            "mirror": str(MIRROR),
            "results": str(results_path),
            "protocol": str(BATCH / "PROTOCOL.md"),
        },
        "remaining_grid_note": (
            f"Full cartesian would be {len(STATE_VARIANTS)}×{len(QUESTION_VARIANTS)}×"
            f"{len(RESPONSE_CLASSES)}={len(STATE_VARIANTS)*len(QUESTION_VARIANTS)*len(RESPONSE_CLASSES)} "
            f"per checkpoint; batch-001 used {len(LEVER_COMBOS)} stratified combos × selected cps."
        ),
        "pack_errors_n": len(pack_errors),
    }
    (BATCH / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    mirror_file(BATCH / "meters.json")
    mirror_file(results_path)
    mirror_file(BATCH / "PROTOCOL.md")

    # METERS.md
    md = []
    md.append("# METERS — interception trials batch-001\n")
    md.append(f"**Generated:** {meters['generated_at']}\n")
    md.append("**Soft Standard HOLD** — TypeSafe: **no**. Hooks unlock: **no**. Luna: **no**.\n")
    md.append("## Counts\n")
    md.append(f"- Sessions: **{meters['n_sessions']}**")
    md.append(f"- Cells: **{meters['n_cells']}**")
    md.append(f"- Flash batches: **{meters['n_flash_batches']}** (parallel≤{MAX_PARALLEL_FLASH}, {CELLS_PER_FLASH}/call)")
    md.append(f"- Flash wall-sum: **{meters['flash_total_elapsed_s']}s**")
    md.append(f"- Parse-miss cells: **{parse_miss}**")
    md.append(f"- Fire count: **{fire_count}**\n")
    md.append("## Harness mix (cells)\n")
    for k, v in sorted(harness_counts.items()):
        md.append(f"- `{k}`: {v}")
    md.append("\n## Maps concentration\n")
    mc = grid["maps_concentration"]
    md.append(
        f"- Sessions maps-family: {mc['sessions_maps']}/{mc['sessions_total']}; "
        f"cells: {mc['cells_maps']}/{mc['cells_total']}\n"
    )
    md.append("## Outcome tags (cell-level)\n")
    for k, v in sorted(outcome_counts.items(), key=lambda x: -x[1]):
        md.append(f"- `{k}`: {v}")
    md.append("\n## Session rollup (long_runawayish)\n")
    md.append(f"- Hits (fire in ideal window): **{sess_hit}**")
    md.append(f"- Miss / outside-window longs: **{sess_miss}**")
    md.append(f"- Sessions with any near_done_fp cell: **{sess_fp}**\n")
    md.append("## Paths\n")
    md.append(f"- `{BATCH}`")
    md.append(f"- mirror `{MIRROR}`\n")
    md.append("## Remaining grid\n")
    md.append(meters["remaining_grid_note"] + "\n")
    md.append("## Ready for WSM\n")
    md.append(
        "yes — offline Flash lever grid burned on #96 shortlist; "
        f"{meters['n_cells']} cells / {meters['n_sessions']} sessions; "
        f"outcomes near_done_fp={outcome_counts.get('near_done_fp',0)}, "
        f"premature={outcome_counts.get('premature',0)}, "
        f"runaway_hit={outcome_counts.get('runaway_hit',0)}, "
        f"runaway_miss_candidate={outcome_counts.get('runaway_miss_candidate',0)}; "
        "TypeSafe unused; Soft Standard HOLD.\n"
    )
    (BATCH / "METERS.md").write_text("\n".join(md) + "\n")
    mirror_file(BATCH / "METERS.md")
    print(json.dumps({"ok": True, **{k: meters[k] for k in ('n_sessions','n_cells','outcome_counts','typesafe_used')}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
