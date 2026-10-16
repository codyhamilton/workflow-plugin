# Brief: 4-04 — Design docs for fly hosting

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 4.
Owned paths: `docs/design/07-analytics-site.md`, `docs/plans/13-client-registration/reports/4-04-design-docs-fly-hosting.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/4-04-design-docs-fly-hosting.md` and include it in the commit.
Depends on: 4-01; read `4-02-fly-collector-deploy.md` for the public collector origin when available.
Runs alongside: 4-03.
Budget: 6 files to read, about 80 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Phase 4 outcome (doc sentence); Domain: Collector hosting.
2. `docs/plans/13-client-registration/reports/4-01-fly-collector-manifest.md` and, when present, `4-02-fly-collector-deploy.md`.
3. `docs/design/07-analytics-site.md` — Hosting section and Browser access / `/settings` (Pages path).
4. `docs/plans/13-client-registration/IMPLEMENTATION.md` — Phase 3 **Carried** item 1 (overview-only `tenant`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Update design doc 7 so the Hosting section names the fly.io collector as the remote `workflow serve` host and keeps Cloudflare Pages as the static pasted-token client.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Phase 4 outcome (this unit)**

- "`docs/design/07-analytics-site.md` names this fly collector as the remote host and leaves the Pages pasted-token path as a static client."

**Domain: Collector hosting**

- "One fly.io machine runs the `workflow serve` binary. A volume holds `WORKFLOW_SERVE_DATA`."
- "Cloudflare Pages, if still used, remains a static site that sends a pasted bearer from `/settings`. It does not receive the session cookie. The fly app sets `WORKFLOW_SERVE_CORS_ORIGINS` to that Pages origin."

Do not rewrite `docs/OVERVIEW.md` or `docs/ARCHITECTURE.md` (plan 13 Architectural Implications).

## Changes

- Extend **`docs/design/07-analytics-site.md` Hosting** with fly.io collector deployment: embedded site same-origin on the collector; persistent volume for `WORKFLOW_SERVE_DATA`; GitHub OAuth callback on the collector origin; `WORKFLOW_SERVE_KEYS` not used; operator sets `WORKFLOW_SERVE_CORS_ORIGINS` to the Pages origin for cross-origin bearer reads.
- Name the **remote host** concretely when 4-02 provides a URL; otherwise describe the fly app pattern from `fly.toml` without inventing a hostname.
- Keep the **Pages** path explicit: `/settings` pasted bearer, no session cookie, static `pages_build_output_dir` unchanged.
- **Carried item 1**: if documenting dashboard `tenant` behavior, state that `?tenant=` from `GET /v1/me` is still only wired on the overview (and profile where already true) — do not claim full-site tenant wiring.

### Keep untouched

- Other design docs except necessary one-line cross-links already present.
- `docs/plans/13-client-registration/DESIGN.md` / `IMPLEMENTATION.md`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg -n 'fly\.io|fly\.toml|WORKFLOW_SERVE_DATA' docs/design/07-analytics-site.md` → at least one substantive fly collector hosting mention.
- `rg -n 'Pages|/settings|pasted' docs/design/07-analytics-site.md` → Pages pasted-token path still documented in Hosting or Browser access.
- `rg -n 'no user identity' docs/design/07-analytics-site.md` → no revived "no user identity" for the collector dashboard.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
