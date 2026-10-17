# Brief: 4-01 — Fly collector manifest

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 4.
Owned paths: `fly.toml`, `Dockerfile`, `.dockerignore`, `docs/plans/13-client-registration/reports/4-01-fly-collector-manifest.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/4-01-fly-collector-manifest.md` and include it in the commit.
Depends on: Phase 2 (code as on branch; no phase 3 requirement).
Runs alongside: nothing.
Budget: 8 files to read, about 200 lines to add, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Collector hosting; Phase 4 outcome and surfaces.
2. `tools/release/build.sh` — how the embedded analytics bundle is produced before `go build`.
3. `tools/workflow/go.mod` — Go version (`go 1.27.1`).
4. `tools/workflow/internal/serve/serve.go` — `ConfigFromEnv` (OAuth trio, `WORKFLOW_SERVE_KEYS` refusal, `WORKFLOW_SERVE_DATA`, `WORKFLOW_SERVE_ADDR`, `WORKFLOW_SERVE_CORS_ORIGINS`).
5. `docs/design/07-analytics-site.md` — Hosting section (embed path, Pages + CORS operator note).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Add a fly.io deployment manifest and container build so one machine can run `workflow serve` as the remote collector with a persistent data volume and no `WORKFLOW_SERVE_KEYS`.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Domain: Collector hosting**

- "One fly.io machine runs the `workflow serve` binary as app `yakka`. A volume holds `WORKFLOW_SERVE_DATA`. The public origin is `https://yakka.build`. The GitHub OAuth app's callback is `https://yakka.build/oauth/callback`, and `WORKFLOW_PUBLIC_URL` is that origin. `WORKFLOW_SERVE_KEYS` is unset. The GitHub client id and secret are fly secrets, not files in the repo. The product, CLI, and packages stay `workflow`. The Fly app name is `yakka`."
- "Cloudflare Pages, if still used, remains a static site that sends a pasted bearer from `/settings`. It does not receive the session cookie. The fly app sets `WORKFLOW_SERVE_CORS_ORIGINS` to that Pages origin. Credentialed CORS stays off."
- Non-goals: "more than one machine; putting the fact ledger on anything other than the volume's tenant directories."

**Phase 4 surfaces (this unit)**

- `new fly.toml` (and the container build it references).

## Changes

- Add **`fly.toml`** at the repo root for a **single** machine app: HTTP service on the port the process binds, **one** mounted volume at the path used as `WORKFLOW_SERVE_DATA`, `primary_region` chosen explicitly. Do **not** set `WORKFLOW_SERVE_KEYS`. Document in the report which env vars are set in the manifest vs fly secrets vs operator `fly secrets set`.
- Set non-secret env in the manifest where appropriate: `WORKFLOW_SERVE_ADDR` listening on `0.0.0.0:<internal_port>` matching fly's `internal_port`; `WORKFLOW_PUBLIC_URL` is `https://yakka.build` (no path). `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` are fly secrets, never committed values or placeholders. `WORKFLOW_SERVE_CORS_ORIGINS` stays unset until the real Pages origin is known (exact origin, no wildcard, no placeholder).
- Add **`Dockerfile`** (multi-stage): build `packages/workflow-analytics` into `tools/workflow/internal/serve/site/` the same way `build.sh` does, then `CGO_ENABLED=0` build `tools/workflow/cmd/workflow`; runtime image runs `workflow serve` (or the binary with equivalent entrypoint). Use `GOTOOLCHAIN=auto` when the host Go is older than `go.mod`.
- Add **`.dockerignore`** to keep the image build bounded (exclude unrelated large trees).
- The report must list: volume name and mount path, internal port, app name, and a **secrets checklist** (`GITHUB_OAUTH_CLIENT_SECRET` at minimum; never commit secrets).

### Keep untouched

- Application Go/TS code (`tools/workflow/internal/serve/*`, analytics package) — hosting only.
- **Carried item 2 (`Server.New` panic)**: do not change registry open/persist behavior.
- **Carried items 1, 3, 4**: no analytics route or e2e changes; no profile/device UI.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `docker build -f Dockerfile .` from repo root (with `GOTOOLCHAIN=auto` in build if needed) → image builds successfully; log shows analytics bundle copied before `go build`.
- `grep -n WORKFLOW_SERVE_KEYS fly.toml Dockerfile` → no assignment of a non-empty `WORKFLOW_SERVE_KEYS`.
- `flyctl config validate` (or `fly config validate`) on `fly.toml` → succeeds when flyctl is installed; if flyctl is missing, report `blocked` with install note and still pass docker build.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
