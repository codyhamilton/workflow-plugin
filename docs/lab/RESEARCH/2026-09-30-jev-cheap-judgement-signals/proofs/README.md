# Proofs — cheap Jev judgement signals (closed 4/4)

Runnable pack for the white paper open questions. **Do not** change default plugin behaviour; hooks are opt-in via `hooks-settings-snippet.json`.

## Closed questions

| # | Topic | Evidence |
|---|--------|----------|
| 1 | PostToolBatch / hooks availability | [`post-tool-batch-hooks.md`](post-tool-batch-hooks.md) + `post_tool_batch_signal.py` + `run_proofs.sh` |
| 2 | Deterministic gate thresholds | [`deterministic-gate-thresholds.md`](deterministic-gate-thresholds.md) + `gate_threshold_simulation.py` → [`validated/gate_simulation_result.json`](validated/gate_simulation_result.json) |
| 3 | Compact Jev state schemas | [`jev-compact-state-schemas.md`](jev-compact-state-schemas.md) + `jev_signal_schemas.py` |
| 4 | False-negative / skip-rate plan | [`false-negative-measurement-plan.md`](false-negative-measurement-plan.md) + `validated/weekly_skim_recipe.sh` |

## Run everything

```bash
cd docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs
chmod +x run_proofs.sh
./run_proofs.sh
```

Expected: unittest OK, simulation JSON printed, hook probe writes non-empty temp log.

## One-paragraph answers

1. **Hooks:** Claude Code exposes the same events in CLI and cloud; `PostToolBatch` includes `session_id`, `transcript_path`, optional `agent_id`, and `tool_calls[]` — no built-in turn count. Opt-in `post_tool_batch_signal.py` logs turn proxy + transcript bytes + gate flags to `tools/driver/.jev-signal-log.jsonl` without calling Jev. Cursor Cloud has no Claude hooks; use driver JSONL there.

2. **Gates:** Log `band_exit` at **76** turns, handoff signal at **85** / **125k** peak / **3MiB** JSONL, escalate at **100** / **130k** / **5MiB** — catches maps >100-turn workers and the 296-call / 12.7MB case in simulation.

3. **Schemas:** Four small `state` objects with Score/Choice questions in `jev_signal_schemas.py`; phase alignment sanity is separate from `outcome-evidence` and does not touch the kill line.

4. **Measurement:** Weekly skim of `.jev-signal-log.jsonl` + `.assert-log.jsonl` with `weekly_skim_recipe.sh`; false negatives via deterministic assert join + 5-row human audit file `.jev-signal-audit.jsonl`.

## LCD harness (closed)

Host `codyh-ubuntu`, checkout `112ccfe` (master after PR #24). OpenCode 1.18.33 with `deepseek/deepseek-flash`: `run_proofs.sh` exit 0, gate simulation checks true, unittest 6/6, fixture wrote one `kind=post_tool_batch` row with `handoff_signal` and `jev_eligible`.

OpenCode does not fire Claude `PostToolBatch` command hooks (per-tool `execute` before/after only). Live `.jev-signal-log.jsonl` was skipped there. Live PostToolBatch logging is Claude Code, or a custom OpenCode plugin that aggregates `tool.execute.after` into `process_hook_input`. This fixture probe is the validated LCD stand-in. Folded into the resolved white paper; not a further research item.
