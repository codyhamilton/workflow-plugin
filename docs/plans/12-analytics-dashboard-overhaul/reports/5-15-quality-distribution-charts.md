# 5-15 — Quality: distribution charts beside the baseline

Status: **done**

## What changed

- `packages/workflow-analytics/src/routes/quality/+page.svelte`: added a derived `distRows`
  (`BoxRow[]`) from `scores.checks` filtered to `n > 0`, carrying `min/p25/median/p75/max` and
  `marker = baselines.checks[name].median` when present. Rendered `<BoxChart testid="quality-dist"
  rows={distRows} />` above the existing table, inside the same `{#if scores}` guard. The kind
  selector, table markup, `scoresParams` use, request set and error handling are untouched.
- `packages/workflow-analytics/tests/e2e/quality.spec.ts`: added a `stubQuality` helper and three
  tests — `quality-dist` renders with one table row per scored check (and the baseline median as the
  marker, blank when absent; an `n = 0` check has no row), the chart re-renders on kind switch, and
  it reports `data-theme="dark"` under `prefers-color-scheme: dark`. Existing tests unchanged.
- `docs/plans/12-analytics-dashboard-overhaul/reports/5-15-quality-distribution-charts.md` (this file).

No new request; the chart reuses the two GETs the page already makes.

## Done evidence

Failing check written first, then run before the page change, then after:

- Before (`E2E_PORT=4515 npm run test:e2e -- quality.spec.ts`): **3 failed, 5 passed (56.5s)**. All
  three new tests failed with `quality-dist` not found (`toBeVisible`, `table-toggle` click timeout,
  `data-ready` not found).
- After the same command: **8 passed (17.6s)**. The three new tests pass; the five pre-existing
  tests still pass.
- `npm test` → 148 passed (15 files).
- `npm run build` → built (`adapter-static`, wrote `build`).

The stub numbers are hand-set in the spec (alpha `n=11`, gamma `n=7`, unscored `n=0`; baseline alpha
median `0.35`); the test asserts the table's `data-value` cells against those numbers, not the code.

## Departures from the brief

- None. The chart is added above the table, both show; `n = 0` checks are omitted; `marker` is the
  baseline median when present.

## Contradiction between this brief and the contracts it cites

- Required reading item 5 says `tests/e2e/fixture.ts` holds "the scores fixture". It does not:
  `fixture.ts` exports `FACTS` and summary/usage/execution/conversation expectations only, with no
  scores or baselines. The e2e serve runs with `TYPESAFE_API_KEY=''` (no scorer), so every quality
  window is `n = 0` and the "zero-scorer" test asserts all-zero rows. A chart of scored checks
  therefore cannot be exercised against the serve; the new tests stub `/v1/analytics/scores` and
  `/v1/baselines` with hand-counted rows, which is what "recount against the fixture" maps onto here.
  Reported, not silently resolved.
- This unit closes the 4-11 Carried-5 contradiction (brief said table only; `DESIGN.md` line 218 says
  "distribution charts beside the baseline"): the chart now exists beside the table.

## Unfinished / known problems

- None in this unit. The build warns that some chunks exceed 500 kB; pre-existing and out of scope.
