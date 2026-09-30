#!/usr/bin/env python3
"""unittest for OpenCode hooks plugin lab proofs."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROOFS = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOFS))

from batch_aggregator import OpenCodeBatchAggregator, simulate_model_steps  # noqa: E402

JEV_PROOFS = PROOFS.parent.parent / "2026-09-30-jev-cheap-judgement-signals" / "proofs"
sys.path.insert(0, str(JEV_PROOFS))
from gate_thresholds import evaluate_gate  # noqa: E402


class BatchAggregatorTests(unittest.TestCase):
    def test_seventy_six_steps_band_exit_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            state_dir = Path(tmp) / "state"
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(state_dir)
            os.environ.pop("WORKFLOW_ANALYTICS_URL", None)
            agg = OpenCodeBatchAggregator(log_path=log)
            entry = simulate_model_steps(agg, session_id="oc-test", steps=76)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["api_turns_proxy"], 76)
            self.assertTrue(entry["gate"]["band_exit"])
            self.assertTrue(log.is_file())
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

    def test_analytics_envelope_opencode_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(Path(tmp) / "state")
            os.environ["WORKFLOW_INSTALL_MODE"] = "opencode"
            os.environ.pop("WORKFLOW_ANALYTICS_URL", None)
            agg = OpenCodeBatchAggregator(log_path=log)
            simulate_model_steps(agg, session_id="oc-analytics", steps=76)
            # Remote skipped; local log still written
            self.assertTrue(log.is_file())


class GateImportTests(unittest.TestCase):
    def test_smoking_gun_shared_thresholds(self) -> None:
        g = evaluate_gate(api_turns=296, peak_ctx_tokens=130_000, transcript_bytes=13_312_000)
        self.assertTrue(g.escalate)


if __name__ == "__main__":
    unittest.main()
