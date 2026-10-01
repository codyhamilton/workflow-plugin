#!/usr/bin/env python3
"""Pilot segment swarm — plan + provider backends (dry-stub default)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from capture_io import utc_now_iso, write_jsonl, write_meters  # noqa: E402
from paths import capture_local_swarm_dir, capture_root, validated_dir  # noqa: E402
from pilot_wave import REGISTRATION_ID  # noqa: E402
from segment_swarm import pilot_swarm_plan  # noqa: E402
from swarm_providers import (  # noqa: E402
    PILOT_SWARM_PROVIDER_DEFAULT,
    PILOT_SWARM_PROVIDERS,
    complete_cell,
)


def _resolve_provider(args: argparse.Namespace) -> str:
    if args.live_local and args.provider is None:
        return "local"
    if args.provider is not None:
        return args.provider
    env = os.environ.get("WORKFLOW_SWARM_PROVIDER", "").strip().lower()
    if env in PILOT_SWARM_PROVIDERS:
        return env
    return PILOT_SWARM_PROVIDER_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=PILOT_SWARM_PROVIDERS,
        default=None,
        help=f"Swarm backend (default {PILOT_SWARM_PROVIDER_DEFAULT}): luna (Codex gpt-6-luna), flash (OpenCode DeepSeek, optional), local (:8080 legacy)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Invoke the provider (default off on cloud VM)",
    )
    parser.add_argument(
        "--live-local",
        action="store_true",
        help="Deprecated alias for --provider local --live",
    )
    args = parser.parse_args()

    provider = _resolve_provider(args)
    live = args.live or args.live_local

    plan = pilot_swarm_plan()
    out_dir = capture_local_swarm_dir("pilot-field-proof")
    out_dir.mkdir(parents=True, exist_ok=True)
    reg_dir = capture_root("pilot-field-proof")
    (reg_dir / "local_swarm_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    mode_label = f"live-{provider}" if live else "dry-stub"
    completion_rows = []
    for i, cell in enumerate(plan["cells"]):
        outcome = complete_cell(provider, cell, live=live)
        completion_rows.append(
            {
                "ts": utc_now_iso(),
                "registration_id": REGISTRATION_ID,
                "cell_index": i,
                "mode": mode_label,
                "swarm_provider": provider,
                **cell,
                **outcome,
            }
        )

    write_jsonl(out_dir / "segment_cells.jsonl", iter(plan["cells"]))
    write_jsonl(out_dir / "completions.jsonl", iter(completion_rows))

    conflict_report = {
        "registration_id": REGISTRATION_ID,
        "status": "registered_awaiting_live" if not live else f"{provider}_probe",
        "swarm_provider": provider,
        "cell_count": plan["cell_count"],
        "flash_arbiter_cap": plan["flash_arbiter_cap"],
        "conflict_workers": [],
        "parse_fail_workers": [],
        "note": (
            "Conflict detection runs after live completions on Ubuntu harness. "
            "Default pilot provider is Luna; Flash is optional when OpenCode seat recovers."
        ),
    }
    (out_dir / "conflict_report.json").write_text(
        json.dumps(conflict_report, indent=2) + "\n",
        encoding="utf-8",
    )

    live_count = sum(1 for r in completion_rows if str(r.get("decision", "")).startswith("live"))
    write_meters(
        out_dir / "meters.json",
        {
            "registration_id": REGISTRATION_ID,
            "swarm_provider": provider,
            "local_completions": live_count,
            "local_completions_planned": plan["cell_count"],
            "mode": mode_label,
        },
    )

    validated = validated_dir("pilot-field-proof")
    validated.mkdir(parents=True, exist_ok=True)
    (validated / "local_swarm_stub_log.json").write_text(
        json.dumps({"plan": plan, "conflict_report": conflict_report, "provider": provider}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "cells": plan["cell_count"],
                "provider": provider,
                "live": live,
                "capture": str(out_dir.relative_to(ROOT.parents[3])),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
