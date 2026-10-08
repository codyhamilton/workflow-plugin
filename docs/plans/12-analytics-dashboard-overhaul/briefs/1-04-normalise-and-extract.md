# Brief: 1-04 — Normalised event table, usage extraction and shared fixture

Consumer: a Go worker (Sonnet-tier) writing pure functions and the shared fixture batch that units 1-05 and 1-06 test against.
Owned paths: `tools/workflow/internal/ingest/normalise.go`, `tools/workflow/internal/ingest/extract.go`, `tools/workflow/internal/ingest/normalise_test.go`, `tools/workflow/internal/ingest/extract_test.go` (all new), `tools/hooklog/tests/fixtures/ingest_policy.json` (new). Touch nothing else, including `ingest.go` and `ingest_test.go`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report (`git commit -- <paths>`); other units commit in parallel.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-04-normalise-and-extract.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-01, 1-02, 1-03.
Budget: 8 files to read, about 450 lines to change (about 150 of them fixture JSON), 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Capture and event policy": bullets "Normalised event" and "Model and usage extraction" (binding), and Phase 1 Outcome.
2. `tools/hooklog/hooklog.py` lines 90-140 — the kinds the mapping is seeded from. Match event names case-insensitively as it does.
3. `tools/transcript/lib/usage.py` — `dedupe_usage` (Claude counting rule).
4. `tools/hooklog/tests/fixtures/commit_calls.json` first 20 lines — fixture style (a `note` field, synthesized payloads).
5. Real payload shapes: query the local ledger read-only, one row per event, e.g. `sqlite3 -readonly "file:$HOME/.local/share/workflow/serve/local/ledger.db?mode=ro" "select raw from facts where harness='codex' and event='transcript.token_count' limit 1 offset 50"`. Do the same for Claude and OpenCode `transcript.assistant_message`. Never run an unbounded query on `message.part.delta` (8.3M rows). Event list: `select harness,event,count(*) from facts where type='hook_event' and event!='message.part.delta' group by 1,2 order by 3 desc` (about 20 s).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Two pure functions give every hook event its `norm_event`, `tool`, `model` and token/cost fields, and one fixture batch pins the expected values for the whole phase.

## Contract

From DESIGN.md:
- `norm_event` is one of `session_start`, `session_end`, `prompt`, `tool_pre`, `tool_post`, `tool_fail`, `batch_end`, `assistant_message`, `usage`, `turn_end`, `subagent_start`, `subagent_end`, `compact`, `message_part`, `other`. "The mapping per harness is a table in `internal/ingest`, seeded from `tools/hooklog/hooklog.py`'s kinds. The native `event` is kept beside it."
- Extraction table (verbatim): Claude `transcript.assistant_message` gives `model`, `usage.{input,output,cache_read_input,cache_creation_input}_tokens`, `output_tokens_details.thinking_tokens`. Codex `transcript.token_count` gives `model`, `usage.{input,cached_input,output,reasoning_output,cache_write_input}_tokens`. OpenCode `transcript.assistant_message` gives `modelID`, `providerID` (model as `provider/model`) and `cost` as a harness-reported cost. Cursor: nothing.
- "One model call is counted once. A fixture test per harness compares extracted totals to `tools/transcript/parsers` (Claude) or hand totals."
- Non-goal: normalising tool names across harnesses.

Settled by this brief:
- Signatures (unit 1-05 calls these; keep the names):
  ```go
  type Derived struct {
      NormEvent, Tool, Model string
      TokIn, TokOut, TokCacheRead, TokCacheWrite, TokReasoning int64
      CostReported *float64 // nil when the payload carries no cost
  }
  func Derive(harness, event string, payload map[string]any) Derived
  ```
  `payload` is decoded with `json.Number` for numbers (as `Ingest` does). `Derive` never panics on missing or mistyped fields; it returns zero values. A nil payload is valid.
