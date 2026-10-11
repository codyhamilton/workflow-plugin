# Brief: 4-12 — Executions: shared client, drill-down cells and conversation links

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/executions/+page.svelte`, `tests/e2e/executions.spec.ts`. Touch nothing else (do not edit `Pager.svelte`; it keeps its props).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-12-executions.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06 to 4-11, 4-13 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4412`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 6 files to read, about 150 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": Executions, drill-down rules. The sankey is Phase 5: do not build it.
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01) — exports only.
3. `src/routes/executions/+page.svelte` and `tests/e2e/executions.spec.ts` — test ids `exec-count-*`, `exec-row`; `src/lib/components/Pager.svelte` (read-only).
4. `tests/e2e/fixture.ts` — `EXECUTION_COUNTS`, `EXECUTION_ROWS`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Executions fetches through the shared client and every repo, plan, harness and conversation cell is a drill-down.

## Contract

- `executions` is a `rest` route (400 `"range too wide"` beyond 400 days; the shell clamps and notifies). It is keyset-paged: the first page goes through `getJSON('executions', 'analytics/executions', view.paramsFor('rest', {limit}))`; `Pager` fetches later pages with the cursor and drops responses after a filter change. Do not change `Pager`.
- Cell clicks: `repo_id`, `plan`, `harness` cells call `view.drill(key, value, ev)` (shift excludes). The conversation id is a link to `/conversation?id=<id>` (the timeline route, 4-14); it keeps no filters.
- No chart is added in this phase. Keep the count tiles `exec-count-<shape>` and rows `exec-row`.

## Changes

Rewrite `+page.svelte` on `view` and the client; slot `executions`. Update `executions.spec.ts`: the counts and rows equal `EXECUTION_COUNTS` and `EXECUTION_ROWS` (c5 has no brief, so they are unchanged unless 4-03 moved them; recount, never edit to match); a repo cell click adds a `repo_id` chip and the rows narrow; shift-click adds an exclude chip; the conversation link navigates to `/conversation?id=c3`; the `limit` param and "Load more" still work; the 1 s timing assertion.

### Keep untouched

`exec-count-*`, `exec-row`, and the paging behaviour.

## Done evidence

Run the old `executions.spec.ts` against the new page first and report which tests fail before you change it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- executions.spec.ts` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
