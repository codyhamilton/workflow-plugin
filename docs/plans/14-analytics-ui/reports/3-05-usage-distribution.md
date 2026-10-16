Status: done with concerns

## What changed

- **`types.ts`**: `DistributionBin`, `DistributionRow`, `DistributionResponse` for `/v1/analytics/distribution`.
- **`distribution.ts` / `DistributionChart.svelte`**: ECharts histogram from API `lo`/`hi`/`n`; cost vs token bin labels; table toggle.
- **`usage/+page.svelte`**: Six contract measures in a selector; `getJSON` slot `usage-distribution` via `view.paramsFor('rest', { measure, grain: 'call' })`; tokens time series `dim=model` stacked; both time charts `{#if …Resp}` mount, `filterDim="model"`, `onseries` → shared `pick`, `onbrush` → `view.setWindow`; `void view.state` so model drill refetches queries.
- **`usage.spec.ts`**: UTC timezone; load asserts 7 query + 1 distribution; new tests for measure switch, `dim=model`, brush + distribution refetch, model bar filter; brush uses table-toggle preamble (same as `interactions.spec.ts` trends pattern).

## Done evidence

**Before** (`npm test -- src/lib/charts/distribution.test.ts`):

```
No test files found, exiting with code 1
```

**After**:

```
✓ src/lib/charts/distribution.test.ts (4 tests)
Test Files  1 passed (1)
```

**Before** (new e2e cases): not present.

**After** (`export E2E_PORT=4397 && npx playwright test tests/e2e/usage.spec.ts`): **15 passed, 3 failed** — failures are pre-existing opus/unpriced expectations (below). New 3-05 tests (distribution measure, tokens `dim=model`, brush, model bar chip, query+distribution counts) pass.

## Departures

- Brief mentions **seven** measures; DESIGN/`distributionMeasures` define **six** (`cost_usd` + five token columns). Selector lists all six.
- **`usage.spec.ts`**: added `test.use({ timezoneId: 'UTC' })` (matches `trends.spec.ts`) so time-bucket queries stay stable; not named in brief but keeps tokens-over-time assertions reliable.

## Contradictions

None between brief and cited DESIGN contracts.

## Problems outside scope (not fixed)

- **`claude-opus-5-5` cost display**: fixture comment and `USAGE_BY_MODEL` say the c1 Opus call is unpriced (`unpriced: 1`, cost `0`), but `pricing_table.json` now prices `claude-opus-5-5`, so `/usage` shows **`$0.13`** and three specs fail (`usage table…`, `harness=claude`, `never $0.00`). Root cause: e2e fixture counts vs store pricing table, not this unit’s UI code. Owned path `fixture.ts` was not in brief.

## Unfinished

None for this brief.
