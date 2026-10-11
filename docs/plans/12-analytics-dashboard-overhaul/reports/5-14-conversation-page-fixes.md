# Report: 5-14 — Conversation page: back link, unpriced rows, cost label

Status: **done**

Branch `wt/5-14`, worktree `/home/codyh/workspace/wt/5-14`. Owned paths only:

- `packages/workflow-analytics/src/routes/conversation/+page.svelte`
- `packages/workflow-analytics/src/lib/format.ts`
- `packages/workflow-analytics/src/lib/format.test.ts`
- `packages/workflow-analytics/tests/e2e/conversation.spec.ts`

## What changed

**Back link (Carried 3).** Imported `afterNavigate` from `$app/navigation`. A `ROUTE_NAMES` map names each site route (`/` Overview, `/trends`, `/usage`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, `/explore`). On navigation the callback remembers `from.url.pathname + from.url.search` when `from` is one of those routes (so `/conversation` and `/settings` are excluded), keeps it in `$state` and writes `{href,name}` to `sessionStorage` under `workflow-analytics-last-list` (try/catch). When `from` is not a known route and nothing is remembered, it loads the stored value; with none it falls back. The anchor is now `href={lastList?.href ?? '/conversations'}` labelled `← Back to {name ?? 'Conversations'}`; `data-testid="back-to-conversations"` unchanged. No links in other routes touched.

**Timeline rows (Carried 4).** `rowCost` counts tokens as `in + out`. A row with `in+out > 0` and no positive `cost_usd` reads `unpriced`; a row with `in+out === 0` (or no tokens) shows no cost text even when `cost_usd` is 0. Priced rows use `costLabel`.

**`costLabel` (Carried 8).** With `calls` known: `calls === 0` → `—`; `unpriced >= calls` → `unpriced`; `0 < unpriced < calls` → `${money(cost)}, N unpriced` when `cost > 0` else `N unpriced` (the fix — was `$0.00`); `unpriced === 0` → `money(cost)` or `$0.00` at zero. With `calls` unknown: `unpriced > 0` → `money(cost), N unpriced` or `unpriced` at zero cost; else `money(cost)` or `$0.00`. `money` is `cost < 0.01 ? toFixed(4) : toFixed(2)`. Signature unchanged.

## Evidence, before → after

- `npm test -- format`: **before** `Tests 3 failed | 20 passed` (the mixed-unpriced/zero-cost case and the invariant returned `$0.00`). **after** `23 passed`.
- `E2E_PORT=4514 npm run test:e2e -- conversation.spec.ts`: **before** `2 failed | 9 passed` (both new tests). **after** `11 passed`.
  - back link: before landed on `/conversations`; after clicking a conversation from `/conversations?range=7d&harness=claude` and back lands on that exact URL.
  - rows: before the zero-token row read `... in 0 ... unpriced`; after it has no `unpriced` text and the tokenized unpriced row still does.
- `npm test`: `89 passed` (10 files).
- `npm run build`: built, adapter-static wrote `build`.
- `E2E_PORT=4514 npm run test:e2e -- overview.spec.ts usage.spec.ts repos.spec.ts`: `27 passed`.

## Deviations

None from the owned paths or the contract. Added one extra invariant assertion ("never prints `$0.00` beside unpriced calls") beyond the truth-table rows; it fails on the old code.

## Contradictions

None between the brief and the contracts it cites. Note one reading: the brief says "return `unpriced` only when every call is unpriced", but with `calls` unknown there is no denominator, so the existing behaviour (`unpriced > 0 && cost === 0` → `unpriced`) is preserved and pinned; the brief's truth table lists `calls undefined` as a case, and existing assertions require it.

## Known problems

None found outside this unit. The back link is per-tab (`sessionStorage`) and a direct deep link with no history shows the `/conversations` fallback, both as specified.
