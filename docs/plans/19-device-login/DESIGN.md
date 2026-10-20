# Device-code login

## Intent

User request, verbatim:

> Well for remote sessions we need to set env var for the api key, so they won't use device flow. but regardless for the skill it definitely seems like device flow will be better

> I think design the device flow

Context from the same conversation, verbatim: "Event delivery is going to local right now - how do we make it go to the remote? how does a user do this?" and "So it requires having the binary, despite us writing the python drain to avoid needing the binary".

## Problem

Scope: how a user of the plugin gets a remote credential into `client.toml` from inside an agent session. Moving existing history to the remote is plan 18 (`yakka sync`). Remote sessions such as claude.ai/code, SSH and containers keep setting `YAKKA_ENDPOINT` and `YAKKA_KEY`; this design does not change that path.

1. **P1, login is a loopback redirect.** `yakka login` (`run_login`, `plugins/yakka/client/yakka.py:2655`) binds a callback server on `127.0.0.1`, opens a browser, and blocks for up to 600 s until the browser is redirected back to it. The server only accepts loopback `redirect_uri` values (`validLoopbackRedirectURI`, `internal/serve/device.go:11`). An agent can only drive this as a background process, it never prints the URL, and the browser must be on the same machine. Closed by Phases 1–3.
2. **P2, no default endpoint.** With no flag and no `client.toml`, login fails with "no collector endpoint" (`resolve_endpoint`, `yakka.py:2526`). A first-time user has to know `https://api.yakka.build`. Closed by Phase 3.
3. **P3, nothing tells the user how to log in.** Design 05 says "`yakka login`" without saying where `yakka` is. The plugin's wrapper is on PATH in Claude Code's Bash tool but not in a plain terminal, and the cache path changes with every version. No skill exists for it. Closed by Phase 4.
4. **P4, the current grant keeps a plaintext token at rest.** `DeviceCodeRecord.TokenPlaintext` (`internal/serve/registry.go:69-76`) holds the minted token in `registry.json` until it is exchanged, and codes that are never exchanged live until the token's own `expires_at` (`registry.go:339`). This is one clause of open issue 18 in design 07. The tokens behind those unredeemed codes are live in `token_hashes` with no holder. Closed by Phase 1.
5. **P5, `yakka status` cannot tell a login from an override.** It prints `config: <client.toml path> (remote mode)` even when `YAKKA_ENDPOINT`/`YAKKA_KEY` come from the environment (`run_status`, `yakka.py:2794-2798`), so neither a user nor a skill can confirm which credential the drain will use. Closed by Phase 4.
6. **P6, two login implementations.** The Go binary's `internal/login` duplicates the Python client and is not reached by the plugin (`plugins/yakka/bin/yakka:23` sends `login` to Python). Any change to the grant has to be made twice, and plan 18 builds on the Go copy. Closed by Phase 3; plan 18's revision is named in Open Questions.

## Solution Shape

The server offers a device-code grant modelled on RFC 8628. The CLI asks for a code anonymously, shows the user a URL and a short user code, and polls. The user approves the code on the Pages `/device` page while signed in, choosing tenant, scope and expiry as today. The token is minted at the first poll after approval and returned once, so it is never stored in plaintext. The loopback grant is removed from the server, the Python client and the Go binary. The plugin gains a `login` skill that runs `yakka login start`, relays the URL and code, runs `yakka login wait` in the background, and confirms with `yakka status`.

### Domain: Device grant (server)

