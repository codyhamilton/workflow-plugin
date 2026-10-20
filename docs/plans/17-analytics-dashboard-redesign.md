# Analytics dashboard redesign

The analytics dashboard in `packages/yakka-analytics` was replaced. After the document loads, a logged-out person is sent to login, `/` opens on two trends, and usage, cost, quality, conversations, and saved analysis are tools on that same path. The old report routes no longer render those reports. The work did what it set out to do. A review found that a client navigation could still mount the dashboard, and that was fixed before close-out.

## Intent

User request, verbatim:

> The analytics dashboard needs a total redesign. We did have a prior plan to do this but it was too conservative. To be clear, just about everything needs replacing. The UI is cumbersome, the layout and styling not usable. We'd need a few passes over this, redesigning the style and component system, rethinking the dashboards and data layouts. I'd like to see landing dashboard with a good quick view into trending data, I'd like the graphs and visualisations to be rich and dynamic and interactive. Also a minor thing if the user isn't logged in just direct straight to login.
>
> create a thorough design to rethink the UI. Keep the changes just to the analytics dashboard package

## Why This Existed

[Plan 14](14-analytics-ui.md) kept the route set, the solarized sheet, and ECharts report pages, and only replaced iframe dashboards with in-document tiles. A person who was not logged in saw an error panel with a sign-in link. Each report built its own analytics requests. `/` was KPI tiles, grouped counts, and a weekday-by-hour heatmap.

## What Was Built

The lasting contracts are in [design 7](../design/07-analytics-site.md): the session gate, the analysis tokens and chart frame, the aggregate boundary, landing and investigation on `/`, and the retired report URLs.

**Changed:** `packages/yakka-analytics` and design 7. No new serve route and no store change.

### Phase 1 — Session gate

The layout calls `GET /v1/me` once per document load. Loopback with an empty base stays on a 401. A 200 stays, and analytics requests send `?tenant=` from that body. A stored bearer with a non-empty base stays. Otherwise the browser goes to `/login?return=`. `/login`, `/oauth/callback`, and `/settings` stay. A 403 `no such tenant` goes to `/profile` only when me returned no tenant. Route children render only when the decision for the current pathname is stay, and a later navigation reuses the remembered result.

### Phase 2 — Analysis component and style system

Logged-in `/`, `/login`, and the identity routes share one background and type color, neither `#002b36` nor `#fdf6e3`. The chart frame draws a trend, a breakdown, a distribution, or a score band, and does not mount the old `EChart` module. The report nav stayed through this phase.

### Phase 3 — Aggregation boundary

`aggregate` returns one result for `trend`, `breakdown`, `distribution`, `quality`, `conversations`, `conversation`, and `executions`. Callers pass that request and do not name analytics URLs. The result carries `clamp`, `partial`, `ignored_filters`, and `truncated` when the read produced them.

### Phase 4 — Landing trend view

Empty `/` shows two day trends, `hook_events` and `cost_usd`, for the default thirty-day window, drawn by the chart frame. The nine KPI tiles and the heatmap are gone.

### Phase 5 — Interactive analysis

A control on the landing opens `/?ask=trend` on that window and those two measures. Brush, a breakdown change, and a drill update the graph. The address round-trips the request. Usage and cost, quality, conversation grain, and saved analysis are tools on that page. The eleven old report paths show a retirement stub. The header is Overview, Profile, and Settings.

## Deviations

- Usage and quality still call `aggregate`, through separate in-flight slots so one read does not cancel the other.
- Retired URLs stay on their path and show a stub.
- The review corrected three chart defects: a quality series for a preset window, a score band from p25 to p75, and one histogram per model.
- Choosing executions fetches and draws nothing. The shell shows `ignored_filters` and does not show `clamp`, `partial`, or `truncated`.

## Review

Independent review of the whole design. At the reviewed tree the verdict was `REMEDIATE`: phase 1 was partial, and phases 2–5 were met. Assumptions 1–3 held. Three mechanical chart defects were fixed in that review. The remaining high finding was logged-out navigation: Overview from `/login`, and a direct `/`, could mount the dashboard and start analytics. That was fixed afterwards. The session-gate unit tests (10), the session end-to-end file (12, including those two cases), and the investigation-shell end-to-end file (6) passed. No blocker or high finding stands.

## QA

There is no separate QA record. Each phase re-ran the unit and Playwright checks named in its outcome. The review re-ran `npm test` (250 passed) and the analysis-shell, shell, overview, session, investigation-shell, and investigation-tools Playwright files (33 passed). Close-out re-ran the session-gate unit tests, `session.spec.ts`, and `investigation-shell.spec.ts` after the navigation fix.

## Residual Risks

- A full Playwright run stays red on the retired-report specs, so a failure there is not a new regression signal.
- `tsc --noEmit` still reports errors in older tests and the retired chart modules. `npm test` does not typecheck.
- Conversation `window_totals` stored as whole seconds, and conversation-grain unpriced accounting, stay in `packages/yakka`.
- The document can paint before the client navigates to login. An HTTP redirect before paint was left out of the package.

## Follow-ups

Recorded as open issues 19–22 in [design 7](../design/07-analytics-site.md): draw the executions ask, retire the old Playwright files, show `clamp`, `partial`, and `truncated`, and register the brush toolbox. The design 7 sentence that gave every chart a data-table toggle was corrected; the analysis frame has none. Open issues 16 and 17 are closed because the filter chrome and the overview report links are gone.

## Decisions Worth Keeping

- Unauthenticated users are sent to login from inside the package, after the document loads. Loopback with an empty base stays.
- The landing picture is `hook_events` and `cost_usd`. Repos, hooks, and execution shape are breakdowns. Explore and the twelve-tile grid do not return.
- A saved analysis is `{ id, name, spec }` in `localStorage`, where `spec` is the aggregate request.
- The chart frame names no library. This build uses ECharts in a new host and does not mount the old chart module.
