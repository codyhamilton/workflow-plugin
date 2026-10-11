# Brief: 5-01 — Saved-view and dashboard store

Consumer: a Svelte 5 / TypeScript worker (flash-tier).
Owned paths: `packages/workflow-analytics/src/lib/views.ts`, `packages/workflow-analytics/src/lib/views.test.ts` (both new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/5-01-saved-view-store.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 5-02, 5-03, 5-04, 5-11, 5-12, 5-14, 5-15, 5-16 (disjoint paths; no shared file).
Budget: 3 files to read, about 220 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": the bullets "Saved views and dashboards" and "The URL is the view".
2. `src/lib/urlstate.ts` — read only, to see what a view URL carries (range, filters, route params).
3. `src/lib/api.ts` lines 1-20 — how the site already guards `localStorage` (the `BASE_KEY` read in a try/catch).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

A pure, tested store for named saved views and dashboards over `localStorage`, plus dashboard JSON export and import, so the shell (5-06), the builder (5-07) and the dashboards route (5-08) share one format.

## Contract

From DESIGN.md: "A named saved view is a stored URL. A dashboard is an ordered grid of saved views, which can be exported and imported as JSON. Both live in `localStorage` under the prefix `workflow-analytics-views`." There is no server-side store.

Settled shapes (export these; other units import them):

```ts
export interface SavedView { id: string; name: string; url: string }   // url = "/path?query", site-relative
export interface Dashboard { id: string; name: string; viewIds: string[] } // ordered; a view may appear twice
export interface ViewStore { /* methods below */ }
export function createStore(storage?: Pick<Storage,'getItem'|'setItem'>): ViewStore
export const store: ViewStore   // createStore(localStorage when usable, else in-memory)
export class ImportError extends Error {}
```

`ViewStore` methods: `listViews()`, `saveView(name, url)` (a view with the same name is replaced in place and keeps its id), `deleteView(id)` (also removes it from every dashboard), `listDashboards()`, `createDashboard(name)`, `addToDashboard(dashboardId, viewId)`, `removeFromDashboard(dashboardId, index)`, `moveInDashboard(dashboardId, from, to)`, `deleteDashboard(id)`, `exportDashboard(id): string`, `importDashboard(json: string): Dashboard`, `subscribe(fn): () => void` (called after any write, and on the window `storage` event when `window` exists).

Storage keys: `workflow-analytics-views:views` and `workflow-analytics-views:dashboards`, each a JSON array.

Export format, exactly: `{"version":1,"name":"<dashboard name>","views":[{"name":"…","url":"…"}]}` (views in dashboard order, no ids).

Import: `JSON.parse` failures, a missing or non-1 `version`, a non-array `views`, or any view whose `url` is not a site-relative path (must start with a single `/`, not `//`, contain no `:` before the first `?`, and be at most 2,000 characters) throw `ImportError` with a plain message, and write nothing. A good import creates a new dashboard (a name that already exists gets ` (2)`, ` (3)`, … appended) and, for each view, reuses an existing saved view with the same name and url or creates one.

## Changes

Write `views.ts` with no Svelte or `$app` imports. Every `localStorage` read and write is in try/catch; when it throws or is absent the store keeps working in memory for the session. Corrupt stored JSON reads as empty. Ids come from `crypto.randomUUID()` when available, else a counter. `saveView` applies the same url check as import, so the dashboards route can rely on every stored url being safe to put in an `iframe src`.

Tests (`views.test.ts`, vitest, a fake in-memory `Storage`): save/replace by name; delete cascades; dashboard add, move, remove; export then import into a second `createStore()` reproduces the dashboard names, order and urls; each ImportError case above; a throwing storage still works; corrupt JSON reads empty.

### Keep untouched

`src/lib/api.ts` and every other file: this unit adds two files only.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- views` → fails before (no module), passes after, covering each case listed above.
- `npm test` → the existing suites still pass.
- `npm run build` → passes (the new file is not yet imported, so this only proves it compiles under `tsc`/svelte-check if the build runs it).

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
