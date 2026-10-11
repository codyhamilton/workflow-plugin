# Brief: 3-08 — Summary usage totals, facets models and norm events, Explore without a full sort

Consumer: a Go worker (flash-tier); the dashboard overview and explore views read these.
Owned paths: `tools/workflow/internal/store/analytics.go` (only `Summary`, `Facets`, `Explore`, their row types), `analytics_test.go`, `tools/workflow/internal/serve/analytics.go` (only `analyticsSummary`, `analyticsFacets`, `analyticsExplore`) and `analytics_test.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-08-summary-facets-explore.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-05, 3-07.
Runs alongside: 3-09.
Budget: 6 files to read, about 250 lines to change, 50 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Existing routes** and **Paging** bullets (binding).
2. `tools/workflow/internal/serve/analytics.go` lines 212-262, 465-497 — facets, summary and explore handlers.
3. `tools/workflow/internal/store/analytics.go` — `Facets`, `Summary`, `Explore`, `ExploreRow`.
4. `tools/workflow/internal/store/usage.go` (3-05) — the call-selection helper and the tokens and cost code; `store/pricing.go` `Cost`.
5. `tools/workflow/internal/serve/analytics_test.go` — the current summary, facets and explore tests; `packages/workflow-analytics/tests/e2e/overview.spec.ts` (read only) for retained shapes.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The three existing routes carry the new fields and Explore stops sorting the whole window, all with unchanged existing fields.

## Contract

Design, cited: "`hook_events` counts a collapsed part once; removed events disappear; `summary` gains `model_calls`, `cost_usd` and `tokens_*`; `facets` gains `models` and `norm_events`." and "Explore applies its cap without sorting the whole window first. Explore columns gain `norm_event`, `model` and `cost_usd`."

Settled by this brief:
- `summary` adds `model_calls` (int), `cost_usd` (float, from 3-05's cost over kept rows), `unpriced_calls` (int) and the flat keys `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning` (the design's `tokens_*`, named as the measures are). Existing keys and values stay.
- `facets` adds `models` and `norm_events` (sorted distinct, in-window, non-empty strings).
- `explore` rows gain `norm_event`, `model`, `cost_usd` (`cost_usd` only for usage rows via `Cost`, else omitted; keep the existing keys). Replace `ORDER BY ts DESC, k ASC LIMIT ?` over the `UNION ALL` of the whole window with: take `limit+1` from facts using `ORDER BY ts DESC, row_hash ASC LIMIT limit+1` (index `facts_ts_harness_event` or `facts_type_ts`; pick by `EXPLAIN QUERY PLAN`) and `limit+1` from rejections by `at DESC, id` separately, then merge the two sorted lists in Go with the existing tie rule (facts before rejections at the same instant; ascending stable key), and cut at `limit+1`. The result and truncation flag equal the old query's.
- The `screens` subselect for verdict stays but only runs on the final page's rows: select the page first, then look up verdicts by `content_hash` for those rows.

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve ./internal/store` passes with the existing tests unchanged in expectation.
- New tests: summary on the 3-05-style usage fixture returns hand-computed `model_calls`, `tokens_out` (deduped) and `cost_usd`; facets lists the fixture's models and norm events; explore with `limit=3` over 5 facts and 2 rejections equals the first 3 of the old ordering (compare against a brute-force sort in the test), `truncated` true; an explore row for a usage fact shows `model`, `norm_event` and `cost_usd`.
- `EXPLAIN QUERY PLAN` for the Explore facts leg is logged by a test and does not contain `USE TEMP B-TREE FOR ORDER BY` (assert on it; if SQLite insists on a temp b-tree for the filtered shape, report the plan and the filter that caused it).
- `go vet` and `gofmt -l` print nothing for both packages.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
