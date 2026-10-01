#!/usr/bin/env python3
"""Spike 0 — segment inventory, no network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from paths import proofs_out_dir  # noqa: E402
from segment_inventory import write_inventory  # noqa: E402


def main() -> int:
    out_dir = proofs_out_dir("spike-0")
    result = write_inventory(out_dir / "segment_inventory.jsonl")
    (out_dir / "gate_checks.json").write_text(
        json.dumps(result["checks"], indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "spike": 0,
        "row_count": result["row_count"],
        "gate_pass": result["checks"]["all_pass"],
        "checks": result["checks"],
    }
    (out_dir / "SPIKE-RESULT.md").write_text(
        _markdown(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["gate_pass"] else 1


def _markdown(summary: dict) -> str:
    lines = [
        "# Spike 0 — segment inventory",
        "",
        f"**Gate:** {'PASS' if summary['gate_pass'] else 'FAIL'}",
        "",
        f"Rows written: {summary['row_count']} (`segment_inventory.jsonl`).",
        "",
        "## Done-when checks",
        "",
    ]
    for key, ok in summary["checks"].items():
        if key == "all_pass":
            continue
        lines.append(f"- `{key}`: {'pass' if ok else '**fail**'}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
