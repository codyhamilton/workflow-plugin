# Execution report: 4-01 service reads (brief 222, exec 24)

## Done
- `internal/store`: migration 2 (`search` FTS5, `porter unicode61`, one row per content hash); `Promote` indexes
  `pass`/`unscreened` blobs in the screens transaction (invalid UTF-8 skipped); `DropBlob` deletes the row in the same
  transaction as the rejection; `Open` backfills when it ran migration 2 on a version-1 db (before the writer starts).
  Methods: `(*Tenant).Reindex(ctx)`, `LatestScores(ctx) []Baseline`, `Search(ctx, match, limit, keep) []Hit`;
  `Latest.Rejection *RejectionRow` read by `Artifact`. Code in `reads.go` plus small edits in `store.go`.
- `internal/serve`: `Options.Checks *scorer.Checks`; handlers `/v1/checks`, `/v1/baselines`, `/v1/search`
  (`reads.go`); `latest.rejection` on `/v1/artifacts`; helpers `percentile` (R-7, 3 places) and `matchExpr`.
- `cmd/workflow/main.go`: `screenStep` now returns `(step, *scorer.Checks, error)`; checks load whenever
  `WORKFLOW_CHECKS_DIR` is set; no-key line kept, plus `workflow serve: checks design=N brief=N report=N`.

## Evidence
Before (Options.Checks stub only, no handlers): `TestAdvisoryReads` failed at setup, `reads_test.go:127: timed out:
settled docs/plans/09-x/DESIGN.md` (no `rejection` field yet, so a flagged artifact never settled).
After: `go vet ./... && go test -race -count=1 ./...` passes in every package.

```
--- PASS: TestAdvisoryReads
    --- PASS: TestAdvisoryReads/artifacts_shape
    --- PASS: TestAdvisoryReads/checks
    --- PASS: TestAdvisoryReads/baselines
    --- PASS: TestAdvisoryReads/search
    --- PASS: TestAdvisoryReads/tenant_scope
    --- PASS: TestAdvisoryReads/backfill
--- PASS: TestReadsWiring
```

Responses (hash replaced by `aaaa...`):
- artifacts: `{"kind":"design","latest":{"content_hash":"aaaa","conversation_id":"c","received_at":"2026-10-04T17:37:35Z","rejection":null,"scores":[{"check":"q.a","score":0.1}],"screen":{"at":"2026-10-04T17:37:35Z","scorer":"fake","verdict":"pass"},"source":"worktree"},"path":"docs/plans/01-x/DESIGN.md","repo_id":"r","versions":1}`
- flagged: `"rejection":{"at":"2026-10-04T17:37:35Z","reason":"screen:test","stage":"screen"},"screen":null`
- baselines: `{"checks":{"q.a":{"median":0.5,"n":5,"p25":0.3,"p75":0.7}},"kind":"design"}`
- search: `{"hits":[{"content_hash":"aaaa","kind":"design","path":"docs/plans/01-x/DESIGN.md","rank":-1.3519119218066566,"repo_id":"r","snippet":"# one score=0.1 [zebrafinch]\n"}]}`
- checks (nil): `{"checks":[],"loaded":false}`

Also added `TestSearchIndex` in `store_test.go` (invalid UTF-8 skipped, Reindex idempotent and rebuilds, DropBlob removes).

## Departures
- The backfill subtest builds its version-1 db by creating a tenant with the current store, dropping `search` and
  setting `user_version=1`, rather than hand-writing the v1 schema.
- `DropBlob` now runs its own submit (delete index row plus `insertRejection`) instead of calling `AppendRejection`,
  so both happen in one transaction.
- The `mcp` package failed vet mid-run (4-02 in flight); the final full run passed.

## Known / unfinished
- `LatestScores` reads every artifact's latest scores and the caller filters by kind; fine at this scale.
- A flagged-pending artifact has `screen: null` with `rejection` set (no screens row is written for a flag).
