# 3-13 — Phase 3 outcome check: benchmark, routes, cost fixture and the Playwright suite

Status: **done**

Every bullet of the Phase 3 Outcome was checked once, on the final code (after 3-12, 3-14, 3-15, 3-16, 3-17), with the command and the number.

## Outcome bullet / command / result

| # | Outcome bullet | Command | Result | Pass |
|---|---|---|---|---|
| 1 | Benchmark p95 < 500 ms, every case, on the compacted copy | full `TestAnalyticsBench` (below) | **2063 cases, 0 over 500 ms, 0 non-200**, worst 463.5 ms (`series/90d`), 20m16.8s | pass |
| 2 | `schema` matrix; unsupported pairing is 400 | `go test ./internal/serve -run 'TestAnalyticsSchema\|TestAnalyticsQuery$' -v` | 15 measures match the matrix; `unsupported dimension tool for conversations`/`model_calls` → 400 | pass |
| 3 | `kind` filter on a `hook_events` query in `ignored_filters` | `TestAnalyticsQuery/ignored_filters` + store `TestQueryIgnoredFilters` | `ignored_filters = ["kind"]` | pass |
| 4 | `cost_usd` equals the hand-computed value; Codex fresh input only | `go test ./internal/store -run TestUsageMeasures -v` | `cost_usd = 0.2504` | pass |
| 5 | Existing Playwright suite passes | `cd packages/workflow-analytics && npm run test:e2e` | **26 passed (19.2s)**, exit 0, 0 failures | pass |
| 6 | Go tests: `query`, `conversation`, keyset past page one, `tz` sub-day, top-N | `go test ./internal/store ./internal/serve … -v` (table below) | all PASS | pass |

## Bullet 1 — benchmark

Command, exactly as 3-11 (same env, same copy; run alone, detached, polled):

```
cd tools/workflow && \
WORKFLOW_BENCH_DIR=/var/tmp/workflow-compact-copy/data/local \
WORKFLOW_BENCH_OUT=/var/tmp/workflow-compact-copy/bench-3-13.txt \
PATH=$HOME/.local/go/bin:$PATH \
go test ./internal/serve -run 'TestAnalyticsBench$' -v -timeout 40m
```

- Copy check: `/var/tmp/workflow-compact-copy/data/local/ledger.db` present, `select count(*) from facts` = **450510**. Unchanged (read-only).
- Log: `/var/tmp/workflow-compact-copy/bench-3-13.log` — `analytics_bench_test.go:85: benchmark: 2063 cases, 20m16.805s elapsed`; `--- PASS: TestAnalyticsBench (1223.20s)`.
- Result artifact: `/var/tmp/workflow-compact-copy/bench-3-13.txt`, 2063 data rows, every `status=200`, **none over 500 ms**.
- Worst ten (p95 ms): `series/90d` 463.5, `series/30d` 453.0, `query/cost_usd/dims=conversation_id/bucket=none/all` 450.7, `query/tokens_out/dims=hour_of_day+weekday/bucket=none/all` 447.0, `query/tokens_in/dims=conversation_id+weekday/bucket=none/all` 446.3, `query/cost_usd/dims=hour_of_day+weekday/bucket=none/all` 445.7, `query/cost_usd/dims=repo_id+hour_of_day/bucket=none/all` 445.0, `query/tokens_out/dims=harness+hour_of_day/bucket=none/all` 444.9, `query/tokens_reasoning/dims=conversation_id+weekday/bucket=none/all` 444.6, `query/tokens_reasoning/dims=repo_id+model/bucket=none/all` 444.3.
- Every prior miss (hook_events 152, conversations 80, facets, summary, scores) is now under the bound: the rollups from 3-12/3-14/3-15 hold.

## Bullets 2, 3, 4, 6 — named test pass lines (verbatim)

```
--- PASS: TestAnalyticsSchema (0.02s)
--- PASS: TestAnalyticsQuery (0.02s)
    --- PASS: TestAnalyticsQuery/errors (0.00s)          # 400 unsupported pairing
    --- PASS: TestAnalyticsQuery/ignored_filters (0.00s) # ["kind"] for hook_events
    --- PASS: TestAnalyticsQuery/top (0.00s)
    --- PASS: TestAnalyticsQuery/tz (0.00s)
--- PASS: TestQueryUnsupportedDim (0.01s)
--- PASS: TestQueryIgnoredFilters (0.01s)
--- PASS: TestQueryTopNSum (0.01s)
--- PASS: TestQueryTopNDistinct (0.02s)
--- PASS: TestQuerySydneyTZ (0.01s)
--- PASS: TestUsageMeasures (0.01s)
ok  	…/internal/store	0.069s
ok  	…/internal/serve	0.047s
```

