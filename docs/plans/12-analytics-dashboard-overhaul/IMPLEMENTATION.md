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


### 2-01-lock-meta-health

Built (52e2358): tenant-dir `.lock` with shared `Open` and exclusive `OpenExclusive` (`ErrLocked`, `TrySharedLock`), migration 5 `meta` table seeded `compaction='complete'` for an empty ledger, `Meta`/`SetMeta`/`CompactionState`/`CompactionStateOf` (read-only), `Raw()` only under exclusive. `serve.Preflight` runs before listen; locked tenant requests return 503; `/v1/health` gains `compaction`. `TestMigrationFast100k` timing assertion gated off under `-race`. `go build`, `go vet`, `go test ./...` and `go test -race ./internal/store/` pass. Surfaces: `internal/store/{lock.go,store.go,store_test.go,lock_test.go,race_on_test.go,race_off_test.go}`, `internal/serve/{serve.go,compaction_state_test.go}`, `cmd/workflow/main.go`. Deviations: migration 5 uses `CREATE TABLE IF NOT EXISTS` because two tests rewind `user_version` without dropping `meta` (one outside owned paths); added exported `store.TrySharedLock`; serve legacy fixture hand-builds a version-4 `facts` table. Carried item 7 resolved. Worker: flash.

### 2-02-archive-torn-frame

Built (7d4b608): `archive.Read` tolerates a torn (truncated) last frame and returns earlier lines; checksum-corrupt frames, trailing garbage and non-JSON lines still error. New `Repair(tenantDir) (Repaired, error)` rewrites a damaged file atomically as one frame of surviving lines; healthy files are untouched. Archive tests pass, gofmt and vet clean. Surfaces: `internal/archive/{archive.go,archive_test.go}`. Deviation: brief's contract ("corruption followed by good data errors") and done-evidence conflict; resolved by treating truncated frames as torn and checksum-corrupt frames as corruption. Limit: until `Repair` runs, a frame appended after a torn tail is not visible to `Read`; 2-03 must call `Repair` first. Carried item 6 resolved.

### 2-03-compact-engine

Built (faa040e, flash worker): `internal/compact.Run(ctx, *store.Tenant, Options)` requires `OpenExclusive`, calls `archive.Repair`, resumes from meta `compact_cursor`, and processes rowid batches in one transaction each (archive body verbatim, then remove or collapse per policy, strip payload, fill columns, advance cursor, commit); sets meta `compaction='complete'` at the end; WAL checkpoint every 20 batches and counts-only progress every 50. Added `store.PlanOf` and `ingest.Envelope`. Tests (equivalence with ingest, outcome, resume at both crash points, repair, pre-existing survivor, requires-exclusive) pass under `-race`; full `go build`/`go test ./...` pass. Throughput about 30,100 rows/s on a synthetic 50k all-keep ledger. Surfaces: `internal/compact/`, `internal/store/plan.go`, `internal/ingest/ingest.go`. Deviations: planning does a read-only SELECT for earlier-batch collapse survivors before the archive append. Contradiction named: the brief's collapse survivor `ts` is the minimum over the part, but ingest keeps the first-arriving `ts`; equal only when parts arrive in ts order.

### 2-04-ledger-compact-command

Built (82b785f, flash worker): `workflow ledger compact --tenant-dir <dir>` (`cmd/workflow/ledger.go`, `main.go` usage and case). Opens exclusive (locked tenant exits 1), prints before counts and bytes, refuses with `need X MiB, have Y MiB` when free space is short (`compact.NeedBytes`, `compact.FreeBytes`), runs `compact.Run` with progress under SIGINT/SIGTERM (interrupt exits 1 and resumes cleanly), then VACUUM and `wal_checkpoint(TRUNCATE)`, prints after counts and bytes and elapsed; a completed ledger skips straight to VACUUM; other argument shapes exit 2. Build, vet, gofmt and `go test ./...` pass. Surfaces: `cmd/workflow/{ledger.go,ledger_test.go,main.go}`, `internal/compact/{finish.go,finish_test.go}`. Deviations: test helper clears `compaction` and `compact_cursor` meta so the legacy fixture reads `required`. Known: a non-existent `--tenant-dir` is created and migrated (exit 0, rows=0); the command skips when meta is `complete` while `compact.Run` would still repair leftover payload rows (unreachable on a genuine ledger).

### 2-05-kickoff-compaction-on-copy

Built (7e78aa1, flash worker): copied the live ledger (11.6 GB) with SQLite online backup (read-only on the live file; mtime and size unchanged) to `/var/tmp/workflow-compact-copy/data/local`; wrote `precounts.txt` (9 counts: facts_total 9,273,647, hook_total 9,272,034, removed 45,836, delta_total 8,792,203, delta_parts 14,902, expected_archive_hashes 9,226,198); built the binary there; started `workflow ledger compact` detached (PID in `compact.pid`, log `compact.log`). Space check passed (need 7,705 MiB, have 18,322 MiB). Observed about 10,800 rows/s on this delta-dense ledger, estimate about 14 min. Surfaces: none in the repo (report only). Deviation: the first launch was SIGTERMed at the tool timeout and resumed cleanly; relaunched with `setsid --fork`. The `before:` line in the log therefore reflects the partly compacted copy; `precounts.txt` was taken before the first start.

### 2-06-verify-compacted-copy

Built (cf457ea, flash worker): `internal/compact/verify_test.go` `TestVerifyCopy` (env-gated, skipped without `WORKFLOW_VERIFY_DIR` and `WORKFLOW_VERIFY_PRE`), subtests a to g. Against the compacted copy all pass: 0 removed events; 14,902 delta rows = 14,902 distinct = `delta_parts`; 0 hook rows with a payload; 9,226,198 distinct archive hashes = expected; `/v1/health` reports `compaction: complete`; facts 450,510 (hook 448,897) as predicted; meta `complete`. Compaction took 12m52s on the resumed run. `ledger.db` 295,919,616 bytes (from 11,618,521,088), archive 756,356,590 bytes; Open Question 3: the 1.5 GB estimate held with about 5x headroom. The copy (about 1.0 GiB now) stays at `/var/tmp/workflow-compact-copy/` for Phase 3's benchmark. Surfaces: `internal/compact/verify_test.go`. Deviations: none. Known: the log `before:` line is from the resumed run and does not equal the true pre-compaction size.
