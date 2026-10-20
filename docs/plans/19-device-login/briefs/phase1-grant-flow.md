# Brief: phase1-grant-flow — In-memory device grant, three routes, exchange removed

Consumer: a Go worker on `packages/yakka/internal/serve`. Phase 1 unit 1 of 2; `phase1-limits` builds on your result, so keep the limiter hook points described below.
Owned paths: `packages/yakka/internal/serve/device.go`, `packages/yakka/internal/serve/registry.go`, `packages/yakka/internal/serve/serve.go` (device route block and the `Server` struct only), `packages/yakka/internal/serve/serve_test.go` (replace `TestDeviceAuthorizationFlow` and its three helpers), new `packages/yakka/internal/serve/device_grants.go` and `device_test.go`. Touch nothing else.
Commits: Leave changes in the working tree.
Report: write `docs/plans/19-device-login/reports/phase1-grant-flow.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: nothing.
Runs alongside: nothing (`phase1-limits` is sequential after this; it edits `device.go`).
Budget: read 6 files, about 600 lines changed (mostly new), 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/19-device-login/IMPLEMENTATION.md` (done, not done, what you learned) and report `over budget`.

## Required reading, in order

1. `docs/plans/19-device-login/DESIGN.md` — "Domain: Device grant (server)" and Phase 1 outcomes (lines 28-41, 105-111). Binding.
2. `packages/yakka/internal/serve/device.go` (161 lines) — being rewritten; keep `handleDeviceAuthorizeRoute`'s guard chain.
3. `packages/yakka/internal/serve/registry.go` lines 50-165 and 265-385 — `DeviceCodeRecord`, load/save, `CreateToken`, the old device functions.
4. `packages/yakka/internal/serve/serve.go` lines 235-248 (`Server`) and 509-512 (routes); `session.go` lines 33-38 (`Session`), 133-140 (`publicOrigin`), 218-245 (origin guard); `tokens.go` 136-142 (`rejectBearer`).
5. `packages/yakka/internal/serve/serve_test.go` lines 433-447 (`remoteTestConfig`), 473 (`doWithCookies`), 825-840 (`remoteCreateTenant`, `remoteIssueToken`), 1050-1195 (old device tests, to replace). `do` is at line 23.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Replace the loopback device grant with the RFC 8628-style grant: anonymous code request, session approval, token minted at the first poll after approval, pending grants held only in memory, so no token plaintext is ever stored.

## Contract

Cite, do not reinterpret. From DESIGN.md "Domain: Device grant (server)":

- "Routes are registered only when `cfg.Remote()`, as now (`serve.go:509-512`)."
- "**`POST /v1/device/code`**: anonymous; body empty or `{}`. 200 → `{"device_code": <43-char base64url, 32 random bytes>, "user_code": "XXXX-XXXX", "verification_uri": <site>/device, "verification_uri_complete": <site>/device?user_code=XXXX-XXXX, "expires_in": 600, "interval": 5}`. `<site>` is `https://yakka.build` when the public origin is `https://api.yakka.build`, otherwise the public origin. ... `user_code` is 8 characters from `BCDFGHJKLMNPQRSTVWXZ` with a hyphen after the fourth; input is matched case-insensitively with hyphens and spaces ignored."
- "**`POST /v1/device/authorize`**: session only, with the existing `rejectBearer` and origin guard (`device.go:142-152`). Approval validates without minting, through a new registry `ValidateGrant(tenant, scope, expiresAt, githubID, now)` that applies the same checks as `CreateToken` (`registry.go:276-288`). JSON or form body `{user_code, tenant, scope, expires_at}` approves; `{user_code, action: "deny"}` denies. 200 `{"approved": true}` or `{"denied": true}`. 404 `{"error":"unknown_code"}` for a code that is unknown, expired or already decided; 403 for a tenant the user does not own (`"forbidden tenant"`, `registry.go:286`); 400 for a bad scope or a non-future `expires_at`; ... `redirect_uri` and `state` are no longer accepted (400)."
- "**`POST /v1/device/token`**: anonymous; `{"device_code": ...}`. Pending → 400 `{"error":"authorization_pending"}`; polled sooner than `interval` → 400 `{"error":"slow_down"}` and that grant's interval grows by 5 s; denied → 400 `{"error":"access_denied"}`; unknown, expired or already redeemed → 400 `{"error":"expired_token"}`. Approved → mint with `CreateToken`, persist the registry, drop the grant, 200 `{"token", "endpoint", "tenant", "scope", "expires_at"}`. If the mint fails because the chosen `expires_at` has passed or the tenant's owner changed since approval, the grant is dropped and the response is 400 `{"error":"access_denied"}`. A grant yields at most one token."
- "**Pending grants are in memory only**, keyed by the SHA-256 of `device_code` and by `user_code`. They hold status, tenant, scope, `expires_at`, GitHub ID, expiry, client IP and last-poll time, never a token. A restart, including every deploy, drops them ... Expired grants are swept whenever a device route touches the grant table; there is no background loop."
- "**`/v1/device/exchange` is removed** (404 through the site handler's `/v1/` fallback). `DeviceCodeRecord` and `device_codes` leave `registryDoc`; a `registry.json` that still has `device_codes` loads (plain `json.Unmarshal`, `registry.go:124`), the token IDs of those unredeemed codes are revoked on load, and the field is dropped on the next persist."
- Non-goals: "RFC 8628 form encoding or OAuth client IDs. ... Changing token storage, scopes, revoke, or bearer auth. Persisting pending grants."

