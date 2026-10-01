#!/usr/bin/env python3
"""Wave-0 batch-002 — decontaminated offline Flash trials (Opus R1–R3).

- No T / progress-frac / full-session length in judge payload (R1)
- No length-derived outcome tags (R2)
- Fixed T-independent schedule; hazard/at-risk framing (R3)
Soft Standard HOLD. No TypeSafe. Do not kill pts/5 OpenCode TUI.
"""
from __future__ import annotations

import hashlib
import json
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
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
MIRROR = Path("/tmp/2026-10-02-interception-trials-batch-002")
INVENTORY = REPO / "docs/lab/RESEARCH/2026-10-02-local-session-inventory"
PROG_PROOFS = REPO / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
AEST = ZoneInfo("Australia/Brisbane")

sys.path.insert(0, str(PROG_PROOFS))
from snapshot_state import build_hybrid_v0, shrink_hybrid_state, state_json_len  # noqa: E402
from turn_index import index_transcript  # noqa: E402

FLASH_MODEL = "deepseek/deepseek-flash"
CELLS_PER_FLASH = 10
MAX_PARALLEL_FLASH = 3
TARGET_CELLS = 240

# R3: same schedule every session (eligibility via survival only)
FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)

QUESTION_VARIANTS = {
    "continue_excessively": (
        "Will this job likely continue excessively from this checkpoint "
        "if uninterrupted? Judge only the snapshot."
    ),
    "steer_now": (
        "Is NOW a useful time to steer toward stopping, without truncating "
        "productive development or near-done closing work?"
    ),
    "productive_arc": (
        "Is there evidence of a steady productive build rather than thrash "
        "or frozen narration?"
    ),
    "near_done": (
        "Does the snapshot suggest closing / validation / delivery "
        "(near-done) rather than mid-runaway?"
    ),
    "thrash_bundle": (
        "Do compaction, rereads, and weak new output form a thrash bundle?"
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
            "fire_offset_turns in {-15,0,15,30} is DIAGNOSTIC only."
        ),
    },
}

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
    ("hybrid_v0", "continue_excessively", "four_class"),
    ("stats_only", "defer_recheck", "rating_plus_offset"),
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

    for r in [
        {
            "harness": "opencode",
            "project": "llama.cpp",
            "path": "sqlite:/home/codyh/.local/share/opencode/opencode.db#session/ses_1a6280e0dffeW0FRROYzKNpNV8",
            "length_metric": 109,
            "norm_length": 54.5,
            "title": "high RAM when idle",
            "session_id": "ses_1a6280e0dffeW0FRROYzKNpNV8",
        },
        {
            "harness": "opencode",
            "project": "free-frontier",
            "path": "sqlite:/home/codyh/.local/share/opencode/opencode.db#session/ses_42080a163ffer9OHMlFrbh7mID",
            "length_metric": 85,
            "norm_length": 42.5,
            "title": "oldest free-frontier",
            "session_id": "ses_42080a163ffer9OHMlFrbh7mID",
        },
        {
            "harness": "codex",
            "project": "garcia-music",
            "path": "/home/codyh/.codex/sessions/2026/04/07/rollout-2026-04-07T04-10-34-019d6622-9229-7f50-85dc-dfcf9b64e188.jsonl",
            "length_metric": 59,
            "norm_length": 59,
        },
        {
            "harness": "codex",
            "project": "lemmings",
            "path": "/home/codyh/.codex/sessions/2026/04/16/rollout-2026-04-16T15-02-55-019d96d1-0a25-73c1-b327-66727ffc00dc.jsonl",
            "length_metric": 20,
            "norm_length": 20,
        },
        {
            "harness": "cursor",
            "project": "garcia-music",
            "path": "/home/codyh/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26/b784e674-febe-4eb4-a2ca-ea2b1c5f7f26.jsonl",
            "length_metric": 61,
            "norm_length": 61,
        },
        {
            "harness": "cursor",
            "project": "garcia-music",
            "path": "/home/codyh/.cursor/projects/home-codyh-workspace-garcia-music/agent-transcripts/87e55915-f481-4dcc-8b6a-54c69392fcf9/87e55915-f481-4dcc-8b6a-54c69392fcf9.jsonl",
            "length_metric": 49,
            "norm_length": 49,
        },
    ]:
        add(r, "flash_qualitative_18")
    return rows


