# Implementation: Device-code login

## Run

- Tool: Claude Code (Haiku 5.5 orchestrator)
- Session: https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk
- Start: 2026-10-21T00:38:00+10:00
- Branch: feat/device-login (from master at 6576c04)
- Invocation: `/yakka:execute plan 19`, bare call, so one phase (Phase 1) and then stop.

## Phase 1 — Device grant on the server

Status: closed, 2026-10-21 (closing commit carries `Yakka-Phase: 19-device-login:1`).

Refine verdict: READY, two units, sequential (both edit `device.go`). Briefs in `briefs/`, committed at 231d7f4.

Units:
1. `phase1-grant-flow` (no dependencies). Worker: Sonnet.
2. `phase1-limits` (depends on 1). Worker: Sonnet.

### Unit `phase1-grant-flow`

Dispatched 2026-10-21T00:42+10:00. Outcome: landed at 2732955. Worker report: `reports/phase1-grant-flow.md`.

- Built: in-memory grant table (`device_grants.go`), `ValidateGrant`, the three device routes, removal of `/v1/device/exchange`, legacy `device_codes` revoke-on-load in `registry.go`.
- Surfaces: `device.go`, `device_grants.go` (new), `device_test.go` (new), `registry.go`, `serve.go`, `serve_test.go` (old flow test removed).
- Deviations, from the worker report: authorize returns 400 for `redirect_uri`/`state`; an unknown `action` returns 400; a non-JSON body on `/v1/device/code` returns 400. The brief's `TestDeviceGrantSlowDown` sequence conflicts with its own poll rule (a poll 6 s later is itself `slow_down`), so the two cases are tested on separate grants.
- Known: if `Persist` fails after a grant is dropped, the user gets 500 and must log in again.
- Agent: sonnet worker, turns and context not reported by the harness.

### Unit `phase1-limits`

Dispatched 2026-10-21T00:44+10:00, after `phase1-grant-flow`. Outcome: landed at bf974e5. Worker report: `reports/phase1-limits.md`.

- Built: per-IP code-request rate (10/min), per-IP live-grant cap (5), global pending cap (1,000), unknown-code attempt limit (10 per session per 10 min), client-IP rule (`Fly-Client-IP` only when `FLY_APP_NAME` is set), 429 and 503 paths. In `device_limits.go` and `device_limits_test.go`.
- Surfaces: `device.go` hook points, `device_limits.go` (new), `device_limits_test.go` (new).
- Deviations, from the worker report: no departures from the contract. Authorize checks the session limit before the lookup, so a valid code also gets 429 while the session is limited. The brief's "rejected attempts count" rule was read as every attempt counting.
- Agent: sonnet worker, turns and context not reported by the harness.

### Verification (Phase 1)

- Entry point: the served device routes through the `internal/serve` handler, exercised by `go test -count=1 ./internal/serve/...` (ok) and `go test -run TestDevice -v` (17 PASS, including `TestDeviceGrantFlow`, `TestDeviceGrantDeny`, `TestDeviceExchangeRemoved`, `TestDeviceNoPlaintextAtRest`, `TestDeviceCodeRateLimit`, `TestDeviceCodeLiveCapPerIP`, `TestDeviceClientIP`).
- `go build ./...` passes, so `internal/login` still builds (it is deleted in Phase 3).
- Result: the phase outcome holds on the server side. The mint-on-poll flow, slow_down, access_denied, expired_token, the 429/503 limits, the removed `/exchange` route and the no-plaintext-at-rest check all pass in the served handler.

### artifact_feedback

Called on both reports and both briefs at closing. Result for all four: "not delivered" (the service has no version of the files and nothing is queued). Recorded here and the run continues, per the execute contract.

### Phase 1 — Carried

1. The brief's `TestDeviceGrantSlowDown` sequence conflicts with its own poll rule (a poll 6 s after a `slow_down` is itself `slow_down`). The two cases are tested on separate grants. The Phase 1 outcome still holds. Phase 3 should keep the rule and not add a combined sequence.
2. `DESIGN.md` Surfaces names `serve.go (sweep)`, but no sweep exists in `serve.go`. The Contract says there is no background loop, so expired grants are swept inside the grant table. Amend the Surfaces line in the design when Phase 4's docs are written.
3. Persist failure after a grant is dropped returns 500, and the user has to log in again. Accepted; the design's restart cost already covers it. A later refine may choose to leave the grant in place on a failed persist.
4. Authorize's session limit runs before the code lookup, so a valid code gets 429 while the session is limited. The design does not state the order. Accepted for now.
5. `device_codes` revoke-on-load and the sweep are covered by tests, not by a real `registry.json` from the deployed service. Check against production state before the Phase 3 deploy.

## Phase 2 — User-code approval page

Status: in progress. Run: Claude Code (Sonnet 5.5 orchestrator), session https://claude.ai/code/session_01DNryxkjkbPeSkJztoo7ZHk, start 2026-10-21 (bare `/yakka:execute phase 2`, so this phase only).

The phase is one unit, so one brief was authored inline from the design's contracts: `briefs/phase2-approval-page.md`, committed before dispatch. Worker: Sonnet.

### Unit `phase2-approval-page`

Dispatched after the brief commit. Outcome: pending.
