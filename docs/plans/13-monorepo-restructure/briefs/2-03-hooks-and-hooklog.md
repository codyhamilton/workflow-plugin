# Brief: 2-03 — Hook configs and hooklog package

Consumer: a phase 2 worker running after `2-01`.
Owned paths:
`hooks/**`,
`packages/hooklog/**`,
`docs/plans/13-monorepo-restructure/reports/2-03-hooks-and-hooklog.md` (new).
Touch nothing else. Do not change Cursor command shape beyond repointing off `tools/hooklog` (Phase 3 owns `./script/...`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-03-hooks-and-hooklog.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`).
Depends on: `2-01`.
Runs alongside: `2-02`, `2-04`, `2-05`.
Budget: 30 files to read, about 200 lines to change, 70 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 2 surfaces (Hook configs), Phase 3 note on `hooks/cursor.json` (repoint only far enough off `tools/hooklog`).
2. `hooks/hooks.json`, `hooks/codex.json`, `hooks/cursor.json` — spool command paths.
3. `packages/hooklog/README.md` and example configs (`cursor-hooks.example.json`, `codex-mcp.example.toml`, etc.).
4. `packages/hooklog/tests/test_surfaces.py`, `test_write_surfaces.py`, `test_spool_queue.py` — hard-coded `tools/hooklog` paths.

## Goal

Every harness hook config and hooklog test resolves `packages/hooklog/spool.sh` (or equivalent) instead of `tools/hooklog`.

## Contract

Cited, binding (Phase 2): "`hooks/{hooks,codex}.json` repoint at `packages/hooklog`. `hooks/cursor.json` is repointed only far enough that it no longer names `tools/hooklog`; Phase 3 replaces its commands." "`packages/hooklog/{cursor-hooks.example.json,cursor-mcp.example.json,codex-mcp.example.toml,README.md}`."

Cited, binding (Plugin, Claude/Codex hook shape until phase 3): commands stay `bash "<root>/...spool.sh" --harness <h> [--event <E>]`, with `<root>` still the repo plugin root today (repo root, not yet `plugins/yakka`).

## Changes

- Replace `tools/hooklog` with `packages/hooklog` in owned hook JSON and hooklog docs/examples.
- Fix `sys.path`, `parents[N]`, and fixture copy paths in `packages/hooklog/tests/` (including spool integration tests that mkdir `tools/hooklog`).
- Keep event names, harness flags, and `${CLAUDE_PLUGIN_ROOT}` / `${CURSOR_PLUGIN_ROOT}` / `${PLUGIN_ROOT}` variable usage as today except the path segment after the root.
- Do not introduce `./script/...` in `hooks/cursor.json` (Phase 3).

### Keep untouched

`hooklog.py` scrub semantics, queue file naming, and spool.sh CLI flags.

## Done evidence

- `python3 -m unittest discover -s packages/hooklog/tests -v` → OK.
- `rg 'tools/hooklog' hooks packages/hooklog` → no hits (live prose in `docs/plans/` excluded by scope; you do not edit those).

## Report back

Under 1,500 tokens. Status, test output, deviations.
