#!/usr/bin/env python3
"""Audit an exact-key decision-window and negative-control protocol.

This is a derived, offline Soft HOLD artifact.  It consumes only the
human-labeled outcome sidecar; it does not read judge ratings, fire decisions,
final session length, or transcript tails.  It never rewrites source results.

The output is deliberately a protocol-audit corpus rather than an FP/miss
scoreboard.  A second independent adjudication and an immutable blind bundle
are still required before the measured strata can be treated as validated
reference outcomes.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
TOOLS = REPO / "tools" / "interception"
sys.path.insert(0, str(TOOLS))

from window_status_join import (  # noqa: E402
    FIXED_SCHEDULE,
    classify_window,
    index_labels,
    load_jsonl,
)

PROTOCOL_REV = "rotate-2-window-controls-v1"
SOFT_HOLD = {
    "soft_standard_hold": True,
    "product_wiring": False,
    "hooks": False,
    "local_8080": False,
    "metrics_computed": False,
    "not_scoreboard": True,
}


def atomic_write(path: Path, text: str) -> None:
    """Write a deterministic artifact without leaving a partial output."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def classify_stratum(near_done: str, runaway_like: str, window_status: str) -> str:
    """Assign mutually exclusive protocol strata, not outcome scores."""
    if runaway_like == "yes" and window_status == "inside_steer_window":
        return "decision_window_positive"
    if near_done == "no" and runaway_like == "no":
        return "negative_control"
    if near_done == "yes" and runaway_like == "no":
        return "near_done_guard"
    if window_status == "outside_steer_window":
        return "outside_window_observation"
    return "unclassified"


def derive_controls(labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive one row for each exact labeled session/checkpoint key."""
    rows: list[dict[str, Any]] = []
    for session_id in sorted(labels):
        label = labels[session_id]
        if label.get("label_status") != "labeled":
            continue
        near = label["near_done_at_checkpoint"]
        runaway = label["runaway_like_at_checkpoint"]
        if set(near) != set(runaway):
            raise ValueError(f"{session_id}: checkpoint maps do not have exact keys")
        for checkpoint_key in sorted(near, key=int):
            checkpoint = int(checkpoint_key)
            status, window = classify_window(label, checkpoint)
            near_done = near[checkpoint_key]
            runaway_like = runaway[checkpoint_key]
            rows.append(
                {
                    "protocol_rev": PROTOCOL_REV,
                    "provisional": True,
                    **SOFT_HOLD,
                    "session_id": session_id,
                    "checkpoint": checkpoint,
                    "window_status": status,
                    "ideal_steer_window": window,
                    "near_done": near_done,
                    "runaway_like": runaway_like,
                    "stratum": classify_stratum(near_done, runaway_like, status),
                    "exact_key_join": True,
                    "nearest_checkpoint_interpolation": False,
                    "final_length_input": False,
                }
            )
    return rows


def summarize(labels: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return validation gates and descriptive counts for the derived corpus."""
    checks = {
        "all_sidecar_rows_labeled": all(
            label.get("label_status") == "labeled" for label in labels.values()
        ),
        "all_checkpoint_keys_fixed_schedule": all(
            str(row["checkpoint"]) in FIXED_SCHEDULE for row in rows
        ),
        "all_exact_session_checkpoint_keys_unique": len(
            {(row["session_id"], row["checkpoint"]) for row in rows}
        )
        == len(rows),
        "all_rows_have_exact_key_join": all(row["exact_key_join"] for row in rows),
        "no_nearest_checkpoint_interpolation": all(
            not row["nearest_checkpoint_interpolation"] for row in rows
        ),
        "no_final_length_input": all(not row["final_length_input"] for row in rows),
        "all_independence_attestations_false": all(
            all(value is False for value in (label.get("independence") or {}).values())
            and set(label.get("independence") or {})
            == {"used_flash_rating", "used_flash_fire", "used_leaked_fields"}
            for label in labels.values()
        ),
    }
    status_counts = Counter(row["window_status"] for row in rows)
    stratum_counts = Counter(row["stratum"] for row in rows)
    outcome_counts = Counter(
        (row["near_done"], row["runaway_like"]) for row in rows
    )
    finite_sessions = {
        row["session_id"]
        for row in rows
        if isinstance(row["ideal_steer_window"], list)
    }
    finite_positive = [
        row
        for row in rows
        if row["stratum"] == "decision_window_positive"
    ]
    return {
        "generated_by": Path(__file__).name,
        "protocol_rev": PROTOCOL_REV,
        **SOFT_HOLD,
        "validation": {
            **checks,
            "protocol_shape_pass": all(checks.values()),
            "empirical_reference_validation": "not_complete",
            "remaining_reference_gates": [
                "second independent adjudication with retained agreement",
                "immutable blind transcript-digest bundle",
                "judge-result join before any FP/miss aggregation",
            ],
        },
        "counts": {
            "sidecar_sessions": len(labels),
            "exact_session_checkpoint_keys": len(rows),
            "finite_window_sessions": len(finite_sessions),
            "finite_window_positive_keys": len(finite_positive),
            "window_status": {
                key: status_counts.get(key, 0)
                for key in (
                    "inside_steer_window",
                    "outside_steer_window",
                    "no_steer_window",
                    "ambiguous",
                    "unidentified",
                )
            },
            "strata": dict(sorted(stratum_counts.items())),
            "near_done_runaway_joint": {
                f"near_done={near},runaway_like={runaway}": count
                for (near, runaway), count in sorted(outcome_counts.items())
            },
        },
        "negative_control_definition": (
            "Exact labeled (session_id, checkpoint) key with "
            "near_done=no and runaway_like=no. Window status remains an "
            "orthogonal field; none is not inferred from no_steer_window."
        ),
        "decision_window_definition": (
            "Exact labeled key with runaway_like=yes and checkpoint inside "
            "the effective finite ideal_steer_window. This is a reference "
            "stratum only; it is not a hit or miss without judge-result joins."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path(__file__).with_name("outcome-labels.jsonl"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).parent,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        labels = index_labels(load_jsonl(args.labels))
        rows = derive_controls(labels)
        summary = summarize(labels, rows)
        if not summary["validation"]["protocol_shape_pass"]:
            raise ValueError("protocol validation failed")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            args.out_dir / "rotate-2-decision-window-controls.jsonl",
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        )
        atomic_write(
            args.out_dir / "rotate-2-decision-window-audit.json",
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"rotate-2 audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
