# Brief: phase1-limits — Rate limits and client-IP rule on the device routes

Consumer: a Go worker on `packages/yakka/internal/serve`. Phase 1 unit 2 of 2.
Owned paths: new `packages/yakka/internal/serve/device_limits.go` and `device_limits_test.go`; `packages/yakka/internal/serve/device.go` and `packages/yakka/internal/serve/device_grants.go` (hook points only); `packages/yakka/internal/serve/device_test.go` (append). Touch nothing else.
Commits: Leave changes in the working tree.
Report: write `docs/plans/19-device-login/reports/phase1-limits.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `phase1-grant-flow` (its report and code must exist; read the report first).
Runs alongside: nothing.
Budget: read 5 files, about 250 lines changed, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/19-device-login/IMPLEMENTATION.md` and report `over budget`.

## Required reading, in order

1. `docs/plans/19-device-login/reports/phase1-grant-flow.md`, then `device_grants.go` and `device.go` as that unit left them.
2. `docs/plans/19-device-login/DESIGN.md` lines 35-36, 40 and the Phase 1 outcomes at 108.
3. `packages/yakka/internal/serve/session.go` lines 33-38 (`Session.ID` is the per-session key).

Read ranges and grep; do not re-read a file already in context, and truncate long tool output.

## Goal

Make the anonymous `/v1/device/code` route unfloodable and the user-code space unguessable through approval attempts, with the client-IP rule the contract names.

## Contract

Cite, do not reinterpret:

- "429 `{"error":"rate_limited"}` when the per-IP request rate or the per-IP live-grant cap is hit; 503 `{"error":"busy"}` when the global pending cap is hit." (`/v1/device/code`)
- "429 after too many unknown-code attempts in one session." (`/v1/device/authorize`)
- "Limits, all *judgement* and named constants: 10 code requests per minute per client IP, 5 live grants per client IP, 1,000 live grants in total, 10 unknown-code attempts per session per 10 minutes. The client IP is `Fly-Client-IP` only when `FLY_APP_NAME` is set, else the connection's remote address."
- Phase 1 outcome: "the eleventh `/v1/device/code` from one IP within a minute returns 429, and so does the sixth while five of that IP's grants are live; a `Fly-Client-IP` header is ignored when `FLY_APP_NAME` is unset; ... an unknown `user_code` returns 404 and the eleventh in a session returns 429".

## Changes

- Named constants in `device_limits.go`: `deviceCodeRatePerMinute = 10`, `deviceLivePerIP = 5`, `deviceLiveTotal = 1000`, `deviceUnknownPerSession = 10`, `deviceUnknownWindow = 10 * time.Minute`. Put the effective values in fields on the grant table (initialised from the constants) so tests can lower or raise them; do not read them from env.
- Client IP: parse `r.RemoteAddr` with `net.SplitHostPort`; if `os.Getenv("FLY_APP_NAME") != ""` use the trimmed `Fly-Client-IP` header when it parses with `net.ParseIP`, else fall back to the remote address. Read the env at request time so `t.Setenv` works. Never trust `X-Forwarded-For`.
- Rate: sliding window of timestamps per IP over 1 minute using the table's injectable clock; prune entries whenever the table sweeps so the map cannot grow without bound. Attempts rejected by any limit still count toward the rate window only if the request reached the rate check first. Check order on `/device/code`: rate (429), per-IP live cap (429), global cap (503). Only an issued grant adds to the live counts.
- Unknown-code attempts: per `Session.ID`, a window of timestamps; check the count before the lookup so the eleventh unknown attempt gets 429 and the first ten get 404. A known code does not count. Prune with the sweep.
- Keep response bodies exactly as quoted. No new routes, no persistence.

### Keep untouched

Behaviour of all routes when under the limits; `phase1-grant-flow` tests must still pass unchanged.

## Done evidence

Write the failing tests first and report output before and after:

- `TestDeviceCodeRateLimit`: with the live cap raised via the table field, ten requests from one remote address return 200 and the eleventh 429 `rate_limited`; after advancing the clock past 60 s the next returns 200; a different remote address is unaffected.
- `TestDeviceCodeLiveCapPerIP`: with defaults, five requests 200 and the sixth 429 `rate_limited`; after one grant is denied-and-polled (dropped) or expires, a further request succeeds.
- `TestDeviceCodeGlobalCap`: with the total cap lowered to 3 and per-IP cap raised, the fourth request from a different IP returns 503 `busy`.
- `TestDeviceClientIP`: with `FLY_APP_NAME` unset, a forged `Fly-Client-IP` does not change the bucket (ten requests with ten different header values still hit 429 on the eleventh); with `t.Setenv("FLY_APP_NAME","x")`, different `Fly-Client-IP` values get separate buckets; an unparseable header falls back to the remote address.
- `TestDeviceAuthorizeUnknownCodeLimit`: ten unknown-code authorizes return 404 and the eleventh 429 in one session; a second session is unaffected; after advancing the clock past 10 minutes the first session gets 404 again; a valid code still approves for the limited session only after the window (assert whichever your check order gives and state it in the report).
- `TestDeviceLimiterPrunes`: after the window passes and a sweep runs, the per-IP and per-session maps are empty.
- `cd packages/yakka && go test ./internal/serve/...` → passes, including every test named here and in `phase1-grant-flow` (`-run 'TestDevice' -v`).
- `cd packages/yakka && go vet ./internal/serve/...` → clean.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
