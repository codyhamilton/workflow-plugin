# Brief: 3-02 — Shared filter keys and column-based reads

Consumer: a Go worker (flash-tier); 3-04, 3-06, 3-07 and 3-08 build on the filter struct and on column reads.
Owned paths: `tools/workflow/internal/store/analytics.go` and `analytics_test.go`. Do not touch `serve/`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-02-filter-columns.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 3-01, 3-03.
Budget: 5 files to read, about 250 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads, **Shared filter** bullet (binding), and the Phase 3 Outcome.
2. `tools/workflow/internal/store/analytics.go` — read all of it (497 lines); it is the file you change.
3. `tools/workflow/internal/store/store.go` lines 28-70 — the migrations: `facts` has columns `norm_event`, `tool`, `model`, `kind`, `plan`, `source`, `sha`, `tok_*`, `cost_reported` and indexes `facts_type_ts`, `facts_ts_harness_event`, `facts_conv`.
4. `tools/workflow/internal/store/analytics_test.go` — how fixtures are inserted (grep `Append(` and `FactRow`).
5. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — Carried item 4 and the 1-05 report line about `serve/analytics_test.go`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Every facts read in `store/analytics.go` filters and groups on the real columns, never on `json_extract` of `raw` or the `wf_kind`/`wf_plan` functions, and the filter carries the new keys.

## Contract

Design, cited: "New repeatable keys: `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. The OR/AND rules are as in design 7." and "New `tz` (IANA name, default `UTC`)". Carried item 4: "analytics tool and source reads still use `json_extract` on `payload`; they return no tools for newly ingested hook facts until moved to the `tool` column. The compacted ledger has no payloads, so this is now also true of every historical row."

Settled by this brief:
- `AnalyticsFilter` gains `NormEvents, Events, Tools, Models, Sources, ConversationIDs []string` and `TZ *time.Location` (nil means UTC). Same semantics as `Repos`: empty means no constraint, OR within a list, AND across lists. `All=1` is the serve layer's job (it sets `From` to `time.Unix(0,0)`); add no field for it.
- `factWhere` uses the columns `kind`, `plan`, `tool`, `source`, `norm_event`, `event`, `model`, `conversation_id` (`kind` and `plan` replace `wf_kind(path)` and `wf_plan(path)` for facts). `rejWhere` keeps the `wf_` functions (the `rejections` table has no such columns) and ignores the new keys.
- Delete `toolExpr`, `sourceExpr`, `shaExpr`; the reads in `Facets`, `Summary`, `Series` (group `tool`, `source`, `kind`, `plan`), `Executions`, `Conversations`, `Explore` and `WindowScores` use `tool`, `source`, `sha`, `kind`, `plan` columns. For `Explore`, `tool` is only shown for `type='hook_event'` rows, as now.
- Behaviour is otherwise unchanged: do not change signatures, ordering, paging or counts. (Later units do that.)
- `Series` accepts the new group names `norm_event`, `model`, `conversation_id` too (a map entry each); the serve layer still restricts the legacy route, do not touch it.

## Done evidence

- `grep -n 'json_extract\|wf_kind\|wf_plan' tools/workflow/internal/store/analytics.go` shows `wf_` only inside `rejWhere`, the `init` registrations and the rejection queries, and no `json_extract`.
- New test: a hook fact appended through `Tenant.Append` with `Tool:"Read"`, `Source`, `NormEvent`, `Model` set and a `raw` with no `payload` appears in `Facets().Tools`, is returned by `Series` grouped by `tool`, and is selected by a filter on each of the six new keys (one assertion per key, and an AND of two keys).
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/serve` passes (the existing tests are the regression check). `go vet ./internal/store` and `gofmt -l internal/store` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
