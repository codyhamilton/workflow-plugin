# Report: 3-07 — Keyset paging in SQL for executions and conversations

Status: **done with concerns** (timing target missed; two forced deviations from the brief snippets).

## What changed, against each part of the brief

- Store (`store/analytics.go`): added `ExecCursor{TS,Key}`, `ConvCursor{TS,ConversationID}`, const
  `execShapeSQL` (the executions shape `CASE`, verbatim), and `ExecutionsPage` / `ConversationsPage`
  / `splitConcat` / `fillHarness`. `database/sql` added to imports. `Executions`/`Conversations`
  kept; the only edit to `Executions` is that its inline `CASE` now references `execShapeSQL`
  (behaviour identical; existing store tests pass).
- Serve (`serve/analytics.go`): rewrote `analyticsExecutions` and `analyticsConversations` to call
  the paged store calls, deleted `pageOf`, removed the now-unused `strings` import. `sort` kept
  (`analyticsSeries`). Cursor type, `pageParams`, `parseFilter`, other handlers untouched.
- Tests (`store/analytics_test.go`): `TestExecutionsPage` (9 briefs, 7 distinct ts + c08/c09 tie,
  limit=3 three-page walk, concatenation equals `limit=500`, page-1 counts equal whole-window
  counts, tie ordered c08 then c09), `TestConversationsPage` (same fixture, `last_ts` tie, three-page
  walk equals unpaged), `TestExecutionsPageTiming` (20,000 facts).
- Report written and included in the commit.

Evidence: `go test -count=1 ./internal/serve ./internal/store` → both `ok`. Existing
`TestAnalyticsOutcome/executions` and `/conversations` pass unchanged in expectation, including the
two-page walk and `cursor mismatch` 400s (serve lines 416-417/449).

## Check output

- Before (HEAD `3f28cbc`, owned files stashed): `go test ./internal/serve ./internal/store` → both `ok` (cached).
- After: `go test -count=1 ./internal/serve ./internal/store` → `ok serve 3.101s`, `ok store 1.649s`.
- `go vet ./internal/serve ./internal/store` → no output (exit 0).
- `gofmt -l internal/serve internal/store` → no output (exit 0).
- `grep -n 'sort.Slice' internal/serve/analytics.go` → only `333: sort.SliceStable(...)` in
  `analyticsSeries`; none in either handler.
- 20k timing: `TestExecutionsPageTiming`: **152-156 ms** (three `-count=1` runs: 156.0, 153.1, 152.1 ms).

## Deviations from the brief (all forced)

1. `ConversationsPage` keyset: the brief snippet tests `cur != nil && len(cur.Key) >= 1` and uses
   `cur.Key[0]`, but `*ConvCursor` has no `Key` field — the snippet does not compile. Used
   `cur != nil` and `cur.ConversationID` (the serve side maps `cursor.Key[0]` into it, as the brief's
   serve snippet and its guard note intend).
2. `group_concat(DISTINCT x, char(31))` is rejected by `modernc.org/sqlite`:
   `DISTINCT aggregates must have exactly one argument`. Used single-arg `group_concat(DISTINCT x)`
   and split on the default `,` in `splitConcat`. DISTINCT semantics retained; only the separator
   differs. Limit: a repo id containing a comma would be split wrongly (kinds are a fixed
   comma-free vocabulary).
3. Test level: used store-level `TestExecutionsPage`/`TestConversationsPage` for the 9-row/tie/
   three-page walks rather than HTTP-level. The brief permits this ("If reproducing the ingest
   fixture at HTTP level proves impractical..."). HTTP-level coverage of the walk and cursor
   mismatch already exists and is unchanged; `serve/analytics_test.go` was not modified.

## Contradiction between brief and cited contracts

None found against DESIGN.md ("Paging... by keyset" and "keep their request and response shapes").
The only contradiction is internal to the brief: the `ConversationsPage` snippet's `cur.Key` versus
the `ConvCursor{TS, ConversationID}` type it defines (deviation 1).

## Unfinished work

None required. Optional, out of the owned paths: add a `facts(type, conversation_id, repo_id)` index
to bring the 20k page under the 100 ms target (see below).

## Known problems

- Page-1 timing is 152-156 ms, above the brief's "under 100 ms" done-evidence line. The brief states
  the assertion is correctness (met) and the time is reported. Root cause: the mandated whole-window
  `counts` aggregate evaluates `execShapeSQL` (two correlated `EXISTS`) once per in-window row, and
  no index covers `(type, conversation_id, repo_id)` for those lookups.
- The counts aggregate is O(window) by design ("count over the whole filtered window").
