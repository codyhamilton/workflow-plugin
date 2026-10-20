# Review — device-code login

Verdict: **PASS_WITH_FOLLOWUPS**

Reviewed SHA: `4c256edd53689164da282f986f24f9bc129a63a4` (post-fix). Parent of the fix is `aea73ee0033c711d5d1e7676fde272559b131ae0` (PR #160 head at review start).

Plan sufficiency: the design was enough to judge intent, place the findings, and derive the automated checks. The Phase 4 live Claude session cannot be proven from the repo; the design correctly treats it as a deployed-service check.

## Phase outcomes

- Phase 1 — device grant: **met**. `TestDeviceGrantFlow` covers code → pending → approve → one token → ingest → second poll `expired_token`. Deny, slow_down, expiry, unknown-code 429, per-IP and global caps, `Fly-Client-IP` ignored when `FLY_APP_NAME` is unset, `expires_at` passing before poll, bearer 401, foreign Origin 403, forbidden tenant 403, exchange 404, `redirect_uri` 400, and legacy `device_codes` revoke-on-load are covered in `device_test.go` and `device_limits_test.go`. Re-ran `go test -race -run TestDevice ./internal/serve/` on this SHA: pass, including a new burst test.
- Phase 2 — approval page: **met** against the mocked API contract. `/device` shows the code, gates Approve, sends one credentialed `fetch` with the four fields, Deny sends `action: "deny"`, 404 is the unknown-code error, the bare page has an entry field, and the signed-out return URL keeps `user_code`. Not re-run here (Playwright); the spec and page match the contract. No loopback navigation.
- Phase 3 — client login: **met**. `python3 -m unittest test_login test_status` in `plugins/yakka/client`: 20 tests OK. `start` / `wait` / browser open, default endpoint, pending-file mode, no token or `device_code` in output, loopback client removed, Go `login` exits 1 naming the plugin wrapper.
- Phase 4 — skill, docs, release: **partial**. Skill, OpenCode symlink-all-skills install, plugin `3.1.0`, binary `0.3.0`, marketplace wording, `yakka status` env line, and designs 03 / 05 / 07 match the code. The live `/yakka:login` session against the deployed service is not done (carried in `IMPLEMENTATION.md` until after merge and the Pages deploy).

## Intent and ledger

The implementation matches the verbatim intent: device flow for the plugin, remote sessions stay on `YAKKA_ENDPOINT` / `YAKKA_KEY`, mint-on-poll, no plaintext grant at rest, loopback grant removed. The assumption ledger is empty. The in-contract assumption of one serving machine still matches design 07 (one Fly machine). A second machine would split the in-memory grant table; that remains a named non-goal.

## Findings

### Resolved in review

- **medium** — Unknown-code limit was not atomic. `unknownBlocked` and `recordUnknown` took the grant lock separately from the lookup, so a parallel burst of `POST /v1/device/authorize` from one session could exceed 10 unknown attempts per 10 minutes. `decide` now checks the cap, looks up the code, and records a miss under one lock. A valid code is still refused while the session is limited, and a blocked attempt is not recorded. `TestDeviceAuthorizeUnknownCodeBurst` (40 parallel requests) expects exactly 10 × 404 and the rest 429. `go test -race` passed.

### Follow-up (not blocking)

- **medium** — A poll that arrives sooner than the grant interval grows that grant's interval by 5s and moves `lastPoll`, but `slow_down` does not tell the client the new interval (`device_grants.go` poll; `yakka.py` `login_wait` adds 5 only when it sees the response). One extra poller (a second `yakka login wait`) or a dropped `slow_down` response leaves the legitimate client one step behind forever, so an approval is never redeemed and `wait` exits expired. The happy path, one waiter, does not hit this. Recovery needs a contract choice (client adopts a server-supplied interval, or the server stops stacking the penalty when the client did not see it).
- **medium** — `/device` can be framed. Design 07 open issue 2 already notes the site sends no `frame-ancestors`. This page is a one-click credential approval, so a framed overlay defeats "check this matches the code in your terminal". Classic cross-site POST CSRF is handled (SameSite=Lax session cookie, allow-listed `Origin`, JSON content type, bearer rejected).
- **low** — The expiry control is `datetime-local` and parsed as local time, but the label says "Expires (UTC)" (`+page.svelte`). Same pre-existing mismatch as the profile page. A non-UTC user sets a different expiry than the label describes, or cannot enable Approve for a time that is still in the future in UTC.
- **low** — Design 03 calls `POST /v1/device/authorize` "same-origin". Production is a credentialed cross-origin `fetch` from `https://yakka.build` to `https://api.yakka.build`, allowed by the origin guard. Tightening the check to literal same-origin would break the Pages page.
- **low** — `redeemDeviceGrant` drops the grant before `Persist`. On persist failure the client gets 500 and the grant is gone, but `CreateToken` has already appended a live hash with no holder. The comment says the token is lost; it is lost to the client and still valid in memory until revoked. Accepted in `IMPLEMENTATION.md`. Revoke-on-persist-failure would match that comment.

## Residual risks

- Pending grants are in memory. A restart during login makes the user run `start` again. Intended.
- Installed 3.0.1 clients cannot log in after the server deploy. Intended. Pages still serving the old `/device` form cannot finish a login until that deploy.
- The user code is printed by `login start` and shown to the agent. Anyone who can see it can approve first and bind the CLI to their tenant. The page shows the code large; the skill does not ask the agent to confirm `tenant:` from `wait` against the tenant the user picked.
- Anonymous `POST /v1/device/code` can fill the global pending cap (1,000) from many IPs and return 503 until grants expire. The cap is the designed control.
