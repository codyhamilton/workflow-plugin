# Brief: 4-03 — Conversations usage and cost distribution

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/conversations/+page.svelte`; `packages/workflow-analytics/src/lib/types.ts` (extend conversation list row fields only: `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`); `packages/workflow-analytics/tests/e2e/conversations.spec.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/4-03-conversations-cost-distribution.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-01-quality-score-series (coordinate `types.ts` with 4-01/4-02 commits).
Runs alongside: 4-02-executions-shape-series, 4-04-conversation-window-timeline.
Budget: 12 files to read, about 280 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 4 `/conversations` outcome; Domain: Analytics reads **`GET /v1/analytics/conversations`** (usage fields, most-frequent `model`); **`GET /v1/analytics/distribution`** (`grain=conversation`, `measure=cost_usd`); Domain: Report interaction (model click includes filter).
2. `packages/workflow-analytics/src/routes/conversations/+page.svelte` — virtual list columns.
3. `packages/workflow-analytics/src/routes/usage/+page.svelte` — `DistributionChart` + distribution fetch pattern (read only).
4. `packages/workflow-analytics/tests/e2e/conversations.spec.ts` and `tests/e2e/fixture.ts` — `CONVERSATION_ROWS` (extend fixture constants in this unit’s spec file only if needed; do not edit `fixture.ts` — that is 4-06).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The conversations list shows model and cost per row, model click filters the page, and a per-conversation cost distribution for the window sits on the same page.

## Contract

Phase 4 outcome:

- On `/conversations`, each loaded row shows model and cost, a model click filters, and the page shows the distribution of per-conversation cost for the window.

`GET /v1/analytics/conversations` from DESIGN.md (binding):

- Each row gains `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`. `model` uses the most-frequent rule above, over in-window calls.

`GET /v1/analytics/distribution` for this page:

- `measure=cost_usd`, `grain=conversation`, `dim` omitted (row `k` `"all"`). Filters `repo_id`, `harness`, `model`, `conversation_id` apply via `view.paramsFor('rest')`.

Report interaction: clicking a mark whose key is a shared filter value includes it; model is a shared filter key.

## Changes

- Extend grid header and row cells for `model` (button → `view.drill('model', …)`) and formatted `cost_usd` (reuse `costLabel` with row unpriced/calls fields).
- Fetch `analytics/distribution?measure=cost_usd&grain=conversation` with window params; render the `"all"` row bins with `DistributionChart` (import component; do not edit chart files).
- Model filter on the list narrows both the list API params and the distribution fetch.
- Keep virtual scroll, pager, and existing drill columns.

### Keep untouched

`DistributionChart.svelte`, `distribution.ts`, `VirtualRows.svelte`, `fixture.ts`, backend.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/conversations.spec.ts` → passes, including new tests: live serve row for `c5` shows model and cost matching API; distribution slot requests `/v1/analytics/distribution` with `grain=conversation&measure=cost_usd`; model cell click sets `model` chip and reduces visible rows; existing paging/virtualisation/error tests still pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
