---
brief_id: 224
design_id: 209
---

# Brief: 4-03 — `workflow mcp` wiring and the phase 4 outcome test

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. The orchestrator runs this unit's
`TestAdvisoryOutcome` to close phase 4; phase 5 (distribution and harness registration) registers
the `workflow mcp` command this unit wires.
Owned paths: `tools/workflow/cmd/workflow/main.go` (only the `case "mcp"` branch and a `runMCP`
function), new `tools/workflow/cmd/workflow/advisory_outcome_test.go`,
`docs/plans/09-workflow-binary/reports/4-03-mcp-wiring-outcome.md` (new). Touch nothing else; in
particular not `internal/` (4-01 and 4-02 own those; a defect there is reported, not fixed), the
other `cmd/workflow/*_test.go` files (reuse their helpers), `go.mod` or `go.sum`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 4-01 (the four reads, checks loading without a key) and 4-02 (`internal/mcp`,
`facts.WritePaths`), both committed. Read their reports first.
Runs alongside: nothing (it edits `main.go` after 4-01 and tests both units together).
Budget: 8 files to read, about 400 lines to write including tests, 50 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 4 (lines 210-220), the outcome sentence
   verbatim.
2. `docs/plans/09-workflow-binary/reports/4-01-service-reads.md` and `4-02-mcp-shim.md`: what was
   built, exported names, the example responses and answer texts.
3. `docs/design/04-advisory-surface.md` — `artifact_feedback` (lines 31-50), Unreachable service
   (lines 73-77), Tests (lines 98-103).
4. `go doc ./internal/mcp` (`Serve`, `Options`).
5. `tools/workflow/cmd/workflow/main.go` — `run` and `runServe` (whole file is about 150 lines).
6. `tools/workflow/cmd/workflow/drain_test.go` — `env`, `newEnv`, `writeConfig`, `spool`,
   `queued`, `rejected`, `ledger`, `noSecret`, `gitRepo` (lines 1-170, and grep `func gitRepo`).
7. `tools/workflow/cmd/workflow/capture_test.go` — `startHosted`, `writeFile`, `writePayload`
   (lines 20-130).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, `workflow mcp` runs the advisory shim on stdin and stdout, and one test run
against the built binary, a temp hosted `serve` and a temp queue proves every clause of the phase 4
outcome.

## Contract

Cited, binding (DESIGN.md, Phase 4 outcome): "`GET /v1/artifacts`, `/v1/checks`, `/v1/baselines`
and `/v1/search` answer per design 4 API against a temp `serve`; over stdio `workflow mcp` answers
`initialize` and lists exactly `artifact_feedback`, `list_checks`, `search_artifacts`;
`artifact_feedback` gives distinct answers for queued, rejected, delivered and stale files, with
baseline flags; with the service down it returns local state and no MCP error."

Decisions made at refine (settled):

- **Wiring.** `case "mcp"` calls `runMCP(args)`: `mcp.Serve(ctx, os.Stdin, os.Stdout,
  mcp.Options{Version: version, QueueDir: drain.QueueDir(), …})` with the default drain starter,
  context cancelled on SIGINT/SIGTERM, exit 0 on EOF, 1 on a fatal error (stderr). No flags. Nothing
  but JSON-RPC on stdout.
- **The test drives the binary.** `TestAdvisoryOutcome` in `cmd/workflow`, using `newEnv` (built
  binary, temp `HOME`, `WORKFLOW_QUEUE`, `WORKFLOW_CLIENT_CONFIG`, `TYPESAFE_API_KEY=` blank) and a
  hosted `serve` from `startHosted("127.0.0.1:0")` with `WORKFLOW_CHECKS_DIR=../../../quality` added
  to its environment (4-01 loads checks without a key). One `workflow mcp` child per subtest or per
  group, with its working directory in the temp repo, fed JSON lines on stdin, replies read line by
  line with a 10 s deadline.
- **Baseline data without Jev.** No key means verdicts are `unscreened` and no scores. To prove
  flags, the test writes `scores` rows straight into the temp tenant's `ledger.db`
  (`<WORKFLOW_SERVE_DATA>/<tenant>/ledger.db`, columns `content_hash, check_name, result, scorer,
  at`, scorer `test`) for five delivered designs, via `database/sql` with `modernc.org/sqlite`
  (already a dependency; WAL allows the write beside the running serve). The target design gets the
  lowest score on one check. This is test setup, not a product path.
