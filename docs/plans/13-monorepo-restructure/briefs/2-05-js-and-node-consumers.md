# Brief: 2-05 — JavaScript and Node test consumers

Consumer: a phase 2 worker running after `2-01`.
Owned paths:
`packages/workflow-analytics/tests/**`,
`packages/opencode-workflow-hooks/{src/index.ts,tests/test_hooks.mjs,README.md}`,
`docs/plans/13-monorepo-restructure/reports/2-05-js-and-node-consumers.md` (new).
Touch nothing else. Signal-log default change is Phase 4 (Assumption 11).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-05-js-and-node-consumers.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`).
Depends on: `2-01`.
Runs alongside: `2-02`, `2-03`, `2-04`.
Budget: 20 files to read, about 80 lines to change, 50 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 2 surfaces (TypeScript and Node tests), Phase 2 [test] outcome for analytics e2e and `test_hooks.mjs`.
2. `packages/workflow-analytics/tests/e2e/global-setup.ts`, `tests/hosted/global-setup.ts` — `cwd` and `WORKFLOW_CHECKS_DIR`.
3. `packages/opencode-workflow-hooks/README.md` and comments in `src/index.ts` naming `tools/hooklog`.

## Goal

Analytics e2e/hosted setups build the Go binary from `packages/workflow` and point `WORKFLOW_CHECKS_DIR` at `packages/workflow/catalogue`; OpenCode package prose matches the moved hooklog path.

## Contract

Cited, binding: "Go tests and the analytics e2e and hosted setups load it from there" (`packages/workflow/catalogue/`). OpenCode package references hooklog queue semantics aligned with `packages/hooklog/spool.sh` (comments/README only in this unit).

## Changes

- Repoint `global-setup.ts` `go build` cwd to `packages/workflow/cmd/workflow` or `packages/workflow` consistent with existing pattern.
- Set `WORKFLOW_CHECKS_DIR` to `packages/workflow/catalogue` (absolute join from repo root).
- Update OpenCode README and source comments from `tools/hooklog` to `packages/hooklog` where they describe paths (not behaviour).
- Do not change runtime default for JEV signal log (Phase 4).

### Keep untouched

Svelte routes named `/quality`, test IDs, and hook policy equality test in `test_hooks.mjs` except path strings in comments if any.

## Done evidence

- `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` → pass.
- If Node/npm deps are installed: run analytics e2e per package README; if not installable in the VM, report `needs context` with the exact command and repoint diff only, and leave e2e for orchestrator. When runnable: e2e suite passes.
- `rg 'tools/workflow|tools/hooklog|tools/quality' packages/workflow-analytics/tests packages/opencode-workflow-hooks` → no hits.

## Report back

Under 1,500 tokens. Status, commands run, deviations.

## Amendment

Bare `node --test` needs Node 22.18 or newer. On older Node the package command is `node --experimental-strip-types --test`. Analytics e2e stays with the orchestrator when `node_modules` is absent; the repoint itself is this unit.
