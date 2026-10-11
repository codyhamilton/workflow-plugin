# Brief: 3-05 — Usage measures: tokens, model calls, cost and Claude message dedupe

Consumer: a Go worker (flash-tier); 3-06 serves the measures, 3-08 and 3-09 reuse its call selection.
Owned paths: `tools/workflow/internal/store/usage.go` (new) and `usage_test.go` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/3-05-usage-measures.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 3-01, 3-04.
Runs alongside: 3-06.
Budget: 6 files to read, about 350 lines to write, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...` from the repo root.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Analytics reads: the matrix rows for `model_calls` … `unpriced_calls`, and **Cost** (binding).
2. `tools/workflow/internal/store/pricing.go` (3-01) — `Cost`, `Tokens`.
3. `tools/workflow/internal/store/query.go` (3-04) — `QueryParams`, `QueryResult`, `usageQuery`, `Measures()`, the grouping and top-N code you reuse.
4. `tools/workflow/internal/ingest/extract.go` lines 36-95 and `normalise.go` lines 1-20 — what a usage fact stores; the `usage` `norm_event`.
5. `docs/plans/12-analytics-dashboard-overhaul/IMPLEMENTATION.md` — Carried items 1-3.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The seven usage measures answer through `Query`, one model call counted once, priced by `Cost`, and the number for a fixture conversation equals a hand computation.

## Contract

Design, cited: "`model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `cost_usd`, `unpriced_calls` | `harness`, `repo_id`, `model`, `conversation_id`" and the Cost rule. Carried item 3: "8 of 13,612 local Claude `message_id`s repeat, so reads need dedupe."

Settled by this brief:
- A model call is a row with `type='hook_event' AND norm_event='usage'`. Filter with `factWhere` as the other measures do; the filter keys that do not apply follow 3-04's ignored-filters rule (usage dims are `harness`, `repo_id`, `model`, `conversation_id`; `kind`, `plan`, `source`, `tool`, `norm_event`, `event` are ignored and listed).
- Dedupe (Claude only): a Claude call's message id is `json_extract(raw,'$.backfill.ref')` (the stored envelope has no payload; backfilled rows keep the id there; the local ledger has 13,612 Claude usage rows with 13,604 distinct ids). Group the Claude usage rows by (`conversation_id`, that id) and keep one row per group: the row with the largest `tok_out`, ties by lowest `row_hash`. Rows with no id (live-captured facts, or other harnesses) are each their own call. Before relying on it, grep `tools/hooklog/tests/fixtures/ingest_policy.json` and `ingest.go` for whether a live fact exposes the message id at top level of the envelope; if it does, `COALESCE` it in as the key. If neither source gives a key for live facts, say so in the report (it is a known limit: live Claude repeats are not deduped).
- `model_calls` is the deduped call count. `tokens_*` sum the columns of the kept rows. `cost_usd` is the sum of `Cost(harness, model, Tokens{…}, cost_reported)` over kept rows, computed per row in Go from a grouped fetch (group rows by `harness, model, cost_reported IS NULL`-class in SQL if you can; correctness over speed here, 3-11 measures speed). `unpriced_calls` counts kept rows where `Cost` says not priced.
- The dedupe must be one helper function other code can reuse (3-09 will): `func usageRowsWhere(f AnalyticsFilter) (sql string, args []any)` returning a `WITH kept AS (...)` fragment or an equivalent documented selection. Export nothing else.
- Set `usageQuery` in an `init()` in `usage.go`. Reuse 3-04's bucketing, `tz`, dims and top-N code; if reuse needs a small refactor inside `query.go`, you may edit only the lines that extract a function without changing behaviour, and say so in the report (3-04's tests must stay green).

## Done evidence

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store -run 'Usage|Query|Cost' -v` passes. New tests: a fixture conversation of 4 usage facts (one Claude pair repeating an id with `tok_out` 10 then 40; one Codex call `In=1000, CacheRead=400` model `kimi-k2.5`; one OpenCode call with `cost_reported=0.25`; one call with an unknown model and no reported cost) gives `model_calls=3` (the repeated Claude pair counts once); write every expected literal by hand in a comment beside the assertion: `tokens_out` counts 40 not 50, `cost_usd` equals the hand-computed sum from `tools/transcript/pricing.json` rates (Codex charged for 600 fresh, not 1000), reported 0.25 passes through unchanged, `unpriced_calls=1`; one test groups by `model` and by `harness` with a dimension pair.
- `go vet ./internal/store`, `gofmt -l internal/store` print nothing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
