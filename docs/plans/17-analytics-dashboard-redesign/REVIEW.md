# Review — analytics dashboard redesign

Terminal review of `docs/plans/17-analytics-dashboard-redesign/` against `packages/yakka-analytics` on `cursor/analytics-dashboard-redesign-ef13`. Independent of the phase builds.

## Verdict

`REMEDIATE` at reviewed SHA `20487dd`.

Post-fix: three mechanical defects are closed in that commit. One high finding is briefed and still stands (`briefs/remediation-01.md`).

## Phase outcomes

| Phase | Assessment |
| --- | --- |
| 1 — Session gate | partial |
| 2 — Analysis component and style system | met |
| 3 — Aggregation boundary | met |
| 4 — Landing trend view | met |
| 5 — Interactive analysis | met |

Evidence is the tree at `20487dd`, `npm test` (250 passed), and Playwright (`analysis-shell`, `shell`, `overview`, `session`, `investigation-shell`, `investigation-tools`: 33 passed). `packages/yakka/internal/serve` and `packages/yakka/internal/store` are unchanged from `master`.

### Phase 1 — partial

`decideAfterMeFetch` and `shouldNavigateToProfile` match the document-load cases. `tests/e2e/session.spec.ts` covers loopback empty-base stay, 401 with no bearer to `/login?return=`, bearer stay, `/settings` stay, `?tenant=` from `GET /v1/me`, and 403 `no such tenant` only when me has no tenant. `+layout.ts` is `ssr = false`.

The guard the outcome names does not hold for the shell the package renders. The layout effect fetches `GET /v1/me` once and does not track pathname. The header on `/login` links to `/`, so a logged-out person stays in the shell after that click. `finishSessionGate` runs even when the decision is login, so a direct `/` can mount `LandingView` and start analytics before `goto` finishes. The session spec that asserts no analytics opens `/usage`, now a stub that does not fetch. Brief: `briefs/remediation-01.md`.

### Phase 2 — met

Logged-in `/` and `/login` share computed `--bg` and `--text`. That background is neither `#002b36` nor `#fdf6e3`. `/profile`, `/settings`, `/device`, and `/oauth/callback` use `IdentityPanel` on the same tokens (`analysis-shell.spec.ts`, `shell.spec.ts`). The chart frame is `src/lib/analysis/chart-frame/` and does not mount `EChart.svelte`. Solarized hexes remain only under `[data-legacy-theme]` in `theme.css`; the layout does not set that attribute.

"The report nav stays in the shell" was the in-phase guard so the old reports stayed reachable until phase 5. Phase 5 removes that nav. At this SHA the header is Overview, Profile, and Settings, which is the phase 5 outcome, not a phase 2 miss.

### Phase 3 — met

