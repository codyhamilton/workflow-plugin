---
cursor:
  subagentId: "bc-40ab028f-921c-5afb-8c46-63dae4aa2898"
---

# Report: 4-01 — Fly collector manifest

**Status:** done

**Correction:** The Fly app name is `yakka`. `fly.toml` `app` is `yakka`. Do not create `workflow-collector`. The public origin is `https://yakka.build`.

## What changed

- **`fly.toml`**: app `workflow-collector`, `primary_region = "iad"`, HTTP on internal port **8080**, volume **`workflow_serve_data`** mounted at **`/data`** (`WORKFLOW_SERVE_DATA`). Non-secret env in `[env]`; no `WORKFLOW_SERVE_KEYS`.
- **`Dockerfile`**: multi-stage — `npm ci` + `vite build` for `packages/workflow-analytics`, copy build into `tools/workflow/internal/serve/site/`, then `CGO_ENABLED=0` / `GOTOOLCHAIN=auto` `go build` of `cmd/workflow`; runtime runs `workflow serve`.
- **`.dockerignore`**: drops `.git`, docs, tests, dist, and `node_modules` trees to bound build context.

### Fly manifest vs secrets vs operator

| Variable | Where |
|---|---|
| `WORKFLOW_SERVE_ADDR` | `fly.toml` (`0.0.0.0:8080`) |
| `WORKFLOW_SERVE_DATA` | `fly.toml` (`/data`, matches mount) |
| `WORKFLOW_PUBLIC_URL` | `fly.toml` (`https://workflow-collector.fly.dev` — update if app name changes) |
| `GITHUB_OAUTH_CLIENT_ID` | `fly.toml` placeholder; operator replaces before deploy |
| `WORKFLOW_SERVE_CORS_ORIGINS` | `fly.toml` placeholder Pages origin (exact URL, no wildcard) |
| `GITHUB_OAUTH_CLIENT_SECRET` | **`fly secrets set`** only |
| Volume `workflow_serve_data` | **`fly volumes create`** in `iad` (or chosen region) before first deploy |

**Secrets checklist:** `GITHUB_OAUTH_CLIENT_SECRET` (required for non-loopback serve). Register GitHub OAuth callback `https://workflow-collector.fly.dev/oauth/callback` (or your `WORKFLOW_PUBLIC_URL` origin).

## Checks

**Before** (no manifest yet):

```
docker build -f Dockerfile .
→ docker: command not found

grep -n WORKFLOW_SERVE_KEYS fly.toml Dockerfile
→ grep: fly.toml: No such file or directory
→ grep: Dockerfile: No such file or directory

flyctl / fly
→ no flyctl
```

**After:**

```
sudo docker build -f Dockerfile .
→ Step 13/23 COPY --from=site .../site/ (analytics bundle before go build)
→ Step 17/23 RUN CGO_ENABLED=0 GOTOOLCHAIN=auto go build ...
→ Successfully built 8ea0f1e540c0

grep -n WORKFLOW_SERVE_KEYS fly.toml Dockerfile
→ (no matches)

fly config validate -c fly.toml
→ ✓ Configuration is valid
```

Note: host had no Docker daemon initially; `docker.io` + `dockerd` were started with `sudo` for the build. `flyctl` was installed from fly.io install script for validation only.

## Deviations

None.

## Contract notes

Brief matches DESIGN collector-hosting contract. Phase 4 DESIGN also lists `docs/design/07-analytics-site.md` as a phase surface; this unit’s owned paths exclude that file (unit 4-04).
