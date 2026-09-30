# Recommendation — packaging and boundaries (closed)

## Ship as a separate OpenCode plugin package

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **Separate npm package** (e.g. `@codyhamilton/opencode-workflow-signals`) | **Recommended** | OpenCode discovery is `opencode.json` + npm/`file://`; keeps Bun/TS lifecycle out of Python `tools/driver/`; version pin independent of workflow-plugin **2.5.0** |
| In-tree under `plugins/workflow-lab/` | **Lab proofs only** | Acceptable for `proofs/plugin_sketch.ts` + docs; do **not** add to default Claude/Cursor plugin manifests |
| Merge into core `workflow` plugin | **Reject** | Violates “no default product behaviour”; couples soft signals to skills install path |

## Boundary: orchestrate ≠ phase-runner

| Layer | Owner | OpenCode plugin role |
|-------|-------|----------------------|
| Phase orchestration | `tools/driver/` (`status`, `run.py --once`, MCP) | **None** — Grok Bot calls CLIs |
| Hard kill / merge gates | `assert_phase.py --deterministic` | **None** — optional subprocess invoke is explicit opt-in |
| Soft signals | Advisory JSONL + optional Jev + optional analytics POST | **Plugin** aggregates tool events, writes signal log |
| Skills / briefs | `install.sh`, `skills/*` | Symlink skills (PR #26); plugin does not replace skills |

## Implementation phases (product, post-acceptance)

1. **Lab** — validate `run_proofs.sh` on `codyh-ubuntu` OpenCode ≥ host pin; enable `file://` plugin locally.
2. **Package** — extract TS sketch to npm; document `workflow-signals.json` thresholds mirroring `gate_thresholds.py`.
3. **Dual-write** — call shared envelope helper (copy or thin npm wrapper posting same schema v1).
4. **Claude parity** — keep `post_tool_batch_signal.py` for Claude Code; share threshold constants via generated JSON from one source when wiring lands.

## Compatibility disclaimer

This plugin **approximates** Claude `PostToolBatch` behaviour; it does **not** claim drop-in compatibility with Cursor hook JSON or Claude hook stdin schemas.
