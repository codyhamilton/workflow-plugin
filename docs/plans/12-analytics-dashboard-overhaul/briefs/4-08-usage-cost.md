# Brief: 4-08 — Usage & cost: cost by model, tokens, and unpriced calls shown explicitly

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/usage/+page.svelte` (new), `tests/e2e/usage.spec.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-08-usage-cost.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-06, 4-07, 4-09 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4408`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 8 files to read, about 300 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": the Usage & cost view; and the Phase 4 outcome "Usage & cost shows cost by model".
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/format.ts` (`costLabel`, `num`), `src/lib/charts/BarChart.svelte` and `TimeChart.svelte` (4-04) — exports and props only.
3. `tests/e2e/fixture.ts` — `USAGE_ALL`, `USAGE_BY_MODEL`, `USAGE_C5` (4-03).
4. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — Phase 3 Carried items 1 and 7.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A reader sees what usage cost, by model and over time, and can tell at a glance which calls had no price.

## Contract

- Cost is 0 for unpriced models (`tools/transcript/pricing.json` holds seven Cursor-class models; 74% of local calls in the last 30 days are unpriced). The page never shows `$0.00` for a model or window with unpriced calls: it shows `costLabel({cost, unpriced, calls})`, and states "N of M calls are unpriced" (`data-testid="usage-unpriced-banner"`, absent when N is 0).
- Measures (`/query`, all take `model`, `harness`, `repo_id`, `conversation_id` dims): `cost_usd`, `model_calls`, `unpriced_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`. Check the dims per measure in `analytics/schema`.
- Latency: the benchmark's slowest cases are usage measures over `all` (463 to 483 ms). Do not issue more than the queries listed under Changes, let the client's three-at-a-time queue and cache work, and for `all` use a `week` or `month` bucket (`pickBucket`).
- Claude message dedupe covers backfilled rows only (Carried item 7): add one line under the table, "Claude calls captured live may be counted more than once", as a footnote (`usage-footnote`).
- Drill-down: clicking a model bar or table row calls `view.drill('model', name, ev)`; shift excludes. `__other__` is not clickable.

## Changes

New `usage/+page.svelte`. Queries (slots `usage-by-model-cost`, `-calls`, `-unpriced`, `-tokens`, `usage-over-time`):
1. `cost_usd`, `model_calls`, `unpriced_calls` each with `dim=model`, `top=20`, `bucket=none`; `tokens_in` and `tokens_out` with `dim=model`. Join by model into one table: model, calls, unpriced, tokens in, tokens out, cost (`costLabel`). Test ids: `usage-row-<model>` and `usage-<model>-calls`, `-unpriced`, `-tokens_in`, `-tokens_out`, `-cost`.
2. `BarChart` `testid="usage-cost-by-model"`: priced cost by model; a model with cost 0 and unpriced calls gets the label `<model> (unpriced)` and an inert row.
3. `TimeChart` `testid="usage-over-time"`: `cost_usd` with `dim=model`, stacked, bucket from `pickBucket`; and a second `TimeChart` `testid="usage-tokens-over-time"` for `tokens_out` with no dim (slot `usage-tokens-over-time`). Total queries on the page: seven (five by model, two over time).
Write `usage.spec.ts` against `USAGE_BY_MODEL`: the priced Sonnet model's row shows its hand-counted cost; the local qwen and Claude opus rows show `unpriced` and never `$0`; the banner reads the hand-counted N of M; `?model=…` narrows the table; clicking a cost bar adds a `model` chip and shift-click adds an exclude chip (`clickBar`); `__other__` is inert (use a `page.route` fulfilling `analytics/query` with an `__other__` row); with only unpriced calls in the window (`harness=claude`) no element contains `$0`; the 1 s timing assertion.

## Done evidence

Write the failing `usage.spec.ts` first and report its output before the page exists and after.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- usage.spec.ts` → all pass.
- `trackRequests(page, /analytics\/query/)` reports seven requests for one load, none per model.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
