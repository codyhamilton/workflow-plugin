# Brief: 3-05 — Design docs for client login and resolution

Consumer: execute worker dispatched by the plan 13 orchestrator for phase 3.
Owned paths: `docs/design/02-edge-capture.md`, `docs/design/05-distribution.md`, `tools/hooklog/README.md`, `docs/plans/13-client-registration/reports/3-05-design-docs-client-login.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/13-client-registration/reports/3-05-design-docs-client-login.md` and include it in the commit.
Depends on: 3-01, 3-02, 3-04 (read reports for as-built behavior; may start prose after those land).
Runs alongside: 3-03.
Budget: 8 files to read, about 200 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-client-registration/DESIGN.md` — Domain: Client presentation, Phase 3 outcome (doc sentences).
2. `docs/plans/13-client-registration/reports/3-01-clientconfig-env-resolution.md`, `3-02-device-auth-server.md`, `3-04-workflow-login-cli.md` — as-built (read after those units land).
3. `docs/design/02-edge-capture.md` — Config section.
4. `docs/design/05-distribution.md` — Local bootstrap / remote client bullets.
5. `tools/hooklog/README.md` — remote mode paragraph.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Update design 2, design 5, and hooklog README so they describe `workflow login`, env/file resolution, and remote-agent `WORKFLOW_ENDPOINT` + `WORKFLOW_KEY`, and no longer say `workflow login` is unbuilt or that client config is file-only.

## Contract

Cited from `docs/plans/13-client-registration/DESIGN.md`, settled:

**Phase 3 outcome (this unit)**

- "`docs/design/02-edge-capture.md` and `docs/design/05-distribution.md` describe this command and this resolution. `workflow init` is not added."

**Client presentation** (align prose; do not invent scope)

- Resolution order: env pair wins; half-set env is bad; file; local default.
- "`workflow login`" writes `client.toml`; remote agents may use env pair.
- "`WORKFLOW_CLIENT_CONFIG`" overrides file path only.

## Changes

- **02-edge-capture.md**: Replace "not env vars" / registration out of scope with plan 13 resolution and `workflow login`; keep test-only `WORKFLOW_CLIENT_CONFIG`; note `WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` for agents without a file.
- **05-distribution.md**: Remove "later phase" wording for `workflow login`; document command and env override; loopback unchanged.
- **hooklog/README.md**: Remote mode via file or env; `workflow login` built; drop stale `WORKFLOW_SERVE_KEYS` local serve wording if still present.
- **Carried item 1**: docs may note dashboard `tenant` query is still only on overview unless 3-03 report says otherwise — do not claim full-site tenant wiring.
- **Carried item 3**: docs must not claim e2e logs in via OAuth unless reports say global-setup was changed (it was not in scope).

### Keep untouched

- `docs/design/03-remote-service.md` (phase 2 doc unit).
- `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg -n 'not built yet|workflow init' docs/design/02-edge-capture.md docs/design/05-distribution.md tools/hooklog/README.md` → no matches (or only negation that init is not added).
- `rg -n 'WORKFLOW_ENDPOINT|workflow login' docs/design/02-edge-capture.md docs/design/05-distribution.md` → each file mentions both resolution and login.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
