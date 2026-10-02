#!/usr/bin/env python3
"""Build a no-network coverage matrix for the response-class strata."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
BATCH = REPO / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
EXACT = BATCH / "typesafe-response-calibration/meters.json"
DIAGNOSTIC = BATCH / "typesafe-response-calibration-diagnostic/meters.json"
OUT_JSON = BATCH / "AXIS-MATRIX.json"
OUT_MD = BATCH / "AXIS-MATRIX.md"


def read(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing meters: {path}")
    data = json.loads(path.read_text())
    if data.get("status") != "complete":
        raise SystemExit(f"incomplete meters: {path}")
    return data


def main() -> int:
    exact = read(EXACT)
    diagnostic = read(DIAGNOSTIC)
    classes = exact["response_classes"]
    scenarios = sorted(
        {
            key.rsplit("|rc.", 1)[0]
            for key in exact["by_scenario_response_class"]
        }
        | {
            key.rsplit("|rc.", 1)[0]
            for key in diagnostic["by_scenario_response_class"]
        }
    )
    rows = []
    for scenario in scenarios:
        for response_class in classes:
            key = f"{scenario}|rc.{response_class}"
            exact_row = exact["by_scenario_response_class"].get(key)
            diagnostic_row = diagnostic["by_scenario_response_class"].get(key)
            rows.append(
                {
                    "scenario_id": scenario,
                    "response_class": response_class,
                    "exact_label_ready": exact_row,
                    "diagnostic_only": diagnostic_row,
                    "complete": bool(exact_row and diagnostic_row),
                }
            )
    matrix = {
        "wave": "typesafe-response-class-calibration",
        "status": "complete" if all(row["complete"] for row in rows) else "incomplete",
        "n_scenarios": len(scenarios),
        "n_response_classes": len(classes),
        "n_matrix_cells": len(rows),
        "exact_cells": exact["n_cells_successful"],
        "diagnostic_cells": diagnostic["n_cells_successful"],
        "exact_pairs": exact["n_representative_pairs"],
        "diagnostic_pairs": diagnostic["n_representative_pairs"],
        "raw_included": False,
        "diagnostic_only": True,
        "soft_standard_hold": True,
        "product_wiring": False,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(matrix, indent=2) + "\n")

    md = [
        "# AXIS MATRIX — TypeSafe response-class calibration",
        "",
        "**Soft Standard HOLD** — coverage inventory only; no product behavior.",
        "",
        f"- scenarios: **{matrix['n_scenarios']}**",
        f"- response classes: **{matrix['n_response_classes']}**",
        f"- exact-label-ready cells: **{matrix['exact_cells']}** (`12×9×4`)",
        f"- diagnostic-only cells: **{matrix['diagnostic_cells']}** (`12×7×4`)",
        f"- matrix status: **{matrix['status']}**",
        "",
        "| scenario | response class | exact n | diagnostic n |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        exact_n = (row["exact_label_ready"] or {}).get("n", 0)
        diagnostic_n = (row["diagnostic_only"] or {}).get("n", 0)
        md.append(
            f"| `{row['scenario_id']}` | `{row['response_class']}` | "
            f"{exact_n} | {diagnostic_n} |"
        )
    OUT_MD.write_text("\n".join(md) + "\n")
    print(
        json.dumps(
            {
                "status": matrix["status"],
                "scenarios": matrix["n_scenarios"],
                "response_classes": matrix["n_response_classes"],
                "exact_cells": matrix["exact_cells"],
                "diagnostic_cells": matrix["diagnostic_cells"],
            }
        )
    )
    return 0 if matrix["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
