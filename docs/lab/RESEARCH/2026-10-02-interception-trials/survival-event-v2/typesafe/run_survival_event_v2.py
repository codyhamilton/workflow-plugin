#!/usr/bin/env python3
"""Maps-only TypeSafe seats for PR-SURVIVAL-EVENT-v2."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


REPO = Path(__file__).resolve().parents[6]
PACK_DIR = (
    REPO
    / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates"
    / "proofs/validated/gold/packs"
)
OUT = Path(__file__).resolve().parent
RAW = OUT / "raw"
URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
PROTOCOL_PATH = Path("/home/codyh/workspace/corpus-ops/registry/survival-event/protocol-v2.json")
PROTOCOL_SHA256 = "eb3386c13c2936e83bef81ac21186c1a4a416ea3f196e391237d4c4b41d90bcd"
AEST = ZoneInfo("Australia/Brisbane")

WORKERS = {
    "92a48e004519": ("thrash", 296),
    "ca977b9ca0dd": ("thrash", 109),
    "87a380bc64ff": ("poll_monitor", 89),
    "bb6165018de0": ("poll_monitor", 154),
    "15f24c7ba18c": ("poll_monitor", 93),
    "8e36f8e80baa": ("poll_monitor", 97),
    "daf933273c8f": ("weak", 122),
    "07357f196666": ("weak", 83),
    "0677f597286e": ("residual", 93),
    "074c8cf22927": ("residual", 76),
    "0853bc21d3aa": ("residual", 155),
    "16a958631580": ("residual", 94),
}

STAGE_1 = {
    "type": "choice",
    "instructions": "In the shown window, did this trajectory become unproductive at some api_turn?",
    "labels": ["event_observed", "censored_productive", "censored_unclear"],
    "criteria": {
        "event_observed": "At least one api_turn is identified where continuing became a mistake.",
        "censored_productive": "The shown trajectory remained productive through the window.",
        "censored_unclear": "The evidence is insufficient to distinguish an event from productive continuation.",
    },
}
STAGE_2 = {
    "type": "choice",
    "answer_contract": "integer|null",
    "instructions": "If event_observed, return only the earliest api_turn integer where continuing became a mistake; otherwise return null.",
    "criteria": {
        "null": "No event was observed in the shown window.",
        **{str(turn): f"The earliest event occurred at api_turn {turn}." for turn in range(1, 151)},
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cell_id(worker_id: str, cutoff: int) -> str:
    return hashlib.sha256(
        f"PR-SURVIVAL-EVENT-v2|maps-only|{worker_id}|{cutoff}|stage_1-stage_2".encode()
    ).hexdigest()[:16]


def load_packs(worker_id: str, t: int) -> list[dict[str, Any]]:
    matches = sorted(PACK_DIR.glob(f"{worker_id}-judge-packs-*.jsonl"))
    if not matches:
        raise RuntimeError(f"frozen pack missing for {worker_id}")
    rows = [json.loads(line) for line in matches[-1].read_text().splitlines()]
    cutoff = min(t, 150)
    rows = [row for row in rows if row["checkpoint_turn"] <= cutoff]
    if not rows:
        raise RuntimeError(f"no checkpoints at or below {cutoff} for {worker_id}")
    return rows


def marker_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    latest = rows[-1].get("cumulative") or {}
    histogram = latest.get("tool_histogram") or {}
    rereads = latest.get("reread_paths") or []
    reread_max = max(
        (item.get("count", 0) for item in rereads if isinstance(item, dict)),
        default=0,
    )
    return {
        "reread_max": reread_max,
        "compaction_event_count": latest.get("compaction_event_count", 0),
        "Edit_count": histogram.get("Edit", 0),
        "Write_count": histogram.get("Write", 0),
    }


def build_cells() -> list[dict[str, Any]]:
    cells = []
    for worker_id, (stratum, t) in WORKERS.items():
        cutoff = min(t, 150)
        rows = load_packs(worker_id, t)
        features = marker_features(rows)
        cells.append(
            {
                "cell_id": cell_id(worker_id, cutoff),
                "worker_id": worker_id,
                "stratum": stratum,
                "T": t,
                "window_cutoff": cutoff,
                "checkpoint_turns": [row["checkpoint_turn"] for row in rows],
                "driver": "TypeSafe",
                "model": MODEL,
                "framing": "PR-SURVIVAL-EVENT-v2 two-stage event Q",
                "protocol_sha256": PROTOCOL_SHA256,
                "maps_only": True,
                "behaviour_ship": False,
                "no_call_jev": True,
                "no_8080": True,
                "pack_source": str(PACK_DIR.relative_to(REPO)),
                "marker_features": features,
                "request": {
                    "model": MODEL,
                    "state": {
                        "evidence_class": "hybrid_v0",
                        "framing": "PR-SURVIVAL-EVENT-v2",
                        "window_rule": "rows through last available cps <= min(T, 150)",
                        "marker_features": features,
                        "snapshot": rows,
                    },
                    "questions": {
                        "stage_1": STAGE_1,
                        "stage_2": STAGE_2,
                        "rationale": {
                            "type": "noul",
                            "instructions": "One line citing a marker or tool pattern.",
                        },
                    },
                },
            }
        )
    return cells


def answer_value(answer: dict[str, Any]) -> Any:
    if answer.get("type") == "choice":
        return answer.get("choice")
    return answer.get("value", answer.get("text"))


def integer_or_null(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = str(value).strip().lower().strip("`")
    if text in {"", "null", "none", "n/a"}:
        return None
    try:
        return int(text)
    except ValueError:
        return value


def parse_answers(payload: dict[str, Any]) -> dict[str, Any]:
    answers = payload.get("answers") or {}
    parsed = {}
    for question_id in ("stage_1", "stage_2", "rationale"):
        answer = answers.get(question_id) or {}
        response_label = answer.get("choice") if answer.get("type") == "choice" else None
        response_class = response_label if answer.get("type") == "choice" else answer.get("type")
        parsed[question_id] = {
            "wire_type": answer.get("type"),
            "response_class": response_class,
            "response_label": response_label,
            "choice_scrape_ok": (
                answer.get("type") != "choice"
                or response_label is not None and response_class == response_label
            ),
            "value": answer_value(answer),
        }
    stage_1 = parsed["stage_1"]["response_label"]
    stage_2 = integer_or_null(
        parsed["stage_2"]["response_label"]
        if parsed["stage_2"]["wire_type"] == "choice"
        else parsed["stage_2"]["value"]
    )
    parsed["stage_2"]["value"] = stage_2
    parsed["gate_ok"] = (
        stage_2 is not None
        if stage_1 == "event_observed"
        else stage_2 is None
    )
    return parsed


def post(cell: dict[str, Any], key: str) -> dict[str, Any]:
    body = json.loads(json.dumps(cell["request"]))
    body["state"]["checkpoint_turn"] = max(cell["checkpoint_turns"])
    request_path = RAW / f"{cell['cell_id']}-request.json"
    request_path.write_text(json.dumps(body, indent=2) + "\n")
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    started = time.time()
    base = {k: cell[k] for k in (
        "cell_id", "worker_id", "stratum", "T", "window_cutoff",
        "checkpoint_turns", "driver", "model", "framing", "protocol_sha256",
        "maps_only", "behaviour_ship", "no_call_jev", "no_8080", "marker_features",
    )}
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            text = response.read().decode()
            payload = json.loads(text)
            status = response.status
        (RAW / f"{cell['cell_id']}-response.json").write_text(text + "\n")
        answers = parse_answers(payload)
        return {
            **base,
            "http": status,
            "error": None,
            "answers": answers,
            "choice_scrape_ok": all(
                answers[question_id]["choice_scrape_ok"]
                for question_id in ("stage_1", "stage_2")
            ),
            "raw_response": f"raw/{cell['cell_id']}-response.json",
            "usage": payload.get("usage"),
            "ts": datetime.now(AEST).isoformat(timespec="seconds"),
            "wall_s": round(time.time() - started, 3),
        }
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        (RAW / f"{cell['cell_id']}-error.txt").write_text(f"HTTP {error.code}\n{detail}\n")
        return {**base, "http": error.code, "error": detail[:1000],
                "raw_response": f"raw/{cell['cell_id']}-error.txt",
                "ts": datetime.now(AEST).isoformat(timespec="seconds"),
                "wall_s": round(time.time() - started, 3)}
    except Exception as error:
        return {**base, "http": None, "error": f"{type(error).__name__}: {error}",
                "ts": datetime.now(AEST).isoformat(timespec="seconds"),
                "wall_s": round(time.time() - started, 3)}


def write_analysis(rows: list[dict[str, Any]]) -> None:
    successful = [row for row in rows if row.get("http") == 200 and not row.get("error")]
    by_stratum: dict[str, dict[str, Any]] = {}
    for stratum in sorted({row["stratum"] for row in rows}):
        group = [row for row in successful if row["stratum"] == stratum]
        labels = Counter((row.get("answers") or {}).get("stage_1", {}).get("response_label") for row in group)
        events = [
            (row["worker_id"], (row.get("answers") or {}).get("stage_2", {}).get("value"))
            for row in group
            if (row.get("answers") or {}).get("stage_1", {}).get("response_label") == "event_observed"
        ]
        by_stratum[stratum] = {
            "n": len(group),
            "stage_1_counts": dict(labels),
            "event_observed_seats": len(events),
            "event_times": events,
            "gate_failures": sum(
                not bool((row.get("answers") or {}).get("gate_ok")) for row in group
            ),
        }
    event_rows = [
        row for row in successful
        if (row.get("answers") or {}).get("stage_1", {}).get("response_label") == "event_observed"
    ]
    event_times = [
        (row["worker_id"], (row.get("answers") or {}).get("stage_2", {}).get("value"))
        for row in event_rows
    ]
    agreement = {
        "status": "estimable" if event_rows else "no_observed_events",
        "event_observed_seat_count": len(event_rows),
        "event_time_values": [value for _, value in event_times],
        "exact_pair_agreement": (
            sum(a == b for a in [v for _, v in event_times] for b in [v for _, v in event_times])
            / (len(event_times) ** 2)
            if event_times else None
        ),
        "by_stratum": by_stratum,
        "gate_failures": sum(
            not bool((row.get("answers") or {}).get("gate_ok")) for row in successful
        ),
    }
    (OUT / "agreement-summary.json").write_text(json.dumps(agreement, indent=2, sort_keys=True) + "\n")
    cox = {
        "status": "eligible" if len(event_rows) >= 2 else "not_estimable",
        "reason": "Exploratory Cox requires >=2 observed events.",
        "observed_events": len(event_rows),
        "covariates": ["reread_max", "compaction_event_count", "Edit_count", "Write_count"],
    }
    (OUT / "cox-summary.json").write_text(json.dumps(cox, indent=2, sort_keys=True) + "\n")


def main() -> int:
    if sha256(PROTOCOL_PATH) != PROTOCOL_SHA256:
        raise RuntimeError("protocol-v2 sha256 mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    cells = build_cells()
    seat_cells = []
    for cell in cells:
        for seat in range(1, 4):
            seat_cell = json.loads(json.dumps(cell))
            seat_cell["seat"] = seat
            seat_cell["cell_id"] = hashlib.sha256(
                f"{cell['cell_id']}|seat-{seat}".encode()
            ).hexdigest()[:16]
            seat_cells.append(seat_cell)
    (OUT / "cell-manifest.json").write_text(json.dumps({
        "case_id": "PR-SURVIVAL-EVENT-v2",
        "supersedes": "PR-SURVIVAL-EVENT (#134)",
        "seat_definition": "one TypeSafe request per worker; 12 workers x 3 seats",
        "seat_count": len(cells) * 3,
        "workers": WORKERS,
        "cells": seat_cells,
        "cell_ids": [cell["cell_id"] for cell in seat_cells],
        "stage_1": STAGE_1,
        "stage_2": STAGE_2,
        "protocol_sha256": PROTOCOL_SHA256,
        "maps_only": True,
        "behaviour_ship": False,
        "no_call_jev": True,
        "no_8080": True,
    }, indent=2, sort_keys=True) + "\n")
    # Three independent seats per worker. Cell IDs include seat ordinal.
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is missing; no seats were called")
    results_path = OUT / "results.jsonl"
    done = {}
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try:
                row = json.loads(line)
                done[row["cell_id"]] = row
            except (ValueError, KeyError):
                pass
    todo = [cell for cell in seat_cells if cell["cell_id"] not in done or done[cell["cell_id"]].get("error")]
    with ThreadPoolExecutor(max_workers=4) as executor, results_path.open("a") as output:
        futures = [executor.submit(post, cell, key) for cell in todo]
        for future in as_completed(futures):
            row = future.result()
            done[row["cell_id"]] = row
            output.write(json.dumps(row, sort_keys=True) + "\n")
            output.flush()
    rows = [done[cell["cell_id"]] for cell in seat_cells if cell["cell_id"] in done]
    results_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    meters = {
        "status": "complete" if len(rows) == len(seat_cells) else "partial",
        "planned_seats": len(seat_cells),
        "captured_seats": len(rows),
        "successful_seats": sum(row.get("http") == 200 and not row.get("error") for row in rows),
        "errors": sum(bool(row.get("error")) for row in rows),
        "http_counts": dict(Counter(str(row.get("http")) for row in rows)),
        "choice_scrape_ok": sum(bool(row.get("choice_scrape_ok")) for row in rows),
        "choice_scrape_failures": sum(not bool(row.get("choice_scrape_ok")) for row in rows),
        "protocol_sha256": PROTOCOL_SHA256,
        "driver": "TypeSafe",
        "model": MODEL,
        "wire": "noul",
        "framing": "two-stage event Q",
        "maps_only": True,
        "behaviour_ship": False,
        "no_call_jev": True,
        "no_8080": True,
        "generated_at": datetime.now(AEST).isoformat(timespec="seconds"),
    }
    (OUT / "meters.json").write_text(json.dumps(meters, indent=2, sort_keys=True) + "\n")
    write_analysis(rows)
    print(json.dumps(meters, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
