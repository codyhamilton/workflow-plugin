---
brief_id: 223
---

# Execution report: 4-02 MCP shim package

## Done

- New `tools/workflow/internal/mcp` (`mcp.go` protocol and tools, `feedback.go` artifact_feedback, HTTP and queue matching, `mcp_test.go`).
- Exported: `mcp.Serve(ctx, r, w, opts) error`, `mcp.Options{Version, QueueDir, Wait, StartDrain, Getwd, HTTP}`, and `facts.WritePaths(raw []byte) []string` (over the raw queue-file bytes; nil when unparseable or no write). `facts.Build` is unchanged.
- Fail first: `go test -run 'TestShim|TestWritePaths'` gave `undefined: Options`, `undefined: Serve` (mcp, build failed) and, for facts, a build failure (`WritePaths` undefined, plus 4-01's mid-flight store errors at that moment).
- After: `go vet ./...` clean; `TYPESAFE_API_KEY= go test -race -count=1 ./...` all packages ok; `TestShim` subtests 1-11 plus a list_checks/search subtest PASS; `TestWritePaths` PASS.

## Answers (from the tests)

queued:
```
state: queued
path: docs/plans/x/DESIGN.md
repo: root:<sha>
content_hash: <hash>
2 events for this file still queued, oldest 40s, draining
```
(with the stub down the line ends `remote unreachable` and adds `service unreachable at <endpoint>`)

rejected:
```
state: rejected
...
secret: aws_access_key at line 3 in docs/plans/x/DESIGN.md
Fix: rewrite the file; the new write is the repair.
```
delivered:
```
state: delivered
...
screen: pass by jev-1
clarity 0.25 (baseline p25 0.50, median 0.70, n 5) BELOW p25
scope 0.50 (baseline p25 0.50, median 0.70, n 5)
few 0.10 (baseline n=3, too few to flag)
new 0.20 (no baseline)
versions: 3
```
stale:
```
state: stale
...
current content not yet delivered (service has abababababab from 2026-01-01T00:00:00Z); normally a write still in the batch window
```
no config:
```
state: no config
...
no client config at <path>; nothing is delivered until it exists
```
not tracked:
```
state: not tracked
path: <abs>
not inside a git repository; nothing is captured for this file
```
not delivered (404 or unreachable): `state: not delivered`, then the reason; unreachable adds `service unreachable at <endpoint>`.

## Departures

- Queued with no client config: the shim does not wait or kick (nothing can drain); why reads `no config (<path>)`.
- Extra no-flag line `<check> <score> (no baseline)` for a check with no baseline entry; `baselines unavailable` when that fetch fails.
- A flagged-by-screen answer has the rewrite fix; other non-null rejection stages with no screen show `screen: awaiting screen` plus `rejection at <stage>: <reason>`.
- A rejected answer makes no service call.

## Known limits

- Commit tool calls are not matched in the queue (their paths come from git at drain time), so a file committed but not yet drained shows as not delivered or stale rather than queued.
- The default drain starter is not exercised by tests (injected fake only).
- Content hash is hex without a `sha256:` prefix, as `keys.ContentHash` returns it.
