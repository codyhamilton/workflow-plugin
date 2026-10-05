# Report: 1-03 `/v1/analytics/*` routes

Status: done with concerns (two contract ambiguities, below; no contradiction with DESIGN.md).

## Done against the brief

- `tools/workflow/internal/serve/analytics.go`: one shared filter parser (`parseFilter`), one handler per route (facets, summary, series, scores, executions, conversations, explore), cursor helpers, and the package variable `exploreCap = 20000`. `serve.go` `Handler` gained seven `mux.HandleFunc("/v1/analytics/<name>", s.method(http.MethodGet, s.auth(...)))` lines and nothing else. `reads.go`, `internal/store/`, the CORS middleware and `go.mod` are untouched.
- Error bodies are the ones fixed in the brief's decision 1; `limit` is clamped to 1..500; the 400-bucket cap counts UTC days (ISO weeks for `bucket=week` on `/series`); cursors are base64url JSON bound to route, canonical filter as sent, the first page's resolved window and the last row's sort key.
- `/facets` validates the full filter but calls the store with only `From` and `To` (decision 10). Lists encode as `[]`, never `null`; summary maps always carry every contract key.
- `analytics_test.go`: `TestAnalyticsOutcome` (one fixture tenant posted through `POST /v1/ingest`: 4 conversations, 2 repos, 2 harnesses, hook events with and without `tool_name`, designs, briefs, a nested brief path, a report and a commit outside the window, a commit-sourced artifact version, one precheck rejection from an AKIA-pattern payload, scores through the screen step) with subtests summary, errors, facets, series, scores, executions, conversations, explore, access; `TestAnalyticsEmptyTenant` pins `[]` on an empty tenant with no catalog.

## Check output

- Before (tests written first): `go test ./internal/serve/ -run Analytics` failed to build: `undefined: exploreCap`.
- After the routes, the first run failed three assertions that were my wrong expectations about the store (see Departures); after correcting them, `go test ./internal/serve/ -run Analytics -v` passes all 9 subtests and `TestAnalyticsEmptyTenant`. `go vet ./...` is clean and `go test ./...` passes in every package.
- Asserted numbers include: summary 4 conversations, 6 hook events, 8 artifact versions, 7 distinct content, by_kind 4/3/0/1, precheck 1; scores for the fixture values 0.2, 0.6, 0.9 equal `round3(percentile(...))` (p25 0.4, p75 0.75); executions complete 1, unreported 1, started 1, with the out-of-window report and commit counting; paged walks for executions and conversations equal the one-page result and `next` is absent on the last page; `cursor mismatch` when `repo_id` or `plan` changes or the cursor comes from another route; explore has exactly the 14 string columns, 16 rows newest first, `truncated` true at `exploreCap = 5` and false at 16; a 401-day range is `range too wide`, 400 days succeeds, and the 401-day range succeeds with `bucket=week`; a keyed no-key or bad-key `summary` is 401, `/v1/analytics/nope` is JSON 404, POST is 405.

## Departures

- The scores fixture uses a small `qaScorer` (wraps `contentScorer`, files the score under the first catalog design check) and a screen step that copies `readStep`'s UNSCREENED handling, because `contentScorer` writes check `q.a`, which is not in the loaded catalog and would never appear in `/scores`.
- The nested brief path (`briefs/sub/1-03-n.md`) is not an execution: the store lists only `briefs/<stem>.md`. It counts in summary `other`. The test follows that.

## Ambiguities for the orchestrator

1. `/facets` `plans` includes `""` when facts have no plan (hook events), and `kinds` is in catalog order (`design`, `brief`, `report`), not alphabetical. That is the store's behavior (1-02); I kept it. DESIGN.md says "every distinct value", which fits, but phase 2 may want to hide `""` in the filter control.
2. Cursor paging reads all matching rows from the store and slices in Go (the store API has no offset). Fine at current sizes; not measured at scale.

## Unfinished / known problems

None in this unit. `gofmt -l` lists `internal/store/analytics.go` and `analytics_test.go` (1-02's files, formatting only); not touched here.
