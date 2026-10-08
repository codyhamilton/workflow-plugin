# Implementation: Analytics Dashboard Overhaul

## Run

- Tool: Claude Code (orchestrator on Sonnet 5.5)
- Session: https://claude.ai/code/session_011T4Vh5cPS7acScndWmdobz
- Started: 2026-10-09
- Branch: plan/12-analytics-dashboard-overhaul

## Phase 1 — Event policy, archive and slim ingest

Units: six, from `refine` (briefs in `briefs/`). 1-01 to 1-04 parallel; 1-05 then 1-06 in sequence.

### 1-03-plugin-remove-list

Built (9f2c7de): `recordHooklog` skips the four removed events by `hook_event_name`; the list sits in a marked `remove-list` block in `src/index.ts`; README updated. Plugin tests 7 pass, 0 fail (were 5 pass, 2 fail with tests updated first). Surfaces: `packages/opencode-workflow-hooks/{src/index.ts,tests/test_hooks.mjs,README.md}`. Deviations: none.

### 1-01-archive-package

Built (64404aa): new `tools/workflow/internal/archive` with `Line`, `Entry`, `Append`, `Read`; one zstd frame per file per call, package mutex, file-name escaping per brief. `go test -race`, `go build ./...`, `go vet` pass. Surfaces: `tools/workflow/internal/archive/`, `go.mod`, `go.sum`. Deviations: none. Limit for 1-05: a crash mid-write can leave a torn last frame, which makes `Read` error for that conversation instead of skipping it.

### 1-04-normalise-and-extract

Built (381a85b): `Derive(harness, event, payload)` yields `norm_event`, tool, model, token fields and reported cost for Claude, Codex, OpenCode and Cursor; shared fixture `tools/hooklog/tests/fixtures/ingest_policy.json` (62 facts with expectations and per-harness totals). `ingest` package tests and `go vet` pass; Claude totals match `dedupe_usage`. Surfaces: `tools/workflow/internal/ingest/`, the fixture. Deviations: Claude and OpenCode `transcript.assistant_message` map to `usage` only when the payload carries usage or tokens, else `assistant_message` (1-05 must not assume otherwise). Design gap: the design's OpenCode row omits `tokens`; extracted them into the same columns.

### 1-02-store-columns

Built (c623dcb): migration 4 adds 13 columns and 3 indexes; `FactRow`, `Append` (computes kind and plan from the path) and `Tenant.Dir()`. New store tests pass; migrating a 100k-row ledger took 97 ms. Surfaces: `tools/workflow/internal/store/store.go`, `store_test.go`. Deviation: two existing tests outside the owned paths now fail: `TestAnalyticsFacets` (`analytics.go:168-169` groups by alias `tool`, which now resolves to the empty `facts.tool` column; rename the alias to `tname`) and `TestAdvisoryReads/backfill` (fakes an old DB by resetting `user_version` to 1, so migration 4 hits duplicate columns; needs a real version-1 database). Both amended into brief 1-05.

### 1-05-ingest-policy

Built (cae2cf5): new `internal/ingest/policy.go` (policy table, `Policy()`, `CollapseHash()`); `ingest.go` answers removed events `accepted` before the secret check (no row, rejection or archive line), collapses deltas to one fact per part, strips `payload` from hook facts and fills the extracted columns, archives each kept or collapsed body under its own hash in one write before the insert. Remove-list equality test with the plugin fails when a Go entry is dropped. `go test ./...` passes in every package. Amendment from 1-02 applied: `tool` alias renamed `tname` in `store/analytics.go`; the backfill test builds a real version-1 database. Surfaces: `internal/ingest/`, `internal/store/analytics.go`, `internal/serve/{analytics_test.go,reads_test.go}`.
Deviations and concerns: fixture statuses are wrong (later deltas of a part return `duplicate`, the fixture expects `accepted`; amended into 1-06); `archive.Append` HTML-escapes `<`, `>`, `&`, so the archive is not verbatim (amended into 1-06); `serve/analytics_test.go` inserts tool-bearing hook facts directly with `Tool` set, and analytics show no tools for newly ingested hook facts until Phase 3 moves reads to the `tool` column; test (a) counts by event, not conversation; `TestMigrationFast100k` fails under `-race` only ("migration too slow").
