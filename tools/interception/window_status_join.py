#!/usr/bin/env python3
"""Validate outcome labels and derive a non-destructive window-status join."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

WINDOW_STATUSES = (
    "inside_steer_window",
    "outside_steer_window",
    "no_steer_window",
    "ambiguous",
    "unidentified",
)
CHECKPOINT_VALUES = {"yes", "no", "ambiguous"}
FIXED_SCHEDULE = {"45", "60", "75", "90", "105", "120"}
TERMINATION_CAUSES = {
    "unknown",
    "natural_completion",
    "user_stop",
    "human_steer",
    "cap_or_compaction",
    "crash_or_abort",
    "other",
}
PATTERN_TAGS = {
    "closing_stage",
    "productive_mid",
    "thrash",
    "low_progress",
    "scope_drift",
    "post_boundary",
    "natural_completion",
}


class JoinError(ValueError):
    """Raised when the sidecar or result rows cannot be joined safely."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JoinError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise JoinError(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def validate_window(value: Any, location: str) -> None:
    if isinstance(value, str) and value in {"none", "ambiguous"}:
        return
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(turn, int) and not isinstance(turn, bool) for turn in value)
        and 0 <= value[0] <= value[1]
    ):
        return
    raise JoinError(f"{location}: expected 'none', 'ambiguous', or [start, end]")


def validate_checkpoint_map(value: Any, location: str) -> None:
    if not isinstance(value, dict):
        raise JoinError(f"{location}: expected an object")
    for checkpoint, outcome in value.items():
        if not isinstance(checkpoint, str) or not checkpoint.isdigit():
            raise JoinError(f"{location}: checkpoint keys must be decimal strings")
        if checkpoint not in FIXED_SCHEDULE:
            raise JoinError(
                f"{location}: checkpoint {checkpoint} is outside the fixed schedule"
            )
        if outcome not in CHECKPOINT_VALUES:
            raise JoinError(
                f"{location}.{checkpoint}: expected one of {sorted(CHECKPOINT_VALUES)}"
            )


