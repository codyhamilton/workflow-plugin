# Report: 4-18 — Show unpriced events as unpriced and stop the superseded-request storm

Status: done with concerns

## What changed (against each part of the brief)

**A — Timeline `$0.00`.** `src/routes/conversation/+page.svelte` `rowCost`: a usage event (`tokens`
present) with `cost_usd` null or not `> 0` now returns `'unpriced'`; a positive cost still goes
through `costLabel`. `tools/workflow/internal/store/conversation.go:117-125` confirms unpriced usage
events carry `cost_usd: 0` (non-usage events omit it), so the old `!= null` branch printed `$0.00`.
`tests/e2e/conversation.spec.ts` gains a test asserting the c5 qwen row reads `unpriced` and no row
reads `$0.00`.

**B — Request storm.** Real cause, found by logging effect runs and requests (`trackRequests`): the
route effects read `view.facets` and re-run when the facets request settles *after* a window change,
re-issuing every query on the same slots; on a slow ledger the in-flight ones are aborted and re-sent.
- Usage's `run()` read `view.paramsFor` untracked, so the effect tracked `facets` on every window.
- Overview's `paramsFor` was already untracked, so a plain change did not storm; with an exclude its
  guard `view.facets !== null` tracked every facet assignment and re-ran.

Fix: `src/lib/view.svelte.ts` records the `facetParams` key `facets` were loaded for and exposes
`view.facetsReady` (a `$derived`, so it flips only on a window change, not on every facet value).
`src/routes/+page.svelte` and `src/routes/usage/+page.svelte` gate on it; Usage reads `paramsFor`
inside `untrack`. The guard that waits for facets is kept. `src/lib/query.ts` default `maxConcurrent`
is now 4 (was 6); `src/lib/query.test.ts` updated to match.

**Regression specs.** `tests/e2e/overview.spec.ts`, `tests/e2e/usage.spec.ts`: query responses are
delayed 700 ms (a busy-ledger stand-in), then 30d→90d once; assert no repeated normalised
`/analytics/query` URL and that the total equals the page's distinct-query count (10 Overview, 7 Usage).

## Evidence

Failing first: with the fix reverted, Usage `switching 30d to 90d…` failed `expect(urls.length)
.toBe(new Set(urls).size)` — 10 requests, 7 distinct. Overview failed only with an exclude: 12
requests, 10 distinct.

Request counts, 30d→90d on the fixture e2e (700 ms `/query` delay), before → after:

| Page | before | after |
| --- | --- | --- |
| Overview (plain) | 10 requests / 10 distinct | 10 / 10 |
| Overview (`x.repo_id=r1`) | 12 requests / 10 distinct | 10 / 10 |
| Usage (plain) | 10 requests / 7 distinct | 7 / 7 |

- `npm test` (`.scratch/4-18-unit.log`): `Test Files 10 passed`, `Tests 74 passed`.
- `npm run build` (`.scratch/4-18-build.log`): success, `built in 6.01s`.
- `E2E_PORT=4418 npm run test:e2e`: `90 passed`, exit 0.

## Deviations from the brief

- The brief says Overview's plain 30d→90d stormed (17 requests, 5 superseded). On the fixture it does
  not — Overview already read `paramsFor` untracked; its storm reproduces only when an exclude makes
  the guard read `view.facets` (28/10). The Overview regression therefore uses `/?x.repo_id=r1` so it
  exercises the fixed path; the 30d→90d switch is as briefed.
- The brief's real-ledger totals (17 Overview, 14 Usage) are larger than the fixture's: the fixture
  emulation delays `/query` only, and its per-window distinct counts are 10 (Overview) and 7 (Usage).
- `maxConcurrent` was lowered 6→4 as instructed; 4-17 had raised it 3→6.
- "Distinct `/analytics/*` URL" is measured over `/analytics/query` only (the page's distinct-query
  count); `/analytics/summary` and `/analytics/facets` are not part of the repeat assertion.
- Tool turns exceeded the 40-turn budget (investigation, effect logging, before/after runs).

## Unfinished work

None.

## Contradictions between the brief and the contracts it cites

- Overview plain-change storm: the brief states it, the fixture contradicts it (needs an exclude) —
  named above, not resolved silently. No other contradiction; the Go store confirms the `cost_usd: 0`
  rule.
