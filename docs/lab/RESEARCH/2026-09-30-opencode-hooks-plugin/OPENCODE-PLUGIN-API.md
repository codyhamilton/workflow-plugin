# OpenCode plugin API inventory (closed 2026-09-30)

**Sources (public, fetched 2026-09-30):**

- [opencode-plugins-manual](https://github.com/joshuadavidthomas/opencode-plugins-manual) — hooks, packaging, config (`04-hooks-reference.md`, `07-events.md`, `11-packaging-and-distribution.md`, `12-plugin-configuration.md`, `10-claude-code-migration.md`)
- Community mirror: [opencode.runman.ai plugins advanced](https://opencode.runman.ai/en/5-advanced/12b-plugins-advanced.html)
- Runtime caveats: [anomalyco/opencode issues](https://github.com/anomalyco/opencode) on `tool.execute.after` (MCP vs native paths, UI vs `output.output` mutation)

**Assumption:** OpenCode runtime matches the manual’s `3efc95b` / `anomalyco/opencode` `dev` lineage unless a host pins an older build (e.g. **1.18.33** on `codyh-ubuntu` per Jev FINDINGS). Validate hook firing on the host OpenCode version before enabling live logging.

## Plugin shape

| Item | Detail |
|------|--------|
| Definition | TypeScript module exporting one or more `Plugin` async factories → **hooks object** |
| Runtime | **Bun** — TS imports without a build step for local/`file://` plugins |
| SDK | `@opencode-ai/plugin` (auto-installed under `.opencode/` for local plugins) |
| Context | `PluginInput`: `directory`, `$` (shell), `client` (SDK), etc. — see manual `03-plugin-context.md` |
| Isolation | **None** — same process, full FS/network/env; hook errors logged per-hook; **load errors break later plugins** |

## Discovery and config wiring

| Mechanism | Location / format |
|-----------|-------------------|
| Config array | `opencode.json` (project + global under `~/.config/opencode/`) — key `"plugin": [...]` |
| Local glob | `.opencode/plugin/*.{ts,js}` and `~/.config/opencode/plugin/*.{ts,js}` (**top-level only**, not nested dirs) |
| Registration | `"my-pkg@1.0.0"` (npm, cached under `~/.cache/opencode/`) or `"file://.opencode/plugin/foo.ts"` |
| Defaults | Built-in auth plugins unless `OPENCODE_DISABLE_DEFAULT_PLUGINS=1` |
| Skills (this repo) | **Separate** from plugins: `install.sh --opencode-skills` symlinks into `~/.config/opencode/skills` (PR #26) |

Example (lab only — not installed by default):

```json
{
  "plugin": [
    "file://.opencode/plugin/workflow-signals.ts"
  ]
}
```

See [`proofs/opencode.json.example`](proofs/opencode.json.example).

## Hook surface (programmatic)

| Hook | Trigger | Can mutate |
|------|---------|------------|
| `config` | Plugin init | `command`, `agent`, `mcp` on config object |
| `tool` | Init | Register custom tools |
| `auth` | Provider init | Auth providers |
| `event` | Any bus event | Observer only |
| `chat.message` | User message before model | Message parts |
| `chat.params` | Before LLM request | temperature, topP, options |
| `permission.ask` | Permission prompt | allow / deny / ask |
| `tool.execute.before` | Each tool call | `args` |
| `tool.execute.after` | Each tool result | `title`, `output`, `metadata`; optional `inject` (synthetic user msgs, newer runtimes) |
| `experimental.text.complete` | After text gen | `text` |

## System events (`event` hook)

From manual `04-hooks-reference.md` / `07-events.md`:

| Family | Event types |
|--------|-------------|
| Command | `command.executed` |
| File | `file.edited`, `file.watcher.updated` |
| LSP | `lsp.client.diagnostics`, `lsp.updated` |
| Message | `message.part.removed`, `message.part.updated`, `message.removed`, `message.updated` |
| Permission | `permission.replied`, `permission.updated` |
| Session | `session.created`, `session.compacted`, `session.deleted`, `session.diff`, `session.error`, `session.idle`, `session.status`, `session.updated` |
| Tool | `tool.execute.after`, `tool.execute.before` (also dedicated hooks) |
| TUI | `tui.prompt.append`, `tui.command.execute`, `tui.toast.show` |

## Load sequence (summary)

1. Merge `plugin` arrays from project + global config and local glob.
2. `import()` each plugin (Bun compiles TS).
3. Call each exported `Plugin` factory → hooks.
4. Run `config` hooks; subscribe `event` hooks.

No hot reload — **restart OpenCode** after config/plugin changes.

## Gaps vs Claude Code command hooks

| Claude Code | OpenCode |
|-------------|----------|
| `PostToolBatch` (once per model step, `tool_calls[]` on stdin) | **No equivalent** — only per-tool `tool.execute.after` |
| Shell command hooks + JSON stdin | TS functions; spawn subprocess yourself if needed |
| `Stop` / `SubagentStop` with rich stdin | **No direct equivalent** — approximate via `session.idle`, subagent events in transcript, or custom agent wiring |
| Hook `reloadSkills` / SessionStart | Skills are filesystem/symlink discovery — use `install.sh`, not a plugin hook |
| Block tool via hook exit code | Use `permission.ask` deny or `tool.execute.before` arg mutation — **not** the workflow soft-signal pattern (we log only) |

## Implication for workflow-plugin

A **custom OpenCode plugin** can:

- Aggregate `tool.execute.after` + `message.updated` / `session.idle` to emulate **PostToolBatch** counters and call shared Python gate logic (or reimplement thresholds in TS).
- Subscribe to `session.compacted` for Pre/PostCompact **logging** analogues.
- Never replace **`tools/driver/`** phase orchestration (`run.py`, `assert_phase.py`) — Grok Bot / driver CLIs remain the phase-runner control plane.
