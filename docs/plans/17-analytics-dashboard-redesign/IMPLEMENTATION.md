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

### 2-02-chart-frame

- Built: a presentational chart frame under `src/lib/analysis/chart-frame/` for trend, breakdown, distribution, and quality. It reads analysis tokens, exposes hover, brush-end, and drill callbacks, and does not fetch. The worker chose Apache ECharts 6 (`echarts/core`) inside a new host. It does not import `src/lib/charts/` or mount `EChart.svelte`. The design names no library.
- Surfaces: `packages/yakka-analytics/src/lib/analysis/chart-frame/`, `src/lib/analysis/chart-frame.test.ts`.
- Deviations: the worker reported none.
- Agent: Composer (`composer-2.5`), subagent `bc-046de867-8a40-56a1-9a72-49daf92cef94`. The harness did not report tool turns or final context. Commit `a72034e`. Status reported: done.

`artifact_feedback` on `briefs/2-01-analysis-shell.md`, `briefs/2-02-chart-frame.md`, `reports/2-01-analysis-shell.md`, and `reports/2-02-chart-frame.md`, before close: unreachable. Yakka MCP failed live tool discovery again (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). No check was flagged.

### Phase 2 verification

Re-ran the outcome checks on `a72034e`. Reports were not the check.

- `npm test -- src/lib/analysis/chart-frame`: 8 passed.
- `npm test`: 213 passed.
- No import of `src/lib/charts/`, `api.ts`, or `query.ts`, and no `#002b36`, `#fdf6e3`, `#839496`, or `#657b83`, under `src/lib/analysis/chart-frame/`.
- `npx playwright test tests/e2e/analysis-shell.spec.ts`: 2 passed. Logged-in `/` and `/login` share `--bg` and `--text`. That background is neither `#002b36` nor `#fdf6e3`.
- The same computed `--bg` and `--text` on `/profile`, `/settings`, `/device`, and `/oauth/callback`. The shell still shows the report nav (Trends, Builder, Dashboards).

Outcome holds. Package boundary stayed `packages/yakka-analytics`, plus the Theme paragraph of `docs/design/07-analytics-site.md`.

### Carried

1. `tests/e2e/shell.spec.ts` "dashboards shares filter chrome" does not find `trends-chart`, and "an ignored-filter notice" does not find `notice-ignored`. Both fail on `af0b6d2`, before this phase, and on this phase's tree. No brief amendment.

## Phase 3 — Aggregation boundary

Tool: Cursor (Grok 4.7 orchestrator, Composer workers).
Run: https://cursor.com/agents/bc-ad411c4d-fde0-5ee0-9581-8daae98ee890
Started: 2026-10-20T16:55:14.686Z

Approach: known. One unit: one request, one result, and every ask shares that module. Refine skipped; the brief is authored inline. Slug from the plan folder `17-analytics-dashboard-redesign`: `analytics-dashboard-redesign`.

Phase 2 carried item is not absorbed here. The two `shell.spec.ts` failures predate this phase and do not touch the aggregation contract, the package boundary, or this phase's outcome. They stay carried.

Package boundary stays `packages/yakka-analytics`. This phase adds no analytics route under `packages/yakka/internal/serve` and no table under `packages/yakka/internal/store`.

Brief: `docs/plans/17-analytics-dashboard-redesign/briefs/3-01-aggregation-boundary.md`

`artifact_feedback` on that brief: unreachable. The Yakka MCP namespace failed live tool discovery (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). No check was flagged because the service did not answer.

### 3-01-aggregation-boundary

