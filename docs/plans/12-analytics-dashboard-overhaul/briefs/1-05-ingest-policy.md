# Brief: 1-05 — Ingest policy, collapse, slim facts and archive wiring

Consumer: a Go worker (Opus-tier recommended: several interacting invariants, hash identity and ordering) wiring the policy into `Ingest`.
Owned paths: `tools/workflow/internal/ingest/ingest.go`, `tools/workflow/internal/ingest/ingest_test.go`, `tools/workflow/internal/ingest/policy.go` (new), `tools/workflow/internal/ingest/policy_test.go` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-05-ingest-policy.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 1-01 (archive), 1-02 (store columns), 1-03 (marked remove list in index.ts), 1-04 (Derive and fixture).
Runs alongside: nothing.
Budget: 8 files to read, about 350 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Capture and event policy" (policy table, remove, collapse, keep), "Domain: Event archive" (delivery), "Ledger shape" bullet "Stored hook facts". Binding.
2. `tools/workflow/internal/ingest/ingest.go` — whole file (244 lines); `Ingest` at line 166 is what you change.
3. Reports of 1-01, 1-02, 1-04 under `docs/plans/12-analytics-dashboard-overhaul/reports/`, then the code they added: `internal/archive/` (`Append`, `Entry`, `Line`), `store.FactRow` new fields and `Tenant.Dir()`, `Derive` and `Derived`.
4. `tools/hooklog/tests/fixtures/ingest_policy.json` — the shared fixture and its `expect` block.
5. `packages/opencode-workflow-hooks/src/index.ts` — the `remove-list:begin/end` block only.
6. `tools/workflow/internal/keys/keys.go` lines 22-61 — `Canonical`, `RowHash`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A posted batch obeys the event policy: removed events leave nothing, deltas collapse to one fact per part, every kept or collapsed body is archived verbatim, and the stored fact is a slim envelope with the extracted columns.

## Contract

Cited from DESIGN.md "Domain: Capture and event policy" (settled, do not re-derive):
- "One table in `internal/ingest` maps `(harness, event)` to `keep`, `collapse` or `remove`. Any pair not listed is `keep`. The OpenCode plugin carries the same `remove` list, and a test asserts the two lists are equal."
- `remove`: OpenCode `experimental.chat.system.transform`, `chat.params`, `chat.headers`, `shell.env`. "Ingest answers them `accepted` and stores nothing: no fact row and no archive line."
- `collapse`: OpenCode `message.part.delta` when `payload.event.properties` carries non-empty `messageID`, `partID` and `field`. "The stored fact's row hash is computed from `(type, harness, event, conversation_id, messageID, partID, field)` instead of the whole envelope ... a redelivered delta is a `duplicate`. Its `ts` is the first-received delta's. Every delta is still archived. A delta lacking the key fields is `keep`."
- `keep`: "Row-hash identity is unchanged: it is computed from the full received envelope, as today."
- From "Event archive": "Ingest appends to the archive before it commits the fact rows"; "For collapsed deltas each line carries the delta's own envelope hash, not the part hash"; the archive holds "every received `keep` and `collapse` hook event, verbatim and after secret redaction", no `remove` event, no artifact content.
- From "Ledger shape": "A hook-event fact's stored `raw` is its envelope ... with no `payload`. `artifact_version` and `commit` facts keep their full `raw`."

Settled by this brief:
- The policy lives in `policy.go`: a table keyed by `(harness, event)` returning `Keep|Collapse|Remove`, plus `func Policy(harness, event string, payload map[string]any) Action` (payload needed for the collapse-key check). Only `type: "hook_event"` facts are subject to policy.
- Order per fact: validate, then policy. A `remove` fact returns `Accepted` immediately, before `Precheck`, so it creates no rejection row and no archive line. Other facts continue: precheck (a rejected fact is not archived), hash, archive entry, row.
- Collapse hash: `keys.ContentHash` over the canonical JSON array `[type, harness, event, conversation_id, messageID, partID, field]`. Put it in `policy.go` (do not edit `keys`). Collapse key fields come from `payload.event.properties` and must be strings.
- Stored `raw` for a hook fact is the canonical form of the received object with only the top-level `payload` key removed (all other top-level keys, e.g. `backfill`, stay; `id` is stripped as today). Archive `fact` is the full canonical received fact, payload included. Archive `RowHash` is `keys.RowHash(raw)` of the received fact for both keep and collapse; the stored row hash is the part hash only for collapse.
- Archive entries for one `Ingest` call are written with a single `archive.Append` before the single `tenant.Append`; an archive error is a whole-request error (as `WritePending` errors are). `ReceivedAt` is `time.Now().UnixNano()`. Entry `TS` is the fact's `ts` (0 if absent).
- `FactRow` fields come from `Derive(harness, event, payload)` for hook events; `Source` from `source` and `SHA` from `sha` for artifact_version and commit facts. Hook facts get empty Source/SHA.
- The remove-list equality test (`policy_test.go`): read `packages/opencode-workflow-hooks/src/index.ts` (path relative to the test file), extract the quoted strings between `// remove-list:begin` and `// remove-list:end`, assert the set equals the Go table's OpenCode `Remove` entries.
- Route name: the design says `POST /v1/facts`; the real route is `POST /v1/ingest`. Do not rename anything; report it.
- Not in this unit: the tenant lock, compaction, health fields, any analytics read change.

### Keep untouched

Existing `Ingest` behaviour for `artifact_version`/`commit` (full raw, pending write, content hash), results order and IDs, rejection recording, and `Precheck`. The existing tests in `ingest_test.go` must keep passing; edit one only where a hook fact's stored `raw` is asserted to hold a payload, and say which.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/ingest/ ./internal/store/ ./internal/archive/` → pass, including new tests driven by the fixture `ingest_policy.json`: (a) every `remove` fact returns `accepted`, `SELECT count(*)` for its conversation is 0 and no archive line contains its marker string; (b) the 3-delta part leaves exactly 1 fact whose `ts` is the first delta's, the 2-delta part exactly 1, the keyless delta 1 more (keep); (c) resending the whole batch returns `duplicate` for every non-remove fact and `accepted` for remove; (d) `archive.Read` for each conversation returns a line per received non-remove fact (all 5 deltas present, own hashes distinct), each `fact` byte-equal to the canonical received fact; after the resend, `Read` still returns each once (dedupe) while the raw files hold the repeated lines; (e) `SELECT count(*) FROM facts WHERE type='hook_event' AND instr(raw,'"payload"')>0` is 0; (f) `norm_event`, `model`, token columns and `cost_reported` equal the fixture `expect` and per-harness sums equal `expect_totals`; (g) a hook body containing a secret is still `rejected` and not archived; (h) the equality test passes, and fails if you temporarily drop an entry from the Go table (show once, then restore).
- `go test ./...` from `tools/workflow` → no new failures versus baseline. If analytics tests fail because they read `payload.tool_name` from `raw` of ingested hook facts, report which; Phase 3 rewrites those reads, so adjust only the test input path (insert via `store.Append` with the `Tool` field) and say so.
- `git diff --stat` shows only owned paths.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
