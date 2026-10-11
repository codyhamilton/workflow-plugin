# Brief: 4-17 — Fix the three defects Phase 4 verification found on the real ledger

Consumer: a TypeScript worker (flash-tier). A fixer after 4-16; the defects were measured by a browser check against the compacted, purged real-ledger copy.
Owned paths: `packages/workflow-analytics/src/routes/+page.svelte`, `src/routes/usage/+page.svelte`, `src/lib/charts/BarChart.svelte`, `src/lib/charts/DataTable.svelte`, `src/lib/query.ts`, `src/lib/query.test.ts`, `tests/e2e/overview.spec.ts`, `tests/e2e/usage.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-17-fix-verification-defects.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit. Do not use `/tmp`; use `.scratch/` inside the repo for scratch files.
Depends on: 4-16.
Runs alongside: nothing.
Budget: 8 files to read, about 120 lines to write, 40 tool turns. Past the budget, stop and report `over budget`.

Run npm commands from `packages/workflow-analytics`. The Go API is read-only here.

## Required reading, in order

1. `DESIGN.md` — "Domain: Dashboard site" (the `costLabel` rule: cost is never shown as `$0` for unpriced calls) and the Phase 4 outcome bullet on 1 s interactions.
2. `src/routes/trends/+page.svelte` lines 50 to 82 — the All time clamp that already works.
3. `src/routes/+page.svelte` (sparkline queries near line 72) and `src/routes/usage/+page.svelte` (`bucket` near line 41, `costRows` near line 94).
4. `src/lib/buckets.ts`, `src/lib/params.ts` (`resolveWindow`), `src/lib/cost.ts` (`costLabel`), `src/lib/query.ts` (`maxConcurrent`).
5. `src/lib/charts/BarChart.svelte` and `DataTable.svelte` — how the `unit` reaches the table cells.

## Goal

On the real ledger: All time on Overview and Usage never sends a `/query` the server rejects with 400, the cost-by-model table never shows a bare `0` or a long float for cost, and Overview and Usage settle inside 1 s after a preset change.

## Defects (symptom, location, cause)

- **A. All time sends 400s.** Overview sends 9 sparkline `/query?all=1&bucket=month` and Usage sends 2 (`cost_usd` by model and `tokens_out`); the server answers 400 "range too wide" (about 680 month buckets over the 400 cap). The failure is silent, so the sparklines and time charts are empty. Trends avoids it by using the 399-day `rest` window with explicit `from` and `to` when `all` comes back from `resolveWindow(..., 'query')`.
- **B. Cost shown as raw numbers.** The Usage cost-by-model chart table shows `0` for an unpriced model and `6.300488369999988` for a priced one: the data-table does not format values through the unit.
- **C. Too slow.** On the big copy a 30d to 90d change on Overview takes about 1.2 s (12 requests) and on Usage about 1.2 s (8 requests); the slowest call is about 455 ms. The client runs at most 3 requests at once, so the rest queue.

## Changes

1. A: in Overview and Usage, when the window resolves with `all`, build the query window the way Trends does (the 399-day clamp, `from` and `to` set, `all` deleted) and pick the bucket from that window with `pickBucket`; the "limited to the last 399 days" notice already shows on these routes, keep it. Do not duplicate the logic a third time: add one exported helper in `src/lib/params.ts`'s neighbour that you own only if needed; otherwise inline in your two routes (you may not edit `params.ts`, so inline).
2. B: the data table formats numeric cells by the chart `unit`: `usd` through `costLabel` semantics (an unpriced row stays text "unpriced", never `$0`; priced rows to cents), `tokens` and `count` with thousands separators. Rows keep their exact values in a `data-value` attribute so tests can read numbers.
3. C: raise the client default `maxConcurrent` from 3 to 6 and update its test. Then measure on the fixture: a preset change on Overview and on Usage settles inside 1 s in the e2e timing assertions that already exist; if the real-ledger number is still over 1 s, report it plainly rather than claiming it fixed.

## Done evidence

Write failing specs first and report their output before and after.

- `overview.spec.ts`: choose All time; every `/analytics/query` request carries `from` and `to`, none carries `all=1`, and none answers 400 (assert on responses).
- `usage.spec.ts`: the same for Usage; and the cost-by-model table cell for the unpriced model reads "unpriced", the priced one reads a dollar amount to cents, with `data-value` holding the exact number.
- `npm test`, `npm run build` and `E2E_PORT=4417 npm run test:e2e` all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. What changed, the check output before and after, every deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers.
