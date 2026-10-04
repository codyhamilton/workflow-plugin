---
brief_id: 237
design_id: 209
---

# Remediation 01: permanent scorer errors are retried on every poll, forever

Severity: high. Source: service-side review (`review-service.md`).
Owned paths: `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`,
and if a terminal state needs storage, `tools/workflow/internal/store/` (one new verdict or
rejection write, no schema break). Do not touch `internal/{drain,mcp,facts,clientconfig}`.

## Defect

`drainPending` (serve.go, about line 230) and `reconcile` (about line 207) back off only when the
error wraps `scorer.ErrUnreachable`. Every other screen error is logged and the hash stays pending.
The worker then waits for the next tick or wake and sends it again with no backoff and no cap.

These errors are not transient:

- `scorer/jev.go` `ask`: HTTP 4xx other than 401, 403 and 429 (`scorer: HTTP %d`), for example
  400 or 413 for content System One will not take;
- a malformed response body;
- a response with no screen answer;
- a Score or Promote failure that repeats for the same input.

## Why it matters

Each stuck hash is a paid TypeSafe call on every 3 s poll and on every ingest wake. That is about
28,800 calls a day per item, plus a stderr line each time. It never ends: the item is never
promoted or rejected, so the reads show it as pending forever and the agent gets no answer.

A probe with a stub returning HTTP 400 at a 30 ms poll made 21 calls in 600 ms.

## Fix approach

1. Keep per-hash failure state in `tenantState`: attempt count and next-try time, with exponential
   backoff from `ScreenBackoff` up to `maxBackoff`. Skip a hash whose next-try time is in the
   future.
2. After N non-unreachable failures (suggest 5), give the item a terminal state the reads can
   show. Two options:
   - a rejection at stage `screen` with reason `screen error: <short cause>`, removing the pending
     file;
   - a screens row with verdict `error`.

   Pick the one the MCP shim already renders without a client change. 4-02's report shows it
   renders `rejection at <stage>: <reason>`, so prefer the rejection.
3. In-memory state lost on restart is acceptable. A restart gets N fresh tries, which is bounded.

Leave `ErrUnreachable` handling as it is: whole-pass backoff, no attempt count.

## Done evidence

Run from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH` and `TYPESAFE_API_KEY=`.

- Fail first: a new `serve_test` case uses a screen step that always returns a plain
  (non-unreachable) error, a 10 ms poll and a 1 s run. It asserts the call count is at most N plus
  a small slack. Quote its failure before the fix.
- After the fix it passes, and the item reads as rejected (or `error`) through the same read the
  shim uses.
- `TestScreeningOutcome` and the unreachable-backoff tests pass unchanged.
- `go vet ./... && go test -race -count=1 ./...` passes.
