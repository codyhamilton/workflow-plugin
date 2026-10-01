#!/usr/bin/env python3
"""batch-002 Flash+Luna SCALE wave — thousands bar (Soft HOLD).

Does NOT touch: typesafe/, flash-hframings/, luna/, flash-hframings-b/, luna-b/
Does NOT rewrite multidriver / flash_luna_b.

Expand:
- session count from inventory (stats.json sessions + det shortlist)
- denser windows: 45..120 step 5
- state-length + deterministic-trim variants
- more query packs / H1–H5 framings

Outputs: flash-scale/  luna-scale/  snapshots-dense/
cell_id salt: b002s|
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path(os.environ.get("WF_REPO", "/home/codyh/workspace/workflow-plugin"))
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
INVENTORY = REPO / "docs/lab/RESEARCH/2026-10-02-local-session-inventory"
PROG_PROOFS = REPO / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
SNAP_DENSE = BATCH / "snapshots-dense"
OUT = {
    "flash": BATCH / "flash-scale",
    "luna": BATCH / "luna-scale",
}
AEST = ZoneInfo("Australia/Brisbane")

sys.path.insert(0, str(PROG_PROOFS))
from snapshot_state import build_hybrid_v0, shrink_hybrid_state, state_json_len  # noqa: E402
from turn_index import index_transcript  # noqa: E402

FLASH_MODEL = "deepseek/deepseek-flash"
LUNA_MODEL = os.environ.get("WORKFLOW_LUNA_MODEL", "gpt-6-luna")

# Denser T-independent schedule (R3 still: same schedule every session; eligibility by survival)
DENSE_SCHEDULE = tuple(range(45, 121, 5))  # 16 points

TARGET_FLASH = int(os.environ.get("SCALE_FLASH_N", "2400"))
TARGET_LUNA = int(os.environ.get("SCALE_LUNA_N", "960"))
CELLS_PER_FLASH = 10
CELLS_PER_LUNA = 6
# Soft yield Claude/Sol: keep Flash/Luna modest parallel
MAX_PAR_FLASH = int(os.environ.get("SCALE_FLASH_PAR", "2"))
MAX_PAR_LUNA = int(os.environ.get("SCALE_LUNA_PAR", "1"))
MAX_SESSIONS = int(os.environ.get("SCALE_MAX_SESSIONS", "80"))

# Import framing/questions from multidriver (do not modify that file)
_spec = importlib.util.spec_from_file_location(
    "batch002_multidriver", BATCH / "run_batch002_multidriver.py"
)
_md = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_md)
FRAMINGS = _md.FRAMINGS
QUESTION_VARIANTS = dict(_md.QUESTION_VARIANTS)
RESPONSE_CLASSES = dict(_md.RESPONSE_CLASSES)
extract_json_array = _md.extract_json_array
prompt_leak_spotcheck = _md.prompt_leak_spotcheck

# Extra query packs (scale)
QUESTION_VARIANTS.update({
    "recheck_interval": (
        "If deferring, is a ~10–15 turn re-check interval still justified, or should fire happen sooner?"
    ),
    "closing_protect": (
        "Would firing now risk interrupting closing-stage validation or delivery value?"
    ),
    "scope_drift": (
        "Do recent turns drift from the brief into unrelated scope expansion?"
    ),
    "activity_without_value": (
        "Is there frequent tool activity without checkable progress (activity ≠ value)?"
    ),
    "tail_risk": (
        "Is the trajectory's continuation tail risk high enough to warrant steering toward stop?"
    ),
    "recoverable_stall": (
        "Does a stall look recoverable/valuable, such that deferral is better than fire?"
    ),
})

RESPONSE_CLASSES.update({
    "ternary_fire": {
        "labels": ["fire", "defer", "abstain"],
        "map": "fire=true only for fire. rating: fire→3, defer→0, abstain→1.",
    },
    "urgency_offset": {
        "labels": ["0", "1", "2", "3"],
        "map": (
            "rating 0-3 urgency. fire=true iff rating>=2. "
            "fire_offset_turns in {-20,-10,0,10,20} DIAGNOSTIC only."
        ),
    },
})


def now_aest() -> str:
    return datetime.now(AEST).strftime("%Y-%m-%d %H:%M:%S AEST")


def project_state(full: dict[str, Any], mode: str) -> dict[str, Any]:
    """Include base modes + state-length + deterministic-trim variants."""
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
    if mode == "state_length_short":
        # Minimal length-of-state: only a few cumulative counters
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "evidence_class": "state_length_short",
            "cumulative": {
                "api_turns": cum.get("api_turns"),
                "compaction_event_count": cum.get("compaction_event_count"),
                "reread_paths": cum.get("reread_paths"),
            },
        }
    if mode == "state_length_mid":
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "schedule": full.get("schedule"),
            "evidence_class": "state_length_mid",
            "cumulative": {
                k: cum.get(k)
                for k in (
                    "api_turns",
                    "peak_ctx_tokens",
                    "compaction_event_count",
                    "reread_paths",
                    "assistant_text_chars",
                    "tool_histogram",
                    "edit_count",
                    "bash_count",
                )
                if k in cum or True
            },
            "delta_since_prior": {
                k: (full.get("delta_since_prior") or {}).get(k)
                for k in ("api_turns", "compaction_event_count", "reread_paths", "assistant_text_chars")
            },
        }
    if mode == "deterministic_trim_v1":
        # Deterministic trim: drop tail text, keep structured counters + brief hash-length
        brief = (full.get("brief_anchor") or "")[:120]
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "schedule": full.get("schedule"),
            "evidence_class": "deterministic_trim_v1",
            "brief_anchor_trim": brief,
            "brief_anchor_len": len(full.get("brief_anchor") or ""),
            "cumulative": {
                k: cum.get(k)
                for k in (
                    "api_turns",
                    "peak_ctx_tokens",
                    "compaction_event_count",
                    "reread_paths",
                    "assistant_text_chars",
                    "tool_histogram",
                )
            },
            "tail_trim": (full.get("tail") or [])[-2:],
        }
    if mode == "deterministic_trim_v2":
        # Stronger trim: no brief/tail prose — counters + delta only
        return {
            "checkpoint_turn": full.get("checkpoint_turn"),
            "evidence_class": "deterministic_trim_v2",
            "cumulative": {
                k: cum.get(k)
                for k in (
                    "api_turns",
                    "peak_ctx_tokens",
                    "compaction_event_count",
                    "reread_paths",
                    "assistant_text_chars",
                    "tool_histogram",
                )
            },
            "delta_since_prior": full.get("delta_since_prior") or {},
        }
    # hybrid_v0 default
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
        "T", "T_observed", "T_observed_session", "approx_progress_frac",
        "userish_count_full_session", "messages_full", "T_proxy", "norm_length",
        "T_eligibility_only", "_T_eligibility_only",
    ):
        projected.pop(bad, None)
        cum = projected.get("cumulative")
        if isinstance(cum, dict):
            cum.pop(bad, None)
    return projected


# Large lever grid: framing × state × question × response (stratified list, not full cartesian dump)
STATE_VARIANTS = (
    "stats_only", "hybrid_v0", "stats_plus_delta", "compact_focus",
    "state_length_short", "state_length_mid",
    "deterministic_trim_v1", "deterministic_trim_v2",
)
SCALE_COMBOS: list[tuple[str, str, str, str]] = []
# Seed from multidriver combos
SCALE_COMBOS.extend(list(_md.LEVER_COMBOS))
# Expand with new states × framing-aligned questions
_extra_q = [
    ("H1", "recheck_interval"), ("H1", "closing_protect"), ("H1", "steer_now"),
    ("H2", "horizon_exceeded"), ("H2", "tail_risk"), ("H2", "continue_excessively"),
    ("H3", "plateau_sustained"), ("H3", "activity_without_value"), ("H3", "thrash_bundle"),
    ("H4", "boundary_overrun"), ("H4", "near_done"), ("H4", "closing_protect"),
    ("H5", "waste_intervene"), ("H5", "recoverable_stall"), ("H5", "scope_drift"),
]
_rcs = ("likert_0_3", "binary_fire", "four_class", "rating_plus_offset", "ternary_fire", "urgency_offset")
_states_cycle = list(STATE_VARIANTS)
i = 0
for framing, q in _extra_q:
    for rc in _rcs:
        st = _states_cycle[i % len(_states_cycle)]
        i += 1
        SCALE_COMBOS.append((framing, st, q, rc))
# Deduplicate
_seen = set()
_deduped = []
for c in SCALE_COMBOS:
    if c not in _seen:
        _seen.add(c)
        _deduped.append(c)
SCALE_COMBOS = _deduped


def cell_id(driver: str, framing: str, session_id: str, cp: int, state_v: str, q: str, rc: str) -> str:
    raw = f"b002s|{driver}|{framing}|{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_expanded_corpus() -> list[dict[str, Any]]:
    """Expand session count from inventory beyond Wave-0 22."""
    stats = json.loads((INVENTORY / "stats.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(r: dict[str, Any], source: str) -> None:
        path = r.get("path") or ""
        sid = r.get("session_id") or ""
        key = path or sid
        if not key or key in seen:
            return
        # eligibility proxy
        lm = r.get("length_metric") or r.get("norm_length") or r.get("user_turns") or r.get("messages") or 0
        try:
            lm_i = int(float(lm))
        except Exception:
            lm_i = 0
        # opencode messages often double-count; norm_length preferred
        if r.get("harness") == "opencode" and r.get("norm_length") is not None:
            try:
                lm_i = int(float(r["norm_length"]))
            except Exception:
                pass
        if lm_i < 45:
            return
        seen.add(key)
        rows.append({
            **r,
            "corpus_source": source,
            "length_metric": lm_i,
            "norm_length": r.get("norm_length") or lm_i,
        })

    for r in stats.get("deterministic_shortlist") or []:
        add(r, "deterministic_30")
    # Expand from full sessions list — prefer longer, diversify harness
    sessions = list(stats.get("sessions") or [])
    def sort_key(r):
        h = r.get("harness") or ""
        try:
            n = float(r.get("norm_length") or r.get("length_metric") or 0)
        except Exception:
            n = 0
        # prefer non-maps diversity slightly after length
        maps = 1 if "pajero-maps" in str(r.get("project") or "") or "pajero-maps" in str(r.get("path") or "") else 0
        return (-n, maps, h)
    sessions.sort(key=sort_key)
    # harness quotas
    quotas = {"claude-code": 40, "opencode": 20, "codex": 12, "cursor": 12}
    got = {k: 0 for k in quotas}
    for r in sessions:
        h = r.get("harness") or ""
        if h not in quotas:
            continue
        if got[h] >= quotas[h]:
            continue
        add(r, "inventory_expand")
        # recount via harness of accepted
        if any(x.get("path") == r.get("path") or x.get("session_id") == r.get("session_id") for x in rows[-1:]):
            got[h] = sum(1 for x in rows if x.get("harness") == h and x.get("corpus_source") == "inventory_expand")
            # also count det toward soft cap but allow det through already
        if len(rows) >= MAX_SESSIONS:
            break
    # top_by_harness fill
    compact = json.loads((INVENTORY / "stats-compact.json").read_text(encoding="utf-8"))
    for h, lst in (compact.get("top_by_harness") or {}).items():
        for r in lst or []:
            if len(rows) >= MAX_SESSIONS:
                break
            rr = dict(r)
            rr.setdefault("harness", h)
            add(rr, "top_by_harness")
    return rows[:MAX_SESSIONS]


def build_cc_pack_dense(path: Path) -> dict[str, Any]:
    indexed = index_transcript(path)
    T = indexed.T
    schedule = {"first_at": DENSE_SCHEDULE[0], "interval": 5, "fixed": list(DENSE_SCHEDULE)}
    prior = None
    snaps = []
    reached, never = [], []
    for cp in DENSE_SCHEDULE:
        if T < cp:
            never.append(cp)
            continue
        reached.append(cp)
        raw = build_hybrid_v0(indexed, cp, first_at=DENSE_SCHEDULE[0], interval=5, prior=prior)
        raw["schedule"] = dict(schedule)
        shrunk, steps = shrink_hybrid_state(raw)
        state = shrunk if shrunk is not None else raw
        snaps.append({
            "checkpoint": cp,
            "prior": prior,
            "state_chars": state_json_len(state),
            "shrink_steps": steps,
            "full_state": state,
        })
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


def lite_prefix_state(path: Path, harness: str, cp: int) -> dict[str, Any]:
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
            proxy = userish if userish else sum(roles.values())
            if proxy >= cp:
                break
            if lines_read > 20000:
                break
    return {
        "checkpoint_turn": cp,
        "harness": harness,
        "evidence_class": "lite_prefix",
        "schedule": {"first_at": DENSE_SCHEDULE[0], "interval": 5, "fixed": list(DENSE_SCHEDULE)},
        "cumulative": {
            "api_turns": cp,
            "prefix_lines_read": lines_read,
            "prefix_role_histogram_top": dict(sorted(roles.items(), key=lambda x: -x[1])[:8]),
            "prefix_userish_or_turn_proxy": userish,
            "note": "lite prefix-only; no full-session length fields",
        },
    }


def build_lite_pack_dense(row: dict[str, Any]) -> dict[str, Any]:
    harness = row["harness"]
    path = row.get("path") or ""
    inv = int(row.get("length_metric") or row.get("norm_length") or 40)
    if harness == "opencode":
        T = max(45, int(float(row.get("norm_length") or inv // 2)))
        worker = (row.get("session_id") or "opencode")[:24]
        snaps, reached, never = [], [], []
        for cp in DENSE_SCHEDULE:
            if T < cp:
                never.append(cp)
                continue
            reached.append(cp)
            state = {
                "checkpoint_turn": cp,
                "harness": "opencode",
                "evidence_class": "lite_inventory_prefix",
                "project": row.get("project"),
                "title": row.get("title"),
                "schedule": {"first_at": DENSE_SCHEDULE[0], "interval": 5, "fixed": list(DENSE_SCHEDULE)},
                "cumulative": {
                    "api_turns": cp,
                    "note": "opencode lite: checkpoint index only; no messages_full/T in state",
                },
            }
            snaps.append({"checkpoint": cp, "prior": None, "state_chars": state_json_len(state), "shrink_steps": [], "full_state": state})
        return {
            "harness": "opencode",
            "worker_id": worker,
            "path": path,
            "T_eligibility_only": T,
            "schedule": {"first_at": DENSE_SCHEDULE[0], "interval": 5, "fixed": list(DENSE_SCHEDULE)},
            "checkpoints": snaps,
            "reached_checkpoints": reached,
            "never_reached_checkpoints": never,
            "window_status": "unidentified",
        }
    p = Path(path)
    T = inv
    snaps, reached, never = [], [], []
    for cp in DENSE_SCHEDULE:
        if T < cp:
            never.append(cp)
            continue
        reached.append(cp)
        state = lite_prefix_state(p, harness, cp)
        snaps.append({"checkpoint": cp, "prior": None, "state_chars": state_json_len(state), "shrink_steps": [], "full_state": state})
    return {
        "harness": harness,
        "worker_id": p.stem[:24],
        "path": str(p),
        "T_eligibility_only": T,
        "schedule": {"first_at": DENSE_SCHEDULE[0], "interval": 5, "fixed": list(DENSE_SCHEDULE)},
        "checkpoints": snaps,
        "reached_checkpoints": reached,
        "never_reached_checkpoints": never,
        "window_status": "unidentified",
    }


def prepare_pack(row: dict[str, Any]) -> dict[str, Any] | None:
    harness = row.get("harness") or ""
    path = row.get("path") or ""
    try:
        if harness == "claude-code" and path and not str(path).startswith("sqlite:"):
            p = Path(path)
            if not p.exists():
                return {"error": f"missing_path:{path}", "harness": harness}
            pack = build_cc_pack_dense(p)
        elif harness in {"opencode", "codex", "cursor"}:
            if harness != "opencode" and path and not Path(path).exists():
                return {"error": f"missing_path:{path}", "harness": harness}
            pack = build_lite_pack_dense(row)
        else:
            return None
        pack["project"] = row.get("project")
        pack["corpus_source"] = row.get("corpus_source")
        pack["maps_family"] = "pajero-maps" in str(row.get("project") or "") or "pajero-maps" in str(path)
        return pack
    except Exception as e:
        return {"error": str(e), "path": path, "harness": harness, "trace": traceback.format_exc()[-400:]}


def _make_cell(pack, snap, framing, state_v, q, rc, driver):
    sid = pack["worker_id"]
    full = snap.get("full_state") or {}
    if "checkpoint_turn" not in full:
        full = {**full, "checkpoint_turn": snap["checkpoint"]}
    projected = project_state(full, state_v)
    if len(json.dumps(projected, ensure_ascii=False)) > 3500:
        projected = project_state(full, "deterministic_trim_v2")
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
        "capture_tag": f"{driver}-scale",
    }


def build_cells(packs, driver, target):
    usable = [p for p in packs if p.get("checkpoints")]
    usable = sorted(
        usable,
        key=lambda p: (
            0 if p.get("harness") == "claude-code" else 1 if p.get("harness") == "opencode" else 2,
            -int(p.get("T_eligibility_only") or 0),
        ),
    )
    pairs = []
    for pack in usable:
        for snap in pack["checkpoints"]:
            pairs.append((pack, snap))
    pairs.sort(key=lambda x: (int(x[1]["checkpoint"]), 0 if x[0].get("harness") == "claude-code" else 1))
    cells = []
    for framing, state_v, q, rc in SCALE_COMBOS:
        for pack, snap in pairs:
            cells.append(_make_cell(pack, snap, framing, state_v, q, rc, driver))
            if len(cells) >= target:
                return cells
    return cells


def llm_prompt(batch, driver):
    slim = []
    for c in batch:
        slim.append({
            "cell_id": c["cell_id"],
            "checkpoint": c["checkpoint"],
            "framing": c["framing"],
            "framing_text": c["framing_text"],
            "state_variant": c["state_variant"],
            "question_variant": c["question_variant"],
            "question": c["question_text"],
            "response_class": c["response_class"],
            "response_class_map": c["response_class_spec"]["map"],
            "labels": c["response_class_spec"]["labels"],
            "state": c["state"],
        })
    role = "Flash" if driver == "flash" else "Luna"
    return (
        f"You are an offline interception policy-under-test via {role} (NOT gold; Soft Standard HOLD).\n"
        "Judge ONLY the provided prefix snapshot + framing + question + response-class mapping.\n"
        "Do NOT infer final session length. Do NOT invent future turns or tool results.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"...","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating = steer-urgency 0..3. Apply response_class_map for fire.\n"
        f"CELLS ({len(slim)}):\n" + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx, batch, raw_dir):
    prompt = llm_prompt(batch, "flash")
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    try:
        proc = subprocess.run(
            ["opencode", "run", "--model", FLASH_MODEL, "--format", "default", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd="/tmp",
            timeout=180,
        )
        stdout, stderr, code = proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr, code = "timeout", -1
    except Exception as e:
        stdout, stderr, code = "", f"{type(e).__name__}: {e}", -1
    elapsed = time.time() - t0
    (raw_dir / f"batch-{batch_idx:03d}-stdout.txt").write_text(stdout, encoding="utf-8")
    (raw_dir / f"batch-{batch_idx:03d}-stderr.txt").write_text(stderr, encoding="utf-8")
    parsed = extract_json_array(stdout)
    by_id = {r.get("cell_id"): r for r in parsed if r.get("cell_id")}
    return {
        "batch_idx": batch_idx, "exit_code": code, "elapsed_s": round(elapsed, 2),
        "n_cells": len(batch), "n_parsed": len(by_id), "by_id": by_id,
        "error": None if by_id else (stderr or "")[:500],
    }


def run_luna_batch(batch_idx, batch, raw_dir):
    prompt = llm_prompt(batch, "luna")
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    bin_path = os.environ.get("WORKFLOW_CODEX_BIN", "codex")
    try:
        proc = subprocess.run(
            [bin_path, "exec", "-m", LUNA_MODEL, "--skip-git-repo-check", "--", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=240,
            env={**os.environ, "TERM": "dumb"},
        )
        stdout, stderr, code = proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr, code = "timeout", -1
    except Exception as e:
        stdout, stderr, code = "", f"{type(e).__name__}: {e}", -1
    elapsed = time.time() - t0
    (raw_dir / f"batch-{batch_idx:03d}-stdout.txt").write_text(stdout, encoding="utf-8")
    (raw_dir / f"batch-{batch_idx:03d}-stderr.txt").write_text(stderr, encoding="utf-8")
    parsed = extract_json_array(stdout)
    by_id = {r.get("cell_id"): r for r in parsed if r.get("cell_id")}
    return {
        "batch_idx": batch_idx, "exit_code": code, "elapsed_s": round(elapsed, 2),
        "n_cells": len(batch), "n_parsed": len(by_id), "by_id": by_id,
        "error": None if by_id else (stderr or "luna_parse_failed")[:500],
    }


def write_results(driver, cells, by_id, out_dir, extra_meters):
    results_path = out_dir / "results.jsonl"
    fire_by_cp: dict[int, list[bool]] = {t: [] for t in DENSE_SCHEDULE}
    rating_hist: dict[str, int] = {}
    harness_counts: dict[str, int] = {}
    framing_counts: dict[str, int] = {}
    state_counts: dict[str, int] = {}
    parse_miss = 0
    fire_count = 0
    error_count = 0
    with results_path.open("w", encoding="utf-8") as out:
        for c in cells:
            ans = by_id.get(c["cell_id"]) or {}
            if not ans:
                parse_miss += 1
            if ans.get("error") and ans.get("rating") is None and ans.get("fire") is None:
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
            if rating_i is not None:
                rating_hist[str(rating_i)] = rating_hist.get(str(rating_i), 0) + 1
            cp = int(c["checkpoint"])
            if fire is not None:
                fire_by_cp.setdefault(cp, []).append(bool(fire))
            harness_counts[c.get("harness") or "?"] = harness_counts.get(c.get("harness") or "?", 0) + 1
            framing_counts[c["framing"]] = framing_counts.get(c["framing"], 0) + 1
            state_counts[c["state_variant"]] = state_counts.get(c["state_variant"], 0) + 1
            model = ans.get("model") or (FLASH_MODEL if driver == "flash" else LUNA_MODEL)
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
                "label": ans.get("label"),
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
                "capture_tag": f"{driver}-scale",
                "typesafe": False,
                "soft_standard_hold": True,
                "batch": "batch-002",
                "wave": "Wave-0-scale",
                "schedule_kind": "dense_step5",
                "error": ans.get("error"),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    fire_rate = {}
    for t, flags in fire_by_cp.items():
        fire_rate[str(t)] = {"n": len(flags), "fire_rate": round(sum(flags) / len(flags), 4) if flags else None}
    leak_hits = prompt_leak_spotcheck(out_dir / "raw")
    meters = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "Wave-0-scale",
        "driver": driver,
        "capture_dir": str(out_dir),
        "meters_class": "score-ready-path-diagnostics",
        "score_ready_fp_miss_board": False,
        "soft_standard_hold": True,
        "typesafe_used": False,
        "hooks_unlock": False,
        "n_variants": len(cells),
        "parse_miss_cells": parse_miss,
        "error_count": error_count,
        "fire_count": fire_count,
        "rating_hist": rating_hist,
        "harness_cell_counts": harness_counts,
        "framing_counts": framing_counts,
        "state_variant_counts": state_counts,
        "dense_schedule": list(DENSE_SCHEDULE),
        "fire_rate_among_at_risk_cells": fire_rate,
        "prompt_leak_spotcheck_hits": leak_hits,
        "cell_id_salt": "b002s",
        **extra_meters,
    }
    (out_dir / "meters.json").write_text(json.dumps(meters, indent=2) + "\n", encoding="utf-8")
    md = [
        f"# METERS — batch-002 {driver}-scale",
        f"**Generated:** {meters['generated_at']}",
        "**Soft Standard HOLD** — Flash/Luna volume only; no TypeSafe / hooks / product unlock.",
        f"- n_variants: **{len(cells)}**",
        f"- parse_miss: **{parse_miss}**; fire: **{fire_count}**; errors: **{error_count}**",
        f"- leak_hits: **{len(leak_hits)}**",
        f"- dense_schedule: `{list(DENSE_SCHEDULE)}`",
        f"- framings: {json.dumps(framing_counts)}",
        f"- state_variants: {json.dumps(state_counts)}",
        f"- cell_id_salt: `b002s`",
        "",
    ]
    (out_dir / "METERS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return meters


def run_driver(driver, cells):
    out_dir = OUT[driver]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    per = CELLS_PER_FLASH if driver == "flash" else CELLS_PER_LUNA
    par = MAX_PAR_FLASH if driver == "flash" else MAX_PAR_LUNA
    runner = run_flash_batch if driver == "flash" else run_luna_batch
    batches = [cells[i:i + per] for i in range(0, len(cells), per)]
    print(f"[{now_aest()}] {driver}-scale start n={len(cells)} batches={len(batches)} par={par}", flush=True)
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=par) as ex:
        futs = {ex.submit(runner, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            results.append(res)
            # Incremental partial flush every batch
            partial_by = {}
            for r in results:
                partial_by.update(r.get("by_id") or {})
            if len(results) % 5 == 0 or len(results) == len(batches):
                write_results(driver, cells, partial_by, out_dir, {
                    "partial": len(results) < len(batches),
                    "batches_done": len(results),
                    "n_batches": len(batches),
                    "wall_s_so_far": round(time.time() - t0, 1),
                    "model": FLASH_MODEL if driver == "flash" else LUNA_MODEL,
                })
            print(
                f"[{now_aest()}] {driver}-scale batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s err={res.get('error')}",
                flush=True,
            )
    by_id = {}
    for r in results:
        by_id.update(r.get("by_id") or {})
    wall = round(time.time() - t0, 1)
    grid = {
        "generated_at": now_aest(),
        "driver": driver,
        "capture_tag": f"{driver}-scale",
        "model": FLASH_MODEL if driver == "flash" else LUNA_MODEL,
        "n_cells": len(cells),
        "n_batches": len(batches),
        "framings": sorted({c["framing"] for c in cells}),
        "state_variants": sorted({c["state_variant"] for c in cells}),
        "dense_schedule": list(DENSE_SCHEDULE),
        "cell_id_salt": "b002s",
        "soft_standard_hold": True,
        "sibling_dirs_untouched": [
            "typesafe", "flash-hframings", "luna", "flash-hframings-b", "luna-b",
        ],
    }
    (out_dir / "grid.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    meters = write_results(driver, cells, by_id, out_dir, {
        "partial": False,
        "wall_s": wall,
        "n_batches": len(batches),
        "batch_elapsed_sum_s": round(sum(r["elapsed_s"] for r in results), 1),
        "model": FLASH_MODEL if driver == "flash" else LUNA_MODEL,
        "batch_errors": [
            {"batch_idx": r["batch_idx"], "error": r.get("error"), "n_parsed": r["n_parsed"]}
            for r in results if r.get("error") or r["n_parsed"] < r["n_cells"]
        ][:60],
    })
    print(f"[{now_aest()}] {driver}-scale done wall={wall}s fire={meters['fire_count']} miss={meters['parse_miss_cells']}", flush=True)
    return meters


def main() -> int:
    for d in list(OUT.values()) + [SNAP_DENSE]:
        d.mkdir(parents=True, exist_ok=True)
    for d in OUT.values():
        (d / "raw").mkdir(exist_ok=True)

    corpus = load_expanded_corpus()
    print(f"[{now_aest()}] scale corpus rows={len(corpus)} combos={len(SCALE_COMBOS)} schedule_n={len(DENSE_SCHEDULE)}", flush=True)

    packs, pack_errors = [], []
    for row in corpus:
        pack = prepare_pack(row)
        if pack is None:
            continue
        if "error" in pack:
            pack_errors.append(pack)
            continue
        if not pack.get("checkpoints"):
            continue
        packs.append(pack)
        slim = {**{k: v for k, v in pack.items() if k != "checkpoints"}, "checkpoints": pack["checkpoints"]}
        (SNAP_DENSE / f"{pack['worker_id']}.json").write_text(json.dumps(slim) + "\n", encoding="utf-8")
    print(f"[{now_aest()}] dense packs={len(packs)} errors={len(pack_errors)}", flush=True)
    (BATCH / "SCALE-PACK-ERRORS.json").write_text(json.dumps(pack_errors[:50], indent=2) + "\n", encoding="utf-8")

    flash_cells = build_cells(packs, "flash", TARGET_FLASH)
    luna_cells = build_cells(packs, "luna", TARGET_LUNA)
    print(f"[{now_aest()}] scale targets flash={len(flash_cells)} luna={len(luna_cells)} salt=b002s", flush=True)

    for name, cells in (("flash", flash_cells), ("luna", luna_cells)):
        (OUT[name] / "cells_plan.json").write_text(
            json.dumps({
                "n": len(cells),
                "cell_id_salt": "b002s",
                "n_sessions": len({c["session_id"] for c in cells}),
                "framings": sorted({c["framing"] for c in cells}),
                "state_variants": sorted({c["state_variant"] for c in cells}),
                "question_variants": sorted({c["question_variant"] for c in cells}),
                "checkpoints": sorted({c["checkpoint"] for c in cells}),
                "cell_ids": [c["cell_id"] for c in cells],
            }, indent=2) + "\n",
            encoding="utf-8",
        )

    drivers = [d.strip() for d in (os.environ.get("SCALE_DRIVERS") or "flash,luna").split(",") if d.strip()]
    summary = {
        "generated_at": now_aest(),
        "drivers": drivers,
        "soft_standard_hold": True,
        "n_packs": len(packs),
        "n_combos": len(SCALE_COMBOS),
        "dense_schedule": list(DENSE_SCHEDULE),
        "results": {},
    }
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {}
        if "flash" in drivers:
            futs[ex.submit(run_driver, "flash", flash_cells)] = "flash"
        if "luna" in drivers:
            futs[ex.submit(run_driver, "luna", luna_cells)] = "luna"
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                summary["results"][name] = fut.result()
            except Exception as e:
                summary["results"][name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[{now_aest()}] {name}-scale FAILED: {e}", flush=True)

    (BATCH / "SCALE-WAVE-SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "summary": "SCALE-WAVE-SUMMARY.json", "hold": True}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
