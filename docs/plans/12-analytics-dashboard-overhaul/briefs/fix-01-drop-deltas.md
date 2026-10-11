# Brief: fix-01 — Drop `message.part.delta` at the source (plugin and ingest)

Consumer: a worker (flash-tier) editing the OpenCode hooks plugin and the Go ingest policy. Fixer unit after Phase 3: it closes no phase and its commit carries no `Workflow-Phase` trailer.
Owned paths: `packages/opencode-workflow-hooks/src/index.ts`, `packages/opencode-workflow-hooks/tests/test_hooks.mjs`, `packages/opencode-workflow-hooks/README.md`, `tools/hooklog/tests/fixtures/ingest_policy.json`, `tools/workflow/internal/ingest/` (all files), `tools/workflow/internal/compact/` (only to delete the collapse branch and its tests, and to update delta expectations), `tools/workflow/internal/serve/ingest_policy_test.go`, `tools/workflow/internal/store/` (comments only). Touch nothing else (not `docs/`, except your report).
Commits: Commit to the current branch when done evidence passes, plain-summary title, no `Workflow-Phase` trailer. Stage only owned paths and the report (`git add <paths>`; `git commit -- <paths>`). End the message with these two trailer lines: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_011T4Vh5cPS7acScndWmdobz`.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/fix-01-drop-deltas.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit. Your final message: the commit hash and a short summary.
Depends on: nothing.
Runs alongside: nothing.
Budget: 10 files to read, about 400 lines changed (mostly deletions), 60 tool turns. Past the budget, stop: write a handoff report, commit what passes, report `over budget`.

Go is at `$HOME/.local/go/bin`; run Go commands as `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go ...`. Repo: `/home/codyh/workspace/workflow-plugin`, branch `plan/12-analytics-dashboard-overhaul`. Never touch `~/.local/share/workflow`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md`, section "Amendments after sign-off" (binding), and `IMPLEMENTATION.md` Phase 3 Carried items 12 and 13.
2. `docs/plans/12-analytics-dashboard-overhaul/briefs/1-03-plugin-remove-list.md` (how the remove-list block is declared) and `briefs/1-05-ingest-policy.md` (policy table, fixture, equality test).
3. `tools/workflow/internal/ingest/policy.go`, then `grep -n "Collapse\|CollapseHash\|collapseKey" -r tools/workflow`.
4. `tools/workflow/internal/ingest/ingest.go` near the `action == Collapse` branch; `internal/compact/compact.go` `processBatch`.

## Goal

A `message.part.delta` event is dropped by the OpenCode plugin and, if one still arrives at ingest, answered `accepted` with no fact row and no archive line, whatever its payload (keyed or keyless). No `collapse` outcome remains.

## Contract (settled by this brief)

- Plugin: add `"message.part.delta"` to the `REMOVE_EVENTS` array between the `remove-list:begin/end` markers (one double-quoted string per entry, same form). Update the plugin test (the marked-block assertion lists five entries; delivering a `message.part.delta` bus event queues nothing; `message.part.updated` still queues) and README (name the fifth event and why: streamed chunks are redundant with `message.part.updated`).
- Ingest policy: `{"opencode","message.part.delta"}` becomes `Remove`. The plugin-versus-ingest equality test (`TestRemoveListMatchesPlugin`) passes with five entries.
- Decision, delete the dead collapse mechanism: nothing else uses it once delta is Remove. Delete the `Collapse` action, `collapseKey`, `CollapseHash`, the `action == Collapse` branches in `ingest.go` and `compact.processBatch` (and the `survivors` map and the existing-survivor SQL lookup that only served collapse), the `Stats.Collapsed` field, and every test and comment that exercised only collapse (`TestPolicyCollapseNeedsKey`, collapse-hash tests, `deltas_of_one_part_leave_one_fact`, `TestCollapseSurvivorFirstArrival`, `TestPreexistingSurvivor` and similar). `Policy` keeps its signature (harness, event, payload) unless an unused parameter makes `go vet` fail; if you simplify it, update all callers. Keyless deltas are Remove too, so the "keep path for a keyless delta" disappears: delete its tests. Remove the `"message.part.delta"` entry from `normalise.go`'s event map (ingest never stores one) and its test expectation.
- Fixture `tools/hooklog/tests/fixtures/ingest_policy.json`: every delta fact's `expect.policy` becomes `remove` (and its first/resend statuses follow the remove rule: accepted on both). Adjust `TestIngestPolicy`, `TestIngestPolicyEndToEnd` style tests in `internal/ingest/policy_test.go` and `internal/serve/ingest_policy_test.go` to match: a delta posts as `accepted`, leaves no fact and no archive line, including a keyless delta.
- `compact.Run` itself stays a one-pass compaction for legacy ledgers: with delta now Remove it deletes delta rows and writes no archive line for them. Update its tests (`compact_test.go`, `rollup_test.go`, `verify_test.go`) that used deltas to assert removal instead of collapse; where a test needed a collapsing event to exercise rollup drift, use a remove-listed event such as `chat.params`.
- Rollup semantics: nothing to change in `store/rollup.go` beyond comments that mention collapsed deltas.
- Keep untouched: `Remove` handling for the other four events, `Keep` envelope behaviour, `archive` package, the `ledger compact` CLI.

## Done evidence

Identify or write the failing check before changing code (the equality test with the five-entry block, and a delta posted to ingest leaving a fact, are the failing checks). Report before and after.

- `cd tools/workflow && PATH=$HOME/.local/go/bin:$PATH go build ./... && go vet ./... && go test ./...` pass; `gofmt -l .` prints nothing.
- `cd packages/opencode-workflow-hooks && node --test tests/test_hooks.mjs` (or the package's own invocation) passes.
- `grep -rn "CollapseHash\|ingest.Collapse\|collapseKey" tools/workflow` prints nothing.
- `git diff --stat` shows only owned paths.

## Report back

Under 1,000 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, any deviation and why, any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

Do not spawn agents beyond read-only research helpers.
