# Client registration implementation

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-3f650f40-1066-5daa-b196-4a4ab11ffc43
Started: 2026-10-16T11:35:03Z
Branch: `cursor/client-registration-3d44`
Starting HEAD: `33f90be`

Phase 1 is closed (`aa3c971`, `Workflow-Phase: client-registration:1`).

## Phase 4 — The collector runs on fly.io

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-c4d46ed6-4237-55d0-950e-4ae0ead9c9c5
Started: 2026-10-16T13:24:36Z
Resuming HEAD: `6e280e3`

Phase 4 only. Terminal review and close-out are not part of this run.

Resumed: 2026-10-17T15:23:19Z.
Run identity: https://cursor.com/agents/bc-88807259-84db-5de5-935e-f6344b0e49a5
Resuming HEAD: `140c63a`

The ctzns token can create apps. Cody corrected the Fly app name to `yakka`. The empty app `workflow-collector` was destroyed. App `yakka` now exists with a volume, dedicated addresses, and an unverified `yakka.build` certificate. The GitHub OAuth client id and secret are still absent, and `yakka.build` has no DNS, so there is no release. The phase is not closed. The product, CLI, and packages were not renamed.

Refined into four units, committed in `fad2d04`. 4-01 first. Then 4-02. After 4-02, 4-03 and 4-04 (4-04 also only needs 4-01). Phase 3 carried items stay out of this phase: other routes omitting `tenant`, the registry-open panic, e2e seeding, and the profile expiry prefill. 4-04 may note the tenant gap and must not claim full-site wiring.

artifact_feedback on the four phase 4 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 4-01-fly-collector-manifest

- Built: `fly.toml` for one machine, HTTP on port 8080, volume `workflow_serve_data` at `/data`. `WORKFLOW_SERVE_KEYS` is not set. `Dockerfile` embeds the analytics build and runs `workflow serve`. The GitHub client secret is not in the repo. Cody later set `app = "yakka"`. The product, CLI, and packages stay `workflow`.
- Surfaces: `fly.toml`, `Dockerfile`, `.dockerignore`.
- Commit: `f23689e`. `docker build` succeeded. `fly config validate` passed. A search of those files finds no `WORKFLOW_SERVE_KEYS`.
- Deviations: none. `GITHUB_OAUTH_CLIENT_ID` and `WORKFLOW_SERVE_CORS_ORIGINS` in `fly.toml` are placeholders for the operator.
- Agent: Composer, harness did not report turns or final context.

### 4-04-design-docs-fly-hosting

- Built: design 7 Hosting names the fly.io collector (`fly.toml`, volume, OAuth callback on the collector origin, no `WORKFLOW_SERVE_KEYS`, CORS for the Pages origin) and keeps Pages as the static pasted-token client. It notes `?tenant=` is still only on the overview and `/profile`.
- Surfaces: `docs/design/07-analytics-site.md`.
- Commit: `6f3e261`. That file names `fly.toml` and `WORKFLOW_SERVE_DATA`, and it does not say the dashboard has no user identity.
- Deviations: none at `6f3e261`. Hosting now names Fly app `yakka` and origin `https://yakka.build`. The product name stays `workflow`.
- Agent: Composer, harness did not report turns or final context.

### 4-02-fly-collector-deploy

- Built: Fly app `yakka` in org `ctzns`. Volume `workflow_serve_data` `vol_v3gppxdm66k9gmw4` in `iad` (1 GB, unattached). Dedicated IPv4 `137.66.6.45`. Dedicated IPv6 `2a09:8280:1::1bb:db4d:0`. Certificate `yakka.build` created, status Not verified. No machines, no secrets, no release. The empty app `workflow-collector` was destroyed. `fly.toml` `app` is `yakka`. `fly config validate` passed.
- Surfaces: `fly.toml`, the collector-hosting sentences in `DESIGN.md` and `docs/design/07-analytics-site.md`, briefs `4-01`, `4-02`, and `4-03` (app name only), and the report.
- `fly secrets list -a yakka` is empty, so `WORKFLOW_SERVE_KEYS` is unset. `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are absent from the environment (injected names are only `GH_TOKEN` and `FLY_API_TOKEN`). `fly deploy` was not run. `https://yakka.build/v1/health` does not resolve.
- Deviations: the earlier `l-fante` attempt created nothing (`bdeb88d`). A first create in this resume used the name `workflow-collector` and was destroyed after Cody corrected the name. No other Fly app was touched.
- Agent: this run, https://cursor.com/agents/bc-88807259-84db-5de5-935e-f6344b0e49a5. Harness did not report turns or final context.

