#!/usr/bin/env python3
"""Pilot local segment swarm — plan + dry stub (no :8080 unless --live-local)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from capture_io import utc_now_iso, write_jsonl, write_meters  # noqa: E402
from paths import capture_local_swarm_dir, capture_root, validated_dir  # noqa: E402
from pilot_wave import REGISTRATION_ID  # noqa: E402
from segment_swarm import pilot_swarm_plan  # noqa: E402

LOCAL_PROMPT = (
    "Return JSON only: {\"phase_tag\": <string>, \"theme_guess\": one of "
    "thrash_bundle|poll_monitor|productive|unknown}."
)


def _local_url() -> str:
    base = os.environ.get("WORKFLOW_LOCAL_LLM_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    return f"{base}/chat/completions"


def _try_local_completion(cell: dict) -> dict:
    url = _local_url()
    body = json.dumps(
        {
            "model": "local",
            "messages": [
                {"role": "system", "content": LOCAL_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"segment_id": cell["segment_id"], "worker_id": cell["worker_id"]},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return {"decision": "live_local", "response": payload, "error": None}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"decision": "missing", "response": None, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live-local",
        action="store_true",
        help="POST to WORKFLOW_LOCAL_LLM_URL (default off on cloud VM)",
    )
    args = parser.parse_args()

    plan = pilot_swarm_plan()
    out_dir = capture_local_swarm_dir("pilot-field-proof")
    out_dir.mkdir(parents=True, exist_ok=True)
    reg_dir = capture_root("pilot-field-proof")
    (reg_dir / "local_swarm_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    completion_rows = []
    for i, cell in enumerate(plan["cells"]):
        if args.live_local:
            outcome = _try_local_completion(cell)
        else:
            outcome = {"decision": "dry_stub", "response": None, "error": None}
        completion_rows.append(
            {
                "ts": utc_now_iso(),
                "registration_id": REGISTRATION_ID,
                "cell_index": i,
                "mode": "live-local" if args.live_local else "dry-stub",
                **cell,
                **outcome,
            }
        )

    write_jsonl(out_dir / "segment_cells.jsonl", iter(plan["cells"]))
    write_jsonl(out_dir / "completions.jsonl", iter(completion_rows))

    conflict_report = {
        "registration_id": REGISTRATION_ID,
        "status": "registered_awaiting_live" if not args.live_local else "local_probe",
        "cell_count": plan["cell_count"],
        "flash_arbiter_cap": plan["flash_arbiter_cap"],
        "conflict_workers": [],
        "parse_fail_workers": [],
        "note": "Conflict detection runs after live local completions on Ubuntu harness.",
    }
    (out_dir / "conflict_report.json").write_text(
        json.dumps(conflict_report, indent=2) + "\n",
        encoding="utf-8",
    )

    write_meters(
        out_dir / "meters.json",
        {
            "registration_id": REGISTRATION_ID,
            "local_completions": plan["cell_count"] if args.live_local else 0,
            "local_completions_planned": plan["cell_count"],
            "mode": "live-local" if args.live_local else "dry-stub",
        },
    )

    validated = validated_dir("pilot-field-proof")
    validated.mkdir(parents=True, exist_ok=True)
    (validated / "local_swarm_stub_log.json").write_text(
        json.dumps({"plan": plan, "conflict_report": conflict_report}, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "cells": plan["cell_count"],
                "live_local": args.live_local,
                "capture": str(out_dir.relative_to(ROOT.parents[3])),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
