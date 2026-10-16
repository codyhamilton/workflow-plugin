Status: done

## What changed

- Extended `allowedCharts(0, 'none')` with chart kind `scalar`; `parseConfig` defaults to it for zero-dimension, no-bucket configs.
- `BuilderChart` renders a prominent formatted scalar (`data-testid` `{testid}-scalar`, `data-value`) when `c=scalar`; builder page passes measure `unit` from schema.
- `heatmapProps` now returns raw `xKeys`/`yKeys`; `Heatmap` wires ECharts and table clicks to `onpick` on the first dimension when it is a `DIM_KEYS` filter key (not `weekday`/`hour_of_day`, not `__other__`/empty).
- E2e: scalar total vs API, model×harness heatmap drill, weekday×hour inert.

## Done evidence

Before (updated expectations, implementation not yet applied):

```
npm test -- src/lib/builder.test.ts
FAIL  allowedCharts(0, 'none') — Expected: ["scalar"] Received: []
FAIL  parseConfig empty URL chart — Expected: "scalar" Received: "line"
```

After:

```
npm test -- src/lib/builder.test.ts
✓ 23 tests passed

export E2E_PORT=4395 && npx playwright test tests/e2e/builder.spec.ts
8 passed (17.4s)
```

## Departures

None.

## Contradictions

None between this brief and cited DESIGN domains (builder scalar and filter-dimension heatmap drill vs overview heatmap inert).

## Problems

None known within done evidence scope.
