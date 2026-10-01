#!/usr/bin/env python3
"""Assert registered pilot/cheap-analysis question blobs are TypeSafe-legal."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB))

from paths import REPO_ROOT  # noqa: E402
from schemas import FRAMING_REGISTRY, SCHEMA_BUILDERS  # noqa: E402

TRANSCRIPT = REPO_ROOT / "tools" / "transcript"
sys.path.insert(0, str(TRANSCRIPT))
from lib.jev_client import validate_systemone_questions  # noqa: E402


class TestRegisteredQuestions(unittest.TestCase):
    def test_framing_registry(self) -> None:
        for schema_id, table in FRAMING_REGISTRY.items():
            for slug, questions in table.items():
                if not questions:
                    continue
                validate_systemone_questions(questions)

    def test_schema_builders(self) -> None:
        for schema_id, builder in SCHEMA_BUILDERS.items():
            for ev in ("stats", "prose"):
                questions = builder(ev)
                if questions:
                    validate_systemone_questions(questions)


if __name__ == "__main__":
    unittest.main()