### 4-03-fly-collector-outcome-verify

- Built: nothing. No health, OAuth, restart, revocation, or CORS check on `https://yakka.build`. The host does not resolve, and app `yakka` has no machines.
- Surfaces: the report only.
- Deviations: none. A local `workflow serve` was not used as a stand-in.
- Agent: this run, https://cursor.com/agents/bc-88807259-84db-5de5-935e-f6344b0e49a5. Harness did not report turns or final context.

### Public origin `https://yakka.build`

Cody set the phase 4 close condition to `https://yakka.build`. The GitHub OAuth callback is already `https://yakka.build/oauth/callback`. The product, CLI, and packages stay `workflow`. The Fly app name is `yakka`. `https://yakka.fly.dev` is not the origin to prove.

- Built: `WORKFLOW_PUBLIC_URL` in `fly.toml` is `https://yakka.build`. The placeholder client id and the placeholder Pages CORS origin are gone from the committed env. Design 7 Hosting and the phase 4 outcome name that origin and that callback. Briefs 4-01, 4-02, and 4-03 name the same origin.
- Surfaces: `fly.toml`, `docs/design/07-analytics-site.md`, `docs/plans/13-client-registration/DESIGN.md`, briefs `4-01`, `4-02`, and `4-03`.
- `fly config validate` on `fly.toml` passed, including `--strict`.
- `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are unset in the environment. Injected secret names on this resume are `GH_TOKEN` and `FLY_API_TOKEN`. `FLY_APP` is `yakka`, which matches the Fly app. No values were invented or written down.
- The earlier `l-fante` token could not create the app. This resume destroyed empty `workflow-collector` and created `yakka` in org `ctzns`. DNS to set, from `fly certs add yakka.build -a yakka`: `A yakka.build → 137.66.6.45` and `AAAA yakka.build → 2a09:8280:1::1bb:db4d:0`. The certificate is Not verified. `https://yakka.build` does not resolve. Do not use the destroyed app's addresses.
- The phase is not closed. `https://yakka.build` was requested and did not resolve, so it is not proof.

### Phase 4 verification

The public origin is not proven. The phase is not closed. No `Workflow-Phase: client-registration:4` trailer.

- App `yakka` exists in org `ctzns` with volume `vol_v3gppxdm66k9gmw4`, dedicated IPv4 `137.66.6.45`, dedicated IPv6 `2a09:8280:1::1bb:db4d:0`, and an unverified certificate for `yakka.build`. `workflow-collector` does not exist. There are no machines and no secrets. `WORKFLOW_SERVE_KEYS` is unset. `fly deploy` was not run because the GitHub OAuth client id and secret are absent.
- `curl` of `https://yakka.build/v1/health` and `https://yakka.build/oauth/login` failed with `Could not resolve host`. `dig` returned no A or AAAA for `yakka.build`.
- An earlier local non-loopback `workflow serve` (OAuth env set, `WORKFLOW_SERVE_KEYS` unset, `WORKFLOW_SERVE_CORS_ORIGINS=https://pages.example`) returned health 200, a GitHub redirect, CORS without credentials, and restart persistence for a token. That was the binary, not this fly app, and it is not proof of `https://yakka.build`.
- `docs/design/07-analytics-site.md` names the fly collector at `https://yakka.build` and leaves Pages as the pasted-token client.

artifact_feedback on the four phase 4 briefs and reports `4-01`, `4-02`, `4-03`, and `4-04`: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores). No `workflow` binary is on this machine.

### Remaining

