# OpenCode workflow-hooks plugin — research pack (2026-09-30)

**Status:** closed (lab). **Not drop-in** Claude Code / Cursor hook compatibility — approximates soft-signal behaviour from the resolved [cheap-Jev proposal](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) using OpenCode-native hooks.

## Closed threads (evidence)

| # | Question | Answer doc | Proof |
|---|----------|------------|-------|
| 1 | OpenCode plugin API inventory (events, ship, config) | [`OPENCODE-PLUGIN-API.md`](OPENCODE-PLUGIN-API.md) | Public [opencode-plugins-manual](https://github.com/joshuadavidthomas/opencode-plugins-manual) + migration doc |
| 2 | Claude/Cursor hook sites → OpenCode | [`HOOK-SITE-MAP.md`](HOOK-SITE-MAP.md) | Explicit gaps table |
| 3 | Prototype: `tool.execute.after` batching + gates | [`proofs/README.md`](proofs/README.md) | `run_proofs.sh` + unittest |
| 4 | `WORKFLOW_ANALYTICS_URL` dual-write | [`ANALYTICS-INTEGRATION.md`](ANALYTICS-INTEGRATION.md) | Reuses sink pack `dual_write_sink.py` |
| 5 | Ship separate npm plugin vs in-tree lab | [`RECOMMENDATION.md`](RECOMMENDATION.md) | orchestrate ≠ phase-runner preserved |

## Runnable validation (Coding Harness Manager / `codyh-ubuntu`)

```bash
cd docs/lab/RESEARCH/2026-09-30-opencode-hooks-plugin/proofs
./run_proofs.sh
```

Expect: unittest green, one `.jev-signal-log.jsonl` row at turn 76 (same gate semantics as Jev pack), optional analytics envelope when `WORKFLOW_ANALYTICS_URL` unset (local skip).

## Related packs

- Soft signals + Claude `PostToolBatch` probe: [`../2026-09-30-jev-cheap-judgement-signals/`](../2026-09-30-jev-cheap-judgement-signals/INDEX.md)
- Analytics envelope: [`../2026-09-30-durable-analytics-sink/`](../2026-09-30-durable-analytics-sink/INDEX.md)
- OpenCode skills symlink: `install.sh` `WORKFLOW_INSTALL_MODE=opencode` (PR #26)

## Policy (unchanged)

- Soft signals are **advisory** (log, optional Jev later); **kill line** stays `assert_phase --deterministic`.
- No default product wiring; lab proofs only.
