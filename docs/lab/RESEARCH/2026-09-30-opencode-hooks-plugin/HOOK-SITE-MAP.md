# Hook site map — Claude Code / Cursor → OpenCode

**Scope:** Soft-signal sites from [cheap-Jev research](../2026-09-30-jev-cheap-judgement-signals/INDEX.md) plus bootstrap hooks documented in this repo. **Cursor Cloud** has no Claude hook surface — driver JSONL stand-in (see FINDINGS).

Legend: **≈** approximate | **✓** close parity | **✗** no native equivalent | **—** out of scope (different product)

## Primary map

| Site we care about | Claude Code | Cursor (desktop/cloud) | OpenCode event / hook | Parity | Notes / gap |
|--------------------|-------------|------------------------|------------------------|--------|-------------|
| **PostToolBatch** (turn/size soft gate) | `PostToolBatch` command hook | **✗** (no batch hook) | `tool.execute.after` + flush on `message.updated` or `session.idle` | **≈** | Must aggregate N tool calls per model step; no `tool_calls[]` on one stdin blob — build from collector state |
| **PreToolUse** | `PreToolUse` | Tool hooks (product-specific) | `tool.execute.before` | **≈** | Match on `input.tool` in TS, not regex matcher |
| **PostToolUse** | `PostToolUse` | — | `tool.execute.after` | **≈** | Per tool, not batch-aware |
| **SessionStart** / skills bootstrap | `SessionStart` + `reloadSkills` | Image bake / project skills at process start | **—** / `session.created` (observe only) | **✗** | Use `install.sh` + `check_skills.py`; plugin cannot reload skills mid-turn |
| **PreCompact** | `PreCompact` | — | `event` → `session.compacted` (before/after timing **assumption**) | **≈** | Log-only steer; confirm payload on host OpenCode version |
| **PostCompact** | `PostCompact` | — | Same bus + diff size heuristics | **≈** | No Anthropic stdin schema |
| **SubagentStart** | `SubagentStart` | Subagent spawn (Task) | `config.agent` subagents + `chat.message` `agent` field (**assumption**) | **≈** | No `agent_type` matcher; stamp brief id in agent config or env |
| **SubagentStop** | `SubagentStop` | Subagent completion | `session.idle` / custom agent hook (**assumption**) | **≈** | Jev pack uses `log_subagent_stop.py` probe for Claude |
| **Stop** / metrics row | `Stop` | Session end | `session.idle` | **≈** | Finalize signal log rollup |
| **StopFailure** | `StopFailure` | — | `session.error` | **≈** | Escalation signal, not quality pass |
| **UserPromptSubmit** | `UserPromptSubmit` | User message | `chat.message` | **✓** | Optional nudge when gates already fired |
| **PermissionRequest** | Permission hook | — | `permission.ask` | **✓** | Auto-allow/deny policies |
| **Phase assert (hard kill)** | CLI / driver (not hook) | `assert_phase --deterministic` | Same CLI subprocess from plugin (**optional**) | **✓** | **Do not** move kill line into plugin hooks |
| **Post-build / orchestrate** | Skills + driver | Cloud agent rules | Skills symlink + **external** `tools/driver/*` | **—** | Plugin ≠ phase-runner; orchestrate stays outside plugin |

## Soft-signal use cases (Jev proposal)

| Use case | Claude anchor | OpenCode implementation sketch |
|----------|---------------|--------------------------------|
| 1 — Session size / progress | `PostToolBatch` + `gate_thresholds` | Plugin batch aggregator → `.jev-signal-log.jsonl`; optional `jev.post_tool_batch` envelope |
| 2 — Post-refine brief complexity | After refine skill / trailer | `chat.message` or `command.executed` when refine command used — **manual wiring** |
| 3 — Unit complete “needs review?” | `SubagentStop` | Subagent stop analogue + trailer `Workflow-Phase:` |
| 4 — Phase alignment sanity | `assert_phase` (deterministic) | **CLI only** — plugin may log shadow Jev, not enforce |

## Cursor-specific

| Cursor feature | Maps to OpenCode? |
|----------------|-------------------|
| Cloud Agent `CURSOR_AGENT=1` | **No** — use driver `.jev-signal-log.jsonl` or analytics envelope with `host_kind: cloud` |
| PostToolBatch-like batch gate in agent loop | **No first-party hook** — product-internal |
| MCP / hooks in `.cursor/` | Different schema — **not** mapped here |

## Explicit non-goals

- Drop-in reuse of `post_tool_batch_signal.py` as a Claude **command** hook on OpenCode.
- Default enablement in `workflow` or `workflow-lab` plugin manifests.
- Replacing `classify.py` or promoting classify thresholds to gates.

## Validation path

| Harness | Live PostToolBatch | OpenCode plugin path |
|---------|-------------------|----------------------|
| Claude Code CLI / remote | ✓ command hook | N/A |
| Cursor Cloud | ✗ | Driver JSONL |
| OpenCode LCD (`codyh-ubuntu`) | ✗ | This pack’s plugin sketch + `run_proofs.sh` |
