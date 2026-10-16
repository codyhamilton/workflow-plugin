# Implementation

- Tool: Cursor
- Session: 93e8d765-46ab-4867-b484-c51b2ec7f579
- Start: 2026-10-16T12:21:49Z
- Branch: plan/14-analytics-ui

## Phase 1 — Solarized shell

### 1-01-solarized-shell

- Built: solarized light and dark tokens, a system/light/dark control stored at `workflow-analytics-theme`, `data-theme` on the document root, chart refresh when that attribute changes, and stylesheet hexes replaced with those tokens. Shell padding and control gaps use the 4/8/16/24/32 scale.
- Surfaces: the files in commit `fb401e4`.
- Deviations: `+layout.svelte` sets `data-theme` from an inline script before hydration, because `app.html` was outside the owned paths and a late effect left the light tokens up through first paint.
- Agent: Composer, agent `6a48cb2a-3ab9-4b1f-ae15-459428a689e3`. The harness did not report turn count or final context size. Status `done`, commit `fb401e4`.

### Verification

Checked against the phase outcome, not the report.

- A scan of `<style>` blocks under `packages/workflow-analytics/src/**/*.svelte` found no hex color.
- `theme.css` and `DEFAULT_TOKENS` (series via `LIGHT_SERIES`) contain only the theme contract's hex values. The series list matches the contract order.
- Shell `padding` and `gap` use `--space-1` through `--space-5`, defined as 4px, 8px, 16px, 24px, and 32px.
- `npm test -- src/lib/charts/theme.test.ts` in `packages/workflow-analytics`: 7 passed.
- `npx playwright test tests/e2e/shell.spec.ts`: 13 passed. With no stored key and dark mode, `/` and `/settings` compute `--bg` `#002b36`, `--text` `#839496`, and the series list. Choosing Light sets `--bg` `#fdf6e3` and `--text` `#657b83` without a reload, and a reload keeps it. Choosing System, then switching the emulated scheme to dark, sets `--bg` to `#002b36`.

### Feedback

`artifact_feedback` on `docs/plans/14-analytics-ui/reports/1-01-solarized-shell.md` and `docs/plans/14-analytics-ui/briefs/1-01-solarized-shell.md` returned not delivered. Nothing is queued for either file.

### Carried

None.

## Phase 2 — Distribution, score series, and run aggregates

Refined in `1773214` into six units. Refine agent `d742ac97-355e-4334-8c57-c8076a6ee14b` returned Proceed. `artifact_feedback` on the six briefs was not delivered; nothing was queued.

### 2-01-distribution-read

- Built: `GET /v1/analytics/distribution` — call and conversation grain, optional `model` dimension, fixed bins, top-N without `__other__`, unpriced cost excluded from percentiles and bins.
- Surfaces: `tools/workflow/internal/store/distribution.go`, `distribution_test.go`, `percentile.go`; `tools/workflow/internal/serve/analytics_distribution.go`, `analytics_distribution_test.go`, `serve.go`, `analytics_bench_test.go`. Commit `f66b9db`.
- Deviations: the serve shape test sees `rows: []` on `queryFixture` because that fixture has no usage facts. Store tests cover the populated cases.
- Agent: Composer, agent `9b0236d1-8c6a-41bb-bd43-323df3157d3d`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run TestDistribution -count=1` and `go test ./internal/serve/ -run 'TestDistribution|TestAnalyticsBenchSmoke' -count=1` from `tools/workflow`, both ok.

### 2-05-conversation-window

- Built: `GET /v1/analytics/conversation` keeps the full event list, `totals` covers the whole run past the event cap, and `window_totals` is present only when `from` or `to` is set. `from` after `to` is 400 `{"error":"from after to"}`.
- Surfaces: `tools/workflow/internal/store/conversation.go`, `conversation_test.go`; `tools/workflow/internal/serve/analytics_conversation.go`, `analytics_conversation_test.go`, `analytics_bench_test.go`. Commit `0d836e5`.
- Deviations: none.
- Agent: Composer, agent `fb7bdfd1-c41d-466a-aa61-912a7a547d43`. The harness did not report turn count or final context size. Status `done`.
- Check: `go test ./internal/store/ -run TestConversation -count=1` and `go test ./internal/serve/ -run TestConversation -count=1` from `tools/workflow`, both ok.
