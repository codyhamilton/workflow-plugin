# Report: 3-06 — Filter parsing, `schema` and `query` routes

done

## What changed

- `internal/serve/analytics.go` (owned: `parseFilter`, `canonFilter`, `filterOpts`):
  - `parseFilter` now reads the six repeatable keys (`norm_event`, `event`, `tool`, `model`,
    `source`, `conversation_id`) into the 3-02 filter fields; `tz` (IANA, default UTC) into `TZ`
    with 400 `{"error":"invalid tz"}` on an unknown name; `all=1` forces `From` to
    `time.Unix(0,0)` and `To` to now when `to` is absent.
  - `filterOpts` gains `query bool`; the day/week `tooWide` cap is skipped only for `query`
    (which applies its own per-unit cap). Existing routes keep the old cap, so `all=1` on them
    stays 400 when the span exceeds 400 days/weeks.
  - `canonFilter` allowlist extended with the six new keys plus `tz` and `all` (see Deviations).
- `internal/serve/analytics_query.go` (new): `analyticsSchema` returns
  `{"measures":[{name,unit,dims}],"buckets":[…]}` from `store.Measures()`/`store.Buckets`;
  `analyticsQuery` validates `measure`/`dim`/`bucket`/`top`, calls `tenant.Query`, and shapes
  `{"measure","bucket","dims","rows":[{t?,k,v}],"ignored_filters"?,"partial"?,"truncated"?}`.
  `partial:true` iff `tenant.CompactionState() != "complete"`. `bucketSpan` counts buckets per
  unit (tz-aware) and caps at 400 → 400 `{"error":"range too wide"}`; `bucket=none` uncapped.
- `internal/serve/serve.go`: two `mux.HandleFunc` lines (`/v1/analytics/schema`,
  `/v1/analytics/query`), GET + the same auth wrapper as the other analytics routes.
- `internal/serve/analytics_query_test.go` (new): the enumerated tests.

## Checks (all run from `tools/workflow`, `PATH=$HOME/.local/go/bin:$PATH`)

Before: `go test ./internal/serve -run 'Query|Schema|Filter' -v` did not exist (PASS on the
pre-existing suite; no query/schema tests).

After:

- `go test ./internal/serve -run 'Query|Schema|Filter' -v` — PASS:
  `TestAnalyticsSchema`, `TestAnalyticsQuery/{dims,errors,ignored_filters,top,all,tz,cap}`,
  `TestAnalyticsQueryPartial`, `TestAnalyticsFilterToolSummary` all PASS.
- `go test ./internal/serve ./internal/store` — `ok` both.
- `go vet ./internal/serve` — no output. `gofmt -l internal/serve` — no output.

## Deviations from the brief (named)

1. The brief says "`canonFilter` already covers the new keys if it sorts all query params; check
   and keep it so." It did **not**: the allowlist held only `from,to,repo_id,harness,kind,plan`.
   I extended it with the six new keys plus `tz` and `all` so a cursor's identity includes the
   new filter/bucketing inputs. This is the one place the brief's stated premise was wrong.
2. `partial` test fixture: I used a fresh tenant with an appended fact and `SetMeta`
   `required`→`complete`, not `legacyLedger` directly. `legacyLedger` writes a `user_version=4`
   db with only `(row_hash,type)`; `Query` then 500s on the missing `ts`/filter columns, so it
   cannot back a query test. The `SetMeta` toggle is exactly the mechanism
   `compaction_state_test.go` uses; the resulting states match the brief.
3. Error strings the brief left unspecified: `unknown bucket <b>`, `top must be an integer`,
   `top must be at most 100`. Chosen to mirror the store's `unknown bucket` wording; no external
   check pins them.
4. `unknown measure` is validated in serve (unquoted `<m>` per the brief) rather than surfacing
   the store's `unknown measure %q` (quoted). Deliberate to match the brief's exact text.

No contradiction found between the brief and DESIGN.md; the brief's contract is a superset of
DESIGN.md §"`GET /v1/analytics/query`" (it adds `truncated`, which DESIGN.md states in prose).

## Unfinished / notes

- None. Usage measures return 400 `{"error":"measure not available"}` until 3-05 registers
  `usageQuery`; covered by a test.

## Non-trivial bug outside done evidence

- `legacyLedger` (in `compaction_state_test.go`) inserts `PRAGMA user_version = 4` but its facts
  table has only two columns, so it is not a real v4 schema. Opening it and running any facts
  read fails (missing columns). It is harmless for the health test that owns it, but it is a
  trap for any future test that wants to query a legacy fixture. Reported, not fixed here.
