from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "window_status_join.py"
SPEC = importlib.util.spec_from_file_location("window_status_join", MODULE_PATH)
assert SPEC and SPEC.loader
JOIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOIN)


def label(window="none", *, overrides=None):
    return {
        "session_id": "session-1",
        "label_status": "labeled",
        "labeler": "human-test",
        "labeled_at": "2026-10-02T00:00:00+00:00",
        "protocol_rev": "outcome-sheet-v1",
        "termination_cause": "unknown",
        "human_steer_count": None,
        "ideal_steer_window": window,
        "ideal_steer_window_by_cp": overrides or {},
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


class WindowStatusJoinTests(unittest.TestCase):
    def test_classifies_each_window_state(self):
        cases = (
            (label([55, 62]), 60, "inside_steer_window"),
            (label([55, 62]), 75, "outside_steer_window"),
            (label("none"), 60, "no_steer_window"),
            (label("ambiguous"), 60, "ambiguous"),
            (None, 60, "unidentified"),
        )
        for outcome_label, checkpoint, expected in cases:
            with self.subTest(expected=expected):
                status, _ = JOIN.classify_window(outcome_label, checkpoint)
                self.assertEqual(status, expected)

    def test_checkpoint_override_takes_precedence(self):
        outcome_label = label("none", overrides={"60": [58, 61]})
        status, window = JOIN.classify_window(outcome_label, 60)
        self.assertEqual(status, "inside_steer_window")
        self.assertEqual(window, [58, 61])

    def test_window_identity_does_not_invent_checkpoint_outcomes(self):
        outcome_label = label([22, 164])
        row = {"cell_id": "cell-1", "session_id": "session-1", "checkpoint": 55}
        derived = JOIN.derive_rows([row], {"session-1": outcome_label})[0]
        self.assertTrue(derived["provisional"])
        self.assertTrue(derived["soft_standard_hold"])
        self.assertTrue(derived["not_scoreboard"])
        self.assertEqual(derived["derived_row_id"], "cell-1@1")
        self.assertEqual(derived["window_status"], "inside_steer_window")
        self.assertIsNone(derived["near_done"])
        self.assertIsNone(derived["runaway_like"])
        self.assertFalse(derived["checkpoint_outcomes_complete"])
        self.assertEqual(derived["label_join_eligibility"], "checkpoint_unlabeled")

    def test_preserves_duplicate_source_cells_with_unique_derived_ids(self):
        row = {"cell_id": "cell-1", "session_id": "session-1", "checkpoint": 60}
        results = [row.copy(), row.copy()]
        derived = JOIN.derive_rows(results, {"session-1": label()})
        self.assertEqual(
            [item["derived_row_id"] for item in derived],
            ["cell-1@1", "cell-1@2"],
        )
        summary = JOIN.summarize(results, {"session-1": label()}, derived)
        self.assertEqual(summary["unique_session_checkpoints"], 1)
        self.assertEqual(summary["window_status_session_checkpoints"]["no_steer_window"], 1)
        self.assertEqual(summary["unique_cell_ids"], 1)
        self.assertEqual(summary["duplicate_cell_ids"], ["cell-1"])
        self.assertEqual(summary["duplicate_cell_id_extra_rows"], 1)
        self.assertEqual(summary["label_join_eligibility_rows"], {"label_join_exact": 2})

    def test_rejects_leakage_attestation(self):
        outcome_label = label()
        outcome_label["independence"]["used_flash_fire"] = True
        with self.assertRaisesRegex(JOIN.JoinError, "attestations must be false"):
            JOIN.index_labels([outcome_label])

    def test_rejects_mismatched_checkpoint_maps(self):
        outcome_label = label()
        outcome_label["runaway_like_at_checkpoint"] = {"45": "no"}
        with self.assertRaisesRegex(JOIN.JoinError, "checkpoint keys differ"):
            JOIN.index_labels([outcome_label])


if __name__ == "__main__":
    unittest.main()
