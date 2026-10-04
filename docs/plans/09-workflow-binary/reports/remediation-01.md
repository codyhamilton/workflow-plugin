# Remediation 01: bound retries of permanent scorer errors

Execution 33. Brief: `briefs/remediation-01.md`.

## Done
- Added `TestPermanentScreenErrorIsBounded` (`internal/serve/serve_test.go`): a screen step that always
  returns a plain error, 10 ms poll, 1 s run. Before the fix: `screen step called 101 times in 1s, want at most 7`.
  After: passes. It also checks the read (`/v1/artifacts`) shows `"stage":"screen"` with a `screen error` reason
  and that `pending/` is empty.
- `serve.go`: `tenantState.fails` holds per-hash attempts and next-try time. Non-unreachable failures back off
  exponentially from `ScreenBackoff` to `maxBackoff`. After `maxScreenAttempts` (5) the hash is dropped with a
  rejection at stage `screen`, pattern `screen_error`, reason `screen error: <cause, 120 runes max>`
  (`DropPending`, no store change). The read already renders it.
- `ErrUnreachable` handling is unchanged. `go vet ./... && go test -race -count=1 ./...` passes.

## Departures
- `reconcile` has no per-hash state. It runs once per worker start and already makes one try per blob, so it is
  bounded; I left it alone.

## Known problems
- State is in memory: a restart gives each stuck hash 5 fresh tries (accepted by the brief).
- A rejected hash whose content is re-ingested is screened again from zero attempts.
