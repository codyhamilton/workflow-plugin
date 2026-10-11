# Brief: 4-02 — URL view state, presets, bucket picker, range-safe API params, cost label

Consumer: a TypeScript worker (flash-tier); 4-05 (shell) and every route unit import these pure modules.
Owned paths: `packages/workflow-analytics/src/lib/urlstate.ts`, `urlstate.test.ts`, `presets.ts`, `presets.test.ts`, `buckets.ts`, `buckets.test.ts`, `params.ts`, `params.test.ts`, `format.ts`, `format.test.ts` (all new except `format.ts`). Touch nothing else; in particular leave `filters.ts` alone (old routes still import it; 4-16 retires it).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-02-filter-model-presets.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-01, 4-03, 4-04.
Budget: 5 files to read, about 450 lines to write (mostly tests), 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`. These modules are pure: no `window`, no `localStorage`, no `$app`. Time-zone maths uses `Intl.DateTimeFormat` only (no date library).

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Dashboard site": presets, brush-to-zoom, `tz` from the browser, "each chart picks the finest bucket within the 400-bucket cap", drill-down and exclusion rules.
2. `packages/workflow-analytics/src/lib/filters.ts` and `filters.test.ts` — the old URL filter; read for style only.
3. `tools/workflow/internal/serve/analytics.go` — `parseFilter` (about line 101) and `tooWide`; `analytics_query.go` — `bucketSpan`. These define what the API rejects.
4. `packages/workflow-analytics/src/lib/format.ts` — `label`, `num`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The site can turn a URL into API params that the API accepts, pick a bucket that is in range, and say what a cost is without ever showing $0 for unpriced calls.

## Contract (what the API does today; the site must stay inside it)

- Non-`/query` routes (`facets`, `summary`, `series`, `scores`, `executions`, `conversations`, `explore`, `conversation`) answer `400 "range too wide"` for a window wider than 400 UTC days (400 UTC weeks for `weeks`). `all=1` therefore fails on them. Only `/query` accepts `all=1`.
- `/query` allows at most 400 buckets per unit in the request tz (`bucketSpan`); otherwise `400 "range too wide"`. Buckets: `none`, `hour`, `day`, `week`, `month`. `/series` takes `day` or `week` only. Default window is 30 days.
- The shared filter keys are `from`, `to` (RFC3339), `repo_id`, `harness`, `kind`, `plan`, `norm_event`, `event`, `tool`, `model`, `source`, `conversation_id`, `tz`, `all`. Each is repeatable. There is no exclude parameter: shift-click exclusion is resolved on the site by sending the complement of the excluded values taken from `facets` (decision recorded at refine; DESIGN.md says only "shift-click excludes it").
- `scores` needs exactly one `kind`.
- Cost is 0 for an unpriced model, and 74% of local calls are unpriced, so a cost shown on its own is wrong.

## Changes

1. `urlstate.ts`
   - `DIM_KEYS = ['repo_id','harness','kind','plan','norm_event','event','tool','model','source','conversation_id']`, `type DimKey`.
   - `type PresetId = 'today'|'24h'|'7d'|'30d'|'90d'|'month'|'ytd'|'all'`.
   - `interface UrlState { range: PresetId | 'custom'; from?: string; to?: string; include: Partial<Record<DimKey,string[]>>; exclude: Partial<Record<DimKey,string[]>> }`.
   - `parseUrlState(q)`: `range=` selects a preset; `from`/`to` without `range` is `custom`; neither is `30d`. Includes are the plain keys, repeated. Excludes are `x.<key>` repeated (`x.harness=cursor`). Unknown `kind` values are dropped.
   - `toSearch(state, keep?: URLSearchParams)`: writes `range` (not for `custom`), `from`/`to` only for `custom`, includes and excludes; carries over every param of `keep` that is not a filter param (metric, group, page cursors are route params).
   - `applyDrill(state, key, value, exclude: boolean)`: include adds to `include[key]` and removes the value from `exclude[key]`; exclude does the reverse; `value === '__other__'` returns the state unchanged. `removeChip(state, key, value)`. `chips(state)` returns `{key, value, mode: 'include'|'exclude'}[]`.
2. `presets.ts`
   - `PRESETS: {id: PresetId, label: string}[]` in this order: Today, 24h, 7d, 30d, 90d, This month, YTD, All time.
   - `presetWindow(id, now: Date, tz: string): {from: Date, to: Date} | null` (`all` returns null). `to` is `now` rounded up to the next full hour so repeated navigation within the hour produces identical params and hits the 4-01 cache. `today`, `month` and `ytd` start at local midnight, the first of the month and 1 January in `tz`. `24h`, `7d`, `30d`, `90d` are `to` minus that span.
3. `buckets.ts`
   - `bucketCount(bucket, from, to, tz): number` (an upper bound: add one for partial edge buckets and one for a DST day).
   - `pickBucket(from, to, tz, allowed: Bucket[] = ['hour','day','week','month'], cap = 400): Bucket | null`: the finest allowed bucket whose count is at most `cap`; `hour` therefore only for windows of about 16 days or less. Null when none fits.
4. `params.ts`
   - `type Route = 'query' | 'rest'`.
   - `resolveWindow(state, now, tz, route): {from?: Date, to?: Date, all: boolean, clamped: boolean}`. For `rest`, any window wider than 399 days (including `all`) is clamped to the last 399 days and `clamped` is true. For `query`, `all` returns `{all: true, clamped: false}` with no `from`.
   - `apiParams(state, win, facets: Partial<Record<DimKey,string[]>> | null, tz): {params: URLSearchParams} | {pending: true} | {empty: true}`. Includes pass through. An exclude with no matching include becomes the complement: `facets[key]` minus the excluded values (an exclude combined with an include removes the excluded values from the include list). `pending` when an exclude needs `facets` and `facets` is null. `empty` when the complement is empty, so the caller issues no request. Always sets `tz`; sets `all=1` or RFC3339 `from`/`to`. Excludes on `conversation_id` are not supported (no facet list): `applyDrill` still stores them, `apiParams` ignores them, and `chips` marks them.
   - `scoresParams(params, kind)`: returns a copy with exactly one `kind`.
5. `format.ts` (keep `label` and `num` as they are, add):
   - `costLabel({cost, unpriced, calls}: {cost: number; unpriced: number; calls?: number}): string`. If `calls` is known and `calls > 0` and `unpriced >= calls`, or `calls` is unknown and `unpriced > 0 && cost === 0`: the text is `unpriced`. If `cost > 0`: `$` with two decimals (four when below $0.01), plus `, N unpriced` when `unpriced > 0`. If `calls === 0`: `—`. Otherwise (no unpriced calls, cost 0): `$0.00`. A cost of `$0.00` must never come out for a row that has unpriced calls.
   - `bytes`-style helpers are not needed.

### Keep untouched

`filters.ts` and its test; `label` and `num` in `format.ts`.

## Done evidence

Write each failing test first and report the output before and after.

- `npm test` → passes, including: a URL round-trip (`parseUrlState` then `toSearch`) for includes, excludes and a custom range; route params survive `toSearch`; `applyDrill` ignores `__other__` and moves a value between include and exclude; `presetWindow` with `tz = 'Australia/Sydney'` and `'America/New_York'` for `today`, `month`, `ytd` across a DST date; `pickBucket` gives `hour` for 7 days, `day` for 90 days, `week` for 3 years, `month` for 30 years, null when `allowed` is `['hour']` over 30 days; `resolveWindow('all', 'rest')` is clamped to 399 days and `('all', 'query')` has `all: true`; an exclude resolves to the facet complement, is `pending` with no facets and `empty` when everything is excluded; `costLabel` cases (all unpriced, mixed, priced, no calls) and none of them returns `$0.00` when `unpriced > 0`.
- `npm run build` → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
