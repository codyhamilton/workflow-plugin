# Analytics UI review

Independent review of `plan/14-analytics-ui` against `DESIGN.md`. Evidence is the code and tests. `IMPLEMENTATION.md` was not used as evidence.

## Verdict

**PASS_WITH_FOLLOWUPS.**

Post-fix state. No briefed finding remains. No blocker or high remains.

## Reviewed SHA

`2bc26e081bb5ddb629fb55a47fe7d02b33acfe08`

The mechanical fixes below are in the commit that adds this file. The verdict is that post-fix tree.

## Phase outcome assessment

| Phase | Assessment |
|---|---|
| 1. Solarized shell | Partial. Theme storage, `data-theme`, solarized hexes, and series order match the contract. `shell.spec.ts` covers system-dark, Light without reload, and a later OS change. No hex remains in `<style>` blocks under `packages/workflow-analytics/src/**/*.svelte`. `theme.css` and `DEFAULT_TOKENS` use only the contract hexes. Notices, save errors, and the dashboard import error now use `danger`, `surface`, `text`, and `border`. The layout header and main use `--space-*`. Filter bar, chips, and save-view gaps still use rem values off that scale (follow-up). |
| 2. Distribution, score series, and run aggregates | Met. `TestAnalyticsBenchSmoke` builds cases for `/distribution`, `/score-series`, `/executions` with `shape` and `bucket`, `/conversations`, and `/conversation` with `from` and `to` (`analytics_bench_test.go`). Store tests cover priced-only cost stats, token `unpriced` 0, shared cost edges, truncation without `__other__`, latest-in-bucket scores, omitted empty buckets, shape narrowing rows but not counts, the three series keys, the most-frequent conversation model, uncapped `totals`, and `window_totals`. `docs/design/07-analytics-site.md` states the routes and leaves `/query` fields as they were. Go tests were not re-executed in this review (`go` is not installed). |
| 3. Model and volume reports | Met. `/usage` requests model totals, cost and token series split by model, and a per-call distribution for `cost_usd` and each token measure; brush and model click/shift are in `usage.spec.ts`. `/trends` drills a series and can draw a stacked area. `/repos` ranks by `cost_usd` and drills a repo. `/hooks` charts `hook_events` with a time bucket and `norm_event` or `tool`, brush, and treemap drill. Overview KPI targets match the interaction contract. The filter bar lists all ten shared dimensions. The builder heatmap drills a filter dimension; zero dimensions and bucket `none` render the scalar. The trends KPI query key is `metric` (follow-up), which is the key `/trends` reads. |
| 4. Quality and runs | Met. `/quality` draws a median and a p25–p75 band, keeps the baseline box, leaves a missing bucket blank (`quality.spec.ts`), and brush sets the window. `/executions` sets `shape` from a sankey edge, pages with that shape, keeps window `counts`, and shows the three-shape series. `/conversations` shows model and cost, filters on model click, and loads per-conversation cost. Shift-click on that table now excludes. `/conversation` shows the window control, keeps out-of-window events, and shows `window_totals` beside `totals`. `/explore` includes `model`, `cost_usd`, and `norm_event`. |
| 5. In-document dashboards | Met. A saved view stores chart params only (`chartParamsFromQuery`, `views.test.ts`). The dashboard page renders `DashboardTile` in the document; there is no iframe and no `embed=1` branch. Import keeps 12 tiles and counts drops. A legacy `/usage` URL keeps `measure` and drops window and filter keys; an unknown path is counted. Changing the dashboard window is what the tile queries use (`paramsForTile`). `docs/design/07-analytics-site.md` now describes the theme override, the in-document dashboard, the overview links, the non-clickable marks, and count-only zero-fill, including the `/series` bullet that previously contradicted that rule. |

## Findings by severity

### Blocker

None.

### High

None.

### Medium

1. **Shift-click on `/conversations` never excluded.** Row handlers passed the `MouseEvent` into `view.drill`, which reads `shift`, not `shiftKey`. Include worked; exclude did not. Executions already passed `{ shift: ev.shiftKey }`.
   - **Resolved in review.** The harness, repo, and model handlers now pass `{ shift: e.shiftKey }`.
