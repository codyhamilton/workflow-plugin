# Inventory — what emits events today

Ground truth paths are relative to the **workflow-plugin** repo root unless noted. Gitignored logs live under `tools/driver/` or `tools/transcript/` in a consuming workspace.

## Driver and phase control

| Emitter | Path | Trigger | Row shape (summary) | Durable on cloud VM? |
|---------|------|---------|---------------------|----------------------|
| Phase status (read-only) | `tools/driver/status.py` | CLI / MCP `status` | JSON stdout from `resolve.py` + trailers | N/A (derived from **git**, survives push) |
| One-phase trigger | `tools/driver/run.py`, `tools/driver/trigger.py` | `--once`, MCP `trigger_phase` | stdout JSON (`workflow-report`, turns, cost) | stdout only unless recorded |
| Run record | `tools/driver/run_record.py` | Appended from `run.py`, `assert_phase.py` | `kind`: `trigger` \| `assert`; `ts`, plan/slug, cost slice | **No** — default `tools/driver/.run-record.jsonl` |
| Run record CLI | `tools/driver/record_cli.py` | Summarize JSONL | Aggregated JSON | Reads local file only |
| Assert (kill line) | `tools/driver/assert_phase.py`, `tools/driver/phase_assert.py` | `--deterministic`, `--live`, `--dry-run` | Pass/fail + Jev audit fields | Assert **result** should be in run record / remote sink; log is local |
| Assert log | `tools/driver/assert_phase.py` → `tools/driver/.assert-log.jsonl` | `--live` | `ts`, `question_id`, `state_hash`, `pass`, `jev`, `usage` | **No** (gitignored) |
| MCP surface | `tools/driver/mcp_server.py` | stdio JSON-RPC | Same as status/trigger | Ephemeral unless caller persists |
| Skills gate | `tools/driver/check_skills.py` | Pre-flight | JSON `{ok, harness, skills_found, missing}` | Ephemeral |

Env overrides: `DRIVER_RUN_RECORD` / `--record` on driver CLIs; assert log path is fixed in `assert_phase.py` (`DEFAULT_LOG_PATH`).

## Git trailers (durable without a sink)

| Emitter | Path | Content |
|---------|------|---------|
| Trailer parser | `tools/driver/resolve.py` | `Workflow-Phase: <slug>:<n>` and `<slug>:done` from `git log` |
| Commit helper (tests) | `tools/driver/tests/fixtures.py` | `commit_trailer()` |

Trailers are the **authoritative phase checkpoint** for Grok Bot resume. They are not high-volume telemetry; they are low-cardinality state.

## Jev soft signals (lab / opt-in)

| Emitter | Path | Trigger | Row shape |
|---------|------|---------|-----------|
| PostToolBatch probe | `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/post_tool_batch_signal.py` | Claude hook stdin | `kind: post_tool_batch`, `gate`, session/agent ids |
| SubagentStop probe | `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/log_subagent_stop.py` | Claude hook | `kind: subagent_stop` |
| Default log | `tools/driver/.jev-signal-log.jsonl` | When gate trips | Sparse append |
| State dir | `~/.cache/workflow-plugin/signal-state/` or `WORKFLOW_SIGNAL_STATE_DIR` | Counter state | Not an event stream |

Env: `WORKFLOW_JEV_SIGNAL_LOG`, `WORKFLOW_SIGNAL_STATE_DIR`, `WORKFLOW_SLUG`, `WORKFLOW_PHASE` (documented in Jev proposal; not set by driver on master).

## Transcript / classify (visualization — not measurement path)

| Emitter | Path | Notes |
|---------|------|--------|
| Classify CLI | `tools/transcript/classify.py` | Session kind + alignment score |
| Classify log | `tools/transcript/.classify-log.jsonl` | **Do not** promote to KPI or default sink |

## Eval / outcome rows

| Emitter | Path | Notes |
|---------|------|--------|
| Trailer completeness | `evals/scenarios/trailer-completeness/verify.py` | Shells status → once → assert; writes outcome JSON for harness |

## Install / harness routing (metadata, not a stream)

| Emitter | Path | Notes |
|---------|------|--------|
| Installer route | `install.sh --print-route` | `cursor-cloud`, `claude-code`, `opencode`, workspace |
| Cloud bootstrap | `docs/lab/bootstrap/cursor-cloud-setup.sh` | Image bake recipe |

## Gap (why this research pack exists)

Nothing on master **ships** a remote append path. All high-value JSONL sinks are **workspace-local** and **gitignored** (see `.gitignore`: `.run-record.jsonl`, `.assert-log.jsonl`, `.jev-signal-log.jsonl`, `.classify-log.jsonl`). Cloud agents that never push logs lose per-run cost, assert slices, and soft-signal rows unless copied to git, PR comments, or an external sink.
