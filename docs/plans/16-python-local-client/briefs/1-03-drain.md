# Brief: 1-03 — Drain command

Consumer: the execute worker for this unit.
Owned paths: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_drain.py`, `docs/plans/16-python-local-client/reports/1-03-drain.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push.
Report: before committing, write `docs/plans/16-python-local-client/reports/1-03-drain.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: 1-02.
Runs alongside: 1-04.
Budget: 14 files to read, about 1,400 lines to change, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/16-python-local-client/DESIGN.md` — Domain: Plugin client, the **`drain`.** bullet (line 29); Domain: Collector, the Contract sentence on the lock (line 45); Assumption 3 (lines 81-86) and Assumption 7 (lines 110-114).
2. `docs/design/02-edge-capture.md` — **Start.** through **Delivery.** (lines 48-107). Binding. The Go tests win on asserted strings.
3. `packages/yakka/internal/drain/drain.go` — `ReasonIdle`, `ReasonLockHeld`, `ReasonGaveUp`, `ReasonStopped` (lines 39-44), `Options` including `afterRelease` (lines 66-82), `Run`, `QueueDir`, `EnsureDirs`, `Running`.
4. `packages/yakka/internal/drain/http.go` — `HTTPSink.Send` and `ConfigSink`.
5. `packages/yakka/internal/drain/cli.go` — `RunStandalone` (lines 16-48) and the duration env names. `RunStatus` is Phase 3; do not port that command.
6. `packages/yakka/internal/drain/drain_test.go` — every test except `TestHostedRetriesLockAndWakes`. `opts` (lines 96-102) is the shortened clock the tests rely on.
7. `packages/yakka/cmd/yakka/drain_test.go` — `TestHalfSetEnvRefusal` (lines 481-535). Port the drain half only (the `drain` command from line 523, plus the loopback listener and the env that sets exactly one of the pair).
8. `plugins/yakka/client/yakka.py` — `Load`, `ErrPartialEnv`, `Build`, `File`, `Output`. Replace `cmd_drain`. Do not re-read 1-01 or 1-02 test files.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Make `python3 plugins/yakka/client/yakka.py drain` post the queue the way the Go client drain does, and lock that with the ported drain tests, including under Python 3.10.

## Contract

Settled by `DESIGN.md`. Do not reopen it.

> **`drain`.** Same queue (`$YAKKA_QUEUE` or `~/.local/share/yakka/queue`), same `.drain.lock` flock, same fact building and client scrub, same `POST <endpoint>/v1/ingest` body `{"facts":[...]}` with `Authorization: Bearer <key>` when a key is set. Delivery follows [design 2](../../design/02-edge-capture.md): delete on `accepted` or `duplicate`; `rejected/` plus a `.reason` on a rejected fact; retry on 5xx, network error, 401, 403, 408; `Retry-After` on 429; split on 400 or 413; idle exit with rescan. Fact kinds, `repo_id`, content hash, and the secret scrub follow [design 1](../../design/01-event-model-and-ingest.md). The lock is the ported Go tests in `internal/clientconfig`, `keys`, `secrets`, `facts`, and `drain`, excluding `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal`. Cases in `cmd/yakka/drain_test.go` that boot `yakka serve` stay Go. Strings the ported tests assert are part of the contract.

> The hosted drain and the Python drain exclude each other with the same `.drain.lock` flock.

> No. `serve` keeps hosting the drain in-process, so the Go drain, facts, secrets, keys, and MCP packages stay. The plugin path stops calling them.

Design 2's delivery table (lines 93-98) is the behavior the tests lock:

> | 200 with per-fact results | a file whose facts are all `accepted` or `duplicate` is deleted; a file with any `rejected` fact moves to `rejected/` with those reasons (its accepted facts are already stored, and a resend dedupes) |
> | 5xx, network error, 401/403/408 | retry with backoff; files stay |
> | 429 | retry after `Retry-After` |
> | 400, 413 | split the batch and resend in halves; a single file that still gets 400 or 413 moves to `rejected/` with the status as its reason |

