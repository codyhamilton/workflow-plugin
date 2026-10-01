#!/usr/bin/env python3
"""Mid-length session expand wave — threshold T>=30, schedule 30..120 step 5 (Soft HOLD).

Complementary to flash-scale/luna-scale. Does not touch sibling TypeSafe / A / B dirs.
Outputs: flash-mid/ luna-mid/ snapshots-mid/
salt: b002m|
"""
from __future__ import annotations
import importlib.util
import os
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent
# Force mid targets before loading scale module constants used at runtime via env
os.environ.setdefault("SCALE_FLASH_N", "1600")
os.environ.setdefault("SCALE_LUNA_N", "640")
os.environ.setdefault("SCALE_FLASH_PAR", "1")  # soft yield vs scale+B
os.environ.setdefault("SCALE_LUNA_PAR", "1")
os.environ.setdefault("SCALE_MAX_SESSIONS", "120")
os.environ.setdefault("SCALE_DRIVERS", "flash,luna")

spec = importlib.util.spec_from_file_location("scale", BATCH / "run_batch002_flash_luna_scale.py")
scale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scale)

# Override outputs / schedule / salt / threshold behavior
scale.OUT = {
    "flash": BATCH / "flash-mid",
    "luna": BATCH / "luna-mid",
}
scale.SNAP_DENSE = BATCH / "snapshots-mid"
scale.DENSE_SCHEDULE = tuple(range(30, 121, 5))  # denser + earlier band
scale.TARGET_FLASH = int(os.environ["SCALE_FLASH_N"])
scale.TARGET_LUNA = int(os.environ["SCALE_LUNA_N"])
scale.MAX_PAR_FLASH = int(os.environ["SCALE_FLASH_PAR"])
scale.MAX_PAR_LUNA = int(os.environ["SCALE_LUNA_PAR"])
scale.MAX_SESSIONS = int(os.environ["SCALE_MAX_SESSIONS"])

_orig_load = scale.load_expanded_corpus

def load_mid():
    """Lower eligibility to length_metric>=30; keep R1 no-T-in-judge."""
    import json
    from pathlib import Path as P
    stats = json.loads((scale.INVENTORY / "stats.json").read_text(encoding="utf-8"))
    rows, seen = [], set()
    def add(r, source):
        path = r.get("path") or ""
        sid = r.get("session_id") or ""
        key = path or sid
        if not key or key in seen:
            return
        try:
            lm_i = int(float(r.get("length_metric") or r.get("norm_length") or 0))
        except Exception:
            lm_i = 0
        if lm_i < 30:
            return
        seen.add(key)
        rows.append({**r, "corpus_source": source, "length_metric": lm_i, "norm_length": r.get("norm_length") or lm_i})
    for r in stats.get("deterministic_shortlist") or []:
        add(r, "deterministic_30")
    sessions = list(stats.get("sessions") or [])
    def sk(r):
        try:
            n = float(r.get("length_metric") or 0)
        except Exception:
            n = 0
        maps = 1 if "pajero-maps" in str(r.get("project") or "") else 0
        return (-n, maps, r.get("harness") or "")
    sessions.sort(key=sk)
    quotas = {"claude-code": 50, "opencode": 30, "codex": 20, "cursor": 20}
    got = {k: 0 for k in quotas}
    for r in sessions:
        h = r.get("harness") or ""
        if h not in quotas or got[h] >= quotas[h]:
            continue
        before = len(rows)
        add(r, "inventory_mid")
        if len(rows) > before:
            got[h] += 1
        if len(rows) >= scale.MAX_SESSIONS:
            break
    return rows[: scale.MAX_SESSIONS]

scale.load_expanded_corpus = load_mid

_orig_cid = scale.cell_id
def cell_id(driver, framing, session_id, cp, state_v, q, rc):
    import hashlib
    raw = f"b002m|{driver}|{framing}|{session_id}|{cp}|{state_v}|{q}|{rc}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
