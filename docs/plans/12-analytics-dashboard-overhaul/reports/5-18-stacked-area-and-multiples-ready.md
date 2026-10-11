# 5-18 — Stacked area type and small-multiples settle signal

Status: done.

## What changed

- `packages/workflow-analytics/src/lib/charts/options.ts`
  - `TimeProps` gains `area?: boolean`.
  - `timeOption` adds `const area = p.area === true;`. Series now: `type: area ? 'line' : stacked ? 'bar' : 'line'`, `stack: (area || stacked) ? 'total' : undefined`, and `areaStyle: {}` only when `area` is true (via `...(area ? { areaStyle: {} } : {})`). `stacked` without `area` is unchanged (bar/`total`, no `areaStyle`). Area takes precedence when both are set. No other key changed.
- `packages/workflow-analytics/src/lib/charts/SmallMultiples.svelte`
  - Added `let panelReady = $state<Record<string, boolean>>({})` and `const ready = $derived(panels.length === 0 || panels.every((p) => panelReady[p.key] === true))`. Readiness is keyed by the panel's stable `key` (`panelReady[p.key]`), so a changed or reordered panel set cannot leave a stale `true` at a reused index and report `data-ready="true"` before the new child charts mount.
  - Root `<div class="multiples" data-ready={ready ? 'true' : 'false'}>`; each `EChart` binds `bind:ready={panelReady[panel.key]}` (whose `ready` is `$bindable(false)`). No `data-theme` added (not required).
- `EChart.svelte` untouched: area is a `line` series with `areaStyle`, and `LineChart` is already registered.

## Tests

- `options.test.ts` (in `timeOption` describe): area → all series `type 'line'`, `stack 'total'`, truthy `areaStyle`, both series share one stack; stacked-only → `type 'bar'`, `stack 'total'`, `areaStyle` undefined.
- `multi.test.ts`: chose the **SSR-render** approach (brief option 1). A temp `src/lib/charts/__spike.test.ts` proved `import { render } from 'svelte/server'` renders `SmallMultiples.svelte` under vitest/node, then was deleted. Two tests: empty panels → body contains `data-ready="true"`; one unmounted panel → body contains `data-ready="false"`.

## Evidence

BEFORE (tests added, source unchanged), `npx vitest run src/lib/charts/options.test.ts src/lib/charts/multi.test.ts`:
```
 FAIL  multi.test.ts > SmallMultiples data-ready > is ready on the root when there are zero panels
     expected '...<div class="multiples svelte-...">...' to contain 'data-ready="true"'
 FAIL  multi.test.ts > SmallMultiples data-ready > is not ready before its child charts mount
     expected '...' to contain 'data-ready="false"'
 FAIL  options.test.ts > timeOption > renders area as stacked line series with an areaStyle
     expected undefined to be 'total'
 Test Files  2 failed (2)
      Tests  3 failed | 20 passed (23)
```

AFTER, `npm test`:
```
 Test Files  15 passed (15)
      Tests  156 passed (156)
```

AFTER, `npm run build`:
```
✓ built in 6.05s
Wrote site to "build"
✔ done
```

`git status --short` / `git diff --stat`: 4 modified files, 67 insertions(+), 4 deletions(-): `SmallMultiples.svelte`, `multi.test.ts`, `options.test.ts`, `options.ts`.

## Deviations from the brief

- (a) The brief told the SSR test to pass `panels: []` and assert `data-ready="false"`. Its own Contract 2 says ready is true when there are zero panels, so `panels: []` yields `"true"`. I kept the empty-panel case asserting `"true"` (the correct aggregation) and added a one-panel pre-mount case asserting `"false"`. Testing `"false"` for `[]` would have failed after the change too.
- (b) `areaStyle` is `{}`; the brief allowed `{}` or an opacity object. No opacity chosen since no design value was given.

## Contradictions

- **TimeChart/BuilderChart (Contract 1 check, read-only).** `TimeChart.svelte` props are `{ testid, series, bucket, stacked = false, onbrush }` and it calls `timeOption({ series, bucket, stacked }, t)` — it does **not** forward an `area` prop. `BuilderChart.svelte` passes `stacked={config.chart === 'area'}`. So after this change the `area` option works in `timeOption`/`SeriesCell`-level tests but is unreachable end-to-end: an area chart still renders stacked bars. This is the expected contradiction; **not fixed** (files not owned; BuilderChart/TimeChart untouched).
- **Brief-internal** (see Deviation a): the suggested `panels: []` → `data-ready="false"` assertion contradicts Contract 2's "true when there are zero panels".

## Unfinished

- Wire `area` through `TimeChart` → `timeOption` and make `BuilderChart` pass `area` (and stop passing `stacked`) for `config.chart === 'area'`. Needs a follow-up unit that owns `TimeChart.svelte`/`BuilderChart.svelte`.

## Known limitations / follow-ups

1. **Area is not wired end-to-end.** `TimeChart.svelte` has no `area` prop and `BuilderChart.svelte:53` still passes `stacked={config.chart === 'area'}`, so area still renders stacked bars in the UI. Files are not owned by this brief — needs a follow-up unit owning `TimeChart.svelte`/`BuilderChart.svelte`.
2. **The `multi.test.ts` data-ready test is SSR-only.** It uses `svelte/server` SSR, which never mounts `EChart`; it proves the `data-ready` attribute exists and its initial aggregation, but does not exercise the `bind:ready={panelReady[p.key]}` propagation. No e2e spec calls `expectSettled` on a `kind=multiples` panel (`tests/e2e/builder.spec.ts` only checks `data-kind`). Real mount/e2e coverage is a recommended follow-up (out of this brief's owned paths).
3. **A panel whose EChart never emits `finished` pins `data-ready="false"`.** This matches every sibling chart component and is not a regression.
