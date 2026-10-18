# Brief: 2-02 — MCP registrations and design 4

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/.mcp.json`, `plugins/yakka/.codex-mcp.json`, `packages/hooklog/cursor-mcp.example.json`, `packages/hooklog/codex-mcp.example.toml`, `docs/design/04-advisory-surface.md`, `docs/plans/16-python-local-client/reports/2-02-mcp-registrations.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/16-python-local-client/reports/2-02-mcp-registrations.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 2-01.
Budget: 8 files to read, about 80 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Phase 2 Outcome (lines 184-185); Domain: Plugin client, Assumption 2 (lines 76-79) for script location; Phase 3 is not this unit (wrapper `bin/yakka` dispatch stays Go until Phase 3).
2. `plugins/yakka/.mcp.json`, `plugins/yakka/.codex-mcp.json`, `packages/hooklog/cursor-mcp.example.json`, `packages/hooklog/codex-mcp.example.toml` — current `command` / `args`.
3. `docs/design/04-advisory-surface.md` — **Registration** (lines 94-97) and the opening **Shape** sentence (lines 18-20).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Every harness MCP registration in the plugin tree and hooklog examples starts `python3` on `plugins/yakka/client/yakka.py` with argument `mcp`, and design 4 names that process instead of the wrapper binary.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> Outcome: Each harness MCP registration starts `python3 plugins/yakka/client/yakka.py mcp` on stdio and does not resolve a binary.

> One script, `plugins/yakka/client/yakka.py`, run as `python3 plugins/yakka/client/yakka.py <command>`.

Design 4 today still says the wrapper (lines 96-97). This unit rewrites **Registration** to the Python stdio command. Do not change tool names, API tables, or skill prose beyond what is needed to name the process consistently in **Shape** and **Registration**.

## Changes

Update each owned MCP config so `command` is `python3` and `args` are the script path plus `"mcp"`:

- `plugins/yakka/.mcp.json`: `command` `python3`, `args` `["${CLAUDE_PLUGIN_ROOT}/client/yakka.py", "mcp"]` (drop `${CLAUDE_PLUGIN_ROOT}/bin/yakka`).
- `plugins/yakka/.codex-mcp.json`: `command` `python3`, `args` `["./client/yakka.py", "mcp"]` with existing `cwd` `.`.
- `packages/hooklog/cursor-mcp.example.json`: `command` `python3`, `args` `["/ABS/PATH/yakka/plugins/yakka/client/yakka.py", "mcp"]` (replace the `bin/yakka` path in `args`; keep the comment pattern of absolute checkout path).
- `packages/hooklog/codex-mcp.example.toml`: `command = "python3"`, `args = ["/ABS/PATH/yakka/plugins/yakka/client/yakka.py", "mcp"]`.

In `docs/design/04-advisory-surface.md`, replace the wrapper registration sentence with the same rule: harnesses spawn `python3 plugins/yakka/client/yakka.py mcp` (stdio). Mention that Phase 3 will also route `plugins/yakka/bin/yakka mcp` through that script; this phase's registrations point at the script directly. Leave the HTTP registration removal sentence as-is.

Do not edit `plugins/yakka/bin/yakka`, SessionStart hooks, or Phase 3 surfaces.

### Keep untouched

JSON/TOML structure besides `command` and `args`. Do not add env vars to MCP configs unless an example already documents them. Do not edit `yakka.py` or tests (2-01).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg 'bin/yakka.*mcp|bin/yakka",\s*\["mcp"\]' plugins/yakka/.mcp.json plugins/yakka/.codex-mcp.json packages/hooklog/cursor-mcp.example.json packages/hooklog/codex-mcp.example.toml docs/design/04-advisory-surface.md` → no matches (or only historical mention you intentionally removed).
- `rg 'client/yakka.py.*mcp|yakka.py", "mcp"' plugins/yakka/.mcp.json plugins/yakka/.codex-mcp.json packages/hooklog/cursor-mcp.example.json packages/hooklog/codex-mcp.example.toml docs/design/04-advisory-surface.md` → each owned file names the Python `mcp` command.
- `python3 -m json.tool plugins/yakka/.mcp.json` and `python3 -m json.tool packages/hooklog/cursor-mcp.example.json` → exit 0.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
