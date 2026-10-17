# Brief: 5-07 — Analytics site design doc delta

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `docs/design/07-analytics-site.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/5-07-analytics-site-doc.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-01-view-store-config, 5-03-remove-embed-chrome, 5-06-dashboard-e2e.
Budget: 3 files to read, about 120 lines to change, 25 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Architectural Implications (Phase 5 site-section delta); Domain: Theme; Domain: Report interaction (overview links, non-clickable marks, zero-fill); Domain: Dashboards; Phase 5 outcome doc bullet.
2. `docs/design/07-analytics-site.md` — **The site** section (charts/theme, saved views, drill-down), **Open issues** item 12 and item 13 dashboard clauses.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Bring design 7's site section in line with plan 14 Phase 5: theme override, in-document dashboards, interaction exceptions, and fix the stale conversation-totals clause (Phase 4 carried).

## Contract

Architectural Implications (`DESIGN.md`):

- Phase 5 writes the theme, the dashboard pivot, and these three site-section exceptions. … Overview counts link as in the interaction contract, not to `/explore`. The empty key, `__other__`, `hour_of_day`, `weekday`, and check names are not clickable. Zero-fill applies to count series only.

Domain: Theme (`DESIGN.md`) — cite verbatim the storage key, `data-theme`, light/dark hex surfaces, accent/danger, series order, space scale, and explicit `light`/`dark`/`system` override (design 7 today says system preference only; replace that sentence).

Domain: Dashboards (`DESIGN.md`) — cite the view/dashboard JSON shapes, in-document tiles, one window and shared filters, twelve-tile cap, import drops, URL→config import, no `embed=1`.

Domain: Report interaction (`DESIGN.md`) — cite overview KPI link targets and `measure` on `/trends`; cite non-clickable keys; cite zero-fill rule for count series vs score gaps.

Phase 5 outcome:

- `docs/design/07-analytics-site.md` describes the theme override, the in-document dashboard, the overview links, the non-clickable marks, and zero-fill for count series only.

Phase 4 carried (binding fix, not optional):

- Replace open issue 12's stale phrase that conversation totals cover only returned events when truncated. Align with the conversation route contract already on the same page: `totals` is the whole conversation, including events past the cap; `truncated` applies to `events` only.

## Changes

- Update **The site** bullets for theme (explicit override + cite contract hex/series), saved views/dashboards (config not URL; no iframes), drill-down (overview links per interaction contract; `__other__`, empty key, `hour_of_day`, `weekday`, check names not clickable), and count-series zero-fill vs score gaps.
- Edit open issue 12: remove the incorrect totals/truncation clause; keep unrelated clauses in that item unless they contradict the conversation contract on the page.
- Trim or update open issue 13 dashboard clauses that contradict the new cap and in-document model (import cap bypass, embed fragment, iframe settle signal) so they reflect implemented behavior or move resolved parts out of open issues.

### Keep untouched

Analytics reads sections written in Phase 2, hosting, CORS, and open issues this phase does not own.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg "embed=1" docs/design/07-analytics-site.md` → no matches in **The site** saved-view description (non-goals in historical open issues may mention embed only if marked fixed — prefer none).
- `rg "totals cover only the returned events" docs/design/07-analytics-site.md` → no matches.
- `rg "workflow-analytics-theme" docs/design/07-analytics-site.md` → matches theme override bullet.
- `rg "in-document|chart configuration" docs/design/07-analytics-site.md` → describes dashboards without iframe framing.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