- Owns: pending device grants, the user-code lookup, minting on poll, rate limits on the three device routes. `internal/serve/device.go`, `internal/serve/registry.go`, route wiring in `internal/serve/serve.go`.
- Contract:
  - Routes are registered only when `cfg.Remote()`, as now (`serve.go:509-512`).
  - **`POST /v1/device/code`**: anonymous; body empty or `{}`. 200 →
    `{"device_code": <43-char base64url, 32 random bytes>, "user_code": "XXXX-XXXX", "verification_uri": <site>/device, "verification_uri_complete": <site>/device?user_code=XXXX-XXXX, "expires_in": 600, "interval": 5}`.
    `<site>` is `https://yakka.build` when the public origin is `https://api.yakka.build`, otherwise the public origin. This mapping moves from the client (`device_page_url`) to the server. `user_code` is 8 characters from `BCDFGHJKLMNPQRSTVWXZ` with a hyphen after the fourth; input is matched case-insensitively with hyphens and spaces ignored. 429 `{"error":"rate_limited"}` when the per-IP request rate or the per-IP live-grant cap is hit; 503 `{"error":"busy"}` when the global pending cap is hit.
  - **`POST /v1/device/authorize`**: session only, with the existing `rejectBearer` and origin guard (`device.go:142-152`). Approval validates without minting, through a new registry `ValidateGrant(tenant, scope, expiresAt, githubID, now)` that applies the same checks as `CreateToken` (`registry.go:276-288`). JSON or form body `{user_code, tenant, scope, expires_at}` approves; `{user_code, action: "deny"}` denies. 200 `{"approved": true}` or `{"denied": true}`. 404 `{"error":"unknown_code"}` for a code that is unknown, expired or already decided; 403 for a tenant the user does not own (`"forbidden tenant"`, `registry.go:286`); 400 for a bad scope or a non-future `expires_at`; 429 after too many unknown-code attempts in one session. `redirect_uri` and `state` are no longer accepted (400).
  - **`POST /v1/device/token`**: anonymous; `{"device_code": ...}`. Pending → 400 `{"error":"authorization_pending"}`; polled sooner than `interval` → 400 `{"error":"slow_down"}` and that grant's interval grows by 5 s; denied → 400 `{"error":"access_denied"}`; unknown, expired or already redeemed → 400 `{"error":"expired_token"}`. Approved → mint with `CreateToken`, persist the registry, drop the grant, 200 `{"token", "endpoint", "tenant", "scope", "expires_at"}`. If the mint fails because the chosen `expires_at` has passed or the tenant's owner changed since approval, the grant is dropped and the response is 400 `{"error":"access_denied"}`. A grant yields at most one token.
  - **Pending grants are in memory only**, keyed by the SHA-256 of `device_code` and by `user_code`. They hold status, tenant, scope, `expires_at`, GitHub ID, expiry, client IP and last-poll time, never a token. A restart, including every deploy, drops them and the user runs login again. This assumes one serving machine, which `fly.toml` runs today; a second machine would need shared grant state. Expired grants are swept whenever a device route touches the grant table; there is no background loop.
  - **`/v1/device/exchange` is removed** (404 through the site handler's `/v1/` fallback). `DeviceCodeRecord` and `device_codes` leave `registryDoc`; a `registry.json` that still has `device_codes` loads (plain `json.Unmarshal`, `registry.go:124`), the token IDs of those unredeemed codes are revoked on load, and the field is dropped on the next persist.
  - Limits, all *judgement* and named constants: 10 code requests per minute per client IP, 5 live grants per client IP, 1,000 live grants in total, 10 unknown-code attempts per session per 10 minutes. The client IP is `Fly-Client-IP` only when `FLY_APP_NAME` is set, else the connection's remote address.
- Non-goals: RFC 8628 form encoding or OAuth client IDs. Tokens with a server-side default or maximum expiry. Changing token storage, scopes, revoke, or bearer auth. Persisting pending grants.

### Domain: Device page (Pages)

- Owns: `packages/yakka-analytics/src/routes/device/+page.svelte` and its helpers in `src/lib/api.ts`.
- Contract: `/device?user_code=X` prefills the code; `/device` alone shows an entry field. Signed out, it shows the existing GitHub sign-in link returning to the same URL. Signed in, it shows the code in large type with "Check this matches the code in your terminal", and the existing tenant, scope and expiry choices (create-tenant when the user has none). Approve and Deny call `/v1/device/authorize` with `fetch` and credentials, and the page shows "Approved — return to your terminal", "Denied", or the error. It no longer reads `state` or `redirect_uri` or posts a navigating form.
- Non-goals: listing or revoking tokens (the existing settings pages), showing which machine asked.

### Domain: Login client (Python)

- Owns: the login section of `plugins/yakka/client/yakka.py`, its tests in `plugins/yakka/client/test_login.py`, and the wrapper's `login` dispatch in `plugins/yakka/bin/yakka`.
- Contract:
  - Endpoint resolution: `--endpoint` flag, else the `endpoint` in `client.toml`, else `https://api.yakka.build`.
  - **`yakka login start [--endpoint URL]`** calls `/v1/device/code`, writes the pending file, prints to stdout exactly:
    ```
    url: <verification_uri_complete>
    code: <user_code>
    expires: <RFC 3339 UTC>
    ```
    and exits 0 without blocking or opening a browser. Exit 1 with one stderr line on any failure; a 404 names "this endpoint has no device login".
  - **Pending file**: `<client config path>.pending` (so `YAKKA_CLIENT_CONFIG` moves it too), mode 0600, JSON `{endpoint, device_code, user_code, interval, expires_at}`. A new `start` replaces it.
  - **`yakka login wait`** reads the pending file and polls `/v1/device/token` at `interval`, honouring `slow_down`, until success or expiry. On success it writes `client.toml` with `write_client_config` (endpoint from the response), deletes the pending file, prints `wrote <path>` and `tenant: <tenant>` to stderr, and exits 0. Denied, expired, or no pending file → exit 1 with one stderr line, and the pending file is deleted except when missing. Transient network errors are retried until expiry.
  - **`yakka login`** runs start, prints the same three lines, opens `verification_uri_complete` best-effort (honouring `YAKKA_LOGIN_BROWSER`; a failure to open is not an error), then runs wait.
  - Neither command prints the token or `device_code`.
- Non-goals: keychain storage, multiple named profiles, plan 18's `sync.toml`.

### Domain: Login skill (plugin)

- Owns: `plugins/yakka/skills/login/SKILL.md`, shared by every harness through the one skills directory.
- Contract: frontmatter `name: login` and a `description` like the other six skills. The skill runs `yakka login start` (with `--endpoint` only if the user names one), gives the user the URL and code, runs `yakka login wait` in the background or as a long-running command, and on exit runs `yakka status` and reports its `config:` and `endpoint:` lines. It never reads, prints or edits `client.toml` or the pending file. For a remote or headless session it tells the user to set `YAKKA_ENDPOINT` and `YAKKA_KEY` instead.
- `yakka status` names where the configuration came from: `config: env (remote mode)` when `YAKKA_ENDPOINT`/`YAKKA_KEY` are set, so the skill does not report a `client.toml` login that the environment is overriding. The skill warns when it sees `env`.
- `login` is a shipped skill, not one of the six "cloud-safe core" skills: it is interactive by nature. `CORE_SKILLS` in `tools/driver/check_skills.py` and the "cloud-safe core" wording stay as they are.
- Non-goals: creating tenants, choosing scope or expiry for the user, migrating history.

## Architectural Implications

- **Installed 3.0.1 clients can no longer log in** once the server deploys, because their loopback grant is gone. Their existing tokens keep working. They log in again after updating the plugin. The user chose this over keeping the old route.
- **Deploy order:** server (Fly), then Pages (Cloudflare), then the plugin release. The two deploys cannot be atomic, but each mismatched pairing only fails logins that the server change has already broken, so nothing new breaks between steps. Until the plugin release, no plugin version can log in.
- **The Go binary loses `login`.** `yakka login` under `YAKKA_BIN` exits 1 and names the plugin wrapper. `internal/login` and its tests are deleted.
- **Stable docs to update:** design 03 (API table lacks the device routes; its "SHA-256 only" claim becomes true; the `yakka.py login` row), design 05 (`yakka login` paragraph, default endpoint, where the wrapper is, the skill), design 07 (`/device` page; remove the plaintext-device-code clause from open issue 18, which keeps its other items).
- **Plugin version:** adding a skill is a plugin change, so `plugins/yakka/bin/VERSION` and the three `plugin.json` files bump together (design 05 :107). The skill lists in those descriptions, both marketplace descriptions, and the hardcoded skill lists in `install.sh` (the OpenCode symlinks) gain `login`.
- **Plan 18 must be revised before either plan is built.** Plan 18 puts its sync login in `internal/login` and `internal/clientconfig` (Go), which this plan deletes. Its `yakka login --sync` moves to the Python client as `start`/`wait` writing `sync.toml`. Its tenant check stays on its own bearer introspection route; this plan's token response does not replace it.

## Decisions

- Loopback login is removed from both server and client, accepting that 3.0.1 clients cannot log in until they update (user, Turn 2).
- Tenant, scope and expiry are chosen on the page at approval, not requested by the CLI (user, Turn 2).
- The skill ships in every harness (user, Turn 2).
- The Go binary's `login` is removed rather than ported (user, Turn 3).
- Remote sessions keep the env-var path; device flow is not required there (user, Intent).

## Assumption Ledger

None — see PROVENANCE.md.

## Open Questions

- The rate-limit numbers and the 600 s / 5 s grant timings are *judgement*. They block nothing; `refine` may adjust them, and the outcomes below do not depend on their values.
- Plan 18's login and sync-credential sections need revising to the Python `start`/`wait` client (see Architectural Implications). This blocks building plan 18, not this plan.

## Phases

Each outcome carries **Guards** (the failure it rules out) and **Basis** (the Problem part, decision or file it comes from). Numbers marked *judgement* are advisory.

### Phase 1 — Device grant on the server

- Outcome: in `internal/serve`, a Go test drives `POST /v1/device/code` → `POST /v1/device/token` (400 `authorization_pending`) → session `POST /v1/device/authorize {user_code, tenant, scope, expires_at}` (200) → `POST /v1/device/token` (200 with `token`, `tenant`) → the token ingests with a bearer → a second `token` call returns `expired_token`. Guards: a grant that never yields a token, or yields two. Basis: P1, the Device grant contract.
- Outcome: tests show that a deny returns `access_denied`; polling inside `interval` returns `slow_down`; an expired grant returns `expired_token`; an unknown `user_code` returns 404 and the eleventh in a session returns 429; the eleventh `/v1/device/code` from one IP within a minute returns 429, and so does the sixth while five of that IP's grants are live; a `Fly-Client-IP` header is ignored when `FLY_APP_NAME` is unset; a grant whose chosen `expires_at` passes between approval and poll returns `access_denied`; authorize with a bearer is 401 and with a foreign Origin is 403; authorize for a tenant the user does not own is 403. Guards: an anonymous route that can be flooded, a guessable code, CSRF on approval. Basis: Device grant contract; `device.go:142-152`.
- Outcome: `POST /v1/device/exchange` returns 404, and authorize with `redirect_uri` returns 400. Guards: the loopback grant surviving beside the new one. Basis: Decision 1.
- Outcome: after an approved grant is redeemed, `registry.json` contains no `device_codes` field and no token plaintext; a `registry.json` with a `device_codes` array loads without error and the tokens those codes reference are revoked. Guards: plaintext tokens at rest; a failed start after deploy. Basis: P4; `registry.go:69-86`.
- Surfaces: `internal/serve/device.go`, `internal/serve/registry.go`, `internal/serve/serve.go` (routes, sweep), `internal/serve/serve_test.go` (`TestDeviceAuthorizationFlow` replaced), a new limiter file in `internal/serve`.
- Approach: known
- Depends on: nothing

### Phase 2 — User-code approval page

- Outcome: in `packages/yakka-analytics/tests/e2e/device.spec.ts`, against a mocked API: `/device?user_code=WDJB-MJHT` shows the code; Approve stays disabled until tenant, scope and expiry are set; Approve sends one `fetch` to `/v1/device/authorize` with credentials and the four fields and shows "Approved"; Deny sends `action: "deny"` and shows "Denied"; a 404 shows the unknown-code error; `/device` with no parameter shows the entry field. Guards: a page that still navigates to a loopback URL, or approves without the user seeing the code. Basis: P1; Device page contract.
- Outcome: signed out, `/device?user_code=X` shows the sign-in link and its return URL keeps `user_code`. Guards: losing the code across sign-in. Basis: Device page contract.
- Surfaces: `packages/yakka-analytics/src/routes/device/+page.svelte`, `packages/yakka-analytics/src/lib/api.ts` (`deviceAuthorizeAction`, `isValidLoopbackRedirectUri` removed), `tests/e2e/device.spec.ts`.
- Approach: known
- Depends on: Phase 1 (the contract; the e2e test mocks it)

### Phase 3 — Two-step client login

- Outcome: in `plugins/yakka/client/test_login.py`, against a fake server: `login start` prints the three lines, writes a 0600 pending file and exits 0 at once; `login wait` gets `authorization_pending`, then `slow_down` (and waits longer), then 200, writes `client.toml` at 0600 with the response endpoint, deletes the pending file and exits 0; `access_denied` and `expired_token` exit 1 and delete the pending file; `wait` with no pending file exits 1. Neither command's output contains the token or `device_code`. Guards: a command an agent cannot drive without blocking; a secret in a transcript. Basis: P1; Login client contract.
- Outcome: with no flag and no config, `login start` requests `https://api.yakka.build/v1/device/code`; with `client.toml` naming an endpoint, it uses that. Guards: the first-login failure. Basis: P2.
- Outcome: `yakka login` with `YAKKA_LOGIN_BROWSER` pointing at a recorder prints the three lines, opens `verification_uri_complete`, and completes as `wait` does; with the opener failing it still completes. Guards: a terminal user losing the browser convenience. Basis: Login client contract.
- Outcome: the loopback code (`device_page_url`, `_login_exchange`, the callback server) is gone from `yakka.py`; `packages/yakka/internal/login` is deleted and `yakka login` in the Go binary exits 1 naming the plugin wrapper (`cmd/yakka/login_test.go`). Guards: two login implementations drifting. Basis: P6; Decisions 1 and 4.
- Surfaces: `plugins/yakka/client/yakka.py`, `plugins/yakka/client/test_login.py`, `plugins/yakka/bin/yakka` (usage string), `tools/release/test_release.py` (pinned usage), `packages/yakka/cmd/yakka/main.go`, `packages/yakka/cmd/yakka/login_test.go`, `packages/yakka/internal/login/` (deleted).
- Approach: known
- Depends on: Phase 1

### Phase 4 — Login skill, docs and release

- Outcome: `plugins/yakka/skills/login/SKILL.md` exists with `name: login`; after `install.sh` for OpenCode, `~/.config/opencode/skills/login` links to it; the three `plugin.json` files and `bin/VERSION` carry the same bumped version, and the plugin and both marketplace descriptions name `login` without listing it among the cloud-safe core. Guards: a skill missing from a harness. Basis: P3; Decision 3; design 05 :107.
- Outcome: with `YAKKA_ENDPOINT` and `YAKKA_KEY` set, `yakka status` prints `config: env (remote mode)` (`plugins/yakka/client/test_status.py` or the existing status test). Guards: the skill confirming a login the environment overrides. Basis: P5; Login skill contract.
- Outcome: in a Claude Code session against the deployed service, `/yakka:login` shows a URL and code; approving on yakka.build makes the session report `config: …/client.toml (remote mode)` and `endpoint: https://api.yakka.build reachable`; the transcript contains no `wk_` token. Guards: a skill that works in tests and not for a user. Basis: P1, P3.
- Outcome: design 03 lists `/v1/device/code`, `/v1/device/authorize` and `/v1/device/token` with their auth, and its statement that the registry stores SHA-256 only is true; design 05 describes `start`/`wait`, the default endpoint, the wrapper's location and the skill; design 07's `/device` text matches the page and open issue 18 no longer mentions plaintext device codes. Guards: stable docs describing a removed flow. Basis: Architectural Implications.
- Surfaces: `plugins/yakka/skills/login/SKILL.md` (new), `plugins/yakka/client/yakka.py` (`run_status`), `plugins/yakka/.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `plugins/yakka/bin/VERSION`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `install.sh`, `docs/design/03-remote-service.md`, `05-distribution.md`, `07-analytics-site.md`, `CHANGELOG.md`, the Fly deploy.
- Approach: known
- Depends on: Phases 1–3

## Provenance Notes

- **Mint on poll, not on approval.** Approval records the choice; the token is created when the CLI redeems it. This is what removes the plaintext token from `registry.json` and lets pending grants stay in memory.
- **Pending grants in memory.** Anonymous requests never write to disk, so `/v1/device/code` cannot be used to grow `registry.json`. The cost is that a restart during a login makes the user run it again.
- **`fetch`, not a navigating form.** The old form had to navigate so the browser followed the redirect to loopback. With no redirect, a credentialed `fetch` (yakka.build and api.yakka.build are the same site, so the `SameSite=Lax` cookie is sent) keeps the user on the page to see the result. The existing origin guard still applies.
- **`start`/`wait` split.** An agent should not have to read a running process's output to learn the URL. `start` returns at once with the URL; `wait` is the only long-running step and its exit is the signal.
- **The user code is checked on the page by eye.** Device-code phishing works by getting someone to approve a code they did not start. Showing the code large with "check this matches your terminal", plus a short expiry, is the standard mitigation.
- Rejected: keeping loopback as a `--browser` fallback (no user it serves); the CLI requesting tenant and scope (the CLI cannot know which tenants the user owns); porting login to Go (the plugin ships only the Python client).
