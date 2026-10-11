# Brief: 5-17 — Phase 5 end-to-end proof and 1 s timing

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: new `packages/workflow-analytics/tests/e2e/phase5.spec.ts`; append-only additions to `packages/workflow-analytics/tests/e2e/fixture.ts` (new exported constants and facts only; do not change an existing constant or fact) and to `tests/e2e/helpers.ts` (new helpers only). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-17-phase-5-e2e.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 5-04, 5-05, 5-06, 5-07, 5-08, 5-09, 5-10, 5-11, 5-14, 5-15, 5-16, 5-18, 5-19 (5-12 and 5-13 are Go only and need not finish first).
Runs alongside: nothing. The e2e suite binds a fixed port and builds once per run: if another worker runs at the same time, use your own `E2E_PORT` (for example `E2E_PORT=45NN`), ideally in a separate git worktree with its own `node_modules`; never run two `vite build`s in one tree.
Budget: 8 files to read, about 250 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — the Phase 5 outcome, all five bullets, and "Chart builder", "Saved views and dashboards".
2. `docs/plans/12-analytics-dashboard-overhaul/briefs/5-02-builder-spec.md`, `5-06-shell-saved-views-embed-notices.md`, `5-07-builder-route.md`, `5-08-dashboards-route.md`, `5-09-executions-sankey.md` — the test ids and URL params (`m`, `d`, `b`, `c`, `top`) are the contract you assert against.
3. `tests/e2e/builder.spec.ts`, `dashboards.spec.ts`, `executions.spec.ts` (from 5-07, 5-08, 5-09) — what is already covered; do not repeat, compose.
4. `tests/e2e/helpers.ts` (`useServe`, `expectSettled`, `trackRequests`) and `tests/e2e/fixture.ts` (`USAGE_*`, models, harnesses).
5. `tests/e2e/interactions.spec.ts` — the 4-16 style of cross-route spec and its timing assertion.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One spec that proves Phase 5's outcome end to end on the fixture served locally, and fails if any step regresses.

## Contract

The Phase 5 outcome (DESIGN.md): "In the builder, `cost_usd` × `model` × `harness` with a `day` bucket renders small multiples. Switching to `heatmap` with `hour_of_day` × `weekday` renders a heatmap. … A view saved under a name and added to a new dashboard survives a reload. Exporting the dashboard JSON and importing it into a fresh browser profile reproduces it. Executions shows the … sankey, and clicking a link filters its table. No unsupported pairing can be selected. Playwright covers builder, save, dashboard, export and import." Interaction timing: "Every interaction renders within 1 s, as measured by a Playwright timing assertion from input to settled chart."

Pin the browser zone (`test.use({ timezoneId: 'UTC' })`) as `interactions.spec.ts` does.

## Changes

Tests in `phase5.spec.ts` (each independent, `useServe(page, 'local')`):
1. Small multiples: open `/builder`, choose `cost_usd`, `model`, `harness`, bucket `day` through the selects; `builder-chart` has `data-kind="multiples"` and the panel count equals the number of distinct harnesses with priced or unpriced calls in the fixture (derive it from a `/v1/analytics/query?measure=cost_usd&dim=harness` request in the test, not a literal). If the fixture has fewer than two harnesses with usage, append fixture usage facts for a second harness (append-only, new constants), and recount.
2. Heatmap: change `builder-chart-type` to `heatmap` after setting dims `hour_of_day`, `weekday` with bucket `none`; `data-kind="heatmap"`; its table has cells summing to the `hook_events` total or the chosen measure's total from the API.
3. No unsupported pairing selectable: for every measure in `/v1/analytics/schema`, select it and assert the options of `builder-dim-1` and `-2` equal the measure's `dims` from the schema (a loop; it is cheap) and `builder-chart-type` options equal the table in 5-02 for the current dims and bucket.
4. Save and dashboard: save the builder view as `Cost split` (`saveview-*`), create dashboard `Ops` and add it (`dash-*`), reload, still there with its tile; the tile iframe shows `builder-chart`.
5. Export and import: export `Ops` (download), parse, `browser.newContext()` (a fresh profile), open `/dashboards`, import the file, the dashboard `Ops` and its tile are there and the tile renders.
6. Sankey: on `/executions`, `exec-link-commit-report` leaves only `complete` rows; again restores.
7. Timing: with the 1 s assertion style of `interactions.spec.ts`, measure from the input (click) to `expectSettled` for: builder chart-type change, builder measure change, dashboard create-and-add, executions link click, and a preset change on `/builder`; each under 1,000 ms (fixture; a warm-up request first). Record each measured time in the test output (`console.log`) so the orchestrator can compare it to the large-ledger run.

### Keep untouched

Existing fixture constants and facts, and the other spec files.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm run test:e2e -- phase5.spec.ts` → passes after the earlier units; before them it fails at the first missing route. Run it three times and report all three timing lists.
- `npm run test:e2e` (the whole suite) → passes, count reported.
- `npm test` and `npm run build` → pass.
- The timing assertion holds on the fixture only. The large-ledger figures are measured by the orchestrator against `/var/tmp/p4verify/data/local`; say so in your report.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
