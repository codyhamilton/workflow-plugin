# Analytics UI

The analytics site gained a solarized light and dark theme, report interactions that compare models and show distributions, and read-time aggregates those views needed. Dashboards stopped being framed copies of saved URLs and became chart configs rendered in the page under one window. The work did what it set out to do. Two small leftovers are open issues on the analytics site design.

## Intent

User request, verbatim:

> /design improvements to the analytics UI. it's extremely basic at the moment, needing:
> - Cleaner style, make it minimalistic but clean, well spaced and modern. Go with a solarized inspired theme (light/dark modes)
> - All charts and reports should be interactive where reasonable, with drill down and time window selection, dynamic filtering
> - Have separate subagents look at each of the pages and dashboards and reimagine them. We want to be able to compare model against model, trend changes and visualise distributions using appropriate graph types, it should be rich and interactive

## Why This Existed

The site was a flat link bar on a gray palette that followed the system scheme only. A person could filter and, on some bars, drill. They could not reliably compare models, see a measure move, or read a distribution. Several charts ignored clicks and brushes the neighbouring page already implemented. Dashboards were iframes of saved URLs. The query API returned sums, so the missing charts had nothing honest to read.

## What Was Built

The lasting contracts live in [design 7](../design/07-analytics-site.md): the theme override, the new and extended analytics reads, the interaction rules, and in-document dashboards.

**Changed:** `packages/workflow-analytics`, `tools/workflow/internal/store`, `tools/workflow/internal/serve`, and design 7.

### Phase 1 — Solarized shell

Light and dark solarized tokens, with a system, light, or dark choice stored on the browser. Charts read computed tokens. Stylesheet hexes in the site were replaced with those tokens. The shell's own padding and control gaps use the 4, 8, 16, 24, and 32 scale. The theme is applied before hydration so the first paint matches the stored choice.

### Phase 2 — Distribution, score series, and run aggregates

`GET /v1/analytics/distribution` summarizes per-call and per-conversation cost and tokens on fixed bins, without an `__other__` row, and keeps unpriced cost out of the percentiles. `GET /v1/analytics/score-series` returns a sparse median and quartile band per check. Executions accept a repeatable `shape` that filters rows only, and an optional time bucket of the three shapes. Conversation list rows carry model and cost. One conversation keeps the full event list, reports totals for the whole run, and adds window totals when a range is set.

### Phase 3 — Model and volume reports

Usage shows cost and token totals by model, both as time series, and a per-call histogram. Trends can drill a series and draw a stacked area. Repos can rank by cost. Hooks chart hook events over time by normalised event or tool. Overview counts link to the report that owns each measure. The filter bar lists all ten shared dimensions. The builder shows a scalar when there is no dimension and no bucket, and a heatmap cell drills a real filter.

### Phase 4 — Quality and runs

Quality draws the score band over the window, with the all-time baseline median, and leaves a hole where a bucket has no point. An executions sankey edge sets `shape` on the URL, and a stacked series of the three shapes sits on the page. The conversation list shows model and cost and the distribution of per-conversation cost. One conversation marks events inside the window and still lists the rest. Explore's table includes model, cost, and normalised event. End-to-end expectations match priced Opus.

### Phase 5 — In-document dashboards

A saved view stores the report and its chart controls only. A dashboard is a grid of those configs, rendered as components in the same document. Every tile uses the dashboard's window and filters. Import keeps twelve tiles and says how many were dropped. A stored URL becomes a config when its path is a known report, and a path that is not a report is counted and dropped. The layout no longer has an embed branch.

## Deviations

- The filter bar, chips, and save control still use rem gaps. The shell header and main use the space scale. That restyle is open issue 16 on design 7.
- Overview links to trends set `metric`, which is the key that page reads. The drill-down sentence says `measure`. That collision is open issue 17.
- Tiles other than hooks, builder, and usage render one primary chart each, not the full report page.
- Hooks tiles treat the stored dimension as the time-series split. The bar and treemap on a tile use fixed dimensions.
- The distribution shape check on the empty serve fixture sees no rows. Store tests cover the populated cases.
- A conversation request omits `from` and `to` when the range is all time, so the response omits window totals. Other reports clamp all time to 399 days.

## Review

Independent review against the phase outcomes. Verdict `PASS_WITH_FOLLOWUPS`. No blocker and no high finding. Four mediums were fixed in that review: conversation shift-click now excludes, the empty filter key is not clickable, notices use the theme's danger, surface, text, and border tokens, and the series bullet no longer says every chart gap is zero-filled. Open issues 13 and 14 were brought in line with the scalar builder and the executions shape filter.

## QA

There is no separate QA record. Each phase re-ran its own store, serve, unit, or Playwright checks, including the analytics smoke cases and the dashboard, usage, quality, and executions specs. The review re-ran the url-state, chart-option, theme, view, and tile unit tests (78 passed) and the area-chart end-to-end spec (2 passed). It did not re-run the Go tests or the rest of Playwright.

## Residual Risks

- The review's Go gap means a later edit could break a read the phase checks had already passed. The suite is the check.
- Open issue 13 still stands: builder `data-ready` stays true while the previous chart is shown, and stored views are dropped on read with no notice when they fail validation.
- A tie for the most frequent conversation model resolves to the smaller name. The fixture asserts a strict winner, not a tie.

## Follow-ups

Recorded as open issues 16 and 17 in [design 7](../design/07-analytics-site.md): restyle the filter bar, chips, and save control onto the space scale, and pick one query key for the overview trends links.

## Decisions Worth Keeping

- The new numbers are read-time aggregates on existing columns, inside the 400-day cap. There is no new table and no ingest change.
- A saved view stores chart controls only. One dashboard window and one filter bar apply to every tile. There is no iframe.
- A distribution has no `__other__` row. Weekday and hour are not filters. Conversation totals are the whole run, and the event cap truncates the list only.
