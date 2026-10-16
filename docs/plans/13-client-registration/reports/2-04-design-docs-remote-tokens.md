---
cursor:
  subagentId: "bc-3ac55136-b8f4-5120-9f4c-d7174cae0439"
---

# Report: 2-04 — Design doc for issued remote credentials

**Status:** done

## What changed

- `docs/design/03-remote-service.md`: Configuration and auth prose now describe loopback keyless mode, `WORKFLOW_SERVE_KEYS` refusing startup, remote collector GitHub OAuth env, profile-issued `wk_` bearer tokens (`read` / `read_write`), session-only tenant/token routes, and bearer vs session on `/v1` reads and ingest. API table and ingest errors updated; local drain tenant is always `local`.

## Checks

**Before:**

```
rg -n 'out of scope|WORKFLOW_SERVE_KEYS.*tenant=key|registration.*out of scope' docs/design/03-remote-service.md
57:| `WORKFLOW_SERVE_KEYS` | `tenant=key[,tenant=key…]`; unset or empty means keyless local mode |
61:Registration, key issue and rotation are out of scope. A key maps to exactly one tenant; the client

rg -n 'wk_|issued token|GitHub' docs/design/03-remote-service.md
(no matches)
```

**After:**

```
rg -n 'out of scope|WORKFLOW_SERVE_KEYS.*tenant=key|registration.*out of scope' docs/design/03-remote-service.md
(no matches)

rg -n 'wk_|issued token|GitHub' docs/design/03-remote-service.md
66:- The bind must be loopback; a non-loopback bind without the GitHub OAuth env is refused at startup.
70:**Remote collector mode** is a non-loopback bind with the GitHub OAuth env set. A person signs in
71:with GitHub; the session opens the embedded analytics dashboard and profile ([design
73:Each issued token is plaintext `wk_` plus an unguessable body, belongs to one tenant, has scope
96:| `GET /v1/me` | session | signed-in GitHub identity and owned tenants (collector dashboard) |
```

## Deviations

- None from this brief.

## Contract notes

- No contradiction between brief and cited DESIGN.md bullets. Prose follows 2-01 as-built behavior and aligns with design 5/7 login and browser-access wording already on the branch.
