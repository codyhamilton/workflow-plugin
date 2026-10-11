# Brief: 4-06 — Overview: KPI tiles with sparklines and the hour-by-weekday heatmap

Consumer: a Svelte 5 worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/routes/+page.svelte`, `tests/e2e/overview.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-06-overview.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-05 (and so 4-01 to 4-04).
Runs alongside: 4-07 to 4-15 (each owns its own route directory and spec). The e2e suite binds a fixed port: run it with your own `E2E_PORT` (for example `E2E_PORT=4406`) if another worker runs at the same time, ideally in a separate git worktree.
Budget: 8 files to read, about 250 lines to write, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site", the Overview bullet (KPI tiles with sparklines including cost and tokens; hour-of-day × weekday heatmap) and the cost rule.
2. `src/lib/view.svelte.ts` (4-05), `src/lib/query.ts` (4-01), `src/lib/format.ts` (`costLabel`), `src/lib/buckets.ts` (4-02) — exports only.
3. `src/lib/charts/Sparkline.svelte` and `Heatmap.svelte` (4-04) — props at the top of each file.
4. `src/routes/+page.svelte` and `tests/e2e/overview.spec.ts` — the test ids and numbers the old page and spec use; and `tests/e2e/fixture.ts` constants `SUMMARY_ALL`, `SUMMARY_R1`, `USAGE_ALL`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Overview shows the window's headline numbers, each with a sparkline, and the activity heatmap, and honours the shared window and filters.

## Contract

- Totals come from one `summary` request per window (`view.paramsFor('rest')`; `summary` has `conversations`, `hook_events`, `artifact_versions`, `distinct_content`, `commits`, `model_calls`, `unpriced_calls`, `cost_usd` and token sums). Distinct counts such as `conversations` do not add across buckets, so a total is never the sum of a sparkline.
- Sparklines are `/query` requests (`view.paramsFor('query', {measure, bucket})`), one per tile, bucket from `pickBucket(from, to, tz, ['hour','day','week','month'])`. They go through the client so at most three run at once. Do not issue a request per repo or per conversation.
- Phase 3 latency headroom is small (worst case 463 to 483 ms on usage measures over `all`). With `all` selected the sparklines use `week` or `month` and the totals show the `notice-clamped` notice from the shell.
- Cost tile: text is `costLabel({cost: cost_usd, unpriced: unpriced_calls, calls: model_calls})`. It never renders `$0.00` when `unpriced_calls > 0`. A second tile `summary-unpriced_calls` shows the count of unpriced calls. Tokens tile shows `tokens_in + tokens_out` and the cache-read figure.
- Heatmap: `measure=hook_events`, `dim=weekday`, `dim=hour_of_day`, `bucket=none`, `Heatmap` with `testid="overview-heatmap"`. Rows come back as `{k: [weekday, hour], v}`; weekday semantics are in `tools/workflow/internal/store/query.go`. Heatmap cells are not clickable (neither is a filter key).
- Unchanged: the `summary-<id>` test ids for the tiles the old page had (same numbers for the same window).

## Changes

Rewrite `+page.svelte` on `view` and the client. Slots: `overview-summary`, `overview-spark-<measure>`, `overview-heatmap`. Ignore `Superseded`; call `setError` for anything else and `clearError` on success. Tiles: conversations, hook_events, artifact_versions, distinct_content, commits, model_calls, tokens, cost, unpriced_calls. Rewrite `overview.spec.ts`: keep the old assertions on `summary-*` numbers (now from the recounted fixture), add cost and unpriced tiles (`USAGE_ALL`: the cost tile shows the priced total together with the unpriced note, and a window containing only the unpriced call shows `unpriced`, not `$0.00`, via `?harness=claude&range=…` or a `page.route` that fulfils `analytics/summary` with `cost_usd: 0, model_calls: 3, unpriced_calls: 3`), the heatmap is ready (`data-ready="true"`), a repo filter changes the tiles, and the 1 s timing assertion from preset click to `expectSettled`.

### Keep untouched

The `summary-<id>` ids and the numbers they assert for the same inputs.

## Done evidence

Run the old `overview.spec.ts` first against the new page and report which tests fail before you rewrite it.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- overview.spec.ts` → all pass, including the cost and heatmap tests and the timing assertion (under 1,000 ms from click to settled).
- `trackRequests(page, /analytics\/(summary|query)/)` shows no more than one `summary` and ten `query` requests for one page load, and none per repo.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
