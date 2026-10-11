# Brief: 3-06 — Filter parsing, `schema` and `query` routes, `ignored_filters`, `partial`

Consumer: a Go worker (flash-tier); the dashboard in Phase 4 calls these routes.
Owned paths: `tools/workflow/internal/serve/analytics.go` (only `parseFilter`, `canonFilter` and `filterOpts`), `tools/workflow/internal/serve/analytics_query.go` (new), `analytics_query_test.go` (new), and `tools/workflow/internal/serve/serve.go` (only the two `mux.HandleFunc` lines for the new routes). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-06-serve-query-routes.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-02, 3-04.
Runs alongside: 3-05.
Budget: 6 files to read, about 300 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Shared filter**, **`GET /v1/analytics/query`**, **The measure × dimension matrix**, the line on `partial` in the compaction domain (`"partial": true` while `/v1/health` reports `compaction: required`) (binding).
2. `tools/workflow/internal/serve/analytics.go` lines 1-180 — `errJSON`, `parseFilter`, `canonFilter`, `tooWide`, `filterOpts`, `pageParams`.
3. `tools/workflow/internal/serve/analytics.go` lines 262-325 — `analyticsSeries` (the bucket cap and 400 messages you mirror).
4. `tools/workflow/internal/store/query.go` (3-04) — `Measures`, `Buckets`, `QueryParams`, `QueryResult`, `ErrUnsupported`.
5. `tools/workflow/internal/serve/serve.go` lines 400-440 (routes) and where `compaction` health is computed (grep `compaction`) — how to read the meta value from a `tenantState`.
6. `tools/workflow/internal/serve/analytics_test.go` lines 1-120 — `aget`, fixture helpers.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

`GET /v1/analytics/schema` and `GET /v1/analytics/query` answer exactly as the design says, and the shared filter accepts the new keys on every analytics route.

## Contract

Design, cited in full above. Settled by this brief:
- `parseFilter` reads the repeatable keys `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id` into the filter (3-02 fields); `tz` (IANA, default `UTC`; an unknown name is 400 `{"error":"invalid tz"}`) into `TZ`; `all=1` sets `From` to `time.Unix(0,0)` and `To` to now when `to` is absent (it overrides `from`). `canonFilter` already covers the new keys if it sorts all query params; check and keep it so for cursors.
- "The 400-bucket cap applies per bucket unit": for `query` the number of buckets in the window for the chosen unit (hour, day, week, month) must be at most 400, otherwise 400 `{"error":"range too wide"}`. `bucket=none` has no cap. Existing routes keep their current cap rule (do not change `tooWide` behaviour for them; `all=1` on them stays subject to it).
- `GET /v1/analytics/schema` returns `{"measures":[{"name","unit","dims":[…]}],"buckets":[…]}` straight from `store.Measures()` and `store.Buckets`; method GET, same auth wrapper as the other analytics routes.
- `GET /v1/analytics/query`: `measure` required (400 `{"error":"measure required"}`; unknown measure 400 `{"error":"unknown measure <m>"}`); `dim` repeated 0 to 2 (a third is 400 `{"error":"at most two dim"}`); `bucket` must be in `Buckets`; `top` integer, default 20, above 100 is 400. An `ErrUnsupported` from the store is 400 with the store's exact text without the wrapped suffix: `unsupported dimension <d> for <measure>`. Response JSON: `{"measure","bucket","dims":[…],"rows":[{"t"?,"k":[…],"v"}],"ignored_filters"?,"partial"?,"truncated"?}` with `t` RFC3339 in `tz`, keys omitted when empty/false. `partial:true` exactly while the tenant's compaction meta is not `complete`.
- If a usage measure's executor is not yet registered (3-05 not merged), the route returns 400 `{"error":"measure not available"}`; your tests use only non-usage measures except one schema test.

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve -run 'Query|Schema|Filter' -v` passes with tests for: schema JSON equals the design table (literal in the test) and includes every measure; `query` with 0, 1 and 2 dims; third dim 400; unsupported pairing returns exactly `{"error":"unsupported dimension tool for conversations"}`; a `kind` filter on `hook_events` lists `kind` in `ignored_filters`; `tz` bucketing of a sub-day fixture (a fact at 23:30 UTC with `tz=Australia/Sydney&bucket=day` lands on the next local date and `t` carries the `+10:00` or `+11:00` offset); `top=1` folds to `__other__`; `all=1` returns a fact older than 30 days; bucket cap exceeded is 400; `partial` appears on an uncompacted fixture and is absent on a compacted one (use `compaction_state_test.go` as the model); an existing route (`summary`) accepts `tool=Read` without error.
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve ./internal/store` passes; `go vet ./internal/serve` and `gofmt -l internal/serve` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
