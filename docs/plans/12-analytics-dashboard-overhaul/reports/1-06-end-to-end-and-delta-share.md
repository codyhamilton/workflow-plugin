---
# Report: 1-06 End-to-end Phase 1 proof and delta-key share

Status: done

## What changed
- New `tools/workflow/internal/serve/ingest_policy_test.go`: `TestIngestPolicy` posts the shared fixture batch (`{"facts":[...]}`) to the in-process `POST /v1/ingest` handler for tenant `a`, then proves Phase 1's outcome through the files and SQL a user would inspect. Six subtests map to the outcome bullets:
  - `removed_events_accepted_no_fact_no_archive` — the 4 remove facts return `accepted`, leave 0 rows for their `(harness,event)`, are absent from `archive.Read`, and no archived fact contains `FAKE-NOT-A-SECRET`.
  - `deltas_of_one_part_leave_one_fact` — 5 deltas over 2 parts: exactly 1 row per collapse hash and exactly 1 `accepted` per part.
  - `kept_and_collapsed_events_have_verbatim_archive_line` — every non-remove fact has an `archive.Read` line whose `fact` byte-equals `keys.Canonical(raw)`; 54 lines.
  - `no_stored_hook_fact_raw_contains_payload` — `SELECT count(*) ... WHERE instr(raw,'"payload"') > 0` is 0.
  - `columns_match_fixture_expected` — `norm_event`, `tool`, `model`, the token columns and `cost_reported` equal the fixture for all 51 surviving rows (by `ts`).
  - `resend_returns_all_duplicate` — an identical resend returns `accepted` for remove and `duplicate` for every other fact, with the fact count unchanged.
- Amendment 1: `tools/hooklog/tests/fixtures/ingest_policy.json` — `first_status` corrected to `duplicate` for `fx-opencode-43`, `-44`, `-46` (later deltas of an already-stored part; the first delta of each part inserts the row).
- Amendment 2: `tools/workflow/internal/archive/archive.go` — `Append` now encodes each line with `json.NewEncoder` and `SetEscapeHTML(false)`, so `<`, `>` and `&` are archived verbatim; `TestAppendVerbatimHTMLChars` in `archive_test.go` round-trips such a body through `Append`/`Read` and checks the decoded zstd frame contains no `\u003c`/`\u003e`/`\u0026`.

## Check output
Before:
- The new `IngestPolicy` test did not exist. With the unamended fixture its status assertion fails for the later collapse deltas; 1-05's report captured the symptom verbatim: `first send 42: {ID:fx-opencode-43 Status:accepted} want duplicate`.
- Without the escaping fix, the archive round-trip leaves `\u003c`/`\u003e`/`\u0026` in the decoded line (1-05 report: "The archive is not byte-verbatim for `<`, `>` and `&`").
I did not re-run the pre-amendment tree; the before evidence is the 1-05 report's captured failure and its documented escaping limit (departure named below).

After:
- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve/ -run IngestPolicy -v`:
```
--- PASS: TestIngestPolicy (0.03s)
    --- PASS: TestIngestPolicy/removed_events_accepted_no_fact_no_archive (0.00s)
    --- PASS: TestIngestPolicy/deltas_of_one_part_leave_one_fact (0.00s)
    --- PASS: TestIngestPolicy/kept_and_collapsed_events_have_verbatim_archive_line (0.00s)
    --- PASS: TestIngestPolicy/no_stored_hook_fact_raw_contains_payload (0.00s)
    --- PASS: TestIngestPolicy/columns_match_fixture_expected (0.00s)
    --- PASS: TestIngestPolicy/resend_returns_all_duplicate (0.01s)
PASS
ok  	.../internal/serve
```
- `go test ./...` from `tools/workflow`: every package `ok` (`archive 0.127s`, `serve 2.844s`, `cmd/workflow 52.983s`); `go vet ./internal/serve/ ./internal/archive/` clean.
- `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs`: `# tests 7 / # pass 7 / # fail 0`.

## Open Question 2 — delta-key share
Read-only on the local ledger (sqlite 3.46.1):
```
sqlite3 -readonly "file:$HOME/.local/share/workflow/serve/local/ledger.db?mode=ro" \
 "select count(*), sum(coalesce(json_extract(raw,'$.payload.event.properties.messageID'),'')='' or coalesce(json_extract(raw,'$.payload.event.properties.partID'),'')='' or coalesce(json_extract(raw,'$.payload.event.properties.field'),'')='') from facts where event='message.part.delta'"
-> 8327466|0
```
8,327,466 deltas, 0 lacking `messageID`/`partID`/`field` — share 0.00%, below the 1% threshold. Verdict: collapse needs no fallback key before Phase 2 for the local ledger; Phase 2 may proceed.

## Departures
- Scope: the brief header says "Owned paths: ... Touch nothing else", but its Amendments section requires editing the shared fixture and `internal/archive/archive.go`/`archive_test.go`. I treated the amendments as authoritative and changed those three plus the new test — the same five paths this commit stages. Named here rather than resolved silently.
- The "before" output is cited from 1-05's report and the documented escaping limit, not freshly reproduced on the pre-amendment tree.
- Test (a) counts removed facts by `(harness,event)` (as 1-05 did), because the remove events share `fx-conv-opencode` with kept events.

## Contradictions
- Brief vs design route: the design writes `POST /v1/facts`; the real route is `POST /v1/ingest`. The brief already settles this ("do not change code"); no change made.
- "Six outcome bullets": the six subtests cover remove, delta collapse, resend, archive verbatim, no-payload and column values. Open Question 2 is not testable in-process — it is a property of the legacy local ledger — so it is reported above instead of as a subtest.

## Unfinished
- Phase 3 (already recorded by 1-05): move analytics tool reads from `raw` to the `tool` column. The delta-key share is 0%, so no Phase 1 fallback key is required.
---
