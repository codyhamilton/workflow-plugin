#!/usr/bin/env python3
"""TypeSafe thousands wave — Soft HOLD. No T leak. Fixed + denser schedule eligibility."""
from __future__ import annotations
import importlib.util, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BATCH = Path(__file__).resolve().parent
REPO = BATCH.parents[4] if False else Path("/home/codyh/workspace/workflow-plugin")
OUT = BATCH / os.environ.get("TS_OUT", "typesafe-k1")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "raw").mkdir(exist_ok=True)

spec = importlib.util.spec_from_file_location("md", BATCH / "run_batch002_multidriver.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)

# Denser schedule (R3-style T-independent); eligibility only — never sent to judge
DENSE_SCHEDULE = (45, 52, 60, 67, 75, 82, 90, 97, 105, 112, 120)
md.FIXED_SCHEDULE = DENSE_SCHEDULE

# Expand lever grid: all framings × states × questions × response classes (stratified, not full cartesian dump)
STATES = ["stats_only", "hybrid_v0", "stats_plus_delta", "compact_focus", "stats_trim", "hybrid_trim"]
# add trim modes into project_state via wrapper
_orig_project = md.project_state

def project_state(full, mode):
    if mode == "stats_trim":
        s = _orig_project(full, "stats_only")
        cum = dict(s.get("cumulative") or {})
        # deterministic trim: keep only top histogram keys / numeric peaks
        th = cum.get("tool_histogram")
        if isinstance(th, dict):
            cum["tool_histogram"] = dict(sorted(th.items(), key=lambda kv: -int(kv[1] or 0))[:4])
        for k in list(cum.keys()):
            if k.endswith("_paths") and isinstance(cum[k], list):
                cum[k] = cum[k][:3]
        s["cumulative"] = cum
        s["evidence_class"] = "stats_trim"
        return s
    if mode == "hybrid_trim":
        s = _orig_project(full, "hybrid_v0")
        s["brief_anchor"] = (s.get("brief_anchor") or "")[:120]
        s["tail"] = (s.get("tail") or [])[-2:]
        s["evidence_class"] = "hybrid_trim"
        return s
    return _orig_project(full, mode)

md.project_state = project_state

QUESTIONS = list(md.QUESTION_VARIANTS.keys())
RESPONSES = list(md.RESPONSE_CLASSES.keys())
FRAMINGS = list(md.FRAMINGS.keys())

# Build expanded LEVER_COMBOS: cycle systematically for volume
combos = []
for fi, fr in enumerate(FRAMINGS):
    for si, st in enumerate(STATES):
        for qi, q in enumerate(QUESTIONS):
            for ri, rc in enumerate(RESPONSES):
                # stride to avoid perfect duplicate explosion while still thousands
                if (fi + si + qi + ri) % 2 == 0 or (qi % 3 == 0):
                    combos.append((fr, st, q, rc))
md.LEVER_COMBOS = combos
print(f"lever_combos={len(combos)}", flush=True)

TARGET = int(os.environ.get("TS_TARGET", "2500"))
MAX_PAR = int(os.environ.get("TS_PAR", "10"))
md.MAX_PAR_TS = MAX_PAR
md.TARGET_TYPESAFE = TARGET
md.OUT["typesafe"] = OUT

# Expand packs: rebuild from FULL deterministic shortlist + existing snapshots
sys.path.insert(0, str(REPO / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"))

def load_expanded_packs():
    packs = md.load_packs()  # existing snapshots
    have = {p.get("worker_id") for p in packs}
    # Also try to prepare more from corpus via run_batch002 helpers
    spec2 = importlib.util.spec_from_file_location("b2", BATCH / "run_batch002.py")
    b2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(b2)
    b2.FIXED_SCHEDULE = DENSE_SCHEDULE
    corpus = b2.load_corpus()
    # take ALL deterministic + qualitative
    selected = corpus  # full shortlist mix
    print(f"corpus_rows={len(selected)} existing_packs={len(packs)}", flush=True)
    added = 0
    for row in selected:
        pack = b2.prepare_session_pack(row)
        if not pack or "error" in pack or not pack.get("checkpoints"):
            continue
        wid = pack.get("worker_id")
        if wid in have:
            # refresh checkpoints onto denser schedule if missing denser cps
            continue
        # save snapshot for reuse
        sp = BATCH / "snapshots" / f"{wid}.json"
        slim = {**{k: v for k, v in pack.items() if k != "checkpoints"}, "checkpoints": pack["checkpoints"]}
        try:
            sp.write_text(json.dumps(slim, indent=2) + "\n")
        except Exception:
            pass
        packs.append(pack)
        have.add(wid)
        added += 1
    print(f"packs_total={len(packs)} newly_added={added}", flush=True)
    return packs

packs = load_expanded_packs()
# Rebuild packs with denser schedule from existing CC snapshots where possible
# For packs that only have old schedule cps, still use those cps (eligibility already baked)
cells = md.build_cells(packs, "typesafe", TARGET)
print(f"[{md.now_aest()}] TypeSafe-K1 launching n={len(cells)} par={MAX_PAR} out={OUT}", flush=True)
(OUT / "cells_plan.json").write_text(json.dumps({"n": len(cells), "target": TARGET, "lever_combos": len(combos), "n_packs": len(packs), "schedule": list(DENSE_SCHEDULE)}) + "\n")

# Override OUT in run_driver by calling internals
md.OUT["typesafe"] = OUT
meters = md.run_driver_typesafe(cells)
summary = {
    "generated_at": md.now_aest(),
    "wave": "typesafe-k1",
    "soft_standard_hold": True,
    "n_cells": meters.get("n_cells"),
    "fire_count": meters.get("fire_count"),
    "parse_miss_cells": meters.get("parse_miss_cells"),
    "error_count": meters.get("error_count"),
    "leak_hits": len(meters.get("prompt_leak_spotcheck_hits") or []),
    "framing_cell_counts": meters.get("framing_cell_counts"),
    "usage_tokens_rough": meters.get("usage_tokens_rough"),
    "wall_s": meters.get("wall_s"),
    "n_packs": len(packs),
    "schedule": list(DENSE_SCHEDULE),
}
(OUT / "WAVE-SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
(BATCH / "PING-METERS-k1.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
