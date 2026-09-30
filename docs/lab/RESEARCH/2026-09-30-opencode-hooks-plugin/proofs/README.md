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
| `batch_aggregator.py` | Shim → `packages/opencode-workflow-hooks/python/batch_aggregator.py` |
| `batch_flush_cli.py` | Shim → package `python/batch_flush_cli.py` |
| `plugin_sketch.ts` | Lab sketch; product plugin at `packages/opencode-workflow-hooks/` |
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

## LCD harness (closed)

Coding Harness Manager, host `codyh-ubuntu`, checkout `d4c4da1` (master after PR #28). `./run_proofs.sh` exit 0. Unittest 4/4. Turn-76 simulation wrote one `kind=post_tool_batch` row with `gate.band_exit=true`.

`plugin_sketch.ts` was not installed and this script does not load it. The closed proof is `batch_aggregator.py` plus the shared Jev gate. Folded into the resolved white paper [`../../../PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](../../../PROPOSALS/2026-09-30-opencode-hooks-plugin.md). Not a further research item.
