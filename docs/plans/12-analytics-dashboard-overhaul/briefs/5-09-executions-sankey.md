# Brief: 5-09 — Executions sankey and link filter

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/executions/+page.svelte`, `packages/workflow-analytics/tests/e2e/executions.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-09-executions-sankey.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-03.
Runs alongside: 5-07, 5-08, 5-10, 5-14, 5-15, 5-16. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 6 files to read, about 150 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Executions: design → brief → commit → report sankey plus table" and the Phase 5 outcome ("clicking a link filters its table").
2. `src/routes/executions/+page.svelte` and `tests/e2e/executions.spec.ts` — test ids `exec-count-*`, `exec-row`, `exec-repo`, `exec-plan`, `exec-harness`, `exec-conversation`; `src/lib/components/Pager.svelte` (read only; do not edit).
3. `src/lib/charts/sankey.ts` and `SankeyChart.svelte` (5-03) — the settled props.
4. `src/lib/view.svelte.ts` — `paramsFor`, `setParam`.
5. `tests/e2e/fixture.ts` — `EXECUTION_COUNTS`, `EXECUTION_ROWS`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Executions shows a design → brief → commit → report sankey above its table, and clicking a link narrows the table to the executions that took that path.

## Contract

What the data supports, and the decision taken (report it as a deviation note, do not hide it): `/executions` returns `counts` per `shape` (`complete` = brief, commit and report; `unreported` = brief and commit, no report; `started` = brief, no commit) and rows that begin at a brief. There is no per-row design reference, so the first link is the whole set.

Nodes: `design`, `brief`, `commit`, `report`, `no commit`, `no report`. Links (value from `counts`):
- `design` → `brief`: `complete + unreported + started`
- `brief` → `commit`: `complete + unreported`
- `brief` → `no commit`: `started`
- `commit` → `report`: `complete`
- `commit` → `no report`: `unreported`

Each link maps to a shape set: design→brief clears the filter; brief→commit = {complete, unreported}; brief→no commit = {started}; commit→report = {complete}; commit→no report = {unreported}. The selection is the page-local URL param `shape` (comma-separated, via `view.setParam`; other params and filters kept), and a link click toggles it. The table shows only rows whose `shape` is in the set, client side (counts tiles stay the unfiltered `counts`). Clicking the same link again clears it.

Test ids (5-17 may use): chart `exec-sankey`; because clicking an SVG link in Playwright is geometry-dependent, also render under the chart a plain button per link, `exec-link-<source>-<target>` (for example `exec-link-brief-commit`), which calls the same handler as a chart click (also the keyboard path); active links have `aria-pressed="true"`.

## Changes

Keep the first-page request, `Pager` wiring and `exec-*` ids as they are. The sankey uses only `counts` from the response already loaded, so there is no extra request. When all counts are zero show "No executions in this window" and no chart. When a filter is active and the table has loaded more pages, the client filter applies to all loaded rows.

Update `executions.spec.ts`: sankey present; `exec-link-brief-no commit`-style ids are spaces-free, so name nodes with ids `design`, `brief`, `commit`, `report`, `nocommit`, `noreport` and labels with spaces; clicking `exec-link-commit-report` leaves exactly the `complete` row (`EXECUTION_ROWS`), clicking again restores three rows; the URL carries `shape=complete`; a reload keeps it; a real click on the chart's link (geometry from the bounding box) is optional and must not be the only coverage.

### Keep untouched

`exec-count-*`, `exec-row` and drill-down cell behaviour from 4-12.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- executions.spec.ts` → the new tests fail before and pass after; the 4-12 tests still pass.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
