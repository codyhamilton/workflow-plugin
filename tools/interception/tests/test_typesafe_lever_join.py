from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "typesafe_lever_join.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("typesafe_lever_join", MODULE_PATH)
assert SPEC and SPEC.loader
JOIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOIN)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def label(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "label_status": "labeled",
        "labeler": "human-test",
        "labeled_at": "2026-10-02T00:00:00+00:00",
        "protocol_rev": "outcome-sheet-v1",
        "termination_cause": "unknown",
        "human_steer_count": None,
        "ideal_steer_window": [55, 62],
        "near_done_at_checkpoint": {"60": "no"},
        "runaway_like_at_checkpoint": {"60": "yes"},
        "pattern_tags": ["low_progress"],
        "rationale": "Turns 55-60 show a low-progress interval.",
        "independence": {
            "used_flash_rating": False,
            "used_flash_fire": False,
            "used_leaked_fields": False,
        },
    }


def result(session_id: str, cell_id: str) -> dict:
    return {
        "cell_id": cell_id,
        "session_id": session_id,
        "checkpoint": 60,
        "driver": "typesafe",
        "wave": "Wave-0-multi",
        "rating": 3,
        "fire": True,
    }


class TypeSafeLeverJoinTests(unittest.TestCase):
    def test_discovers_only_lever_wave_results(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            write_jsonl(
                batch / "typesafe-k1/results.jsonl",
                [result("session-1", "cell-1")],
            )
            write_jsonl(
                batch / "typesafe-scenario-sweep/results.jsonl",
                [
                    {
                        "cell_id": "scenario-1",
                        "session_id": "session-1",
                        "checkpoint": 60,
                        "scenario_id": "state.x|q.y",
                    }
                ],
            )

            streams, exclusions = JOIN.discover_lever_streams(batch)

            self.assertEqual([path.parent.name for path, _ in streams], ["typesafe-k1"])
            self.assertEqual(
                [item["stream"] for item in exclusions],
                ["typesafe-scenario-sweep"],
            )

    def test_reports_exact_join_and_unlabeled_remainder_without_model_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            labels_path = batch / "outcome-labels.jsonl"
            write_jsonl(labels_path, [label("session-1")])
            write_jsonl(
                batch / "typesafe/results.jsonl",
                [
                    result("session-1", "cell-1"),
                    result("session-2", "cell-2"),
                ],
            )

            summary, joined = JOIN.build_join(batch, labels_path)

            self.assertEqual(summary["result_rows"], 2)
            self.assertEqual(summary["joined_rows"], 1)
            self.assertEqual(summary["unjoined_rows"], 1)
            self.assertEqual(
                summary["result_sessions_without_label"],
                ["session-2"],
            )
            self.assertEqual(
                summary["label_join_eligibility_rows"]["session_unlabeled"],
                1,
            )
            self.assertEqual(len(joined), 1)
            self.assertEqual(joined[0]["window_status"], "inside_steer_window")
            self.assertNotIn("rating", joined[0])
            self.assertNotIn("fire", joined[0])

    def test_reports_meter_only_stream_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory)
            meter_path = batch / "typesafe-k4/meters.json"
            meter_path.parent.mkdir(parents=True)
            meter_path.write_text(
                json.dumps(
                    {
                        "driver": "typesafe",
                        "wave": "Wave-0-multi",
                        "n_cells": 1500,
                    }
                ),
                encoding="utf-8",
            )

            meter_only = JOIN.discover_meter_only_streams(batch)

            self.assertEqual(
                meter_only,
                [
                    {
                        "stream": "typesafe-k4",
                        "meters": "typesafe-k4/meters.json",
                        "reported_cells": 1500,
                        "reason": (
                            "results.jsonl is not committed, so session_id + "
                            "checkpoint join coverage cannot be measured"
                        ),
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
