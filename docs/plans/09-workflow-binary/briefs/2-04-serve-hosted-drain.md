---
brief_id: 219
design_id: 209
---

# Brief: 2-04 — `serve` hosts the drain, and the phase 2 outcome test

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its output closes phase 2; the
orchestrator verifies the phase outcome against the test written here. Phase 5's `workflow init`
writes the client config this mode keys on.
Owned paths: `tools/workflow/internal/serve/`, `tools/workflow/cmd/workflow/main.go` (the `serve`
wiring), `tools/workflow/cmd/workflow/main_test.go`, `tools/workflow/cmd/workflow/capture_test.go`
(new), `tools/workflow/go.mod`, `tools/workflow/go.sum`,
`docs/plans/09-workflow-binary/reports/2-04-serve-hosted-drain.md`. Touch nothing else.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 2-03 (and through it 2-01, 2-02).
Runs alongside: nothing.
Budget: 10 files to read, about 700 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 2 outcome (lines 163-178). The test you write
   is what the orchestrator runs to close the phase. Also IMPLEMENTATION.md's Phase 1 Carried
   item 4.
2. `docs/design/03-remote-service.md` — Local and remote (lines 36-48), Local serve hosts the drain
   (lines 179-198), Tests 5 (lines 215-217). Binding.
3. `docs/design/02-edge-capture.md` — Drain Start (lines 48-52) and Config (lines 121-139).
4. `docs/design/01-event-model-and-ingest.md` — Edges (lines 49-55): the join the outcome queries.
5. `docs/plans/09-workflow-binary/reports/2-01-spool-coexistence.md`,
   `reports/2-02-facts-clientconfig.md`, `reports/2-03-drain-status.md` — what was built and the
   final API names.
6. `go doc` of `./internal/drain`, `./internal/clientconfig`, `./internal/ingest`, `./internal/serve`.
7. `tools/workflow/internal/serve/serve.go` — `New`, `tenant`, `tenantFor`, `Close`; and
   `cmd/workflow/main.go` `runServe`.
8. `tools/workflow/cmd/workflow/drain_test.go` — 2-03's binary helpers; reuse them.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Make local `workflow serve` drain the user's queue in process when the client config points at
it, and leave the queue alone otherwise; then prove the whole phase 2 outcome in one test.

## Contract

Cited, binding (design 3, Local serve hosts the drain): "It takes `queue/.drain.lock` and holds it
while running, so hooks find the lock held and start nothing"; "it watches the queue directory
(inotify on Linux, kqueue on macOS) with a slow poll as a fallback. The design 2 batch window still
applies"; "It runs the same drain module as `workflow drain`, with an in-process sink in place of
HTTP. The sink calls the same ingest function as the handler, so the precheck and screening apply.
In process never means unchecked"; "It drains only when the client config's endpoint is this
server (same host and port). Otherwise the queue is addressed elsewhere and it leaves it alone. Its
tenant is the one the client config's key maps to"; "If it stops, the lock is released, the next
hook starts a standalone drain, and that drain posts to the endpoint with backoff until `serve`
returns." Design 2 Config: "Re-read on every batch".

Carried from phase 1 (absorbed here): item 4, "`TestServeOutcome` picks a free port by binding and
releasing it, which is a small race."

Decisions made at refine (settled):

- **Queue**: `serve` uses the same queue resolution as the drain (`WORKFLOW_QUEUE`, else the
  default). Hosting is decided on a tick (every `Poll`, a few seconds): load the client config; host
  when its endpoint's port equals the bound port and its host is the bound host, or both are
  loopback (`127.0.0.1`, `localhost`, `::1`), and its key maps to a configured tenant. Not hosting
  means the lock is never taken. If a tick finds the config no longer points here, stop the hosted
  drain and release the lock. No config, or a key that maps to no tenant, logs once per change and
  does not host.
- **Lock**: hosted mode uses 2-03's `Hosted` option: it retries the lock every `Poll` while a
  standalone drain holds it, and holds it until `serve` stops. Graceful shutdown stops the hosted
  drain before closing tenants.
- **Sink**: an in-process sink that calls `ingest.Ingest` with the tenant from the server's
  registry (the same one the HTTP handler uses, so the pending worker wakes) and returns status 200
  with its results, or 500 on a whole-request error.