- `NormEvent` is always set (`other` for unmapped). Unknown harness or event is `other`.
- `Tool` is `payload.tool_name` for `tool_pre`, `tool_post` and `tool_fail` events, else empty.
- Usage events are `transcript.assistant_message` (all harnesses) and Codex `transcript.token_count`. Codex `transcript.token_count` maps to `usage`; its `usage` object is the per-call figure and `total` is cumulative: read `usage`, never `total`. Other `transcript.assistant_message` events map to `assistant_message`.
- The design's OpenCode row lists only model and cost, but its payload carries `tokens.{input,output,reasoning,cache.read,cache.write}` and Phase 1's outcome requires "the token columns" per harness. Extract those into the same columns, and say so in the report as a gap in the design table.
- Token fields are stored as reported. Codex `input_tokens` already includes `cached_input_tokens`; do not subtract. Add a code comment saying so, and list it in the report under "carried to Phase 3" (cost computation must not double-charge cached input).
- OpenCode `cost` of 0 (local models report 0) is treated as not reported: `CostReported` is nil unless `cost` > 0. Comment this in the code and list it in the report so Phase 3 knows a zero-cost local model falls to the pricing table and, failing that, `unpriced_calls`.
- Model: Claude/Codex `payload.model`; OpenCode `providerID + "/" + modelID` (just `modelID` when providerID is empty).
- Counting once: Claude repeats a `message_id` on a few transcript lines (8 of 13,612 locally). `Derive` is per-fact and cannot dedupe; do not try. Report in the report the duplicate-`message_id` count in the fixture and the local share, so the orchestrator can place read-side dedupe in Phase 3.

### The fixture

`tools/hooklog/tests/fixtures/ingest_policy.json`, style of `commit_calls.json`: `{"note": ..., "facts": [...], "expect": [...]}`. Each fact is a full wire fact (`id`, `type: "hook_event"`, `conversation_id`, `harness`, `event`, `ts`, `payload`) built from real shapes, trimmed. It must contain, per harness (claude, codex, opencode, cursor): at least one kept non-usage event of each distinct norm_event you map; for OpenCode: one fact for each of the four remove events (`experimental.chat.system.transform`, `chat.params`, `chat.headers`, `shell.env`), one `message.part.delta` part with 3 deltas in one conversation (distinct `delta` text, same `messageID`/`partID`/`field`), a second part with 2 deltas, one delta missing `partID` (keep), and a `transcript.assistant_message`; usage events for Claude (with `cache_creation_input_tokens`, `cache_read_input_tokens`, `thinking_tokens`), Codex (`token_count` with `usage` and `total`) and OpenCode; and one artifact-free conversation_id per harness. Do not put real secrets or environment values in remove-event payloads: use obviously fake values such as `"Authorization": "FAKE-NOT-A-SECRET"` that secrets.Scan does not flag (check by running `secrets.Scan` in your test).
`expect` lists per fact id: `policy` (`keep`|`collapse`|`remove`), `norm_event`, `model`, token fields, `cost_reported`, and `first_status` (`accepted`) / `resend_status` (`accepted` for remove, `duplicate` otherwise) for unit 1-06. Also include `expect_totals` per harness: summed token fields over its usage facts.
For Claude, derive `expect_totals` by running the real parser: `tools/transcript/lib/usage.py::dedupe_usage` over assistant messages built from your fixture usage (run it with `python3 -I` from `tools/transcript`; record in `note` the command and that totals came from it). Codex and OpenCode use hand totals, written out in `note`.

### Keep untouched

Nothing in `ingest.go`. Do not edit `hooklog.py`; the mapping is Go, seeded from it.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go test ./internal/ingest/ -run 'Normalise|Extract'` → pass. Table test: every `(harness, event)` pair from the fixture and every pair in the ledger event list you queried maps to the norm_event you list in the report; a test loads the fixture and asserts `Derive` equals `expect` for each fact; per-harness summed totals equal `expect_totals`.
- Python cross-check recorded in the report: the Claude totals command and its output.
- `go vet ./internal/ingest/` clean. `git diff --stat` shows only owned paths.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
