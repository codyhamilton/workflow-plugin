---
cursor:
  subagentId: "bc-a6d87835-33cb-509e-8621-1ead8277a408"
---

# Report: 4-02 — Fly collector deploy

**Status:** blocked

## What changed

Nothing on fly.io. No app, volume, secrets, or release was created (operator constraint: no `GITHUB_OAUTH_CLIENT_ID` / `GITHUB_OAUTH_CLIENT_SECRET` in this environment; do not invent values or placeholder secrets).

Added this report only.

## Checks

**Before** (no deploy; app does not exist):

```
flyctl auth whoami
→ 1b1db139-7037-53c8-a4c6-cde73c4f1733@tokens.fly.io

flyctl apps list -o l-fante
→ lfante-api-production, lfante-api-staging (no workflow-collector)

flyctl status -a workflow-collector
→ Could not find App "workflow-collector"

env | grep '^GITHUB_OAUTH'
→ (not set)

curl -sS -o /dev/null -w '%{http_code}' https://workflow-collector.fly.dev/v1/health
→ curl: (6) Could not resolve host: workflow-collector.fly.dev
→ 000

curl -sS -D - -o /dev/null https://workflow-collector.fly.dev/oauth/login
→ curl: (6) Could not resolve host: workflow-collector.fly.dev
```

**After** (unchanged — deploy not attempted):

Same outputs as before.

`fly secrets list` / `fly config env` for `workflow-collector`: not applicable until the app exists.

## Handoff for 4-03

| Item | Value |
|---|---|
| Intended public origin | `https://workflow-collector.fly.dev` (`WORKFLOW_PUBLIC_URL` in `fly.toml`) |
| Fly app name | `workflow-collector` (not created) |
| Volume | `workflow_serve_data` in `iad` per 4-01 (not created) |
| Pages CORS origin | `fly.toml` still has placeholder `https://replace-with-pages-project.pages.dev` — set to the real Pages URL before or during deploy |
| GitHub OAuth | Callback to register: `https://workflow-collector.fly.dev/oauth/callback`; scopes `read:user`, `user:email`. Real `GITHUB_OAUTH_CLIENT_ID` in env or `fly.toml`; `GITHUB_OAUTH_CLIENT_SECRET` via `fly secrets set` only |

**Resume steps:** `fly apps create workflow-collector` (or `fly launch` from repo), `fly volumes create workflow_serve_data -r iad -a workflow-collector`, set secrets, update GitHub OAuth app callback, replace placeholder client id and CORS origin, `fly deploy`, then run 4-03 evidence curls. Confirm `WORKFLOW_SERVE_KEYS` is never set.

## Deviations

Deploy and GitHub OAuth registration were skipped per run instructions when OAuth credentials are absent; aligns with brief “report `blocked`” when deploy cannot complete.

## Contract notes

Brief matches DESIGN collector-hosting contract. No contradiction between brief and DESIGN cited contracts.

## Bugs

None observed (no running collector).
