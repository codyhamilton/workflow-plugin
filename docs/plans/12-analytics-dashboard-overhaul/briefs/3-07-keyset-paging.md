# Brief: 3-07 — Keyset paging in SQL for executions and conversations

Consumer: a Go worker (flash-tier); the dashboard's tables page through these routes.
Owned paths: `tools/workflow/internal/store/analytics.go` (only `Executions`, `Conversations`, and new paged variants), `analytics_test.go`, `tools/workflow/internal/serve/analytics.go` (only `analyticsExecutions`, `analyticsConversations`, `pageOf`) and `analytics_test.go`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-07-keyset-paging.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-02, 3-06.
Runs alongside: 3-09.
Budget: 6 files to read, about 300 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: **Paging** and **Existing routes** bullets (binding).
2. `tools/workflow/internal/serve/analytics.go` lines 34-60, 350-465 — `cursor`, `pageOf`, the two handlers.
3. `tools/workflow/internal/store/analytics.go` — `Executions`, `Conversations`.
4. `tools/workflow/internal/serve/analytics_test.go` — grep `executions` and `conversations` tests: the current response shape and ordering you must keep.
5. `packages/workflow-analytics/tests/e2e/executions.spec.ts` and `conversations.spec.ts` — what the current site expects (read, do not edit).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

`executions` and `conversations` return one page by a SQL keyset and never load the whole window into Go, with the same request and response shapes and the same ordering as today.

## Contract

Design, cited: "Paging. Executions and conversations page in SQL by keyset." and "`facets`, `summary`, `series`, `scores`, `executions`, `conversations` and `explore` keep their request and response shapes."

Settled by this brief:
- Keep the cursor type and its fields (`cursor{Route, Filter, From, To, TS, Key}`) and the query parameters `limit` (1..500) and `cursor`. Order is unchanged: executions by `ts desc, conversation_id, brief path, repo_id`; conversations by `last_ts desc, conversation_id`.
- Executions: push `LIMIT limit+1` and the keyset predicate `(ts < ?) OR (ts = ? AND (conversation_id, path, repo_id) > (?,?,?))` into the SQL. The `counts` object (`complete`, `unreported`, `started`) is the count over the whole filtered window, not the page; compute it with one aggregate query, not by loading rows.
- Conversations: aggregate per conversation in SQL (`GROUP BY conversation_id` with `min(ts)`, `max(ts)`, counts per type, and `kinds` and `repos` through `group_concat(DISTINCT …)`), keyset on `(last_ts desc, conversation_id)` via `HAVING` or an outer `WHERE`, `LIMIT limit+1`. `harness` is the most frequent harness per conversation, ties to the smaller name: fetch it for the page's conversation ids only, with one grouped query. The totals the route reports for the window (read the handler for which) must stay equal to today's.
- Store signatures: add `ExecutionsPage(ctx, f, cur *ExecCursor, limit int) (rows []ExecRow, counts map[string]int, more bool, err error)` and `ConversationsPage(...)` analogously; keep or delete the old whole-window functions only if nothing else uses them (grep first).

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve ./internal/store` passes, including the existing executions and conversations tests unchanged in expectation.
- New tests: 7 executions at distinct `ts` plus 2 sharing one `ts`, `limit=3`, three pages by following `next` gives all 9 rows once in the old order; the same for conversations with a `last_ts` tie; a cursor from a different filter is 400 `cursor mismatch` (existing behaviour); `counts` on page 1 equals counts over all rows.
- A test or a short `EXPLAIN QUERY PLAN` assertion shows the page query does not read a number of rows proportional to the window: on a 20,000-fact fixture, page 1 of `executions` with `limit=5` returns in under 100 ms (log the time; the assertion is on correctness, the time is reported).
- `go vet ./internal/serve ./internal/store` and `gofmt -l` print nothing. `grep -n 'sort.Slice' tools/workflow/internal/serve/analytics.go` shows none inside the two handlers.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
