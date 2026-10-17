# Brief: 4-02 — Fly collector deploy

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 4.
Owned paths: `docs/plans/13-client-registration/reports/4-02-fly-collector-deploy.md` only. Touch nothing else unless the orchestrator authorizes a one-line fix to `fly.toml` from 4-01 when deploy fails for a manifest typo.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title (report-only commit is fine).
Report: before committing, write `docs/plans/13-client-registration/reports/4-02-fly-collector-deploy.md` and include it in the commit.
Depends on: 4-01.
Runs alongside: nothing.
Budget: 6 files to read, about 30 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Collector hosting; Phase 4 outcome (public https origin, OAuth callback path, `WORKFLOW_SERVE_KEYS` unset).
2. `docs/plans/13-client-registration/reports/4-01-fly-collector-manifest.md` — app name, volume, ports, env vs secrets split.
3. `fly.toml` — as committed by 4-01.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Deploy the collector to fly.io so the app's public `https` origin is live, GitHub OAuth callback URL can be registered, and unit 4-03 can verify persistence and CORS on that host.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- "The public origin is `https://yakka.build`. The GitHub OAuth app's callback is `https://yakka.build/oauth/callback`, and `WORKFLOW_PUBLIC_URL` is that origin."
- "`WORKFLOW_SERVE_KEYS` is unset."
- Phase 4 outcome: "The fly app `yakka` serves `https://yakka.build`. That origin answers `GET /v1/health` with no bearer and `GET /oauth/login` with a redirect to GitHub. The OAuth app callback is `https://yakka.build/oauth/callback`."

Identity and admission (for operator setup only): authorize URL uses scopes `read:user` and `user:email` (design Domain: Identity and admission).

## Changes

- Ensure fly.io auth and org access for this worker (or report `blocked` if credentials are unavailable).
- Create or attach the fly app from 4-01; provision the volume if not already present.
- The public origin is `https://yakka.build`. The Fly app name is `yakka`. Do not treat `https://yakka.fly.dev` as the origin to prove.
- Set fly secrets from credentials already present in the environment or on an existing Fly app: `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET`. Never write either value into the repo, a commit, or a log. If either value is missing, do not invent it and do not deploy.
- `WORKFLOW_PUBLIC_URL` is `https://yakka.build` in `fly.toml`. Confirm **`WORKFLOW_SERVE_KEYS` is not set** on the app (`fly secrets list` / `fly config env`).
- The GitHub OAuth app **Authorization callback URL** is already `https://yakka.build/oauth/callback`. Do not register a different callback.
- Run **`fly deploy`** (or equivalent) until the release is healthy, and only when both OAuth values are real.
- Hand off in the report: public origin URL, fly app name, volume id, Pages origin used (or to be used) for `WORKFLOW_SERVE_CORS_ORIGINS`, and whether GitHub OAuth app id matches deploy env.

### Keep untouched

- Product source trees; no code changes except manifest typo fix per owned-path rule.
- **Carried items 1–4**: out of scope.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `curl -sS -o /dev/null -w '%{http_code}' https://yakka.build/v1/health` → `200`.
- `curl -sS -D - -o /dev/null https://yakka.build/oauth/login` → `302` or `303` with `Location` starting with `https://github.com/login/oauth/authorize` and `redirect_uri` containing `https://yakka.build/oauth/callback`.
- `fly secrets list` (or config) shows **no** `WORKFLOW_SERVE_KEYS` with a non-empty value.

If deploy cannot complete in this run, status `blocked`, record partial progress, and leave enough detail for 4-03 to resume.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