1. Cody sets DNS: `A yakka.build → 137.66.6.45` and `AAAA yakka.build → 2a09:8280:1::1bb:db4d:0`. Then `fly certs check yakka.build -a yakka` can verify. Do not treat `https://yakka.fly.dev` as the close condition. Do not recreate `workflow-collector`.
2. Cody provides `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` in the environment (the GitHub OAuth app callback is already `https://yakka.build/oauth/callback`). Set both with `fly secrets set -a yakka`. Do not commit them. Do not deploy until both are set. Then `fly deploy` from this branch.
3. Then re-run 4-03 against `https://yakka.build`: health `200`, `/oauth/login` redirect to GitHub with that callback, `WORKFLOW_SERVE_KEYS` unset, a `read_write` token still ingests after a machine restart, a token revoked before the restart does not. The Pages origin is still unknown, so `WORKFLOW_SERVE_CORS_ORIGINS` stays unset until Cody names it; the CORS sentence of the outcome waits on that origin.
4. Collector-mode `tenant` is still only on `/` and `/profile`. `Server.New` still panics if the registry cannot be opened or persisted. E2e still seeds `registry.json`. The profile expiry field is still prefilled in the browser.

## Phase 2 — Issued tokens are the remote credential

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-6714af74-e997-5724-81fe-38570d576092
Started: 2026-10-16T12:08:00Z
Resuming HEAD: `aa3c971`

Phase 2 is closed (`1b7c79b`, `Workflow-Phase: client-registration:2`).

Refined into four units, committed in `3423391`. 2-01 first. After it, 2-02, 2-03, and 2-04 have disjoint paths. Phase 1 carried items: the e2e keyed setup and the overview `tenant` query go to 2-03; the registry-open panic stays as 2-01 left it.

artifact_feedback on the four phase 2 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 2-01-registry-tenancy-bearer

- Built: tenant create, issued `wk_` tokens stored as SHA-256, profile and admin token routes, bearer scope checks (read ingest is 403, revoked or expired is 401), and remote `tenantForKey` from the registry. A restart reloads the registry. A policy change does not revoke tokens.
- Surfaces: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/tokens.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/host.go`, `tools/workflow/internal/serve/session.go`, `tools/workflow/internal/serve/serve_test.go`.
- Commit: `a8cc689`. `go test ./internal/serve/` passed, including the token, tenant, and bearer tests.
- Deviations: token lists are a JSON array, not an object with a `tokens` field. `session.go` was edited; the brief's owned paths did not name it.
- Agent: Composer, harness did not report turns or final context.

### 2-02-wk-secret-scrub

- Built: the shared secret scanner treats `wk_` plus a 32-character body as `workflow_api_token` and redacts it.
- Surfaces: `tools/workflow/internal/secrets/secrets.go`, `tools/workflow/internal/secrets/secrets_test.go`.
- Commit: `11509e0`. `go test ./internal/secrets/` passed. `TestScanPatterns` failed before the pattern existed and passed after.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 2-03-analytics-profile-e2e

- Built: `/profile` creates a tenant and a token, shows the plaintext once, lists tokens without it, and revokes. Admin sessions also load `GET /v1/admin/tokens`. Collector posts send the session cookie and no bearer. E2e global-setup no longer sets `WORKFLOW_SERVE_KEYS`; it starts a remote serve with a registry-seeded `wk_` bearer.
- Surfaces: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/routes/profile/+page.svelte`, `packages/workflow-analytics/tests/e2e/global-setup.ts`.
- Commit: `d0cc49a`. `npm test` passed (166). Playwright `session.spec.ts` and `settings.spec.ts` (excluding `@slow`) passed, 4 tests, after previously exiting because of `WORKFLOW_SERVE_KEYS`.
- Deviations: the e2e bearer is written into `registry.json` before serve starts, not issued through OAuth and `POST /v1/tokens`. Other analytics routes still omit `tenant`.
- Agent: Composer, harness did not report turns or final context.

### 2-04-design-docs-remote-tokens

- Built: `docs/design/03-remote-service.md` describes issued `wk_` tokens, GitHub session login, and a non-empty `WORKFLOW_SERVE_KEYS` refusing startup. It no longer says registration, key issue, or rotation are out of scope.
- Surfaces: `docs/design/03-remote-service.md`.
- Commit: `bf25bde`. A search of that file finds no `out of scope` and no `tenant=key` credential line. It names `wk_` and GitHub.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### Phase 2 verification

Outcome holds.

