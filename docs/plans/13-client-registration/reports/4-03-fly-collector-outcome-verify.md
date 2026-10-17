---
cursor:
  subagentId: "bc-1ec6b82c-d11a-5065-b210-5ffbb1fbf758"
---

# Report: 4-03 — Fly collector outcome verify

**Status:** done

## What changed

Checked `https://yakka.build` after the ownership TXT was published and the certificate issued. Health, the GitHub login redirect, `WORKFLOW_SERVE_KEYS`, and restart persistence hold. There is no Cloudflare Pages site, so the browser-origin CORS check is not applicable. `WORKFLOW_SERVE_CORS_ORIGINS` stays unset.

## Checks

**Before** (certificate Not verified): `https://yakka.build/v1/health` was Cloudflare 525.

**After** (Let's Encrypt certificate verified; machine `8047ddb6475de8` restarted once during the check):

```
fly certs check yakka.build -a yakka
→ Issued, Let's Encrypt, verified

curl https://yakka.build/v1/health
→ 200 {"ok":true,"version":"dev",...}
→ via: 1.1 fly.io

curl https://yakka.build/oauth/login
→ 302 Location https://github.com/login/oauth/authorize
→ redirect_uri=https://yakka.build/oauth/callback
→ client_id present, not recorded

fly secrets list -a yakka
→ GITHUB_OAUTH_CLIENT_ID
→ GITHUB_OAUTH_CLIENT_SECRET
→ no WORKFLOW_SERVE_KEYS

fly config env
→ WORKFLOW_PUBLIC_URL, WORKFLOW_SERVE_ADDR, WORKFLOW_SERVE_DATA
→ no WORKFLOW_SERVE_CORS_ORIGINS
```

Using Cody's existing admin session (not printed), tenant `p4restart`:

```
POST /v1/tokens read_write  → 201 id b96f310fbd8afc4597f777c63849c088 last4 rXSw
POST /v1/tokens read_write  → 201 id 9f03e391efd9e99d324456bf42448407 last4 7Cis
POST /v1/ingest live        → 200 accepted id p4#live-before
POST /v1/tokens/9f03e391efd9e99d324456bf42448407/revoke → 204
POST /v1/ingest revoked     → 401 unauthorized
fly machines restart 8047ddb6475de8
GET /v1/health              → 200
POST /v1/ingest live        → 200 accepted id p4#live-after
POST /v1/ingest p4#live-before again → 200 duplicate (same tenant)
POST /v1/ingest revoked     → 401 unauthorized
GET /v1/analytics/summary?tenant=p4restart → 200 conversations 1, hook_events 1
```

The live verification token was revoked after that transcript (204, next ingest 401). Plaintext was not written down.

CORS, env still unset:

```
GET /v1/analytics/summary?tenant=p4restart
  Origin: https://evil.example  → 200, no Access-Control-Allow-* headers
```

No allowed-origin check. Cody confirmed there is no Cloudflare Pages site, so there is no frontend origin to allow.

`docs/design/07-analytics-site.md` names app `yakka`, `https://yakka.build`, and the Pages pasted-token path.

## Deviations

The CORS half of the brief was not run against a Pages origin. There is no such site. The secret stays unset.

## Contract notes

Health, the callback, unset `WORKFLOW_SERVE_KEYS`, and restart/revocation hold on `https://yakka.build`. The browser-origin CORS check is not applicable: there is no Cloudflare Pages site, and `WORKFLOW_SERVE_CORS_ORIGINS` stays unset.

## Unfinished

None. The Pages CORS check is not applicable.

## Bugs

None. The summary window does not count the pre-restart fact because its `ts` was 1. The post-restart fact used a current timestamp and showed up as `hook_events: 1`.
