# Analytics sink integration (closed)

Cross-ref: [`../2026-09-30-durable-analytics-sink/`](../2026-09-30-durable-analytics-sink/INDEX.md).

## Behaviour on master (lab only)

| Env var | Role |
|---------|------|
| `WORKFLOW_ANALYTICS_URL` | HTTPS POST target; **unset → remote skip** (exit 0 workflow) |
| `WORKFLOW_ANALYTICS_TOKEN` | Optional `Authorization: Bearer` |
| `WORKFLOW_ANALYTICS_LOCAL_LOG` | Override local JSONL for envelope experiments |
| `WORKFLOW_ANALYTICS_HOST_KIND` | Test override for `host_kind` |
| `WORKFLOW_INSTALL_MODE=opencode` | Sets envelope `host_kind: opencode` / `host_detail: opencode` |

Helper: [`../2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py`](../2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py).

## OpenCode plugin emission

When the batch aggregator writes a legacy row to `WORKFLOW_JEV_SIGNAL_LOG` (default `tools/driver/.jev-signal-log.jsonl`):

1. **Local:** append legacy row (unchanged consumer for weekly skim / grep).
2. **Remote (optional):** `emit_from_jev_signal_row(row, local_path=...)` wraps envelope:

   - `kind`: `jev.post_tool_batch` (from row `kind: post_tool_batch`)
   - `payload`: row body minus duplicated top-level fields
   - `session_id`: OpenCode `sessionID` passed through
   - `source`: `opencode-hooks-plugin-lab` in proof; product would use npm package name

Remote failure sets `_remote_ok: false` on the returned dict; **must not block** the agent loop (same policy as sink pack).

## What we do not emit by default

- Full tool stdout / `output.output` bodies (size + redaction — see EVENT-SCHEMA § Size).
- `TYPESAFE_API_KEY` or provider keys.
- Classify `.classify-log.jsonl` rows (not promoted).

## Product wiring status

**None on master.** Proofs call `dual_write_sink` only from lab `batch_aggregator.py`. Driver `run_record.py` is not modified.

## Skip documentation

If `WORKFLOW_ANALYTICS_URL` is unset, proof records `_remote_detail: skipped:no_url` — intentional for offline LCD and CI.
