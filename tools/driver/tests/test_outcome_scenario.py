"""Outcome row: trailer-completeness verifier (status → once → assert)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VERIFY = REPO / "evals" / "scenarios" / "trailer-completeness" / "verify.py"
BASELINE = REPO / "evals" / "scenarios" / "trailer-completeness" / "baseline" / "outcome.json"
EXPECTED_TRAILERS = [
    "trailer-completeness:1",
    "trailer-completeness:2",
    "trailer-completeness:done",
]


def _env_without_keys() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("ANTHROPIC_API_KEY", "CURSOR_API_KEY", "TYPESAFE_API_KEY", "DRIVER_RUN_RECORD"):
        env.pop(key, None)
    return env


def _run(
    extra: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFY), *(extra or [])],
        cwd=REPO,
        env=env if env is not None else _env_without_keys(),
        capture_output=True,
        text=True,
        check=False,
    )


class TestTrailerCompletenessVerifier(unittest.TestCase):
    def test_verifier_passes_and_matches_baseline(self) -> None:
        proc = _run()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["verifier"], "pass")
        self.assertEqual(data["checks"], {
            "status": "pass",
            "trailers": "pass",
            "once": "pass",
            "assert": "pass",
        })
        self.assertEqual(data["failures"], [])
        self.assertEqual(data["trailers"], EXPECTED_TRAILERS)
        self.assertEqual(data["ignored_trailers"], ["other-slug:1"])
        self.assertEqual(data["status"]["open"], "done")
        self.assertEqual(data["status"]["closed"], EXPECTED_TRAILERS[:2])
        self.assertTrue(data["status"]["done"])
        self.assertTrue(data["once"]["skipped"])
        self.assertEqual(data["once"]["exit_code"], 0)
        self.assertTrue(data["assert"]["pass"])
        self.assertEqual(data["assert"]["decision_source"], "deterministic")
        self.assertEqual(data["assert"]["exit_code"], 0)
        self.assertFalse(data["cost"]["available"])
        self.assertIsNone(data["cost"]["cost_usd"])
        self.assertEqual(data["cost"]["reason"], "no ANTHROPIC_API_KEY or CURSOR_API_KEY")
        self.assertEqual(data["classify"], "not used")
        self.assertNotIn("session_kind", proc.stdout)
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(data, baseline)

    def test_missing_phase_trailer_fails(self) -> None:
        proc = _run(["--omit-trailer", "trailer-completeness:2"])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["verifier"], "fail")
        self.assertEqual(data["checks"]["trailers"], "fail")
        self.assertEqual(data["checks"]["status"], "fail")
        self.assertNotIn("trailer-completeness:2", data["trailers"])
        self.assertEqual(data["classify"], "not used")

    def test_provider_stub_does_not_fail_trailer_row(self) -> None:
        env = _env_without_keys()
        env["ANTHROPIC_API_KEY"] = "test-not-a-real-key"
        proc = _run(env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = json.loads(proc.stdout)
        self.assertEqual(data["verifier"], "pass")
        self.assertEqual(data["trailers"], EXPECTED_TRAILERS)
        self.assertFalse(data["cost"]["available"])
        self.assertIsNone(data["cost"]["cost_usd"])
        self.assertIn("not implemented", data["cost"]["reason"])
        self.assertEqual(data["classify"], "not used")


if __name__ == "__main__":
    unittest.main()