2. **The empty filter key could be applied.** Hooks and dashboard tiles renamed `""` to `(none)` and then drilled that label back to `""`. `applyDrill` only ignored `__other__`. Bar and grouped-bar tables treated an empty key as selectable. The contract says the empty key is not clickable.
   - **Resolved in review.** `applyDrill` ignores `""` and returns the same state (`urlstate.test.ts`). `TimeChart` treats `(none)` as inert. The hooks page and `DashboardTile` return before drilling it. Bar, grouped bar, and builder treemap picks skip `""` (`options.test.ts`, `multi.test.ts`).
3. **Notices and inline errors did not use the theme quartet.** `.notice` used an accent border and muted text. `.saveview-error` used muted only. The dashboard import error set `color: var(--danger)` only. The contract says a notice, warning, or error uses `danger`, `surface`, `text`, and `border`, and adds no hex.
   - **Resolved in review.** Those three rules now use that set. The layout error panel already did.
4. **Design 7 contradicted count-only zero-fill.** The `/analytics/series` bullet said the site zero-fills every gap when charting. The site section, and the design, zero-fill only count series and leave a score-series gap.
   - **Resolved in review.** The `/series` bullet now says those metrics are counts and points at the site rule.

### Low

5. **Open issues 13 and 14 described behavior this plan replaced.** Issue 13 said zero dimensions and bucket `none` had no valid chart type; the builder renders the scalar. Issue 14 said the executions sankey filtered the loaded page client-side; a click sets `shape`, and `counts` stay the window totals.
   - **Resolved in review.** The scalar clause is removed from issue 13 (the `data-ready` and store-validation clauses stay). The site chart-builder bullet names the scalar. Issue 14 is marked closed in place so later numbers do not move.
6. **Filter bar, chips, and save-view gaps are off the space scale.** The layout header and main use `--space-1` through `--space-5`. `FilterBar` still uses `0.75rem` and a new `0.1rem` caption gap; chips and the save control use other rem gaps. Which scale step replaces `0.75rem` is a visual choice, so this was not restyled.
   - **Follow-up.**
7. **Overview trends links set `metric`, not `measure`.** `kpiHref` writes `metric`, and `/trends` reads `metric` (`trends/+page.svelte`). `overview.spec.ts` expects that. The dashboard contract lists `metric` as a chart control, and brief 3-02 forbade renaming it. The interaction sentence and the design 7 site bullet say the link sets `measure`. The tiles land on `/trends` with `artifact_versions`, `distinct_content`, or `commits`. Changing only the overview key would make those tiles show the default measure.
   - **Follow-up.** Pick one key and update the design sentence or the trends control together.

## Intent and ledger

The request was a solarized light/dark shell, drill, brush, and filtering, and first-class model comparison, trend, and distribution views. The branch does that on the current tree: tokens and an explicit theme override, report interactions on the URL, read-time aggregates for distribution, score series, execution shape, and conversation usage, and dashboards as in-document chart configs under one window. No second chart library, no ingest, no `__other__` distribution row.

The assumption ledger is empty. The provenance decisions still hold: aggregates stay read-time inside the 400-day cap, surfaces stay `packages/workflow-analytics` and `tools/workflow`, a saved view stores chart controls only, heatmap cells are not filters, and conversation `totals` are the whole run.

## Plan sufficiency

The design was enough to determine intent, place these findings, and derive QA. Phase outcomes name the fixture and the page behavior, and the domain contracts name the error strings, bin edges, and storage shapes the tests assert.

One collision was not resolved in the design: the interaction sentence says the trends KPI sets `measure`, and the dashboard params list includes `metric`, which is the key the trends page already used. Dispatch kept `metric`. That is follow-up 7, not a hole that hid the rest of the work.

## Residual risks

- `go` is not installed here, so `TestAnalyticsBenchSmoke` and the store and serve tests were read, not re-run.
- Playwright was re-run only for `tests/e2e/area.spec.ts` (2 passed), which now expects series color `#268bd2`. The rest of the e2e suite was not re-run.
- Unit tests re-run: `urlstate`, `options`, `multi`, `theme`, `views`, `dashboard-tile` (78 passed).
- Open issue 13 still says builder `data-ready` stays true while the previous chart is shown, and that stored views are not validated on read. Invalid entries are dropped on read with no notice.
- `dominantModel` breaks ties to the smaller name. The conversations fixture asserts a strict frequency winner, not a tie.
