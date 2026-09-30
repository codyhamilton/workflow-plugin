# Proofs — OpenCode batch aggregator

Lab-only. Validates shared gate thresholds and optional analytics dual-write without a live OpenCode process.

## Run

```bash
./run_proofs.sh
# or
python3 -m unittest discover -s . -p 'test_*.py' -v
```

## Files

| File | Role |
|------|------|
| `batch_aggregator.py` | Aggregate tool calls → `process_hook_input` (Jev pack) |
| `batch_flush_cli.py` | Stdin helper for `plugin_sketch.ts` spawn |
| `plugin_sketch.ts` | TS sketch: buffer + flush on `message.updated` / `session.idle` |
| `test_proofs.py` | Simulates 76 model steps; expects signal log row + analytics skip |

## Dependencies (sibling packs)

- `../2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py`
- `../2026-09-30-jev-cheap-judgement-signals/proofs/post_tool_batch_signal.py`
- `../2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py`

## Env

| Variable | Default |
|----------|---------|
| `WORKFLOW_JEV_SIGNAL_LOG` | temp file in tests |
| `WORKFLOW_SIGNAL_STATE_DIR` | temp dir in tests |
| `WORKFLOW_ANALYTICS_URL` | unset (remote skip) |
| `WORKFLOW_INSTALL_MODE` | `opencode` in analytics test |
