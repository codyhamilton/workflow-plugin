---
cursor:
  subagentId: "bc-88807259-84db-5de5-935e-f6344b0e49a5"
---

# Report: 4-03 — Fly collector outcome verify

**Status:** blocked

## What changed

Nothing verified. 4-02 left `https://yakka.build` without a release. The Fly app is `yakka`. No local substitute was run for the fly restart, revocation, or CORS checks.

## Checks

**Before and after** (same; host does not resolve):

```
curl -sS -o /dev/null -w '%{http_code}' https://yakka.build/v1/health
→ curl: (6) Could not resolve host: yakka.build
→ 000

curl -sS -D - -o /dev/null https://yakka.build/oauth/login
→ curl: (6) Could not resolve host: yakka.build
```

No ingest, revoke, restart, or CORS transcript. `fly machines list -a yakka` reports no machines, so there is nothing to restart.

## Deviations

None. The brief says to stay blocked when 4-02 is blocked and not to invent a local stand-in.

## Contract notes

The phase outcome's health, GitHub redirect, restart, and CORS sentences are all on `https://yakka.build`, served by Fly app `yakka`. That origin does not resolve. `WORKFLOW_SERVE_CORS_ORIGINS` is unset because the Pages origin is still unknown.

## Unfinished

1. Cody sets `A yakka.build → 137.66.6.45` and `AAAA yakka.build → 2a09:8280:1::1bb:db4d:0`, and sets `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` with `fly secrets set -a yakka`.
2. Then `fly deploy` from this branch. Confirm `fly secrets list -a yakka` still has no `WORKFLOW_SERVE_KEYS`.
3. Re-run this unit on `https://yakka.build`: health `200`, `/oauth/login` redirect to GitHub with `redirect_uri` `https://yakka.build/oauth/callback`, ingest before and after a machine restart, revoked bearer `401` after that restart.
4. CORS still needs the real Pages origin in `WORKFLOW_SERVE_CORS_ORIGINS`. Do not invent one.

## Bugs

None observed. The collector is not running.
