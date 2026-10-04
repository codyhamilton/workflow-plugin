# Execution report: 1-03 ingest, precheck and `workflow serve`

Execution 16. Brief: `briefs/1-03-ingest-serve.md`.

## Done

- `tools/workflow/internal/ingest`: fact types (package doc), per-fact validation, recursive
  precheck, `Ingest(ctx, tenant, facts)`. Order per fact: validate, precheck, row hash, `WritePending`;
  one `Append` per batch.
- `tools/workflow/internal/serve`: env config (`ParseKeys`), constant-time auth over all keys, lazy
  tenant registry, one pending worker per tenant (screen step is the `ScreenFunc` option, default
  `Promote(..., unscreened)`), `/v1/health`, `/v1/ingest`, `/v1/artifacts`.
- `tools/workflow/cmd/workflow`: `serve`, `version`; `drain|mcp|status` exit 2 "not implemented yet".
- Tests written first as the failing check: the packages did not exist, so every named test failed
  to build until the code existed. All now pass.

## Evidence (from `tools/workflow`)

- `go vet ./... && go test -count=1 -race ./...`: all six packages `ok`.
- store burst line: `writer-burst: tenants=8 facts=4800 p50=11.90148ms p99=24.473472ms db_bytes=5992448`.
- `-run 'Ingest|Precheck' ./internal/ingest`: 4 tests PASS. `-run Pending ./internal/serve`: PASS.
  `-run TestServeOutcome ./cmd/workflow`: PASS (binary built into a temp dir, temp HOME/data, free port).

## Departures and choices

- Worker enable/disable: `Options.DisableWorker` plus `Server.StartWorker()` (tests start disabled, then enable).
- Worker retries failed promotions on the next wake or poll; on tenant open its first pass handles
  leftover `pending/` files (store note: Promote is repeatable and heals a crash mid-promotion).
- `ts` absent is stored as 0; present but non-number is `invalid:`. `harness`/`event` non-string is
  `invalid:`. The brief listed neither; the store columns are NOT NULL strings/real.
- `content` is scanned first (reason without a path), other leaves in sorted-key order.
- Extra: `workflow version` subcommand (brief mentions the variables only).
- No `429` is produced; no `Retry-After` handling (not required this phase).

## Unfinished / known problems

- Resent artifact whose pending file was lost but ledger row exists is `duplicate` and not re-written (blob loss is out of scope).
- `Server.Close` assumes the HTTP server was shut down first (cmd does this).
- Free-port selection in `TestServeOutcome` has a small listen/rebind race.
- No contradiction with the cited contracts found.
