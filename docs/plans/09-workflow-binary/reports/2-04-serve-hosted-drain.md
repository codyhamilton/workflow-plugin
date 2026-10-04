---
brief_id: 219
design_id: 209
---

# Execution report: 2-04 `serve` hosts the drain, and the phase 2 outcome test

## Done

- `internal/serve/host.go`: `Server.Host(ctx, HostOptions{Bound, Queue, Poll, Log})`. Each tick it loads the client
  config; it hosts when the endpoint's port equals the bound port and its host is the bound host (or both are
  loopback) and the key maps to a tenant; it runs `drain.Run` with `Hosted: true`, an in-process sink
  (`ingest.Ingest` on the registry tenant, wakes the pending worker, 200 with results or 500) and a `Wake` channel.
  A tick that no longer matches (or a changed tenant) stops the drain and releases the lock. Config problems log once
  per change. The `serve.go` handlers are untouched.
- `watch_linux.go`: inotify (`IN_MOVED_TO|IN_CREATE`) via `golang.org/x/sys/unix`, 200 ms poll(2) so it stops with ctx,
  feeds `Wake`; the drain's `Poll` is the fallback. `watch_other.go` is a no-op: kqueue is deferred to phase 5.
- `main.go`: starts `Host` after binding; shutdown order is hosted drain, HTTP shutdown, tenants. The
  `serve: listening on <addr>` line already existed; `WORKFLOW_SERVE_ADDR` accepts port 0.
- `go.mod`: `golang.org/x/sys` promoted to direct.
- Carried item 4: `TestServeOutcome` now starts on `127.0.0.1:0` and reads the address from the log line.
- `capture_test.go`: `TestCaptureOutcome` (7 subtests, one temp root).

## Evidence

There was no failing check to run first (new behavior; the first `TestCaptureOutcome` run failed at `write`, see
below). After, from `tools/workflow`: `go vet ./... && go test -race -count=1 ./...` passes (2-03 tests unchanged).
`~/.local/share/workflow` and `~/.config/workflow` do not exist; no `serve`/`drain` process survives.

```
outcome hosted-burst           PASS
outcome write                  PASS
outcome commit-and-join        PASS
outcome secret                 PASS
outcome endpoint-elsewhere     PASS
outcome kill-and-recover       PASS
outcome status                 PASS
--- PASS: TestCaptureOutcome (19.43s)
```

Join query (rows from `ledger.db`; `facts` has no artifact path in commit rows, so the path comes from `raw`):

```sql
SELECT a.path, json_extract(CAST(c.raw AS TEXT), '$.sha'), c.conversation_id
FROM facts a JOIN facts c ON c.type = 'commit' AND c.repo_id = a.repo_id
 AND EXISTS (SELECT 1 FROM json_each(CAST(c.raw AS TEXT), '$.paths') j WHERE j.value = a.path)
WHERE a.type = 'artifact_version' AND a.path = 'docs/plans/x/DESIGN.md'
```
Row: `docs/plans/x/DESIGN.md | 23e1d6f950e5ad75a4da7a1eb9481629e873eb9c | conv-commit` (the SHA is the repo's real HEAD,
asserted in the test; it varies per run).

## Departures

- A wildcard bind (`0.0.0.0`, `::`) counts as loopback for the host match (the brief names only loopback).
- Test-only `WORKFLOW_SERVE_POLL` (default 3 s) sets the hosting tick and the hosted drain's `Poll`; tests use 500 ms.
  The hosted drain does not read the `WORKFLOW_DRAIN_*` env (window stays 1.5 s); only standalone does.
- `main_test.go` also gets `WORKFLOW_QUEUE` and `WORKFLOW_CLIENT_CONFIG` temp values so `TestServeOutcome` can never
  touch the real queue.
- The test repo needs a root commit before the first hook (an empty repo has no repo identity, so the `Write`
  produced no `artifact_version`); the test makes one.

## Unfinished / known problems

- kqueue (macOS) deferred; darwin polls.
- A hosted drain's standalone-held-lock takeover waits up to `Poll` after the standalone exits.