- A logged-in session `POST`ed tenant `acme` and a `read_write` token. The create response carried the `wk_` plaintext. `GET /v1/tokens` and `registry.json` did not. `POST /v1/ingest` with that bearer stored the fact under `acme`, and `GET /v1/analytics/summary?tenant=acme` returned 200. The same tenant's `read` token got 403 `read-only token` and stored nothing, and 200 on the summary.
- A fact whose text contained the `wk_` token was rejected by precheck and the plaintext was absent from the data directory. The same text after `Redact` was accepted and stored without the token.
- After the owner revoked, the next ingest was 401 and stored nothing. An in-process reload kept the token valid, and the revocation after that reload stuck. A separate OS restart of `workflow serve` on the same data directory still accepted the live token (`duplicate` for the fact stored before the restart) and still returned 401 for the revoked token. The plaintext was not on disk.
- A session summary for the owned tenant was 200; another tenant was 403 `no such tenant`. Tightening the domain policy left the bearer able to ingest.
- `go test` covering `TestToken`, `TestRegistryTenant`, `TestRegistryRestart`, and `TestBearerTenant` passed, including admin list without `token` and admin revoke of another user's token. `go test ./internal/secrets/` passed. `npm test` passed (166).
- Chromium on the collector origin, with a stored `wk_` key: `/` requested `GET /v1/analytics/summary?...&tenant=acme` with an empty `Authorization` and showed that summary (`4242` conversations). `/profile` created a token, showed the plaintext once, and the list table did not contain it. The create `POST /v1/tokens` sent no bearer.
- Starting with `WORKFLOW_SERVE_KEYS` set exited before listen, and the error names that variable. `docs/design/03-remote-service.md` has no `out of scope` and no `tenant=key` credential line.

artifact_feedback on the four phase 2 briefs and four reports: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### Carried

1. Collector-mode `tenant` is still only on `/`. Other analytics routes omit it.
2. `Server.New` panics if the registry cannot be opened or persisted.
3. E2e global-setup seeds `registry.json` instead of logging in and calling `POST /v1/tokens`.
4. The profile expiry field is prefilled to three months in the browser. The device page must not copy that. The server still has no default.

## Phase 3 — Devices and remote agents present a token

Tool: Cursor (Grok 4.7 orchestrator).
Run identity: https://cursor.com/agents/bc-b44d5a65-1dda-58d1-8753-0a1631f41a82
Started: 2026-10-16T12:29:57Z
Resuming HEAD: `1b7c79b`

Phase 3 is closed (`6e280e3`, `Workflow-Phase: client-registration:3`).

Refined into five units, committed in `e0d9c1d`. 3-01 and 3-02 first (disjoint). After 3-02, 3-03 and 3-04. 3-05 after 3-01 and 3-04. Phase 2 carried items: other routes omitting `tenant` stay out of this phase; the registry-open panic stays; e2e seeding stays; the device page must not prefill expiry.

artifact_feedback on the five phase 3 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 3-01-clientconfig-env-resolution

- Built: `clientconfig.Load` uses both `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` over the file, and returns `ErrPartialEnv` when exactly one is set. Drain and status exit 1 on that error before any request. Env-only remote ingest and an MCP bearer GET are covered.
- Surfaces: `tools/workflow/internal/clientconfig/clientconfig.go`, `tools/workflow/internal/clientconfig/clientconfig_test.go`, `tools/workflow/internal/drain/cli.go`, `tools/workflow/cmd/workflow/drain_test.go`, `tools/workflow/internal/mcp/mcp_test.go`.
- Commit: `5fa53ad`. `go test` on `internal/clientconfig`, `cmd/workflow` (`Drain|Env|Client|Status`), and `internal/mcp` passed.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 3-02-device-auth-server

- Built: remote `POST /v1/device/authorize` (session, JSON, Origin) issues a token and 303s to the loopback redirect with `code` and `state` only. `POST /v1/device/exchange` takes no session and no Origin, returns `endpoint` and the one-time `token`, and a second exchange is 401. Device codes persist in `registry.json`.
- Surfaces: `tools/workflow/internal/serve/device.go`, `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`.
- Commit: `e04e500`. `go test ./internal/serve/` passed, including `-run Device`.
- Deviations: none. The registry keeps the token plaintext until exchange so a restart can still redeem the code.
- Agent: Composer, harness did not report turns or final context.

