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

### 3-13-phase-proof

Run (flash worker, 0707a11 report): all six Phase 3 outcome bullets checked on the final code. Full benchmark on the compacted copy: 2,063 cases, 0 over 500 ms p95, 0 non-200, worst 463.5 ms (`series/90d`), 20 m 17 s. Schema, 400 on unsupported pairing, `ignored_filters`, `cost_usd` fixture (0.2504), Go tests and Playwright (26 passed) pass.

### Phase 3 verification

Run by a separate Sonnet subagent against a real `serve` process on a scratch copy of the compacted ledger (the copy at `/var/tmp/workflow-compact-copy/` and the live ledger were not touched). `schema` lists 14 measures; unsupported pairings, three dimensions, an unknown measure and a bad `tz` return 400; `hook_events` with a `kind` filter returns 200 with `ignored_filters: ["kind"]`; `tz=Australia/Sydney` buckets carry the +11:00 offset; keyset paging walked 441 executions (9 pages) and 4,668 conversations (10 pages) with no overlap and totals equal to `counts` and `summary`; top-N folds into `__other__` with the sum preserved; `conversation` returns 200, 404 for an unknown id and 400 for a missing one. Seven benchmark filter families (268 cases) on the copy: none over 500 ms p95 (slowest `series/90d` 460 ms). Rollup tables `hook_events_hourly`, `conversations_hourly` and `facets_hourly` equal base-row aggregates in both EXCEPT directions on a scratch ledger before and after `ledger compact` and on the real-copy ledger. `go build`, `go vet`, `go test ./...` pass and `npm run test:e2e` reports 26 passed. `store/analytics.go` has no `json_extract` and no `payload` reference; a newly ingested hook fact with a tool appears in `facets`. The curl-timed worst of five over the live API was 477 ms (`conversations?limit=500`). Open Question 1 is closed: rollups were needed and are built. `artifact_feedback` on the Phase 3 briefs and reports was not run: the workflow MCP server failed to connect (ENOENT).

### Carried

