# Report: 1-05 Ingest policy, collapse, slim facts and archive wiring

Status: done with concerns (the concerns are a fixture status mismatch for 1-06 and an archive escaping limit; details below)

## What changed
- New `tools/workflow/internal/ingest/policy.go`:
  - `Action` (`Keep|Collapse|Remove`) and the `policyTable` keyed by `(harness, event)`. The four OpenCode remove events map to `Remove`; OpenCode `message.part.delta` maps to `Collapse`.
  - `Policy(harness, event, payload)`. A delta whose `payload.event.properties` lacks a non-empty string `messageID`, `partID` or `field` is `Keep`.
  - `CollapseHash`: `keys.ContentHash` over the canonical array `[type, harness, event, conversation_id, messageID, partID, field]`.
- `tools/workflow/internal/ingest/ingest.go`, per fact:
  1. validate;
  2. for `hook_event` only, policy. A `Remove` fact returns `accepted` before Precheck, so it leaves no rejection, no archive line and no row;
  3. precheck;
  4. hash and canonicalise;
  5. WritePending;
  6. for hook facts: stored `raw` = canonical envelope without top-level `payload` (via new `envelope()`); row hash = the collapse hash for `Collapse`; the `Derive` columns are filled; one `archive.Entry` is added (own `keys.RowHash` of the received fact, `fact` = full canonical received fact, `TS` = fact ts, a single `ReceivedAt = time.Now().UnixNano()` per call);
  7. for artifact_version/commit facts: `Source`/`SHA` come from `source`/`sha` and `raw` stays full.

  Then one `archive.Append(tenant.Dir(), entries)` runs before the one `tenant.Append`. An archive error fails the whole request. The package doc comment is updated.
- New `policy_test.go`:
  - `TestRemoveListMatchesPlugin` (h);
  - `TestPolicyCollapseNeedsKey`;
  - `TestIngestPolicyFixture`, driven by `ingest_policy.json` (a–f);
  - `TestIngestSecretHookNotArchived` (g).
- Amendment from 1-02:
  - `internal/store/analytics.go` Facets: renamed the alias `tool` to `tname`.
  - `internal/serve/reads_test.go` backfill: the test now steps the db back to a real version 1. It drops `search`, the indexes from migrations 3 and 4, and the 13 migration-4 columns before it sets `user_version = 1`.
- `ingest_test.go` is unchanged. No existing ingest test asserted a payload in a hook fact's stored `raw`.

## Check output
- Before, with `ingest.go` at HEAD and the new tests in place:
  - `go test ./internal/ingest/` gives `FAIL TestIngestPolicyFixture: first send 42: {ID:fx-opencode-43 Status:accepted} want duplicate`. The old code stores every delta.
  - Baseline `go test ./...` also failed `store TestAnalyticsFacets`, `serve TestAnalyticsOutcome/{summary,facets}` and `serve TestAdvisoryReads/backfill`. These are the 1-02 breakages.
- After:
  - `go test ./internal/ingest/ ./internal/store/ ./internal/archive/` passes. `go test -race ./internal/ingest/` passes.
  - `go test ./...` passes in every package. `go test -count=3 ./internal/serve/` passes.
  - Under `-race` only, `store TestMigrationFast100k` reports "migration too slow". That is race-detector overhead on 1-02's timing test, not this change; it passes without `-race`.
- (h) After removing the `shell.env` entry from the Go table, the test fails with `plugin [chat.headers chat.params experimental.chat.system.transform shell.env] / go [chat.headers chat.params experimental.chat.system.transform]`. With the entry restored, it passes.
- Coverage:
  - (a) For each remove event, `SELECT count(*) FROM facts WHERE harness='opencode' AND event=?` returns 0, and no raw archive line contains `FAKE-NOT-A-SECRET`.
  - (b) Parts of 3 and 2 deltas each leave 1 row, and its `ts` is the first delta's. The keyless delta is 1 more row, so there are 3 delta rows in total.
  - (c) On resend, every non-remove fact is `duplicate`, remove facts are `accepted`, and the fact count is unchanged.
  - (d) `archive.Read` returns one line per non-remove fact. All 5 deltas have distinct own hashes, and each `fact` is byte-equal to `keys.Canonical(received)`. After the resend, `Read` still returns each line once, while the raw zstd files hold 2× the lines.
  - (e) The `instr(raw,'"payload"')` count is 0.
  - (f) Every column equals `expect`, and the per-harness sums equal `expect_totals`. Claude is deduped by `payload.message_id`; collapsed parts count once.
- `git diff --stat`: `ingest.go`, `policy.go`, `policy_test.go`, plus the three amendment files `store/analytics.go`, `serve/analytics_test.go` and `serve/reads_test.go`.

## Departures
1. **Test (a) query.** The brief asks for `SELECT count(*)` "for its conversation". In the fixture, the remove events share `fx-conv-opencode` with kept events, so that count could never be 0. The test counts by `(harness, event)` instead.
2. **`serve/analytics_test.go` is edited.** This is the case the brief anticipated. After the change, `TestAnalyticsOutcome/{facets,series,explore}` failed: those analytics read `payload.tool_name` from `raw`, and ingested hook facts no longer carry a payload. Only the input path changed: the 4 tool-bearing hook facts are now inserted with `store.Append`, with a payload-bearing raw (the uncompacted-ledger shape) and `Tool` set. The secret-bearing fact still goes through `/v1/ingest`. Phase 3 must move these reads to the `tool` column. Until then, analytics show no tools for newly ingested hook facts.
3. **First-send statuses differ from the fixture.** The fixture's `first_status` is `accepted` for all 5 collapse deltas. Actually, a later delta of a part already stored (here, earlier in the same batch: `fx-opencode-43`, `-44`, `-46`) hits `INSERT OR IGNORE` on the part row and returns `duplicate`. I kept the store semantics, which the design's "INSERT OR IGNORE keeps exactly one row per part" implies, and my test asserts them. Telling a new delta apart from a redelivered one would need an archive lookup. **Unit 1-06 must either assert `duplicate` for those three or decide on a different rule.** The fixture's `first_status` for those IDs is wrong as written. I did not edit the fixture because it is not an owned path.

## Contradictions and notes
- Route: the design says `POST /v1/facts`; the real route is `POST /v1/ingest`. Nothing was renamed.
- **The archive is not byte-verbatim for `<`, `>` and `&`.** `archive.Append` uses `json.Marshal(Line)`. That HTML-escapes the contents of `RawMessage`, so a fact containing those characters is archived as `<` and similar. The fix belongs in `internal/archive/archive.go` (1-01): encode with `json.NewEncoder` and `SetEscapeHTML(false)`. The fixture contains none of these characters, so (d) passes. I did not fix it here.
- A hook fact that `keys.Canonical` accepts but `envelope()` cannot encode is rejected as `cannot canonicalise fact`. This cannot happen in practice.

## Unfinished
- 1-06: correct the fixture's `first_status` for `fx-opencode-43`, `-44` and `-46` (see Departure 3).
- 1-01 follow-up: the escaping fix above.
- Phase 3: move the analytics tool reads (`toolExpr`, `Explore`'s `AS tool` subquery alias, which 1-02 flagged) to the `tool` column.
