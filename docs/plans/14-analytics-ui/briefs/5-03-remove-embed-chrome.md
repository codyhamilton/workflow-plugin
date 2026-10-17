# Brief: 5-03 — Remove embed mode, dashboard chrome

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `packages/workflow-analytics/src/routes/+layout.svelte`; `packages/workflow-analytics/tests/e2e/shell.spec.ts` (embed test replacement only). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-03-remove-embed-chrome.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01-view-store-config, 5-07-analytics-site-doc.
Budget: 4 files to read, about 60 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Phase 5 outcome (`embed=1` is not generated, and the layout no longer has an embed branch); Domain: Dashboards non-goals (`embed=1`).
2. `packages/workflow-analytics/src/routes/+layout.svelte`.
3. `packages/workflow-analytics/tests/e2e/shell.spec.ts` — embed test.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

One shell and one filter bar for the whole app, including `/dashboards`; remove the embed-only layout branch.

## Contract

Phase 5 outcome:

- `embed=1` is not generated, and the layout no longer has an embed branch.

Domain: Dashboards:

- The dashboard page renders each tile as a component in the same document. There is no iframe and no `embed=1`. Every tile uses the dashboard URL's window and shared filters. Changing that window updates every tile.
- Non-goals: … `embed=1`.

## Changes

- Delete the `embed` derived flag and the `{#if embed}` branch; always render header and main.
- Set `chrome` true on `/dashboards` (keep `/settings` without filter bar). Dashboard tiles share the dashboard URL's FilterBar, FilterChips, Notices, and SaveView.
- Replace the embed e2e test with one that `/dashboards?range=7d` shows `data-testid="preset-7d"` pressed (or equivalent window control) and `data-testid="saveview-save"`, and that `?embed=1` on `/trends` no longer hides the header (header count 1).

### Keep untouched

Theme controls, nav, conversation route window exception (layout already shows chrome per 4-04), and notice/error plumbing.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npx playwright test tests/e2e/shell.spec.ts -g "embed|dashboards"` from `packages/workflow-analytics` → passes with the new assertions; no test navigates to `embed=1` expecting a hidden shell.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