### 3-03-device-page

- Built: `/device` requires `state` and a loopback `redirect_uri`, and tenant, grant, and expiry with no defaults (expiry starts empty). Zero tenants shows a create form. Signed-out users go to `/oauth/login?return=…`. Submit is one form POST to `/v1/device/authorize`, and the browser follows the 303 to the loopback callback. The page does not show the plaintext.
- Surfaces: `packages/workflow-analytics/src/routes/device/+page.svelte`, `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/tests/e2e/device.spec.ts`. The fixer also touched `tools/workflow/internal/serve/device.go`, `tools/workflow/internal/serve/session.go`, and `tools/workflow/internal/serve/serve_test.go`.
- Commit: `48309e2`. `npm test` passed (169). Playwright `device.spec.ts` passed (2). Fixer `2141d86` replaced the fetch workaround with the form POST.
- Deviations: the first page used `fetch` and, in Chromium, that opaque 303 issued a second token and never navigated. `2141d86` accepts `application/x-www-form-urlencoded` on this route (session and Origin still required) and the page submits once. `global-setup.ts` was left alone.
- Agent: Composer, harness did not report turns or final context.

### 3-04-workflow-login-cli

- Built: `workflow login [--endpoint URL]` listens on loopback `/callback`, opens `{endpoint}/device?state=&redirect_uri=`, exchanges the code, and writes `endpoint` and `key` into `client.toml` at mode 0600. Missing endpoint exits 1 and writes nothing. Success output does not include the token.
- Surfaces: `tools/workflow/internal/login/login.go`, `tools/workflow/internal/login/login_test.go`, `tools/workflow/cmd/workflow/main.go`, `tools/workflow/cmd/workflow/login_test.go`.
- Commit: `102e791`. `go test ./internal/login/ ./cmd/workflow/ -run Login` passed.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 3-05-design-docs-client-login

- Built: design 2 and design 5, and `tools/hooklog/README.md`, describe env-pair resolution, half-set failure, `client.toml`, local default, and the built `workflow login`. They no longer say the command is not built yet. Design 5 notes that `tenant` is still only on the overview. They do not claim an OAuth e2e login.
- Surfaces: `docs/design/02-edge-capture.md`, `docs/design/05-distribution.md`, `tools/hooklog/README.md`.
- Commit: `8456ea3`. Those files name `WORKFLOW_ENDPOINT` and `workflow login`, and the only `workflow init` lines say there is none.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### Phase 3 verification

Outcome holds.

- With `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` set to a live `read_write` token and no `client.toml`, `workflow drain` stored the spooled fact and `workflow mcp` `list_checks` reached the collector with that bearer (`no checks loaded on the service`, HTTP 200). A `client.toml` from `workflow login`, with those env vars unset, did the same. A hand-written `client.toml` with the same key did too.
- Neither file nor env is local mode: `workflow status` said `config: none (local mode)` and `GET /v1/health` on `127.0.0.1:8770` carried an empty `Authorization`.
- Exactly one of `WORKFLOW_ENDPOINT` or `WORKFLOW_KEY`, with a working `client.toml` present, made `workflow status` and `workflow drain` exit 1 before any connection. `workflow mcp` returned the unusable-config text and did not contact the file's collector, the half-set endpoint, or loopback.
- `workflow login --endpoint` opened `https://<collector>/device?state=&redirect_uri=` with the loopback callback. The live `/oauth/login?return=` redirected to `https://github.com/login/oauth/authorize` and set `workflow_oauth_return`. The signed-out device page links to that login with the device path as `return`. The binary has no mock GitHub base, so the session cookie was seeded and the page was driven in Chromium; the return trip from github.com was not run.
- With no tenant, the page asked for a name and created it. Grant and expiry were empty, and Authorize stayed disabled until both were chosen. The submitted `expires_at` was the chosen time (`2027-06-15T15:30:00Z`), not a generated lifetime. One form POST, then the browser document landed on that login's `http://127.0.0.1:<port>/callback?code=&state=`. The page, the callback URL, and the login stderr contained no `wk_` plaintext. After exchange, `registry.json` had no `wk_` plaintext. A second exchange of that code was 401 and returned no token.
- Drain with the `read_write` key from that file delivered. A `read` token from a second login left ingest 403 `read-only token` and stored nothing, and `workflow mcp` still read. The earlier `read_write` token still authorized (`200`, `duplicate` for a fact already stored). Quitting before submit wrote no file. Login with no endpoint exited 1 and wrote nothing.
- Loopback `workflow serve` with no keys answered `GET /v1/health`. `workflow init` is not a command (exit 2, usage has no `init`). `docs/design/02-edge-capture.md` and `docs/design/05-distribution.md` name `WORKFLOW_ENDPOINT` and `workflow login`, and they do not say the command is not built yet.
- `go test` on `internal/clientconfig`, `internal/login`, `internal/serve` (including `TestDeviceAuthorizationFlow`), `internal/mcp`, and `cmd/workflow` (`Login|ClientEnv|HalfSet`) passed. `npm test` passed (169).

