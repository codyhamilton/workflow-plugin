# Report: phase1-grant-flow

Status: done with concerns (one brief inconsistency, below).

## Done against the brief

- `POST /v1/device/code`, `/v1/device/authorize`, `/v1/device/token` registered inside `cfg.Remote()`; `/v1/device/exchange` removed (404). All three are POST only.
- In-memory grant table (`device_grants.go`) with an injectable clock, keyed by SHA-256 of `device_code` and by normalised user code; swept at the start of every device route; no goroutine.
- Token minted by `CreateToken` at the first poll after approval, then `Persist`. The approved grant is claimed (dropped) inside the table lock in `poll`, so two concurrent polls cannot both mint.
- `Registry.ValidateGrant` added; `CreateToken` now calls the same private check, so error strings match (`invalid scope`, `expires_at must be in the future`, `forbidden tenant`).
- Removed `DeviceCodeRecord`, `CreateDeviceAuthorization`, `ExchangeDeviceCode`, `handleDeviceExchange*`, `validLoopbackRedirectURI`, `redirectWithDeviceCode`. `load()` reads `device_codes` through a private legacy type, revokes the referenced token IDs (sets `dirty`), and the field is never written back.
- `TestDeviceAuthorizationFlow` and its three helpers replaced by the tests in `device_test.go`.

## Check output

- Before: `go test ./internal/serve/ -run 'TestDevice|TestRegistryLegacy|TestValidateGrant'` failed to build (`s.grants`, `ValidateGrant` undefined).
- After: all 13 named tests pass (`TestDeviceGrantFlow`, `SiteMapping`, `UserCodeNormalisation`, `Deny`, `SlowDown`, `Expiry`, `ExpiresAtPassesBeforePoll`, `TestDeviceAuthorizeGuards`, `TestDeviceExchangeRemoved`, `TestDeviceRoutesLocalOnlyAbsent`, `TestDeviceNoPlaintextAtRest`, `TestRegistryLegacyDeviceCodes`, `TestValidateGrant`).
- `go test ./internal/serve/...` ok; `go test -race` on `TestDevice*` ok; `go vet ./internal/serve/...` clean; `go build ./...` ok (`internal/login` still builds). The grep for `ExchangeDeviceCode|CreateDeviceAuthorization|TokenPlaintext` finds only `hashTokenPlaintext`/`generateTokenPlaintext` (unrelated names).

## Departures and contradictions

- Brief contradiction: `TestDeviceGrantSlowDown` as written ("interval is then 10 s; a poll 6 s later is still slow_down, 11 s later is authorization_pending") cannot hold in one sequence under the brief's own poll rule, because the 6 s `slow_down` poll grows the interval to 15 s and the 11 s poll is then also `slow_down`. I kept the rule and tested the two cases on two grants (each after a single slow_down). The rule is unchanged.
- The authorize 400 for `redirect_uri`/`state` returns `{"error":"redirect_uri and state are not accepted"}`; the brief gave no body.
- `action` other than empty or `deny` returns 400 `invalid body`.
- `/v1/device/code` rejects a non-empty body that is not valid JSON (400); the brief only said empty or `{}`.
- `docs/plans/19-device-login/IMPLEMENTATION.md` showed as modified in the working tree before I committed; it is not mine and I left it out of the commit.

## Unfinished or deferred

- No limits (belongs to `phase1-limits`). Hook points: `handleDeviceCode` (per-IP rate, per-IP and global caps, before `grants.create`) and the `!found` branch of `handleDeviceAuthorize` (per-session unknown-code count). Client IP is the connection's remote host only, stored on `deviceGrant.clientIP`; the `Fly-Client-IP` rule is the limits unit's.
- `ValidateGrant` and `CreateToken` still return `err.Error()` strings to the client for 400s, as before.

## Known problems

- Persist-failure edge: the grant is already dropped when `Persist` fails, so the 500 `persist failed` loses the grant and the minted token (it stays in the in-memory registry and is persisted by a later `Persist`). The user must run login again.
- Approval and the later mint are separate checks: if the tenant owner changes between them the poll returns `access_denied`, as the design says.
