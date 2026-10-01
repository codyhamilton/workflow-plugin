#!/usr/bin/env python3
"""Flash+Luna volume competing axes — Soft HOLD. Soft yield Claude/Sol."""
from __future__ import annotations
import importlib.util, json, os, sys
from pathlib import Path
BATCH = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("md", BATCH / "run_batch002_multidriver.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)

# Expanded levers (same spirit as typesafe-k1 but lighter for slower drivers)
STATES = ["stats_only", "hybrid_v0", "stats_plus_delta", "compact_focus"]
QUESTIONS = list(md.QUESTION_VARIANTS.keys())
RESPONSES = ["likert_0_3", "binary_fire", "four_class"]
FRAMINGS = list(md.FRAMINGS.keys())
combos = []
for fr in FRAMINGS:
    for st in STATES:
        for q in QUESTIONS:
            for rc in RESPONSES:
                if hash((fr, st, q, rc)) % 3 != 0:
                    combos.append((fr, st, q, rc))
md.LEVER_COMBOS = combos
print("lever_combos", len(combos), flush=True)

tag = os.environ.get("MULTI_OUT_TAG", "vol1")
md.OUT["flash"] = BATCH / f"flash-hframings-{tag}"
md.OUT["luna"] = BATCH / f"luna-{tag}"
for d in (md.OUT["flash"], md.OUT["luna"]):
    d.mkdir(parents=True, exist_ok=True)
    (d / "raw").mkdir(exist_ok=True)

# Luna flag already patched in multidriver
md.TARGET_FLASH = int(os.environ.get("FLASH_TARGET", "800"))
md.TARGET_LUNA = int(os.environ.get("LUNA_TARGET", "200"))
md.CELLS_PER_FLASH = 10
md.CELLS_PER_LUNA = 6
md.MAX_PAR_FLASH = int(os.environ.get("FLASH_PAR", "2"))  # throttle if Maps contends
md.MAX_PAR_LUNA = 2

packs = md.load_packs()
flash_cells = md.build_cells(packs, "flash", md.TARGET_FLASH)
luna_cells = md.build_cells(packs, "luna", md.TARGET_LUNA)
print(f"flash_n={len(flash_cells)} luna_n={len(luna_cells)} packs={len(packs)}", flush=True)

os.environ["MULTI_DRIVERS"] = "flash,luna"
# run both
from concurrent.futures import ThreadPoolExecutor, as_completed
summary = {"soft_standard_hold": True, "tag": tag, "drivers": {}}

def run(name):
    if name == "flash":
        return name, md.run_driver_flash(flash_cells)
    return name, md.run_driver_luna(luna_cells)

with ThreadPoolExecutor(max_workers=2) as ex:
    futs = [ex.submit(run, n) for n in ("flash", "luna")]
    for fut in as_completed(futs):
        name, meters = fut.result()
        summary["drivers"][name] = {
            "n_cells": meters.get("n_cells"),
            "fire_count": meters.get("fire_count"),
            "parse_miss_cells": meters.get("parse_miss_cells"),
            "error_count": meters.get("error_count"),
            "leak_hits": len(meters.get("prompt_leak_spotcheck_hits") or []),
            "framing_cell_counts": meters.get("framing_cell_counts"),
            "wall_s": meters.get("wall_s"),
            "error": meters.get("error"),
        }
(BATCH / f"PING-METERS-{tag}.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
