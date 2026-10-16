# Brief: 2-01 — Distribution read

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `tools/workflow/internal/store/distribution.go`; `tools/workflow/internal/store/distribution_test.go`; `tools/workflow/internal/store/percentile.go`; `tools/workflow/internal/serve/analytics_distribution.go`; `tools/workflow/internal/serve/analytics_distribution_test.go`; `tools/workflow/internal/serve/serve.go` (register `GET /v1/analytics/distribution` only); `tools/workflow/internal/serve/analytics_bench_test.go` (distribution bench cases and smoke route coverage for `distribution/`). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-01-distribution-read.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: `2-05-conversation-window` (disjoint paths).
Budget: 12 files to read, about 450 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Analytics reads, bullet **`GET /v1/analytics/distribution`**, and Phase 2 outcome bullets on the distribution fixture.
2. `tools/workflow/internal/store/usage.go` — `usageRowsWhere` and `usageValue` (call identity and measures).
3. `tools/workflow/internal/serve/reads.go` — `percentile` in serve (store must match the same algorithm; implement in `store/percentile.go` for reuse by score-series).
4. `tools/workflow/internal/serve/analytics.go` — `parseFilter`, `tooWide`, `errJSON`, handler JSON patterns.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The tenant read API exposes `GET /v1/analytics/distribution` with the design’s measure, grain, dimension, filter, bin, and percentile semantics, backed by store logic the smoke bench can call at 200.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Domain: Analytics reads, **`GET /v1/analytics/distribution`**. Settled:

- `measure` required: one of `cost_usd`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`; unknown → 400 `{"error":"unknown measure <m>"}`.
- `grain` is `call` (default) or `conversation`; unknown → 400 `{"error":"unknown grain <g>"}`.
- `dim` omitted or `model`; any other → 400 `{"error":"unsupported dimension <d> for <measure>"}`.
- Call grain: one value per model call in the window (same call identity as `model_calls` / `usageRowsWhere`). Conversation grain: one value per conversation, sum of the measure over its calls; conversation `model` is the most frequent model on those calls, ties to smaller name, `""` when none (same rule as the conversation list).
- For `cost_usd`: `n` is priced calls, `unpriced` is the rest; percentiles and bins use priced calls only. Token measures: `unpriced` is 0; every call is in `n` and bins.
- Filters: `repo_id`, `harness`, `model`, `conversation_id` apply. `kind`, `plan`, `norm_event`, `event`, `tool`, `source` ignored and listed in `ignored_filters`.
- Response shape: `{"measure","grain","dim","rows":[{"k","n","unpriced","min","p25","median","p75","p95","max","bins":[{"lo","hi","n"}]}],"truncated"?,"ignored_filters"?}`. `k` is the model or `"all"` when `dim` omitted. `top` defaults 20, max 100, rows ordered by `n` desc. No `__other__` row. `truncated` true when keys were dropped.
- Percentiles: same method as `/scores` — sorted values, position `(n-1)*q`, linear interpolation. Cost rounded to 6 decimal places; token measures to 1 decimal.
- Bin edges fixed (tokens: zero bin; `[2^i, 2^(i+1))` for i 0–19; overflow at `2^20`. Cost: zero bin; `(0, 10^-4)`; `[10^i, 10^(i+1))` for i -4 through 1; overflow at `100`. `lo` inclusive, `hi` exclusive; overflow bin has no `hi`.
- Scans existing columns; no hourly rollup; no `partial`. Wider than 400 UTC days → 400 `{"error":"range too wide"}` (reuse `parseFilter` / `tooWide` like other analytics GETs).

## Changes

- Add `store/percentile.go` with the `/scores` interpolation method and rounding helpers used by distribution (and later score-series).
- Implement `Tenant.Distribution` (or equivalent) in `distribution.go` using `usageRowsWhere` for call grain; conversation grain aggregates kept calls per `conversation_id` then applies the model rule.
- Handler validates query params, applies `parseFilter`, maps ignored dimensions into `ignored_filters`, enforces `top`, writes JSON.
- Store tests (`TestDistribution*`): fixture proving (1) cost row with priced vs unpriced split on bins/percentiles, (2) token row with `unpriced` 0, (3) two models sharing fixed cost bin edges, (4) more than `top` models sets `truncated` with no `__other__`.
- Serve tests mirror 400 cases and one 200 shape check.
- Register route in `serve.go`. Extend `buildBenchCases` with `distribution/<preset>` per servable preset (at least `measure=cost_usd&grain=call` and one token measure). Extend `TestAnalyticsBenchSmoke` route list to require a `distribution/` case.

### Keep untouched

Existing routes, `ExecutionsPage`, `ConversationsPage`, `Conversation`, and `/query` behavior. Do not edit `analytics.go` except if unavoidable — prefer new handler file.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `go test ./internal/store/ -run TestDistribution -count=1` from `tools/workflow` → passes, including cost unpriced exclusion and truncated-without-`__other__` assertions.
- `go test ./internal/serve/ -run 'TestDistribution|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow` → passes; smoke includes a `distribution/` case at 200.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
