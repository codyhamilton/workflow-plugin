---
cursor:
  subagentId: "bc-1ec6b82c-d11a-5065-b210-5ffbb1fbf758"
---

# Report: 4-02 — Fly collector deploy

**Status:** done

## What changed

App `yakka` in org `ctzns` is released. Machine `8047ddb6475de8` is started, volume `vol_v3gppxdm66k9gmw4` is attached, and the Let's Encrypt certificate for `yakka.build` is verified after Cody published `TXT _fly-ownership.yakka.build` = `app-5ydex1q`. Cloudflare still proxies the name. `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are Deployed. This environment never had those variables, so this run did not call `fly secrets set`. `WORKFLOW_SERVE_KEYS` is unset. `workflow-collector` was not recreated.

## Checks

**Before:** no machines, certificate Not verified, `https://yakka.build` was Cloudflare 525.

**After:**

```
fly certs check yakka.build -a yakka
→ Issued, verified

curl https://yakka.build/v1/health
→ 200 {"ok":true,...} via fly.io

curl https://yakka.build/oauth/login
→ 302 https://github.com/login/oauth/authorize
→ redirect_uri=https://yakka.build/oauth/callback

fly secrets list -a yakka
→ GITHUB_OAUTH_CLIENT_ID Deployed
→ GITHUB_OAUTH_CLIENT_SECRET Deployed
→ no WORKFLOW_SERVE_KEYS
```

TLS to `yakka.build` verifies, certificate CN `yakka.build`.

## Handoff for 4-03

| Item | Value |
|---|---|
| Public origin | `https://yakka.build` (health 200, login redirect) |
| Fly app | `yakka` in org `ctzns` |
| Machine | `8047ddb6475de8` |
| Volume | `vol_v3gppxdm66k9gmw4` attached |
| Pages CORS origin | not applicable; there is no Cloudflare Pages site; `WORKFLOW_SERVE_CORS_ORIGINS` stays unset |
| GitHub OAuth | Callback on the live redirect is `https://yakka.build/oauth/callback` |

## Deviations

OAuth values were not set from this environment. They were already staged and the deploy released them. There is no Cloudflare Pages site, so `WORKFLOW_SERVE_CORS_ORIGINS` stays unset.

## Contract notes

The public origin is live on Fly app `yakka`. `https://yakka.fly.dev` is not the origin that was proven.

## Bugs

None.