**Bullet 4 hand-computed value.** `TestUsageMeasures` (fixture `usage_test.go`) asserts `cost_usd == 0.2504` (line 76), derived at line 75 as **Codex 0.0004 + OpenCode 0.25 = 0.2504** (Claude is unpriced, adds 0). The Codex fixture (line 35) is `in=1000, cache_read=400`; per lines 33-34 the fixture's `input_tokens` already include cached input, so **the Codex fixture charges fresh input only**: `fresh = 1000 − 400 = 600`, giving `(600×0.6 + 400×0.1)/1e6 = 0.0004`. Same rule asserted directly by `TestCostCodexNoDoubleCharge` (`pricing_test.go:44`).

| Bullet 6 behaviour | Test |
|---|---|
| `query` (measure × dim matrix) | `TestAnalyticsQuery` (serve), `TestQueryEveryMeasure` (store) |
| `conversation` route | `TestConversationRouteFields`, `TestConversationRouteDedupe` (serve) |
| keyset paging past page one | `TestExecutionsPage`, `TestConversationsPage` (store) |
| `tz` bucketing of a sub-day fixture | `TestQuerySydneyTZ` (store), `TestAnalyticsQuery/tz` (serve) |
| top-N folding to `__other__` | `TestQueryTopNSum`, `TestQueryTopNDistinct` (store), `TestAnalyticsQuery/top` (serve) |

## Carried items 1 to 5 — what closes each

1. Cached input not double-charged → `TestCostCodexNoDoubleCharge` (`pricing_test.go:44`) and the Codex fixture (`usage_test.go:33-35`, fresh = 1000−400).
2. OpenCode reported cost of 0 treated as not reported → `TestCostReportedZeroFallsToTokens` (`pricing_test.go:34`).
3. Repeated Claude `message_id` dedupe → `TestUsageClaudeDedupeKeepsLargestOut` (`usage_test.go:102`), reused by summary/conversation.
4. Tool/source reads off `json_extract` → `TestAnalyticsColumnReads` (`analytics_test.go:453`); no `json_extract` on `payload` remains.
5. Collapse survivor `ts` (first-arriving rule) → `TestCollapseSurvivorFirstArrival` (`compact_test.go:440`).

## Done evidence

```
# cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go build ./... && go vet ./... && go test ./...
exit 0 / exit 0 / exit 0
ok  	…/tools/workflow/internal/archive	(cached)
ok  	…/tools/workflow/internal/compact	(cached)
ok  	…/tools/workflow/internal/ingest	(cached)
ok  	…/tools/workflow/internal/serve	(cached)
ok  	…/tools/workflow/internal/store	(cached)
ok  	…/tools/workflow/cmd/workflow	53.110s
   … 14 packages, all ok.
```

```
# cd packages/workflow-analytics && npm run test:e2e
26 passed (19.2s)   exit 0
```

## Deviations from the brief, with reasons

1. **First bullet-1 run was contaminated.** It was launched in parallel with the Playwright build, `go test ./...` and the named tests (the orchestrator ran checks concurrently on a 12-core host). It reported 2 near-threshold misses: `series/30d` 511.0 ms and `series/90d` 538.8 ms (3-11 alone recorded 458.2/458.5). A quiet filtered rerun (`WORKFLOW_BENCH_FILTER=series`) gave `series/90d` 472.6 ms, and the **clean full rerun reproduced by the evidence above passed all 2063 cases**. The contaminated artifacts are kept as `bench-3-13-contended.txt`/`.log`; the committed numbers are the clean run.
2. **`series` is the tightest route.** It was 458 ms in 3-11 and ~453-464 ms here; no Phase 3 unit owns it. It passes but has ~40 ms of headroom.
3. No source changes; only this report is committed.

## Contradictions between this brief and the contracts it cites

None found. The design's "rollups are conditional" holds (they were added only where the benchmark missed); edge hours are read from base rows; compaction rebuilds every rollup (3-17).

## Known problems

- Inherited, not new, and outside this brief: `Append` now issues 8 rollup upserts per inserted fact (ingest write amplification, unmeasured); an `open` that commits `user_version=8` but crashes before the facet backfill leaves an empty `facets_hourly` treated as authoritative (migrations 6/7 share the window); live-captured Claude facts carry no stored `message_id`, so repeats among them are not deduped. No non-trivial bug was found by this brief.
