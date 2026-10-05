# Brief: 1-03 — `/v1/analytics/*` routes

Consumer: a Sonnet worker dispatched by the plan 10 phase 1 orchestrator. The JSON these routes
return is what phase 2's Svelte views are built on; the orchestrator verifies the phase outcome
against this unit's fixture test and a live `workflow serve`.
Owned paths: new `tools/workflow/internal/serve/analytics.go`, new
`tools/workflow/internal/serve/analytics_test.go`, `tools/workflow/internal/serve/serve.go` (only the
route registrations in `Handler`), `docs/plans/10-workflow-analytics/reports/1-03-analytics-routes.md`
(new). Touch nothing else; in particular not `internal/store/` (1-02's API is fixed; report a gap
instead of changing it), `reads.go` (call `percentile`, `round3`, `validKind`, `badKind`,
`kindOrder` as they are), the CORS middleware 1-01 added, `go.mod`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/1-03-analytics-routes.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 1-01 (it changed `Handler`) and 1-02 (the store API you call). Both are committed on this branch.
Runs alongside: nothing.
Budget: 8 files to read, about 700 lines to write including tests, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — "Domain: Analytics reads" (lines 49-173). Binding: every route, parameter, error body and JSON shape.
2. `docs/plans/10-workflow-analytics/DESIGN.md` — Phase 1 Outcome (line 277).
3. `docs/plans/10-workflow-analytics/reports/1-02-store-analytics.md` and `go doc ./internal/store AnalyticsFilter` (and the other types in `internal/store/analytics.go` by `go doc`, not by reading the file) — the API you call, and any deviation 1-02 reported.
4. `docs/plans/10-workflow-analytics/reports/1-01-browser-access.md` — what changed in `Handler`.
5. `tools/workflow/internal/serve/reads.go` — whole file (138 lines): `percentile`, `round3`, `checks`, `baselines`, `search` (the handler idiom to match).
6. `tools/workflow/internal/serve/serve.go` — `Handler`, `writeJSON`, `method`, `auth` (around lines 377-470).
7. `tools/workflow/internal/serve/serve_test.go` lines 21-43 (`do`, `newServer`, `artBody`) and `reads_test.go` lines 20-80 (`contentScorer`, `readStep`, `getJSON`, `putSettled`) — test helpers to reuse.

Go is at `~/.local/go/bin` (add it to `PATH`). Run tests from `tools/workflow`. Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Expose the seven analytics reads as additive `GET /v1/analytics/{facets,summary,series,scores,executions,conversations,explore}` routes with exactly the contract's JSON, tenant auth and error bodies.

## Contract

DESIGN.md "Domain: Analytics reads" is the authority; cite it, do not reinterpret. Points that bind the handler layer:

- "Every analytics `GET` uses the same tenant resolution as `GET /v1/artifacts`" → register each with `s.method(http.MethodGet, s.auth(...))`. "Unknown routes under `/v1/` stay JSON 404. Error body stays `{"error":"<text>"}`."
- Shared filter (lines 62-72): `from`/`to` RFC3339 inclusive, defaults (`to` = now, `from` = `to` − 30 days), the 400-bucket cap with `{"error":"range too wide"}`, repeatable `repo_id`/`harness`/`kind`/`plan`, `kind` validation, and for `/scores` exactly one `kind` else 400 `{"error":"kind required"}`.
- Facets `checks` "is the in-memory catalog served by `GET /v1/checks` (all kinds)"; scores has "One object per catalog check for that kind, zeros when nothing was scored" with `min`/`p25`/`median`/`p75`/`max` from `percentile`/`round3` at q = 0, .25, .5, .75, 1.
- Series pairing table (lines 100-108): any other pairing is 400. Executions and conversations paging (lines 150, 161): `limit` default 100, max 500, `next` absent on the last page, opaque cursor bound to filters and order, mismatch → 400 `{"error":"cursor mismatch"}`. Explore: 20,000-row cap with `truncated`.

Decisions settled at refine (do not re-derive):

