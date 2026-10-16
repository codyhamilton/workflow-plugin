# Execution report: 4-01 — Quality score drift bands

**Status:** done

## What changed

- **`types.ts`**: `ScoreSeriesPoint`, `ScoreSeriesCheck`, `ScoreSeries` response types.
- **`params.ts`**: `scoreSeriesParams` (kind + bucket on rest window params).
- **`score-series.ts` / `ScoreBandChart.svelte`**: ECharts median line, stacked p25–p75 band, optional baseline `markLine`, brush → `view.setWindow`; table rows use empty cells for missing buckets (not zero).
- **`quality/+page.svelte`**: Fetches score-series with scores/baselines; bucket control (`day`|`week`|`month`, `pickBucket` cap logic); one band chart per check with points; box plot + table unchanged.
- **`quality.spec.ts`**: Stubs score-series on existing tests; new gap, brush, and kind-refetch tests.

## Done evidence

**Before** (`npm test -- src/lib/charts/score-series.test.ts`):

```
No test files found, exiting with code 1
```

**After:**

```
✓ src/lib/charts/score-series.test.ts (5 tests)
```

**Before:** score-series e2e cases did not exist.

**After** (`export E2E_PORT=4411 && npx playwright test tests/e2e/quality.spec.ts`):

```
11 passed
```

## Departures

- **`quality.spec.ts`**: Added `test.use({ timezoneId: 'UTC' })` so bucket `t` keys match stubbed RFC3339 points (same pattern as `trends.spec.ts` / `usage.spec.ts`). Not named in the brief; avoids locale-dependent failures.
- **Kind-refetch e2e**: Uses `waitForRequest` after tab click because the client cache/debounce can settle before `trackRequests` observes the brief fetch; still asserts exactly one post-click score-series URL with `kind=brief`.

## Contradictions

None between this brief and cited DESIGN / API contracts.

## Known problems (outside done evidence)

None observed.
