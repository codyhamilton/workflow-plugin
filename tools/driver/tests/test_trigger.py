"""Tests for one-phase trigger (dry-run and fixture reports)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
DRIVER = Path(__file__).resolve().parents[1]
FIXTURE_OUTPUT = (
    DRIVER / "tests" / "fixtures" / "agent_outputs" / "phase2_unsuccessful.txt"
)
sys.path.insert(0, str(DRIVER))
sys.path.insert(0, str(DRIVER / "providers"))

from fixtures import FIXTURE_SLUG, commit_trailer, init_fixture_repo  # noqa: E402
from report import parse_workflow_report  # noqa: E402
from trigger import trigger_once  # noqa: E402


class TestReportParse(unittest.TestCase):
    def test_fixture_unsuccessful(self) -> None:
        text = FIXTURE_OUTPUT.read_text(encoding="utf-8")
        report = parse_workflow_report(text)
        self.assertEqual(report.status, "unsuccessful")
        self.assertEqual(report.phase, 2)
        self.assertIn("Fixture", report.reason or "")


class TestTriggerDryRun(unittest.TestCase):
    def test_dry_run_incomplete_not_fake_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            outcome = trigger_once(
                plan_dir,
                default_branch="master",
                dry_run=True,
            )
        self.assertFalse(outcome.skipped)
        self.assertEqual(outcome.mode, "dry-run")
        self.assertIsNotNone(outcome.report)
        self.assertEqual(outcome.report.status, "incomplete")
        self.assertEqual(outcome.report.phase, 2)
        self.assertIn("Dry-run", outcome.report.reason or "")

    def test_fixture_proves_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            outcome = trigger_once(
                plan_dir,
                default_branch="master",
                dry_run=True,
                fixture_output=FIXTURE_OUTPUT,
            )
        self.assertEqual(outcome.report.status, "unsuccessful")
        self.assertEqual(outcome.turns, 0)
        self.assertEqual(outcome.cost_usd, 0.0)

    def test_done_skips_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            for n in (1, 2, 3):
                commit_trailer(root, f"p{n}", f"{FIXTURE_SLUG}:{n}")
            commit_trailer(root, "done", f"{FIXTURE_SLUG}:done")
            outcome = trigger_once(
                plan_dir,
                default_branch="master",
                dry_run=True,
            )
        self.assertTrue(outcome.skipped)
        self.assertIsNone(outcome.report)


class TestRunCLI(unittest.TestCase):
    def test_run_once_stdout_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER / "run.py"),
                    str(plan_dir),
                    "--once",
                    "--dry-run",
                    "--default-branch",
                    "master",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"]["open"], "phase")
            self.assertEqual(data["report"]["status"], "incomplete")
            self.assertEqual(data["mode"], "dry-run")

    def test_run_once_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER / "run.py"),
                    str(plan_dir),
                    "--once",
                    "--fixture-output",
                    str(FIXTURE_OUTPUT),
                    "--default-branch",
                    "master",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["report"]["status"], "unsuccessful")

    def test_mcp_oneshot_status(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(DRIVER / "mcp_server.py"),
                "status",
                "--plan-folder",
                "docs/plans/06-phase-driver",
                "--default-branch",
                "master",
            ],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertEqual(data["slug"], "phase-driver")


if __name__ == "__main__":
    unittest.main()
