# hooklog

Harness-neutral capture of user prompts and tool calls, written by hooks as the session happens.
Two uses: (1) historical corpus for Jev testing (Cursor transcripts omit tool calls and results; hooks
are the only way to get them), (2) the "recent tools" a live Jev call needs, which must be stored somewhere.

- Store: `~/.local/share/workflow-plugin/hooklog/<harness>/<session_id>.jsonl` (override `WORKFLOW_HOOKLOG_DIR`;
  disable with `WORKFLOW_HOOKLOG=off`). Local only; secrets pattern-redacted, fields truncated (2 KB, prompts 20 KB).
- Claude Code: `hooks/hooks.json` at the repo root registers it for the `workflow` plugin (UserPromptSubmit,
  PostToolUse, PostToolUseFailure, Stop).
- Cursor: copy `cursor-hooks.example.json` to `~/.cursor/hooks.json` (or `.cursor/hooks.json`) and fix the path.
  Cursor hook event names/payloads vary by version and are **not verified here**; `normalize` is tolerant and
  silently ignores unknown events. Check `hooklog.py ls` after a session.
- OpenCode: not wired (use the existing opencode-workflow-hooks package; adapter TODO).
- Hooks always exit 0 and never print to stdout (except Cursor's `{"continue": true}`).
- Inspect: `hooklog.py ls`, `hooklog.py show <file>`.
- Row: `{v, ts, harness, session_id, hook_event, kind, cwd, text|tool_name|tool_use_id|input|output|ok}`.

Turn counting (`events.load_hooklog`): a turn is one model response.
- Cursor: `afterAgentThought` fires once per model step (its `generation_id` ends `-<step>-<rand>`), so each is a turn and
  the tool calls after it belong to it. **Verified** with `agent -p --model composer-2.5` (4 steps for a 3-tool-batch task;
  `postToolUse` carries `tool_output`, JSON-encoded).
- Claude: `PostToolBatch` (`batch_end`) closes a tool-calling turn; `Stop` always closes a final text-only turn (the
  reply has no hook of its own). **Verified** with `claude -p --plugin-dir <repo>` (Read+Read, Bash, Edit, then a reply = 4 turns;
  PostToolBatch carried the tool_use_ids; UserPromptSubmit, PostToolUse and Stop all fired). Use `--plugin-dir` to load the local
  plugin's `hooks/hooks.json` instead of the published one.
- An agent reply alone is not a turn; subagent rows (`agent_id`) are excluded; logs with no marker fall back to a 1.5 s gap.

Cursor `agent -p` did **not** fire `beforeSubmitPrompt` or `stop` in the test run (only `sessionStart`, `afterAgentThought`,
`preToolUse`, `postToolUse`, `after*Execution`, `sessionEnd`), so user prompts are captured only where the interactive
client fires `beforeSubmitPrompt` (unverified). `afterShellExecution` duplicates `postToolUse`, so the example registers
only `postToolUse`.
