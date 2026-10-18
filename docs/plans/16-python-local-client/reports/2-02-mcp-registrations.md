---
cursor:
  subagentId: "bc-c628a64b-7d6c-5006-b74f-9c91715b10b5"
---

# Unit 2-02 — MCP registrations and design 4

**Status:** done

## What changed

- `plugins/yakka/.mcp.json`: `command` → `python3`, `args` → `${CLAUDE_PLUGIN_ROOT}/client/yakka.py` + `mcp`.
- `plugins/yakka/.codex-mcp.json`: `command` → `python3`, `args` → `./client/yakka.py` + `mcp` (unchanged `cwd` `.`).
- `packages/hooklog/cursor-mcp.example.json`: `command` → `python3`, absolute script path in `args`.
- `packages/hooklog/codex-mcp.example.toml`: `command` → `python3`, absolute script path in `args`.
- `docs/design/04-advisory-surface.md`: **Shape** and **Registration** name `python3 plugins/yakka/client/yakka.py mcp`; Registration notes Phase 3 wrapper routing; HTTP removal sentence unchanged.

## Checks (before → after)

**`rg 'bin/yakka.*mcp|bin/yakka",\s*\["mcp"\]'` (owned paths)**

Before:

```
docs/design/04-advisory-surface.md:`plugins/yakka/bin/yakka mcp`. The HTTP registration of `127.0.0.1:8765/mcp` is removed.
```

(Four MCP configs still pointed at `bin/yakka` via `command`; that pattern does not match split `command`/`args` lines.)

After:

```
docs/design/04-advisory-surface.md:Phase 3 will also route `plugins/yakka/bin/yakka mcp` through that script; this phase's
```

(Intentional Phase 3 forward reference per brief; no config files match.)

**`rg 'client/yakka.py.*mcp|yakka.py", "mcp"'` (owned paths)**

Before: no matches.

After: all five owned files name the Python `mcp` command (see commit tree).

**`python3 -m json.tool`**

Before: not run (JSON unchanged structurally).

After: `plugins/yakka/.mcp.json` and `packages/hooklog/cursor-mcp.example.json` → exit 0.

## Departures

None.

## Contradictions

None between this brief and cited `DESIGN.md` Phase 2 outcome / Assumption 2.

## Problems

None found outside done evidence.
