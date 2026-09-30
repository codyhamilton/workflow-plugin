#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== gate_threshold_simulation =="
python3 gate_threshold_simulation.py | tee "$ROOT/validated/gate_simulation_result.json"

echo "== unittest =="
python3 -m unittest -v test_proofs.py

echo "== hook probe (fixture stdin) =="
export WORKFLOW_SIGNAL_STATE_DIR="${TMPDIR:-/tmp}/workflow-signal-state-probe"
export WORKFLOW_JEV_SIGNAL_LOG="${TMPDIR:-/tmp}/jev-signal-probe.jsonl"
rm -f "$WORKFLOW_JEV_SIGNAL_LOG"
python3 -c "
import json, subprocess, sys
from pathlib import Path
d = json.loads(Path('fixtures/post_tool_batch_input.json').read_text())
d['transcript_path'] = str((Path('fixtures') / 'sample_transcript.jsonl').resolve())
subprocess.run([sys.executable, 'post_tool_batch_signal.py'], input=json.dumps(d).encode(), check=True)
"
wc -c "$WORKFLOW_JEV_SIGNAL_LOG" || true

echo "All proofs passed."
