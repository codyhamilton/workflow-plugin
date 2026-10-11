# 4-06 — Overview: KPI tiles with sparklines and the hour-by-weekday heatmap

Status: **done**

## What changed

- `src/routes/+page.svelte`: rewritten on `view` and the `getJSON` client. One `analytics/summary` per window (slot `overview-summary`); nine `analytics/query` sparkline requests (slot `overview-spark-<id>`, bucket from `pickBucket(from, to, tz, …)`, `month` on `all`); one `analytics/query` heatmap (`measure=hook_events`, `dim=weekday`, `dim=hour_of_day`, `bucket=none`, slot `overview-heatmap`). Tiles: conversations, hook_events, artifact_versions, distinct_content, commits, model_calls, tokens (`tokens_in + tokens_out`) with a `summary-tokens_cache_read` element, cost (`costLabel`), unpriced_calls. `Heatmap testid="overview-heatmap"`, `xLabels` "00".."23", `yLabels` Sun..Sat. Ignore `Superseded`, `setError` otherwise, `clearError` on success.
- `tests/e2e/overview.spec.ts`: 8 tests — whole-window tiles incl. tokens/cache-read/cost; `repo_id` in URL + reload; filter-bar select + goBack; non-empty filter options; cost never `$0.00` while unpriced (real `$0.02, 2 unpriced`, then a `page.route` summary with `cost_usd:0, model_calls:3, unpriced_calls:3` → `unpriced`); heatmap `data-ready="true"`; preset click → settled < 1 s; request count (≤1 summary, ≤10 query).
- Reactivity trap: as briefed — track `view.state`, track `view.facets` only when `state.exclude` is non-empty, and compute every `view.paramsFor(…)` inside `untrack`.

## Check output

**Before** (old spec against the new page): `E2E_PORT=4406 npx playwright test overview.spec.ts` → 4 failed / 0 passed. All four fail the same way: `expectNumbers` awaits `summary-by_kind-design` (and would then hit `by_source-*`, `rejections-*`, `screens-*`), which the new page does not render. Per test:

- `overview shows the fixture numbers for the whole window` (l.15) — `summary-by_kind-design` expected "3": element not found.
- `repo_id in the URL filters, and survives a reload` (l.20) — `summary-by_kind-design` expected "2": element not found.
- `choosing a repo in the filter bar changes the URL and the numbers` (l.28) — `summary-by_kind-design` expected "3": element not found.
- `no filter control offers an empty option` (l.38) — `summary-by_kind-design` expected "3": element not found.

**After** (measured):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0 (`✓ built in 15.00s`, `Wrote site to "build"`).
- `E2E_PORT=4406 npm run test:e2e -- overview.spec.ts` → `8 passed (25.7s)`; timing test 280 ms; request-count test passed.

## Deviations

1. Test 4 ("no filter control offers an empty option") waits on `TILES_ALL`, not the old `SUMMARY_ALL`. `SUMMARY_ALL` carries `by_kind-*`/`by_source-*`/`rejections-*`/`screens-*` keys the new page no longer renders, so a verbatim copy would fail before the options loop. Loop body is otherwise identical.
2. Tiles are the nine the brief lists; the old page's grouped tiles (`by_kind-*`, `by_source-*`, `rejections-*`, `screens-*`) are gone. Only the scalar `summary-<id>` ids both sets share were kept.

## Contradictions

- The brief's Contract line 33 ("Unchanged: the `summary-<id>` test ids for the tiles the old page had") conflicts with its Changes section and required-tile list, which omit the old grouped tiles. Those ids no longer exist, so their old assertions were dropped. Named, not resolved silently.

## Non-trivial bugs outside done evidence

None found. Verified `localKey` (`tools/workflow/internal/store/query.go:632-635`) emits hour `"00".."23"` and weekday `"0".."6"`, so the page's `Number(x.k[1])` / `Number(x.k[0])` decode is correct. The heatmap test asserts only `data-ready`, not cells.

## Unfinished

None.
