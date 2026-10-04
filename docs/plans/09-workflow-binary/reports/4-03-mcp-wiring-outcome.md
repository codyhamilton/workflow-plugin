---
brief_id: 224
---

# Execution report: 4-03 `workflow mcp` wiring and outcome test (exec 26)

## Done

- `cmd/workflow/main.go`: `case "mcp"` calls `runMCP(args[1:])`: `mcp.Serve(ctx, os.Stdin, os.Stdout, mcp.Options{Version, QueueDir: drain.QueueDir()})`, default drain starter, ctx cancelled on SIGINT/SIGTERM, exit 0 on EOF, 1 on a fatal error (stderr), 2 on any argument.
- `cmd/workflow/advisory_outcome_test.go`: `TestAdvisoryOutcome` drives the built binary, a hosted `serve` on `127.0.0.1:0` (checks from `../../../quality`, no key) and a temp queue; one `workflow mcp` child with its working directory in the temp repo; JSON-RPC client with a 10 s reply deadline that fails on any non-JSON stdout line. Scores for five delivered designs are inserted into the tenant `ledger.db` (scorer `test`).

## Evidence

Before (only the test, `case "mcp"` still `not implemented yet`, exit 2):
```
outcome reads PASS
--- FAIL: TestAdvisoryOutcome
    advisory_outcome_test.go:271: mcp stdout closed
    --- FAIL: TestAdvisoryOutcome/initialize
```
After: `go vet ./... && TYPESAFE_API_KEY= go test -race -count=1 ./...` all packages ok. `go test -v -count=1 -run TestAdvisoryOutcome ./cmd/workflow`:
```
outcome reads                  PASS
outcome initialize             PASS
outcome tools-list             PASS
outcome queued                 PASS
outcome rejected               PASS
outcome delivered-baseline     PASS
outcome stale                  PASS
outcome distinct-answers       PASS
outcome tools-answer           PASS
outcome service-down           PASS
```
After the runs, `pgrep` shows no process of mine (every temp dir is killed by `pkill -9 -f <tmp>` in `newEnv`'s cleanup).

## First lines of each answer (hash and repo elided)

- queued: `state: queued` / `path: docs/plans/10-adv/DESIGN.md` / `repo: root:<sha>`; further down `1 events for this file still queued, oldest ..., remote unreachable` and `service unreachable at <endpoint>`.
- rejected: `state: rejected` / `path: docs/plans/11-adv/DESIGN.md` / `repo: root:<sha>`; further down `secret: aws_access_key at line 3 ...` and `Fix: rewrite the file; the new write is the repair.`
- delivered: `state: delivered` / `path: docs/plans/01-adv/DESIGN.md` / `repo: root:<sha>`; further down `screen: unscreened (no scorer on the service)` and the target's check line with `BELOW p25`.
- stale: `state: stale` / `path: docs/plans/02-adv/DESIGN.md` / `repo: root:<sha>`.
- service down: queued file `state: queued ... service unreachable at`; delivered file `state: not delivered ... service unreachable at`. All `result`, `isError` false.

## Default drain starter (4-02's unverified item)

Verified at binary level: in `queued`, the queue write is spooled with `WORKFLOW_BIN=/bin/true` so spool.sh starts no drain; the shim's default starter (`os.Executable()` + `drain`) then takes the drain lock (`lockHeld` true within 5 s) and the wrapper start count does not change. It works.

## Departures

- Subtest order: `tools-answer` runs before `service-down` (it needs serve up); the brief numbers it 10.
- Rejection body is `the credential AKIA... was pasted here`, not `key = AKIA...`: the latter is classified `env_assignment` by the secret scanner, not `aws_access_key`.
- "Delivered, with baseline flags" and "stale" use designs delivered in setup (before `reads`), since scores must exist before the baselines read.
- A delivered file asked about with serve down answers `state: not delivered` plus `service unreachable at`, not `delivered` (the shim cannot know delivery without the service); matches 4-02's design.
- Two queued/service-down writes spool with `WORKFLOW_BIN=/bin/true` (see above).

## Known problems

None found in `internal/`. No contradiction between brief and cited contracts.