- **Drains the shim starts.** The default starter launches the built binary's `drain` with the
  test's environment. Kill every process whose command line holds the test's temp dir in
  `t.Cleanup`, and check none remain.

## Changes

`cmd/workflow/main.go`: `runMCP` and the `case "mcp"` branch. `cmd/workflow/advisory_outcome_test.go`:
the test below, reusing existing helpers. A small JSON-RPC client helper inside the test file.

### Keep untouched

Every other subcommand and the `runServe` and `screenStep` code as 4-01 left it. All earlier tests
pass unchanged.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

Fail first: write `TestAdvisoryOutcome` first and quote its failure (`not implemented yet`, exit 2).

- `go vet ./... && go test -race -count=1 ./...` → passes.
- `go test -v -count=1 -run TestAdvisoryOutcome ./cmd/workflow` → the orchestrator's phase gate.
  One subtest per outcome clause, each printing PASS/FAIL:
  1. **reads**: with the test key, `GET /v1/artifacts` for a delivered design has every design 4
     field; `/v1/checks?kind=design` lists 11; `/v1/baselines?kind=design` has `n`, `p25`,
     `median`, `p75` for the seeded check; `/v1/search?q=<distinctive word>` returns that design
     with a `[word]` snippet. Clause: "answer per design 4 API against a temp `serve`".
  2. **initialize**: `protocolVersion` echoed, `serverInfo.name` `workflow`. Clause: "answers
     `initialize`".
  3. **tools/list**: exactly the three names, no more. Clause: "lists exactly …".
  4. **queued**: stop the hosted serve; write a design and spool its write → `state: queued`, `1
     events`, `remote unreachable`. Clause: "queued".
  5. **rejected**: with serve running, write a design containing a fake AWS key
     (`AKIA` + 16 chars built at runtime) and spool it; wait until it is in `rejected/` → `state:
     rejected`, the pattern name, the rewrite fix, and `noSecret` holds for the answer text. Clause:
     "rejected".
  6. **delivered with baseline flags**: five designs written, spooled and delivered; seed scores; →
     `state: delivered`, `screen: unscreened`, the target's seeded check line has `BELOW p25`, the
     others do not. Clause: "delivered … with baseline flags".
  7. **stale**: rewrite a delivered design without spooling → `state: stale`. Clause: "stale".
  8. **four distinct answers**: the first lines of 4 to 7 are four different states. Clause:
     "distinct answers".
  9. **service down**: serve stopped, a queued file and a delivered file asked about → each reply is
     a JSON-RPC `result` (no `error` member), `isError` false, text has local state and `service
     unreachable at`; `list_checks` and `search_artifacts` likewise say unreachable. Clause: "with the
     service down it returns local state and no MCP error".
  10. **tools answer**: with serve up, `list_checks {kind:"report"}` lists 5 checks;
      `search_artifacts` finds the distinctive word. (Guards the two tools the outcome only names.)
- Confirm after the run: `pgrep -f '<the test temp dir>'` prints nothing.

Safety: temp dirs only (`t.TempDir()`); `WORKFLOW_SERVE_DATA`, `WORKFLOW_QUEUE`, `HOME` and
`WORKFLOW_CLIENT_CONFIG` point at temp paths for every child. Never touch the live queue,
`~/.config/workflow` or `~/.local/share/workflow*`. Every `serve` listens on `127.0.0.1:0` (never
8765 or 8770) and is killed after; every drain the shim starts is killed in `t.Cleanup`.
`TYPESAFE_API_KEY` is in your environment: every child process gets `TYPESAFE_API_KEY=` (blank);
never print, log, echo or write it (no `env`, `printenv`, `set -x`). No Jev call is made in phase 4.
The fake AWS key and the test client key never appear in test output or the report.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 4: workflow mcp wiring and
outcome test` (the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/4-03-mcp-wiring-outcome.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), including the full `TestAdvisoryOutcome` subtest lines and the first three lines of each
state's answer, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