def build_cc_pack(path: Path) -> dict[str, Any]:
    indexed = index_transcript(path)
    T = indexed.T
    schedule = {"first_at": FIXED_SCHEDULE[0], "interval": 15, "fixed": list(FIXED_SCHEDULE)}
    prior = None
    snaps = []
    reached = []
    never = []
    for cp in FIXED_SCHEDULE:
        if T < cp:
            never.append(cp)
            continue
        reached.append(cp)
        raw = build_hybrid_v0(
            indexed, cp, first_at=FIXED_SCHEDULE[0], interval=15, prior=prior
        )
        # overwrite schedule stamp to disclose fixed schedule not H1-only story
        raw["schedule"] = dict(schedule)
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
        "T_eligibility_only": T,
        "schedule": schedule,
        "checkpoints": snaps,
        "reached_checkpoints": reached,
        "never_reached_checkpoints": never,
        "window_status": "unidentified",
    }


def lite_prefix_state(path: Path, harness: str, inventory_T: int, cp: int) -> dict[str, Any]:
    """Prefix-local lite counts only — stop reading after roughly cp-proportional scan.

    For non-CC we lack api_turn index; approximate by reading the first
    fraction of lines without storing full-session totals in state.
    """
    n_target_lines = None
    # rough: read until we've seen ~cp userish-or-turn-like events, else first chunk
    roles: dict[str, int] = {}
    userish = 0
    lines_read = 0
    with path.open() as f:
        for line in f:
            lines_read += 1
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = str(o.get("type") or "")
            roles[t] = roles.get(t, 0) + 1
            msg = o.get("message")
            if t in {"user", "user_message", "human"}:
                userish += 1
            if isinstance(msg, dict) and msg.get("role") == "user":
                userish += 1
            if harness == "codex" and t == "turn_context":
                userish += 1
            # stop once prefix proxy reaches checkpoint
            proxy = userish if userish else sum(roles.values())
            if proxy >= cp:
                break
            # safety cap
            if lines_read > 20000:
                break
    return {
        "checkpoint_turn": cp,
        "harness": harness,
        "evidence_class": "lite_prefix",
        "schedule": {
            "first_at": FIXED_SCHEDULE[0],
            "interval": 15,
            "fixed": list(FIXED_SCHEDULE),
        },
        "cumulative": {
            "api_turns": cp,
            "prefix_lines_read": lines_read,
            "prefix_role_histogram_top": dict(
                sorted(roles.items(), key=lambda x: -x[1])[:8]
            ),
            "prefix_userish_or_turn_proxy": userish,
            "note": "lite prefix-only; no full-session length fields",
        },
    }


