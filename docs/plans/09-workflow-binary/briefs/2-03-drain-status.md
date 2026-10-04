---
brief_id: 218
design_id: 209
---

# Brief: 2-03 — `workflow drain` and `workflow status`

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Unit 2-04 hosts this drain
module inside `serve`; phase 4's shim reads `queue/` and `rejected/` in the layout fixed here; phase
5 makes the hooks start it by default.
Owned paths: `tools/workflow/internal/drain/`, `tools/workflow/cmd/workflow/main.go` (the `drain`
and `status` dispatch only), `tools/workflow/cmd/workflow/drain_test.go` (new),
`docs/plans/09-workflow-binary/reports/2-03-drain-status.md`. Touch nothing else (`go.mod` only if a
dependency is unavoidable; say why in the report).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 2-01 (the real `spool.sh` and its `WORKFLOW_BIN` kick), 2-02 (`facts`, `clientconfig`).
Runs alongside: nothing.
Budget: 10 files to read, about 1,200 lines to write including tests, 80 tool turns. Past the
budget, stop: write a handoff under this brief's name in
`docs/plans/09-workflow-binary/IMPLEMENTATION.md` (done, not done, what you learned), commit, and
report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 2 (lines 163-178), and IMPLEMENTATION.md's
   Phase 1 Carried item 3.
2. `docs/design/02-edge-capture.md` — Shape (lines 14-27), Drain (lines 41-120: Start, Batch
   window, Linger, Idle exit without stranding, Delivery table, backoff, No local archive, No queue
   cap, macOS), Config (lines 121-139), Tests 1-3 (lines 220-end). Binding.
3. `docs/design/03-remote-service.md` — Ingest (lines 76-96): status codes the service returns.
4. `docs/design/05-distribution.md` — Local bootstrap, last paragraph: `status` reports an
   unreachable endpoint as a failure, not idle.
5. `docs/plans/09-workflow-binary/reports/2-01-spool-coexistence.md` and
   `reports/2-02-facts-clientconfig.md` — what was actually built, and the final API names.
6. `go doc` of `./internal/facts`, `./internal/clientconfig`, `./internal/ingest` (`Result`).
7. `tools/workflow/cmd/workflow/main.go` and `main_test.go` — dispatch, and how the phase 1 test
   builds the binary and starts `serve`.
8. `tools/hooklog/spool.sh` — the Go path and kick.
9. `tools/hooklog/drain.py` `daemon` (lines 172-199) — the existing release-then-rescan loop, for
   reference only.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Build the one-per-user drain of design 2: it takes the lock, batches queue files into facts,
delivers them to the configured endpoint, deletes or rejects each file by its worst fact, survives
an unreachable remote without losing anything, and exits when idle without stranding a file; and
`workflow status` reports the queue.

## Contract

Cited, binding: design 2 Drain in full, in particular "holding an exclusive flock on
`queue/.drain.lock` for its lifetime"; "the drain acquires with a short blocking wait (about 1 s),
not `-n`"; batch window "about 1.5 s"; linger "about 60 s with an empty queue (configurable)"; idle
exit "Release the lock, rescan the queue, and if files exist, try to retake the lock and continue;
if another drain holds it, exit"; the Delivery table (200 per-fact; 5xx, network error,
401/403/408 retry; 429 `Retry-After`; 400/413 split in halves, a single file still 400/413 to
`rejected/` with the status as its reason); "Backoff is exponential with jitter, capped at about 5
min, and held in memory only"; "Once backoff is at its cap and no new file has arrived for about 15
min, the drain exits"; "it tries once immediately" on restart; "No local archive"; "`workflow
status` reports queue size, oldest file, `rejected/` count and whether a drain is running". Config:
"Re-read on every batch"; "No config: the drain makes no attempt and exits; the queue grows and
nothing is lost. `status` says so." Design 3 Ingest: request `{"facts": [...]}`, response
`{"results": [{"id","status","reason"}]}` in order; auth `Authorization: Bearer <key>` (brief 1-03).

