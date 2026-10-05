# Brief: 2-02 — Trends, repos and hooks reports

Consumer: a worker dispatched by the plan 10 phase 2 orchestrator. The orchestrator verifies the phase outcome by running this unit's e2e specs with the rest of the suite.
Owned paths: `packages/workflow-analytics/src/routes/trends/`, `src/routes/repos/`, `src/routes/hooks/`, `src/lib/charts/` (new), `tests/e2e/trends.spec.ts`, `tests/e2e/repos.spec.ts`, `tests/e2e/hooks.spec.ts` (all under `packages/workflow-analytics/`), plus `docs/plans/10-workflow-analytics/reports/2-02-chart-reports.md`. Touch nothing else — in particular not `package.json`, `package-lock.json`, `vite.config.ts`, `svelte.config.js`, `src/lib/api.ts`, `src/lib/filters.ts`, `src/lib/types.ts`, `src/lib/components/FilterBar.svelte`, the root layout, or `tests/e2e/fixture.ts` (2-01 owns them; report a gap instead of changing them).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/2-02-chart-reports.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-01 (committed on this branch).
Runs alongside: nothing. Paths are disjoint from 2-03 and 2-04, but all three share the e2e harness's `build/` directory and fixed ports, so they run one at a time (2-02, then 2-03, then 2-04).
Budget: 10 files to read, about 700 lines to write including specs, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — Solution Shape view table (lines 33-47), the `series` contract (lines 96-118), "Domain: Analytics site" (181-187), Phase 2 Outcome (line 290). Binding.
2. `docs/plans/10-workflow-analytics/reports/2-01-site-shell.md` — the client, filter helpers, `label()`, fixture exports, dependency versions, how to run the suites.
3. `packages/workflow-analytics/src/routes/+page.svelte` — the overview, as the idiom for a report route (filter from URL, fetch, error panel, `data-testid`).
4. `packages/workflow-analytics/src/lib/api.ts`, `src/lib/filters.ts`, `src/lib/types.ts`, `tests/e2e/fixture.ts`, `tests/e2e/helpers.ts` — by export list first (`grep -n export`), then the parts you call.
5. LayerChart's docs for the installed version (`node_modules/layerchart/README.md` and its package exports) — the chart components you use.

Run commands from `packages/workflow-analytics`; Go is at `~/.local/go/bin`. Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

Three report routes show the fixture's time-series, per-repo and hook-usage lenses for the URL filter, as LayerChart charts with the numbers also readable as text.

## Contract

- `/trends` — "Time series: those volumes by day or week, split by one dimension." Calls `GET /v1/analytics/series` with `metric`, `bucket`, `group` and the shared filter. The allowed pairings are the table at DESIGN.md lines 100-106; "Any other pairing is 400."; "`group=none` returns one series whose `key` is `"all"`."; "an empty name is the series key `""`."
- `/repos` — "Repo comparison: the same volumes side by side per `repo_id`."
- `/hooks` — "Hook usage: `event` and `tool_name` distributions, plus harness."
- "Charts on the fixed routes use LayerChart (MIT)." "No second chart grammar."
- "Every report except `/settings` shares one filter set, stored in the page URL … Changing a filter refetches and the URL is the shareable report."

Decisions settled at refine (do not re-derive):

1. **`/trends` controls** are URL params beside the shared filter: `metric` (default `hook_events`), `bucket` (default `day`), `group` (default `none`). The `group` control offers only the pairings the contract allows for the chosen metric; changing `metric` to one that disallows the current `group` resets `group` to `none` in the same navigation. Render one LayerChart line (or stacked area) per series key, and beneath it a table of `t` × key with `data-testid="series-<key>-<t>"` on each count cell. Empty keys display through `label()` as `(none)`; the test id uses the raw key (empty → `none`).
2. **`/repos`** fetches `GET /v1/analytics/facets` for the window, takes its non-empty `repos` (intersected with the URL's `repo_id` values when any are set), and calls `GET /v1/analytics/summary` once per repo with `repo_id=<repo>` plus the rest of the shared filter. Show a grouped bar chart of `conversations`, `hook_events`, `artifact_versions`, `commits` per repo, and a table with one row per repo carrying `data-testid="repo-<repo>-<field>"` for those four fields plus `by_kind` design / brief / report. Requests run in parallel.
3. **`/hooks`** calls `series` three times with `metric=hook_events`, `bucket=day` and `group` = `event`, `tool`, `harness`, sums each key's points, and shows three horizontal bar charts sorted by count descending, each with a table (`data-testid="hooks-<group>-<key>"`, empty key → `none`). Facets are not used for these counts, because `/facets` ignores `repo_id` (phase 1 brief 1-03 decision 10) and the outcome requires `repo_id` to change the numbers.
4. **Shared chart wrappers** go in `src/lib/charts/` (for example `LineSeries.svelte`, `Bars.svelte`); other units do not import them. Use LayerChart's default theme with CSS variables; no colour library.
5. **Errors:** a 400 from the API shows the error panel the layout provides; the route never sends a pairing outside the table.

### Keep untouched

2-01's files listed under Owned paths. If a shared file needs a change (a missing type, a fixture number), report it as a gap and compute what you need in your spec from the exported fixture facts.

## Done evidence

Write the failing specs first and report their output before and after. Why: these specs are the phase outcome for three of the eight report routes — "shows the fixture's numbers for that route's lens; setting `repo_id` in the URL changes those numbers …; reloading the same URL keeps the filter." Each check below says what it guards:

- The per-day and per-harness counts prove the chart draws the API's series and not a re-aggregation that could drift from it. The `repo_id` + reload check is the outcome's "filters … survive a reload" guard. The `group` options check proves the page can never send a pairing the contract answers with 400.
- The repos counts prove each repo's column is that repo's summary and not the window total. The filtered URL proves the comparison respects the shared filter.
- The hook counts prove the `(none)` key for missing `tool_name` is shown rather than dropped (Architectural Implications: "Views must tolerate empty keys"). They also prove `repo_id` changes the counts, which a facets-based count would not do.
- The build + bundle check proves this unit added no secret to the Pages artifact. The whole-suite run proves the shell still holds.

- `npm run test:e2e -- trends.spec.ts repos.spec.ts hooks.spec.ts` → passes, with at least:
  - `trends.spec.ts`: `/trends` shows the fixture's per-day `hook_events` counts; `/trends?metric=hook_events&group=harness` shows one series per harness with the fixture counts; adding `repo_id=<repo>` changes them to the filtered counts and survives `page.reload()`; choosing `metric=conversations` in the controls leaves only `none` and `harness` selectable for `group`.
  - `repos.spec.ts`: both fixture repos appear with their expected four counts; `/repos?repo_id=<repo>` shows only that repo.
  - `hooks.spec.ts`: event, tool (including the `(none)` row for hook events without `tool_name`) and harness counts equal the fixture; `repo_id` in the URL changes them; reload keeps them.
- `npm run build && npm run check:bundle` (with the `E2E_FORBIDDEN` the 2-01 report names) → passes.
- `npm run test:e2e` (whole suite) → passes, so 2-01's specs still hold.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in phase 1's routes or 2-01's shell): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
