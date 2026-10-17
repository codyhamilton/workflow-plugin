# Brief: 5-04 — npm runtime packages

Consumer: a phase 5 worker running after `5-01`.
Owned paths:
`packages/yakka-analytics/**`,
`packages/opencode-yakka-hooks/**`,
`docs/plans/13-monorepo-restructure/reports/5-04-npm-runtime-packages.md` (new).
Touch nothing else. Do not edit `packages/yakka/` Go sources (`5-02` / `5-05`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-04-npm-runtime-packages.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `5-01`.
Runs alongside: `5-02`, `5-06`.
Budget: 40 files to read, about 200 lines to change, 75 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Names (npm scopes `@codyhamilton/yakka-analytics`, `@codyhamilton/opencode-yakka-hooks`, export names, `localStorage` keys `yakka-analytics-*`, signal-log default with `YAKKA_JEV_SIGNAL_LOG`), Assumption 11 (state path under `yakka`), Phase 5 outcome [test] (analytics e2e catalogue path).
2. `packages/yakka-analytics/package.json`, `src/lib/api.ts`, `src/lib/views.ts`, `src/lib/charts/theme.ts`.
3. `packages/opencode-yakka-hooks/package.json`, `src/index.ts`, `python/batch_flush_cli.py`, `tests/test_batch.py`.
4. `packages/yakka-analytics/tests/e2e/global-setup.ts` and `tests/hosted/global-setup.ts` — `WORKFLOW_CHECKS_DIR` and `go build` cwd.

## Goal

The two shipped npm packages carry the `yakka` names, analytics storage keys, and OpenCode runtime env defaults aligned with the Go binary, without pointing at old `workflow` identifiers in runtime code.

## Contract

Cited, binding: "npm: `@codyhamilton/yakka-analytics` … and `@codyhamilton/opencode-yakka-hooks` (export `yakka-signals.json`, plugin export `YakkaSignalsPlugin`). Analytics `localStorage` keys become `yakka-analytics-base`, `yakka-analytics-key` and `yakka-analytics-views:*`."

Cited, binding: "`WORKFLOW_*` becomes `YAKKA_*`" in shipped runtime code. OpenCode signal log: "`${XDG_STATE_HOME:-~/.local/state}/yakka/jev-signal-log.jsonl`, overridable by `YAKKA_JEV_SIGNAL_LOG`."

Cited, binding (Packages): test and e2e config may reference paths; update `WORKFLOW_CHECKS_DIR` → `YAKKA_CHECKS_DIR` and catalogue path `packages/yakka/catalogue` in analytics setups.

## Changes

- Rename `package.json` `name` fields and any public export paths (`opencode.json.example`, README consumers) to the yakka names above.
- Rename TypeScript/Python runtime env reads from `WORKFLOW_*` to `YAKKA_*` and default queue/binary paths to `yakka` (match `5-02` / hooklog).
- Rename all `workflow-analytics-*` `localStorage` keys to `yakka-analytics-*` in source and tests (including theme key if present).
- Point e2e/hosted global setup at `packages/yakka` and `packages/yakka/catalogue` with `YAKKA_CHECKS_DIR`.
- Update `packages/opencode-yakka-hooks` default signal-log resolution to the Assumption 11 path with `yakka` and `YAKKA_JEV_SIGNAL_LOG`.

### Keep untouched

`docs/design/*.md` (Phase 7). `tools/driver` (Phase 6) except if a test in this package imports it — prefer local test doubles. Embedded site output under `packages/yakka/internal/serve/site/`.

## Done evidence

- `node --test packages/opencode-yakka-hooks/tests/test_hooks.mjs` on Node v22.23.3+ → pass (use `--experimental-strip-types` only if the brief from phase 2 still requires it on older Node).
- `python3 -m unittest packages/opencode-yakka-hooks/tests/test_batch.py` → pass.
- `grep -r 'WORKFLOW_' packages/yakka-analytics/src packages/opencode-yakka-hooks/src packages/opencode-yakka-hooks/python` → no hits (except Markdown comments if any).
- `grep -r 'workflow-analytics-' packages/yakka-analytics/src` → no hits.

## Report back

Under 1,500 tokens. Status, test commands and output, deviations. Note if analytics e2e was not run (orchestrator may run at phase close).
