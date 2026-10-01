#!/usr/bin/env python3
"""Phase 1a — marker screen + survival/Cox sketch (0 network calls)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from marker_analysis import analyze  # noqa: E402
from marker_features import build_all_features  # noqa: E402
from paths import phase_out_dir  # noqa: E402
from theme_strata import strata_table  # noqa: E402

# Cox runner shares lib on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import run_cox_sketch  # noqa: E402


def _markdown(
    *,
    mismatch_count: int,
    kill: dict[str, Any],
    analysis: dict[str, Any],
    cox: dict[str, Any],
) -> str:
    strict = analysis["combined_thrash_screen_strict"]
    lines = [
        "# Phase 1a — marker screen (`marker-screen-margin`)",
        "",
        "**Approach:** `marker-screen-margin` · **API calls:** 0 · **Pack:** shape-qual-full-maps-v1 (n=34)",
        "",
        f"**Round-trip gate:** {'PASS' if mismatch_count == 0 else 'FAIL'} "
        f"(mismatch rows={mismatch_count})",
        "",
        f"**Kill check (thrash_screen_strict cell vs poll labels):** {strict['kill_check']}",
        "",
        f"- Strict cell workers ({len(strict['cell_workers'])}): "
        + ", ".join(f"`{w}`" for w in strict["cell_workers"]),
        f"- Poll overlap: "
        + (
            ", ".join(f"`{w}`" for w in strict["poll_label_overlap"])
            if strict["poll_label_overlap"]
            else "none"
        ),
        "",
        "## Spearman vs T (numeric families)",
        "",
        "| family | ρ all | ρ without thrash prototypes | poll overlap in extreme tail |",
        "|--------|------:|----------------------------:|------------------------------|",
    ]
    for fam, block in analysis["numeric_families"].items():
        if block.get("skipped"):
            lines.append(f"| `{fam}` | — | — | skipped |")
            continue
        overlap = block.get("poll_label_overlap") or []
        lines.append(
            f"| `{fam}` | {block.get('spearman_vs_T')} | "
            f"{block.get('spearman_vs_T_without_thrash_prototypes')} | "
            f"{len(overlap)} |"
        )
    lines.extend(
        [
            "",
            "## Cox sketch (exploratory)",
            "",
            f"- Status: `{cox.get('status')}`",
            f"- Concordance index: {cox.get('concordance_index')}",
            f"- Future gate (concordance ≤ 0.70): "
            f"{'would KILL' if cox.get('future_kill_would_fire') else 'would not kill'} Alternate E on this proxy",
            "",
            "See `cox_sketch.json` and `run_cox_sketch.py`.",
            "",
        ]
    )
    return "\n".join(lines)


def _rank_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# Marker rank tables (phase 1a)",
        "",
        "## Combined kill cell — `thrash_screen_strict`",
        "",
    ]
    strict = analysis["combined_thrash_screen_strict"]
    lines.append(f"**Kill check:** {strict['kill_check']}")
    lines.append("")
    lines.append("Workers: " + ", ".join(f"`{w}`" for w in strict["cell_workers"]))
    lines.append("")
    lines.append("## Boolean families (thrash prototype cell + poll overlap)",
    )
    lines.append("")
    lines.append("| family | cell n | poll overlap |")
    lines.append("|--------|-------:|--------------|")
    for fam, block in analysis["boolean_families"].items():
        if block.get("skipped"):
            continue
        overlap = block.get("poll_label_overlap") or []
        lines.append(
            f"| `{fam}` | {block.get('n_in_cell', '—')} | "
            + (", ".join(f"`{w}`" for w in overlap) if overlap else "none")
            + " |"
        )
    lines.extend(["", "## Numeric families", ""])
    lines.append("| family | ρ vs T | ρ vs T (no thrash prototypes) | thrash pct ca977 | thrash pct 92a48e | poll overlap |")
    lines.append("|--------|-------:|------------------------------:|-----------------:|------------------:|--------------|")
    for fam, block in analysis["numeric_families"].items():
        if block.get("skipped"):
            continue
        tp = block.get("thrash_consensus_percentile") or {}
        overlap = block.get("poll_label_overlap") or []
        lines.append(
            f"| `{fam}` | {block.get('spearman_vs_T')} | "
            f"{block.get('spearman_vs_T_without_thrash_prototypes')} | "
            f"{tp.get('ca977b9ca0dd')} | {tp.get('92a48e004519')} | "
            f"{len(overlap)} |"
        )
    lines.append("")
    return "\n".join(lines)


def _cycle_result(kill: str, mismatch: int) -> str:
    status = "killed" if kill == "KILL" else "gate_cleared"
    return "\n".join(
        [
            "# CYCLEResult — phase 1a",
            "",
            "| field | value |",
            "|-------|-------|",
            f"| cycle_id | `phase-1a-marker-screen` |",
            f"| approach | `marker-screen-margin` |",
            f"| status | `{status}` |",
            f"| api_calls | 0 |",
            f"| kill_check | `{kill}` |",
            f"| round_trip_mismatches | {mismatch} |",
            f"| artifacts | `proofs/phase-1a/` |",
            "",
        ]
    )


def main() -> int:
    out = phase_out_dir("phase-1a")
    out.mkdir(parents=True, exist_ok=True)

    rows = build_all_features()
    mismatch_count = sum(1 for r in rows if r["markers"]["round_trip_mismatch"])

    with (out / "marker_features.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    (out / "theme_strata.json").write_text(
        json.dumps(strata_table(), indent=2) + "\n", encoding="utf-8"
    )

    analysis = analyze(rows)
    (out / "marker_analysis.json").write_text(
        json.dumps(analysis, indent=2) + "\n", encoding="utf-8"
    )

    poll_doc = {
        "combined_thrash_screen_strict": analysis["combined_thrash_screen_strict"],
        "boolean_poll_overlaps": {
            k: v.get("poll_label_overlap")
            for k, v in analysis["boolean_families"].items()
            if v.get("poll_label_overlap")
        },
        "numeric_poll_overlaps": {
            k: v.get("poll_label_overlap")
            for k, v in analysis["numeric_families"].items()
            if v.get("poll_label_overlap")
        },
    }
    (out / "poll_overlap.json").write_text(
        json.dumps(poll_doc, indent=2) + "\n", encoding="utf-8"
    )
    (out / "rank_tables.md").write_text(_rank_markdown(analysis), encoding="utf-8")

    cox = run_cox_sketch.run_sketch(rows)
    (out / "cox_sketch.json").write_text(json.dumps(cox, indent=2) + "\n", encoding="utf-8")

    kill = analysis["combined_thrash_screen_strict"]["kill_check"]
    (out / "SPIKE-RESULT.md").write_text(
        _markdown(
            mismatch_count=mismatch_count,
            kill=analysis["combined_thrash_screen_strict"],
            analysis=analysis,
            cox=cox,
        ),
        encoding="utf-8",
    )
    (out / "CYCLEResult.md").write_text(_cycle_result(kill, mismatch_count), encoding="utf-8")

    summary = {
        "workers": len(rows),
        "round_trip_mismatch_workers": mismatch_count,
        "kill_check": kill,
        "cox_status": cox.get("status"),
        "concordance_index": cox.get("concordance_index"),
    }
    print(json.dumps(summary, indent=2))
    gate_ok = mismatch_count == 0
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
