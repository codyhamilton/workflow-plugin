# Findings — OpenCode hooks plugin research (2026-09-30)

Confidence: **high** for the API inventory (public manual) and for the Python batch proofs. The `message.updated` / `session.idle` flush is the accepted approximation in the resolved white paper. LCD on `codyh-ubuntu` @ `d4c4da1` ran `run_proofs.sh` only; `plugin_sketch.ts` was not installed, so those bus events were not observed live. That is closed evidence, not an open spike.

## Closed answers

1. **Plugin API:** Hooks + `event` bus documented in [`OPENCODE-PLUGIN-API.md`](OPENCODE-PLUGIN-API.md). Ship via `opencode.json` `"plugin"` array, local `file://.opencode/plugin/*.ts`, or npm with version pin; skills remain separate (`install.sh --opencode-skills`).

2. **Hook map:** [`HOOK-SITE-MAP.md`](HOOK-SITE-MAP.md). Largest gap: **no `PostToolBatch`** — aggregate `tool.execute.after` and flush at model-step boundary. Cursor Cloud still **driver JSONL**, not OpenCode.

3. **Prototype:** [`proofs/`](proofs/README.md) — Python `batch_aggregator.py` + TS `plugin_sketch.ts`; unittest simulates 76 single-tool steps, writes one signal row at `band_exit`; optional analytics envelope via `dual_write_sink`.

4. **Analytics:** [`ANALYTICS-INTEGRATION.md`](ANALYTICS-INTEGRATION.md) — reuse sink pack; `WORKFLOW_ANALYTICS_URL` unset skips POST; `host_kind: opencode` when `WORKFLOW_INSTALL_MODE=opencode`.

5. **Recommendation:** Separate npm OpenCode plugin; lab proofs in-tree; **orchestrate ≠ phase-runner**; no default product enablement — [`RECOMMENDATION.md`](RECOMMENDATION.md).

## Kill line (unchanged)

`assert_phase --deterministic` remains authoritative when Jev disagrees (`jev.disagreed_with_deterministic`). Plugin hooks **exit 0 / log only** for soft signals.

## Validation command

```bash
./docs/lab/RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/run_proofs.sh
```