1. **Errors not worded by the contract:** bad `from`/`to` → 400 `{"error":"from and to must be RFC3339"}`; `from` after `to` → 400 `{"error":"from is after to"}`; invalid `kind` value → the existing `badKind` body; missing/invalid `metric` → `{"error":"metric must be hook_events, artifact_versions, commits, conversations or rejections"}`; missing/invalid `bucket` → `{"error":"bucket must be day or week"}`; disallowed `group` → `{"error":"group not allowed for metric"}`; non-integer `limit` → `{"error":"limit must be an integer"}`; an undecodable cursor → `{"error":"cursor mismatch"}`. `limit` outside 1..500 is clamped, as `search` clamps.
2. **Bucket cap:** count UTC calendar days from `from`'s date to `to`'s date inclusive; over 400 → `range too wide`. With `bucket=week` on `/series`, count ISO weeks (Mondays) instead. Every other route uses the day count.
3. **Kinds on `/scores`:** zero or more than one `kind` value → `kind required`; one invalid value → `badKind`.
4. **Timestamps out:** `from`, `to`, and row `ts`/`first_ts`/`last_ts` are RFC3339 in UTC at second precision (`time.RFC3339`). Series `t` is the store's `YYYY-MM-DD`.
5. **Series response:** group the store's points by key into `series` entries ordered by key ascending; `group=none` with no data still returns one entry `{"key":"all","points":[]}`.
6. **Cursor:** base64url JSON holding the route name, a canonical form of the request's filter parameters *as sent* (sorted repeated values of `from`, `to`, `repo_id`, `harness`, `kind`, `plan`; not `limit`, not `cursor`), the resolved `from`/`to` of the first page, and the last row's sort key. A follow-up request must send the same filter parameters; it then uses the cursor's resolved window, so an omitted `to` does not drift between pages. Any difference → `cursor mismatch`. Page by sort key over the store's sorted rows (1-02 decision 8: executions also tie-break on `repo_id`).
7. **Executions `counts`** cover every matching brief regardless of page, with all three keys present.
8. **JSON lists are never `null`:** empty slices encode as `[]`. Explore rows are objects with exactly the 14 contract columns, strings throughout (`ts` RFC3339). The explore cap is an unexported package variable `exploreCap = 20000` so the test can lower it.
9. **Checks catalog absent** (`Options.Checks == nil`): facets `checks` and scores `checks` are `[]`.
10. **Facets scope** (amended after 1-02): the contract says facets are "every distinct value on facts in the window", so `/facets` validates the full shared filter but calls `store.Facets` with only `From` and `To` set. `store.Series` already rejects unknown metric/bucket/group; validate the pairing table in the handler anyway so error bodies are the ones in decision 1.

## Changes

- `analytics.go`: one shared filter parser returning `store.AnalyticsFilter` or writing the 400; one handler per route; the cursor helpers. Keep handlers in the style of `reads.go` (`map[string]any` or small structs with JSON tags, `writeJSON`).
- `serve.go` `Handler`: seven `mux.HandleFunc("/v1/analytics/<name>", s.method(http.MethodGet, s.auth(...)))` lines beside the existing reads. Nothing else in that file.

### Keep untouched

Every existing route, its response shape, and the existing tests: "`GET /v1/artifacts` and `GET /v1/health` keep their current shapes." 1-01's CORS middleware must wrap the new routes as it wraps the old ones.

## Done evidence

Write the failing tests first and report their output before and after. Why: this test is the phase outcome in executable form. Phase 2 builds views on these exact shapes, so every field and error body asserted here is one the site will not have to guess. The paging walk proves a table can page without duplicates or gaps. The 401 and 404 cases prove the new routes did not widen access.

- `go test ./internal/serve/ -run Analytics -v` → passes. `TestAnalyticsOutcome` builds one fixture tenant through `POST /v1/ingest` (explicit `ts` values across two repos, two harnesses, several conversations, hook events with and without `payload.tool_name`, designs/briefs/reports/commits including one nested brief path, at least one precheck rejection from a fact carrying a secret pattern, and scored content via `readStep`/`contentScorer`), then asserts each route's JSON against hand-computed numbers: summary fields; facets lists and catalog `checks`; series for each metric with one allowed group, plus a disallowed pairing → 400; scores five-number summary equal to `round3(percentile(...))` of the fixture values, and `kind required` for zero and two `kind` params; executions shapes per brief (complete/unreported/started, with a commit and a report outside the window still counting), row order, a two-page walk with `limit=1` whose concatenation equals the one-page result, `next` absent on the last page, and `cursor mismatch` when `repo_id` changes; conversations order and paging; explore columns (exactly the 14), order, and `truncated` true when `exploreCap` is lowered below the row count and false when not; `range too wide` for a 401-day range and success for the same range with `bucket=week` on series.
- The same test asserts a keyed server returns 401 on `/v1/analytics/summary` without a key, and `/v1/analytics/nope` → JSON 404.
- `go vet ./... && go test ./...` from `tools/workflow` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in 1-02's store queries): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
