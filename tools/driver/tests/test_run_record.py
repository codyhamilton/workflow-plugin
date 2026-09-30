"""Run record: external JSONL per invocation; git + record for fresh session context."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DRIVER = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[3]
FIXTURE_OUTPUT = (
    DRIVER / "tests" / "fixtures" / "agent_outputs" / "phase2_unsuccessful.txt"
)
FIXTURE_ASSERT = DRIVER / "fixtures" / "assert" / "pass_jev_response.json"
FIXTURE_STATE = DRIVER / "fixtures" / "assert" / "pass_state.json"
sys.path.insert(0, str(DRIVER))
sys.path.insert(0, str(DRIVER / "providers"))

from fixtures import FIXTURE_SLUG, commit_trailer, init_fixture_repo  # noqa: E402
from run_record import (  # noqa: E402
    append_record,
    entry_from_assert,
    entry_from_trigger,
    summarize,
)
from resolve import resolve_plan_folder  # noqa: E402


class TestRunRecordModel(unittest.TestCase):
    def test_trigger_entry_omits_git_closed(self) -> None:
        entry = entry_from_trigger(
            plan="docs/plans/01-fixture",
            slug="fixture",
            default_branch="master",
            skipped=False,
            report={"status": "incomplete", "phase": 2, "reason": "dry"},
            dispatch_target={"kind": "phase", "phase": 2},
            turns=0,
            cost_usd=0.0,
            provider="dry-run",
            mode="dry-run",
        )
        self.assertNotIn("closed", entry)
        self.assertNotIn("open", entry)
        self.assertEqual(entry["last_report"]["status"], "incomplete")
        self.assertEqual(entry["phase_dispatch"]["phase"], "2")

    def test_summarize_aggregates_cost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.jsonl"
            append_record(
                path,
                entry_from_trigger(
                    plan="docs/plans/01-x",
                    slug="x",
                    default_branch="master",
                    skipped=False,
                    report={"status": "closed", "phase": 1, "reason": None},
                    dispatch_target={"kind": "phase", "phase": 1},
                    turns=3,
                    cost_usd=0.5,
                    provider="dry-run",
                    mode="dry-run",
                ),
            )
            append_record(
                path,
                entry_from_trigger(
                    plan="docs/plans/01-x",
                    slug="x",
                    default_branch="master",
                    skipped=False,
                    report={"status": "unsuccessful", "phase": 2, "reason": "blocked"},
                    dispatch_target={"kind": "phase", "phase": 2},
                    turns=1,
                    cost_usd=0.25,
                    provider="dry-run",
                    mode="dry-run",
                ),
            )
            summary = summarize(path, plan="docs/plans/01-x")
        self.assertEqual(summary["total_cost_usd"], 0.75)
        self.assertEqual(summary["last_report"]["status"], "unsuccessful")
        self.assertEqual(summary["phases"]["1"]["cost_usd"], 0.5)
        self.assertEqual(summary["phases"]["2"]["turns"], 1)


class TestRunRecordCliIntegration(unittest.TestCase):
    def test_fresh_session_git_plus_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            record_path = root / "driver-run.jsonl"

            run_py = DRIVER / "run.py"
            env = {**os.environ, "DRIVER_RUN_RECORD": str(record_path)}
            proc = subprocess.run(
                [
                    sys.executable,
                    str(run_py),
                    str(plan_dir),
                    "--once",
                    "--dry-run",
                    "--fixture-output",
                    str(FIXTURE_OUTPUT),
                ],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            run_payload = json.loads(proc.stdout)
            self.assertIn("run_record", run_payload)
            self.assertFalse("closed" in run_payload["run_record"])

            status_py = DRIVER / "status.py"
            proc2 = subprocess.run(
                [
                    sys.executable,
                    str(status_py),
                    str(plan_dir),
                    "--default-branch",
                    "master",
                    "--run-record",
                    str(record_path),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            status_payload = json.loads(proc2.stdout)
            git_status = resolve_plan_folder(plan_dir, default_branch="master")
            self.assertEqual(status_payload["open"], git_status.open)
            self.assertEqual(status_payload["phase"], git_status.phase)
            self.assertEqual(
                status_payload["run_record"]["last_report"]["status"],
                "unsuccessful",
            )
            self.assertEqual(status_payload["run_record"]["total_cost_usd"], 0.0)

    def test_assert_appends_to_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_path = Path(tmp) / "record.jsonl"
            assert_py = DRIVER / "assert_phase.py"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(assert_py),
                    "--fixture-jev",
                    str(FIXTURE_ASSERT),
                    "--state",
                    str(FIXTURE_STATE),
                    "--record",
                    str(record_path),
                ],
                cwd=WORKSPACE,
                capture_output=True,
                text=True,
                check=True,
            )
            result = json.loads(proc.stdout)
            self.assertIn("run_record", result)
            summary = summarize(record_path)
            self.assertIsNotNone(summary["last_assert"])
            self.assertTrue(summary["last_assert"]["pass"])
