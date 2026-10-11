# Report: 3-05 — Usage measures: tokens, model calls, cost and Claude message dedupe

done with concerns

## What changed

- `tools/workflow/internal/store/usage.go` (new): `init()` sets the package var `usageQuery`
  that 3-04 left nil, so the eight usage measures answer through `(*Tenant).Query`.
  - `usageRowsWhere(f AnalyticsFilter) (string, []any)` (unexported, reusable by 3-08/3-09)
    returns `WITH usage_u AS (...), kept AS (...)` over facts with
    `type='hook_event' AND norm_event='usage'`. The base predicate is fixed; `f` is applied
    verbatim through `factWhere`.
  - Claude dedupe: `_mid = CASE WHEN harness='claude' THEN json_extract(raw,'$.backfill.ref') END`;
    `kept` keeps every row with a null/empty id and, per `(conversation_id, _mid)`, only the row
    with the largest `tok_out` (ties: lowest `row_hash`).
  - Aggregation is done in Go over the kept rows: `model_calls`=1/call, `tokens_*`=column sums,
    `cost_usd`=Σ `Cost(harness, model, Tokens{…}, cost_reported)` per kept call, `unpriced_calls`
    counts kept calls where `Cost` is not priced. Top-N folding (`foldUsageDim`), UTC/local
    bucketing and `hour_of_day`/`weekday` reuse 3-04's `rankKeys`, `localKey`, `localBucket`,
    `sortRows`, `queryRowCap`. No change to any file in query.go.
- `tools/workflow/internal/store/usage_test.go` (new): `TestUsageMeasures`,
  `TestUsageGroupByHarnessAndModel`, `TestUsageClaudeDedupeKeepsLargestOut`,
  `TestUsageLiveClaudeWithoutIdIsNotDeduped`. Hand-computed expectations are in comments.
- Two files outside the brief's owned paths (see Deviations 2): `internal/store/query_test.go`
  and `internal/serve/analytics_query_test.go`.

## Checks

All from `tools/workflow`, `PATH=$HOME/.local/go/bin:$PATH`.

- Before: `go test ./internal/store -run 'Usage|Query|Cost'` had no usage tests; usage measures
  returned `errors.New("measure not available")` (`TestQueryUsageUnavailable`).
- After:
  - `go test ./internal/store -run 'Usage|Query|Cost' -v` — PASS (21 tests; the 4 new Usage tests
    plus `TestQueryUsageAvailable`). Hand computation asserted: `model_calls=3`,
    `tokens_out=40` (not 50), `tokens_in=1000`, `tokens_cache_read=400`, `cost_usd=0.2504`
    (Codex fresh 600×0.6 + cache 400×0.1 = 0.0004, plus reported 0.25), `unpriced_calls=1`.
  - `go test ./internal/store ./internal/serve` — `ok` both.
  - `go test ./...` — `ok` every package; `go build ./...` — clean.
  - `go vet ./internal/store ./internal/serve` — no output. `gofmt -l internal/store internal/serve`
    — no output.

## Deviations from the brief (named)

1. **Fixture count.** The brief's done evidence describes "4 usage facts" but enumerates a Claude
   pair (2 rows), a Codex call, an OpenCode call and a call with an unknown model / no cost —
   five rows. Five rows with one dedupe gives `model_calls=4`, not the stated 3. I read the last
   clause as characterising the kept Claude call (its model, `claude-sonnet-5-5`, is absent from
   `pricing_table.json` and it reports no cost, so it is the one unpriced call). The fixture is
   therefore four rows (2 Claude + Codex + OpenCode), giving `model_calls=3`, `unpriced_calls=1`.
2. **Owned paths vs done evidence (contradiction).** Registering `usageQuery` in `init()`
   necessarily makes 3-04's `TestQueryUsageUnavailable` fail, yet that test matches the brief's own
   done-evidence regex `'Usage|Query|Cost'`, and the brief forbids touching files other than
   `usage.go`/`usage_test.go`. I resolved it by updating that now-obsolete test in
   `internal/store/query_test.go` (renamed `TestQueryUsageAvailable`, asserts the query succeeds).
   3-06's `serve/analytics_query_test.go:156` likewise asserted `model_calls` → 400 "measure not
   available" (3-06's own report says it covered the gap "until 3-05 registers `usageQuery`");
   left unfixed it makes `go test ./...` red, so I pointed it at a still-valid usage error path
   (`dim=tool` → 400 `unsupported dimension tool for model_calls`). Both edits are test-only.
3. **Cost in Go, full fetch.** The brief suggests a grouped fetch ("group rows by `harness`,
   `model`, `cost_reported IS NULL`-class in SQL if you can"). I fetch the whole kept set and
   aggregate in Go instead: 3-04's aggregation helpers issue their own SQL with the window/filter
   args, and a parameterised `WITH kept` fragment cannot be spliced in without breaking the
   placeholder order. Cost is linear in tokens, so summing per-row `Cost` in Go is exact and the
   brief says correctness over speed here.

## Unfinished / notes

- Dedupe uses `$.backfill.ref` only. Backfilled Claude rows also still retain
  `$.payload.message_id`; I did not `COALESCE` it in because the brief names `backfill.ref` and the
  two agree on every backfilled row. A future unit could add it as a fallback key.
- Live-captured Claude repeats are not deduped. Confirmed (grep of
  `tools/hooklog/tests/fixtures/ingest_policy.json` and `internal/ingest/ingest.go`): the wire
  fixture carries `payload.message_id`, but `ingest.envelope` strips the top-level `id`, `content`
  and `payload` before storing, so no stored live fact exposes a message id. This is the known
  limit the brief names, not a defect introduced here.

## Problems

- The `usageQuery` registration invalidates test assertions built on its absence (Deviation 2);
  these are the only contradictions found between the brief and the contracts it cites, and both
  are named above rather than resolved silently.

## Non-trivial bug outside done evidence

- None found. The only cross-cutting effect (serve's "measure not available" test) is the direct,
  intended consequence of wiring usage and is handled in Deviation 2.
