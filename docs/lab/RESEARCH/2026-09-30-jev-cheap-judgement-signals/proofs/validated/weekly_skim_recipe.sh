#!/usr/bin/env bash
# Weekly Grok Bot skim helpers (read-only). Log path overridable.
set -euo pipefail
LOG="${WORKFLOW_JEV_SIGNAL_LOG:-tools/driver/.jev-signal-log.jsonl}"
if [[ ! -f "$LOG" ]]; then
  echo "No signal log at $LOG"
  exit 0
fi
echo "== line count =="
wc -l "$LOG"
echo "== post_tool_batch escalate count =="
jq -s '[.[] | select(.kind=="post_tool_batch" and .gate.escalate==true)] | length' "$LOG"
echo "== distinct agent_id with band_exit =="
jq -s '[.[] | select(.gate.band_exit==true) | .agent_id] | unique | length' "$LOG"
