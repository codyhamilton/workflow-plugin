---
cursor:
  subagentId: "bc-900a6b46-5bc9-5525-8dfc-e665c1a04e54"
---

# Report: 1-04 — Design docs for login and admission

**Status:** done

## What changed

- `docs/design/05-distribution.md`: loopback keyless unchanged; `WORKFLOW_SERVE_KEYS` exits before listen; remote collector uses GitHub OAuth env vars, session-backed embedded site, bearer for clients; `workflow login` deferred to a later phase.
- `docs/design/07-analytics-site.md`: Shape and routes document collector session login (`/login`, cookie, `GET /v1/me`, `?tenant=`); Pages `/settings` bearer path unchanged; analytics reads and browser-access sections split collector vs keyed CORS.

## Checks

**Before:**

```
rg -n 'no user identity|WORKFLOW_SERVE_KEYS=tenant|workflow login.*not built' docs/design/05-distribution.md docs/design/07-analytics-site.md
docs/design/05-distribution.md:57:- Remote mode is opted into with `workflow login` (not built yet), ...

rg -n 'GitHub|session|/login|workflow_session' docs/design/05-distribution.md docs/design/07-analytics-site.md
(no collector-login substance; only release GitHub and "session by normalised query" cache line in 07)
```

**After:**

```
rg -n 'no user identity|WORKFLOW_SERVE_KEYS=tenant|workflow login.*not built' docs/design/05-distribution.md docs/design/07-analytics-site.md
(no matches)

rg -n 'GitHub|session|/login|workflow_session' docs/design/05-distribution.md docs/design/07-analytics-site.md
(multiple substantive hits in each file: OAuth env, /login, workflow_session, GET /v1/me)
```

## Deviations

- None from this brief.

## Contract notes

- Docs mention issued bearer tokens on the collector as the client credential; phase 2 implements issuance — consistent with DESIGN.md end state, not new scope in code.
- No contradiction between brief and cited DESIGN bullets.
