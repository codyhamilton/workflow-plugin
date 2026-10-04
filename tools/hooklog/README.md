# hooklog

Local, advisory capture of hook payloads as a session happens. All command hooks exit 0;
OpenCode observers leave inputs and outputs unchanged. The store remains
`~/.local/share/workflow-plugin/hooklog/<harness>/<session>.jsonl`.
Override it with `WORKFLOW_HOOKLOG_DIR`, or disable capture with `WORKFLOW_HOOKLOG=off`.
Secret patterns and credential/header keys are redacted; string fields are clipped at 2 KB,
user prompts at 20 KB, and collections at 40 items. Capture failures never deny or rewrite
an action. Cursor receives the permissive response required by its pre-action schema.

| Harness | Catalog requirement | Registration |
|---------|---------------------|--------------|
| Claude Code | 33 catalog keys; 31 active + 2 integration-only | [`hooks/hooks.json`](../../hooks/hooks.json), command handlers |
| Cursor | 22 claimed; 21 enumerated | [`hooks/cursor.json`](../../hooks/cursor.json), selected by `.cursor-plugin/plugin.json` |
| OpenCode | 18 Hooks + 28 bus types | [`packages/opencode-workflow-hooks`](../../packages/opencode-workflow-hooks), JS callbacks |
| Codex | 12 events | [`codex-hooks.example.json`](codex-hooks.example.json), command handlers |

