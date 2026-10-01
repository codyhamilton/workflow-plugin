#!/usr/bin/env python3
"""Spike 2 — batch dry-run, dedupe, caps (no live POST)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from batch_trial import batch_trial
from paths import proofs_out_dir
from trial_segments import segments_for_spike2

DUMMY_KEY = "typesafe-dummy-key-for-spike2-grep-test-not-real"


def main() -> int:
    out_dir = proofs_out_dir("spike-2")
    out_dir.mkdir(parents=True, exist_ok=True)
    segments = segments_for_spike2()
    dup_seg = segments[0]["segment_id"]
    framings = ["signal-v0-default", "signal-v0-alt"]

    dry = batch_trial(
        schema_id="early-signal-v0",
        framing_slugs=framings,
        segments=segments,
        live=False,
        confirm_live=False,
        duplicate_cells=[(dup_seg, framings[0])],
    )

    os.environ["TYPESAFE_API_KEY"] = DUMMY_KEY
    capped = batch_trial(
        schema_id="early-signal-v0",
        framing_slugs=framings,
        segments=segments,
        live=True,
        confirm_live=True,
        max_calls=1,
        duplicate_cells=None,
    )
    rejected = batch_trial(
        schema_id="early-signal-v0",
        framing_slugs=framings,
        segments=segments,
        live=True,
        confirm_live=True,
        max_calls=257,
    )

    combined = json.dumps({"dry": dry, "capped": capped, "rejected": rejected})
    leak = DUMMY_KEY in combined

    cap_cells = [c for c in capped["cells"] if c.get("reason") == "cap"]
    dup_once = sum(1 for c in dry["cells"] if c.get("reason") == "duplicate_input") == 1

    expected_unique = len(framings) * len(segments)
    checks = {
        "dry_run_decisions": all(c.get("decision") == "dry_run" for c in dry["cells"]),
        "cartesian_unique_count": dry["unique_cell_count"] == expected_unique,
        "duplicate_input_once": dup_once,
        "duplicate_post_rate_zero": dry["duplicate_post_rate"] == 0.0,
        "dry_run_ignores_cap": not dry.get("rejected") and dry["capped"] == 0,
        "live_shaped_cap_cells": len(cap_cells) > 0 and capped["posts"] == 1,
        "max_calls_257_rejected": rejected.get("rejected") and rejected.get("reason") == "max_calls_above_256",
        "no_api_key_leak": not leak,
        "no_live_post": _no_socket_activity(),
    }
    checks["all_pass"] = all(checks.values())

    payload = {"dry": dry, "capped": capped, "rejected": rejected, "checks": checks}
    out_json = out_dir / "batch_trial_results.json"
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    grep = subprocess.run(
        ["grep", "-F", DUMMY_KEY, str(out_json)],
        capture_output=True,
        text=True,
    )
    checks["grep_dummy_key_absent"] = grep.returncode != 0
    checks["all_pass"] = all(checks.values())

    (out_dir / "SPIKE-RESULT.md").write_text(_md(checks), encoding="utf-8")
    print(json.dumps({"gate_pass": checks["all_pass"]}, indent=2))
    return 0 if checks["all_pass"] else 1


def _no_socket_activity() -> bool:
    """Harness never imports urllib for POST in this spike."""
    from pathlib import Path as P

    lib = P(__file__).resolve().parent / "lib"
    for name in ("classify.py", "batch_trial.py"):
        text = (lib / name).read_text(encoding="utf-8")
        if "urllib" in text or "post_systemone" in text:
            return False
    return True


def _md(checks: dict) -> str:
    lines = [
        "# Spike 2 — batch dry-run",
        "",
        f"**Gate:** {'PASS' if checks['all_pass'] else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        if k == "all_pass":
            continue
        lines.append(f"- `{k}`: {'pass' if v else '**fail**'}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
