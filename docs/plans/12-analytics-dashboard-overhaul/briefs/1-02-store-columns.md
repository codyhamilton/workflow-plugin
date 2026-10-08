# Brief: 1-02 — Ledger columns, indexes and Append

Consumer: a Go worker (Sonnet-tier) changing the store so unit 1-05 can write slim hook facts with extracted analytics fields.
Owned paths: `tools/workflow/internal/store/store.go`, `tools/workflow/internal/store/store_test.go`. Touch nothing else (not `analytics.go`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report (`git commit -- <paths>`); other units commit in parallel.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-02-store-columns.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-01, 1-03, 1-04.
Budget: 4 files to read, about 150 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Ledger shape and compaction", bullets "New columns on facts" and "Schema migration" (binding).
2. `tools/workflow/internal/store/store.go` — lines 22-50 (migrations), 127-152 (migrate), 246-296 (FactRow, Append).
3. `tools/workflow/internal/store/store_test.go` — `TestMigrationsVersioned` (line ~281) and `TestAppendIdempotent`.
4. `tools/workflow/internal/store/analytics.go` lines 20-45 — `planOf` and `keys.Kind`, which you reuse (same package) without editing.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

`facts` has the new columns and indexes, filled at insert, and an existing 10 GB ledger opens as fast as today.

## Contract

From DESIGN.md "Ledger shape and compaction":
- New columns on `facts`: `norm_event`, `tool`, `model`, the artifact `kind` and `plan`, `source` and `sha`, `tok_in`, `tok_out`, `tok_cache_read`, `tok_cache_write`, `tok_reasoning`, `cost_reported`. All filled at insert.
- `rejections` gains an index on `at`. `facts` gains `(type, ts)` and `(ts, harness, norm_event)` indexes.
- "The migration runs inside `Open()`, as today, and is `ADD COLUMN`/`CREATE INDEX`-cheap only. It never rewrites rows."
- `facts` stays append-only; `Append` stays `INSERT OR IGNORE` by row hash.

Settled by this brief:
- One new migration appended to `migrations` (never edit earlier ones). Text columns are `TEXT NOT NULL DEFAULT ''`, integer columns `INTEGER NOT NULL DEFAULT 0`, `cost_reported REAL` nullable (NULL means not reported). Existing rows keep the defaults; filling them is Phase 2's compaction.
- `FactRow` gains exactly these fields (unit 1-05 codes to them):
  ```go
  NormEvent, Tool, Model, Source, SHA string
  TokIn, TokOut, TokCacheRead, TokCacheWrite, TokReasoning int64
  CostReported *float64
  ```
  `kind` and `plan` are not fields: `Append` computes them from `Path` with `keys.Kind` and `planOf` (empty for a non-artifact path).
- Add `func (t *Tenant) Dir() string` returning the tenant directory (ingest needs it for the archive). Check it does not already exist under another name.
- Do not add the tenant lock here; it belongs to Phase 2 with its outcome.

### Keep untouched

`TestMigrationsVersioned` semantics (update its expected count only). The writer-group, `submit` and WAL pragmas. The existing columns and indexes. `wf_kind`/`wf_plan` registration in analytics.go.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/store/` → pass, including new tests: (a) a ledger created at the previous user_version with rows opens, migrates, and old rows read back with defaults and NULL cost; (b) `Append` of a FactRow with every new field round-trips them through a SELECT; (c) an artifact_version row at `docs/plans/01-x/DESIGN.md` gets kind and plan filled and a hook row gets empty; (d) `EXPLAIN QUERY PLAN` for `WHERE type=? AND ts BETWEEN ? AND ?` uses the new index; (e) re-Append of the same row hash is still `false`.
- `go test ./...` from `tools/workflow` → same pass/fail set as before your change (record the baseline first; other units are changing ingest in parallel, so a failure only in `internal/ingest` is not yours, report it).
- Timing note in the report: migration on a copy of a 100k-row test ledger completes in well under a second (no row rewrite).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
