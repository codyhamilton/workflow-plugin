#!/usr/bin/env python3
"""TypeSafe phase-gating + review-check trial axes (Soft HOLD).

Measured corpus only — reuses tools/driver phase_assert schemas +
jev-cheap-judgement-signals builders. Does NOT wire assert_phase product /
hooks / Soft Standard unlock.

Outputs:
  batch-002/typesafe-phase-gate/
  batch-002/typesafe-review-check/
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path("/home/codyh/workspace/workflow-plugin")
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
SNAP_DIRS = [BATCH / "snapshots-dense", BATCH / "snapshots"]
DRIVER = REPO / "tools/driver"
PROOFS = REPO / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs"
AEST = ZoneInfo("Australia/Brisbane")
URL = "https://api.typesafe.ai/v1/systemone"
JEV = "jev-1.13.0"

sys.path.insert(0, str(DRIVER))
sys.path.insert(0, str(PROOFS))
from phase_assert import (  # noqa: E402
    build_jev_request,
    deterministic_outcome_evidence,
    jev_score_from_response,
)
from jev_signal_schemas import (  # noqa: E402
    build_phase_alignment_sanity_request,
    build_unit_needs_review_request,
    example_states,
)

AXIS = os.environ.get("TS_AXIS", "both")  # phase | review | both
TARGET_PHASE = int(os.environ.get("TS_PHASE_TARGET", "1500"))
TARGET_REVIEW = int(os.environ.get("TS_REVIEW_TARGET", "1500"))
WORKERS = int(os.environ.get("TS_AXIS_WORKERS", "12"))


def now() -> str:
    return datetime.now(AEST).isoformat(timespec="seconds")


def load_packs() -> list[dict[str, Any]]:
    seen: set[str] = set()
    packs: list[dict[str, Any]] = []
    for d in SNAP_DIRS:
        if not d.is_dir():
            continue
        for sp in sorted(d.glob("*.json")):
            try:
                pack = json.loads(sp.read_text(encoding="utf-8"))
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


def load_fixtures() -> dict[str, Any]:
    fx = DRIVER / "fixtures/assert"
    out = {
        "pass": json.loads((fx / "pass_state.json").read_text()),
        "fail": json.loads((fx / "fail_state.json").read_text()),
        "examples": example_states(),
    }
    return out


# --- compact state synthesizers (corpus-derived, Soft HOLD measurement only) ---

VERIFICATION_BODIES = {
    "strong": (
        "### Verification\n\nRan `python3 -m unittest` and checked DESIGN outcome. "
        "Evidence ties to stated design outcome. Exit 0.\n\n### Carried\n\nNone\n"
    ),
    "partial": (
        "### Verification\n\nRan some tests. Commands named but not clearly tied "
        "to design outcome.\n\n### Carried\n\nOpen questions remain.\n"
    ),
    "thin": (
        "## Phase close\n\nShipped work. Looks done.\n"
    ),
    "contradict": (
        "### Verification\n\nSkipped verification; claimed success without evidence. "
        "Design outcome ignored.\n"
    ),
    "placeholder": (
        "### Verification\n\nTODO: verify\n\n### Carried\n\nTODO\n"
    ),
}

HEADINGS = {
    "strong": ["## Phase", "### Verification", "### Carried"],
    "partial": ["## Phase", "### Verification"],
    "thin": ["## Phase"],
    "contradict": ["## Phase", "### Verification"],
    "placeholder": ["## Phase", "### Verification", "### Carried"],
}


def synth_phase_state(
    sid: str,
    harness: str | None,
    project: str | None,
    cp: int,
    quality: str,
    phase: int,
    report_status: str,
    trailer_ok: bool,
) -> dict[str, Any]:
    slug = (project or harness or "session")[:40].replace(" ", "-").lower() or "session"
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug)[:32] or "session"
    design = (
        f"Checkpoint-{cp} phase outcome for {sid[:12]}: "
        f"prefix work verified against plan intent (measurement only)."
    )
    body = VERIFICATION_BODIES[quality]
    if quality == "strong":
        body = body.replace("DESIGN outcome", design[:80])
    trailer = f"{slug}:{phase}" if trailer_ok else f"{slug}:999"
    return {
        "question_id": "outcome-evidence",
        "slug": slug,
        "phase": phase,
        "design_outcome": design,
        "closing_record": {
            "headings": [h.replace("Phase", f"Phase {phase}") for h in HEADINGS[quality]],
            "body": f"## Phase {phase}\n\nSession {sid[:16]} @cp{cp} ({harness}).\n\n{body}",
        },
        "workflow_report": {
            "status": report_status,
            "phase": phase if trailer_ok else phase + 1,
            "reason": "",
        },
        "trailer": trailer,
        # metadata not sent as T-leak; stripped from jev slice by build_jev_request
        "_meta": {
            "session_id": sid,
            "checkpoint": cp,
            "harness": harness,
            "project": project,
            "quality": quality,
            "soft_standard_hold": True,
        },
    }


def synth_review_state(
    sid: str,
    harness: str | None,
    project: str | None,
    cp: int,
    quality: str,
    phase: int,
    verifier_exit: int,
) -> dict[str, Any]:
    slug = (project or harness or "unit")[:32].replace(" ", "-").lower() or "unit"
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug)[:32] or "unit"
    return {
        "question_id": "unit-needs-review",
        "slug": slug,
        "phase": phase,
        "unit_id": f"{sid[:8]}-cp{cp}-q{quality[:4]}",
        "closing_headings": [h.replace("Phase", f"Phase {phase}") for h in HEADINGS[quality]],
        "closing_body_excerpt": VERIFICATION_BODIES[quality][:400],
        "trailer": f"{slug}:{phase}",
        "verifier_exit_code": verifier_exit,
        "_meta": {
            "session_id": sid,
            "checkpoint": cp,
            "harness": harness,
            "project": project,
            "quality": quality,
            "soft_standard_hold": True,
        },
    }


def round_robin_pairs(packs: list[dict[str, Any]]) -> list[tuple[dict, dict]]:
    """Interleave checkpoints across ALL packs (avoid first-N session skew)."""
    lists = []
    for pack in packs:
        cps = sorted(pack["checkpoints"], key=lambda s: int(s["checkpoint"]))
        lists.append([(pack, snap) for snap in cps])
    out: list[tuple[dict, dict]] = []
    i = 0
    while True:
        added = False
        for lst in lists:
            if i < len(lst):
                out.append(lst[i])
                added = True
        if not added:
            break
        i += 1
    return out


def build_phase_cells(packs: list[dict[str, Any]], fixtures: dict, target: int) -> list[dict]:
    cells: list[dict] = []
    # seed with driver fixtures × schema variants
    for label, st in (("fixture_pass", fixtures["pass"]), ("fixture_fail", fixtures["fail"])):
        for schema in ("outcome_evidence", "phase_alignment"):
            cid = hashlib.sha1(f"pg|{label}|{schema}".encode()).hexdigest()[:16]
            cells.append({
                "cell_id": cid,
                "axis": "phase-gate",
                "schema": schema,
                "source": label,
                "session_id": label,
                "checkpoint": 0,
                "quality": label,
                "state": st,
                "phase": st.get("phase"),
            })
    ex = fixtures["examples"]["phase_alignment"]
    cid = hashlib.sha1(b"pg|example|phase_alignment").hexdigest()[:16]
    cells.append({
        "cell_id": cid,
        "axis": "phase-gate",
        "schema": "phase_alignment",
        "source": "example_states",
        "session_id": "example_phase",
        "checkpoint": 0,
        "quality": "example",
        "state": ex,
        "phase": ex.get("phase"),
    })

    qualities = list(VERIFICATION_BODIES)
    phases = (1, 2, 3)
    report_statuses = ("closed", "open")
    pairs = round_robin_pairs(packs)
    for pack, snap in pairs:
        sid = pack["worker_id"]
        cp = int(snap["checkpoint"])
        for quality in qualities:
            for phase in phases:
                for report_status in report_statuses:
                    for trailer_ok in (True, False):
                        for schema in ("outcome_evidence", "phase_alignment"):
                            st = synth_phase_state(
                                sid, pack.get("harness"), pack.get("project"),
                                cp, quality, phase, report_status, trailer_ok,
                            )
                            raw = f"pg|{schema}|{sid}|{cp}|{quality}|{phase}|{report_status}|{int(trailer_ok)}"
                            cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
                            cells.append({
                                "cell_id": cid,
                                "axis": "phase-gate",
                                "schema": schema,
                                "source": "synth_from_pack",
                                "session_id": sid,
                                "checkpoint": cp,
                                "quality": quality,
                                "state": st,
                                "phase": phase,
                                "harness": pack.get("harness"),
                                "project": pack.get("project"),
                                "report_status": report_status,
                                "trailer_ok": trailer_ok,
                            })
                            if len(cells) >= target:
                                return cells
    return cells


def build_review_cells(packs: list[dict[str, Any]], fixtures: dict, target: int) -> list[dict]:
    cells: list[dict] = []
    ex = fixtures["examples"]["unit_needs_review"]
    cid = hashlib.sha1(b"rc|example|unit_needs_review").hexdigest()[:16]
    cells.append({
        "cell_id": cid,
        "axis": "review-check",
        "schema": "unit_needs_review",
        "source": "example_states",
        "session_id": "example_review",
        "checkpoint": 0,
        "quality": "example",
        "state": ex,
        "phase": ex.get("phase"),
    })
    # derive review-ish states from pass/fail fixtures
    for label, base in (("fixture_pass", fixtures["pass"]), ("fixture_fail", fixtures["fail"])):
        st = {
            "question_id": "unit-needs-review",
            "slug": base.get("slug"),
            "phase": base.get("phase"),
            "unit_id": f"{label}-u1",
            "closing_headings": (base.get("closing_record") or {}).get("headings"),
            "closing_body_excerpt": ((base.get("closing_record") or {}).get("body") or "")[:400],
            "trailer": base.get("trailer"),
            "verifier_exit_code": 0 if label == "fixture_pass" else 1,
        }
        cid = hashlib.sha1(f"rc|{label}|unit_needs_review".encode()).hexdigest()[:16]
        cells.append({
            "cell_id": cid,
            "axis": "review-check",
            "schema": "unit_needs_review",
            "source": label,
            "session_id": label,
            "checkpoint": 0,
            "quality": label,
            "state": st,
            "phase": st.get("phase"),
        })

    qualities = list(VERIFICATION_BODIES)
    phases = (1, 2, 3)
    exits = (0, 1)
    pairs = round_robin_pairs(packs)
    for pack, snap in pairs:
        sid = pack["worker_id"]
        cp = int(snap["checkpoint"])
        for quality in qualities:
            for phase in phases:
                for vex in exits:
                    st = synth_review_state(
                        sid, pack.get("harness"), pack.get("project"),
                        cp, quality, phase, vex,
                    )
                    raw = f"rc|unit_needs_review|{sid}|{cp}|{quality}|{phase}|{vex}"
                    cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
                    cells.append({
                        "cell_id": cid,
                        "axis": "review-check",
                        "schema": "unit_needs_review",
                        "source": "synth_from_pack",
                        "session_id": sid,
                        "checkpoint": cp,
                        "quality": quality,
                        "state": st,
                        "phase": phase,
                        "harness": pack.get("harness"),
                        "project": pack.get("project"),
                        "verifier_exit": vex,
                    })
                    if len(cells) >= target:
                        return cells
    return cells


def make_request(cell: dict) -> dict:
    st = deepcopy(cell["state"])
    st.pop("_meta", None)
    schema = cell["schema"]
    if schema == "outcome_evidence":
        return build_jev_request(st)
    if schema == "phase_alignment":
        return build_phase_alignment_sanity_request(st)
    if schema == "unit_needs_review":
        return build_unit_needs_review_request(st)
    raise ValueError(schema)


def post_cell(cell: dict, raw_dir: Path) -> dict:
    key = os.environ["TYPESAFE_API_KEY"].strip()
    req = make_request(cell)
    cid = cell["cell_id"]
    (raw_dir / f"{cid}-request.json").write_text(json.dumps(req, indent=2) + "\n")
    data = json.dumps(req).encode()
    http = urllib.request.Request(
        URL, data=data, method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(http, timeout=120) as resp:
            raw = resp.read().decode()
            code = resp.status
            err = None
            payload = json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        (raw_dir / f"{cid}-error.txt").write_text(f"HTTP {e.code}\n{detail}\n")
        return {
            **_row_base(cell),
            "ok": False,
            "http": e.code,
            "error": f"HTTP {e.code}: {detail[:400]}",
            "wall_s": round(time.time() - t0, 3),
        }
    except Exception as e:
        (raw_dir / f"{cid}-error.txt").write_text(f"{type(e).__name__}: {e}\n")
        return {
            **_row_base(cell),
            "ok": False,
            "http": None,
            "error": f"{type(e).__name__}: {e}",
            "wall_s": round(time.time() - t0, 3),
        }
    (raw_dir / f"{cid}-response.json").write_text(raw + ("\n" if not raw.endswith("\n") else ""))
    answers = payload.get("answers") or {}
    score = None
    choice = None
    if cell["schema"] == "outcome_evidence":
        score = jev_score_from_response(payload)
    elif cell["schema"] == "phase_alignment":
        raw_a = answers.get("alignment_sanity")
        if isinstance(raw_a, dict) and isinstance(raw_a.get("score"), (int, float)):
            score = float(raw_a["score"])
        elif isinstance(raw_a, (int, float)):
            score = float(raw_a)
    elif cell["schema"] == "unit_needs_review":
        nr = answers.get("needs_review")
        if isinstance(nr, dict):
            choice = nr.get("choice")
        rc = answers.get("review_confidence")
        if isinstance(rc, dict) and isinstance(rc.get("score"), (int, float)):
            score = float(rc["score"])

    det = None
    if cell["schema"] == "outcome_evidence":
        try:
            det = deterministic_outcome_evidence(cell["state"]).to_dict()
        except Exception as e:
            det = {"error": str(e)}

    return {
        **_row_base(cell),
        "ok": True,
        "http": code,
        "error": err,
        "wall_s": round(time.time() - t0, 3),
        "answers": answers,
        "usage": payload.get("usage"),
        "jev_score": score,
        "needs_review_choice": choice,
        "deterministic": det,
        "soft_standard_hold": True,
        "product_wiring": False,
        "assert_phase_unlock": False,
        "ts": now(),
    }


def _row_base(cell: dict) -> dict:
    return {
        "cell_id": cell["cell_id"],
        "axis": cell["axis"],
        "schema": cell["schema"],
        "source": cell.get("source"),
        "session_id": cell["session_id"],
        "checkpoint": cell.get("checkpoint"),
        "quality": cell.get("quality"),
        "phase": cell.get("phase"),
        "harness": cell.get("harness"),
        "project": cell.get("project"),
        "model": JEV,
    }


def run_axis(name: str, out_dir: Path, cells: list[dict]) -> dict:
    raw_dir = out_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    results_path = out_dir / "results.jsonl"
    done: set[str] = set()
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try:
                done.add(json.loads(line)["cell_id"])
            except Exception:
                pass
    todo = [c for c in cells if c["cell_id"] not in done]
    (out_dir / "cells_plan.json").write_text(json.dumps({
        "axis": name,
        "n_planned": len(cells),
        "n_todo": len(todo),
        "n_already": len(done),
        "n_sessions": len({c["session_id"] for c in cells}),
        "schemas": sorted({c["schema"] for c in cells}),
        "soft_standard_hold": True,
        "product_wiring": False,
        "generated_at": now(),
    }, indent=2) + "\n")
    print(json.dumps({"axis": name, "planned": len(cells), "todo": len(todo),
                      "sessions": len({c["session_id"] for c in cells}),
                      "workers": WORKERS}), flush=True)
    ok = err = 0
    tok_in = tok_out = 0
    t0 = time.time()
    with results_path.open("a") as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(post_cell, c, raw_dir) for c in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            if row.get("ok"):
                ok += 1
            else:
                err += 1
            u = row.get("usage") or {}
            tok_in += int(u.get("input_tokens") or 0)
            tok_out += int(u.get("output_tokens") or 0)
            if i % 50 == 0 or i == len(todo):
                print(json.dumps({
                    "axis": name, "done": i, "todo": len(todo),
                    "ok": ok, "err": err, "tok_in": tok_in,
                    "wall_s": round(time.time() - t0, 1),
                }), flush=True)
    meters = {
        "axis": name,
        "n_cells": len(done) + len(todo),
        "new": len(todo),
        "ok": ok,
        "errors": err,
        "tok_in": tok_in,
        "tok_out": tok_out,
        "wall_s": round(time.time() - t0, 1),
        "n_sessions": len({c["session_id"] for c in cells}),
        "soft_standard_hold": True,
        "product_wiring": False,
        "assert_phase_unlock": False,
        "generated_at": now(),
    }
    (out_dir / "meters.json").write_text(json.dumps(meters, indent=2) + "\n")
    (out_dir / "METERS.md").write_text(
        f"# METERS — {name}\n\n"
        f"**Generated:** {meters['generated_at']}\n\n"
        f"**Soft Standard HOLD** — measured corpus only; no assert_phase product wiring.\n\n"
        f"- n_cells: **{meters['n_cells']}**\n"
        f"- ok/err: {ok}/{err}\n"
        f"- sessions: {meters['n_sessions']}\n"
        f"- tokens in/out: {tok_in}/{tok_out}\n"
        f"- wall_s: {meters['wall_s']}\n"
    )
    print(json.dumps(meters), flush=True)
    return meters


def main() -> int:
    assert os.environ.get("TYPESAFE_API_KEY", "").strip(), "TYPESAFE_API_KEY missing"
    packs = load_packs()
    fixtures = load_fixtures()
    print(json.dumps({"n_packs": len(packs), "axis": AXIS}), flush=True)
    summaries = {}
    if AXIS in ("phase", "both"):
        cells = build_phase_cells(packs, fixtures, TARGET_PHASE)
        summaries["phase"] = run_axis(
            "phase-gate", BATCH / "typesafe-phase-gate", cells
        )
    if AXIS in ("review", "both"):
        cells = build_review_cells(packs, fixtures, TARGET_REVIEW)
        summaries["review"] = run_axis(
            "review-check", BATCH / "typesafe-review-check", cells
        )
    (BATCH / "PHASE-REVIEW-AXES-SUMMARY.json").write_text(
        json.dumps({"generated_at": now(), "soft_hold": True, **summaries}, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
