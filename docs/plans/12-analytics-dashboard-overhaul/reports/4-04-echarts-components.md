# 4-04 — ECharts components, theme tokens and the data-table toggle

Status: **done with concerns**

## What changed

- `packages/workflow-analytics/package.json`, `package-lock.json`: added `echarts` pinned to `6.1.0` (npm resolved 6.1.0).
- `src/lib/theme.css` (new): `:root` tokens `--bg --surface --text --muted --border --accent --danger --series-1..8`, dark under `@media (prefers-color-scheme: dark)`; comment says the layout imports it.
- `src/lib/charts/theme.ts` (new): `DEFAULT_TOKENS`, `readTokens(el)` (getComputedStyle, per-var fallback), `scheme()`, `watchScheme(cb)`.
- `src/lib/charts/options.ts` + `options.test.ts` (new): pure `barOption`, `timeOption`, `heatmapOption`, `treemapOption`; no DOM, no runtime echarts import.
- `src/lib/charts/theme.test.ts` (new): readTokens fallback/series order, scheme, watchScheme subscribe/unsubscribe.
- `src/lib/charts/EChart.svelte` (new): `echarts.init(el, null, {renderer:'svg'})`, `ResizeObserver`, dispose, `data-ready` (false per option → true on `finished`), `data-theme`, re-`setOption` on media-query change, forwards click (`event.event`) and `brushEnd`; registers only bar/line/heatmap/treemap + grid/tooltip/legend/brush/visualMap/aria + SVGRenderer.
- `DataTable.svelte` (new): one `<tr>` per row, click/keydown fires select, inert rows.
- `BarChart.svelte` (new): fixed grid 120/24/8/24, `yAxis.inverse`, height `max(120, 28×rows+32)`, `__other__` inert, table toggle.
- `TimeChart.svelte` (new): time axis, line/stacked bar, `brush.brushType:'lineX'` armed on mount via `takeGlobalCursor`, `brushEnd` → `onbrush({from,to})` then clear, table toggle.
- `Heatmap.svelte`, `Treemap.svelte` (new): visualMap 24×7 heatmap; treemap leaf click → `onselect({path,shift})` from `treePathInfo`; table toggles.
- `Sparkline.svelte` (new): 28 px, no axes, `silent`.

Temporary `src/routes/charts-preview/+page.svelte` used to compile/SSR-validate, deleted before commit.

## Check output

- Before impl: `npx vitest run src/lib/charts` → FAIL, 2 files: `Cannot find module './options'` and `'./theme'`.
- After impl: `npx vitest run src/lib/charts` → 2 files / 14 tests pass. `npm test` → 11 files / 76 tests pass (other workers' suites also green by then).
- Build/bundle (exact brief command): build passes; `check:bundle` with `E2E_FORBIDDEN=k,d` **fails** — see contradiction below.
- Build/bundle (16-char secrets): `npm run build` with two dummy 20-char values in the E2E key and dummy-token environment variables → exit 0; `E2E_FORBIDDEN=<same>` `npm run check:bundle` → `ok (79 files, 2 forbidden values)`.

## Contradictions / deviations (named)

1. **Brief vs `check-bundle.mjs`.** The brief's `E2E_FORBIDDEN=k,d` cannot pass: `check-bundle` does substring matching, so single-char `k`/`d` match every bundle (`build/index.html: contains a forbidden value (length 1)`). This is a tooling/brief contradiction, not a leak; proven with 16-char secrets above. Not resolved silently.
2. **Temp route path.** SvelteKit treats `_`-prefixed dirs as private and does not route them, so `src/routes/_charts/+page.svelte` would be unvisitable in `npm run dev`. Used `src/routes/charts-preview/+page.svelte` for validation, then deleted (neither is committed).
3. **Per-datum cursor.** ECharts has no per-data `cursor`; series-level only would also give `__other__` a pointer. Implemented via `mouseover` + `getZr().setCursorStyle` using the datum `clickable` flag, honouring the contract's `__other__` no-pointer rule.
4. **heatmapOption shape.** Returns sparse triples (`data.length == cells.length`); the 24×7 domain is the axis categories and visualMap `min/max` derive from the values. A literal "168 filled cells" reading would zero-fill and collapse the visualMap range; chose the reading that keeps the range meaningful.
5. **TimeChart not using `fillBuckets`.** `fillBuckets` steps day/week and consumes `{t,n}`; TimeChart buckets include hour/month and points are `{t,v}`. Not applicable, so omitted.
6. Version pinned to exact `6.1.0` (brief: pin the resolved version).

## Known problems

- Concurrent `vite build` across the parallel workers clobbers `.svelte-kit/output`: symptom `ENOENT … server/manifest-full.js`; location `@sveltejs/kit` vite plugin (`writeFileSync`); cause is two builds sharing the output dir. A solo re-run passed. Not fixed (outside owned paths).
- UI not eyeballed in a real browser; validation was SSR + client build (the preview SSR entry compiled) and unit tests.
