---
cursor:
  subagentId: "bc-1ec6b82c-d11a-5065-b210-5ffbb1fbf758"
---

# Report: 4-03 — Fly collector outcome verify

**Status:** blocked

## What changed

Nothing verified on `https://yakka.build`. 4-02 released machine `8047ddb6475de8`, and that origin still returns Cloudflare 525. No ingest, revoke, restart, or CORS check was run. `https://yakka.fly.dev` was not used as a substitute.

## Checks

**Before** (from the previous report): host did not resolve, no machines.

**After** (release exists; close origin does not answer):

```
curl -sS -o /dev/null -w '%{http_code}' https://yakka.build/v1/health
→ 525
→ server: cloudflare
→ body: error code: 525

curl -sS -D - -o /dev/null https://yakka.build/oauth/login
→ 525
→ server: cloudflare

curl -sS -D - -o /dev/null http://yakka.build/v1/health
→ 301 Location: https://yakka.build/v1/health
→ via: 1.1 fly.io

fly certs check yakka.build -a yakka
→ Not verified
→ add TXT _fly-ownership.yakka.build = app-5ydex1q

dig +short TXT _fly-ownership.yakka.build
→ empty

https://yakka.fly.dev/v1/health
→ 200 (not the close condition)

https://yakka.fly.dev/oauth/login
→ 302 to https://github.com/login/oauth/authorize
→ redirect_uri=https://yakka.build/oauth/callback
→ not the close condition
```

No ingest, revoke, restart, or CORS transcript. Restart persistence needs a session on the close origin, and the Pages origin for `WORKFLOW_SERVE_CORS_ORIGINS` is still unknown.

## Deviations

None. The brief says to stay blocked when the public origin is not proven and not to invent a fly.dev or local stand-in.

## Contract notes

Health, the GitHub redirect, restart, and CORS are all on `https://yakka.build`. That URL is a Cloudflare 525 because Fly has no certificate for the name. Orange-cloud DNS is expected. The missing record is `TXT _fly-ownership.yakka.build` = `app-5ydex1q`. Cloudflare SSL must stay Full (strict): the app's port 80 response is a 301 to HTTPS, so Flexible will loop. `WORKFLOW_SERVE_CORS_ORIGINS` is unset because the Pages origin is still unknown.

## Unfinished

1. Publish `TXT _fly-ownership.yakka.build` = `app-5ydex1q`. Leave the Cloudflare proxy on. Do not point the apex A/AAAA at `137.66.6.45` / `2a09:8280:1::1bb:db4d:0`. Keep SSL Full (strict).
2. `fly certs check yakka.build -a yakka` until the certificate is issued. Then `https://yakka.build/v1/health` must be 200 and `https://yakka.build/oauth/login` must 302 to GitHub with `redirect_uri` `https://yakka.build/oauth/callback`.
3. Re-run ingest before and after `fly machines restart`, and confirm the revoked bearer is still 401. `fly secrets list -a yakka` must still omit `WORKFLOW_SERVE_KEYS`.
4. CORS still needs the real Pages origin in `WORKFLOW_SERVE_CORS_ORIGINS`. Do not invent one.

## Bugs

None observed on the process. `https://yakka.fly.dev/v1/health` is 200. The custom hostname's TLS handshake to Fly fails, which is the missing certificate, not an app error.