1. Cost is 0 for every Claude and Codex call: `tools/transcript/pricing.json` holds seven Cursor-class models, so 14,715 of 19,759 model calls in the last 30 days (74%) are unpriced and `cost_usd` only reflects reported costs (OpenCode, DeepSeek, OpenRouter). Daily cost series therefore stop at the last day with a priced call. Add rates to `tools/transcript/pricing.json` (and the byte-identical `internal/store/pricing_table.json`) and the site should show `unpriced_calls` beside cost.
2. Phase 4: the benchmark has little headroom (cases at 440 to 477 ms against 500; with a few runs p95 is the max). Cases are dominated by usage measures over `all` and `series/90d`.
3. Phase 4: the API rejects some windows with 400 "range too wide" (`all=1` on `executions` and the non-query routes, `bucket=hour` over 30 days), and `scores` needs `kind`. The site must pick presets and buckets that stay in range.
4. `scores` was fast (about 33 ms) only after `ANALYZE facts` ran (3-14 runs it when it first builds its index); 3-11's 4.9 to 6.6 s came from missing planner statistics. Any ledger the new binary opens runs `ANALYZE` once; a long-lived upgraded ledger that never did would still be slow.
5. Ingest cost: `Append` now upserts into three rollup tables (about eight upserts per inserted fact) in the fact transaction; ingest throughput after this change was not measured.
6. First open of an uncompacted large ledger by the new binary pays a one-time rollup backfill, `ANALYZE facts` and index build (3-14 concern M3); compaction is expected to run first.
7. Claude message dedupe covers backfilled rows only (id lives in `raw.backfill.ref`); live-captured Claude facts have no stored id, so repeats among them are not deduped. The dedupe reads `json_extract(raw, ...)` and stays inside the bound.
8. `workflow ledger compact` creates and migrates a non-existent `--tenant-dir` (exit 0, rows=0) instead of failing; it also skips when meta is `complete` while `compact.Run` would still repair leftover payload rows (unreachable on a genuine ledger).
9. The keyless-delta keep path is covered by unit tests only; the real ledger has none.
10. The workflow MCP server does not start (ENOENT), so `artifact_feedback` has not run on Phase 1, 2 or 3 briefs or reports.
11. Later phase (not Phase 3 scope), from the user: shrink `facts.row_hash` from 64-char hex TEXT to a 16-byte BLOB (the first 128 bits of the existing SHA-256; no rehash, dedupe identities preserved). Saves about 48 bytes per row in the table and about 48 in the unique index (about 40 MB on the 283 MB copy, about 100 GB per billion rows). 64 bits is too small (about 3% chance of a collision at 1e9 rows; 128 bits is about 1e-21). Touches ingest dedupe, archive dedupe by `row_hash`, the delta collapse hash, any API or MCP surface that returns `row_hash`, and the client and spool if they compute it. Needs its own migration, and every rollup and index touching `row_hash`.
12. Done in "Fixer: drop message.part.delta". Later phase (not Phase 3 scope), user decision: drop `message.part.delta` at the source. It moves from `collapse` to `remove` in the shared remove list: the OpenCode plugin stops recording it (the marked remove-list block in `packages/opencode-workflow-hooks/src/index.ts`), and ingest answers it `accepted` with no fact and no archive line; the plugin-versus-ingest remove-list equality test and the shared fixture and `TestIngestPolicy` expectations change with it; `collapse` and `CollapseHash` then have no remaining event, so the brief decides whether the mechanism stays. Historical: `workflow ledger compact` (or a sibling) rewrites the ledger offline under the tenant lock with VACUUM, deleting the roughly 14.9k collapsed delta facts and every `message.part.delta` line from the archive, with no keep-if-incomplete exception, because the parts remain in `message.part.updated`. Measured on the compacted copy: 8,797,023 delta archive lines, 5.8 GB raw and 556 MB compressed of the 721 MB archive (77%); expected archive about 165 MB; per-chunk streaming timing is lost. It must also rebuild every rollup (3-17's `RebuildRollups` does so at the end of compaction).
13. Done in "Fixer: drop message.part.delta" (the amendment is in DESIGN.md "Amendments after sign-off"). Design amendment (from item 12): "hook_events counts a part once" must count parts from `message.part.updated`, not deltas. Phase 3 does depend on delta facts existing in one place: `hook_events` counts, `norm_event` facets and the benchmark's `norm_event` and `event` cases include the roughly 14.9k collapsed delta facts. They stay correct until item 12 lands; after it, counts of OpenCode parts drop by that number and the rollups rebuild on the same compaction. Phase 3's fixtures do not assert a delta count.

## Fixer: drop message.part.delta

A fixer after Phase 3. It closes no phase and carries no `Workflow-Phase` trailer. It resolves Carried items 12 and 13. Briefs: `briefs/fix-01-drop-deltas.md`, `briefs/fix-02-purge-deltas.md`; both built by flash workers.

Built (4bab839, 6dd4ead):
- fix-01: the OpenCode plugin lists `message.part.delta` in its `REMOVE_EVENTS` block and ingest's policy table maps it to `Remove` (accepted, no fact, no archive line, keyed or keyless). The collapse mechanism was dead code and is deleted: `Collapse` action, `collapseKey`, `CollapseHash`, the ingest and `compact.processBatch` branches, `Stats.Collapsed`, the `normalise.go` delta entry. The shared fixture, `TestIngestPolicy` expectations, the plugin-versus-ingest equality test and the plugin README follow. `compact.Run` now deletes delta rows on a legacy ledger.
- fix-02: sibling subcommand `workflow ledger purge-deltas --tenant-dir <dir>`. `archive.Filter` rewrites files atomically (one frame of surviving lines, emptied files deleted, untouched files byte-identical); `compact.PurgeDeltas` runs Repair, batched fact deletes, archive filter and `RebuildRollups` last, under `OpenExclusive`; the CLI then runs VACUUM. It is idempotent and converges after a kill, with no cursor.

Surfaces: `packages/opencode-workflow-hooks/`, `tools/hooklog/tests/fixtures/ingest_policy.json`, `tools/workflow/internal/{ingest,compact,archive,serve,store}/`, `tools/workflow/cmd/workflow/{ledger.go,main.go}`. `hook_events` counts parts from `message.part.updated` now that no delta fact exists; no analytics API or site code assumed deltas.

Deviations: the fix-02 worker delegated to a general subagent against the brief's no-agents line, and exceeded its line budget (about 790 lines, mostly tests). The ledger delta predicate is harness plus event while the archive predicate is event only (harmless on real data). `TestVerifyCopy`'s external precounts may need regeneration (env-gated, not run). `artifact_feedback` is reachable but returned "not delivered" for the fix briefs (the service had no copy yet); earlier phases' note stands.

Verification (separate Sonnet subagent, fresh copy of the compacted real-ledger copy; the live ledger and the source copy were not touched): facts 450,510 to 435,608 (14,902 deltas removed, 0 left); archive 756,356,590 to 151,027,095 bytes (8,797,023 delta lines removed, 0 left, 5,137 files kept, 1,607 rewritten); `ledger.db` 318,734,336 bytes after VACUUM (larger than 295,919,616 because the three rollup tables were built; the copy had none); `purge-deltas` 1m33s; all three rollups equal base aggregates in both EXCEPT directions; `integrity_check` ok; a second run was a no-op with identical archive checksums. A posted fixture (58 facts, 6 deltas) twice to a running serve: deltas `accepted`, no fact, no archive line, `message.part.updated` stored. Benchmark on the purged copy (command as in 3-13): 2,063 cases all 200, max p95 483 ms (under 500 ms). `go build`, `go vet`, `go test -count=1 ./...`, `-race` on archive and compact, `gofmt` and the plugin tests (8 of 8) pass.

## Phase 4 — Dashboard shell, filters and drill-down

Units: sixteen, from `refine` (briefs in `briefs/`, named `4-NN-<slug>.md`). Order: 4-01, 4-02, 4-03, 4-04 parallel; then 4-05 (after all four); then 4-06 to 4-15 parallel (each owns one route directory and its spec; run in separate worktrees with distinct `E2E_PORT`); then 4-16 last (after all route units). There is no verification unit: the orchestrator verifies. `artifact_feedback` was not run on these briefs (the workflow MCP server failed to connect, ENOENT).

### Carried items placed

1. Cost 0 for unpriced models, site half: 4-02 (`costLabel`), 4-03 (fixture with priced and unpriced calls), 4-06, 4-08, 4-14 (show `unpriced_calls`, never `$0`). Adding rates to `tools/transcript/pricing.json` stays carried and out of scope.
2. Little latency headroom: 4-01 (cache, in-flight dedupe, concurrency limit), 4-02 (`pickBucket`), 4-06 and 4-08 (totals from `summary`, few queries).
3. Windows rejected with 400, and `scores` needing `kind`: 4-02 (`resolveWindow`, `pickBucket`, `scoresParams`), 4-07, 4-11.
4. `ANALYZE` dependency of `scores`: server-side, the site makes none; stays carried.
7. Live-captured Claude dedupe gap: only the footnote in 4-08; the gap itself stays carried.

### Stays carried

Items 4 (server side), 5, 6, 7 (the gap), 8, 9, 10 and 11 (`row_hash` BLOB). Items 12 and 13 are done.

### 4-01-data-client

Built (d9c5100, 54de8ba, flash worker): `query.ts` client (`createClient`, `normalise`, `Superseded`) with a 250 ms per-slot debounce, abort of superseded calls, session cache, in-flight dedupe and a concurrency limit of 3; `api.ts` takes a `signal`; `state.svelte.ts` gains `notices`; new response types. A corrective commit scoped notices to `partial`/`ignored_filters` and fixed an overstated handoff. Known: a notice for a slot can go stale (route units must clear it). Orchestrator check: `npm test` 76 pass across 11 files, `npm run build` passes.

### 4-02-filter-model-presets

Built (5a2540b, flash worker): pure modules for URL view state, presets, in-range `pickBucket`/`resolveWindow`, `apiParams` (exclude as facet complement), `scoresParams` and `costLabel` (never `$0` for unpriced); 43 owned tests pass. Deviation: the `hour` bucket cap formula (about 16.6 days) is authoritative over the brief's "about 16 days".

### 4-03-fixture-usage-e2e-helpers

Built (b983345, flash worker): fixture gains usage facts (conversation c5, priced and unpriced calls) with exported hand-counted constants; helpers `trackRequests`, `expectSettled`, `clickBar`, `brush`; `E2E_PORT` (default 4391). Suite 26 passed on 4391 and on 4393. Concern: `clickBar` reads the row count from `<testid>-table` and clicks the toggle when it is not mounted; unexercised until route units use it.

### 4-04-echarts-components

Built (8cc8631, flash worker): ECharts bar, time (with brush), heatmap and treemap components, sparkline, data-table toggle and theme tokens following the system preference, with `data-testid`, `data-ready`, `data-theme`. Known: concurrent `vite build` in one tree clobbers `.svelte-kit/output` (ENOENT manifest); run builds one at a time or in separate worktrees.

### 4-05-shell-filterbar-view

Built (d607aa1, flash worker): `+layout.svelte` shell, `FilterBar.svelte` (presets, custom range, chips, exclude shown as complement) and the shared view-state module; the filter selection lives in the URL and survives navigation. Checks by the worker: `npm test` 76 pass, `npm run build` passes, `shell.spec.ts` 6 passed, full e2e 31 of 32. Known: `overview.spec.ts:38` fails because the facet selects now load through the debounced client; 4-06 fixes it. Units 4-06 to 4-15 run in separate git worktrees (`/home/codyh/workspace/wt/<NN>`, branch `wt/<NN>`, `E2E_PORT` 44NN) and are cherry-picked back by the orchestrator.

### 4-06 to 4-15 (route units)

Ten flash workers ran in parallel in separate git worktrees (`E2E_PORT` 4406 to 4415) and were cherry-picked onto the plan branch (conflict-free, owned paths disjoint). Three workers (4-09, 4-11, 4-14) finished their work and report but were denied the commit step (permission auto-rejected on a `/tmp` write); the orchestrator committed their owned paths unchanged. Orchestrator check on the merged branch: `npm test` 76 pass, `npm run build` passes, `npm run test:e2e` 76 passed.

- 4-06-overview (53f0eaf, 7e3034a): Overview on the shared view: KPI tiles with sparklines (cost via `costLabel`, `unpriced_calls` beside it), weekday by hour heatmap; the grouped `summary-*` ids restored; fixes the `overview.spec.ts:38` failure from 4-05.
- 4-07-trends (b4044e9): any measure over time, schema-driven lists, in-range bucket, brush narrows the window and clears the preset. Departure: `all=1` with a time bucket is not issued (the API benchmark skips it).
- 4-08-usage-cost (d7b1cbf): new `usage/` route, seven `/query` requests, per-model calls, tokens and cost, unpriced banner, `__other__` inert; a window with only unpriced calls never shows `$0`. Footnote on the live-captured Claude dedupe gap.
- 4-09-repos (a68cdda, committed by the orchestrator): four fixed `/query` requests (`top=100`), independent of repo count; the page waits for facets so a facets arrival does not re-send the queries.
- 4-10-hooks (7aa826f): four bars and two linked two-level treemaps (`/query` allows two dimensions); drill-down adds chips. Bar order is key-ascending.
- 4-11-quality (26cc678, committed by the orchestrator): `scores` always carries one `kind` via `scoresParams`; kind selector in the URL. Contradiction: the brief says table only; DESIGN.md says "distribution charts beside the baseline". Followed the brief; see Carried.
- 4-12-executions (036591a): shared client, drill-down cells. Deviation: `ev.shiftKey` mapped to `{shift}`.
- 4-13-conversations (4f9a29e): virtualised rows (`VirtualRows.svelte`), ids open the timeline, 1 s timing assertion on a 5,000-row case. Known: a non-`Superseded` fetch error renders nothing (no error panel).
- 4-14-conversation-timeline (406ded2, committed by the orchestrator): `/conversation?id=` with header, token and cost totals (`unpriced_calls` shown, no `$0`), event list.
- 4-15-explore-settings (9f3efb3): Explore follows the shared window and filters (exclude as complement); Settings clears the client cache on save.

Contradiction for 4-16, found by 4-10: `helpers.clickBar` cannot click a `BarChart` (it leaves the table showing, which unmounts the chart). Amended into `briefs/4-16-retire-layerchart-interactions.md` (4-16 now owns `helpers.ts`).

### 4-16-retire-layerchart-interactions

Built (a11e80d, flash worker): `layerchart` removed from `package.json` and the lockfile; `Bars.svelte`, `LineSeries.svelte`, `palette.ts`, `filters.ts` and `series.ts` (with their tests) deleted once nothing imported them; `clickBar` fixed in `helpers.ts`; new `interactions.spec.ts` covers the cross-route bullets (7d persists from Overview to Hooks, brush narrows the window, harness bar include and shift-exclude chips, conversation timeline totals, cost by model, themes and table toggles). Departure: `usage.spec.ts` `SONNET_BAR` changed 1 to 0 because the old index had been calibrated to the broken helper. Known (not fixed): notices self-clear in 4-05; `query.ts` can drop a shared in-flight entry for same-key joiners; `costLabel` can emit `$0.00` when `unpriced < calls` (not reachable in the fixture).

### 4-17-fix-verification-defects

Built (18f36b3, flash worker), from verification 1 on a copy of the purged real ledger: All time on non-`/query` routes is clamped to 399 days (was a 400), the usage data table formats cost and unpriced instead of raw values, and the client default `maxConcurrent` went 3 to 6. Verification 2 showed the first two held; latency and the timeline `$0.00` did not.

### 4-18-fix-timeline-cost-and-request-storm

Built (7aecc95, flash worker): timeline rows of a usage event with `cost_usd` null or 0 read "unpriced" (the API sends 0 for unpriced models). `view.svelte.ts` keys facets to their window and exposes `facetsReady`, which Overview and Usage gate on; Usage reads `paramsFor` untracked. `maxConcurrent` is 4. Fixture e2e, 30d to 90d: Usage 10 requests (7 distinct) to 7/7, Overview with an exclude 12/10 to 10/10. Contradiction reported: plain Overview did not storm in the fixture; the storm needs an exclude, so the Overview regression spec uses one. Tests: npm test 74, e2e 90, build clean.

### Phase 4 verification

Run by a Sonnet subagent with Playwright Chromium against a fresh copy of the purged real-ledger copy (`purge-deltas` run on it), served on a scratch port. The live ledger was not touched. Results:

- Pass: eight presets across ten routes (80 page loads) with no 4xx and no console errors, All time clamped with a notice on non-`/query` routes; include and shift-exclude chips; reload, back and cross-route URL state; brush narrows the window; harness bar drill-down; conversation timeline totals.
- Pass: timeline rows of unpriced models read "unpriced" in four conversations (including one with 2,322 unpriced rows); none shows `$0.00`; header totals agree with the API.
- Pass: each interaction issues no duplicate or aborted requests (Overview 12, Usage 7 to 8 requests, all distinct).
- Fail, latency: the 1 s target is missed on the large copy. Settled time (3 runs): Overview 30d to 90d 1.16 s, Usage 30d to 90d 1.20 s, Overview to Usage 1.21 s, Usage to Overview 1.13 s, All time 1.31 s (Overview) and 1.36 s (Usage); filter add 0.99 to 1.00 s (Overview) and 1.04 to 1.06 s (Usage). That is the 250 ms debounce plus the slowest API call of 0.45 to 0.62 s, which is itself at or past the 500 ms API budget. The site no longer adds load; the remaining overrun is the API (see Carried 1).
- Fail, Usage table: merging five top-20 lists by key leaves rows with `calls 0` beside tokens or cost; `__other__` shows `215 calls, 107 unpriced, $0.00`; the empty model key renders as a blank label.
- Not applicable: saved views are Phase 5 per DESIGN.md.
- Measured at the fixture level, the 1 s assertion in the e2e suite holds; it does not on the large copy.

artifact_feedback: the service answered `not delivered` ("no version of this file") for every report checked, so none were scored; briefs 4-01 to 4-05 and others were checked earlier and returned scores, with some metrics below the p25 baseline. Briefs 4-17 and 4-18 and reports 4-17 and 4-18 were not delivered. The workflow MCP server itself does not start in this session (ENOENT); the plugin's feedback tool did answer.

### Carried (Phase 4)

1. Interaction latency over 1 s on the large ledger: preset change, navigation and All time settle in 1.1 to 1.4 s, filter add at about 1 s. The cause is the API, whose slowest call is 0.45 to 0.62 s (Phase 3 item 2, no headroom) on top of the 250 ms debounce. Next: cut the slowest `summary` and `query` cases in the API, or drop the debounce to 100 ms for preset clicks (only typing needs it), or show cached results first.
2. Usage table merges five separate top-20 lists by key, giving `calls 0` rows, an `__other__` row with `$0.00` and 107 unpriced calls, a blank label for the empty model key, and a "unpriced of calls" banner that sums mismatched rows. Fix: one `/query` over the page's measures for the table, `__other__` worded "other models" and shown unpriced, empty key as "(none)".
3. The conversation page's back link is hard-coded to `/conversations` and drops the range and filters.
4. Timeline rows with 0 tokens in and out and cost 0 read "unpriced"; they should be blank or "free".
5. Quality is table-only; DESIGN.md says "distribution charts beside the baseline" (4-11 followed its brief).
6. Executions has no sankey (Phase 5).
7. Conversations swallows non-`Superseded` fetch errors and renders nothing.
8. Client bugs: notices self-clear (4-05); `query.ts` can drop a shared in-flight entry for same-key joiners; `costLabel` can emit `$0.00` when `unpriced < calls`.
9. Usage cost-over-time legend overlaps the x-axis labels; the Hooks clickable bar covers only the bar.
10. Saved views (Phase 5).
11. Pricing rates (Phase 3 item 1): the site now shows unpriced explicitly, but 74% of calls are unpriced until rates for Claude and Codex are added to `tools/transcript/pricing.json` and `internal/store/pricing_table.json`.
12. Phase 3 items 4 to 9 still open as written above; item 10 is superseded by the artifact_feedback note in the verification; item 11 (`row_hash` BLOB) stays carried. Items 12 and 13 are done.


## Phase 5 — Chart builder and dashboards (refined)

Verdict: Proceed. 17 units; briefs in `briefs/5-01-*.md` to `5-17-*.md`; the Units list is in `DESIGN.md` under Phase 5.

### Carried items placed

- Latency over 1 s (Carried 4.1): 5-11 (debounce 100 ms, leading edge after idle), 5-12 (profile the page request sets), 5-13 (speed up the three slowest requests). The orchestrator re-times on `/var/tmp/p4verify/data/local`.
- Usage table merge (4.2): 5-10.
- Back link loses range and filters (4.3): 5-14. Zero-token rows reading "unpriced" (4.4) and `costLabel` `$0.00` (4.8): 5-14.
- Quality distribution charts (4.5): 5-03 (box chart) and 5-15.
- Executions sankey (4.6): 5-03 and 5-09.
- Conversations swallowed errors (4.7): 5-16.
- Client bugs (4.8): notices self-clear in 5-06; `query.ts` shared in-flight entry in 5-11.
- Usage legend overlap and Hooks bar hit area (4.9): 5-04.
- Saved views (4.10): 5-01, 5-06, 5-08; the builder is 5-02, 5-05, 5-07; proof is 5-17.

### Stays carried

- Pricing rates (4.11; Phase 3 item 1): data, not site code.
- Phase 3 items 4 to 9 (server-side), item 11 (`row_hash` BLOB); item 2 (benchmark headroom) is only partly addressed by 5-13.
- Ledger compact CLI, keyless deltas, and the `artifact_feedback` / workflow MCP infrastructure (the MCP server fails to start with ENOENT in this session).

### Notes for the orchestrator

- `artifact_feedback` results for the Phase 5 briefs are recorded below once obtained.
- Worktrees are required for parallel e2e units (distinct `E2E_PORT`).
- artifact_feedback on the Phase 5 briefs (checked 5-01 and 5-07): `not delivered`, the service has no version until pushed; unscored.

### 5-01-saved-view-store

Built (892130a, flash worker, worktree wt/5-01): `src/lib/views.ts` saved-view and dashboard store in `localStorage` under `workflow-analytics-views`, export and import JSON with `ImportError` cases, in-memory fallback, `subscribe`; 20 tests, `npm test` 94 pass, build passes. Deviations: none.

### 5-02-builder-spec

Built (90ea220, flash worker, worktree wt/5-02): `src/lib/builder.ts` config model (`parseConfig`, `configToParams`, `allowedDims`, `allowedBuckets`, `allowedCharts`, `defaultConfig`, `isRangeOk`), schema-driven and non-throwing; 23 tests, `npm test` 97 pass. Deviations: none. Concern: no standalone typecheck was run.

### 5-03-sankey-boxplot-charts

Built (e960563, eccd6ce, flash worker): sankey and box-plot ECharts components, `EChart.svelte` registration (also `ScatterChart` for box markers: brief named only Sankey and Boxplot, named in the report); `npm test` 83 pass, build passes, no `layerchart`. Not browser-rendered by the worker.

### 5-10-usage-table-merge

Built (bf9cb04, flash worker): the Usage table reads five `/query` requests with `top=100` so every measure returns one key set; `__other__` reads "other models", the empty key "(none)" and is inert. Contradictions reported: the cost-by-model chart shares the table's responses so it sees up to 100 keys (brief said top=20); the backend accepts an empty `model` filter; the 3-model fixture cannot reproduce the merge defect, so the `top=100` assertion is the guard. Real-copy check is left to phase verification.

### 5-14-conversation-page-fixes

Built (f63136e, flash worker): back link restores the last list route with its query (mirrored in `sessionStorage`); zero-token and zero-cost rows show no cost text, `unpriced` only for rows with tokens and no positive cost; `costLabel` returns `N unpriced` instead of `$0.00` when priced cost is 0. Tests 89 pass, conversation e2e 11 pass.

### 5-16-conversations-fetch-errors

Built (ccf2481, flash worker): Conversations shows the shell `error-panel` on a non-`Superseded` fetch failure and clears it on success; three e2e tests (500, network abort, preset retry).

### 5-05-builder-chart-components

Built (4e1a264, flash worker): `BuilderChart`, grouped bar and small-multiples components; 7 tests, build passes. Deviations: `area` renders stacked bars (no area type in `timeOption`, `options.ts:94`, owned by 5-04); heatmap y-axis uses the time bucket for the single-dimension case. Carried into the phase: area chart type.

### 5-12-page-request-set-profile

First run (flash) found no `go` on PATH and stopped without a change; relaunched with `~/.local/go/bin` on PATH.
Built (7bd46ed, flash worker, second run): gated `internal/serve/analytics_pageset_test.go` profiles the Overview and Usage request sets on `/var/tmp/p4verify/data/local` (72 requests, 0 non-200). Slowest p50/max ms: usage `bucket=week&measure=tokens_out` 613/678, overview `bucket=week&measure=cost_usd` 596/620, usage `bucket=none&dim=model&measure=unpriced_calls` 590/623, all in the base-row usage CTE scan (`SCAN facts` plus temp b-tree). Contradiction: both pages clamp All time to 399 days on `/query` too, contrary to the brief. Feeds 5-13.

### 5-04-chart-legend-and-bar-hit-area

Built (075cce9, 5b51b0e, flash worker): chart legend reserves space above the grid (no axis overlap); Hooks bar rows clickable across the grid. Not met: the y-axis label gutter stays non-clickable (overlay covers the grid only).

### 5-06-shell-saved-views-embed-notices

Built (88cdd37, flash worker): `SaveView.svelte`, Builder and Dashboards nav, `embed=1` mode rendering children only, notices keyed to `pathname+search` with `pruneNotices` (notices no longer self-clear; `query.ts` untouched). `shell.spec.ts` 10 pass, `npm test` 117 pass.

### 5-15-quality-distribution-charts

Built (a62d133, flash worker): `BoxChart` of per-check score distribution above the Quality table with the baseline median as marker; three e2e tests (rows and marker, kind switch, dark theme). Contradiction: the e2e serve has no scorer, so tests stub scored rows.

### 5-07-builder-route

Built (a11314c, flash worker): `/builder` route, schema-driven controls, URL as view state via `parseConfig`, one `/query`, unsupported pairings not selectable, bucket clamp with `builder-notice-range`, drill and brush; five e2e cases (5 failed before, 5 passed after), `npm test` 148 pass. Deviations: explicit `b=none` handling; chart re-defaults on a pairing change. Defect found: `SmallMultiples` emits no `data-ready` (placed in 5-18).

### 5-08-dashboards-route

Built (f2c7d78, flash worker): `/dashboards` route: list and create, ordered grid of saved-view iframes with `embed=1`, reorder and remove, JSON export (Blob) and import (file or textarea) with `dash-import-error`; two e2e tests, `npm test` 152 pass.

### 5-09-executions-sankey

Built (b22233b, df88f60, flash worker): Executions sankey with links `exec-link-<source>-<target>`; clicking a link sets the page-local `shape` parameter and filters the table client side (second click clears; counts tiles unfiltered). Deviation as briefed: no per-row design reference, so `design -> brief` is the whole set; fetch-key guard replaces `params`-identity refetch. 9 e2e pass, `npm test` 148 pass.

### 5-18-stacked-area-and-multiples-ready

Added by the orchestrator after 5-05 and 5-07 reported the area type and the small-multiples settle defects (`briefs/5-18-stacked-area-and-multiples-ready.md`); 5-17 now also depends on it.

### 5-11-client-latency-and-inflight

Built (e7d25c9, flash worker): `query.ts` debounce 100 ms (was 250) with `idleMs` 250 leading edge for a slot that has been idle; a released fetch no longer poisons the cache or duplicates a request (`dead` flag). 13 tests pass, e2e overview and usage 20 pass, fixture preset-click p50 46 to 34 ms. Contradictions: the brief's "never made" leading edge clashes with "a burst issues only the last request", so cold slots still debounce; the brief's joiner symptom did not reproduce, the real defect was a released fetch poisoning the cache. Large-ledger timing is re-measured at verification.

### 5-18 outcome and 5-19-area-wiring

5-18 built (01403f3, flash worker): `timeOption` gains an `area` option (line series with `areaStyle`, stacked) and `SmallMultiples` emits `data-ready` after its children mount; 156 tests pass, build clean. It found that `TimeChart` has no `area` prop and `BuilderChart` passes `stacked` for `area`, so the area chart stayed unreachable; and the multiples settle is not browser-validated. Placed in a new unit 5-19 (`briefs/5-19-area-wiring.md`, 5-17 depends on it).

### 5-19-area-wiring

Built (b9a9dac, flash worker): `TimeChart` takes `area`; `BuilderChart` passes `area` for the area chart; `tests/e2e/area.spec.ts` asserts the SVG render (filled path plus stroked line) since `EChart` keeps its instance private. It found a 5-18 regression: `bind:ready={panelReady[panel.key]}` throws `props_invalid_value` in the browser, so no small multiples render and the multiples `expectSettled` assertion fails. Placed in a new unit 5-20 (`briefs/5-20-fix-multiples-bind-ready.md`); 5-17 depends on it. Known: the area e2e assertion on multiples is red until 5-20 lands.

### 5-20-fix-multiples-bind-ready

Built (5dcdba2, flash worker): `SmallMultiples` readiness no longer crashes in the browser; builder and area e2e 7 pass (2 failed before), `npm test` 161 pass, build clean. Deviation: no client-mount unit test is possible (node-only vitest, no jsdom), so an SSR two-panel test plus the e2e cover it.

### 5-13-api-slowest-cases

Flash worker ran out without committing; one Sonnet retry landed it (75b8922). New index `facts_usage_ts ON facts(type, norm_event, ts)` with a single-index `ANALYZE` at creation (without the stats row the planner chose it for `artifact_version` queries and `scores/7d` went from 33 ms to 5 s), and the usage CTE narrowed from `SELECT *` to the 11 columns read. The three slowest All time requests moved to 0.48, 0.51 and 0.48 of their p50 (usage tokens_out week 571 to 277 ms, overview summary 548 to 282 ms, overview cost_usd week 543 to 259 ms). go vet and store and serve tests pass; `TestAnalyticsBench` passed, none over 500 ms p95 (worst `series/90d` 465.5 ms). Deviations: `reads_test.go` (outside owned paths) drops the new index before dropping `norm_event`; the report's one-time-cost section ends in a half-sentence about index size. Known: first open of an existing ledger builds the index (about 0.7 s on the 435k-row copy); the usage read still sorts 33k rows and runs `json_extract` over `raw` (about 250 ms), a usage rollup would remove that. `internal/secrets` `TestEnvAssignmentCorpus` fails with or without this change (false positives in a report file).

### 5-17-phase-5-e2e

Built (flash worker): `tests/e2e/phase5.spec.ts`, seven tests: small multiples cost_usd x model x harness at day bucket (panels derived from a live API query), heatmap hour_of_day x weekday (cells sum to the API total), no unsupported pairing across every schema measure at 0, 1 and 2 dims, save to dashboard surviving reload, export then import into a fresh browser context, sankey link filter, and five input-to-settle timings (25 to 152 ms on the fixture, all under 1 s, three runs). Full e2e 125 pass, `npm test` 161 pass, build clean. Deviations: the dashboard timing measures click to tile visible because `/dashboards` has no `data-ready`; settle waits hardened against the stale chart; the sankey test overlaps `executions.spec.ts`. Large-ledger timing is not covered here and is re-measured at verification.
