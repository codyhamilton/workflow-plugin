# 5-19-area-wiring — Wire the area chart end to end

Status: blocked. The area wiring is built and verified in isolation (unit, build, and a new e2e proving area renders as line+areaStyle), but the brief's done evidence cannot pass: `tests/e2e/builder.spec.ts:31` is already red on the base commit for an unowned reason — a 5-18 regression in `SmallMultiples.svelte`. This commit lands the wiring and the spec; the blocker is recorded below.

## What changed

- `packages/workflow-analytics/src/lib/charts/TimeChart.svelte`: added an optional `area` boolean prop (default `false`); `build` now calls `timeOption({ series, bucket, stacked, area }, t)`.
- `packages/workflow-analytics/src/lib/charts/BuilderChart.svelte`: the `line`/`area` branch passes `area={config.chart === 'area'}` instead of `stacked={config.chart === 'area'}`; `line` stays unstacked.
- New `packages/workflow-analytics/tests/e2e/area.spec.ts`.
- `options.ts` and `multi.test.ts` untouched.

## Tests

`tests/e2e/area.spec.ts`:
- "area chart renders a filled area path and its line stroke": `?m=cost_usd&d=model&b=day&c=area`; asserts `data-kind=area`, `builder-chart-chart` visible and `expectSettled`; then that the chart SVG holds both a filled series-colour path (`path[fill="#2563eb"]`, the area fill) and a stroked `fill="none"` path of the same colour (the line). Fails before the two edits, passes after.
- "multiples chart settles in the browser": `?m=cost_usd&d=model&d=harness&b=day&c=multiples`; asserts `data-kind=multiples`, a visible `builder-chart-panel` and `expectSettled`. Fails before and after — the 5-18 blocker below.

`npm test`: 15 files, 160 passed. `npm run build`: passed.

## Evidence

BEFORE the two edits — `E2E_PORT=4519 npm run test:e2e -- area.spec.ts`:
```
  ✘  area chart renders a filled area path and its line stroke
     locator('svg path[stroke="#2563eb"][fill="none"]') — element(s) not found
  ✘  multiples chart settles in the browser
  2 failed
```
The stroke path is absent because pre-fix `chart=area` renders stacked bars (filled paths only): the required BEFORE failure.

AFTER the two edits — same command:
```
  ✓  area chart renders a filled area path and its line stroke (447ms)
  ✘  multiples chart settles in the browser
  1 failed  1 passed (15.1s)
```

Done-evidence gate — `E2E_PORT=4519 npm run test:e2e -- builder.spec.ts area.spec.ts`:
```
  2 failed
    area.spec.ts › multiples chart settles in the browser
    builder.spec.ts:31 › cost_usd by model and harness on a day bucket renders small multiples
  5 passed
```

Base commit `bff3b57` with the 5-19 edits stashed — `E2E_PORT=4519 npm run test:e2e -- builder.spec.ts`:
```
  4 passed, 1 failed
  builder.spec.ts:31 fails at :38 (builder-chart-panel not visible)
```
So `builder.spec.ts:31` is red without 5-19: pre-existing.

`npm test`: `Test Files 15 passed (15) / Tests 160 passed (160)`. `npm run build`: `✓ built in 6.74s`, `Wrote site to "build"`, `✔ done`.

`git diff --stat` (source only): `TimeChart.svelte | 4 +++-`, `BuilderChart.svelte | 2 +-`.

## Deviations from the brief

1. Contract 3 permits asserting "the chart's data-table or the ECharts option (`getOption()` through the page)". Neither can reveal series type/`areaStyle` (see Contradictions), so the spec asserts the ECharts **SVG render output** instead — a real browser observable. Recorded, not silent.
2. Done evidence ("`builder.spec.ts area.spec.ts` pass") cannot be met. The area assertions pass; the two multiples failures are the unowned 5-18 blocker. Recorded, not silent.
3. `multi.test.ts` was an owned path but the contract required no change, so it is untouched.

## Contradictions

- **`getOption()` / data-table unreachable.** `EChart.svelte` keeps the ECharts instance in a component-local `let`, never exposed; there is no global `echarts`; the e2e runs a production `vite preview`, so nothing can be imported from the page, and `getOption()` cannot be called. The `TimeChart` data-table renders values only. The renderer is SVG, so the option is observable in the DOM: area = a filled `path[fill=#2563eb]` **and** a stroked `path[stroke=#2563eb][fill=none]`; stacked bar = filled only; plain line = stroked only. `#2563eb` is `DEFAULT_TOKENS.series[0]`; axes use `t.border` (#d1d5db). Requiring both uniquely proves line+`areaStyle`.
- **5-18 regression blocks the brief (unowned path).** `SmallMultiples.svelte:79` binds `bind:ready={panelReady[panel.key]}` to `EChart`'s `ready = $bindable(false)`, which has a fallback. On first mount `panelReady[panel.key]` is `undefined`, so Svelte throws `props_invalid_value` ("Cannot do `bind:ready={undefined}` when `ready` has a fallback") and the multiples subtree fails to render; the query itself returns 200 with 4 rows. Introduced by 5-18 (`01403f3`); `builder.spec.ts:31` predates it (`a11314c`) and was green until then, so both it and this unit's multiples test fail before and after the edits. `SmallMultiples.svelte` is not an owned path and was not touched. 5-18's own report predicted this ("Known limitations" #2: the bind is unverified in a browser; real mount/e2e coverage is a recommended follow-up).

## Unfinished

1. Fix `SmallMultiples.svelte` so it never binds `undefined` into a fallback prop — e.g. initialise `panelReady` keys to `false`, or set readiness without `bind` (callback/`$effect`). Owned by a follow-up unit (not 5-19).
2. After (1), re-run `E2E_PORT=4519 npm run test:e2e -- builder.spec.ts area.spec.ts`; expect 7 passed.

## Known limitations / follow-ups

- The area assertion depends on ECharts' SVG path attributes rather than its API; if ECharts changes how it colourises areas the selector must be revisited. It is intentionally strict (fails on stacked bars).
- The multiples route stays red until the 5-18 blocker is fixed; this unit's multiples test will then pass unchanged.
