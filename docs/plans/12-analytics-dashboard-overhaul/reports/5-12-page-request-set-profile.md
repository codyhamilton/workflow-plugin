# Report: 5-12 — Profile the page request sets on the large ledger

Status: done with concerns

## What changed (against each part of the brief)

One new file, `tools/workflow/internal/serve/analytics_pageset_test.go` (test-only; nothing else
touched).

- `TestAnalyticsPageSet` (env-gated on `WORKFLOW_BENCH_DIR`): copies `ledger.db` into a temp dir via
  the bench helpers (`openBenchCopy`, never opens the source), then issues exactly the Overview and
  Usage request sets for the 7d, 30d, 90d and All time presets: Overview sends one
  `/v1/analytics/summary` plus one `/v1/analytics/query` per spark measure (site `pickBucket`
  duplicated in `pagesetBucket`) plus the heatmap `/query` (`hook_events`, `dim=weekday&dim=hour_of_day`,
  `bucket=none`); Usage sends five by-model `/query` calls (`bucket=none&top=20`), `cost_usd` over
  time and `tokens_out` over time. Requests of one page load run with concurrency 4, each preset run
  5 times with the first run discarded; each distinct request carries p50 (`nearestRank`) and max.
  Results are `t.Logf` lines and, when `WORKFLOW_PAGESET_OUT` names a file, JSON (`requests`, plus
  `slowest` = slowest 8 distinct requests with `EXPLAIN QUERY PLAN` rows).
- `TestAnalyticsPageSetSmoke` (not gated): on the bench fixture it asserts the request list is
  non-empty and every request returns 200, so the file cannot rot.
- EXPLAIN helpers reproduce the store SQL for the slowest requests (`query.go` `measureDef.source`
  interior-rollup-plus-two-edge-hours union, `usage.go` `usageRowsWhere` CTE, `analytics.go` Summary's
  rollup union) and run `EXPLAIN QUERY PLAN` on the copied DB.

## Evidence

Failing/absent check first: `go test ./internal/serve -run TestAnalyticsPageSet -v -count=1` returned
`testing: warning: no tests to run` / `PASS` before the file existed. `go vet ./...` passed.

After, in `tools/workflow`:

| Check | Result |
| --- | --- |
| `go vet ./...` | pass (exit 0) |
| `go test ./internal/serve` | `ok ... 5.4s`; gated test skips |
| `WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local go test ./internal/serve -run TestAnalyticsPageSet -v -count=1` | PASS, 30.9 s (well under 10 min), 72 requests, 0 non-200 |

Gated run (run 2 of 2) against `/var/tmp/p4verify/data/local` (318 MB, purged compacted copy), tz UTC,
`to` = ledger max ts rounded up to the hour. Ranked by p50 (ms); the slowest 15 of 72:

| # | Page/preset | Request (params after `?`, from/to elided) | p50 | max | Plan summary |
| --- | --- | --- | --- | --- | --- |
| 1 | usage/all | `query bucket=week&measure=tokens_out` | 612.6 | 677.8 | base scan + dedupe |
| 2 | overview/all | `query bucket=week&measure=cost_usd` | 596.0 | 619.6 | base scan + dedupe |
| 3 | usage/all | `query bucket=none&dim=model&measure=unpriced_calls&top=20` | 590.4 | 622.9 | base scan + dedupe |
| 4 | usage/all | `query bucket=none&dim=model&measure=tokens_out&top=20` | 589.7 | 657.4 | base scan + dedupe |
| 5 | overview/all | `summary` | 572.3 | 624.6 | rollup interior + 2 edge seeks; usage CTE base scan |
| 6 | usage/all | `query bucket=none&dim=model&measure=cost_usd&top=20` | 567.0 | 591.0 | base scan + dedupe |
| 7 | usage/all | `query bucket=none&dim=model&measure=model_calls&top=20` | 562.3 | 620.0 | base scan + dedupe |
| 8 | overview/all | `query bucket=week&measure=unpriced_calls` | 562.2 | 667.8 | base scan + dedupe |
| 9 | overview/all | `query bucket=week&measure=tokens_in` | 557.8 | 592.6 | base scan + dedupe |
| 10 | usage/all | `query bucket=none&dim=model&measure=tokens_in&top=20` | 555.8 | 608.4 | base scan + dedupe |
| 11 | overview/all | `query bucket=week&measure=model_calls` | 554.1 | 589.3 | base scan + dedupe |
| 12 | usage/90d | `query bucket=none&dim=model&measure=unpriced_calls&top=20` | 521.9 | 552.8 | base scan + dedupe |
| 13 | overview/90d | `query bucket=day&measure=cost_usd` | 513.2 | 531.8 | base scan + dedupe |
| 14 | overview/90d | `summary` | 511.5 | 545.1 | rollup interior + 2 edge seeks; usage CTE base scan |
| 15 | overview/90d | `query bucket=day&measure=unpriced_calls` | 506.5 | 610.5 | base scan + dedupe |