## Changes

Decisions you should not re-derive (all consistent with the contract; none changes it):

- New `device_grants.go`: a `deviceGrants` table owned by `Server`, guarded by its own mutex, with an injectable clock `now func() time.Time` (default `time.Now`) so tests can advance time. Maps: by `hashDeviceCode(device_code)` and by normalised user code. Normalise: uppercase, strip `-` and space. Generate `user_code` by rejection-free sampling with `crypto/rand` over the 20-letter alphabet; retry on collision with a live grant.
- Every device route calls the table's sweep (drop grants past expiry) before doing anything else. Do not add a goroutine. Note the DESIGN Surfaces line says "serve.go (routes, sweep)"; the Contract says no background loop, and the Contract wins. There is no existing sweep in serve.go.
- Expiry of a grant is `now + 600s`; `interval` starts at 5 s. Poll rule, applied in every status including approved: if `now - lastPoll < interval` return `slow_down` and add 5 s to that grant's interval; always record `lastPoll = now` (a first poll never counts as too soon). Consequence for tests: advance the fake clock by at least the current interval between polls.
- Deny: authorize with `action: "deny"` marks the grant denied. The next poll returns `access_denied` and drops the grant. Authorizing an already decided grant is 404 `unknown_code`.
- Authorize validation order: parse body (400 `invalid body`), reject `redirect_uri`/`state` present (400), find code (404), then `ValidateGrant` (400 bad scope / non-future `expires_at`, 403 `{"error":"forbidden"}` for foreign tenant, the existing response body). Keep accepting JSON or form content types via `originGuardJSONOrForm`.
- `ValidateGrant(tenant, scope, expiresAt, githubID, now) error` in `registry.go` runs the same scope, future-expiry and owner checks as `CreateToken` with the same error strings; refactor `CreateToken` to call it so the two cannot drift. It takes the read lock and mints nothing.
- Token response `endpoint` is `s.publicOrigin()`, as the old exchange returned. `expires_at` is RFC 3339 UTC.
- Limiter hook points for the next unit: keep client IP as a field on the grant, and have `handleDeviceCode` and the unknown-code branch of authorize each in one obvious place. Do not implement any limit here.
- Registry: delete `DeviceCodeRecord`, `r.deviceCodes`, `CreateDeviceAuthorization`, `ExchangeDeviceCode`, `generateDeviceCode` is kept for the new device_code (move it if you like). Keep a private legacy read type used only by `load()` to read `device_codes`; revoke each referenced `token_id` there (mark `Revoked`, set `dirty`), and never write the field back. Remove `handleDeviceExchange*`, `validLoopbackRedirectURI`, `redirectWithDeviceCode`; `loopbackHost` is used elsewhere in serve.go and session.go, leave it.
- Routes: register `/v1/device/code`, `/v1/device/authorize`, `/v1/device/token` inside the existing `if s.cfg.Remote()` block; drop the `/exchange` line. All three accept POST only (405 with `Allow: POST`, as now).
- `/v1/device/code` and `/v1/device/token` need no origin guard (anonymous, non-browser). The code route must not require a body; accept empty or `{}`.
- Persist: only `/v1/device/token` on a successful mint calls `s.registry.Persist()`; a persist failure returns 500 `persist failed` and the token is not returned (the grant is already dropped, so say so in your report if you hit that edge).