Carried from phase 1 (absorbed here): item 3, "The service never sends `429` yet. The drain must
still honour it" — test it against a fake HTTP server.

Decisions made at refine (settled; 2-04 builds against them):

- **Queue dir**: `$WORKFLOW_QUEUE`, else `~/.local/share/workflow/queue`; create `tmp/` and
  `rejected/` inside it with mode 0700. Only `*.evt` directly in the queue dir are work.
- **Rejected layout** (phase 4's shim reads it): the file moves to `rejected/<same name>`, and its
  reasons are written to `rejected/<same name>.reason`, one line per reason, `<fact id or file
  name>: <reason>`. The `rejected/` count in `status` counts `*.evt`.
- **Sink.** The module delivers through an interface, so 2-04 can supply an in-process one:
  roughly `Send(ctx, facts []json.RawMessage) (Response, error)` with `Response{Status int;
  RetryAfter time.Duration; Results []ingest.Result}`. The HTTP sink POSTs
  `<endpoint>/v1/ingest` with the bearer key from `clientconfig`, a 30 s timeout, and parses
  `Retry-After` (seconds). The standalone drain builds its sink from a fresh `clientconfig.Load()`
  before every batch; `ErrNoConfig` makes it log once and exit 0 without touching the queue.
- **Options** (names may differ): queue dir, sink factory, `Window` (1.5 s), `Linger` (60 s),
  `BackoffMax` (5 min), `GiveUp` (15 min), `Poll` (how often the queue is listed while waiting;
  at most 500 ms standalone), an optional `Wake <-chan struct{}` that also triggers a listing, and
  `Hosted bool`. Hosted means: never exit on linger or give-up, run until the context ends, and
  retry the lock every `Poll` instead of exiting when it is held. 2-04 sets these.
- **Test-only env** for the standalone binary (documented in the package doc as test-only):
  `WORKFLOW_DRAIN_WINDOW`, `WORKFLOW_DRAIN_LINGER`, `WORKFLOW_DRAIN_BACKOFF_MAX`,
  `WORKFLOW_DRAIN_GIVEUP`, as Go duration strings.
- **Batch limits**: at most 500 files and about 8 MB of fact JSON per request; a file is never split
  across requests. Facts for a file come from one `facts.Build` call over the batch.
- **File outcome** after a 200: a file whose facts are all `accepted` or `duplicate` and that has no
  `Build` reasons is deleted; any `rejected` result or any `Build` reason moves it to `rejected/`
  with all of them. A file that yields no facts but has reasons goes straight to `rejected/`. A
  result missing for a fact is treated as a 5xx for the whole batch (retry).
- **Logging**: to stderr, one line on lock acquired (`drain: acquired lock pid=<n>`), one on exit
  with the reason, one per failed attempt with the status (never the key, never fact content).
- **`workflow drain`** runs the standalone drain; exit 0 when idle-exited, lock held by another,
  or no config. **`workflow status`** prints, one per line: `queue: <dir>`, `queued: <n>`,
  `oldest: <age in s or ->`, `rejected: <n>`, `drain: running|not running` (probe the lock with a
  non-blocking `flock(2)` and release it), `config: <path>|missing`, `endpoint: <url> reachable|
  unreachable|-` (a `GET <endpoint>/v1/health` with a 2 s timeout). Never print the key. Exit 0,
  except 1 when the endpoint is unreachable and files are queued (design 5: a failure, not idle).

## Changes

New package `internal/drain` (lock, scan, window, batching, delivery, backoff, idle exit, status
data) with a package doc comment; `main.go` dispatches `drain` and `status` (leave `mcp` as `not
implemented yet`); `cmd/workflow/drain_test.go` holds the binary-level tests below.

### Keep untouched

`serve` behaviour and `TestServeOutcome` (2-04 owns `internal/serve` and the serve tests);
`internal/facts`, `internal/clientconfig` (report gaps; one-line fixes allowed and named);
`tools/hooklog/` (2-01's).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test -race ./...` → passes.
- `go test -v -run 'Delivery|Backoff|RetryAfter|Split' ./internal/drain` against an `httptest`
  server: per-fact results drive delete versus `rejected/` (with `.reason` lines); 503 and a
  dropped connection keep files and retry with growing delay; 429 with `Retry-After: 1` waits about
  a second (carried item 3); 413 on a batch splits it, and a single file still 413 lands in
  `rejected/` with reason `413`; 401 keeps files.
- `go test -v -run 'IdleExit|Race' ./internal/drain` → files spooled while a drain is in its
  release-and-rescan step are all delivered (no file left after the last drain exits); a second
  drain started while one holds the lock exits within about 1 s.
- `go test -v -run 'Burst' ./cmd/workflow` → builds the binary into `t.TempDir()`; starts
  `workflow serve` on a free port other than 8765/8770 with temp `HOME`, `WORKFLOW_SERVE_DATA`,
  `WORKFLOW_SERVE_KEYS=t=k`, and **no** `WORKFLOW_CLIENT_CONFIG` (so it never hosts a drain once
  2-04 lands); writes a temp client config pointing at it; sets `WORKFLOW_BIN` to a wrapper script
  that logs one line per start then `exec`s the binary with stderr to a per-pid log; fires 20
  concurrent `bash tools/hooklog/spool.sh --harness claude` calls with distinct payloads in one
  conversation and `WORKFLOW_QUEUE` in the temp dir. Then: the queue empties; the ledger
  (`<data>/t/ledger.db`, read with the module's SQLite driver) holds 20 `hook_event` rows; exactly
  one drain log says it acquired the lock; the wrapper start count is reported (extra starts that
  failed to acquire are allowed; the count is reported, not asserted).
- Same file, `-run 'Write|Commit|Rejected'`: replaying the `artifact_writes.json` Claude `Write`
  fixture (with `cwd` a temp git repo holding `docs/plans/x/DESIGN.md`) through `spool.sh` yields an
  `artifact_version` row; a `commit_calls.json` fixture yields a `commit` row and `commit`-source
  versions; a DESIGN.md containing a concatenated credential leaves its queue file in `rejected/`
  with a `.reason` naming the pattern and line, and the secret appears nowhere under the serve data
  dir, in any `.reason` file or in any log (the DESIGN.md and the raw queue file itself, which holds
  the hook payload, are the only places it may remain).
- Same file, `-run 'DownUp'`: with the config pointing at a closed port and
  `WORKFLOW_DRAIN_BACKOFF_MAX=1s`, spooled files stay queued; start `serve` on that port; all are
  delivered and the queue empties.
- `-run 'Status'`: `workflow status` on the temp queue shows the counts, `drain: running` while a
  drain holds the lock, `config: missing` without a config, and never the key.

Safety: test only in `t.TempDir()` / `mktemp -d` dirs, with `WORKFLOW_QUEUE`, `HOME`,
`WORKFLOW_CLIENT_CONFIG` and `WORKFLOW_SERVE_DATA` set to temp paths and `WORKFLOW_HOOKLOG_DIR` set
to a temp dir too. Never touch `~/.local/share/workflow*`, the legacy spool
(`~/.local/share/workflow-plugin/hooklog`), `~/.config/workflow` or ports 8765/8770. Kill every
`serve` and drain you start (`t.Cleanup`); confirm with `pgrep -f '<tempdir>'` before reporting.
Never print `TYPESAFE_API_KEY` or any key.

Commit: title `[exec <execution_id>] Phase 2: workflow drain and status` (the orchestrator supplies
the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write `docs/plans/09-workflow-binary/reports/2-03-drain-status.md`
(design 1, Execution report: what was done against this brief, verifiably; departures and why;
unfinished work; known problems; nothing derivable; include the final `drain` API names 2-04 will
use) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