The supplied 2026-10-03 catalog's Cursor subtotal says 19 agent hooks but lists 18.
The [official plugin reference](https://cursor.com/docs/reference/plugins#available-hook-events)
also lists those 18, plus 2 Tab hooks and workspaceOpen: **21 distinct names**. Every named
catalog event is registered. The 22nd name needs a catalog correction; it is not fabricated.

## Quality service

Rows are posted to the quality service (`WORKFLOW_QUALITY_URL`, default `http://127.0.0.1:8765`, the address `.mcp.json`
registers; set it empty to disable). If it is unset, down or slow (`WORKFLOW_QUALITY_TIMEOUT`, 2 s), the row is appended to the
JSONL store above, which then acts as a spool; `tools/quality/backfill_hooklog.py` drains it. An explicit `WORKFLOW_HOOKLOG_DIR`
means file-only. See `docs/lab/QUALITY-SERVICE.md`.

Plan file writes also run the [artifact submission backstop](../../docs/lab/QUALITY-SERVICE.md#hook-backstop)
after capture. Its HTTP predicate and posts use the same `WORKFLOW_QUALITY_URL`,
independently of the hooklog spool setting; it never checks `WORKFLOW_QUALITY_DIR`.

## Claude Code

Load the checkout as a plugin (`claude --plugin-dir /absolute/path/workflow-plugin`), or use
the marketplace plugin. `hooks/hooks.json` records with `--harness auto` and resolves its
script from `${CLAUDE_PLUGIN_ROOT}` (with `$PLUGIN_ROOT` fallback).

**Worktree integration caveat:** [Claude's WorktreeCreate contract](https://code.claude.com/docs/en/hooks#worktreecreate)
replaces built-in creation and requires a directory path on stdout. WorktreeRemove also
replaces cleanup. A standalone logger cannot observe these two events without taking over
those operations. Both keys therefore have **empty registration arrays** in the shipped config, preserving the
host's built-in worktree behavior. To capture them, call the logger **inside an existing
worktree handler** with its input JSON, preserving that handler's creation/removal and stdout
path contract. Do not add a standalone logger as a replacement worktree handler. For example,
from a handler that already has the payload in `$payload`:

```sh
printf '%s\n' "$payload" | python3 "$CLAUDE_PLUGIN_ROOT/tools/hooklog/hooklog.py" record --harness claude
# The existing handler then performs its original operation and returns its original output.
```

The logger supports both event names; **automatic capture of these two cannot meet the
observe-only contract** on this host. This is an explicit exception to all-33 active registration.

## Cursor

The plugin manifest selects `./hooks/cursor.json`, so native events are first-class and
Claude-name import mapping is no longer needed. This replaces default `hooks/hooks.json`
discovery for Cursor. Commands resolve `${CURSOR_PLUGIN_ROOT}` and pass the registration's
`--event`, ensuring an allow response even if input is malformed or logging is disabled.

For a standalone user/project install, merge [`cursor-hooks.example.json`](cursor-hooks.example.json)
into `~/.cursor/hooks.json` or `<project>/.cursor/hooks.json`, replacing `/ABS/PATH/workflow-plugin`
with the checkout path. Preserve unrelated existing hooks. Use one registration path to avoid
capturing each event twice.

Agent names: sessionStart, sessionEnd, preToolUse, postToolUse, postToolUseFailure,
subagentStart, subagentStop, beforeShellExecution, afterShellExecution, beforeMCPExecution,
afterMCPExecution, beforeReadFile, afterFileEdit, beforeSubmitPrompt, preCompact, stop,
afterAgentResponse, afterAgentThought. Tab: beforeTabFileRead, afterTabFileEdit. App: workspaceOpen.

Cloud agents omit sessionStart/sessionEnd, beforeMCPExecution/afterMCPExecution, both Tab hooks,
and workspaceOpen according to the supplied catalog. Registration cannot create events the
host omits. Headless `agent -p` can also omit beforeSubmitPrompt and stop (observed in the
2.6.0 smoke); interactive coverage needs a host run. workspaceOpen has no session and writes
`cursor/unknown.jsonl`.

Permission hooks print `{"permission":"allow"}`; beforeSubmitPrompt prints `{"continue":true}`;
other Cursor capture hooks print `{}`. The separate artifact-submit command may
emit advisory `additionalContext` on `postToolUse`; `afterFileEdit` remains `{}`.

## OpenCode

Register the package's `src/index.ts` in project/global `opencode.json`; see the
[package README](../../packages/opencode-workflow-hooks/README.md). All 18 capture callbacks are
present, including config, dispose, permission.ask, chat parameters/headers, tool definitions,
shell environment and experimental transforms/compaction/model selection. `event` captures
all 28 catalog bus names, plus future types. Older runtimes may not invoke newer callbacks.

Rows preserve native hook names and `source: hook|bus|derived`. Bus tool/shell events are
observations; dedicated tool callbacks provide completed tool calls. Derived PostToolBatch and
Stop rows retain existing turn markers. Nested session/message/part envelopes resolve to the
owning session; callbacks with no session write `opencode/unknown.jsonl`.

`WORKFLOW_OPENCODE_SIGNALS=0` disables soft signals independently of hooklog. Writes are ordered
and teardown awaits capture; logger errors are swallowed. Callbacks never change permissions,
arguments, prompts, headers, config, environment, tool definitions or experimental outputs.

## Codex

Merge [`codex-hooks.example.json`](codex-hooks.example.json) into **`~/.codex/hooks.json`** or
**`<project>/.codex/hooks.json`**, replacing `/ABS/PATH/workflow-plugin` with the absolute checkout
path. Preserve existing hooks. Codex also supports inline `[hooks]` in `config.toml`.
Non-managed hooks need the host's trust review before execution; installing a definition does
not bypass that review. See [official OpenAI documentation](https://developers.openai.com/codex/hooks).

All 12 names use `hooklog.py record --harness codex`: SessionStart, SessionEnd, SubagentStart,
SubagentStop, PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact,
UserPromptSubmit, Stop, Interrupt. Explicit `codex` avoids ambiguity with Claude's common
payload fields; `auto` only distinguishes Cursor from Claude. Codex is **not N/A**.
Hosted tools such as WebSearch skip PreToolUse/PostToolUse, so their absence is a host gap.
Codex capture and artifact-submit command hooks emit no stdout or control decision.

## Rows and turns

Inspect with `python3 tools/hooklog/hooklog.py ls` and `show <file>`.
The v1 schema keeps `{v, ts, harness, session_id, hook_event, kind, cwd}` and adds bounded,
redacted native payload details in `data`. Existing prompt/tool/step fields remain compatible.
New pre-tool rows use `tool_pre`; lifecycle and unknown named events use `event`. Events with
no name or malformed JSON are ignored. Subagent IDs are preserved as `agent_id`.

`events.load_hooklog` counts one model response per turn:

- Cursor: afterAgentThought (`step`) marks each response; following tools belong to it.
- Claude: PostToolBatch (`batch_end`) closes a tool turn; Stop closes the final reply.
- OpenCode: step-finish bus parts derive PostToolBatch; session.idle derives Stop.
- Codex and logs without step/batch markers use the existing 1.5 s tool-gap heuristic.

Lifecycle/pre-tool/bus observations do not advance turns. SessionEnd is a lifecycle observation,
so it cannot repeat Stop's final turn. Specific Cursor shell/MCP/edit observations remain in
JSONL but are ignored by the loader when canonical postToolUse events are present. Tab edits
are excluded from agent turns. Subagent rows are excluded from main-session analysis.

## Tests and smoke notes (2.7.0)

```sh
python3 -m unittest discover -s tools/hooklog/tests -v
python3 -m unittest discover -s tools/jev-variants/tests -v
python3 -m unittest discover -s packages/opencode-workflow-hooks/tests -v
node --experimental-strip-types --test packages/opencode-workflow-hooks/tests/test_hooks.mjs
```

The command smoke executes every active shipped registration in a temporary store, plus
manual logger payloads for both integration-only worktree names, including all
12 Codex names. OpenCode's callback smoke invokes all 18 keys and 28 bus types, verifies
unchanged permission/args/headers/compaction outputs, nested session IDs, redaction, boundary
markers and unavailable-logger tolerance. These prove adapter behavior, not live host delivery
of every event. Live Claude and Cursor sessions were not run for this change per invoker's
harness restriction. The prior 2.6.0 live turn-count observations remain reference evidence.

An OpenCode 1.18.33 startup smoke loaded the local plugin using `OPENCODE_CONFIG_CONTENT`
and an intentionally unavailable model (no inference). It captured config/dispose, session
created/updated/status/error/idle, chat.message/params/headers/system transform, and nested
message/part events into the expected session file. The host exited 1 for the unavailable
model; this is a plugin-load/error-path smoke, not a successful tool run.