artifact_feedback on the five phase 3 briefs and five reports: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### Carried

1. Collector-mode `tenant` is still only on `/`. Other analytics routes omit it.
2. `Server.New` panics if the registry cannot be opened or persisted.
3. E2e global-setup seeds `registry.json` instead of logging in and calling `POST /v1/tokens`.
4. The profile expiry field is prefilled to three months in the browser. The device page does not copy that. The server still has no default.

## Phase 1 — GitHub login and admission

Refined into four sequential units, committed in `7dd001f`. Nothing runs in parallel: 1-01, then 1-02, then 1-03, then 1-04.

artifact_feedback on the four phase 1 briefs: quality service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### 1-01-registry-remote-config

- Built: `registry.json` under `WORKFLOW_SERVE_DATA` (policy, sessions, reserved owners and token hashes), `Local()` / `Remote()`, and `ConfigFromEnv` that refuses a non-empty `WORKFLOW_SERVE_KEYS`, ignores OAuth on loopback, and requires the OAuth trio plus a valid `WORKFLOW_PUBLIC_URL` on a non-loopback bind. `New` opens the registry when remote.
- Surfaces: `tools/workflow/internal/serve/registry.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`, `tools/workflow/cmd/workflow/main_test.go`.
- Commit: `3191ce2`. `go test` on `internal/serve` and `cmd/workflow` passed (`TestServeOutcome` now covers OAuth refusal, keys refusal on loopback, and loopback local ingest).
- Deviations: the keys refusal lives in `ConfigFromEnv` only, not a second check in `runServe`. `New` panics if the registry cannot be opened or persisted. Tests for the registry landed in `serve_test.go` rather than a new `registry_test.go`. `main.go` was not edited.
- Agent: Composer, harness did not report turns or final context.

### 1-02-oauth-session-remote-auth

- Built: GitHub OAuth login, callback, and logout; `workflow_session` with a policy re-check; admin `PUT /v1/admin/policy`; `GET /v1/me`; remote `/v1` auth that treats ingest as bearer-only and leaves loopback on `localGuard`. Unknown bearers are `unauthorized` until phase 2 issues tokens.
- Surfaces: `tools/workflow/internal/serve/oauth.go`, `tools/workflow/internal/serve/session.go`, `tools/workflow/internal/serve/serve.go`, `tools/workflow/internal/serve/serve_test.go`.
- Commit: `40b81f7`. `go test ./internal/serve/` passed, including `TestOAuthSessionRemoteAuth`, `TestRemoteSessionIngestAndTenant`, `TestRemotePolicyAdmin`, and `TestLoopbackUnchangedWithOAuthEnv`.
- Deviations: none.
- Agent: Composer, harness did not report turns or final context.

### 1-03-analytics-session-site

