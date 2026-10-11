# 5-03 — Sankey and box-plot chart components

Status: **done with concerns**

## What changed

- `src/lib/charts/sankey.ts` (new): pure `sankeyOption({nodes,links}, t)`; `SankeyNode`, `SankeyLink`. One `sankey` series, `emphasis.focus:'adjacency'`, `lineStyle` token colour + `opacity:0.35` + `curveness:0.5`, `label.color=t.text`, `itemStyle` `bg`/border, links filtered to `value>0`.
- `src/lib/charts/sankey.test.ts` (new): nodes/links mapping, non-positive links dropped, adjacency emphasise, translucent token line, recursive "every hex is a token" check.
- `src/lib/charts/SankeyChart.svelte` (new): `EChart` + table toggle (`<testid>-table-toggle`, `<testid>-table`), columns `source,target,value` (positive links only), `onlink` fires on `dataType==='edge'`.
- `src/lib/charts/box.ts` (new): pure `boxOption({rows}, t)`; `BoxRow`. Horizontal boxplot (`xAxis` value, inverted `yAxis` category), fixed grid 120/24/8/24, token axis/line colours; adds one `scatter` series only when a row has a numeric `marker`.
- `src/lib/charts/box.test.ts` (new): category per row, `series[0].data[0]===[min,p25,median,p75,max]`, no scatter without markers, exactly one scatter with only marked rows, token-colour check.
- `src/lib/charts/BoxChart.svelte` (new): `EChart` + table toggle, columns `Name,Min,P25,Median,P75,Max,Marker` (marker blank when unset).
- `src/lib/charts/EChart.svelte` (edit): added `SankeyChart`, `BoxplotChart`, `ScatterChart` to the `echarts/charts` import and the `echarts.use([...])` list. Nothing else changed.

## Check output

**Before** — `npm test -- sankey box`:
```
No test files found, exiting with code 1
filter: sankey, box
include: src/**/*.test.ts
```
(also `Cannot find base config file "./.svelte-kit/tsconfig.json"` warning; `.svelte-kit` absent pre-build.)

**After** — `npm test -- sankey box`:
```
✓ src/lib/charts/box.test.ts (5 tests) 6ms
✓ src/lib/charts/sankey.test.ts (4 tests) 6ms
 Test Files  2 passed (2)
      Tests  9 passed (9)
```

**Full suite** — `npm test`: `Test Files 12 passed (12)`, `Tests 83 passed (83)`.

**Build** — `npm run build`: `✓ built in 7.14s`, adapter-static `Wrote site to "build"`, exit 0. No ENOENT manifest.

**layerchart grep** — `rg -il layerchart build` and `rg -il layerchart .svelte-kit/output/client`: **no matches** in either.

## Deviations (named)

1. **Brief self-contradiction — Sankey/Boxplot vs ScatterChart registration.** The EChart.svelte section says "only add SankeyChart and BoxplotChart", but the boxplot section requires a `scatter` series when a row has a marker. `boxOption` emits that series, so a registered `ScatterChart` is required for the chart to render. I added **all three** (`SankeyChart`, `BoxplotChart`, `ScatterChart`).
2. **Return types left inferred** (not annotated `object` as in the contract block). The brief's own "existing patterns" shows `barOption` etc. with no return annotation, and `options.test.ts` reads `.series[0].data` directly; annotating `object` would break typed access in tests and downstream. Followed the established `options.ts` style. The intermediate local `series` is likewise typed concretely (`{ type: string; data: unknown[]; itemStyle?; emphasis? }[]`) rather than the initial `object[]`; `object[]` erased element types and produced 6 `tsc` errors in `box.test.ts` (`option.series[0].type` / `.data`), so the concrete element type is required to keep the test type-checkable, aligning with how `options.ts` lets series shapes infer concretely. Runtime shape is exactly as contracted.
3. **No explicit `height` prop** on either component; EChart's default 280 is used, matching the minimal contract given (no height specified).

## Known problems

- None new within owned paths. Pre-existing risk noted in 4-04: concurrent `vite build` across parallel worktree workers can clobber `.svelte-kit/output` (ENOENT manifest). The solo build here passed; not reproduced.
- UI not eyeballed in a browser; validated by unit tests, full suite and client+server build, not a visual render.
