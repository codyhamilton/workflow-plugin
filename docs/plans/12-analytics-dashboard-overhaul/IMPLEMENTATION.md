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

### Phase 2 verification

Run by a separate Sonnet subagent against a small legacy-shaped copy (30,401 rows, built read-only from the live ledger; the live ledger was never modified) and a read-only spot check of the compacted real copy. Every bullet of the Phase 2 outcome passed. `ledger compact` reported before and after rows and bytes (30,401 to 1,846 rows). 192 removed-event rows became 0. 28,418 delta rows became 55, the distinct key count. 0 hook rows carried a payload. 29,809 distinct archive hashes matched the pre-compaction non-removed set exactly. `/v1/health` went from `required` to `complete`. A running compaction made `serve` refuse to start and a second compaction fail with the lock error. SIGINT then rerun produced the same facts and archive hashes as an uninterrupted run, and a third run was a no-op. On the real copy: 450,510 facts, 448,897 hook rows, `ledger.db` 295,919,616 bytes (from 11,618,521,088, under 1.5 GB), archive 756,356,590 bytes, compaction 12m52s on the resumed run. `go build`, `go vet`, `go test ./...` and `-race` on the touched packages pass. `artifact_feedback` on the Phase 2 briefs and reports was not run: the workflow MCP server failed to connect (ENOENT). The compacted copy remains at `/var/tmp/workflow-compact-copy/` for Phase 3's benchmark.

### Carried

1. Phase 3: cost must not double-charge cached input; Codex `input_tokens` already includes it.
2. Phase 3: OpenCode `cost` of 0 is treated as not reported.
3. Phase 3: 8 of 13,612 local Claude `message_id`s repeat, so reads need dedupe.
4. Phase 3: analytics tool and source reads still use `json_extract` on `payload`; they return no tools for newly ingested hook facts until moved to the `tool` column. The compacted ledger has no payloads, so this is now also true of every historical row.
5. Collapse survivor `ts`: compaction uses the minimum over the part, ingest keeps the first-arriving part's `ts`; they differ when parts arrive out of order. Pick one rule.
6. `workflow ledger compact` creates and migrates a non-existent `--tenant-dir` (exit 0, rows=0) instead of failing; it also skips when meta is `complete` while `compact.Run` would still repair leftover payload rows (unreachable on a genuine ledger).
7. The keyless-delta keep path (delta without a collapse key) is covered by unit tests only; the real ledger has none.
8. The workflow MCP server does not start (ENOENT), so `artifact_feedback` has not run on Phase 1 or Phase 2 briefs or reports.

## Phase 3 — Fast analytics API with usage and cost

Units: thirteen, from `refine` (briefs in `briefs/`, named `3-NN-<slug>.md`). Order: 3-01, 3-02, 3-03 parallel; then 3-04 (after 3-02); then 3-05 and 3-06 parallel; then 3-07 (after 3-06), with 3-09 (after 3-05 and 3-06) alongside it; 3-08 after 3-05 and 3-07; 3-10; 3-11; 3-12 only if 3-11 finds a miss; 3-13 last. `artifact_feedback` was not run on these briefs (the workflow MCP server failed to connect, ENOENT).

### Carried items placed

1. Cached input double charge: 3-01 (`Cost` subtracts Codex cached input from fresh input; hand-computed test); checked again in 3-13.
2. OpenCode `cost` of 0 as not reported: 3-01 (a reported value of 0 or less falls back to token pricing; `extract.go` already stores nil).
3. Repeated Claude `message_id`: 3-05 (one call per conversation and message id, keeping the row with the largest output; reused by 3-08 and 3-09). Limit: the id exists only in `backfill.ref` on backfilled rows; live-captured Claude facts have no stored id, so repeats among them are not deduped unless 3-05 finds the id in the envelope.
4. Tool and source reads off `json_extract`: 3-02 (all facts reads use the `tool`, `source`, `sha`, `kind`, `plan` columns).
5. Collapse survivor `ts`: 3-03 (rule chosen at refine: first-arriving, so compaction changes to match ingest).
6. `ledger compact` creating a non-existent `--tenant-dir` and skipping on `complete` meta: stays carried (compaction CLI, no analytics reader).
7. Keyless-delta keep path covered by unit tests only: stays carried (the real ledger has none, and no Phase 3 read depends on it).
8. `artifact_feedback` not run on earlier briefs and reports: stays carried (infrastructure).