def index_labels(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    for line_number, label in enumerate(rows, 1):
        location = f"labels line {line_number}"
        session_id = label.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise JoinError(f"{location}: session_id must be a non-empty string")
        if session_id in labels:
            raise JoinError(f"{location}: duplicate session_id {session_id!r}")

        status = label.get("label_status")
        if status not in {"not_labeled", "labeled", "excluded"}:
            raise JoinError(f"{location}: invalid label_status {status!r}")
        if status == "labeled":
            for field in ("labeler", "labeled_at", "protocol_rev", "rationale"):
                if not isinstance(label.get(field), str) or not label[field].strip():
                    raise JoinError(f"{location}.{field}: must be a non-empty string")
            try:
                datetime.fromisoformat(label["labeled_at"])
            except ValueError as exc:
                raise JoinError(
                    f"{location}.labeled_at: must be an ISO date or datetime"
                ) from exc
            if label.get("termination_cause") not in TERMINATION_CAUSES:
                raise JoinError(
                    f"{location}.termination_cause: expected one of "
                    f"{sorted(TERMINATION_CAUSES)}"
                )
            steer_count = label.get("human_steer_count")
            if steer_count is not None and (
                not isinstance(steer_count, int)
                or isinstance(steer_count, bool)
                or steer_count < 0
            ):
                raise JoinError(
                    f"{location}.human_steer_count: expected a non-negative int or null"
                )
            pattern_tags = label.get("pattern_tags")
            if not isinstance(pattern_tags, list) or any(
                tag not in PATTERN_TAGS for tag in pattern_tags
            ):
                raise JoinError(
                    f"{location}.pattern_tags: expected a list drawn from "
                    f"{sorted(PATTERN_TAGS)}"
                )
            if len(label["rationale"].split()) > 200:
                raise JoinError(f"{location}.rationale: exceeds 200 words")
            validate_window(label.get("ideal_steer_window"), f"{location}.ideal_steer_window")
            validate_checkpoint_map(
                label.get("near_done_at_checkpoint"),
                f"{location}.near_done_at_checkpoint",
            )
            validate_checkpoint_map(
                label.get("runaway_like_at_checkpoint"),
                f"{location}.runaway_like_at_checkpoint",
            )
            if set(label["near_done_at_checkpoint"]) != set(
                label["runaway_like_at_checkpoint"]
            ):
                raise JoinError(
                    f"{location}: near-done and runaway-like checkpoint keys differ"
                )
            overrides = label.get("ideal_steer_window_by_cp", {})
            if not isinstance(overrides, dict):
                raise JoinError(f"{location}.ideal_steer_window_by_cp: expected an object")
            for checkpoint, window in overrides.items():
                if not isinstance(checkpoint, str) or not checkpoint.isdigit():
                    raise JoinError(
                        f"{location}.ideal_steer_window_by_cp: "
                        "checkpoint keys must be decimal strings"
                    )
                validate_window(
                    window,
                    f"{location}.ideal_steer_window_by_cp.{checkpoint}",
                )
            independence = label.get("independence")
            required_attestations = (
                "used_flash_rating",
                "used_flash_fire",
                "used_leaked_fields",
            )
            if not isinstance(independence, dict) or any(
                independence.get(field) is not False for field in required_attestations
            ):
                raise JoinError(
                    f"{location}.independence: all three leakage attestations must be false"
                )
        labels[session_id] = label
    return labels


def effective_window(label: dict[str, Any], checkpoint: int) -> Any:
    overrides = label.get("ideal_steer_window_by_cp", {})
    return overrides.get(str(checkpoint), label["ideal_steer_window"])


def classify_window(label: dict[str, Any] | None, checkpoint: int) -> tuple[str, Any]:
    if label is None or label.get("label_status") != "labeled":
        return "unidentified", None
    window = effective_window(label, checkpoint)
    if window == "none":
        return "no_steer_window", window
    if window == "ambiguous":
        return "ambiguous", window
    if isinstance(window, list):
        status = (
            "inside_steer_window"
            if window[0] <= checkpoint <= window[1]
            else "outside_steer_window"
        )
        return status, window
    raise JoinError(f"unexpected validated window value: {window!r}")


def derive_rows(
    results: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    for line_number, result in enumerate(results, 1):
        location = f"results line {line_number}"
        session_id = result.get("session_id")
        checkpoint = result.get("checkpoint")
        if not isinstance(session_id, str) or not session_id:
            raise JoinError(f"{location}: session_id must be a non-empty string")
        if not isinstance(checkpoint, int) or isinstance(checkpoint, bool):
            raise JoinError(f"{location}: checkpoint must be an integer")
        cell_id = result.get("cell_id")
        if cell_id is not None:
            if not isinstance(cell_id, str) or not cell_id:
                raise JoinError(f"{location}: cell_id must be a non-empty string")

        label = labels.get(session_id)
        window_status, window = classify_window(label, checkpoint)
        near_done = None
        runaway_like = None
        label_status = "missing"
        protocol_rev = None
        if label is not None:
            label_status = label["label_status"]
            protocol_rev = label.get("protocol_rev")
            if label_status == "labeled":
                key = str(checkpoint)
                near_done = label["near_done_at_checkpoint"].get(key)
                runaway_like = label["runaway_like_at_checkpoint"].get(key)
        if label is None:
            join_eligibility = "session_unlabeled"
        elif label_status == "excluded":
            join_eligibility = "label_excluded"
        elif label_status != "labeled":
            join_eligibility = "session_not_labeled"
        elif near_done is None or runaway_like is None:
            join_eligibility = "checkpoint_unlabeled"
        else:
            join_eligibility = "label_join_exact"

        derived.append(
            {
                "provisional": True,
                "soft_standard_hold": True,
                "not_scoreboard": True,
                "source_row": line_number,
                "derived_row_id": (
                    f"{cell_id}@{line_number}" if cell_id else f"row@{line_number}"
                ),
                "cell_id": cell_id,
                "session_id": session_id,
                "checkpoint": checkpoint,
                "window_status": window_status,
                "ideal_steer_window": window,
                "near_done": near_done,
                "runaway_like": runaway_like,
                "checkpoint_outcomes_complete": (
                    near_done is not None and runaway_like is not None
                ),
                "label_join_eligibility": join_eligibility,
                "label_status": label_status,
                "protocol_rev": protocol_rev,
            }
        )
    return derived


def summarize(
    results: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    derived: list[dict[str, Any]],
) -> dict[str, Any]:
    result_sessions = {row["session_id"] for row in results}
    labeled_sessions = {
        session_id
        for session_id, label in labels.items()
        if label["label_status"] == "labeled"
    }
    statuses = Counter(row["window_status"] for row in derived)
    status_counts = {status: statuses.get(status, 0) for status in WINDOW_STATUSES}
    checkpoint_statuses = {
        (row["session_id"], row["checkpoint"]): row["window_status"]
        for row in derived
    }
    unique_statuses = Counter(checkpoint_statuses.values())
    unique_status_counts = {
        status: unique_statuses.get(status, 0) for status in WINDOW_STATUSES
    }
    complete = sum(row["checkpoint_outcomes_complete"] for row in derived)
    eligibility = Counter(row["label_join_eligibility"] for row in derived)
    checkpoint_eligibility = {
        (row["session_id"], row["checkpoint"]): row["label_join_eligibility"]
        for row in derived
    }
    unique_eligibility = Counter(checkpoint_eligibility.values())
    cell_ids = Counter(
        row["cell_id"] for row in results if isinstance(row.get("cell_id"), str)
    )
    duplicate_cell_ids = sorted(
        cell_id for cell_id, count in cell_ids.items() if count > 1
    )
    windows = []
    for session_id in sorted(result_sessions & labeled_sessions):
        window = labels[session_id]["ideal_steer_window"]
        if isinstance(window, list):
            checkpoints = sorted(
                {
                    row["checkpoint"]
                    for row in results
                    if row["session_id"] == session_id
                }
            )
            windows.append(
                {
                    "session_id": session_id,
                    "ideal_steer_window": window,
                    "observed_checkpoints": checkpoints,
                    "checkpoints_inside_window": [
                        checkpoint
                        for checkpoint in checkpoints
                        if window[0] <= checkpoint <= window[1]
                    ],
                }
            )
    return {
        "provisional": True,
        "soft_standard_hold": True,
        "not_scoreboard": True,
        "result_rows": len(results),
        "unique_session_checkpoints": len(checkpoint_statuses),
        "unique_cell_ids": len(cell_ids),
        "duplicate_cell_ids": duplicate_cell_ids,
        "duplicate_cell_id_extra_rows": sum(
            cell_ids[cell_id] - 1 for cell_id in duplicate_cell_ids
        ),
        "result_sessions": len(result_sessions),
        "sidecar_labels": len(labels),
        "labeled_result_sessions": len(result_sessions & labeled_sessions),
        "result_sessions_without_label": sorted(result_sessions - labeled_sessions),
        "labeled_sessions_without_result": sorted(labeled_sessions - result_sessions),
        "window_status_rows": status_counts,
        "window_status_session_checkpoints": unique_status_counts,
        "label_join_eligibility_rows": dict(sorted(eligibility.items())),
        "label_join_eligibility_session_checkpoints": dict(
            sorted(unique_eligibility.items())
        ),
        "checkpoint_outcomes_complete_rows": complete,
        "checkpoint_outcomes_missing_rows": len(derived) - complete,
        "finite_window_sessions": windows,
        "source_results_mutated": False,
        "metrics_computed": False,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate outcome labels and derive window_status rows. "
            "This tool does not compute FP/miss metrics or modify source results."
        )
    )
    parser.add_argument("--labels", type=Path, required=True, help="Outcome-label JSONL")
    parser.add_argument("--results", type=Path, required=True, help="Result-cell JSONL")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for derived mapping JSONL; source results are never rewritten",
    )
    parser.add_argument(
        "--require-all-labeled",
        action="store_true",
        help="Fail if any result session lacks a labeled sidecar row",
    )
    parser.add_argument(
        "--require-checkpoint-outcomes",
        action="store_true",
        help="Fail if any row lacks near-done or runaway-like labels at its checkpoint",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        labels = index_labels(load_jsonl(args.labels))
        results = load_jsonl(args.results)
        derived = derive_rows(results, labels)
        summary = summarize(results, labels, derived)
        if args.require_all_labeled and summary["result_sessions_without_label"]:
            raise JoinError(
                "unlabeled result sessions: "
                + ", ".join(summary["result_sessions_without_label"])
            )
        if (
            args.require_checkpoint_outcomes
            and summary["checkpoint_outcomes_missing_rows"]
        ):
            raise JoinError(
                "rows without checkpoint outcome labels: "
                f"{summary['checkpoint_outcomes_missing_rows']}"
            )
        if args.output:
            write_jsonl(args.output, derived)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (JoinError, OSError) as exc:
        print(f"window-status join failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
