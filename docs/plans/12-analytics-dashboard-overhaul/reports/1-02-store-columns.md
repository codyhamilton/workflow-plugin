# Report: 1-02 store columns

Status: done with concerns (the new columns break two existing, unowned things; fixes named below).

## Changed
- `tools/workflow/internal/store/store.go`: migration 4 (13 `ADD COLUMN`s on `facts`; indexes `facts_type_ts(type,ts)`, `facts_ts_harness_event(ts,harness,norm_event)`, `rejections_at(at)`); `FactRow` gains the 11 contracted fields; `Append` inserts them and computes `kind`/`plan` via `keys.Kind`/`planOf(Path)`; `func (t *Tenant) Dir() string` (did not exist). Imports `keys`.
- `store_test.go`: `TestMigrationFromPreviousVersion` (a), `TestAppendNewColumns` (b, c, e), `TestTypeTsIndexUsed` (d), `TestMigrationFast100k`. `TestMigrationsVersioned` unchanged (it compares to `len(migrations)`).

## Evidence
- Baseline `go test ./...` (before): all packages ok.
- After: all new store tests pass. Migration of a 100k-row copy: 97 ms (ADD COLUMN plus building the 3 new indexes, no row rewrite).
- After, `go test ./...` fails in two places, both caused by this change:

1. **Store `TestAnalyticsOutcome/facets`, `TestAnalyticsFacets`** (tools list empty). Cause: `analytics.go:168-169` selects `toolExpr AS tool ... GROUP BY tool HAVING tool != ''`. With a real `facts.tool` column, SQLite resolves `tool` in GROUP BY/HAVING to the column (all ''), not the alias. The brief names the column `tool` and forbids editing analytics.go, so I did not fix it. Verified fix (reverted here): rename the alias to `tname` in lines 168-169 (`AS tname ... GROUP BY tname HAVING tname != '' ORDER BY n DESC, tname ASC`); store package then passes. Line 464-466 (`AS tool` in a subquery) is not yet failing but is the same hazard. Same for `event` is unaffected (already a column).
2. **Serve `TestAdvisoryReads/backfill`** (`tenant unavailable`). Cause: `internal/serve/reads_test.go:318+` fakes an old tenant by setting `PRAGMA user_version = 1` on an already fully migrated db; migrations 3+ rerun, and migration 4's `ADD COLUMN` fails with duplicate column. This is a test artefact (real v1 databases lack the columns). Fix in that test: build the version-1 db by dropping columns is impractical, so create it from `migrations[0]` only, or make the test also `DROP` the new columns/indexes. Not in my owned paths.

## Deviations / contradictions
- Brief says "go test ./... same pass/fail set as before"; that cannot hold with a `tool` column and an unmodified analytics.go (item 1). Contradiction between "column named `tool`" + "touch nothing else" and the existing alias. Left unresolved for the coordinator; nothing else deviates.
- Committed despite the failures because both fixes are outside owned paths; the branch is red on those two tests until analytics.go (alias) and reads_test.go are fixed.
