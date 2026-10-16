# Brief: 1-04 — Design docs for login and admission

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 1.
Owned paths: `docs/design/05-distribution.md`, `docs/design/07-analytics-site.md`, `docs/plans/13-client-registration/reports/1-04-design-docs-login.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/1-04-design-docs-login.md` and include it in the commit.
Depends on: 1-02, 1-03.
Runs alongside: nothing (after 1-03 lands).
Budget: 6 files to read, about 120 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Phase 1 outcome (last clause on docs), Solution Shape, Domain: Identity and admission, Domain: Request authorization (collector site bullet).
2. `docs/design/05-distribution.md` — remote serve and `workflow login` mentions.
3. `docs/design/07-analytics-site.md` — Shape, `/settings`, identity line.
4. `docs/plans/13-client-registration/reports/1-02-oauth-session-remote-auth.md` and `1-03-analytics-session-site.md` — what actually shipped.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Bring design docs 05 and 07 in line with phase 1: the collector has GitHub login and session-backed dashboard reads; loopback stays keyless; env `WORKFLOW_SERVE_KEYS` is rejected on the collector path.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

- Phase 1 outcome: "`docs/design/05-distribution.md` and `docs/design/07-analytics-site.md` describe this login and no longer say the dashboard has no user identity."
- Architectural Implications: "`workflow login` (not built yet)" becomes the device path in later phases; phase 1 still documents dashboard session login on the collector.
- Request authorization: collector-origin site uses session cookie, not pasted bearer; Pages `/settings` keeps pasted bearer.

Do not document phase 2 token APIs or fly.io (phase 4) beyond a forward pointer if already present.

## Changes

- **05-distribution.md**: State that remote collector mode uses GitHub OAuth env vars, not `WORKFLOW_SERVE_KEYS`; loopback local mode unchanged; `workflow login` remains future for device tokens (phase 3).
- **07-analytics-site.md**: Replace "no user identity" with collector session login (`/login`, `/oauth/login`, cookie-backed same-origin reads, `GET /v1/me` for tenant); keep Cloudflare Pages pasted-token path explicit.

### Keep untouched

- Other design docs (`03-remote-service.md` is phase 2).
- Plan folder `DESIGN.md` / `IMPLEMENTATION.md`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg -n 'no user identity|WORKFLOW_SERVE_KEYS=tenant|workflow login.*not built' docs/design/05-distribution.md docs/design/07-analytics-site.md` → no matches (or only historical quoted context clearly marked superseded).
- `rg -n 'GitHub|session|/login|workflow_session' docs/design/05-distribution.md docs/design/07-analytics-site.md` → at least one substantive mention in each file describing collector login.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
