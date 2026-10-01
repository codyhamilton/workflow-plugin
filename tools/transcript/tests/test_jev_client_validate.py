"""Preflight validation for TypeSafe System One requests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TRANSCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPT_ROOT))

from lib.jev_client import (  # noqa: E402
    build_questions,
    validate_systemone_questions,
    validate_systemone_request,
)


class TestValidateSystemoneQuestions(unittest.TestCase):
    def test_build_questions_passes(self) -> None:
        validate_systemone_questions(build_questions())

    def test_rejects_report_type(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_systemone_questions(
                {
                    "x": {
                        "type": "report",
                        "instructions": "nope",
                    }
                }
            )
        self.assertIn("report", str(ctx.exception))

    def test_rejects_score_criteria_dict(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_systemone_questions(
                {
                    "s": {
                        "type": "score",
                        "instructions": "rate",
                        "criteria": {"0": "low"},
                    }
                }
            )
        self.assertIn("array", str(ctx.exception))

    def test_request_wrapper(self) -> None:
        req = {"model": "jev-1.13.0", "state": {}, "questions": build_questions()}
        validate_systemone_request(req)


if __name__ == "__main__":
    unittest.main()