- Built: collector-origin fetches send the session cookie and no bearer; the overview appends `tenant` from `GET /v1/me`; `/login` exists, including the denied-admission message; a 403 `no such tenant` is not treated as a logged-out 401.
- Surfaces: `packages/workflow-analytics/src/lib/api.ts`, `packages/workflow-analytics/src/lib/api.test.ts`, `packages/workflow-analytics/src/routes/+layout.svelte`, `packages/workflow-analytics/src/routes/+page.svelte`, `packages/workflow-analytics/src/routes/login/+page.svelte`, `packages/workflow-analytics/tests/e2e/session.spec.ts`.
- Commit: `fd91d15`. `npm test` passed (163 tests). Playwright `--grep 'session|login'` did not run: e2e global-setup starts a keyed `workflow serve` with `WORKFLOW_SERVE_KEYS`, and that process now exits before listen.
- Deviations: none from the brief. Other analytics routes still omit `tenant` in collector mode.
- Agent: Composer, harness did not report turns or final context.

### 1-04-design-docs-login

- Built: `docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` describe the collector GitHub session, `/login`, and `workflow_session`. They no longer say the dashboard has no user identity, and they no longer say `workflow login` is the way remote mode is opted into.
- Surfaces: `docs/design/05-distribution.md`, `docs/design/07-analytics-site.md`.
- Commit: `aa6dd93`. A search of those two files finds no `no user identity`, no `WORKFLOW_SERVE_KEYS=tenant`, and no `workflow login (not built yet)`.
- Deviations: none. The docs name bearer tokens as the client credential before phase 2 issues them.
- Agent: Composer, harness did not report turns or final context.

### Phase 1 verification

Outcome holds.

- A non-loopback `workflow serve` with the OAuth env set and `WORKFLOW_SERVE_KEYS` unset listened, wrote `registry.json`, and answered `GET /v1/analytics/summary` with 401 `sign in at https://collector.example/login`. The same bind with `WORKFLOW_SERVE_KEYS` set, a loopback bind with that variable set, and a non-loopback bind missing the OAuth env each exited 1 before the port accepted a connection. The keys error names `WORKFLOW_SERVE_KEYS`.
- Against the handler and a mock GitHub: a verified `codyh@ctzns.net` login set `workflow_session` (HttpOnly, SameSite=Lax, Secure) and redirected to `/`. The same admin still got a session when the allow list was `allowed.example`. A verified `x@denied.example` login redirected to `/login?error=denied` with no session cookie. `PUT /v1/admin/policy` to `allow_list` and back to `everyone` was 200 for the admin and 403 for a non-admin; `everyone` stored an empty domain list. After the list was tightened, the member's next summary was 401 and the cookie was cleared. The stranger's next login then landed on `/` with a session. A session with no owned tenant got 403 `{"error":"no such tenant"}`. `POST /v1/ingest` with no bearer, and with a session and no bearer, was 401 and left no `ledger.db`.
- The live binary's `/oauth/login` redirected to `https://github.com/login/oauth/authorize`. The binary has no mock GitHub base, so the cookie was checked on the handler, not against github.com.
- Loopback with the OAuth env set served `/` (200, built site) and `GET /v1/analytics/summary` (200) with no cookie. A bearer on that summary was ignored (200).
- Chromium on the collector origin, with `workflow-analytics-key` set to a `wk_` value: `/login` showed Sign in with GitHub; `/login?error=denied` showed the denial. With `/v1/me` returning no tenants and summary returning 403 `no such tenant`, the page said "You do not have a tenant yet" and did not offer the logged-out sign-in link. Every `/v1` request had an empty `Authorization` header.
- `npm test` in `packages/workflow-analytics`: 163 passed. `go test ./internal/serve/` passed. The first `go test ./cmd/workflow` failed because those servers still set `WORKFLOW_SERVE_KEYS` and exited before listen. `52dfcf0` starts them without that variable and expects tenant `local`. `main_test.go` still expects the refusal. After that commit, `go test ./cmd/workflow/` passed.
- `docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` have no `no user identity`, no `WORKFLOW_SERVE_KEYS=tenant`, and no `workflow login (not built yet)`.

artifact_feedback on the four phase 1 briefs and four reports: service unreachable at `http://127.0.0.1:8770` (`state: not delivered`, no scores).

### Carried

1. `packages/workflow-analytics` e2e global-setup still sets `WORKFLOW_SERVE_KEYS`, so the keyed server exits before listen and `tests/e2e/session.spec.ts` did not run.
2. Collector-mode `tenant` is appended on the overview only. Other analytics routes still omit it.
3. `Server.New` panics if the registry cannot be opened or persisted.