def build_lite_pack(row: dict[str, Any]) -> dict[str, Any]:
    harness = row["harness"]
    path = row.get("path") or ""
    inv = int(row.get("length_metric") or row.get("norm_length") or 40)
    # eligibility T: inventory metric (not sent to judge)
    if harness == "opencode":
        T = max(20, int(float(row.get("norm_length") or inv // 2)))
        worker = (row.get("session_id") or "opencode")[:24]
        snaps = []
        reached, never = [], []
        for cp in FIXED_SCHEDULE:
            if T < cp:
                never.append(cp)
                continue
            reached.append(cp)
            # inventory-only lite without full sqlite body: prefix-synthetic from cp
            state = {
                "checkpoint_turn": cp,
                "harness": "opencode",
                "evidence_class": "lite_inventory_prefix",
                "project": row.get("project"),
                "title": row.get("title"),
                "schedule": {
                    "first_at": FIXED_SCHEDULE[0],
                    "interval": 15,
                    "fixed": list(FIXED_SCHEDULE),
                },
                "cumulative": {
                    "api_turns": cp,
                    "note": "opencode lite: checkpoint index only; no messages_full/T in state",
                },
            }
            snaps.append(
                {
                    "checkpoint": cp,
                    "prior": None,
                    "state_chars": state_json_len(state),
                    "shrink_steps": [],
                    "full_state": state,
                }
            )
        return {
            "harness": "opencode",
            "worker_id": worker,
            "path": path,
            "T_eligibility_only": T,
            "schedule": {"first_at": FIXED_SCHEDULE[0], "interval": 15, "fixed": list(FIXED_SCHEDULE)},
            "checkpoints": snaps,
            "reached_checkpoints": reached,
            "never_reached_checkpoints": never,
            "window_status": "unidentified",
        }

    p = Path(path)
    T = inv
    if harness == "codex":
        # inventory user_messages is the eligibility length, not response_item inflation
        T = inv
    snaps = []
    reached, never = [], []
    for cp in FIXED_SCHEDULE:
        if T < cp:
            never.append(cp)
            continue
        reached.append(cp)
        state = lite_prefix_state(p, harness, inv, cp)
        snaps.append(
            {
                "checkpoint": cp,
                "prior": None,
                "state_chars": state_json_len(state),
                "shrink_steps": [],
                "full_state": state,
            }
        )
    return {
        "harness": harness,
        "worker_id": p.stem[:24],
        "path": str(p),
        "T_eligibility_only": T,
        "schedule": {"first_at": FIXED_SCHEDULE[0], "interval": 15, "fixed": list(FIXED_SCHEDULE)},
        "checkpoints": snaps,
        "reached_checkpoints": reached,
        "never_reached_checkpoints": never,
        "window_status": "unidentified",
    }


def prepare_session_pack(row: dict[str, Any]) -> dict[str, Any] | None:
    harness = row.get("harness") or ""
    path = row.get("path") or ""
    try:
        if harness == "claude-code" and path and not str(path).startswith("sqlite:"):
            pack = build_cc_pack(Path(path))
        elif harness in {"opencode", "codex", "cursor"}:
            pack = build_lite_pack(row)
        else:
            return None
        pack["project"] = row.get("project")
        pack["corpus_source"] = row.get("corpus_source")
        pack["maps_family"] = "open-pajero-maps" in str(row.get("project") or "") or "pajero-maps" in str(path)
        return pack
    except Exception as e:
        return {"error": str(e), "path": path, "harness": harness, "trace": traceback.format_exc()[-500:]}


def cell_id(session_id: str, cp: int, state_v: str, q: str, rc: str) -> str:
    raw = f"b002|{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


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
    ):
        projected.pop(bad, None)
        cum = projected.get("cumulative")
        if isinstance(cum, dict):
            cum.pop(bad, None)
    return projected


def _make_cell(pack: dict[str, Any], snap: dict[str, Any], state_v: str, q: str, rc: str) -> dict[str, Any]:
    sid = pack["worker_id"]
    projected = project_state(snap["full_state"], state_v)
    if len(json.dumps(projected, ensure_ascii=False)) > 3500:
        projected = project_state(snap["full_state"], "stats_only")
        projected["truncated_from"] = state_v
    projected = _strip_leaks(projected)
    return {
        "cell_id": cell_id(sid, snap["checkpoint"], state_v, q, rc),
        "session_id": sid,
        "harness": pack["harness"],
        "project": pack.get("project"),
        "maps_family": pack.get("maps_family"),
        "corpus_source": pack.get("corpus_source"),
        "checkpoint": snap["checkpoint"],
        "state_variant": state_v,
        "question_variant": q,
        "response_class": rc,
        "state": projected,
        "question_text": QUESTION_VARIANTS[q],
        "response_class_spec": RESPONSE_CLASSES[rc],
        "window_status": "unidentified",
        "_T_eligibility_only": pack["T_eligibility_only"],
    }


def build_trial_cells(packs: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    """Cover FIXED_SCHEDULE breadth first (R3), then levers — avoid filling only t=first."""
    usable = [p for p in packs if "error" not in p and p.get("checkpoints")]
    usable = sorted(
        usable,
        key=lambda p: (
            0 if p.get("harness") == "claude-code" else 1 if p.get("harness") == "opencode" else 2,
            -int(p.get("T_eligibility_only") or 0),
        ),
    )
    # Primary levers for breadth; exploratory fill afterward
    primary = LEVER_COMBOS[:4]
    explor = LEVER_COMBOS[4:]

    # Round-robin over (session, checkpoint) with primary levers
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for pack in usable:
        for snap in pack["checkpoints"]:
            pairs.append((pack, snap))
    # sort pairs by checkpoint then harness diversity already in usable order
    pairs.sort(key=lambda x: (int(x[1]["checkpoint"]), 0 if x[0].get("harness")=="claude-code" else 1))

    cells: list[dict[str, Any]] = []
    # pass 1: one primary lever cycle across all pairs
    for state_v, q, rc in primary:
        for pack, snap in pairs:
            cells.append(_make_cell(pack, snap, state_v, q, rc))
            if len(cells) >= target:
                return cells
    # pass 2: exploratory levers
    for state_v, q, rc in explor:
        for pack, snap in pairs:
            cells.append(_make_cell(pack, snap, state_v, q, rc))
            if len(cells) >= target:
                return cells
    return cells


def extract_json_array(text: str) -> list[dict[str, Any]]:
    text = text.strip()
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


def flash_prompt(batch: list[dict[str, Any]]) -> str:
    slim = []
    for c in batch:
        slim.append(
            {
                "cell_id": c["cell_id"],
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
        "You are an offline interception policy-under-test (NOT gold; Soft Standard HOLD).\n"
        "Judge ONLY the provided prefix snapshot + question + response-class mapping.\n"
        "Do NOT infer final session length. Do NOT invent future turns or tool results.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"...","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating = steer-urgency 0..3. Apply response_class_map for fire.\n"
        f"CELLS ({len(slim)}):\n"
        + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx: int, batch: list[dict[str, Any]], raw_dir: Path) -> dict[str, Any]:
    prompt = flash_prompt(batch)
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
    }


def mirror_tree() -> None:
    MIRROR.mkdir(parents=True, exist_ok=True)
    (MIRROR / "raw").mkdir(exist_ok=True)
    (MIRROR / "snapshots").mkdir(exist_ok=True)
    for name in (
        "PROTOCOL.md",
        "LEAKAGE-AUDIT.md",
        "METERS.md",
        "meters.json",
        "grid.json",
        "results.jsonl",
    ):
        src = BATCH / name
        if src.exists():
            (MIRROR / name).write_bytes(src.read_bytes())


def main() -> int:
    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "raw").mkdir(exist_ok=True)
    (BATCH / "snapshots").mkdir(exist_ok=True)
    MIRROR.mkdir(parents=True, exist_ok=True)
    (MIRROR / "raw").mkdir(exist_ok=True)
    (MIRROR / "snapshots").mkdir(exist_ok=True)

    corpus = load_corpus()
    cc = [r for r in corpus if r.get("harness") == "claude-code"][:14]
    other = [r for r in corpus if r.get("harness") != "claude-code"][:8]
    selected = cc + other

    packs, pack_errors = [], []
    for row in selected:
        pack = prepare_session_pack(row)
        if pack is None:
            continue
        if "error" in pack:
            pack_errors.append(pack)
            continue
        packs.append(pack)
        # snapshots on disk omit judge-forbidden eligibility from nested full_state already
        slim = {
            **{k: v for k, v in pack.items() if k != "checkpoints"},
            "checkpoints": pack["checkpoints"],
        }
        sp = BATCH / "snapshots" / f"{pack['worker_id']}.json"
        sp.write_text(json.dumps(slim, indent=2) + "\n")
        (MIRROR / "snapshots" / sp.name).write_text(sp.read_text())

    cells = build_trial_cells(packs, TARGET_CELLS)

    # survival table
    n_at_risk = {t: 0 for t in FIXED_SCHEDULE}
    n_never = {t: 0 for t in FIXED_SCHEDULE}
    for p in packs:
        T = int(p["T_eligibility_only"])
        for t in FIXED_SCHEDULE:
            if T >= t:
                n_at_risk[t] += 1
            else:
                n_never[t] += 1

    grid = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "Wave-0",
        "score_ready_path": True,
        "protocol_decontaminated_r1_r2_r3": True,
        "fixed_schedule": list(FIXED_SCHEDULE),
        "target_cells": TARGET_CELLS,
        "n_cells": len(cells),
        "n_sessions": len(packs),
        "n_sessions_independent": len(packs),
        "n_variants": len(cells),
        "lever_combos": [
            {"state": a, "question": b, "response_class": c} for a, b, c in LEVER_COMBOS
        ],
        "window_status": "unidentified",
        "typesafe_used": False,
        "soft_standard_hold": True,
        "flash_role": "policy-under-test",
        "maps_concentration": {
            "sessions_maps": sum(1 for p in packs if p.get("maps_family")),
            "sessions_total": len(packs),
            "cells_maps": sum(1 for c in cells if c.get("maps_family")),
            "cells_total": len(cells),
        },
        "n_at_risk": n_at_risk,
        "n_never_reached": n_never,
        "pack_errors": pack_errors,
    }
    (BATCH / "grid.json").write_text(json.dumps(grid, indent=2) + "\n")

    batches = [cells[i : i + CELLS_PER_FLASH] for i in range(0, len(cells), CELLS_PER_FLASH)]
    print(
        f"[{now_aest()}] batch-002 sessions={len(packs)} cells={len(cells)} "
        f"flash_batches={len(batches)} schedule={FIXED_SCHEDULE}",
        flush=True,
    )

    flash_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FLASH) as ex:
        futs = {
            ex.submit(run_flash_batch, i, batch, BATCH / "raw"): i
            for i, batch in enumerate(batches)
        }
        for fut in as_completed(futs):
            res = fut.result()
            flash_results.append(res)
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
    harness_counts: dict[str, int] = {}
    fire_by_cp: dict[int, list[bool]] = {t: [] for t in FIXED_SCHEDULE}
    rating_hist: dict[str, int] = {}
    abstain = 0
    parse_miss = 0
    fire_count = 0

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
            fire = None
            if ans:
                fire = bool(ans.get("fire")) if "fire" in ans else (
                    rating_i is not None and rating_i >= 2
                )
            if fire:
                fire_count += 1
            label = ans.get("label")
            if label == "uncertain" or (rating_i == 1 and c["response_class"] == "four_class"):
                abstain += 1
            if rating_i is not None:
                rating_hist[str(rating_i)] = rating_hist.get(str(rating_i), 0) + 1
            cp = int(c["checkpoint"])
            if fire is not None:
                fire_by_cp.setdefault(cp, []).append(bool(fire))
            harness_counts[c["harness"]] = harness_counts.get(c["harness"], 0) + 1
            row = {
                "cell_id": c["cell_id"],
                "session_id": c["session_id"],
                "harness": c["harness"],
                "project": c.get("project"),
                "maps_family": c.get("maps_family"),
                "corpus_source": c.get("corpus_source"),
                "checkpoint": cp,
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
                "outcome_tag": None,  # R2: no length-derived tags
                "judge_role": "policy-under-test",
                "model": FLASH_MODEL,
                "typesafe": False,
                "soft_standard_hold": True,
                "batch": "batch-002",
                "wave": "Wave-0",
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

    # prompt leakage spot-check
    leak_hits = []
    for prompt in (BATCH / "raw").glob("batch-*-prompt.txt"):
        txt = prompt.read_text(encoding="utf-8", errors="replace")
        for needle in (
            "T_observed_session",
            "approx_progress_frac",
            "userish_count_full_session",
            "T_eligibility",
            "short_natural",
            "long_runawayish",
            "ideal_window",
        ):
            if needle in txt:
                leak_hits.append({"file": prompt.name, "needle": needle})

    meters = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "Wave-0",
        "meters_class": "score-ready-path-diagnostics",
        "score_ready_fp_miss_board": False,
        "reason_fp_miss_board_false": (
            "window_status=unidentified; length-derived windows forbidden (R2). "
            "Diagnostic fire rates among at-risk sessions only."
        ),
        "protocol_fixes": ["R1_no_T_in_prompt_or_state", "R2_non_length_outcome_sheet", "R3_fixed_schedule_hazard"],
        "soft_standard_hold": True,
        "typesafe_used": False,
        "hooks_unlock": False,
        "n_sessions_independent": len(packs),
        "n_variants": len(cells),
        "n_flash_batches": len(flash_results),
        "flash_model": FLASH_MODEL,
        "flash_role": "policy-under-test",
        "flash_total_elapsed_s": round(sum(r["elapsed_s"] for r in flash_results), 1),
        "parse_miss_cells": parse_miss,
        "fire_count": fire_count,
        "abstain_approx": abstain,
        "rating_hist": rating_hist,
        "harness_cell_counts": harness_counts,
        "maps_concentration": grid["maps_concentration"],
        "fixed_schedule": list(FIXED_SCHEDULE),
        "n_at_risk": n_at_risk,
        "n_never_reached": n_never,
        "fire_rate_among_at_risk_cells": fire_rate_at_risk,
        "prompt_leak_spotcheck_hits": leak_hits,
        "luna_used": False,
        "paths": {"batch": str(BATCH), "mirror": str(MIRROR)},
    }
    (BATCH / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")

    md = []
    md.append("# METERS — interception trials batch-002 (Wave-0)\n")
    md.append(f"**Generated:** {meters['generated_at']}\n")
    md.append(
        "**Meters class:** score-ready-path **diagnostics** "
        "(clean inputs + fixed schedule). "
        "**NOT** a length-window FP/miss scoreboard — `window_status=unidentified` (R2).\n"
    )
    md.append("**Soft Standard HOLD** — TypeSafe: **no**. Hooks: **no**. Luna: **no**.\n")
    md.append("## Protocol fixes vs batch-001\n")
    md.append("- R1: no `T_observed_session` / progress-frac / full-session length in prompt or state")
    md.append("- R2: no `runaway_hit` / `near_done_fp` from `f(T)`; outcome sheet unidentified")
    md.append(f"- R3: fixed schedule `{list(FIXED_SCHEDULE)}`; at-risk / never-reached reported\n")
    md.append("## Counts\n")
    md.append(f"- n_sessions_independent: **{len(packs)}**")
    md.append(f"- n_variants (cells): **{len(cells)}**")
    md.append(f"- Flash batches: **{len(flash_results)}**; wall-sum **{meters['flash_total_elapsed_s']}s**")
    md.append(f"- Parse-miss: **{parse_miss}**; fire_count: **{fire_count}**")
    md.append(f"- Prompt leak spotcheck hits: **{len(leak_hits)}**\n")
    md.append("## Harness mix (cells)\n")
    for k, v in sorted(harness_counts.items()):
        md.append(f"- `{k}`: {v}")
    mc = grid["maps_concentration"]
    md.append(
        f"\n## Maps concentration\n- sessions {mc['sessions_maps']}/{mc['sessions_total']}; "
        f"cells {mc['cells_maps']}/{mc['cells_total']}\n"
    )
    md.append("## Survival (R3)\n")
    md.append("| t | n_at_risk | n_never_reached | fire_rate among cells at t |")
    md.append("|---|-----------|-----------------|------------------------------|")
    for t in FIXED_SCHEDULE:
        fr = fire_rate_at_risk.get(str(t), {})
        md.append(
            f"| {t} | {n_at_risk[t]} | {n_never[t]} | {fr.get('fire_rate')} (n={fr.get('n')}) |"
        )
    md.append("\n## Rating hist\n")
    for k, v in sorted(rating_hist.items()):
        md.append(f"- rating {k}: {v}")
    md.append("\n## Paths\n")
    md.append(f"- `{BATCH}`")
    md.append(f"- mirror `{MIRROR}`\n")
    md.append("## Ready for WSM\n")
    md.append(
        f"yes — Wave-0 batch-002 decontaminated path live; "
        f"{len(cells)} cells / {len(packs)} sessions; "
        f"leak_spotcheck_hits={len(leak_hits)}; "
        "FP/miss board **not** claimed (windows unidentified); "
        "TypeSafe unused; Soft Standard HOLD.\n"
    )
    (BATCH / "METERS.md").write_text("\n".join(md) + "\n")

    # update evidence log
    elog = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/EVIDENCE-LOG.md"
    if elog.exists():
        txt = elog.read_text()
        line = (
            f"| batch-002 | Wave-0 | score-ready-path diagnostics "
            f"(FP/miss board deferred; windows unidentified) | {len(packs)} | {len(cells)} | "
            f"R1–R3 decontaminated. leak_hits={len(leak_hits)}. |\n"
        )
        if "batch-002 | Wave-0 | *in progress" in txt:
            txt = txt.replace(
                "| batch-002 | Wave-0 | *in progress / score-ready path* | TBD | TBD | Protocol decontaminated: no T-in-prompt/state, T-independent schedule, non-length outcome sheet. |\n",
                line,
            )
            elog.write_text(txt)

    mirror_tree()
    print(
        json.dumps(
            {
                "ok": True,
                "n_sessions": len(packs),
                "n_cells": len(cells),
                "leak_hits": len(leak_hits),
                "fire_count": fire_count,
                "typesafe_used": False,
                "meters_class": meters["meters_class"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
