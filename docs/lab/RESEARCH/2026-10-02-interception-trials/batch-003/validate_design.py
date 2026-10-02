#!/usr/bin/env python3
"""Validate the batch-003 Soft HOLD design without making judge calls."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
BATCH_002 = HERE.parent / "batch-002"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_labels() -> dict[str, dict]:
    rows = {}
    for line in (BATCH_002 / "outcome-labels.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["session_id"]] = row
    return rows


def load_snapshots() -> dict[str, dict]:
    rows = {}
    for path in sorted((BATCH_002 / "snapshots-mid").glob("*.json")):
        row = load_json(path)
        session_id = row.get("worker_id") or path.stem
        rows[session_id] = row
    return rows


def validate() -> dict:
    matrix = load_json(HERE / "TRIAL-MATRIX.json")
    strata = load_json(HERE / "SESSION-STRATA.json")
    labels = load_labels()
    snapshots = load_snapshots()
    sessions = strata["sessions"]

    assert matrix["authorization"] == {
        "soft_standard_hold": True,
        "design_only": True,
        "product_wiring": False,
        "hooks": False,
        "localhost_8080": False,
        "standard_unlock": False,
        "scoreboard_authorized": False,
    }
    assert len(sessions) == 28
    assert len({row["session_id"] for row in sessions}) == 28
    assert Counter(row["block"] for row in sessions) == {
        f"B{index:02d}": 4 for index in range(1, 8)
    }

    harness_counts = Counter(row["harness"] for row in sessions)
    assert harness_counts == {
        "claude-code": 11,
        "opencode": 13,
        "codex": 2,
        "cursor": 2,
    }
    maps_count = sum(row["maps_family"] for row in sessions)
    assert maps_count == 11
    assert harness_counts["claude-code"] / len(sessions) <= 0.4
    assert maps_count / len(sessions) <= 0.4
    assert len({row["project"] for row in sessions}) == 6

    holdout = [row for row in sessions if row["holdout"]]
    assert not holdout
    assert strata["selection_rule"]["holdout_block"] is None
    assert strata["selection_rule"]["late_replay_block"] == "B02"
    assert sum(row["block"] == "B02" for row in sessions) == 4

    for row in sessions:
        snapshot = snapshots[row["session_id"]]
        checkpoints = {int(item["checkpoint"]) for item in snapshot["checkpoints"]}
        assert 45 in checkpoints, row["session_id"]
        assert snapshot["harness"] == row["harness"]
        assert snapshot["project"] == row["project"]
        assert snapshot["corpus_source"] == row["corpus_source"]
        assert row["maps_family"] == str(row["project"]).startswith("open-pajero-maps")
        if row["harness"] == "claude-code":
            assert row["state_contract"] == "growth-fill-v1-native"
        else:
            assert row["state_contract"] == "harness-tail-adapter-required"

    core = matrix["core_state_contrast"]
    assert core["n_cells_per_driver"] == (
        len(sessions) * len(matrix["questions"]) * len(matrix["states"])
    ) == 1008
    assert core["n_cells_all_drivers"] == 1008 * len(matrix["drivers"]) == 3024
    assert core["canary"]["cells_per_driver"] == (
        4 * len(matrix["questions"]) * len(matrix["states"])
    ) == 144
    assert core["holdout_block"] is None
    assert core["late_replay_block"] == "B02"
    assert core["fresh_validation_extension"]["n_cells_per_driver"] == (
        8 * len(matrix["questions"]) * len(matrix["states"])
    ) == 288
    assert core["fresh_validation_extension"]["n_cells_all_drivers"] == 864
    assert matrix["state_contract_gate"]["canonical_rebuild_sessions_at_t45"] == 28

    zero = matrix["zero_fire_factorial"]
    panel_sessions = (
        zero["corpus_panel_per_question"]["target_evidence_positive_sessions"]
        + zero["corpus_panel_per_question"]["matched_quiet_sessions"]
    )
    assert len(zero["questions"]) == 5
    assert zero["analysis_cells_per_driver"] == (
        len(zero["questions"]) * len(zero["wordings"]) * panel_sessions
    ) == 160
    assert zero["new_cells_per_driver_after_core_reuse"] == (
        len(zero["questions"]) * panel_sessions
    ) == 80

    ranking = matrix["fixed_schedule_ranking_extension"]
    assert ranking["minimum_cells_per_driver_with_t90_support"] == (
        12 * ((12 * 3) + 4)
    ) == 480

    nulls = matrix["current_12x9_h2_nulls"]
    exact_sessions = nulls["sessions"]
    assert len(exact_sessions) == 9
    assert Counter(row["checkpoint"] for row in exact_sessions) == {
        45: 3,
        60: 1,
        75: 5,
    }
    for row in exact_sessions:
        label = labels[row["session_id"]]
        key = str(row["checkpoint"])
        assert key in label["runaway_like_at_checkpoint"]
        assert label["runaway_like_at_checkpoint"][key] != "yes"
    fires = {
        row["id"]: row["derived_fire_cells"] for row in nulls["policies"]
    }
    assert fires == {
        "never_fire": 0,
        "constant_turn_75": 60,
        "constant_turn_90": 0,
    }
    assert nulls["n_derived_policy_rows"] == 3 * 12 * 9 == 324

    t75_survivors = []
    for session_id, snapshot in snapshots.items():
        checkpoints = {int(item["checkpoint"]) for item in snapshot["checkpoints"]}
        if 75 in checkpoints:
            t75_survivors.append(session_id)
    runaway_sessions = {
        session_id
        for session_id, label in labels.items()
        if "yes" in (label.get("runaway_like_at_checkpoint") or {}).values()
    }
    current = matrix["label_and_corpus_gate"]["current_state"]
    assert len(t75_survivors) == current["sessions_surviving_to_75"] == 12
    assert len(runaway_sessions) == current["runaway_like_yes_sessions"] == 2
    assert sum(
        value == "yes"
        for label in labels.values()
        for value in (label.get("runaway_like_at_checkpoint") or {}).values()
    ) == current["runaway_like_yes_checkpoint_slots"] == 4

    return {
        "soft_standard_hold": True,
        "judge_calls": 0,
        "core_cells_per_driver": core["n_cells_per_driver"],
        "core_cells_all_drivers": core["n_cells_all_drivers"],
        "zero_fire_new_cells_per_driver": zero[
            "new_cells_per_driver_after_core_reuse"
        ],
        "fresh_validation_cells_per_driver": core[
            "fresh_validation_extension"
        ]["n_cells_per_driver"],
        "current_null_rows": nulls["n_derived_policy_rows"],
        "balanced_sessions": len(sessions),
        "maps_share": round(maps_count / len(sessions), 6),
        "claude_code_share": round(
            harness_counts["claude-code"] / len(sessions), 6
        ),
        "current_t75_survivors": len(t75_survivors),
        "current_runaway_like_yes_sessions": len(runaway_sessions),
        "ranking_ready_now": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