### Keep untouched

`rejectBearer`, `originGuardJSONOrForm`, `sessionOnly`, `loopbackHost`, `CreateToken`'s observable behaviour, `/v1/tokens` handlers, and every non-device test.

## Done evidence

Write the failing tests first and report their output before and after. Tests, named, in `device_test.go` unless noted (use `remoteTestConfig`, `loginRemote`, `remoteCreateTenant`, `doWithCookies`; set the fake clock through the table's `now` field):

- `TestDeviceGrantFlow`: code → token (400 `authorization_pending`) → authorize 200 `{"approved":true}` → token 200 with `token` (prefix `wk_`) and `tenant` → bearer ingest of that token succeeds (use the same ingest/summary call the old test used) → second token call 400 `expired_token`. Also asserts the `/device/code` JSON shape: 43-char `device_code`, `user_code` matching `^[BCDFGHJKLMNPQRSTVWXZ]{4}-[BCDFGHJKLMNPQRSTVWXZ]{4}$`, `verification_uri` `<origin>/device`, `expires_in` 600, `interval` 5.
- `TestDeviceGrantSiteMapping`: public origin `https://api.yakka.build` gives `https://yakka.build/device?user_code=...`.
- `TestDeviceGrantUserCodeNormalisation`: lower case, no hyphen, with spaces all authorize the same grant.
- `TestDeviceGrantDeny`: deny → next token call `access_denied`; code now unknown (404).
- `TestDeviceGrantSlowDown`: second poll inside `interval` is `slow_down` and the interval is then 10 s (a poll 6 s later is still `slow_down`, 11 s later is `authorization_pending`).
- `TestDeviceGrantExpiry`: advance clock past 600 s → token `expired_token`, authorize 404.
- `TestDeviceGrantExpiresAtPassesBeforePoll`: approve with an `expires_at` 1 min ahead, advance clock past it (within the 600 s), poll → `access_denied`, grant dropped.
- `TestDeviceAuthorizeGuards`: bearer → 401; foreign Origin → 403; disallowed content type → 403; foreign tenant → 403; bad scope → 400; past `expires_at` → 400; unknown code → 404; `redirect_uri` or `state` present → 400; a grant that failed validation is still approvable afterwards with good fields.
- `TestDeviceExchangeRemoved`: `POST /v1/device/exchange` → 404.
- `TestDeviceRoutesLocalOnlyAbsent`: in a non-remote config the three routes are not registered (assert the same status the old exchange gave there, or 404).
- `TestDeviceNoPlaintextAtRest` (`registry_test.go` or `device_test.go`): after a redeemed grant, read `registry.json`: no `device_codes` key, and the token plaintext does not appear in the file.
- `TestRegistryLegacyDeviceCodes`: write a `registry.json` with a `device_codes` array referencing a live token ID; `OpenRegistry` succeeds, `resolveBearer` for that token fails, and after `Persist` the file has no `device_codes`.
- `TestValidateGrant`: scope, expiry, owner errors identical to `CreateToken`'s strings.

Then:

- `cd packages/yakka && go test ./internal/serve/...` → passes, including the names above (`go test ./internal/serve/ -run 'TestDevice|TestRegistryLegacy|TestValidateGrant' -v`).
- `cd packages/yakka && go vet ./internal/serve/...` → clean; `grep -rn "ExchangeDeviceCode\|CreateDeviceAuthorization\|TokenPlaintext" packages/yakka/internal/serve` → no hits outside tests of removal.
- `internal/login` still builds (`go build ./...` from `packages/yakka`); it is deleted in Phase 3, not by you.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
