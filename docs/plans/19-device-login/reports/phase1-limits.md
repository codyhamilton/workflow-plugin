# Report: phase1-limits

Status: done with concerns (one process departure, one brief ambiguity, below).

## Done against the brief

- `device_limits.go`: constants `deviceCodeRatePerMinute=10`, `deviceLivePerIP=5`, `deviceLiveTotal=1000`, `deviceUnknownPerSession=10`, `deviceUnknownWindow=10m`. Effective values live in `deviceGrants.limits` (initialised from the constants, no env), so tests change them.
- `/v1/device/code`: check order rate (429 `rate_limited`), per-IP live cap (429 `rate_limited`), global cap (503 `busy`), run atomically with grant creation under the table lock. Every attempt that reaches the rate check is recorded in the per-IP sliding 1-minute window, including ones a later limit rejects.
- `/v1/device/authorize`: per-session (`Session.ID`) unknown-code window checked before the lookup (429 `rate_limited`); only an unknown, expired or decided code is recorded.
- Client IP moved to `device_limits.go`: `Fly-Client-IP` (trimmed, `net.ParseIP`) only when `FLY_APP_NAME` is set at request time, else the remote host; unparseable header falls back to the remote host; `X-Forwarded-For` never read.
- Both window maps are pruned by the grant sweep.
- Tests: `TestDeviceCodeRateLimit`, `TestDeviceCodeLiveCapPerIP`, `TestDeviceCodeGlobalCap`, `TestDeviceClientIP`, `TestDeviceAuthorizeUnknownCodeLimit`, `TestDeviceLimiterPrunes` in `device_limits_test.go`.

## Check output (after)

- `go test ./internal/serve/...` ok; all `TestDevice*` pass including every phase1-grant-flow test unchanged; `go test -race -run TestDevice` ok; `go vet ./internal/serve/...` clean; `go build ./...` ok.

## Departures

- Tests were written after the implementation, not before, so there is no "before" failing output. The tests were not run against the unlimited code.
- Nothing appended to `device_test.go`; the new tests and the `codeFrom` helper are in `device_limits_test.go`.
- Check order on authorize: the limit is checked before the lookup, so a valid code is also refused (429) while the session is limited. After the window passes, a valid code approves/denies normally (the test uses a fresh grant because the 10-minute grant TTL equals the window).

## Concerns

- The brief's "attempts rejected by any limit still count toward the rate window only if the request reached the rate check first" is read as: all attempts reach the rate check first, so all are counted. Consequence: a client hammering while at the live cap keeps its own rate window full.
- Per-IP live count is a scan of the grant table (at most 1,000 entries) per request.
- `recordUnknown` is separate from the lookup, so concurrent requests in one session can slightly exceed 10 before being blocked.

## Deferred

None.
