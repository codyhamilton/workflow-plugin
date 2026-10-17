---
cursor:
  subagentId: "bc-1ec6b82c-d11a-5065-b210-5ffbb1fbf758"
---

# Report: 4-02 — Fly collector deploy

**Status:** blocked

## What changed

`fly deploy --ha=false --remote-only -a yakka` from this branch released one machine. `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` were already staged on app `yakka` when this run started. This run did not call `fly secrets set`: those two names were absent from the environment. The release moved both to Deployed. `WORKFLOW_SERVE_KEYS` is not a secret and is not in `fly.toml`.

App `yakka` in org `ctzns`:

- Machine `8047ddb6475de8` (`withered-waterfall-175`), region `iad`, state started, size shared-cpu-1x 1024MB, image `yakka:deployment-01M558Z6K3Q8GGZ2PXRZVERQ4E`.
- Volume `vol_v3gppxdm66k9gmw4` (`workflow_serve_data`) attached at `/data`. The process logs `workflow serve: listening on [::]:8080`.
- Dedicated IPv4 `137.66.6.45`. Dedicated IPv6 `2a09:8280:1::1bb:db4d:0`.
- Certificate `yakka.build` still Not verified. `fly certs setup yakka.build -a yakka` says the proxy path needs `TXT _fly-ownership.yakka.build` = `app-5ydex1q`. That TXT is not published. Public DNS is Cloudflare (`104.21.87.219`, `172.67.147.5`, and Cloudflare AAAA). That proxy is expected. Do not replace it with the Fly addresses.

`workflow-collector` was not recreated. The product, CLI, and packages were not renamed.

## Checks

**Before** (no machines; OAuth env absent; secrets already staged; `https://yakka.build` did not serve this app):

```
GITHUB_OAUTH_CLIENT_ID
→ absent from this environment

GITHUB_OAUTH_CLIENT_SECRET
→ absent from this environment

flyctl secrets list -a yakka
→ GITHUB_OAUTH_CLIENT_ID Staged
→ GITHUB_OAUTH_CLIENT_SECRET Staged
→ no WORKFLOW_SERVE_KEYS

flyctl machines list -a yakka
→ No machines
```

**After** (one machine; secrets Deployed; custom hostname still not the app):

```
flyctl secrets list -a yakka
→ GITHUB_OAUTH_CLIENT_ID Deployed
→ GITHUB_OAUTH_CLIENT_SECRET Deployed
→ no WORKFLOW_SERVE_KEYS

flyctl machines list -a yakka
→ 8047ddb6475de8 started, volume vol_v3gppxdm66k9gmw4

curl https://yakka.build/v1/health
→ HTTP 525 from Cloudflare (server: cloudflare). Body: error code: 525

curl https://yakka.build/oauth/login
→ HTTP 525 from Cloudflare

curl http://yakka.build/v1/health
→ HTTP 301 Location https://yakka.build/v1/health
→ via: 1.1 fly.io (the proxy reached the app on port 80; force_https redirected)

curl https://yakka.fly.dev/v1/health
→ HTTP 200 {"ok":true,...}

curl https://yakka.fly.dev/oauth/login
→ HTTP 302 Location https://github.com/login/oauth/authorize
→ redirect_uri=https://yakka.build/oauth/callback
→ client_id present, not recorded

flyctl certs check yakka.build -a yakka
→ Not verified
→ ownership TXT required for HTTP validation behind a proxy

dig TXT _fly-ownership.yakka.build
→ no record
```

Direct TLS to `137.66.6.45` with SNI `yakka.build` closes during the handshake. SNI `yakka.fly.dev` completes with `CN=*.fly.dev`.

## Handoff for 4-03

| Item | Value |
|---|---|
| Public origin to prove | `https://yakka.build` (Cloudflare 525; not proven) |
| Fly app | `yakka` in org `ctzns` |
| Machine | `8047ddb6475de8` started |
| Volume | `vol_v3gppxdm66k9gmw4` attached |
| Hostname that answers | `https://yakka.fly.dev` is not the close condition |
| Ownership TXT still to set | `TXT _fly-ownership.yakka.build` = `app-5ydex1q` |
| ACME CNAME from `fly certs setup` | `CNAME _acme-challenge.yakka.build` → `yakka.build.5ydex1q.flydns.net.` (only if issuing before traffic) |
| Pages CORS origin | still unknown; `WORKFLOW_SERVE_CORS_ORIGINS` stays unset |
| GitHub OAuth | Callback on the fly.dev login redirect is `https://yakka.build/oauth/callback`. Secret names are Deployed. Values were not printed. |
| Cloudflare SSL | Keep Full (strict). Port 80 already 301s to HTTPS, so Flexible will loop. HTTPS is 525 until Fly has a cert. |

## Deviations

This run did not set the OAuth secrets from the environment, because both variables were absent. They were already staged, and the deploy released them. The public-origin curls are 525, so the brief's done evidence on `https://yakka.build` did not pass. `https://yakka.fly.dev` was checked only as the fallback the orchestrator asked for.

## Contract notes

The public origin is `https://yakka.build`. The app is released, and that origin does not answer health or the GitHub redirect. The certificate cannot be issued through the Cloudflare proxy until the ownership TXT exists.

## Bugs

None in the product. `workflow serve` is listening. The custom hostname has no Fly certificate.
