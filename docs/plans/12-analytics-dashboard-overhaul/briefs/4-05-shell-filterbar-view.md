# Brief: 4-05 — Layout shell, FilterBar with presets and chips, and the `view` module routes share

Consumer: a Svelte 5 worker (flash-tier); every route unit (4-06 to 4-15) reads `view` and relies on the shell.
Owned paths: `packages/workflow-analytics/src/routes/+layout.svelte`, `src/lib/view.svelte.ts` (new), `src/lib/components/FilterBar.svelte`, `src/lib/components/FilterChips.svelte` (new), `src/lib/components/Notices.svelte` (new), `tests/e2e/shell.spec.ts` (new). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-05-shell-filterbar-view.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 4-01, 4-02, 4-03, 4-04.
Runs alongside: nothing (the route units wait for this one).
Budget: 8 files to read, about 450 lines to write, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": the URL is the view, presets, `tz`, notices, chips, nav list, theme, 1024 px.
2. `packages/workflow-analytics/src/lib/query.ts` (4-01), `urlstate.ts`, `params.ts`, `presets.ts` (4-02), `src/lib/theme.css` (4-04) — the APIs you wire up. Read their exports, not their tests.
3. `packages/workflow-analytics/src/routes/+layout.svelte` and `src/lib/components/FilterBar.svelte` — what you replace.
4. `packages/workflow-analytics/tests/e2e/helpers.ts` (4-03) — `trackRequests`, `expectSettled`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The shell keeps the chosen window and filters in the URL across every route, offers quick ranges and removable chips, and gives route units one small `view` API so they never parse the URL or fan out requests themselves.

## Contract

- DESIGN.md: "the URL is the view. Filters survive navigation", presets Today, 24h, 7d, 30d, 90d, This month, YTD, All time, plus a custom range; `tz` is sent from the browser; `partial` and `ignored_filters` show as notices; chips are removable.
- Outcome this unit serves: the 7d preset chosen on Overview persists when navigating to Hooks.
- Unchanged: the `/settings` page, its base URL and token behaviour, the error panel (`data-testid="error-panel"`) and its text, the non-JSON connection error.
- Old routes (until their units land) read `from`, `to`, `repo_id`, `harness`, `kind`, `plan` from the URL through the old `filters.ts`. A URL with `from` and `to` and no `range` parses as `custom` in `parseUrlState`, so old routes keep working.

## Changes

1. `view.svelte.ts` exports one object `view` (a Svelte 5 reactive module over `page` from `$app/state`):
   - `state`: `UrlState` parsed from `page.url.searchParams`.
   - `tz`: `Intl.DateTimeFormat().resolvedOptions().timeZone`.
   - `facets`: `Partial<Record<DimKey, string[]>> | null`, loaded through `getJSON('facets', 'analytics/facets', …)` for the `rest` window and re-requested when the window changes (the 4-01 client dedupes and caches). Map the API fields: `repos`→`repo_id`, `harnesses`→`harness`, `kinds`→`kind`, `plans`→`plan`, `events`→`event`, `models`→`model`, `norm_events`→`norm_event`, `tools` (objects with `name`)→`tool`. Check the shape in `tools/workflow/internal/serve/analytics.go` (`analyticsFacets`).
   - `paramsFor(route: 'query' | 'rest', extra?: Record<string, string | string[]>): URLSearchParams | null`: `null` means do not fetch yet (facets pending) or nothing matches (`view.empty` is true). Otherwise `apiParams(...)` plus `extra`. `now` is taken once per URL change.
   - `empty: boolean`, `clamped: boolean` (the window was clamped for `rest` routes).
   - Mutators, each one `goto(url, {noScroll: true, keepFocus: true})` keeping route params: `setPreset(id)`, `setWindow(from: Date, to: Date)` (custom), `drill(key, value, ev?: {shift?: boolean})`, `setInclude(key, values: string[])` (replaces that key's includes in one navigation), `removeChip(key, value)`, `setParam(name, value | null)` (route params such as `metric`).
   - `route` helpers are not needed. Routes call `getJSON(slot, path, view.paramsFor(...))` inside `$effect` and ignore `Superseded`.
2. `FilterBar.svelte`: a preset button group (`data-testid="preset-<id>"`, `aria-pressed`), custom `from` and `to` date inputs (`filter-from`, `filter-to`, shown always, applied on change as a `custom` window), and multi-selects `filter-repo_id`, `filter-harness`, `filter-kind`, `filter-plan`, `filter-model` filled from `view.facets` (selecting adds an include through `view.drill`; keep the old test ids). No `goto` per keystroke; every change goes through the `view` mutators, and the 4-01 client collapses a burst into one request per slot.
3. `FilterChips.svelte`: one chip per `chips(state)` entry, `data-testid="chip-<key>-<value>"`, `data-mode="include"|"exclude"` (excluded chips show a leading "not"), a remove button `chip-remove-<key>-<value>`. A `conversation_id` exclude chip says it is not applied.
4. `Notices.svelte`: from `notices` (4-01) show `data-testid="notice-ignored"` ("`kind` does not apply to this measure and was ignored"), `notice-partial` ("Partial result: the query hit its time limit"), and, when `view.clamped`, `notice-clamped` ("All time is limited to the last 399 days on this view"). From `view.empty` show `notice-empty` ("Nothing matches these exclusions").
5. `+layout.svelte`: import `$lib/theme.css`; nav entries in this order: Overview `/`, Trends `/trends`, Usage & cost `/usage`, Repos `/repos`, Hooks `/hooks`, Quality `/quality`, Executions `/executions`, Conversations `/conversations`, Explore `/explore`, Settings `/settings`. Nav links keep the current search string (filters survive navigation) except Settings. Render FilterBar, chips and notices on every route except `/settings` and `/conversation`. Call `clearNotices()` and `clearError()` on route or search change (keep the existing error behaviour). Layout works at 1024 px: nav wraps, no horizontal page scroll.
6. `tests/e2e/shell.spec.ts` (local serve): choosing `7d` on `/` then clicking the Hooks nav link keeps `range=7d` in the URL and `preset-7d` pressed; reload keeps it; a drill through `view.drill` is not tested here; custom range inputs set `from` and `to`; removing a chip drops it from the URL; at viewport 1024×768 `document.documentElement.scrollWidth <= innerWidth`; dark scheme (`page.emulateMedia({colorScheme: 'dark'})`) changes the computed `--bg`. Use `trackRequests` to assert that five quick clicks on different presets then settle issue the facets request at most twice.

### Keep untouched

The error panel markup and text, the settings link logic for a 401 or network error, `+layout.ts`, and the `/settings` page.

## Done evidence

Run the existing e2e suite first and report its pass count; some old specs may fail only because of the new FilterBar markup. Fix those inside your owned paths if you can; otherwise list each failing spec and why for the route units.

- `npm test` and `npm run build` → pass.
- `npm run test:e2e -- shell.spec.ts` → all new tests pass.
- Report the rest of the suite's result and which old specs now fail, if any.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
