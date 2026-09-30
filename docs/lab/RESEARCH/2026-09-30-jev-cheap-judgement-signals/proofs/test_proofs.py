#!/usr/bin/env python3
"""unittest entry for research proofs (run from proofs/ directory)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROOFS = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOFS))

from gate_thresholds import evaluate_gate  # noqa: E402
from jev_signal_schemas import BUILDERS, example_states  # noqa: E402
from post_tool_batch_signal import process_hook_input  # noqa: E402


class GateThresholdTests(unittest.TestCase):
    def test_smoking_gun_worker(self) -> None:
        g = evaluate_gate(api_turns=296, peak_ctx_tokens=130_000, transcript_bytes=13_312_000)
        self.assertTrue(g.band_exit)
        self.assertTrue(g.escalate)
        self.assertTrue(g.jev_eligible)

    def test_refine_agent_below_band_exit(self) -> None:
        g = evaluate_gate(api_turns=70, peak_ctx_tokens=110_000)
        self.assertFalse(g.band_exit)
        self.assertFalse(g.escalate)


class JevSchemaTests(unittest.TestCase):
    def test_dry_run_sizes(self) -> None:
        for name, state in example_states().items():
            req = BUILDERS[name](state)
            self.assertEqual(req["model"], "jev-1.13.0")
            blob = json.dumps(req)
            self.assertLess(len(blob), 16_000, msg=name)

    def test_phase_alignment_distinct_from_outcome_evidence(self) -> None:
        state = example_states()["phase_alignment"]
        self.assertEqual(state["question_id"], "phase-alignment-sanity")


class HookProbeTests(unittest.TestCase):
    def test_post_tool_batch_probe_writes_log_on_band_exit(self) -> None:
        fixture = json.loads(
            (PROOFS / "fixtures" / "post_tool_batch_input.json").read_text(encoding="utf-8")
        )
        transcript = PROOFS / "fixtures" / "sample_transcript.jsonl"
        fixture["transcript_path"] = str(transcript)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "signal.jsonl"
            state_dir = Path(tmp) / "state"
            os.environ["WORKFLOW_SIGNAL_STATE_DIR"] = str(state_dir)
            # No transcript: turn proxy = PostToolBatch count (76 crosses band_exit).
            fixture_no_tx = {**fixture, "transcript_path": ""}
            entry = None
            for _ in range(76):
                entry = process_hook_input(fixture_no_tx, log_path=log)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["api_turns_proxy"], 76)
            self.assertTrue(entry["gate"]["band_exit"])
            self.assertTrue(log.is_file())
            lines = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)

    def test_simulation_script_exit_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(PROOFS / "gate_threshold_simulation.py")],
            cwd=str(PROOFS),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        summary = json.loads(proc.stdout)
        self.assertTrue(summary["checks"]["smoking_gun_escalate"])


if __name__ == "__main__":
    unittest.main()
