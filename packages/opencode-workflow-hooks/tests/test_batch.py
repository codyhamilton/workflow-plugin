#!/usr/bin/env python3
"""Unit tests for package batch aggregator (same contract as lab test_proofs.py)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_PY = _PKG / "python"
_REPO = _PKG.parents[1]
sys.path.insert(0, str(_PY))

from batch_aggregator import OpenCodeBatchAggregator, repo_root, simulate_model_steps  # noqa: E402

JEV_PROOFS = _REPO / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs"
sys.path.insert(0, str(JEV_PROOFS))
from gate_thresholds import evaluate_gate  # noqa: E402


class BatchAggregatorTests(unittest.TestCase):
    def test_repo_root_points_at_workflow_plugin(self) -> None:
        self.assertTrue((repo_root() / "tools" / "driver").is_dir())

    def test_seventy_six_steps_band_exit_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(Path(tmp) / "state")
            os.environ.pop("WORKFLOW_ANALYTICS_URL", None)
            agg = OpenCodeBatchAggregator(log_path=log)
            entry = simulate_model_steps(agg, session_id="oc-test", steps=76)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["api_turns_proxy"], 76)
            self.assertTrue(entry["gate"]["band_exit"])
            lines = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)

    def test_parallel_tools_one_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(Path(tmp) / "state")
            agg = OpenCodeBatchAggregator(log_path=log)
            sid = "parallel"
            agg.on_tool_execute_after(session_id=sid, tool="read", call_id="a", output="a")
            agg.on_tool_execute_after(session_id=sid, tool="write", call_id="b", output="b")
            entry = agg.flush_step(session_id=sid)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["tool_calls_in_batch"], 2)
            self.assertEqual(entry["post_tool_batch_count"], 1)

    def test_flush_cli_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            os.environ["WORKFLOW_JEV_SIGNAL_LOG"] = str(log)
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(Path(tmp) / "state")
            os.environ["WORKFLOW_REPO_ROOT"] = str(_REPO)
            payload = {
                "session_id": "cli-test",
                "cwd": str(_REPO),
                "tool_calls": [{"tool_name": "bash", "tool_use_id": "x", "tool_response": "ok"}],
            }
            cli = _PY / "batch_flush_cli.py"
            proc = subprocess.run(
                [sys.executable, str(cli)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ},
            )
            self.assertEqual(proc.returncode, 0)
            # One flush without gate flags may not write; run 76 flushes via aggregator test instead
            self.assertFalse(proc.stderr.strip())


class GateImportTests(unittest.TestCase):
    def test_smoking_gun_shared_thresholds(self) -> None:
        g = evaluate_gate(api_turns=296, peak_ctx_tokens=130_000, transcript_bytes=13_312_000)
        self.assertTrue(g.escalate)


if __name__ == "__main__":
    unittest.main()
