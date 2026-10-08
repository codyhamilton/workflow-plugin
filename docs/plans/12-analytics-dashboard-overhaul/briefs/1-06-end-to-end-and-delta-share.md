# Brief: 1-06 — End-to-end Phase 1 proof and delta-key share

Consumer: a Go worker (Sonnet-tier) writing the HTTP-level proof of Phase 1's outcome and measuring Open Question 2.
Owned paths: `tools/workflow/internal/serve/ingest_policy_test.go` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-06-end-to-end-and-delta-share.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 1-05.
Runs alongside: nothing.
Budget: 5 files to read, about 150 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — Phase 1 Outcome (binding) and Open Question 2.
2. `tools/workflow/internal/serve/serve_test.go` — the `do` helper and server setup (lines 1-60).
3. `tools/hooklog/tests/fixtures/ingest_policy.json` — facts and `expect`.
4. `docs/plans/12-analytics-dashboard-overhaul/reports/1-05-ingest-policy.md` — what ingest now does.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The whole phase outcome is proved through the real handler, and the share of local-ledger deltas lacking the collapse key is reported.

## Contract

Phase 1 Outcome, cited: "the shared fixture batch is posted ... Removed events return `accepted` and leave no fact and no archive line. The deltas of one part leave exactly one fact, and resending the batch returns all `duplicate`. Every kept or collapsed event has a verbatim archive line under `archive/<YYYY-MM>/<conversation_id>.jsonl.zst`. No stored hook fact's `raw` contains `payload`. `norm_event`, `model` and the token columns equal the fixture's expected values." Open Question 2: "What share of deltas lack the collapse key ... If the share is more than 1%, collapse needs a fallback key before Phase 2 runs."

Settled by this brief:
- The route is `POST /v1/ingest` with body `{"facts":[...]}` (the design's `/v1/facts` is a naming slip; do not change code for it). Use the in-process handler and tenant dir exactly as `serve_test.go` does.
- Assertions go through the files and SQL a user would inspect: decode each `archive/<YYYY-MM>/<conv>.jsonl.zst` with the `archive` package or `klauspost/compress/zstd`, count `facts` rows by SQL, read the `raw` column. This test adds no production code; if it exposes a defect in 1-05's code, report `blocked` with the symptom, do not fix it here.
- Resend: post the identical batch again; expect `duplicate` for every non-remove fact, `accepted` for remove, and unchanged fact counts.

### Delta-key share (Open Question 2)

Run, read-only, and put the output in the report:
`sqlite3 -readonly "file:$HOME/.local/share/workflow/serve/local/ledger.db?mode=ro" "select count(*), sum(coalesce(json_extract(raw,'$.payload.event.properties.messageID'),'')='' or coalesce(json_extract(raw,'$.payload.event.properties.partID'),'')='' or coalesce(json_extract(raw,'$.payload.event.properties.field'),'')='') from facts where event='message.part.delta'"`
(about 20 s; the orchestrator's recon on 2026-10-09 got `8327466|0`, so expect 0 lacking, and the ledger has grown since the design's 7.46M figure). State the share as a percentage and whether it is above 1%.

### Keep untouched

Everything else.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/serve/ -run IngestPolicy -v` → pass with subtests named for each of the six outcome bullets.
- `go test ./...` from `tools/workflow` and `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` → both pass (the phase gate); paste the summary lines.
- The delta-share query output and the verdict on Open Question 2 are in the report.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.

## Amendments from unit 1-05 (do these too)

- The shared fixture's expected statuses are wrong for collapsed deltas: later deltas of one part (`fx-opencode-43`, `-44`, `-46`) return `duplicate` on first send, because the part already has its row. Correct the fixture's expectations to that rule.
- `internal/archive/archive.go` encodes JSON with HTML escaping, so `<`, `>` and `&` in an archived fact become `<` etc. and the archive is not verbatim. Encode with HTML escaping off. Add a test with those characters in a body, round-tripped through `Append` and `Read`.