Everything at 7d/30d is below 505 ms; the fast tail is `hook_events`/`conversations`/`artifact_versions`/
`distinct_content`/`commits` `/query` calls (0.4 to 158 ms) and the heatmap `hook_events` two-dim
`bucket=none` call (105 to 158 ms).

### The three slowest, classified by plan

1. **usage/all `tokens_out` `bucket=week` (612.6 / 677.8 ms)** — the time is in the **query**: the
   usage CTE (`usageRowsWhere`) plans as `SCAN facts USING INDEX facts_conv_page` over the whole base
   table plus `USE TEMP B-TREE` for the `ROW_NUMBER()` dedupe (`json_extract(raw,'$.backfill.ref')`,
   partition by conversation/id). No rollup table exists for usage measures, and the `ts` window is
   not driving an index seek, so it is a base-row scan, not a rollup read and not the two-hour edge
   path.
2. **overview/all `cost_usd` `bucket=week` (596.0 / 619.6 ms)** — same shape: `cost_usd` is a usage
   measure, so the same `SCAN facts USING INDEX facts_conv_page` + dedupe temp b-tree. Time is in the
   **query (base-row scan + dedupe)**.
3. **usage/all `unpriced_calls` `dim=model&bucket=none` (590.4 / 622.9 ms)** — same CTE, same plan.
   Time is in the **query (base-row scan + dedupe)**.

Nearest non-usage case, **overview/all `summary` (#5, 572.3 ms)**: its hook/conversations counts are
cheap — `SEARCH hook_events_hourly USING PRIMARY KEY (hour>? AND hour<?)` for the interior hours plus
two `SEARCH facts USING COVERING INDEX facts_type_ts` for the edge hours — so the rollup read and the
edge hours are **not** the cost. Its `summary.usage` statement plans exactly like the three slowest
above (`SCAN facts USING INDEX facts_conv_page` + dedupe), i.e. Summary's time is its usage CTE, the
same base-row read. (The screens and by-kind statements are not shown.)

Takeaway for 5-13: the slow calls are base-row reads over `facts` (the usage dedupe CTE in
particular) on the All time window, and they are not served by any rollup. Order varies run to run by
about 5 to 10 % (run 1 had `overview/all summary` first at 646 ms); the plan is identical across the
usage-measure requests.

## Deviations from the brief and their reasons

- **All time is a 399-day window, not `all=1` on `/query`.** The brief's parenthetical says "All time
  on `/query` is `all=1`; on other routes a 399-day window." The pages do not do this: both
  `+page.svelte:74-95` and `usage/+page.svelte:44-71` resolve All time through `resolveWindow(...,
  'rest')` and then delete `all` and set explicit `from`/`to` on the `/query` params too. The test
  follows the code (the goal is to time what the pages actually request) and flags the contradiction;
  see "Contradiction" below.
- **The site's `now` is stood in by the ledger's max ts rounded up to the hour, tz UTC.** The pages
  use the browser clock and `Intl` tz; a wall-clock window on a ledger whose last fact is old would
  profile empty windows. Max-ts keeps the copied data inside the windows and matches the bench's
  convention. Params otherwise match (`tz`, RFC3339 `from`/`to`; the site's `.000Z` is accepted by
  `parseFilter`'s `time.RFC3339`).
- **The EXPLAIN rows are representative SQL, not captured from execution.** The store exposes no SQL
  hook and this file may not edit non-test code, so `pagesetDef.source`, `pagesetUsageExplain` and
  `pagesetSummaryExplain` mirror the store's SQL verbatim for the slow requests. Plan shapes are what
  the live statements produce; only the requests' own filters are absent, and the pages' plain loads
  send none.

## Contradiction

The brief (line 15) says All time on `/query` is `all=1`. The two pages it names clamp to a 399-day
`from`/`to` for All time on every route, including `/query` (comments at `+page.svelte:75-77` and
`usage/+page.svelte:42-43` say so explicitly). Recorded, not silently resolved: the test profiles the
clamped window.

## Unfinished / for 5-13

- All time (and to a lesser extent 90d) on the usage measures exceeds 500 ms p50 because the usage
  CTE scans base rows; there is no usage rollup. 7d/30d are inside budget.
- `summary` is over budget only on All time, and its cost is the same usage CTE plus the screens and
  by-kind statements (not separately measured here).
- Nothing was fixed, per the brief.

## Known problems / limits

- Timing has run-to-run variance (about 5 to 10 %); the report uses the last run. Rank order near the
  top is not stable, the plan classification is.
- `t.TempDir` copies only `ledger.db` (as `openBenchCopy` does); a source with un-checkpointed WAL
  content would not be seen. The target copy has none.
- No non-trivial bug was found outside the done evidence.