- Built: `aggregate(request, options?)`. One call returns one result for `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, and `executions`. The caller passes the request and does not name `/v1/analytics/*` or `baselines`. Window, exclude-as-complement, `clamp` (`rest-days`, `bucket-cap`), `controls`, and `partial` / `ignored_filters` / `truncated` when a read produced them are on that result. The Data layer bullet now says landing and analysis read through this boundary.
- Surfaces: `packages/yakka-analytics/src/lib/aggregate.ts`, `src/lib/aggregate.test.ts`, `docs/design/07-analytics-site.md` Data layer.
- Deviations: the worker reported none. Commit `2462715`.
- Agent: Composer (`composer-2.5`), subagent `bc-16caa26d-1590-5dd5-a87e-8d0b23d46e38`. The harness did not report tool turns or final context. Status reported: done.

`artifact_feedback` on `briefs/3-01-aggregation-boundary.md` and `reports/3-01-aggregation-boundary.md`, before close: unreachable. Yakka MCP failed live tool discovery again (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). No check was flagged.

### Phase 3 verification

Re-ran the outcome checks on `2462715`. Reports were not the check.

- `npm test -- src/lib/aggregate.test.ts`: 13 passed. One call per ask (`trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, `executions`) returned that ask's slice. `partial`, `ignored_filters`, and `truncated` were present when the fake read returned them. A `conversation_id` exclude was listed in `ignored_filters` and was not sent. A rest span wider than 399 days set `clamp` `rest-days` and a different window. An hour bucket over the 400 cap set `clamp` `bucket-cap` and did not call the query read. An omitted range was thirty days ending at the injected now. `tenant` was sent only when the request carried it. The `aggregate` arguments in those calls do not name `/v1/analytics/*` or `baselines`.
- `npm test`: 226 passed.
- `git diff --name-only e717a8d..2462715` has no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

Outcome holds. Package boundary stayed `packages/yakka-analytics`, plus the Data layer bullet of `docs/design/07-analytics-site.md`.

### Carried

1. `tests/e2e/shell.spec.ts` "dashboards shares filter chrome" does not find `trends-chart`, and "an ignored-filter notice" does not find `notice-ignored`. Both fail on `af0b6d2`, before phase 2, and on this phase's tree. No brief amendment.
2. `src/lib/aggregate.ts` calls `unionMeta` with a `Conversations` value and an `Executions` value. `tsc --noEmit` reports TS2559: those types share no properties with `MetaFields`. `aggregate.test.ts` builds a `ConversationDetail` whose `totals` includes `hook_events` (TS2353). `npm test` does not typecheck, and those tests pass. Design 7 records that `svelte-check` is not installed. No brief amendment.

## Phase 4 — Landing trend view

Tool: Cursor (Grok 4.7 orchestrator, Composer workers).
Run: https://cursor.com/agents/bc-acee832e-e24a-5847-9bc4-bee3e19a322f
Started: 2026-10-20T17:10:42Z

Approach: known. One unit: one route and one picture. The chart frame and the aggregation boundary already exist. Refine skipped; the brief is authored inline. Slug from the plan folder `17-analytics-dashboard-redesign`: `analytics-dashboard-redesign`.

Phase 3 carried items are not absorbed here. The two `shell.spec.ts` failures predate phase 2 and do not touch this phase's outcome. The `aggregate.ts` type errors are in a module this phase calls and does not edit. They stay carried. No brief amendment. No bounce.

Package boundary stays `packages/yakka-analytics`. Assumption 1 stands: two `ask: trend` results, measures `hook_events` and `cost_usd`, same window and bucket. The investigation control is phase 5.

Brief: `docs/plans/17-analytics-dashboard-redesign/briefs/4-01-landing-trend.md`

`artifact_feedback` on that brief: unreachable. The Yakka MCP namespace failed live tool discovery (`This MCP server failed during live tool discovery. Its tools are unavailable until the connection is fixed.`). The server closed during discovery (`python3: can't open file '/workspace/${CLAUDE_PLUGIN_ROOT}/client/yakka.py': [Errno 2] No such file or directory`). No check was flagged because the service did not answer.

### 4-01-landing-trend

- Built: `/` with an empty query loads two sequential `aggregate` `ask: trend` results, measures `hook_events` and `cost_usd`, bucket `day`, window `{ tz }` only, and draws them with `TrendChart`. The nine KPI tiles, grouped counts, and weekday-by-hour heatmap are gone. The route row and the overview KPI link sentences in design 7 match that picture.
- Surfaces: `packages/yakka-analytics/src/routes/+page.svelte`, `tests/e2e/overview.spec.ts`, `tests/e2e/session.spec.ts`, `tests/e2e/explore.spec.ts`, `tests/hosted/hosted.spec.ts`, `docs/design/07-analytics-site.md`.
- Deviations: `overview.spec.ts` and the Perspective test in `explore.spec.ts` set the local serve base in a second `addInitScript`, because `useServe` stringifies its argument into `http://127.0.0.1:<port>,,e2e-local-stay`. `helpers.ts` was left untouched. The collector session test fulfills `analytics/facets` and `analytics/query` so the charts can render. Commit `c4d8a94`.
- Agent: Composer (`composer-2.5`), subagent `bc-75ed486e-12a4-5d7a-911f-c65391f908ff`. The harness did not report tool turns or final context. Status reported: done with concerns.

Orchestrator re-run after `c4d8a94`, reports not the check:

- `npm test`: 226 passed.
- `npx playwright test tests/e2e/overview.spec.ts tests/e2e/session.spec.ts tests/e2e/explore.spec.ts`: overview 2 passed. The two landing charts are visible and `data-ready`, the old overview test ids are absent, and the two `analytics/query` requests are `hook_events` and `cost_usd`, `bucket=day`, the same `from` and `to`, 30 days apart, with no `repo_id`. Session: 8 passed, 1 failed. `no tenant: summary 403 no such tenant sends to /profile` stayed on `/`. That test still fulfills only `analytics/summary`. `/` now calls `analytics/facets` (the log is `404 GET /v1/analytics/facets`). `explore.spec.ts`: the Perspective test passed; the other four failed. The page fetch URL was `http://127.0.0.1:39721,,e2e-local-stay/v1/analytics/explore`. `helpers.ts` is unchanged since `8967d43`.
- `src/routes/+page.svelte` does not import `$lib/charts/` or `EChart.svelte` and does not call `getJSON`. `git diff --name-only c61f1a9..c4d8a94` has no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

The session 403 test is this phase's break. A fixer follows. The explore failures stay carried: `useServe` predates this phase.

Brief: `docs/plans/17-analytics-dashboard-redesign/briefs/4-02-session-403.md`

`artifact_feedback` on that brief: unreachable. Same Yakka MCP discovery failure (`python3: can't open file '/workspace/${CLAUDE_PLUGIN_ROOT}/client/yakka.py': [Errno 2] No such file or directory`). No check was flagged.

### 4-02-session-403

- Built: the two `no such tenant` session tests fulfill `**/v1/analytics/**` with 403 `{ error: 'no such tenant' }`. No tenant ends on `/profile`. A tenant stays on `/` after an analytics request is seen. The landing source was not edited.
- Surfaces: `packages/yakka-analytics/tests/e2e/session.spec.ts`.
- Deviations: none. Commit `63effc0`.
- Agent: Composer (`composer-2.5`), subagent `bc-38ee4899-c7c2-51ca-a98b-2f813d017021`. The harness did not report tool turns or final context. Status reported: done.

`artifact_feedback` on `briefs/4-01-landing-trend.md`, `briefs/4-02-session-403.md`, `reports/4-01-landing-trend.md`, and `reports/4-02-session-403.md`, before close: unreachable. Yakka MCP failed live tool discovery again (`python3: can't open file '/workspace/${CLAUDE_PLUGIN_ROOT}/client/yakka.py': [Errno 2] No such file or directory`). No check was flagged.

### Phase 4 verification

Re-ran the outcome checks on `63effc0`. Reports were not the check.

- `npx playwright test tests/e2e/overview.spec.ts tests/e2e/session.spec.ts`: 12 passed. Empty `/` shows `landing-trend-hook_events` and `landing-trend-cost_usd`, both `data-ready`. `overview-summary`, `overview-heatmap`, and `summary-conversations` are absent. The two `analytics/query` requests are measures `hook_events` and `cost_usd`, `bucket=day`, the same `from` and `to`, thirty days apart, with no `repo_id`. `/?repo_id=r1` still shows those charts and does not send `repo_id`. No tenant plus 403 `no such tenant` on the landing analytics read ends on `/profile`. A tenant stays on `/` after that read.
- `npm test` on `c4d8a94`: 226 passed. The fixer did not change package source.
- `src/routes/+page.svelte` imports `TrendChart` from `$lib/analysis/chart-frame`. It does not import `$lib/charts/` or `EChart.svelte` and does not call `getJSON`.
- `git diff --name-only c61f1a9..63effc0` has no path under `packages/yakka/internal/serve` or `packages/yakka/internal/store`.

Outcome holds. Package boundary stayed `packages/yakka-analytics`, plus the `/` route row and the overview-link sentences of `docs/design/07-analytics-site.md`.

### Carried

1. `tests/e2e/shell.spec.ts` "dashboards shares filter chrome" does not find `trends-chart`, and "an ignored-filter notice" does not find `notice-ignored`. Both fail on `af0b6d2`, before phase 2, and on this phase's tree. No brief amendment.
2. `src/lib/aggregate.ts` calls `unionMeta` with a `Conversations` value and an `Executions` value. `tsc --noEmit` reports TS2559: those types share no properties with `MetaFields`. `aggregate.test.ts` builds a `ConversationDetail` whose `totals` includes `hook_events` (TS2353). `npm test` does not typecheck, and those tests pass. Design 7 records that `svelte-check` is not installed. No brief amendment.
3. `tests/e2e/helpers.ts` `useServe` passes a nested array into `addInitScript`, so the local base is stored as `http://127.0.0.1:<port>,,e2e-local-stay`. The file is unchanged since `8967d43`. Four `explore.spec.ts` cases fail on that URL. `overview.spec.ts` and `the overview does not load Perspective` set the base again in a second init script. No brief amendment.

## Phase 5 — Interactive analysis

Tool: Cursor (Grok 4.7 orchestrator, Composer workers).
Run: https://cursor.com/agents/bc-049ba4b3-b0be-5f30-abcb-1c19ee983f58
Started: 2026-10-20T17:38:12Z

Approach: open. The invoker declared the normal execute path. The phase outcome in `DESIGN.md` is the fixed yardstick. No iterate lab and no new plan folder. Assumption 2 stands: repos, hooks, and execution shape stay as breakdowns inside the investigation; explore and the twelve-tile grid do not return as tools. Package boundary stays `packages/yakka-analytics`.

Slug from the plan folder `17-analytics-dashboard-redesign`: `analytics-dashboard-redesign`.

No Units list. The phase is more than one worker's work: the investigation path, the four tools (usage and cost, quality, conversation grain, saved analysis), and the removal of the old report routes and nav are separate contracts on a surface one worker cannot hold. Refine is dispatched. Phase 4's Carried section is for that refinement to place.

### Refine

Proceed. Four units, sequential. `5-02` depends on `5-01`, `5-03` on `5-02`, `5-04` on `5-03`. Nothing runs alongside: they share `+page.svelte` and the shell wiring. No bounce. Commit `004b2f0`.

- `5-01` Investigation URL codec — `briefs/5-01-investigation-url.md`
- `5-02` Investigation shell and landing handoff — `briefs/5-02-investigation-shell.md`
- `5-03` Exploration tools — `briefs/5-03-exploration-tools.md`
- `5-04` Legacy routes and shell retirement — `briefs/5-04-legacy-retirement.md`

Phase 4 carried items placed by that refinement:

1. `shell.spec.ts` "dashboards shares filter chrome" and "an ignored-filter notice" — absorbed into `5-04`.
2. `aggregate.ts` / `aggregate.test.ts` `tsc` issues — absorbed into `5-01` as type-only, no behaviour change.
3. `helpers.ts` `useServe` nested-array URL — absorbed into `5-04`.

`artifact_feedback` on the four briefs: unreachable. Yakka and Workflow MCP failed live tool discovery (`artifact_feedback` not callable; `python3: can't open file '/workspace/${CLAUDE_PLUGIN_ROOT}/client/yakka.py': [Errno 2] No such file or directory`). The refine worker reported the same. No check was flagged because the service did not answer.

Agent: Composer (`composer-2.5`), subagent `bc-1ecdd64c-9ef8-557a-aedd-e2a8d62e6229`. The harness did not report tool turns or final context.
