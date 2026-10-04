---
brief_id: 218
design_id: 209
---

# Execution report: 2-03 `workflow drain` and `workflow status`

## Done

- `tools/workflow/internal/drain` (package doc states layout and the test-only env): lock, scan, window,
  batching (500 files / 8 MB, a file never split), delivery table, backoff, idle exit, status data.
- `main.go` dispatches `drain` (`drain.RunStandalone`) and `status` (`drain.RunStatus`); `mcp` unchanged.
- Final API for 2-04: `drain.Run(ctx, drain.Options) (reason string, err error)`;
  `Options{Dir, Sink SinkFunc, Window, Linger, BackoffMax, BackoffMin, GiveUp, Poll, LockWait, Wake <-chan struct{}, Hosted bool, Log io.Writer}`;
  `Sink interface{ Send(ctx, []json.RawMessage) (Response, error) }`, `Response{Status, RetryAfter, Results []ingest.Result}`,
  `SinkFunc func() (Sink, error)` (may return `clientconfig.ErrNoConfig`); `HTTPSink{Endpoint, Key, Client}`, `ConfigSink`;
  `QueueDir()`, `EnsureDirs`, `Running(dir)`, `QueueStatus(dir)`; reasons `ReasonIdle|LockHeld|NoConfig|GaveUp|Stopped`.
  Hosted: lock retried every `Poll`, never exits on linger or give-up; `Wake` triggers a listing.
- Tests: `internal/drain/drain_test.go` (httptest fake: results to delete/rejected+.reason, 503, dropped connection,
  401, 429 Retry-After 1 s, 413 split 1+2+4 calls, single 413/400 reject, give-up, idle-exit race via an in-package
  release hook, second drain exits, no config, hosted); `cmd/workflow/drain_test.go` (Burst, Write, Commit,
  Rejected secret, DownUp, Status).

## Evidence

No failing check existed (new package). After, from `tools/workflow`: `go vet ./... && go test -race ./...` passes.
Burst: 20 spools gave 14 wrapper starts, 1 log that acquired the lock, 20 `hook_event` rows, queue empty. The
secret is absent from the serve data, `.reason` files and all drain logs. No leftover processes (`pgrep`).

## Departures and contradictions

- `cmd/workflow/main_test.go` is outside my owned paths: I removed three lines of `TestServeOutcome` that
  asserted `workflow drain` exits non-zero. They contradict the brief (drain with no config exits 0) and ran the
  drain with the real `HOME`, so it would have created the real queue dir. Nothing else in that test changed.
- Other 4xx and unexpected statuses (404, 3xx, a 200 with unreadable JSON, or results count/ids mismatch) are
  retried like 5xx; the table does not cover them and nothing is lost.
- The batch window also applies at drain start (not only after an empty queue), so a freshly kicked drain batches
  the burst; "tries once immediately" on restart is therefore after one window.
- Standalone checks config once before taking the lock (no config exits at once, queue untouched) and again before
  every batch. Backoff starts at 500 ms (`BackoffMin`), doubles with 50-100% jitter.
- Idle-exit race is tested with an unexported `afterRelease` hook, not real concurrent spools (the Burst test
  covers those).

## Unfinished / known problems

- Final-batch results are applied per request: a retry after a split can resend facts already accepted (dedupes).
- `status` reports `reachable` only for a 2xx health reply.