New, from refine: `tools/transcript/pricing.json` holds only seven Cursor models, so most local calls will be unpriced unless a cost was reported. 3-11 records the share. Adding rates is outside this plan's scope and is left to the user.

### 3-02-filter-columns

Built (702ba01, flash worker): `AnalyticsFilter` gained `NormEvents`, `Events`, `Tools`, `Models`, `Sources`, `ConversationIDs`, `TZ`; `factWhere` filters real columns; `Facets`, `Summary`, `Series`, `WindowScores`, `Executions`, `Conversations`, `Explore` read the `tool/source/sha/kind/plan/norm_event/model/conversation_id` columns, with no `json_extract` left (carried item 4). New `TestAnalyticsColumnReads`; `go test ./internal/store ./internal/serve`, vet and gofmt pass. Surfaces: `internal/store/{analytics.go,analytics_test.go}`. Deviations: none beyond fixture adjustments. `TZ` and serve wiring are left to 3-06.

### 3-03-collapse-survivor-ts

Built (d1af2e2, flash worker): compaction keeps the first-arriving part's `ts` as ingest does (carried item 5); `minInto` and the retime op removed. `TestCollapseSurvivorFirstArrival` added, `TestPreexistingSurvivor` updated; compact and ingest tests, vet and gofmt pass. Surfaces: `internal/compact/`. Deviations: none.

### 3-01-pricing-cost

Built (70b9d16, Sonnet retry): the first flash run died on opencode's own "database is locked" before any change (three flash workers started at once); retried once on Sonnet. `store.Cost`, `Tokens` and `PricedModel` in `internal/store/pricing.go`, with the embedded `pricing_table.json` (byte copy of `tools/transcript/pricing.json`, equality test). Codex cached input is subtracted from fresh input (carried item 1); a reported cost of 0 or less falls back to token pricing (item 2). Seven `Cost|Pricing` tests, vet and gofmt pass. Deviations: none. Known: the table holds only seven Cursor models, so most local models are unpriced unless a cost was reported.

### 3-04-query-engine

Built (f57db2b, flash worker): `internal/store/query.go` with the measure matrix, `Measures()`, `Buckets`, `QueryParams/QueryResult`, `ErrUnsupported`, and `(*Tenant).Query` for the six non-usage measures (tz bucketing, top-N folding, `ignored_filters`); 11 tests, package green, vet and gofmt clean. Deviations: the usage executor is named `usageQuery` (brief said both `usageExec` and `usageQuery`); measure units `count`/`tokens`/`usd` chosen by the worker.

### 3-05-usage-measures

Built (c80be8e, flash worker): `internal/store/usage.go` registers the usage executor so `model_calls`, `tokens_*`, `cost_usd`, `unpriced_calls` answer through `Query`; Claude rows dedupe on `raw.backfill.ref` keeping the largest `tok_out` (carried item 3); cost computed with `store.Cost`. `usage_test.go` fixture gives `model_calls=3`, `tokens_out=40` (not 50), `cost_usd=0.2504`, `unpriced_calls=1`; usage, query and cost tests pass. Deviations: refreshed 3-04's `TestQueryUsageUnavailable` and 3-06's matching serve assertion (registering the executor invalidates them; test-only edits outside owned paths); brief's "4 usage facts" reconciled to 4 rows. Limit as predicted: live-captured Claude facts have no stored message id, so repeats among them are not deduped.

