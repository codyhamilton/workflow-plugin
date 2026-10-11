# Report: 5-07 — Chart builder route

Status: **done**

## What changed (against each part of the brief)

- `packages/workflow-analytics/src/routes/builder/+page.svelte` (new). Loads the schema once with `getJSON('builder-schema', 'analytics/schema', new URLSearchParams())` and builds every control from it. Test ids: `builder-measure`, `builder-dim-1`, `builder-dim-2`, `builder-bucket`, `builder-chart-type`, `builder-top`, the `builder-chart` `testid` on `BuilderChart`, and `builder-notice-range`.
  - **URL is the view.** Config read with `parseConfig`, or `defaultConfig(schema)` when the URL has no `m`; written back with one `goto` per change (a local `navigateConfig` modelled on `view.setParam`) that keeps filter and route params. An explicit `b` (including `b=none`) wins; with no `b`, `pickBucket` picks the finest in-range bucket.
  - **Pairing guard.** `builder-dim-1`/`-2` list `allowedDims(schema, measure, other)` plus `none`; `builder-chart-type` lists `allowedCharts(dims.length, bucket)`; changing the measure drops dims it does not support and re-defaults the chart to the first kind the new shape offers, so an unsupported pairing is never offered.
  - **One request.** `view.paramsFor('query', {measure, dim, bucket, top})` through `getJSON('builder-query', 'analytics/query', params)`. All time uses `all=1` only with `bucket=none`; a time bucket replaces `all` with the rest 399-day `from`/`to`. When `isRangeOk` (via `pickBucket`) says the bucket exceeds the cap, no request goes out and `builder-notice-range` shows.
  - Mark click calls `view.drill(dim, key, {shift})` only when `dim` is in `DIM_KEYS` (`hour_of_day`, `weekday`, `stage` do nothing); brush calls `view.setWindow`. Slots, `Superseded`, `facetsReady` (with `untrack`) and `setError`/`clearError` mirror Trends.
- `packages/workflow-analytics/tests/e2e/builder.spec.ts` (new): the five specified cases, all against the fixture ledger.

## Check output

Before (route missing), `E2E_PORT=4507 npm run test:e2e -- builder.spec.ts`:

```
5 failed
 tests/e2e/builder.spec.ts:19 › opens with a default chart and no console error
 ... (all five) ...
 Error: expect(locator).toHaveValue(...) / element(s) not found
```

After, same command:

```
5 passed (14.1s)
```

`npm test` (all suites):

```
Test Files  15 passed (15)
     Tests  148 passed (148)
```

`npm run build`:

```
✓ built in 6.67s
Wrote site to "build"
✔ done
```

## Deviations

1. **`b=none` written explicitly.** `configToParams` omits `b=none` and `parseConfig` maps an absent `b` to `none`; the brief needs absence to mean "pick". A local navigator writes every config param, setting `b=none` when the bucket is `none`, so a chosen `none` survives a reload.
2. **A pairing change re-defaults the chart to `allowedCharts(...)[0]`.** Reason: DESIGN's outcome is two dims on a time bucket → small multiples; both `line` and `multiples` are allowed there, so preserving the previous `line` would not meet it.
3. **The chart renders only when `rangeOk`**; otherwise only `builder-notice-range` shows.
4. **`builder-dim-2` may be set before `builder-dim-1`** (it then becomes the first dim). Unspecified; the specs set dim-1 first.
5. **Test 2 waits on `builder-chart-panel` rather than `expectSettled`** (see Known problems).

## Contradictions

1. `builder.ts` / `configToParams` treat absent `b` and `b=none` as the same `none`, while the brief says a new window with no explicit `b` uses `pickBucket`. Resolved by distinguishing the URL's literal `b` presence (Deviation 1); named here, not resolved silently.
2. DESIGN's "finest bucket within the cap unless one is set" vs. the select listing every schema bucket: the chosen bucket is honoured, but an out-of-cap time bucket is not requested and the notice is shown, per the brief's explicit rule.

## Unfinished

None.

## Known problems

- `SmallMultiples` (`packages/workflow-analytics/src/lib/charts/SmallMultiples.svelte`) renders `EChart` without a `data-ready` element, unlike TimeChart/Heatmap/GroupedBar, so `expectSettled` cannot observe a settled multiples chart; test 2 waits on a panel instead. Not fixed (outside this unit's owned paths).
