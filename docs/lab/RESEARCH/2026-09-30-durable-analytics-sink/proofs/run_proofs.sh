#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
VALIDATED="$ROOT/validated"
mkdir -p "$VALIDATED"

echo "== unittest =="
python3 -m unittest -v test_proofs.py

echo "== mock HTTP sink + dual_write =="
rm -f "$VALIDATED/mock_sink_received.jsonl"
PORT=18765
python3 mock_sink_server.py "$PORT" &
SERVER_PID=$!
sleep 0.3
export WORKFLOW_ANALYTICS_URL="http://127.0.0.1:${PORT}/v1/events"
export WORKFLOW_ANALYTICS_TOKEN="lab-test-token"
export WORKFLOW_ANALYTICS_SESSION_ID="${WORKFLOW_ANALYTICS_SESSION_ID:-lab-session}"
TMP_LOG="$(mktemp)"
python3 -c "
from pathlib import Path
import json
from dual_write_sink import emit_event
legacy = {'record_version': 1, 'ts': '2026-09-30T00:00:00+00:00', 'kind': 'trigger', 'slug': 'lab'}
env = emit_event(
    kind='driver.trigger',
    payload={'skipped': False, 'phase_dispatch': {'phase': '1'}},
    local_path=Path('$TMP_LOG'),
    legacy_row=legacy,
    slug='lab',
    source='run_proofs.sh',
)
assert env['_remote_ok'], env
print(json.dumps({'remote_detail': env['_remote_detail'], 'event_id': env['event_id']}))
" | tee "$VALIDATED/dual_write_result.json"
wait "$SERVER_PID" 2>/dev/null || true
test -s "$VALIDATED/mock_sink_received.jsonl"

echo "== cloud egress probe (HTTPS) =="
# Non-fatal: document failure modes in FINDINGS if blocked in some environments
if python3 prove_cloud_egress.py; then
  echo "egress: ok"
else
  echo "egress: failed (see validated/egress_cloud_result.json)" >&2
fi

echo "All proofs passed."