`aggregate()` returns one result for `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, and `executions`, including `partial`, `ignored_filters`, and `truncated` when the read produced them, and `clamp` for the 399-day rest clamp and the 400-bucket cap. Callers pass an `AggregateRequest`. They do not name `/v1/analytics/*` or `baselines` in that request. `aggregate.test.ts` (13) passes. No analytics route was added under `packages/yakka/internal/serve`.

### Phase 4 — met

Empty `/` loads two `ask: trend` results, `hook_events` and `cost_usd`, bucket `day`, window `{ tz }` only (the thirty-day default). Both charts are `TrendChart`, not `EChart.svelte`. The nine KPI tiles and the weekday-by-hour heatmap are absent (`overview.spec.ts`).

### Phase 5 — met

Empty `/` stays the landing. "Open analysis" goes to `/?ask=trend` on `hook_events` and `day`, and the shell also draws `cost_usd` for that shape. Brush, preset, drill, and shift-click exclude update the URL and refetch. `__other__` is not a filter. A `conversation_id` exclude shows `notice-ignored`. A pasted URL reproduces ask, window, and filters. Usage shows unpriced cost as `unpriced`. Quality shows the design window beside the baseline. Conversation `c5` marks in-window events. Save, then open by name, restores ask and window on `/`. The eleven legacy paths render `legacy-route-stub`. The report nav is gone (`investigation-shell.spec.ts`, `investigation-tools.spec.ts`, `shell.spec.ts`).

At review, three outcome gaps in that picture were fixed in `20487dd` (quality series window, score-band placement, one histogram per model). They are the resolved findings below.

## Findings

### Blocker

None.

### High

1. **Logged-out client navigation still mounts the dashboard.** The document-load predicate is right. The layout does not re-check it on pathname change, and it marks the gate ready before `goto` finishes, so `/` can start analytics and Overview from `/login` stays in the shell. **Briefed:** `briefs/remediation-01.md`. Inside `packages/yakka-analytics`. Not architectural.

2. **Quality score series did not draw for a preset window.** `QualityTool` took `from`/`to` off the URL. A preset (`range=7d`, or the landing handoff) has neither, so `QualityChart` never mounted and a missing bucket could not show as a gap. **Resolved in review** (`20487dd`): the chart uses the boundary result's resolved `window`. `quality-window.test.ts`.

3. **Usage distribution drew one model.** With `dim=model` the server returns one row per model and no `k=all` row. `distData` kept a single bin list (the `all` row, or the first row with bins), so the distribution was not model against model. **Resolved in review** (`20487dd`): one histogram per row that has bins, under `investigation-usage-distribution`. `usage-distribution.test.ts`. The distribution e2e still passes.

### Medium

4. **The quality score band was stacked from zero.** `qualityOption` stacked `median - p25` and `p75 - median`, so the shaded band sat on the axis instead of from p25 to p75. The median line and the null gap were already right. **Resolved in review** (`20487dd`): transparent `p25` baseline plus a `p75 - p25` span, same stacking as `src/lib/charts/score-series.ts`. Asserted in `chart-frame.test.ts`.

5. **Executions over time fetches and draws nothing.** The investigation dim select commits `ask: executions`, and `aggregate` runs, but the shell template only renders trend and breakdown charts. **Follow-up.** Inside the package. Not architectural.

6. **The package e2e suite is not green.** `area.spec.ts`, `builder.spec.ts`, `executions.spec.ts`, `filter-bar.spec.ts`, and `hooks.spec.ts` still drive retired reports. `settings.spec.ts` waits for `GET /v1/analytics/summary` and the old summary tiles on `/`. This review did not re-run that full file. **Follow-up.** Inside the package. Not architectural.

### Low

7. **`clamp`, `partial`, and `truncated` are not shown.** The boundary sets them. The shell surfaces `ignored_filters` only, so a clamped window looks complete. **Follow-up.**

8. **Brush buttons are not registered.** Trend and quality options set `toolbox`, and `ChartHost` does not register ECharts `ToolboxComponent`. Drag still works: `armBrush` calls `takeGlobalCursor`, and the brush e2e passed. **Follow-up.**

9. **Design 7 still says each chart has a data-table toggle.** The analysis chart frame has no such toggle. **Follow-up.** Outside `packages/yakka-analytics` (`docs/design/07-analytics-site.md`). Not architectural.

## Intent and ledger

The implementation matches the verbatim intent inside the package: a new analysis shell, a landing of two trends, interactive investigation tools, and a client send to login after the document loads. The login send is incomplete for client navigations off a stay path (finding 1). Repos, hooks, explore, and the twelve-tile grid did not return as tools.

- **Assumption 1** (landing is `hook_events` and `cost_usd`, not the nine KPI tiles): holds.
- **Assumption 2** (repos, hooks, and executions stay breakdowns; explore and the grid do not return): holds. The executions control does not draw (finding 5); that is presentation, not a ledger change.
- **Assumption 3** (loopback with an empty base stays on 401): holds in `decideAfterMeFetch` and in `session.spec.ts`.

## Plan sufficiency

Sufficient. The phase outcomes were enough to judge met or partial and to place every finding. Two sentences were thin and produced findings: the gate is specified as one document-load check, while the shell links from stay paths to `/`; the quality series is specified without saying the chart window is the boundary's resolved window when the URL only has a preset. The distribution sentence says model against model and does not say whether that is one chart or one per model. This review drew one histogram per model row.

## Residual risks

- Finding 1 until `briefs/remediation-01.md` is done.
- A full `npx playwright test` stays red for the retired-report specs (finding 6), so a later failure in those files is not a new regression signal.
- Conversation `window_totals` stored as whole seconds, and conversation-grain unpriced accounting, stay in `packages/yakka` as the design says. This review did not treat them as package defects.

## Tests

- `npm test` in `packages/yakka-analytics`: 250 passed (26 files), including `chart-frame.test.ts`, `quality-window.test.ts`, `usage-distribution.test.ts`, `aggregate.test.ts`, and `session-gate.test.ts`.
- `npx playwright test` for `analysis-shell`, `shell`, `overview`, `session`, `investigation-shell`, `investigation-tools`: 33 passed.
- Full Playwright file not re-run (finding 6).
