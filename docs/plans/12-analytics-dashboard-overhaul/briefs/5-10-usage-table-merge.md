# Brief: 5-10 — Usage table: one consistent key set

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/usage/+page.svelte`, `packages/workflow-analytics/tests/e2e/usage.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-10-usage-table-merge.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-07, 5-08, 5-09, 5-14, 5-15, 5-16 (and every wave-1 unit). The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 5 files to read, about 120 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — "Phase 4 verification" (Usage table) and "Carried (Phase 4)" item 2.
2. `src/routes/usage/+page.svelte` — the five by-model queries, `models`, `totalCalls`, `totalUnpriced`, `costRows`, `pick`, `cost()`.
3. `tests/e2e/usage.spec.ts` and `tests/e2e/fixture.ts` (`USAGE_ALL`, `USAGE_BY_MODEL`, `USAGE_C5`).
4. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "`GET /v1/analytics/query`" (`top` ranks each measure's keys independently; `__other__`).
5. `src/lib/format.ts` — `costLabel`, `label` (read only; 5-14 owns it).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The Usage table shows every model with calls, tokens, cost and unpriced counts from one consistent set of model keys, so no row reads `calls 0` beside tokens, `__other__` is never `$0.00`, and an empty model reads `(none)`.

## Contract

Root cause (Phase 4 verification): the page asks five measures with `top=20`; `top` ranks keys per measure, so each response holds a different set of 20 and the merge by key leaves holes and an `__other__` row that mixes different folds. `/query` takes one measure per request, so "one /query over the page's measures" is realised as the same key set for every measure: send `top=100` (the API maximum) on all five by-model requests so each returns every model key, then merge. A key missing from one response means that measure was zero or not applicable, shown as `—`, never `0` for calls.

The by-model chart for cost and the time-series requests keep `top=20`.

## Changes

- Table queries (`usage-by-model-*` slots): `top: '100'`. Everything else on the page unchanged.
- If a response still contains `__other__` (more than 100 models), label that row "other models", make it inert (no drill), show its cost with `costLabel` using the same row's unpriced and calls, never `$0.00`, and add a visible note that the table is truncated to 100 models.
- Empty model key renders `(none)` via `label`; it is a valid drill key only if the API accepts an empty `model` filter, which it does not, so a `(none)` row is inert too.
- The banner totals (`totalCalls`, `totalUnpriced`) sum rows from the same key set, so "unpriced of calls" is consistent.
- Add `usage.spec.ts` tests on the fixture: every table row's calls equals `USAGE_BY_MODEL` for that model and no row has calls 0 with tokens > 0; a model with no cost data shows `unpriced`, never `$0.00`. Then assert in a Playwright `page.route` interception that the five table requests carry `top=100` (the fixture has too few models to show the original defect, so the request-parameter assertion is the regression guard; say so in your report).

### Keep untouched

The cost-over-time and tokens-over-time charts, `pick` guards for unpriced bars, and existing test ids.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- usage.spec.ts` → the new tests fail before (table requests carry `top=20`) and pass after.
- `npm test` and `npm run build` → pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
