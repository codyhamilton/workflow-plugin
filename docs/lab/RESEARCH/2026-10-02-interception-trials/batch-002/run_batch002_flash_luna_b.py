#!/usr/bin/env python3
"""Complementary Flash+Luna B-wave for batch-002 (Soft HOLD).

Does NOT touch sibling dirs: typesafe/, flash-hframings/, luna/
or rewrite run_batch002_multidriver.py.

Outputs:
  batch-002/flash-hframings-b/
  batch-002/luna-b/

cell_id salt prefix: b002b|...  (distinct from multidriver b002|)
Luna uses --skip-git-repo-check (sibling Luna failed without it).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path("/home/codyh/workspace/workflow-plugin")
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
SNAP_DIR = BATCH / "snapshots"
OUT = {
    "flash": BATCH / "flash-hframings-b",
    "luna": BATCH / "luna-b",
}
AEST = ZoneInfo("Australia/Brisbane")

FLASH_MODEL = "deepseek/deepseek-flash"
LUNA_MODEL = os.environ.get("WORKFLOW_LUNA_MODEL", "gpt-6-luna")
FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)

# Larger complementary n (Flash+Luna emphasis)
TARGET_FLASH = int(os.environ.get("BWAVE_FLASH_N", "360"))
TARGET_LUNA = int(os.environ.get("BWAVE_LUNA_N", "180"))
CELLS_PER_FLASH = 10
CELLS_PER_LUNA = 6
# Soft yield: leave room for sibling Flash (3) + maps Flash
MAX_PAR_FLASH = int(os.environ.get("BWAVE_FLASH_PAR", "2"))
MAX_PAR_LUNA = int(os.environ.get("BWAVE_LUNA_PAR", "2"))

# Import shared lever defs / helpers from sibling multidriver WITHOUT modifying it
_md_path = BATCH / "run_batch002_multidriver.py"
_spec = importlib.util.spec_from_file_location("batch002_multidriver", _md_path)
_md = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_md)

FRAMINGS = _md.FRAMINGS
QUESTION_VARIANTS = _md.QUESTION_VARIANTS
RESPONSE_CLASSES = _md.RESPONSE_CLASSES
LEVER_COMBOS = list(_md.LEVER_COMBOS)
project_state = _md.project_state
_strip_leaks = _md._strip_leaks
extract_json_array = _md.extract_json_array
load_packs = _md.load_packs
prompt_leak_spotcheck = _md.prompt_leak_spotcheck

# Extra B-wave lever combos (complementary coverage; H1–H5 × more axes)
EXTRA_COMBOS: list[tuple[str, str, str, str]] = [
    ("H1", "stats_plus_delta", "steer_now", "four_class"),
    ("H1", "compact_focus", "continue_excessively", "binary_fire"),
    ("H1", "hybrid_v0", "productive_arc", "likert_0_3"),
    ("H1", "stats_only", "near_done", "rating_plus_offset"),
    ("H2", "hybrid_v0", "horizon_exceeded", "rating_plus_offset"),
    ("H2", "stats_only", "defer_recheck", "four_class"),
    ("H2", "stats_plus_delta", "continue_excessively", "likert_0_3"),
    ("H2", "compact_focus", "steer_now", "binary_fire"),
    ("H3", "hybrid_v0", "plateau_sustained", "binary_fire"),
    ("H3", "stats_only", "thrash_bundle", "rating_plus_offset"),
    ("H3", "stats_plus_delta", "plateau_sustained", "four_class"),
    ("H3", "compact_focus", "productive_arc", "likert_0_3"),
    ("H4", "hybrid_v0", "boundary_overrun", "likert_0_3"),
    ("H4", "stats_only", "near_done", "binary_fire"),
    ("H4", "stats_plus_delta", "boundary_overrun", "rating_plus_offset"),
    ("H4", "compact_focus", "defer_recheck", "four_class"),
    ("H5", "hybrid_v0", "continue_excessively", "binary_fire"),
    ("H5", "stats_only", "waste_intervene", "four_class"),
    ("H5", "stats_plus_delta", "waste_intervene", "likert_0_3"),
    ("H5", "compact_focus", "horizon_exceeded", "rating_plus_offset"),
    ("H5", "hybrid_v0", "plateau_sustained", "four_class"),
    ("H2", "hybrid_v0", "productive_arc", "binary_fire"),
    ("H3", "hybrid_v0", "near_done", "likert_0_3"),
    ("H4", "stats_only", "steer_now", "rating_plus_offset"),
]

B_COMBOS = LEVER_COMBOS + EXTRA_COMBOS


def now_aest() -> str:
    return datetime.now(AEST).strftime("%Y-%m-%d %H:%M:%S AEST")


def cell_id(driver: str, framing: str, session_id: str, cp: int, state_v: str, q: str, rc: str) -> str:
    # Distinct salt from multidriver (b002|...) → b002b|
    raw = f"b002b|{driver}|{framing}|{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_cell(pack, snap, framing, state_v, q, rc, driver):
    sid = pack["worker_id"]
    full = snap.get("full_state") or {}
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
        "capture_tag": f"{driver}-b",
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
    for framing, state_v, q, rc in B_COMBOS:
        for pack, snap in pairs:
            cells.append(_make_cell(pack, snap, framing, state_v, q, rc, driver))
            if len(cells) >= target:
                return cells
    return cells


def llm_prompt(batch, driver):
    slim = []
    for c in batch:
        slim.append(
            {
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
            }
        )
    role = "Flash" if driver == "flash" else "Luna"
    return (
        f"You are an offline interception policy-under-test via {role} (NOT gold; Soft Standard HOLD).\n"
        "Judge ONLY the provided prefix snapshot + framing + question + response-class mapping.\n"
        "Do NOT infer final session length. Do NOT invent future turns or tool results.\n"
        "Return ONLY a JSON array (no prose) with one object per cell_id:\n"
        '[{"cell_id":"...","label":"...","rating":0-3,"fire":true/false,'
        '"fire_offset_turns":0,"rationale":"<=20 words"}]\n'
        "rating = steer-urgency 0..3. Apply response_class_map for fire.\n"
        f"CELLS ({len(slim)}):\n"
        + json.dumps(slim, ensure_ascii=False)
    )


def run_flash_batch(batch_idx, batch, raw_dir):
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
        "error": None if by_id else (proc.stderr or "")[:500],
    }


def run_luna_batch(batch_idx, batch, raw_dir):
    prompt = llm_prompt(batch, "luna")
    (raw_dir / f"batch-{batch_idx:03d}-prompt.txt").write_text(prompt, encoding="utf-8")
    t0 = time.time()
    bin_path = os.environ.get("WORKFLOW_CODEX_BIN", "codex")
    # Fix: --skip-git-repo-check + trusted repo cwd (sibling luna failed in /tmp)
    try:
        proc = subprocess.run(
            [
                bin_path,
                "exec",
                "-m",
                LUNA_MODEL,
                "--skip-git-repo-check",
                "--",
                prompt,
            ],
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


def write_results(driver, cells, by_id, out_dir, extra_meters):
    results_path = out_dir / "results.jsonl"
    fire_by_cp = {t: [] for t in FIXED_SCHEDULE}
    rating_hist: dict[str, int] = {}
    harness_counts: dict[str, int] = {}
    framing_counts: dict[str, int] = {}
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
                "capture_tag": f"{driver}-b",
                "typesafe": False,
                "soft_standard_hold": True,
                "batch": "batch-002",
                "wave": "Wave-0-b",
                "error": ans.get("error"),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    fire_rate = {}
    for t, flags in fire_by_cp.items():
        fire_rate[str(t)] = {
            "n": len(flags),
            "fire_rate": round(sum(flags) / len(flags), 4) if flags else None,
        }
    leak_hits = prompt_leak_spotcheck(out_dir / "raw")
    meters = {
        "generated_at": now_aest(),
        "batch": "batch-002",
        "wave": "Wave-0-b",
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
        "fixed_schedule": list(FIXED_SCHEDULE),
        "fire_rate_among_at_risk_cells": fire_rate,
        "prompt_leak_spotcheck_hits": leak_hits,
        "cell_id_salt": "b002b",
        **extra_meters,
    }
    (out_dir / "meters.json").write_text(json.dumps(meters, indent=2) + "\n", encoding="utf-8")
    md = [
        f"# METERS — batch-002 {driver}-b complementary wave",
        f"**Generated:** {meters['generated_at']}",
        "**Soft Standard HOLD** — no hooks / TypeSafe / product unlock.",
        f"- n_variants: **{len(cells)}**",
        f"- parse_miss: **{parse_miss}**; fire_count: **{fire_count}**; errors: **{error_count}**",
        f"- leak_hits: **{len(leak_hits)}**",
        f"- framings: {json.dumps(framing_counts)}",
        f"- cell_id_salt: `b002b`",
        "",
        "## Fire rate by checkpoint (diagnostic)",
    ]
    for t in FIXED_SCHEDULE:
        fr = fire_rate.get(str(t), {})
        md.append(f"- t={t}: fire_rate={fr.get('fire_rate')} (n={fr.get('n')})")
    (out_dir / "METERS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return meters


def run_driver_flash(cells):
    out_dir = OUT["flash"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    batches = [cells[i : i + CELLS_PER_FLASH] for i in range(0, len(cells), CELLS_PER_FLASH)]
    print(f"[{now_aest()}] Flash-B start n={len(cells)} batches={len(batches)} par={MAX_PAR_FLASH}", flush=True)
    flash_results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_FLASH) as ex:
        futs = {ex.submit(run_flash_batch, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            flash_results.append(res)
            print(
                f"[{now_aest()}] Flash-B batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s "
                f"err={res.get('error')}",
                flush=True,
            )
    by_id = {}
    for res in flash_results:
        by_id.update(res.get("by_id") or {})
    wall = round(time.time() - t0, 1)
    grid = {
        "generated_at": now_aest(),
        "driver": "flash",
        "capture_tag": "flash-b",
        "model": FLASH_MODEL,
        "n_cells": len(cells),
        "n_batches": len(batches),
        "framings": sorted({c["framing"] for c in cells}),
        "cell_id_salt": "b002b",
        "soft_standard_hold": True,
        "sibling_dirs_untouched": ["typesafe", "flash-hframings", "luna"],
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
            "batch_errors": [
                {"batch_idx": r["batch_idx"], "error": r.get("error"), "n_parsed": r["n_parsed"]}
                for r in flash_results
                if r.get("error") or r["n_parsed"] < r["n_cells"]
            ][:40],
        },
    )
    print(f"[{now_aest()}] Flash-B done wall={wall}s fire={meters['fire_count']} miss={meters['parse_miss_cells']}", flush=True)
    return meters


def run_driver_luna(cells):
    out_dir = OUT["luna"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    batches = [cells[i : i + CELLS_PER_LUNA] for i in range(0, len(cells), CELLS_PER_LUNA)]
    print(f"[{now_aest()}] Luna-B start n={len(cells)} batches={len(batches)} par={MAX_PAR_LUNA}", flush=True)
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PAR_LUNA) as ex:
        futs = {ex.submit(run_luna_batch, i, b, raw_dir): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            res = fut.result()
            results.append(res)
            print(
                f"[{now_aest()}] Luna-B batch {res['batch_idx']} "
                f"parsed={res['n_parsed']}/{res['n_cells']} {res['elapsed_s']}s "
                f"err={res.get('error')}",
                flush=True,
            )
    by_id = {}
    for res in results:
        by_id.update(res.get("by_id") or {})
    wall = round(time.time() - t0, 1)
    grid = {
        "generated_at": now_aest(),
        "driver": "luna",
        "capture_tag": "luna-b",
        "model": LUNA_MODEL,
        "n_cells": len(cells),
        "n_batches": len(batches),
        "framings": sorted({c["framing"] for c in cells}),
        "cell_id_salt": "b002b",
        "soft_standard_hold": True,
        "luna_flags": ["--skip-git-repo-check", f"cwd={REPO}"],
        "sibling_dirs_untouched": ["typesafe", "flash-hframings", "luna"],
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
            "batch_errors": [
                {"batch_idx": r["batch_idx"], "error": r.get("error"), "n_parsed": r["n_parsed"]}
                for r in results
                if r.get("error") or r["n_parsed"] < r["n_cells"]
            ][:40],
        },
    )
    print(f"[{now_aest()}] Luna-B done wall={wall}s fire={meters['fire_count']} miss={meters['parse_miss_cells']}", flush=True)
    return meters


def main() -> int:
    for d in OUT.values():
        d.mkdir(parents=True, exist_ok=True)
        (d / "raw").mkdir(exist_ok=True)

    packs = load_packs()
    print(f"[{now_aest()}] B-wave loaded packs={len(packs)}", flush=True)
    flash_cells = build_cells(packs, "flash", TARGET_FLASH)
    luna_cells = build_cells(packs, "luna", TARGET_LUNA)
    print(
        f"[{now_aest()}] B targets flash={len(flash_cells)} luna={len(luna_cells)} "
        f"combos={len(B_COMBOS)} salt=b002b",
        flush=True,
    )
    (OUT["flash"] / "cells_plan.json").write_text(
        json.dumps(
            {
                "n": len(flash_cells),
                "cell_id_salt": "b002b",
                "framings": sorted({c["framing"] for c in flash_cells}),
                "cell_ids": [c["cell_id"] for c in flash_cells],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT["luna"] / "cells_plan.json").write_text(
        json.dumps(
            {
                "n": len(luna_cells),
                "cell_id_salt": "b002b",
                "framings": sorted({c["framing"] for c in luna_cells}),
                "cell_ids": [c["cell_id"] for c in luna_cells],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    drivers = [d.strip() for d in (os.environ.get("BWAVE_DRIVERS") or "flash,luna").split(",") if d.strip()]
    summary = {"generated_at": now_aest(), "drivers": drivers, "soft_standard_hold": True, "results": {}}

    # Run Flash and Luna in parallel processes via threads of driver runners
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {}
        if "flash" in drivers:
            futs[ex.submit(run_driver_flash, flash_cells)] = "flash"
        if "luna" in drivers:
            futs[ex.submit(run_driver_luna, luna_cells)] = "luna"
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                summary["results"][name] = fut.result()
            except Exception as e:
                summary["results"][name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[{now_aest()}] {name} FAILED: {e}", flush=True)

    summary_path = BATCH / "B-WAVE-SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "summary": summary_path.name, "hold": True}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
