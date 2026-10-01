#!/usr/bin/env python3
"""Join TypeSafe lever-wave rows to independent batch-002 outcome labels.

The output is a derived Soft HOLD mapping only. It does not rewrite source
results, inspect model ratings/fire decisions, or compute FP/miss metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from window_status_join import (
    JoinError,
    derive_rows,
    index_labels,
    load_jsonl,
)

EXPECTED_SIGNATURE = ("typesafe", "Wave-0-multi")
OUT_OF_SCOPE_STREAMS = {
    "typesafe-scenario-sweep": (
        "scenario corpus, not a lever wave; coverage is tracked in "
        "WINDOW-STATUS-JOIN.md"
    ),
    "typesafe-review-check": "review-check axis, not an interception lever wave",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise JoinError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise JoinError(f"{path}: expected a JSON object")
    return value


def stream_sort_key(item: tuple[Path, list[dict[str, Any]]]) -> tuple[int, str]:
    name = item[0].parent.name
    return (0 if name == "typesafe" else 1, name)


def discover_lever_streams(
    batch: Path,
) -> tuple[
    list[tuple[Path, list[dict[str, Any]]]],
    list[dict[str, Any]],
]:
    """Find committed TypeSafe Wave-0-multi results and explicit exclusions."""
    streams: list[tuple[Path, list[dict[str, Any]]]] = []
    exclusions: list[dict[str, Any]] = []
    for path in sorted(batch.glob("typesafe*/results.jsonl")):
        rows = load_jsonl(path)
        signatures = {(row.get("driver"), row.get("wave")) for row in rows}
        if signatures == {EXPECTED_SIGNATURE}:
            streams.append((path, rows))
            continue
        if EXPECTED_SIGNATURE in signatures:
            raise JoinError(
                f"{path}: mixes TypeSafe lever rows with other result schemas"
            )
        stream = path.parent.name
        reason = OUT_OF_SCOPE_STREAMS.get(
            stream,
            "does not declare driver=typesafe and wave=Wave-0-multi",
        )
        exclusions.append(
            {
                "stream": stream,
                "source_result": str(path.relative_to(batch)),
                "result_rows": len(rows),
                "reason": reason,
            }
        )
    streams.sort(key=stream_sort_key)
    return streams, exclusions


def discover_meter_only_streams(batch: Path) -> list[dict[str, Any]]:
    """Report TypeSafe lever meters whose row-level results are not committed."""
    meter_only: list[dict[str, Any]] = []
    for path in sorted(batch.glob("typesafe*/meters.json")):
        meters = load_json(path)
        if (
            (meters.get("driver"), meters.get("wave")) != EXPECTED_SIGNATURE
            or (path.parent / "results.jsonl").exists()
        ):
            continue
        meter_only.append(
            {
                "stream": path.parent.name,
                "meters": str(path.relative_to(batch)),
                "reported_cells": meters.get("n_cells"),
                "reason": (
                    "results.jsonl is not committed, so session_id + checkpoint "
                    "join coverage cannot be measured"
                ),
            }
        )
    return meter_only


def count_values(
    rows: list[dict[str, Any]], field: str, values: tuple[str, ...]
) -> dict[str, int]:
    counts = Counter(row[field] for row in rows)
    return {value: counts.get(value, 0) for value in values}


def build_join(
    batch: Path,
    labels_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    labels = index_labels(load_jsonl(labels_path))
    streams, exclusions = discover_lever_streams(batch)
    if not streams:
        raise JoinError(f"{batch}: no committed TypeSafe lever-wave results found")

    all_derived: list[dict[str, Any]] = []
    joined_rows: list[dict[str, Any]] = []
    per_stream: list[dict[str, Any]] = []
    result_sessions: set[str] = set()
    labeled_result_sessions: set[str] = set()
    key_statuses: dict[tuple[str, int], str] = {}
    key_eligibility: dict[tuple[str, int], str] = {}

    for path, results in streams:
        source_result = str(path.relative_to(batch))
        derived = derive_rows(results, labels)
        for row in derived:
            source_row_id = row["derived_row_id"]
            row["source_result"] = source_result
            row["derived_row_id"] = f"{source_result}:{source_row_id}"
            key = (row["session_id"], row["checkpoint"])
            prior_status = key_statuses.setdefault(key, row["window_status"])
            prior_eligibility = key_eligibility.setdefault(
                key, row["label_join_eligibility"]
            )
            if prior_status != row["window_status"]:
                raise JoinError(f"inconsistent window status for join key {key!r}")
            if prior_eligibility != row["label_join_eligibility"]:
                raise JoinError(f"inconsistent label eligibility for join key {key!r}")
            result_sessions.add(row["session_id"])
            if row["label_status"] == "labeled":
                labeled_result_sessions.add(row["session_id"])
            if row["label_join_eligibility"] == "label_join_exact":
                joined_rows.append(row)
        all_derived.extend(derived)

        exact_rows = sum(
            row["label_join_eligibility"] == "label_join_exact" for row in derived
        )
        stream_sessions = {row["session_id"] for row in derived}
        stream_keys = {(row["session_id"], row["checkpoint"]) for row in derived}
        per_stream.append(
            {
                "stream": path.parent.name,
                "source_result": source_result,
                "result_rows": len(results),
                "joined_rows": exact_rows,
                "unjoined_rows": len(results) - exact_rows,
                "coverage_fraction": round(exact_rows / len(results), 6)
                if results
                else None,
                "result_sessions": len(stream_sessions),
                "unique_session_checkpoints": len(stream_keys),
            }
        )

    eligibility_values = (
        "label_join_exact",
        "session_unlabeled",
        "checkpoint_unlabeled",
        "session_not_labeled",
        "label_excluded",
    )
    window_values = (
        "inside_steer_window",
        "outside_steer_window",
        "no_steer_window",
        "ambiguous",
        "unidentified",
    )
    eligibility_rows = count_values(
        all_derived, "label_join_eligibility", eligibility_values
    )
    unique_eligibility = Counter(key_eligibility.values())
    unique_statuses = Counter(key_statuses.values())
    missing_keys = sorted(
        (
            {"session_id": session_id, "checkpoint": checkpoint, "reason": eligibility}
            for (session_id, checkpoint), eligibility in key_eligibility.items()
            if eligibility != "label_join_exact"
        ),
        key=lambda row: (row["session_id"], row["checkpoint"]),
    )
    meter_only = discover_meter_only_streams(batch)
    meter_only_cells = sum(
        item["reported_cells"]
        for item in meter_only
        if isinstance(item.get("reported_cells"), int)
    )

    summary = {
        "soft_standard_hold": True,
        "not_scoreboard": True,
        "metrics_computed": False,
        "source_results_mutated": False,
        "scope": "committed TypeSafe Wave-0-multi lever-wave result rows",
        "join_key": ["session_id", "checkpoint"],
        "label_source": str(labels_path.relative_to(batch)),
        "sidecar_label_rows": len(labels),
        "result_rows": len(all_derived),
        "joined_rows": len(joined_rows),
        "unjoined_rows": len(all_derived) - len(joined_rows),
        "coverage_fraction": round(len(joined_rows) / len(all_derived), 6),
        "result_sessions": len(result_sessions),
        "labeled_result_sessions": len(labeled_result_sessions),
        "result_sessions_without_label": sorted(
            result_sessions - labeled_result_sessions
        ),
        "unique_session_checkpoints": len(key_statuses),
        "joined_session_checkpoints": sum(
            value == "label_join_exact" for value in key_eligibility.values()
        ),
        "unjoined_session_checkpoints": missing_keys,
        "label_join_eligibility_rows": eligibility_rows,
        "label_join_eligibility_session_checkpoints": {
            value: unique_eligibility.get(value, 0) for value in eligibility_values
        },
        "window_status_rows": count_values(
            all_derived, "window_status", window_values
        ),
        "window_status_session_checkpoints": {
            value: unique_statuses.get(value, 0) for value in window_values
        },
        "streams": per_stream,
        "meter_only_streams": meter_only,
        "meter_only_reported_cells": meter_only_cells,
        "excluded_result_streams": exclusions,
    }
    return summary, joined_rows


def render_markdown(summary: dict[str, Any]) -> str:
    coverage = summary["coverage_fraction"] * 100
    lines = [
        "# TypeSafe lever-wave outcome join — batch-002",
        "",
        "**Soft Standard HOLD.** Derived evidence only: no hooks, product wiring, "
        "Standard unlock, or FP/miss board.",
        "",
        "This report joins committed TypeSafe `Wave-0-multi` lever rows to the "
        "independent outcome sidecar on exact `session_id` + `checkpoint`. It "
        "does not read or aggregate judge ratings/fire decisions and does not "
        "rewrite source `results.jsonl` files.",
        "",
        "## Coverage meters",
        "",
        f"- Result rows: **{summary['result_rows']}**",
        f"- Exact joined rows: **{summary['joined_rows']}** ({coverage:.1f}%)",
        f"- Unjoined committed rows: **{summary['unjoined_rows']}**",
        f"- Result sessions: **{summary['result_sessions']}**; labeled: "
        f"**{summary['labeled_result_sessions']}**",
        f"- Unique `(session_id, checkpoint)` keys: "
        f"**{summary['unique_session_checkpoints']}**; exact: "
        f"**{summary['joined_session_checkpoints']}**",
        "",
        "| Stream | result rows | exact join | unjoined | sessions | unique keys |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for stream in summary["streams"]:
        lines.append(
            f"| `{stream['stream']}` | {stream['result_rows']} | "
            f"{stream['joined_rows']} | {stream['unjoined_rows']} | "
            f"{stream['result_sessions']} | "
            f"{stream['unique_session_checkpoints']} |"
        )

    lines.extend(
        [
            "",
            "## Unlabeled remainder",
            "",
        ]
    )
    if summary["unjoined_rows"] == 0:
        lines.append(
            "None among committed TypeSafe lever-wave result rows: every row has "
            "an exact labeled checkpoint in `outcome-labels.jsonl`."
        )
    else:
        lines.append(
            f"**{summary['unjoined_rows']}** committed rows remain unjoined. "
            "See `coverage.json` for exact session/checkpoint keys and reasons."
        )

    if summary["meter_only_streams"]:
        lines.extend(
            [
                "",
                "Meter-only waves are a separate remainder: they are not counted "
                "as unlabeled rows because no committed row-level join keys exist.",
                "",
                "| Stream | meter-reported cells | reason |",
                "|---|---:|---|",
            ]
        )
        for stream in summary["meter_only_streams"]:
            lines.append(
                f"| `{stream['stream']}` | {stream['reported_cells']} | "
                f"{stream['reason']} |"
            )

    lines.extend(
        [
            "",
            "## Scope boundaries",
            "",
            "- `joined.jsonl` contains only `label_join_exact` rows and preserves "
            "source path + row identity.",
            "- Repeated lever cells are coverage rows, not independent trials; "
            "the 20 sessions and 67 unique join keys are the non-replicated "
            "coverage denominators.",
            "- Window status, near-done, and runaway-like values are copied or "
            "derived only from the validated sidecar. Missing labels are never "
            "interpolated.",
            "- Scenario-sweep and review-check streams are outside this "
            "lever-wave join. Scenario coverage remains documented in "
            "[`WINDOW-STATUS-JOIN.md`](../../../2026-10-02-interception-steer-to-stop/WINDOW-STATUS-JOIN.md).",
            "",
            "## Reproduce",
            "",
            "```bash",
            "python3 tools/interception/typesafe_lever_join.py --require-complete",
            "python3 -m unittest discover -s tools/interception/tests -p 'test_*.py'",
            "```",
            "",
            "Generated artifacts: `joined.jsonl` (exact joins only) and "
            "`coverage.json` (coverage and remainder meters).",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    joined_rows: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "joined.jsonl").open("w", encoding="utf-8") as stream:
        for row in joined_rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    (output_dir / "coverage.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "COVERAGE.md").write_text(
        render_markdown(summary),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[2]
    default_batch = (
        repo
        / "docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002"
    )
    parser = argparse.ArgumentParser(
        description=(
            "Join committed TypeSafe lever-wave rows to outcome labels without "
            "computing FP/miss metrics."
        )
    )
    parser.add_argument("--batch", type=Path, default=default_batch)
    parser.add_argument(
        "--labels",
        type=Path,
        help="Defaults to <batch>/outcome-labels.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Defaults to <batch>/typesafe-outcome-join",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail if any committed lever result row lacks an exact label join",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    labels = args.labels or args.batch / "outcome-labels.jsonl"
    output_dir = args.output_dir or args.batch / "typesafe-outcome-join"
    try:
        summary, joined_rows = build_join(args.batch, labels)
        if args.require_complete and summary["unjoined_rows"]:
            raise JoinError(
                f"{summary['unjoined_rows']} committed lever rows lack exact labels"
            )
        write_outputs(output_dir, summary, joined_rows)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (JoinError, OSError) as exc:
        print(f"TypeSafe lever join failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