### 3-06-serve-query-routes

Built (60f1e42, flash worker): `GET /v1/analytics/schema` and `GET /v1/analytics/query` (`internal/serve/analytics_query.go`), `parseFilter`/`canonFilter`/`filterOpts` extended for the six filter keys, `tz`, `all=1` and the query bucket cap, routes registered in `serve.go`. Store and serve tests, vet and gofmt pass. Deviations: none. Known: the `legacyLedger` serve fixture is not a real v4 schema.

### 3-07-keyset-paging

Built (dc8e481, flash worker): `Executions` and `Conversations` page by keyset in SQL, with whole-window counts; `sort.Slice` remains only in `analyticsSeries`. Store and serve tests, vet and gofmt pass. Concerns from the report: page-1 over 20k rows takes about 153 ms (the whole-window `counts` aggregate; the benchmark in 3-11 is the real judge); `splitConcat` splits `group_concat` on `,` so a repo id containing a comma would mis-split; the paging walk tests are store-level, not HTTP.

### 3-09-conversation-route

Built (3f28cbc, flash worker): `Tenant.Conversation(ctx, id)` and `GET /v1/analytics/conversation` (400 missing `id`, 404 unknown, 5,000-event cap with `truncated`), reusing 3-05's deduped call selection; 6 files, store and serve tests, vet and gofmt pass. Interpretation: unpriced kept usage events emit `cost_usd: 0`.

### 3-08-summary-facets-explore

Built (a13d3aa, flash worker): `Summary` gains `model_calls`, `unpriced_calls`, `cost_usd` and the five token sums; `Facets` gains `models` and `norm_events`; `Explore` fetches `limit+1` from facts and rejections separately, merges in Go, and looks up screen verdicts only for the page, with `norm_event`, `model`, `cost_usd` on rows. Store and serve tests, vet and gofmt pass. Deviations: the serve explore exact-column assertion gained `norm_event`/`model`; the `row_hash` tie still uses a temp b-tree (no `(ts DESC, row_hash ASC)` index), a candidate for 3-12 if the benchmark flags Explore.

### 3-10-benchmark-harness

Built (86bde56, flash worker): `internal/serve/analytics_bench_test.go` with env-gated `TestAnalyticsBench` (`WORKFLOW_BENCH_DIR`; copies only `ledger.db` to a temp dir and opens the copy) plus ungated smoke and non-mutation self-tests; vet, gofmt and `go test ./internal/serve` pass. Deviation: the `all` preset is covered on `/query` cases only, because `parseFilter` caps every other route at 400 UTC days and `all=1` returns `400 range too wide`.

### 3-11-run-benchmark-on-copy

Run (flash worker; report in b3145ea): the benchmark on the compacted copy ran 2,063 cases in 38 m 8 s and **243 missed the 500 ms p95 bound**, none returned non-200. Misses by measure: `hook_events` 152 (520 to 1,500 ms), `conversations` 80 (520 to 1,900 ms) plus bare `conversations/30d` and `/90d` (about 570 ms), `facets` (1.5 to 1.8 s), `summary` (530 to 780 ms), `scores` (4.9 to 6.6 s). Everything with `bucket=none` plus a dimension pair is slow; usage measures, `executions`, `explore`, `rejections` and `timeline`-style cases passed. Open Question 1 is answered: a read-side fix is needed (indexes first, then the hourly rollup). Unpriced share: 28,342 of 33,464 usage rows (pricing.json holds seven Cursor models; adding rates is outside this plan). Departure: the live ledger mtime changed during the run because a live `serve` writes it; the benchmark itself only touched the copy.

Brief 3-12 was written for one flash worker and says to stop after the first measure when more than three miss, and five did. The orchestrator split it by measure group: 3-12 (`hook_events`, builds the shared rollup), 3-14 (`conversations`), 3-15 (`facets`, `summary`, `scores`), run in that order; 3-13 now depends on all three. 3-12's budget and scope were amended in its brief.

