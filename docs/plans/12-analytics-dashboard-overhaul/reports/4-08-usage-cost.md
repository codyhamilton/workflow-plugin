# 4-08 — Usage & cost: cost by model, tokens and unpriced calls shown explicitly

Status: **done with concerns**

## What changed

- New `packages/workflow-analytics/src/routes/usage/+page.svelte`.
- New `packages/workflow-analytics/tests/e2e/usage.spec.ts` (7 tests).

The page issues exactly seven `/query` requests on load, all through `view.paramsFor('query', …)` and the shared client (debounce + cache + 3-at-a-time): five by model (`cost_usd`, `model_calls`, `unpriced_calls`, `tokens_in`, `tokens_out` — `dim=model`, `top=20`, `bucket=none`) and two over time (`cost_usd` × model stacked, `tokens_out` no dim, `bucket` from `pickBucket`). Rows from the five responses are joined by model into one table (`usage-row-<model>`, `usage-<model>-{calls,unpriced,tokens_in,tokens_out,cost}`). Cost text is `costLabel({cost, unpriced, calls})`; the banner `usage-unpriced-banner` reads "N of M calls are unpriced" and is absent when N is 0. `BarChart usage-cost-by-model` labels a zero-cost model with unpriced calls `<model> (unpriced)` and makes it inert (the page's select handler ignores it). `usage-footnote` carries the Claude-live-dedupe line. Model bars and table rows call `view.drill('model', name, {shift})`; `__other__` is ignored.

## Check output

- Before the page existed: `E2E_PORT=4408 npm run test:e2e -- usage.spec.ts` → **7 failed** (no `/usage` route; `expectSettled` found no `[data-ready]`).
- After: `E2E_PORT=4408 npm run test:e2e -- usage.spec.ts` → **7 passed** (25.5 s).
- `npm test` → **11 files / 76 tests passed**.
- `npm run build` → **pass** (static adapter wrote `build/`).
- `trackRequests(page, /analytics\/query/)` → **7** for one load, none per model.

## Departures (named, with reasons)

1. **`all` bucket = `month`.** `resolveWindow(state, now, tz, 'query')` returns `{all:true}` with no `from`/`to` for `range=all`, so `pickBucket` has nothing to size against. The brief says "for `all` use a `week` or `month` bucket (`pickBucket`)"; `month` is chosen for the no-edges case; every windowed range uses `pickBucket`.
2. **`clickBar` needs the table opened first.** The helper (`tests/e2e/helpers.ts:58-73`) counts `<testid>-table` rows immediately after its own toggle click, before Svelte flushes, so `n` is still 0 and it throws `no chart box or table rows`; it then computes chart coordinates against the table box. The specs open the chart's table (`openTable`) and wait for a row before calling `clickBar`, and use `clickBar` index = row + 1. Consequence: the click lands on the table-row representation of the bar, not the bar mark. Reported below as a helper bug; not fixed (not an owned path).
3. **Token slot names.** The brief lists slots `usage-by-model-cost`, `-calls`, `-unpriced`, `-tokens`, `usage-over-time` (five) but also "seven (five by model, two over time)". The two token measures therefore use `usage-by-model-tokens-in` and `usage-by-model-tokens-out`.

## Contradictions between this brief and the contracts it cites

- The brief's slot list names five slots for seven queries and collapses `tokens_in`/`tokens_out` into one `-tokens`. Resolved by naming both; not resolved silently.
- "The priced Sonnet model's row shows its hand-counted cost": the hand-count is `0.0223`, but `costLabel` renders `$0.02` (it formats, per DESIGN.md line 455). The spec asserts `$0.02`.

## Known problems

- **`clickBar` is unusable as written** (`tests/e2e/helpers.ts:58-73`). Symptom: it throws `clickBar: no chart box or table rows`, or clicks the wrong row. Root cause: on its `n===0` path it clicks the table toggle and counts `tbody tr` with no wait for the Svelte flush, then derives bar coordinates (fixed `120/24/8/24` grid) from a box that now holds the table. A correct helper would read N some other way (or await the toggle) and click while the chart is the visible branch. Outside this unit's owned paths; left for 4-03/4-16.
- `data/summary`-style totals are not used: N and M for the banner are the sums over the top-20 model rows, so with more than 20 models they under-count. Matches the brief (no summary query permitted) but is worth noting.

Nothing unfinished: the two owned files are complete and all done-evidence checks pass.
