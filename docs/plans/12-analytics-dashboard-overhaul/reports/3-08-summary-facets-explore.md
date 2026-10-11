# 3-08 — Summary usage totals, facets models and norm events, Explore without a full sort

Status: done with concerns

## What changed
- `store.Summary` (`internal/store/analytics.go`): adds `ModelCalls`, `UnpricedCalls` (int), `TokensIn/Out/CacheRead/CacheWrite/Reasoning` (int) and `CostUSD` (float), summed from 3-05's `usageKeptRows` (Claude dedupe) via `Cost`. Existing fields unchanged.
- `store.Facets`: adds `Models`, `NormEvents` — sorted distinct, in-window, non-empty (empty values excluded, unlike `repo_id`).
- `store.Explore`/`ExploreRow`: rows gain `NormEvent`, `Model`, `CostUSD *float64` (pointer so a non-usage row omits it, a usage row keeps even 0). Facts leg is now `FROM facts ... ORDER BY ts DESC, row_hash ASC LIMIT limit+1`; rejections are `ORDER BY at DESC, id ASC LIMIT limit+1`; the two sorted lists merge in Go with the old tie rule (facts before rejections at the same instant, ascending key) and cut at `limit+1`. The screens verdict is no longer a correlated subselect in the scan: `fillVerdicts` looks up the latest verdict by `content_hash` for the page's rows only.
- `serve` handlers `analyticsSummary`/`analyticsFacets`/`analyticsExplore` emit the new keys (`model_calls`, `unpriced_calls`, `cost_usd`, `tokens_*`; `models`, `norm_events`; `norm_event`, `model`, `cost_usd`).
- Tests: new store tests `TestAnalyticsSummaryUsage`, `TestAnalyticsFacetsModels`, `TestAnalyticsExploreCap` (5 facts + 2 rejections, limit 3, compared to a brute-force old-ordering SQL sort), `TestAnalyticsExploreUsageRow`, `TestAnalyticsExploreFactsPlan` (EXPLAIN). Serve summary/facets subtests assert the new keys; the explore column set gains `norm_event` and `model`.

## Checks
- Before: `go test ./internal/serve ./internal/store` ok; `gofmt -l` empty; `go vet` empty.
- After: `go test ./internal/serve ./internal/store` → both ok (serve 3.112s, store 1.706s); `gofmt -l` empty; `go vet` empty.
- EXPLAIN plan for the facts leg, logged by `TestAnalyticsExploreFactsPlan`:
```
SEARCH facts USING INDEX facts_ts (ts>? AND ts<?)
USE TEMP B-TREE FOR LAST TERM OF ORDER BY
```
No whole-window `USE TEMP B-TREE FOR ORDER BY`. No index hint needed.

## Deviations
1. The serve explore test's exact per-row column assertion had to gain `norm_event` and `model`. The brief says existing tests pass "unchanged in expectation", but the design mandates two always-present columns, so the existing check cannot pass unmodified. Minimal edit: added exactly those two names to `cols`; all existing keys, values and the 16-row count are unchanged.
2. Summary applies the caller's filter verbatim to the usage (kept) rows, including non-usage dimensions such as `kind`, rather than clearing them as a measure query does. The brief says cost over "kept rows" without specifying; summary is not a measure request, so `ignored_filters` does not apply. Tests use a window-only filter.

## Contradictions
1. Brief: existing tests unchanged in expectation vs. design: `explore` gains `norm_event`/`model`/`cost_usd`. The serve explore test asserts an exact per-row column set, so the two always-present columns force a test edit (deviation 1). The store explore test checks fields individually and was not changed.
2. Design: Explore "applies its cap without sorting the whole window first." SQLite still emits `USE TEMP B-TREE FOR LAST TERM OF ORDER BY` for the `ts DESC, row_hash ASC` tie: no existing index provides `(ts DESC, row_hash ASC)` (all are ts-ascending; `row_hash` is a separate unique autoindex). It does not sort the whole window, only the ts tie rows, and the surviving text is not the whole-window `USE TEMP B-TREE FOR ORDER BY`. A new `facts(ts DESC, row_hash ASC)` index would remove it; that index is outside this brief's owned paths.

## Unfinished
None.