Exit reasons the Go tests compare are `idle`, `lock held by another drain`, `backoff at cap and no new file`, and `stopped`. `RunStandalone` prints `yakka drain:` plus `Load`'s error and returns 1 when the error is `ErrPartialEnv`, before any request. Duration overrides are `YAKKA_DRAIN_WINDOW`, `YAKKA_DRAIN_LINGER`, `YAKKA_DRAIN_BACKOFF_MAX`, and `YAKKA_DRAIN_GIVEUP`. Python 3.10 and the standard library only. Linux and macOS only; the lock is `fcntl.flock` on `.drain.lock`.

## Changes

Replace `cmd_drain` so `python3 plugins/yakka/client/yakka.py drain` is `RunStandalone`. Call 1-02's `Build` with `File` (`Name`, `Data`) and read `Facts` and `Reasons`. Call 1-01's `Load`. Do not reimplement config, keys, secrets, or fact building.

Port `Run`, `Options` (including the test hook `afterRelease`), `HTTPSink`, `ConfigSink`, `QueueDir`, `EnsureDirs`, `Running`, and `QueueStatus`. `TestStatusData` uses `QueueStatus`; port it. Do not implement the `status` command (`RunStatus` is Phase 3). Do not port `TestHostedRetriesLockAndWakes` and do not add a hosted mode: `serve` keeps the Go drain. There is no `Wake` channel and no `Hosted` flag in this program.

`test_drain.py` ports the `internal/drain` tests except `TestHostedRetriesLockAndWakes`, plus the drain half of `TestHalfSetEnvRefusal`. Go tests in package `drain` set unexported fields; on this script those names are public attributes the Python tests set (`afterRelease`, `Options`, `HTTPSink`). Keep the shortened durations from `opts`. The half-set test listens on `127.0.0.1:8770`, runs this script's `drain` (not the Go binary) with exactly one of `YAKKA_ENDPOINT` and `YAKKA_KEY` set, and asserts what the Go drain half asserts: non-zero exit, stderr contains `YAKKA_ENDPOINT`, and the listener accepted nothing. Do not port the `status` half of that test.

Write the failing tests before replacing `cmd_drain`.

The suite must also pass on a 3.10 interpreter. `python3` here is newer than 3.10. If `python3.10` is not on `PATH`, install CPython 3.10 outside the repo (no project dependency, nothing committed) and run the same unittest command with it.

### Keep untouched

Do not edit Go files. Do not edit 1-01 or 1-02 test modules except if a port bug in `yakka.py` makes them fail; fix the port, not the assertions. Do not edit `spool.sh`, design 2, or the OpenCode plugin (1-04). Do not implement `mcp`, `login`, `status`, or `version`. Do not add a module or `__init__.py`. `main` still rejects every command other than `drain` with `yakka: unknown command` and exit 2.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- From the repo root, `python3 -m unittest discover -s plugins/yakka/client -t plugins/yakka/client -p 'test_*.py'` → exit 0.
- The same command with the 3.10 interpreter → exit 0. Record `python3.10 --version` (or the binary you invoked) in the report.
- From `packages/yakka`, `go test ./internal/clientconfig ./internal/keys ./internal/secrets ./internal/facts ./internal/drain -count=1` → exit 0.
- From `packages/yakka`, `go test ./cmd/yakka -count=1 -run 'TestBurst|TestWriteArtifactVersion|TestCommitCalls|TestRejectedSecretArtifact|TestDownUp|TestClientEnvDrainIngest|TestCaptureOutcome|TestLocalModeHosting|TestAdvisoryOutcome|TestServeOutcome|TestReadsWiring|TestServeScorerWiring|TestHalfSetEnvRefusal'` → exit 0. Those Go tests still boot `yakka serve` or, for `TestHalfSetEnvRefusal`, the Go binary. They are not the plugin client's suite.
- A direct run is not required beyond the tests. `TestDeliveryAuthHeader` is the check that the post carries `Authorization: Bearer <key>`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
