#!/usr/bin/env python3
"""Seat the PR-SURVIVAL-EVENT TypeSafe event-time trial.

This runner is deliberately independent of the product and localhost.  It
uses the frozen maps-5h early-window packs as one stimulus per worker/seat,
calls TypeSafe directly, and writes auditable request/response artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = Path("/home/codyh/workspace/corpus-ops/registry/survival-event/protocol.json")
EXPECTED_PROTOCOL_SHA256 = (
    "b32652421d15dcd85ecc920c6bcd13d5304b9ce457dc17c69bbe8213549cf26d"
)
SOURCE_REF = "origin/cursor/adversarial-brittle-v2-c262"
SOURCE_BASE = (
    "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/"
    "proofs/validated/gold/packs"
)
CORPUS_PACK_DIRS = (
    Path("/home/codyh/workspace/corpus-ops/corpus-ops/registry/validation-phase/packs"),
    Path("/home/codyh/workspace/corpus-ops/registry/validation-phase/packs"),
)
API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
EARLY_MAX = 120
SEATS = (1, 2, 3)
WORKERS = (
    "92a48e004519",
    "ca977b9ca0dd",
    "87a380bc64ff",
    "bb6165018de0",
    "15f24c7ba18c",
    "8e36f8e80baa",
    "daf933273c8f",
    "07357f196666",
    "0677f597286e",
    "074c8cf22927",
    "0853bc21d3aa",
    "16a958631580",
)
STRATA = {
    "thrash": ("92a48e004519", "ca977b9ca0dd"),
    "poll_monitor": ("87a380bc64ff", "bb6165018de0", "15f24c7ba18c", "8e36f8e80baa"),
    "weak": ("daf933273c8f", "07357f196666"),
    "residual": ("0677f597286e", "074c8cf22927", "0853bc21d3aa", "16a958631580"),
}
PACK_FILENAMES = {
    "92a48e004519": "92a48e004519-judge-packs-20261001-194107.jsonl",
    "ca977b9ca0dd": "ca977b9ca0dd-judge-packs-20261001-204508.jsonl",
    "87a380bc64ff": "87a380bc64ff-judge-packs-20261001-214046.jsonl",
    "bb6165018de0": "bb6165018de0-judge-packs-20261001-194107.jsonl",
    "15f24c7ba18c": "15f24c7ba18c-judge-packs-20261001-214046.jsonl",
    "8e36f8e80baa": "8e36f8e80baa-judge-packs-20261001-214046.jsonl",
    "daf933273c8f": "daf933273c8f-judge-packs-20261001-204508.jsonl",
    "07357f196666": "07357f196666-judge-packs-20261001-214046.jsonl",
    "0677f597286e": "0677f597286e-judge-packs-20261001-214046.jsonl",
    "074c8cf22927": "074c8cf22927-judge-packs-20261001-214046.jsonl",
    "0853bc21d3aa": "0853bc21d3aa-judge-packs-20261001-202909.jsonl",
    "16a958631580": "16a958631580-judge-packs-20261001-214046.jsonl",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def protocol_stamp() -> str:
    actual = sha256_bytes(PROTOCOL_PATH.read_bytes())
    if actual != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(
            f"protocol SHA mismatch: expected {EXPECTED_PROTOCOL_SHA256}, got {actual}"
        )
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("case_id") != "PR-SURVIVAL-EVENT" or protocol.get("wsm_status") != "GO":
        raise RuntimeError("protocol case_id or WSM status is not authorized")
    return actual


def git_text(path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{SOURCE_REF}:{path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise FileNotFoundError(path)
    return result.stdout


def source_pack(worker_id: str) -> tuple[bytes, str]:
    filename = PACK_FILENAMES[worker_id]
    for directory in CORPUS_PACK_DIRS:
        path = directory / f"{worker_id}-judge-packs-20261002-earlycps.jsonl"
        if path.exists():
            return path.read_bytes(), str(path)
    path = f"{SOURCE_BASE}/{filename}"
    return git_text(path), f"{SOURCE_REF}:{path}"


def source_metric(worker_id: str) -> tuple[dict[str, Any], str]:
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", SOURCE_REF],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    candidates = [
        path
        for path in listing
        if worker_id in Path(path).name and "dry-run-metrics" in Path(path).name
    ]
    if not candidates:
        inventory_path = (
            "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/"
            "proofs/validated/gold/packs/INVENTORY-shape-qual-full-maps-v1-20261001-214046.json"
        )
        inventory = json.loads(git_text(inventory_path))
        worker_row = next(
            (row for row in inventory.get("workers", []) if row.get("worker_id") == worker_id),
            None,
        )
        if not isinstance(worker_row, dict) or not isinstance(worker_row.get("T"), int):
            raise FileNotFoundError(f"no metrics source for {worker_id}")
        return worker_row, f"{SOURCE_REF}:{inventory_path}"
    data = git_text(candidates[0])
    metric = json.loads(data)
    worker_rows = metric.get("workers") or []
    worker_row = next((row for row in worker_rows if row.get("worker_id") == worker_id), None)
    if worker_row is not None:
        metric = worker_row
    if not isinstance(metric.get("T"), int):
        raise ValueError(f"metrics source has no integer T for {worker_id}")
    return metric, f"{SOURCE_REF}:{candidates[0]}"


def load_rows(worker_id: str) -> tuple[list[dict[str, Any]], str, str, int]:
    data, source = source_pack(worker_id)
    rows = [
        json.loads(line)
        for line in data.decode("utf-8").splitlines()
        if line.strip()
    ]
    rows = sorted(
        [row for row in rows if int(row["checkpoint_turn"]) <= EARLY_MAX],
        key=lambda row: int(row["checkpoint_turn"]),
    )
    if not rows:
        raise ValueError(f"{worker_id}: source pack has no row at or below {EARLY_MAX}")
    metric, metric_source = source_metric(worker_id)
    return rows, source, metric_source, int(metric["T"])


def card_row(row: dict[str, Any]) -> dict[str, Any]:
    """Retain only prefix-visible hybrid pack fields."""
    return {
        key: row[key]
        for key in (
            "worker_id",
            "checkpoint_turn",
            "schedule",
            "snapshot_mode",
            "snapshot_params",
            "prior_checkpoint_turn",
            "brief_anchor",
            "cumulative",
            "delta_since_prior",
            "tail",
            "thrash_top_rereads",
        )
        if key in row
    }


def marker_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    last = rows[-1]
    first_cum = rows[0].get("cumulative") or {}
    last_cum = last.get("cumulative") or {}
    hists = [
        (row.get("cumulative") or {}).get("tool_histogram") or {} for row in rows
    ]
    reread_max = max(
        (
            max(
                [int(item.get("count") or 0) for item in (row.get("cumulative") or {}).get("reread_paths") or []],
                default=0,
            )
            for row in rows
        ),
        default=0,
    )
    last_hist = last_cum.get("tool_histogram") or {}
    mutation_absent = all(
        int(hist.get("Edit") or 0) + int(hist.get("Write") or 0) == 0 for hist in hists
    )
    return {
        "compaction_last_le120": int(last_cum.get("compaction_event_count") or 0),
        "compaction_delta_le120": int(last_cum.get("compaction_event_count") or 0)
        - int(first_cum.get("compaction_event_count") or 0),
        "edit_write_absent": mutation_absent,
        "no_mutation": mutation_absent,
        "reread_max": reread_max,
        "reread_cluster": reread_max >= 3,
        "assistant_text_chars_last": int(last_cum.get("assistant_text_chars") or 0),
        "checkpoints_seen_le120": len(rows),
        "last_checkpoint_le120": int(last["checkpoint_turn"]),
        "peak_ctx_first": int(first_cum.get("peak_ctx_tokens") or 0),
        "tool_histogram_last": dict(last_hist),
    }


def build_stimulus(worker_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    rows, source, metric_source, t = load_rows(worker_id)
    card = {
        "card_kind": "hybrid_v0_early_window",
        "case_id": "PR-SURVIVAL-EVENT",
        "worker_id": worker_id,
        "stratum": next(name for name, ids in STRATA.items() if worker_id in ids),
        "early_window_max": EARLY_MAX,
        "rows": [card_row(row) for row in rows],
    }
    serialized = json.dumps(card, ensure_ascii=False, sort_keys=True)
    if len(serialized) >= 60_000:
        raise ValueError(f"{worker_id}: stimulus exceeds 60k judge budget")
    card["stimulus_sha256"] = sha256_bytes(serialized.encode("utf-8"))
    meta = {
        "worker_id": worker_id,
        "T": t,
        "early_window_end": min(t, EARLY_MAX),
        "source_pack": source,
        "source_pack_sha256": sha256_bytes(
            source_pack(worker_id)[0]
        ),
        "source_metrics": metric_source,
        "feature_set": "EX-MARKER-1A",
        "markers": marker_features(rows),
        "stimulus_chars": len(serialized),
    }
    return card, meta


def question_schema() -> dict[str, dict[str, Any]]:
    criteria = {
        "null": (
            "No supported transition to unproductive is visible in this prefix; "
            "return null rather than guessing."
        )
    }
    criteria.update(
        {
            str(turn): f"The earliest supported transition occurred at api_turn {turn}."
            for turn in range(1, EARLY_MAX + 1)
        }
    )
    return {
        "event_time": {
            "type": "choice",
            "instructions": (
                "At what api_turn, if any, did this trajectory become unproductive? "
                "Use only the shown early-window card. Return the earliest supported "
                "api_turn as an integer label, or null when the card does not support "
                "an event. Do not use trajectory length or hindsight."
            ),
            "criteria": criteria,
        },
        "rationale": {
            "type": "noul",
            "instructions": (
                "Optional one-line rationale. Cite only visible checkpoint turns and "
                "observable activity in the card; do not invent an event."
            ),
        },
    }


def cell_id(worker_id: str, seat: int) -> str:
    raw = f"PR-SURVIVAL-EVENT|typesafe|jev-1.13.0|maps-5h|{worker_id}|{seat}|EX-MARKER-1A"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_cell(worker_id: str, seat: int, card: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": cell_id(worker_id, seat),
        "case_id": "PR-SURVIVAL-EVENT",
        "driver": "typesafe",
        "model": MODEL,
        "seat": seat,
        "worker_id": worker_id,
        "stratum": meta["stratum"] if "stratum" in meta else card["stratum"],
        "framing": "EX-MARKER-1A",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "no_call_jev": True,
        "product_wiring": False,
        "request": {
            "model": MODEL,
            "state": {
                "scenario_id": f"PR-SURVIVAL-EVENT|{worker_id}|seat-{seat}",
                "framing": "EX-MARKER-1A",
                "snapshot": card,
            },
            "questions": question_schema(),
        },
    }


def parse_answers(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    answers = payload.get("answers") or {}
    event = answers.get("event_time") or {}
    wire_type = event.get("type")
    label = event.get("choice")
    scrape_ok = wire_type != "choice" or (
        label is not None and event.get("response_class") == label
    )
    if wire_type != "choice":
        return {
            "event_time": None,
            "response_class": event.get("response_class"),
            "response_label": None,
            "choice_scrape_ok": False,
            "wire_type": wire_type,
            "rationale": None,
        }, "event_time was not a choice answer"
    if not scrape_ok:
        return {
            "event_time": None,
            "response_class": event.get("response_class"),
            "response_label": label,
            "choice_scrape_ok": False,
            "wire_type": wire_type,
            "rationale": None,
        }, "choice scrape invariant failed: response_class != response_label"
    if label == "null":
        value: int | None = None
    else:
        try:
            value = int(label)
        except (TypeError, ValueError):
            return {
                "event_time": None,
                "response_class": event.get("response_class"),
                "response_label": label,
                "choice_scrape_ok": False,
                "wire_type": wire_type,
                "rationale": None,
            }, f"invalid event_time label: {label!r}"
        if not 1 <= value <= EARLY_MAX:
            return {}, f"event_time outside 1..{EARLY_MAX}: {value}"
    rationale_answer = answers.get("rationale") or {}
    rationale = rationale_answer.get("text", rationale_answer.get("value"))
    return {
        "event_time": value,
        "response_class": event.get("response_class"),
        "response_label": label,
        "choice_scrape_ok": True,
        "wire_type": wire_type,
        "rationale": rationale,
    }, None


def call_cell(cell: dict[str, Any], api_key: str, raw_dir: Path) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    cid = cell["cell_id"]
    request_text = json.dumps(cell["request"], ensure_ascii=False, indent=2) + "\n"
    (raw_dir / f"{cid}-request.json").write_text(request_text, encoding="utf-8")
    base = {
        "cell_id": cid,
        "case_id": cell["case_id"],
        "worker_id": cell["worker_id"],
        "seat": cell["seat"],
        "driver": cell["driver"],
        "model": cell["model"],
        "framing": cell["framing"],
        "protocol_sha256": cell["protocol_sha256"],
        "no_call_jev": True,
        "product_wiring": False,
        "request_sha256": sha256_bytes(request_text.encode("utf-8")),
        "started_at": started.isoformat(),
    }
    request = urllib.request.Request(
        API_URL,
        data=request_text.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response_text = response.read().decode("utf-8")
            status = response.status
        (raw_dir / f"{cid}-response.json").write_text(
            response_text + ("" if response_text.endswith("\n") else "\n"),
            encoding="utf-8",
        )
        payload = json.loads(response_text)
        parsed, parse_error = parse_answers(payload)
        return {
            **base,
            "http": status,
            "error": parse_error,
            "answers": parsed,
            "raw_request": f"raw/{cid}-request.json",
            "raw_response": f"raw/{cid}-response.json",
            "response_sha256": sha256_bytes(response_text.encode("utf-8")),
            "usage": payload.get("usage"),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        (raw_dir / f"{cid}-error.txt").write_text(
            f"HTTP {error.code}\n{detail}\n", encoding="utf-8"
        )
        return {**base, "http": error.code, "error": detail[:2000], "answers": None}
    except Exception as error:  # noqa: BLE001 - persist transport failures per cell
        (raw_dir / f"{cid}-error.txt").write_text(
            f"{type(error).__name__}: {error}\n", encoding="utf-8"
        )
        return {**base, "http": None, "error": f"{type(error).__name__}: {error}", "answers": None}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def prepare(out: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "raw"
    raw.mkdir(exist_ok=True)
    cells: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    cards = []
    for worker_id in WORKERS:
        card, meta = build_stimulus(worker_id)
        cards.append({"worker_id": worker_id, "card": card, "metadata": meta})
        metadata.append(meta)
        for seat in SEATS:
            cells.append(build_cell(worker_id, seat, card, meta))
    write_json(out / "cell-manifest.json", {
        "case_id": "PR-SURVIVAL-EVENT",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "driver": "TypeSafe",
        "model": MODEL,
        "stratum": "maps-5h",
        "n_workers": len(WORKERS),
        "n_seats": len(SEATS),
        "planned_calls": len(cells),
        "no_call_jev": True,
        "product_wiring": False,
        "cells": [
            {key: value for key, value in cell.items() if key != "request"}
            for cell in cells
        ],
    })
    write_json(out / "stimulus-cards.json", cards)
    with (out / "prepared-cells.jsonl").open("w", encoding="utf-8") as handle:
        for cell in cells:
            handle.write(json.dumps(cell, ensure_ascii=False) + "\n")
    write_json(out / "source-metadata.json", metadata)
    return cells, metadata


def run_calls(out: Path, cells: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not set")
    results_path = out / "results.jsonl"
    done: dict[str, dict[str, Any]] = {}
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["cell_id"]] = row
    todo = [cell for cell in cells if cell["cell_id"] not in done]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(call_cell, cell, key, out / "raw"): cell["cell_id"]
            for cell in todo
        }
        for future in as_completed(futures):
            row = future.result()
            done[row["cell_id"]] = row
            ordered = [done[cell["cell_id"]] for cell in cells if cell["cell_id"] in done]
            results_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in ordered) + "\n",
                encoding="utf-8",
            )
            print(
                f"{row['cell_id']} worker={row['worker_id']} seat={row['seat']} "
                f"http={row.get('http')} error={row.get('error')!r}",
                flush=True,
            )
    return [done[cell["cell_id"]] for cell in cells if cell["cell_id"] in done]


def event_value(row: dict[str, Any]) -> int | None:
    answers = row.get("answers") or {}
    value = answers.get("event_time")
    return value.get("event_time") if isinstance(value, dict) else None


def agreement_summary(results: list[dict[str, Any]], metadata: list[dict[str, Any]]) -> dict[str, Any]:
    by_worker: dict[str, list[dict[str, Any]]] = {worker: [] for worker in WORKERS}
    for row in results:
        by_worker.setdefault(row["worker_id"], []).append(row)
    per_worker = []
    pairwise_total = pairwise_agree = 0
    for worker in WORKERS:
        values = [event_value(row) for row in sorted(by_worker[worker], key=lambda r: r["seat"])]
        pairwise = sum(a == b for index, a in enumerate(values) for b in values[index + 1 :])
        pairwise_total += 3
        pairwise_agree += pairwise
        counts = Counter(values)
        majority_value, majority_count = counts.most_common(1)[0] if counts else (None, 0)
        per_worker.append({
            "worker_id": worker,
            "stratum": next(name for name, ids in STRATA.items() if worker in ids),
            "event_times_by_seat": values,
            "all_three_exact": len(set(values)) == 1 if values else False,
            "majority_event_time": majority_value,
            "majority_count": majority_count,
            "range": max(values) - min(values) if values and all(v is not None for v in values) else None,
            "pairwise_exact_agreement": pairwise / 3 if values else None,
        })
    return {
        "case_id": "PR-SURVIVAL-EVENT",
        "n_workers": len(WORKERS),
        "n_seats": len(SEATS),
        "n_worker_seat_rows": len(results),
        "all_three_exact_workers": sum(row["all_three_exact"] for row in per_worker),
        "worker_exact_agreement_rate": sum(row["all_three_exact"] for row in per_worker) / len(WORKERS),
        "pairwise_exact_agreement_rate": pairwise_agree / pairwise_total if pairwise_total else None,
        "per_worker": per_worker,
        "prefix_causal_alpha": None,
        "agreement_kill_fired": None,
        "agreement_kill_status": "not_evaluable: protocol does not specify prefix-causal alpha",
    }


def c_index(durations: list[float], events: list[int], risks: list[float]) -> float | None:
    concordant = comparable = 0.0
    for i in range(len(durations)):
        for j in range(i + 1, len(durations)):
            if durations[i] == durations[j]:
                continue
            if events[i] and durations[i] < durations[j]:
                earlier, later = i, j
            elif events[j] and durations[j] < durations[i]:
                earlier, later = j, i
            else:
                continue
            comparable += 1
            if risks[earlier] > risks[later]:
                concordant += 1
            elif risks[earlier] == risks[later]:
                concordant += 0.5
    return concordant / comparable if comparable else None


def fit_cox(rows: list[dict[str, Any]], covariates: list[str]) -> dict[str, Any]:
    try:
        import numpy as np
        from scipy.optimize import minimize
        from scipy.special import logsumexp
    except ImportError as error:
        return {"status": "unavailable", "error": str(error), "covariates": covariates}
    if sum(row["event"] for row in rows) < 2:
        return {"status": "refused", "reason": "fewer than two events", "covariates": covariates}
    x = np.asarray([[float(row["features"][name]) for name in covariates] for row in rows])
    durations = np.asarray([float(row["duration"]) for row in rows])
    events = np.asarray([int(row["event"]) for row in rows])
    if np.ptp(x, axis=0).min(initial=0) == 0:
        return {"status": "refused", "reason": "constant covariate", "covariates": covariates}

    def objective(beta: Any) -> float:
        value = 0.0
        for index in np.where(events == 1)[0]:
            risk = np.where(durations >= durations[index])[0]
            value += float(x[index] @ beta) - float(logsumexp(x[risk] @ beta))
        return -value

    result = minimize(objective, np.zeros(len(covariates)), method="BFGS")
    risks = (x @ result.x).tolist()
    concordance = c_index(durations.tolist(), events.tolist(), risks)
    return {
        "status": "ok" if result.success or concordance is not None else "fit_failed",
        "covariates": covariates,
        "concordance_index": concordance,
        "coefficients": {name: float(value) for name, value in zip(covariates, result.x)},
        "events": int(events.sum()),
        "n": len(rows),
        "optimizer_message": str(result.message),
    }


def cox_summary(results: list[dict[str, Any]], metadata: list[dict[str, Any]]) -> dict[str, Any]:
    meta_by_worker = {row["worker_id"]: row for row in metadata}
    feature_names = ("compaction_last_le120", "edit_write_absent", "reread_max")
    by_seat: dict[int, list[dict[str, Any]]] = {seat: [] for seat in SEATS}
    for row in results:
        if row.get("http") != 200 or row.get("error"):
            continue
        worker = row["worker_id"]
        event = event_value(row)
        t = meta_by_worker[worker]["T"]
        by_seat[row["seat"]].append({
            "duration": float(event if event is not None else t),
            "event": int(event is not None),
            "features": meta_by_worker[worker]["markers"],
        })
    models: dict[str, Any] = {}
    for seat, rows in by_seat.items():
        models[f"seat_{seat}"] = {
            "|".join(name for name in feature_names if name != omitted): fit_cox(
                rows, [name for name in feature_names if name != omitted]
            )
            for omitted in feature_names
        }
    consensus_rows = []
    agreement = agreement_summary(results, metadata)
    for row in agreement["per_worker"]:
        values = [value for value in row["event_times_by_seat"] if value is not None]
        event = len(values) >= 2
        consensus_rows.append({
            "duration": float(sorted(values)[len(values) // 2] if event else meta_by_worker[row["worker_id"]]["T"]),
            "event": int(event),
            "features": meta_by_worker[row["worker_id"]]["markers"],
        })
    models["majority_consensus"] = {
        "|".join(name for name in feature_names if name != omitted): fit_cox(
            consensus_rows, [name for name in feature_names if name != omitted]
        )
        for omitted in feature_names
    }
    valid_concordances = [
        model.get("concordance_index")
        for group in models.values()
        for model in group.values()
        if model.get("status") == "ok" and model.get("concordance_index") is not None
    ]
    kill_fired = any(value < 0.60 for value in valid_concordances)
    return {
        "case_id": "PR-SURVIVAL-EVENT",
        "feature_set": "EX-MARKER-1A",
        "covariates": list(feature_names),
        "loo_definition": "Each model leaves one of the three preregistered features out.",
        "models": models,
        "valid_model_count": len(valid_concordances),
        "kill_threshold": 0.60,
        "kill_fired": kill_fired,
        "kill_rule_evaluated": bool(valid_concordances),
        "kill_note": "Any valid 2-covariate LOO concordance below 0.60 fires this gate.",
    }


def analyze(out: Path, results: list[dict[str, Any]], metadata: list[dict[str, Any]]) -> None:
    agreement = agreement_summary(results, metadata)
    cox = cox_summary(results, metadata)
    write_json(out / "agreement-summary.json", agreement)
    write_json(out / "cox-summary.json", cox)
    successful = [row for row in results if row.get("http") == 200 and not row.get("error")]
    meters = {
        "case_id": "PR-SURVIVAL-EVENT",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "planned_calls": len(WORKERS) * len(SEATS),
        "captured_rows": len(results),
        "successful_parsed_rows": len(successful),
        "errors": len(results) - len(successful),
        "http_counts": dict(Counter(str(row.get("http")) for row in results)),
        "choice_scrape_failures": sum(
            not bool((row.get("answers") or {}).get("event_time", {}).get("choice_scrape_ok"))
            for row in successful
        ),
        "stimulus_max_chars": max(row["stimulus_chars"] for row in metadata),
        "no_call_jev": True,
        "product_wiring": False,
        "localhost_8080_used": False,
        "kill_fired": cox["kill_fired"],
        "agreement_kill_fired": agreement["agreement_kill_fired"],
    }
    write_json(out / "meters.json", meters)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    protocol_stamp()
    out = args.output.resolve()
    if args.analyze_only:
        metadata = json.loads((out / "source-metadata.json").read_text(encoding="utf-8"))
        results = [
            json.loads(line)
            for line in (out / "results.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        analyze(out, results, metadata)
        return 0
    cells, metadata = prepare(out)
    if args.prepare_only:
        print(f"prepared {len(cells)} cells")
        return 0
    results = run_calls(out, cells, args.workers)
    analyze(out, results, metadata)
    print(f"completed {len(results)}/{len(cells)} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
