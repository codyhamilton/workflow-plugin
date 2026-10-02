#!/usr/bin/env python3
"""Materialize frozen batch-003 core cells; never invokes a judge."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BATCH_002 = HERE.parent / "batch-002"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def cell_id(
    driver: str,
    session_id: str,
    checkpoint: int,
    state: str,
    question: str,
    wording_id: str,
) -> str:
    raw = (
        f"batch003-v1|{driver}|{session_id}|{checkpoint}|"
        f"{state}|{question}|{wording_id}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def snapshot_paths() -> dict[str, str]:
    paths = {}
    for path in sorted((BATCH_002 / "snapshots-mid").glob("*.json")):
        row = load(path)
        session_id = row.get("worker_id") or path.stem
        paths[session_id] = str(path.relative_to(HERE))
    return paths


def core_cells(matrix: dict, strata: dict, drivers: set[str], blocks: set[str]):
    snapshots = snapshot_paths()
    checkpoint = matrix["core_state_contrast"]["checkpoint"]
    for session in strata["sessions"]:
        if session["block"] not in blocks:
            continue
        for driver in matrix["drivers"]:
            driver_id = driver["id"]
            if driver_id not in drivers:
                continue
            for state in matrix["states"]:
                for question in matrix["questions"]:
                    yield {
                        "cell_id": cell_id(
                            driver_id,
                            session["session_id"],
                            checkpoint,
                            state,
                            question,
                            "w0",
                        ),
                        "batch": "batch-003",
                        "design": "core_state_contrast",
                        "driver": driver_id,
                        "judge_role": driver["judge_role"],
                        "model": driver["model"],
                        "session_id": session["session_id"],
                        "checkpoint": checkpoint,
                        "state_variant": state,
                        "question_variant": question,
                        "question_text": matrix["question_text_w0"][question],
                        "wording_id": "w0",
                        "response_class": "binary_fire",
                        "block": session["block"],
                        "holdout": session["holdout"],
                        "harness": session["harness"],
                        "project": session["project"],
                        "maps_family": session["maps_family"],
                        "corpus_source": session["corpus_source"],
                        "state_contract": session["state_contract"],
                        "snapshot_source": snapshots[session["session_id"]],
                        "soft_standard_hold": True,
                        "product_wiring": False,
                        "window_status": "unidentified",
                        "outcome_tag": None,
                    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--driver",
        action="append",
        choices=["typesafe", "flash", "luna"],
        help="Repeat to select drivers; default is all.",
    )
    parser.add_argument(
        "--block",
        action="append",
        choices=[f"B{index:02d}" for index in range(1, 8)],
        help="Repeat to select blocks; default is all.",
    )
    parser.add_argument("--output", type=Path, help="Write JSONL instead of stdout.")
    parser.add_argument(
        "--summary", action="store_true", help="Print counts, not result rows."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    matrix = load(HERE / "TRIAL-MATRIX.json")
    strata = load(HERE / "SESSION-STRATA.json")
    drivers = set(args.driver or [row["id"] for row in matrix["drivers"]])
    blocks = set(args.block or [f"B{index:02d}" for index in range(1, 8)])
    rows = list(core_cells(matrix, strata, drivers, blocks))

    if args.summary:
        print(
            json.dumps(
                {
                    "soft_standard_hold": True,
                    "judge_calls": 0,
                    "drivers": sorted(drivers),
                    "blocks": sorted(blocks),
                    "n_cells": len(rows),
                    "n_sessions": len({row["session_id"] for row in rows}),
                    "n_states": len({row["state_variant"] for row in rows}),
                    "n_questions": len(
                        {row["question_variant"] for row in rows}
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    stream = args.output.open("w") if args.output else sys.stdout
    try:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    finally:
        if args.output:
            stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