### 3-12-fix-misses-indexes-rollups

Built (80181fe, flash worker): hook_events fixed with an hourly rollup, `hook_events_hourly` (migration 6; keyed hour, harness, repo_id, norm_event, event, tool, conversation_id; filled by a Go backfill in `open()`, maintained in `Append`'s transaction, read for whole interior hours with the two edge hours from base rows). The covering index was tried first and left 139 of 213 cases over, so it was dropped. Rerun on the compacted copy: 213 of 213 `query/hook_events/` cases under 500 ms p95 (max 146.5 ms, was up to 1,500 ms). Rollup equals base rows over mid-hour windows and duplicate appends (`rollup_test.go`); store, serve and compact tests, vet and gofmt pass. Defect found, outside the unit's owned paths: compaction deletes and rewrites hook_event rows without touching the rollup, so it drifts after any compaction. Placed in new unit 3-16 (phase proof 3-13 now depends on it).

### 3-16-compact-keeps-rollup-exact

Built (132dce4, flash worker): `compact.Run` rebuilds `hook_events_hourly` from base rows in a deferred step on any successful finish (normal, resumed or no-op), via a new `RebuildHookRollup` in `store/rollup.go`. Tests `TestCompactRebuildsRollup`, `TestCompactRebuildsRollupOnResume` (proves drift after a committed first batch, then exactness after resume) and `TestRebuildHookRollup` assert rollup equals base aggregates both ways; store, compact and serve tests, vet and gofmt pass. Deviations: none.

### 3-14-fix-conversations-misses

Built (498e66c, flash worker): migration 7 `conversations_hourly(hour, harness, repo_id, model, conversation_id, n)`, kept current in `Append`, backfilled at open, read with base-row edge hours through the generalized rollup path in `query.go`; plus a page index for the bare `conversations/<preset>` route. Rerun on the compacted copy: 112 of 112 conversations cases under 500 ms p95 (worst 389 ms, was up to 1,855 ms); store, serve and compact tests, vet and gofmt pass. Concerns: `conversations_hourly` is not rebuilt after compaction (placed in unit 3-17); the first upgraded start pays a one-time `ANALYZE facts` and index build on a large uncompacted ledger; the rollup test has no bucket, tz or two-dimension case (placed in 3-17).

### 3-15-fix-facets-summary-scores-misses

Built (7c4f934, flash worker): `facets_hourly` rollup (migration 8, filled at open, kept current in `Append`; whole interior hours from the rollup, edge hours from base rows) takes facets 7d/30d/90d from 1.9, 2.1 and 2.0 s to 3 to 4 ms; `summary` reuses `hook_events_hourly` and `conversations_hourly` for its counts (falls back to the old query for filtered windows) and now sits at 220 to 380 ms. `scores` needed no change: it measured about 33 ms after 3-14's `ANALYZE facts`, so 3-11's 4.9 to 6.6 s came from a missing planner statistics state in the benchmark copy, not from the query. Store, serve and compact tests, vet and gofmt pass. Concerns: `facets_hourly` and the conversations rollup are not rebuilt by compaction (3-17); `Append` now does eight rollup upserts per inserted fact (ingest cost not measured); `scores` depends on `ANALYZE` having run on the ledger.

### 3-17-compact-rebuilds-all-rollups

Built (62b3316, bb546af, flash worker): `RebuildConversationRollup`, `RebuildFacetRollup` and `RebuildRollups` (one registration point) in `store/rollup.go`; `compact.Run`'s deferred step now rebuilds every rollup. Tests: conversations rollup equals a base-only oracle on bucket day and week, two dimensions, UTC and Australia/Sydney; compaction tests assert every rollup equals base rows after `Run` and after a resumed run, including a removal that clears a conversation and an asserted `model` fill. `go vet ./...` and `go test ./...` in `tools/workflow` pass. Deviations: none.
