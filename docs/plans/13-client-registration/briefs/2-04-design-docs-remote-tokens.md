# Brief: 2-04 — Design doc for issued remote credentials

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 2.
Owned paths: `docs/design/03-remote-service.md`, `docs/plans/13-client-registration/reports/2-04-design-docs-remote-tokens.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/2-04-design-docs-remote-tokens.md` and include it in the commit.
Depends on: 2-01 (read reports for actual behavior; may start after 2-01 merges to branch).
Runs alongside: 2-02, 2-03.
Budget: 5 files to read, about 120 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Tenancy and tokens, Domain: Request authorization, Phase 2 outcome (doc sentence).
2. `docs/plans/13-client-registration/reports/2-01-registry-tenancy-bearer.md` — as-built API and env behavior (read after 2-01 lands).
3. `docs/design/03-remote-service.md` — Configuration and auth sections to replace.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Update design doc 3 so it describes GitHub-session profile token issue and bearer authorization on the collector, and no longer says registration, key issue, or rotation are out of scope.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Phase 2 outcome (this unit)**

- "`docs/design/03-remote-service.md` states this and no longer says registration, key issue, or rotation are out of scope."

Align prose with plan 13 contracts (do not invent endpoints):

- Remote collector uses OAuth env + issued `wk_` tokens, not `WORKFLOW_SERVE_KEYS`.
- Local loopback stays keyless; `WORKFLOW_SERVE_KEYS` non-empty refuses startup.
- Bearer `read` vs `read_write`; session for dashboard; profile routes session-only.

## Changes

- Replace or extend the "Configuration" and auth tables in `03-remote-service.md` to match implemented behavior.
- Remove "Registration, key issue and rotation are out of scope" and the env-only `WORKFLOW_SERVE_KEYS` tenant=key model as the remote credential.
- Cross-link to plan 13 or design 5/7 only where existing doc already links; no new scope.

### Keep untouched

- `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` (explicit non-goals in plan 13).
- Other design docs except necessary one-line cross-refs.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg -n 'out of scope|WORKFLOW_SERVE_KEYS.*tenant=key|registration.*out of scope' docs/design/03-remote-service.md` → no matches for the retired phrases (or only historical negation in a "replaced by" note you add).
- `rg -n 'wk_|issued token|GitHub' docs/design/03-remote-service.md` → at least one hit describing issued tokens or profile issue.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
