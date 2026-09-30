# PostToolBatch / Claude hooks (closed)

**Source:** [Claude Code hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks) fetched 2026-09-30 (`code.claude.com` mirror). **Validated:** `run_proofs.sh` exercises `post_tool_batch_signal.py` with fixture stdin.

## Local CLI vs cloud / headless

| Surface | Hooks fire? | Notes |
|---------|-------------|--------|
| Terminal CLI | Yes | Same event set per Anthropic: “fires the same hook events wherever it runs: terminal, IDE, Desktop, **cloud sessions**.” |
| Claude Code on the web | Yes | `CLAUDE_CODE_REMOTE=true` in hook subprocess env (v2.1.199+); matches in-repo `session-start.sh` guard pattern. |
| Cursor Cloud Agent (this repo’s VM) | **No** | `docs/lab/FINDINGS.md`: no `CLAUDECODE` / `CLAUDE_CODE_REMOTE`; skills baked in image — **driver JSONL path** is the Cursor stand-in until workers run under Claude Code hooks. |

Cloud-specific settings: cloud sessions **do not** read local `~/.claude/settings.json`; operator-seeded hooks on the runner image apply instead (same doc § settings carry-over).

## Events relevant to the four use cases

| Event | Matcher | Use case |
|-------|---------|----------|
| `PostToolBatch` | none (always fires) | **1** turn/size gate + optional Jev |
| `SubagentStart` | `agent_type` | Stamp `brief_id` / budget baseline (future) |
| `SubagentStop` | `agent_type` | **3** unit-complete log (`log_subagent_stop.py` probe) |
| `Stop` | n/a | Attach in-flight signals to metrics row (future) |
| Phase assert CLI | n/a | **4** `assert_phase.py --deterministic` (not a hook) |

`PostToolBatch` fires **once per model step** after all parallel tools in the batch resolve — preferred over `PostToolUse` for batch-aware counters.

## Common stdin JSON fields (all command hooks)

| Field | Present | Purpose |
|-------|---------|---------|
| `session_id` | Yes | Correlate with `.jev-signal-log.jsonl` and run record |
| `transcript_path` | Yes | Path to session JSONL (may **lag** current turn) |
| `cwd` | Yes | Project root |
| `hook_event_name` | Yes | e.g. `PostToolBatch` |
| `permission_mode` | Often | `default`, `auto`, … |
| `prompt_id` | v2.1.196+ | Correlate with OTel |
| `agent_id` | Subagent / `--agent` only | Distinguish worker from parent |
| `agent_type` | Subagent / `--agent` only | Matcher on `SubagentStart` / `SubagentStop` |

**Not in common fields:** turn count, peak context, or `tool_batch` id — the hook must derive turns (PostToolBatch counter or transcript scan) and read `tool_calls[]` on `PostToolBatch` only.

### PostToolBatch-specific fields

- `tool_calls[]`: `{tool_name, tool_input, tool_use_id, tool_response}` per call in the batch (`tool_response` is serialized model-facing content, can be large).

### SubagentStop-specific fields

- `agent_transcript_path` — subagent JSONL under `subagents/`
- `last_assistant_message` — preferred over parsing transcript on stop

## Minimal command hook (log only, no Jev)

See `hooks-settings-snippet.json` and `post_tool_batch_signal.py`. Behaviour:

1. Increment per-`(session_id, agent_id)` PostToolBatch counter (turn proxy when transcript lags).
2. `stat(transcript_path)` for bytes; optional scan for peak `usage` tokens.
3. Evaluate `gate_thresholds.evaluate_gate`.
4. Append **only when** `band_exit`, `handoff_signal`, or `escalate` to `WORKFLOW_JEV_SIGNAL_LOG` (default `tools/driver/.jev-signal-log.jsonl`).
5. **Always exit 0** — no `decision: block`.

## Brief id / phase / unit without loading skills

| Field | How to populate |
|-------|-----------------|
| `slug` / `phase` | Read `Workflow-Phase:` trailer via `git log -1 --format=%b` or env `WORKFLOW_SLUG` / `WORKFLOW_PHASE` set by driver bootstrap (documented pattern; not shipped by default). |
| `brief_id` | `SubagentStart` matcher on `agent_type` + map to brief file under `docs/plans/.../briefs/`; or parse Task tool metadata when driver spawns workers. |
| `unit_id` | Trailer slug + phase index, or brief filename stem at `SubagentStop`. |

Proof hook logs raw `session_id` / `agent_id` only; driver integration is a later spike.