scale.cell_id = cell_id

# Patch lite opencode T floor
_orig_lite = scale.build_lite_pack_dense
def build_lite_pack_dense(row):
    pack = _orig_lite(row)
    # rebuild schedule stamp already from DENSE_SCHEDULE via closure — ok
    return pack
scale.build_lite_pack_dense = build_lite_pack_dense

# Also patch write_results salt labels via monkeypatch of cell capture_tag in _make_cell
_orig_make = scale._make_cell
def _make_cell(pack, snap, framing, state_v, q, rc, driver):
    c = _orig_make(pack, snap, framing, state_v, q, rc, driver)
    c["cell_id"] = cell_id(driver, framing, pack["worker_id"], snap["checkpoint"], state_v, q, rc)
    c["capture_tag"] = f"{driver}-mid"
    return c
scale._make_cell = _make_cell

# Redirect summary path
_orig_main = scale.main
def main():
    # ensure dirs
    for d in list(scale.OUT.values()) + [scale.SNAP_DENSE]:
        d.mkdir(parents=True, exist_ok=True)
        if d in scale.OUT.values():
            (d / "raw").mkdir(exist_ok=True)
    # Temporarily rename summary writer by wrapping
    import json as _json
    from concurrent.futures import ThreadPoolExecutor, as_completed
    corpus = scale.load_expanded_corpus()
    print(f"[{scale.now_aest()}] mid corpus rows={len(corpus)} schedule_n={len(scale.DENSE_SCHEDULE)}", flush=True)
    packs, pack_errors = [], []
    for row in corpus:
        pack = scale.prepare_pack(row)
        if pack is None:
            continue
        if "error" in pack:
            pack_errors.append(pack)
            continue
        if not pack.get("checkpoints"):
            continue
        packs.append(pack)
        slim = {**{k: v for k, v in pack.items() if k != "checkpoints"}, "checkpoints": pack["checkpoints"]}
        (scale.SNAP_DENSE / f"{pack['worker_id']}.json").write_text(_json.dumps(slim) + "\n", encoding="utf-8")
    print(f"[{scale.now_aest()}] mid packs={len(packs)} errors={len(pack_errors)}", flush=True)
    flash_cells = scale.build_cells(packs, "flash", scale.TARGET_FLASH)
    luna_cells = scale.build_cells(packs, "luna", scale.TARGET_LUNA)
    print(f"[{scale.now_aest()}] mid targets flash={len(flash_cells)} luna={len(luna_cells)} salt=b002m", flush=True)
    for name, cells in (("flash", flash_cells), ("luna", luna_cells)):
        (scale.OUT[name] / "cells_plan.json").write_text(
            _json.dumps({
                "n": len(cells),
                "cell_id_salt": "b002m",
                "n_sessions": len({c["session_id"] for c in cells}),
                "framings": sorted({c["framing"] for c in cells}),
                "state_variants": sorted({c["state_variant"] for c in cells}),
                "checkpoints": sorted({c["checkpoint"] for c in cells}),
                "cell_ids": [c["cell_id"] for c in cells],
            }, indent=2) + "\n",
            encoding="utf-8",
        )
    summary = {
        "generated_at": scale.now_aest(),
        "wave": "Wave-0-mid",
        "soft_standard_hold": True,
        "n_packs": len(packs),
        "dense_schedule": list(scale.DENSE_SCHEDULE),
        "results": {},
    }
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {
            ex.submit(scale.run_driver, "flash", flash_cells): "flash",
            ex.submit(scale.run_driver, "luna", luna_cells): "luna",
        }
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                summary["results"][name] = fut.result()
            except Exception as e:
                summary["results"][name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[{scale.now_aest()}] {name}-mid FAILED: {e}", flush=True)
    (BATCH / "MID-WAVE-SUMMARY.json").write_text(_json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(_json.dumps({"ok": True, "summary": "MID-WAVE-SUMMARY.json", "hold": True}, indent=2), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
