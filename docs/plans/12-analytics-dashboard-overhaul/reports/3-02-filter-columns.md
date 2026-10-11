# Report: 3-02 — Shared filter keys and column-based reads

Status: **done**

## What changed

- `tools/workflow/internal/store/analytics.go` (26 insertions, 20 deletions):
  - `AnalyticsFilter` gains `NormEvents, Events []string`, `Tools, Models, Sources []string`, `ConversationIDs []string`, and `TZ *time.Location` (nil means UTC). No `All` field (serve's job).
  - `factWhere` now filters the columns `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`. `rejWhere` is unchanged: it keeps `wf_kind(path)`/`wf_plan(path)` and ignores the new keys.
  - Deleted `toolExpr`, `sourceExpr`, `shaExpr`. `Facets`, `Summary`, `Series` (groups `tool`, `kind`, `plan`, `source` now columns; added `norm_event`, `model`, `conversation_id` group entries), `WindowScores` (`kind=?`), `Executions` (`kind='brief'`, plan from the CTE), `Conversations` and `Explore` read the columns. Explore still blanks `tool` for non-`hook_event` rows.
  - Signatures, ordering, paging and counts are unchanged.
- `tools/workflow/internal/store/analytics_test.go` (73 insertions): the fixture's `addFacts` now sets `Tool`, `Source` and `SHA` on `FactRow` (it previously encoded them only in `raw`, which the old `json_extract` reads decoded). New `TestAnalyticsColumnReads`.

## Done evidence

`grep -n 'json_extract\|wf_kind\|wf_plan' analytics.go` — before (HEAD) 22 hits including `json_extract` at 86-88 and `wf_` throughout the reads; after, `wf_` only at the `init` registrations (23, 24, 28), `rejWhere` (125, 126) and the rejection arm of `Explore` (477), and no `json_extract`. Matches the brief.

    cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store ./internal/serve
    ok  .../internal/store 0.897s
    ok  .../internal/serve 2.822s
    go vet ./internal/store   # prints nothing
    gofmt -l internal/store   # prints nothing

`TestAnalyticsColumnReads` appends a hook fact via `Tenant.Append` with `Tool:"Read"`, `Source`, `NormEvent`, `Model` set and a `raw` with no payload; it appears in `Facets().Tools`, in `Series` grouped by `tool` (and by `norm_event`, `model`, `conversation_id`), and is selected by a `Summary` filter on each of the six new keys plus an AND of two.

## Departures from the brief

- The fixture (`addFacts`) had to start filling the new columns. It is inside the owned path; the old reads decoded `source`/`sha`/`tool_name` from `raw`, so switching reads to columns requires the fixture to populate them. No assertion changed.
- `Executions`: the CTE now selects `plan` and the report-path check uses `b.plan` instead of `wf_plan(b.path)`, so no facts read calls `wf_plan`. Behaviour is identical (`Append` fills `plan` with `planOf(path)`).
- No other departures.

## Contradictions

None. The brief's grep evidence ("`wf_` only inside `rejWhere`, the `init` registrations and the rejection queries") is consistent with the code after this change.

## Known problems

- `TZ` is added but unused here (buckets remain UTC), and the six new filter keys are not yet populated by `serve/`. Both are deferred to later units by this brief, not defects. No non-trivial bug found outside the done evidence.

## Unfinished work

None for this brief. Later units must wire `serve/` to the new keys and `TZ`, and expose facets `models`/`norm_events`.
