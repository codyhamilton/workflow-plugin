# Brief: 4-16 — Retire LayerChart and the old filter model; prove the cross-route interactions

Consumer: a TypeScript worker (flash-tier). This is the last unit of Phase 4; it writes tests, not a verification report.
Owned paths: `packages/workflow-analytics/package.json`, `package-lock.json`, `src/lib/filters.ts`, `src/lib/filters.test.ts`, `src/lib/charts/Bars.svelte`, `src/lib/charts/LineSeries.svelte`, `src/lib/charts/palette.ts`, `src/lib/series.ts`, `src/lib/series.test.ts` (only if nothing imports them any more), `tests/e2e/interactions.spec.ts` (new), `tests/e2e/helpers.ts` (amended: fix `clickBar`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-16-retire-layerchart-interactions.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-06, 4-07, 4-08, 4-09, 4-10, 4-11, 4-12, 4-13, 4-14, 4-15.
Runs alongside: nothing.
Budget: 8 files to read, about 200 lines to write, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 4 outcome list, every bullet.
2. `tests/e2e/helpers.ts` and `fixture.ts` (4-03) — `trackRequests`, `clickBar`, `brush`, `expectSettled`, constants.
3. The reports `docs/plans/12-analytics-dashboard-overhaul/reports/4-0[5-9]-*.md` and `4-1[0-5]-*.md` — what the route units left open.
4. `grep -rn "layerchart\|\$lib/filters\|\$lib/series\|charts/Bars\|charts/LineSeries\|charts/palette" packages/workflow-analytics/src packages/workflow-analytics/tests` — what still imports the old code.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The old chart stack and filter model are gone, and the Phase 4 outcome bullets that span routes are each asserted by a test.

## Contract

DESIGN.md Phase 4 outcome: "Every design 7 report renders with ECharts in light and dark themes, each with a data-table toggle, and `layerchart` is gone from `package.json`." Perspective stays (Explore only). The `/settings` behaviour, the non-JSON error, `scripts/check-bundle.mjs` and the static build output are unchanged.

## Changes

1. Remove every remaining import of `layerchart` and of the old modules found by the grep (a leftover is a route unit's miss: fix it only inside your owned paths, otherwise report which file and which unit). Then `npm uninstall layerchart` and delete the files nothing imports (`Bars.svelte`, `LineSeries.svelte`, `palette.ts`, and `filters.ts`, `series.ts` with their tests if unused). Keep any file that is still imported.
2. `interactions.spec.ts` (local serve, recounted fixture), one test per bullet, each using helpers from 4-03:
   - choose `7d` on Overview, click the Hooks nav link: the URL has `range=7d` and `preset-7d` is pressed;
   - `brush(page, 'trends-chart', 0.25, 0.75)` on `/trends` narrows the window (`from` and `to` in the URL, `range` absent, the table toggle shows fewer buckets);
   - on `/hooks`, `clickBar(page, 'hooks-harness', 0)` adds a `chip-harness-*` with `data-mode="include"`, and with `{shift: true}` `data-mode="exclude"`;
   - on `/conversations`, clicking the `c5` link opens `/conversation?id=c5` whose totals equal `USAGE_C5`;
   - `/usage` shows cost by model, and no element on a window with only unpriced calls contains `$0`;
   - interaction timing: for a preset click, a harness drill and a brush, the time from the input to `expectSettled` is under 1,000 ms (`performance.now()` in the test);
   - burst: five preset clicks inside 250 ms leave one `analytics/query` request per slot on `/trends` (`trackRequests`), and `/repos` issues four `analytics/query` requests with two repos and four with forty (a `page.route` that invents the rows);
   - every chart on every route has `data-ready="true"` in light and dark (`page.emulateMedia({colorScheme})`), and each chart's `-table-toggle` switches to a `-table` with at least one row (iterate `[data-testid$="-table-toggle"]` on `/`, `/trends`, `/usage`, `/repos`, `/hooks`).
3. Keep the full existing e2e suite passing.

### Keep untouched

Perspective packages in `package.json`; `scripts/check-bundle.mjs`.

## Done evidence

- `grep -n layerchart packages/workflow-analytics/package.json packages/workflow-analytics/package-lock.json` → no output.
- `npm test`, `npm run build` → pass.
- `npm run test:e2e` → every spec passes, including `interactions.spec.ts`; report the pass count.
- `npm run check:bundle` passes through the e2e build (no key or token in `build/`).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.

## Amendment (from the 4-10 report)

`helpers.ts` `clickBar` cannot click a `BarChart`: it toggles to the table to count rows and leaves the table showing, but `BarChart` renders the table and the chart as alternatives, so the geometry click lands on nothing. Fix it first, inside `tests/e2e/helpers.ts`, by copying the working `clickHarnessBar` in `tests/e2e/hooks.spec.ts` (read the row count from the table, toggle back to the chart, wait for `.echart svg`, then click the band centre). Bar and table order is key-ascending, so harness index 0 is `claude`. Keep the existing `clickBar` signature. Then use it in the `/hooks` interaction test as written above.
