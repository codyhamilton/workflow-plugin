# 4-06 — Overview: KPI tiles with sparklines and the hour-by-weekday heatmap

Status: **done**

## What changed

- `src/routes/+page.svelte`: rewritten on `view` and the `getJSON` client. One `analytics/summary` per window (slot `overview-summary`); nine `analytics/query` sparkline requests (slot `overview-spark-<id>`, bucket from `pickBucket(from, to, tz, …)`, `month` on `all`); one `analytics/query` heatmap (`measure=hook_events`, `dim=weekday`, `dim=hour_of_day`, `bucket=none`, slot `overview-heatmap`). Tiles: conversations, hook_events, artifact_versions, distinct_content, commits, model_calls, tokens (`tokens_in + tokens_out`) with a `summary-tokens_cache_read` element, cost (`costLabel`), unpriced_calls. `Heatmap testid="overview-heatmap"`, `xLabels` "00".."23", `yLabels` Sun..Sat. Ignore `Superseded`, `setError` otherwise, `clearError` on success.
- Restored the old page's grouped `summary-*` tiles. A secondary grouped section is derived from the same single `summary` response (no extra requests) and renders `summary-by_kind-{design,brief,report,other}`, `summary-by_source-{worktree,commit}`, `summary-rejections-{precheck,screen}` and `summary-screens-{pass,unscreened}` as plain number rows. The nine scalar tiles, the `overview-summary`/`overview-spark-*`/`overview-heatmap` slots, and every `summary-<id>` id are unchanged. This keeps the `summary-<id>` ids the brief's Contract line 33 requires to stay untouched.
- `tests/e2e/overview.spec.ts`: 8 tests — whole-window (`expectNumbers(page, SUMMARY_ALL)` over the full map incl. the grouped ids, the `model_calls`/`unpriced_calls` usage tiles, then the dedicated `summary-tokens`, `summary-tokens_cache_read`, `summary-cost_usd` assertions); `repo_id` in URL + reload and filter-bar select + goBack, both over the full `SUMMARY_R1`; non-empty filter options; cost never `$0.00` while unpriced (real `$0.02, 2 unpriced`, then a `page.route` summary with `cost_usd:0, model_calls:3, unpriced_calls:3` → `unpriced`); heatmap `data-ready="true"`; preset click → settled < 1 s; request count (≤1 summary, ≤10 query).
- The cost-unpriced mock now supplies the nested `by_kind`/`by_source`/`rejections`/`screens` shape the real serve returns (rebuilt from the flat fixture keys, no invented counts). The restored grouped render reads those nested fields, so a flat mocked body would have faulted and hidden the cost tile.
- Reactivity trap: as briefed — track `view.state`, track `view.facets` only when `state.exclude` is non-empty, and compute every `view.paramsFor(…)` inside `untrack`.

## Check output

All commands from `packages/workflow-analytics`.

**Before** (recorded at `eed814d`, old spec against the rewritten page): `E2E_PORT=4406 npx playwright test overview.spec.ts` → 4 failed / 0 passed, every failure `expectNumbers` awaiting `summary-by_kind-design` (then `by_source-*`, `rejections-*`, `screens-*`), which the page did not render.

**After** (measured):

- `npm test` → `Test Files 11 passed (11) / Tests 76 passed (76)`.
- `npm run build` → exit 0 (`✓ built in 10.71s`, `Wrote site to "build"`).
- `E2E_PORT=4406 npm run test:e2e -- overview.spec.ts` → `8 passed (19.3s)`.
- `E2E_PORT=4406 npm run test:e2e -- settings.spec.ts` → `1 passed (15.5s)`.
- `E2E_PORT=4406 npm run test:e2e` (full suite) → `36 passed (29.3s)`, no failures.

## Deviations

1. Whole-window usage numbers: `USAGE_ALL` also carries `tokens_in`/`tokens_out`/`tokens_cache_read`/`tokens_cache_write`/`tokens_reasoning` and `cost_usd`, which the page renders through the dedicated `summary-tokens`/`summary-tokens_cache_read`/`summary-cost_usd` tiles, not as `summary-tokens_in`-style plain rows. So the usage portion asserts `model_calls`/`unpriced_calls` via `expectNumbers` and keeps the dedicated tiles for the rest, per the brief's parenthetical ("usage covers model_calls/unpriced_calls; do not assert cost_usd/tokens_* raw").
2. The cost-unpriced mock body was given the nested grouped shape (see "What changed"). The test itself is unchanged; only the mocked response was completed to match the shape the serve returns.

## Contradictions

- The brief's Contract line 33 ("Unchanged: the `summary-<id>` test ids for the tiles the old page had") conflicted with its Changes section and required-tile list, which omit the old grouped tiles (recorded when `eed814d` dropped them). Resolution: the Contract wins — the grouped `summary-*` ids were restored, rendered off the same `summary` response, and the old `SUMMARY_ALL` assertions are back. The ids are exercised by `tests/e2e/settings.spec.ts:23-24` (passing in this run) and `tests/hosted/hosted.spec.ts:33-34`, both of which assert every `SUMMARY_ALL` entry as `summary-<key>`. The hosted spec is not re-run here (it needs a `tools/release/build.sh` binary via `WORKFLOW_BIN`, absent in this worktree); it reads the same page and fixture.

## Non-trivial bugs outside done evidence

None found. Verified `localKey` (`tools/workflow/internal/store/query.go:632-635`) emits hour `"00".."23"` and weekday `"0".."6"`, so the page's `Number(x.k[1])` / `Number(x.k[0])` decode is correct. The heatmap test asserts only `data-ready`, not cells.

## Unfinished

None.
