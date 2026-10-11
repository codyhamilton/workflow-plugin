# Report: 3-17 — Compaction rebuilds every rollup

Status: **done**

## What changed

- `store/rollup.go`: added `RebuildConversationRollup` (`conversations_hourly` / `convRollupFill`),
  `RebuildFacetRollup` (`facets_hourly` / `facetRollupFill`), each mirroring `RebuildHookRollup`
  (guard → `BeginTx` → `DELETE` → `ExecContext(fill)` → `Rollback` on error / `Commit`), and
  `RebuildRollups`, the single registration point that calls the three in order and returns the
  first error.
- `compact/compact.go`: the deferred step now calls `t.RebuildRollups(ctx)` instead of
  `RebuildHookRollup`; comment updated to "every rollup".
- `store/rollup_test.go`: `exceptBothWays` helper; `TestRebuildConversationRollup`,
  `TestRebuildFacetRollup`, `TestRebuildRollups` (mutate base via `tn.wdb.Exec` behind the rollup,
  rebuild, assert exact both ways). Facet oracle mirrors `facetRollupFill`'s 8 `UNION ALL` branches.
  M4: `queryMeasureNoRollup` + `convBucketedFixture` + `TestConversationRollupBucketedLocalTwoDim`
  (utc/Sydney × day/week, two dims, `reflect.DeepEqual` on `Rows`, `len>0`).
- `compact/rollup_test.go`: `assertConvRollupExact`/`assertFacetRollupExact`/`assertAllRollupsExact`
  and boolean `allRollupsExact`; `allRollupsLedger` (row 1 = remove-listed opencode `chat.params`,
  only row of `cdrop`; row 2 = kept opencode `transcript.assistant_message` + `modelID`, so
  compaction fills `model`/`norm_event`); `TestCompactRebuildsAllRollups`,
  `TestCompactRebuildsAllRollupsOnResume`.

Confirmed `Derive` combination: opencode `transcript.assistant_message` with payload `modelID`
(`extract.go:74-79`) gives `Model="m1"`, and the event is not in `policyTable` ⇒ Keep.

## Check output

```
ok  github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store    3.017s
ok  github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact  0.263s
ok  github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve    (cached)
```
`go vet ./internal/store ./internal/compact ./internal/serve` — clean.
`gofmt -l` on the four owned files — prints nothing.
New tests verbose: all PASS (store 4/4, compact 4/4).

## Deviations

1. **Base-only oracle lives in the test, via the unexported `queryMeasure`.** `Query` exposes no
   rollup-off toggle and `query.go` is not an owned path, so the brief's "forced off" oracle is
   implemented in `queryMeasureNoRollup` by calling `tn.queryMeasure(..., def, top, bucket)` with
   `def.rollup = ""` (tests are `package store`). This is the mechanism the brief instructed.
2. **Compound `EXCEPT` needs subquery wrapping.** The facet base aggregate is a 8-branch
   `UNION ALL`; SQLite compound operators are left-associative, so `rollup EXCEPT branch1 UNION ALL
   branch2 ...` mis-parsed and the first run failed (64 phantom tuples). Fixed by wrapping each side
   as `SELECT * FROM (<sel>)` in `exceptBothWays`/`exceptBothEmpty`. The hook/conversation helpers
   are unaffected (single-SELECT bases).
3. **No `_ "time/tzdata"` added.** `query_test.go` already blank-imports it in the same package test
   binary, so `time.LoadLocation("Australia/Sydney")` works; adding it was conditional in the brief.

## Contradictions

None. The three `Rebuild*` tables and helpers the brief cites (`RebuildHookRollup`, `convRollupFill`,
`facetRollupFill`, guards) all exist as described, and 3-15's report confirms `facets_hourly` is the
only rollup it added. The brief itself states the rollup-off oracle must be test-only, so (1) is not
a contradiction.

## Unfinished

None.
