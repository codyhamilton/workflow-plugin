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

### 1-06-end-to-end-and-delta-share

Built (55887c7, flash worker): `serve/ingest_policy_test.go` with `TestIngestPolicy`, six subtests that post the shared fixture to the `POST /v1/ingest` handler and check remove, delta collapse, resend, verbatim archive line, no stored `payload`, and column values. Both amendments applied: fixture `first_status` corrected to `duplicate` for `fx-opencode-43/-44/-46`; `archive.Append` encodes with HTML escaping off, with a round-trip test. Open Question 2: 0 of 8,327,466 local deltas lack the collapse key (0.00%, under the 1% threshold), so Phase 2 needs no fallback key. Surfaces: `internal/serve/ingest_policy_test.go`, `internal/archive/{archive.go,archive_test.go}`, the fixture. Deviation: edited the fixture and `internal/archive/` beyond the brief's owned paths because its amendments required it.

### Phase 1 verification

Run by the orchestrator after the delegated check agent was stopped. `go build ./...` and `go test ./...` pass in every package under `tools/workflow`; plugin tests 7 pass, 0 fail; `TestIngestPolicy` passes all six subtests through the real `/v1/ingest` handler, covering each outcome bullet. Not run: a separate server process against a live port; the handler-level test is the proof. `artifact_feedback` on the briefs and reports was not run: the workflow MCP server failed to connect (ENOENT).

### Carried

1. Phase 3: cost must not double-charge cached input; Codex `input_tokens` already includes it.
2. Phase 3: OpenCode `cost` of 0 is treated as not reported.
3. Phase 3: 8 of 13,612 local Claude `message_id`s repeat, so reads need dedupe.
4. Phase 3: analytics tool and source reads still use `json_extract` on `payload`; they return no tools for newly ingested hook facts until moved to the `tool` column.
5. Phase 2: the tenant-dir lock was deferred from Phase 1 to Phase 2.
6. Phase 2: `archive.Read` errors for a conversation whose last frame was torn by a crash; compaction and reads must tolerate or repair it.
7. `TestMigrationFast100k` fails with "migration too slow" under `-race` only.
8. The design text says `/v1/facts`; the real route is `/v1/ingest`.
9. The workflow MCP server does not start (ENOENT), so `artifact_feedback` has not run on Phase 1 briefs or reports.

## Phase 2 — Historical compaction and reclaim

Units: six, from `refine` (briefs in `briefs/`). 2-01 and 2-02 parallel; then 2-03, 2-04, 2-05, 2-06 in sequence.

Carried items from Phase 1 placed: 5 (tenant-dir lock) in 2-01; 6 (torn archive frame) in 2-02, with 2-03 repairing before it runs; 7 (`TestMigrationFast100k` under `-race`) in 2-01; 8 (`/v1/facts` naming) corrected in `DESIGN.md` at refine. Items 1 to 4 stay carried to Phase 3. Item 9 still applies: `artifact_feedback` has not run on the Phase 2 briefs (the workflow MCP server did not connect).

