# Brief: 5-03 — Plugin `bin/yakka` and hook edge

Consumer: a phase 5 worker running after `5-02`.
Owned paths:
`plugins/yakka/bin/**`,
`plugins/yakka/hooks/**`,
`plugins/yakka/script/**`,
`plugins/yakka/.mcp.json`,
`plugins/yakka/.codex-mcp.json`,
`packages/hooklog/**`,
`docs/plans/13-monorepo-restructure/reports/5-03-plugin-bin-and-hook-edge.md` (new).
Touch nothing else. Do not edit plugin manifest version fields or `skills/` (Phase 6).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-03-plugin-bin-and-hook-edge.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `5-02`.
Runs alongside: nothing.
Budget: 35 files to read, about 250 lines to change, 70 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Plugin (`bin/yakka` four-step resolution, cache key), Decision 3 (Claude/Codex binary path `plugins/yakka/bin/yakka`; Cursor stays `./script/...`), Domain: Names (cache and release asset names `yakka-<os>-<arch>`, `bin/VERSION` bump), Phase 5 outcome [cmd] (spool queue path, hook shape), Phase 4 Carried item 3 in `IMPLEMENTATION.md`.
2. `plugins/yakka/bin/workflow` — steps 3–4 paths and cache layout.
3. `plugins/yakka/hooks/cursor.json` (command shape only), `hooks/hooks.json` and `hooks/codex.json` (binary prefetch lines).
4. `plugins/yakka/script/prefetch-version.sh`, `packages/hooklog/spool.sh` (env vars and queue default).
5. `docs/plans/13-monorepo-restructure/IMPLEMENTATION.md` — Phase 4 Carried item 3 (step 4 must join `$ROOT/../../packages/yakka`, not `$ROOT/../packages/workflow`).

## Goal

The plugin install root ships `bin/yakka` with a working source-build path, harness hooks and MCP configs invoke `yakka`, hook capture defaults land under `~/.local/share/yakka/queue`, and Cursor commands remain `./script/...`.

## Contract

Cited, binding: "`bin/yakka` keeps the four-step resolution." "Cache, release assets and state directories use `yakka`." "`bin/VERSION` is bumped, so no tag serves both asset names."

Cited, binding (Decision 3): "Cursor hook commands stay `./script/...` through the rename. Claude and Codex commands change only the binary path, to `plugins/yakka/bin/yakka`."

Cited, binding (Phase 5 outcome): "Every Cursor hook command is still plugin-root-relative `./script/...`."

Cited, binding: `WORKFLOW_*` → `YAKKA_*` in shipped code (hooklog and scripts). Exception: `WORKFLOW_QUALITY_` does not apply here.

Cited, binding (IMPLEMENTATION Phase 4 Carried 3): step-4 source build must read `packages/yakka` at `$ROOT/../../packages/yakka/go.mod` when `ROOT` is `plugins/yakka`.

Settled: Phase 3 Carried item 1 (logged-in Cursor session) is not this unit. Do not run `agent login` or claim a live hook fire.

## Changes

- Rename `plugins/yakka/bin/workflow` → `plugins/yakka/bin/yakka`. Remove the `workflow` wrapper name.
- Fix module probe and build directory to `$ROOT/../../packages/yakka` and `./cmd/yakka`. Update cache dir to `.../yakka/$VERSION`, binary name `yakka-$OS-$ARCH`, `YAKKA_ROOT`, `YAKKA_BIN`, `YAKKA_RELEASE_URL`, and user-facing `yakka:` error prefixes.
- Bump `plugins/yakka/bin/VERSION` (and keep `SHA256SUMS` / `RELEASE_URL` consistent with asset naming expected in `5-05`).
- Update Claude/Codex hook JSON and `script/prefetch-version.sh` to call `bin/yakka`. Leave Cursor `cursor.json` commands as `./script/...` only.
- Update `.mcp.json` and `.codex-mcp.json` to run `bin/yakka` with server key `yakka` (not `workflow`).
- In `packages/hooklog` and copies under `plugins/yakka/script/`, rename env vars and default queue/hooklog paths to `YAKKA_*` and `~/.local/share/yakka/...` per the state-path table. Keep spool behaviour otherwise identical.
- Sync `plugins/yakka/script/spool.sh` from `packages/hooklog/spool.sh` if the package is the source of truth after edits.

### Keep untouched

Plugin manifest `name` fields (`workflow` until Phase 6). Skill bodies except paths owned by `5-06`. `tools/release/` (owned by `5-05`).

## Done evidence

- From cwd `plugins/yakka`, with empty `yakka` cache under a temp `HOME`, `WORKFLOW_RELEASE_URL` / `YAKKA_RELEASE_URL` pointed at an unreachable host, and Go on `PATH`: `./bin/yakka --version` → exit 0, stdout matches `^yakka [0-9.]+ [0-9a-f]{12}$`.
- `test -f ../../packages/yakka/go.mod` relative to `plugins/yakka` (the step-4 probe path) → exit 0.
- Every command in `plugins/yakka/hooks/cursor.json` still starts with `./script/`.
- `python3 -m unittest discover -s packages/hooklog/tests -p 'test_spool_queue.py' -v` → pass (update tests for `YAKKA_*` as needed).

## Report back

Under 1,500 tokens. Status, cold-build version output, cursor hook shape check, test output, deviations.
