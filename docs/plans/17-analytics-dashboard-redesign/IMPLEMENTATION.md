# Analytics dashboard redesign implementation

Tool: Cursor (Grok 4.7 orchestrator, Composer workers).
Run: https://cursor.com/agents/bc-67f9e02e-c19f-50bd-bd4a-d84165d303e0
Started: 2026-10-20T16:12:52Z

Package boundary: `packages/yakka-analytics`. Phase 1 also amends the Site section of `docs/design/07-analytics-site.md`, which the phase names as a surface.

## Phase 1 — Session gate

Approach: known. One unit: one predicate, and the layout, session client, login return, and overview tenant send share those files. Refine skipped for this phase; the brief is authored inline. Slug from the plan folder `17-analytics-dashboard-redesign`: `analytics-dashboard-redesign`.

Brief: `docs/plans/17-analytics-dashboard-redesign/briefs/1-01-session-gate.md`

`artifact_feedback` on that brief: unreachable. The Yakka MCP namespace failed live tool discovery (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). No check was flagged because the service did not answer.

### 1-01-session-gate

- Built: the document-load gate. One `fetchMe` (`GET /v1/me`) per load, children held until it settles, then the Phase 1 predicate: local empty-base 401 stays, 200 stays and the overview sends `?tenant=` from that body, 401 with a stored bearer and a non-empty base stays, 401 with no bearer otherwise goes to `/login?return=`, `/login`, `/oauth/callback`, and `/settings` stay, and 403 `no such tenant` goes to `/profile` only when me returned no tenant. Login passes a same-origin `return` through `oauthLoginPath`. Design 7 Site states that send.
- Surfaces: `packages/yakka-analytics/src/lib/session-gate.ts`, `src/lib/session-gate.svelte.ts`, `src/routes/+layout.svelte`, `src/routes/+page.svelte`, `src/routes/login/+page.svelte`, `tests/e2e/session.spec.ts`, `tests/e2e/settings.spec.ts`, `tests/e2e/helpers.ts`, `docs/design/07-analytics-site.md`.
- Deviations: the worker reported none. Commit `8967d43`.
- Agent: Composer (`composer-2.5`), subagent `bc-7d3588c0-2b30-5368-b0b5-84fbbfb5fd98`. The harness did not report tool turns or final context.

`artifact_feedback` on the brief and on `reports/1-01-session-gate.md`, before close: unreachable. The Yakka MCP server closed during discovery (`python3: can't open file '/workspace/${CLAUDE_PLUGIN_ROOT}/client/yakka.py': [Errno 2] No such file or directory`). No check was flagged.

### Phase 1 verification

Re-ran the outcome checks after `8967d43`. Reports were not the check.

- `npm test -- src/lib/session-gate.test.ts`: 10 passed.
- `npm test`: 205 passed.
- `npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts`: 11 passed. Empty-base `/v1/me` 401 stayed on `/trends?range=7d`. Non-empty base, no bearer, 401 ended on `/login` with `return` `/usage?range=7d` and no analytics request. Bearer plus non-empty base stayed. `/settings` stayed. Login passed `return` through. 200 sent `tenant=acme` on summary. 403 `no such tenant` with no tenant ended on `/profile`; with a tenant it did not. Clearing the keyed bearer from settings sent `/` to `/login?return=/`.

Outcome holds.

### Carried

None.

## Phase 2 — Analysis component and style system

Tool: Cursor (Grok 4.7 orchestrator, Composer workers).
Run: https://cursor.com/agents/bc-5e66a519-1517-56ff-b425-f01ddf9fadd5
Started: 2026-10-20T16:31:52Z

Approach: open. The invoker declared the normal execute path. The phase outcome in `DESIGN.md` is the fixed yardstick. No iterate lab and no new plan folder. A library may implement the chart frame or the tokens; the design names none. The report nav stays in the shell. Package boundary stays `packages/yakka-analytics`.

Slug from the plan folder `17-analytics-dashboard-redesign`: `analytics-dashboard-redesign`.

No Units list. The phase is more than one worker's work: the shell frame and the chart frame are separate contracts, and `src/lib/charts/` is a few thousand lines the style pass must not absorb. Refine is dispatched. Phase 1 carried: none.

### Refine

Proceed. Two units, sequential. `2-02` depends on `2-01`. Nothing runs alongside. Coarse check of phases 3–5: surfaces and contracts are locatable, outcomes are testable, dependency order holds. No bounce. Commit `ae18144`.

- `2-01` Analysis shell and tokens — `briefs/2-01-analysis-shell.md`
- `2-02` Chart frame — `briefs/2-02-chart-frame.md`

`artifact_feedback` on both briefs: unreachable. Yakka MCP failed live tool discovery (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). The refine worker also reported the `yakka.py` path missing. No check was flagged because the service did not answer.

### 2-01-analysis-shell

- Built: the analysis frame and non-solarized type, color, and space tokens. The document root uses them. Legacy report routes keep the solarized sheet inside a legacy wrapper. `/login`, `/profile`, `/settings`, `/device`, and `/oauth/callback` use the same frame. The report nav stays in the shell.
- Surfaces: `packages/yakka-analytics/src/lib/analysis/`, `src/routes/+layout.svelte`, `src/lib/theme.css`, the identity and login routes, `tests/e2e/analysis-shell.spec.ts`, `tests/e2e/shell.spec.ts`, `docs/design/07-analytics-site.md` Theme.
- Deviations: the worker reported none. Two `shell.spec.ts` cases fail here and on the parent commit `af0b6d2`: `dashboards shares filter chrome` never finds `trends-chart`, and `an ignored-filter notice` never finds `notice-ignored`. Not introduced by this unit.
- Agent: Composer (`composer-2.5`), subagent `bc-10682fdb-8eab-571a-9f73-4246b7b5b6eb`. The harness did not report tool turns or final context. Commit `06ae01d`. Status reported: done with concerns.
- Checked: `npm test` 205 passed. `analysis-shell.spec.ts` 2 passed. `session.spec.ts` passed. Logged-in `/`, `/login`, `/profile`, `/settings`, `/device`, and `/oauth/callback` share computed `--bg` and `--text`, and that background is neither `#002b36` nor `#fdf6e3`. The report nav (Trends, Builder, Dashboards) is in the shell.
