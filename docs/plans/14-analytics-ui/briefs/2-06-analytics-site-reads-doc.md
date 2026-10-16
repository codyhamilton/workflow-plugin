# Brief: 2-06 — Analytics site reads doc

Consumer: the Cursor worker dispatched for this unit.
Owned paths: `docs/design/07-analytics-site.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title.
Report: before committing, write `docs/plans/14-analytics-ui/reports/2-06-analytics-site-reads-doc.md` and include it in the commit.
Depends on: `2-01-distribution-read`, `2-02-score-series-read`, `2-03-executions-shape-series`, `2-04-conversations-usage-fields`, `2-05-conversation-window` (document what shipped).
Runs alongside: nothing.
Budget: 4 files to read, about 120 lines to change, 15 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/14-analytics-ui/DESIGN.md` — Domain: Analytics reads (full **`GET /v1/analytics/distribution`**, **`score-series`**, executions delta, conversations delta, conversation delta) and Phase 2 outcome on `docs/design/07-analytics-site.md`.
2. `docs/design/07-analytics-site.md` — existing read API section (facets through conversation).
3. `tools/workflow/internal/serve/serve.go` — grep registered analytics paths only, to match names.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Design 7’s analytics read section documents the Phase 2 routes and parameters as implemented, and states that existing `/query` fields are unchanged.

## Contract

From `docs/plans/14-analytics-ui/DESIGN.md`, Phase 2 outcome:

- `docs/design/07-analytics-site.md` states these routes and states that existing `/query` fields are unchanged.

The Domain: Analytics reads bullets in plan 14 are authoritative for wording of parameters, errors, and response shapes.

## Changes

- Insert or extend subsections for `GET /v1/analytics/distribution` and `GET /v1/analytics/score-series` with measure/grain/dim/filter/bin/score semantics as in plan 14 (cite-level detail, not paraphrase drift).
- Update the `GET /v1/analytics/executions` bullet for repeatable `shape`, optional `bucket`, and `series` three-key order.
- Update `GET /v1/analytics/conversations` row fields for usage and `model`.
- Update `GET /v1/analytics/conversation` for optional `from`/`to`, `window_totals`, and whole-run `totals` under truncation.
- Add one explicit sentence that `/query`, `/schema`, `/summary`, `/series`, `/scores`, and `/baselines` are unchanged by this plan (per plan 14 non-redefinition).
- Do not edit theme, dashboard, or site interaction sections (Phase 5 owns those deltas).

### Keep untouched

Pages/routes table at the top unless a one-line cross-reference is needed. Ingest, compaction, and non-analytics API sections.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `rg -n 'distribution|score-series|window_totals' docs/design/07-analytics-site.md` → each Phase 2 route name appears in the read API section; `window_totals` documented on conversation.
- `rg -n '/query.*unchanged|unchanged.*\/query' docs/design/07-analytics-site.md` → explicit statement that existing `/query` fields are unchanged.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, contradictions. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
