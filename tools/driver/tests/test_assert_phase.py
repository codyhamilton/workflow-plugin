"""Tests for phase-boundary assert (deterministic + fixture Jev)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

DRIVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DRIVER_DIR))

from phase_assert import (  # noqa: E402
    QUESTION_OUTCOME_EVIDENCE,
    SCORE_PASS_THRESHOLD,
    build_jev_request,
    deterministic_outcome_evidence,
    evaluate_assert,
    jev_pass_from_score,
)

FIXTURES = DRIVER_DIR / "fixtures" / "assert"
ASSERT_CLI = DRIVER_DIR / "assert_phase.py"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestDeterministicFixtures(unittest.TestCase):
    def test_pass_fixture(self) -> None:
        state = _load("pass_state.json")
        det = deterministic_outcome_evidence(state)
        self.assertTrue(det.pass_, det.reasons)

    def test_fail_fixture(self) -> None:
        state = _load("fail_state.json")
        det = deterministic_outcome_evidence(state)
        self.assertFalse(det.pass_)
        self.assertIn("Verification", " ".join(det.reasons))

    def test_fail_fixture_jev_disagrees_kill_line(self) -> None:
        state = _load("fail_state.json")
        jev = _load("fail_jev_response.json")
        result = evaluate_assert(state, jev_response=jev)
        self.assertFalse(result.pass_)
        self.assertEqual(result.decision_source, "deterministic")
        self.assertTrue(result.jev_disagreed)
        self.assertTrue(jev_pass_from_score(3.0))

    def test_pass_fixture_jev_agrees(self) -> None:
        state = _load("pass_state.json")
        jev = _load("pass_jev_response.json")
        result = evaluate_assert(state, jev_response=jev)
        self.assertTrue(result.pass_)
        self.assertFalse(result.jev_disagreed)


class TestJevRequestShape(unittest.TestCase):
    def test_dry_run_request_has_pin_and_score_question(self) -> None:
        state = _load("pass_state.json")
        req = build_jev_request(state)
        self.assertEqual(req["model"], "jev-1.13.0")
        self.assertIn("outcome_evidence", req["questions"])
        self.assertEqual(req["questions"]["outcome_evidence"]["type"], "score")
        self.assertNotIn("session_kind", req["questions"])
        self.assertIn("closing_body", req["state"])


class TestAssertCli(unittest.TestCase):
    def test_dry_run_stdout_is_request_only(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ASSERT_CLI),
                "--dry-run",
                "--state",
                str(FIXTURES / "pass_state.json"),
            ],
            cwd=DRIVER_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["model"], "jev-1.13.0")

    def test_fixture_jev_fail_exit_code(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ASSERT_CLI),
                "--fixture-jev",
                str(FIXTURES / "fail_jev_response.json"),
                "--state",
                str(FIXTURES / "fail_state.json"),
            ],
            cwd=DRIVER_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout)
        data = json.loads(proc.stdout)
        self.assertFalse(data["pass"])
        self.assertEqual(data["fail_branch"], "stop_and_escalate")
        jev = data["jev"]
        self.assertIsNotNone(jev)
        self.assertTrue(jev["disagreed_with_deterministic"])

    def test_deterministic_pass_exit_code(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ASSERT_CLI),
                "--deterministic",
                "--no-record",
                "--state",
                str(FIXTURES / "pass_state.json"),
            ],
            cwd=DRIVER_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["pass"])
        self.assertEqual(data["decision_source"], "deterministic")
        self.assertIsNone(data["jev"])

    def test_deterministic_fail_exit_code(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ASSERT_CLI),
                "--deterministic",
                "--no-record",
                "--state",
                str(FIXTURES / "fail_state.json"),
            ],
            cwd=DRIVER_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout)
        data = json.loads(proc.stdout)
        self.assertFalse(data["pass"])
        self.assertEqual(data["decision_source"], "deterministic")
        self.assertEqual(data["fail_branch"], "stop_and_escalate")
        self.assertIsNone(data["jev"])

    def test_fixture_jev_pass_exit_code(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ASSERT_CLI),
                "--fixture-jev",
                str(FIXTURES / "pass_jev_response.json"),
                "--state",
                str(FIXTURES / "pass_state.json"),
            ],
            cwd=DRIVER_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["pass"])


if __name__ == "__main__":
    unittest.main()
