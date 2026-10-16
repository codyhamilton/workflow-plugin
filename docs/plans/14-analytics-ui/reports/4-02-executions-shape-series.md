# Execution report: 4-02 — Executions shape filter and series

**Status:** done

## What changed

- **`types.ts`**: Extended `Executions` with optional `bucket` and `series` (three shape keys).
- **`executions/+page.svelte`**: Sends repeatable `shape` and `bucket` on `analytics/executions`; refetch keyed on full query string; table uses API `rows`; bucket control; stacked area `TimeChart` (`exec-shape-series`) with window zero-fill via `bucketStarts`/`instantKey`; brush → `view.setWindow`; sankey/link `shape` and tile `counts` unchanged.
- **`executions.spec.ts`**: UTC timezone; tests for API `shape`, reload/limit paging under `shape=complete`, series visibility, brush + refetch.

## Done evidence

**Before** (`export E2E_PORT=4414 && npx playwright test tests/e2e/executions.spec.ts`):

```
9 passed
```

**After:**

```
13 passed
```

## Departures

- **`executions.spec.ts`**: `test.use({ timezoneId: 'UTC' })` for stable bucket keys (same pattern as trends/usage/quality).
- **Brush e2e**: Drags on `.echart` at 75% height; shared `brush()` helper targets the chart wrapper and did not fire `brushEnd` on this stacked chart with legend.
- **Paging under `shape=complete`**: Fixture has one `complete` row, so `limit=1` walk is a single page (no Load more); reload still asserted.

## Contradictions

None between brief and cited DESIGN / API contracts.

## Known problems (outside done evidence)

- Generic `brush()` helper may be unreliable on `exec-shape-series` without targeting the inner plot area (TimeChart out of scope).