- **Watch**: Linux uses inotify through `golang.org/x/sys/unix` (already in `go.sum` as indirect;
  promote it) on the queue dir for `IN_MOVED_TO`/`IN_CREATE`, feeding 2-03's `Wake` channel, with
  a 5 s poll as fallback. Other platforms use the poll only; kqueue on macOS is deferred (name it in
  the report; phase 5 owns darwin).
- **Carried item 4**: `serve` logs one line `serve: listening on <addr>` to stderr after binding,
  and accepts `WORKFLOW_SERVE_ADDR` with port `0`. `TestServeOutcome` and the new tests start serve
  on `127.0.0.1:0` and read the address from that line. Because hosting is decided per tick, a
  test may write the client config after reading the bound port.

## Changes

`internal/serve`: hosting tick, in-process sink, watcher, shutdown order, the listening line.
`cmd/workflow/main.go`: pass the queue and client-config hooks into `serve` as needed.
`main_test.go`: port 0 per carried item 4. New `capture_test.go`: the phase outcome below.

### Keep untouched

`internal/drain`, `internal/facts`, `internal/clientconfig` (report gaps; one-line fixes allowed and
named); 2-03's tests must still pass unchanged (they start `serve` with no client config, so it
never hosts). The `/v1` handlers and auth from phase 1.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test -race ./...` → passes, including 2-03's binary tests and
  `TestServeOutcome` on port 0.
- `go test -v -run TestCaptureOutcome ./cmd/workflow` → one temp root (`t.TempDir()`) holding the
  queue, `HOME`, serve data, client config and a temp git repo; `serve` on `127.0.0.1:0` with
  `WORKFLOW_SERVE_KEYS=t=k`, the client config pointing at its address with key `k`;
  `WORKFLOW_BIN` is a wrapper that logs each start. Subtests, in order:
  1. **Hosted burst**: 20 concurrent `spool.sh --harness claude` calls → the wrapper log shows zero
     starts, the queue empties, the ledger has 20 more `hook_event` rows.
  2. **Write**: the `artifact_writes.json` Claude `Write` fixture for `docs/plans/x/DESIGN.md` →
     an `artifact_version` row, source `worktree`.
  3. **Commit and join**: commit that file in the temp repo, replay a `commit_calls.json` fixture
     with the real SHA through `spool.sh` → a `commit` row and a `commit`-source version; then one
     SQL query over `ledger.db` returns (artifact path, commit SHA, conversation ID), joining
     `artifact_version` → `commit` (by `repo_id` and the path in the commit's `paths`, via
     `json_each(raw, '$.paths')`) → the commit's `conversation_id`. Quote the query and its row in
     the report.
  4. **Secret**: a DESIGN.md with a concatenated credential → its queue file in `rejected/` with a
     `.reason` naming pattern and line; the secret is in no file under the serve data dir, no
     `.reason` and no log.
  5. **Endpoint elsewhere**: restart `serve` with the client config pointing at another port and
     `WORKFLOW_HOOKLOG_KICK=0` for the spools → files stay queued, and `flock -n` on
     `.drain.lock` succeeds (serve does not hold it).
  6. **Kill and recover**: config back to `serve`; `kill -9` serve; spool 5 files (kick on,
     `WORKFLOW_DRAIN_BACKOFF_MAX=1s`, `WORKFLOW_DRAIN_LINGER=2s`) → the wrapper logs a start; files
     stay while serve is down; restart `serve` on the same address → all files delivered; after
     the standalone drain exits, `serve` holds the lock again (`flock -n` fails).
  7. **Status**: `workflow status` reports the queue count, rejected count and `drain: running`.
- The test prints the phase outcome as one line per outcome clause with pass/fail, so the
  orchestrator can quote it.

Safety: test only under `t.TempDir()`, with `WORKFLOW_QUEUE`, `HOME`, `WORKFLOW_CLIENT_CONFIG`,
`WORKFLOW_SERVE_DATA` and `WORKFLOW_HOOKLOG_DIR` set to temp paths. Never touch
`~/.local/share/workflow*`, the legacy spool (`~/.local/share/workflow-plugin/hooklog`),
`~/.config/workflow`, or ports 8765/8770. Kill every `serve` and drain you start (`t.Cleanup`);
confirm none survive with `pgrep -f '<tempdir>'` before reporting. Never print `TYPESAFE_API_KEY`
or any key.

Commit: title `[exec <execution_id>] Phase 2: serve hosts the drain` (the orchestrator supplies the
id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/2-04-serve-hosted-drain.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems;
nothing derivable) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
