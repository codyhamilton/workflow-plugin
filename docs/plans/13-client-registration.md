# Client registration

The collector can now issue its own credentials and run on fly.io. A person signs in with GitHub, creates tenants, and issues `wk_` tokens with a scope and an expiry. Devices get a token through `workflow login`. Agents send it as a bearer. The public collector is app `yakka` at `https://yakka.build`. It does what the request asked.

## Intent

User request, verbatim:

> Important next step for this workflow service is to be able to run it as a collector on fly.io, so that both cloud and local agents can post events. Key item we are missing is client registration, which will be via keys we issue from the service. I'm wondering if we can do it like this - we register this as a github oauth app. We have a login page on the service, which logs the user in with github. On the user profile page we let them create api tokens, which then can be configured in various places - user device, claude / codex remote agent env etc for submitting events and getting data. feasible? /design

## Why This Existed

Remote `workflow serve` had one credential, `WORKFLOW_SERVE_KEYS`: tenant and key pairs in the process environment, with no issuer, no expiry, and no way to add a key without a restart. `workflow login` was documented and not built. The analytics site asked a person to paste a long-lived tenant key. Nothing in the tree was a GitHub login, a profile, or a fly.io collector.

## What Was Built

**Changed:** `tools/workflow` serve, login, client config, and secret scrub; `packages/workflow-analytics` login, profile, and device page; `fly.toml`, `Dockerfile`, and `.dockerignore`; design docs 2, 3, 5, and 7; `tools/hooklog/README.md`.

The living contract is in [design 3](../design/03-remote-service.md) (remote mode, issued tokens, registry), [design 5](../design/05-distribution.md) and [design 2](../design/02-edge-capture.md) (`workflow login` and client config), and [design 7](../design/07-analytics-site.md) (session site and the fly host).

### Phase 1 — GitHub login and admission
A non-loopback `workflow serve` requires the GitHub OAuth env and refuses a non-empty `WORKFLOW_SERVE_KEYS`. Loopback stays keyless local mode. `GET /oauth/login` goes to GitHub. A verified `codyh@ctzns.net` session is admin even when the allow list omits that domain. Other users follow the collector policy (`everyone` by default, or an exact domain allow list). Ingest without a bearer stores nothing. The embedded site sends the session cookie and no stored bearer.

### Phase 2 — Issued tokens are the remote credential
The profile creates a tenant and a `read` or `read_write` token with a future `expires_at`. The plaintext appears only in that create response. The registry stores the SHA-256. A `read` token gets 403 on ingest and 200 on summary. Revoked or expired is 401. Restart reloads the registry. A policy change does not revoke tokens. Submitted text that contains a `wk_` token is stored without it.

### Phase 3 — Devices and remote agents present a token
`WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` together beat `client.toml`. Exactly one of them fails drain, status, and MCP before any request. `workflow login` opens the collector device page. The page asks for tenant, grant, and expiry with no defaults, then redirects the browser to that login's loopback URI with a one-time code. The CLI writes `endpoint` and `key` into `client.toml` and prints no token. `workflow init` was not added.

### Phase 4 — The collector runs on fly.io
One machine, app `yakka` in org `ctzns`, volume `workflow_serve_data`, serves the API at `https://api.yakka.build` (`YAKKA_PUBLIC_URL`). Health is 200 with no bearer. GitHub's registered callback stays `https://yakka.build/oauth/callback`: that Pages page shows status and sends a credentialed request to the API, which sets the host-only session cookie and returns JSON with no redirect. `YAKKA_PUBLIC_URL` is the device-exchange endpoint, the Secure-cookie flag, and the 401 login hint. It is not the GitHub `redirect_uri`. `YAKKA_SERVE_CORS_ORIGINS` allows `https://yakka.build` and `https://www.yakka.build`. The production Fly image does not embed the analytics site. `yakka login` writes the API endpoint and the minted token; the device page is Pages `/device` and the form posts to the API.

## Deviations

- Device codes keep the token plaintext in the registry until exchange, so a restart can still redeem the code. The hash is what authorizes after that.
- Token lists are a JSON array, not an object with a `tokens` field.
- The device authorize route accepts a form POST as well as JSON, so the browser can follow the loopback redirect in one navigation.
- E2e seeds the registry instead of logging in. The profile expiry field is prefilled; the device page is not.
- Collector-mode `?tenant=` from `GET /v1/me` is wired on the overview and `/profile` only.

## Review

Terminal review at the phase 4 close found no blocker and no high finding. One mechanical docs sentence was corrected: design 7 no longer says the fly app already lists a Pages origin. Verdict was PASS_WITH_FOLLOWUPS.

## QA

Phases 1–3 were checked with `go test` on serve, login, client config, and secrets, plus the analytics unit tests and the session, settings, and device Playwright specs. Phase 4 was checked on `https://yakka.build`: health, the GitHub redirect, and ingest before and after a machine restart. There was no separate QA script.

## Residual Risks

- The collector is one machine and one volume. Losing the volume loses the registry and the ledgers. A second replica is out of scope.
- Cloudflare proxies `yakka.build`. SSL has to stay Full (strict). Flexible loops because the app redirects port 80 to HTTPS.
- `artifact_feedback` never scored the briefs or reports. The quality service was not running.
- The GitHub round trip for `workflow login` was not driven against github.com. The session was seeded, and the device page and exchange were.

## Follow-ups

Recorded as open issue 18 in [design 7](../design/07-analytics-site.md): overview-only `?tenant=`, the registry-open panic, e2e seeding, the prefilled profile expiry, and device-code plaintext until exchange. The OAuth return path now rejects values that are not a same-origin path, including those whose cookie serialization would become protocol-relative.

## Decisions Worth Keeping

- The session is not a bearer, and a bearer is not a session. Ingest is bearer-only.
- A token has one tenant, one scope, and one expiry the issuer set. There is no silent default.
- `WORKFLOW_SERVE_KEYS` is refused, not imported.
- `workflow login` is how a device gets `client.toml`. `workflow init` stays absent.
