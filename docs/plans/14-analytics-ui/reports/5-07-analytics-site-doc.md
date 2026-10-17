# Execution report: 5-07 — Analytics site design doc delta

**Status:** `done`

## What was done

Updated `docs/design/07-analytics-site.md` **The site** section per plan 14 Phase 5 and the brief:

- **Theme:** Documented `workflow-analytics-theme`, `data-theme`, `system`/`light`/`dark` override (replacing system-preference-only wording), light/dark hex surfaces, accent/danger, series order, and space scale.
- **Saved views and dashboards:** Replaced stored-URL + framed embed model with view/dashboard JSON shapes, 12-tile cap and import drop rule, in-document tile render, shared window/filters, URL→config import, and export/import as JSON.
- **Drill-down / interaction:** Overview KPI link targets and `/trends` `measure` rule; non-clickable `__other__`, empty key, `hour_of_day`, `weekday`, and check names; zero-fill for count series only vs score gaps.
- **Open issue 12:** Removed the stale clause that conversation totals cover only returned events when truncated (aligned with the `/conversation` contract on the same page).
- **Open issue 13:** Removed dashboard clauses superseded by Phase 5 (import cap bypass, embed fragment, iframe settle signal); kept builder clauses and saved-view read validation.

Only owned path touched besides this report.

## Done evidence (rg)

**Before**

```
$ rg "embed=1" docs/design/07-analytics-site.md
  of saved views, rendered as framed `embed=1` pages ...
13. ... fragment in a saved URL drops `embed=1`, ...

$ rg "totals cover only the returned events" docs/design/07-analytics-site.md
12. ... conversation totals cover only the returned events when a timeline is truncated; ...

$ rg "workflow-analytics-theme" docs/design/07-analytics-site.md
(no matches)

$ rg "in-document|chart configuration" docs/design/07-analytics-site.md
URL is the view: ... every chart configuration ...
```

**After**

```
$ rg "embed=1" docs/design/07-analytics-site.md
(exit 1, no matches)

$ rg "totals cover only the returned events" docs/design/07-analytics-site.md
(exit 1, no matches)

$ rg "workflow-analytics-theme" docs/design/07-analytics-site.md
  colours). **Theme.** `localStorage` key `workflow-analytics-theme` holds ...

$ rg "in-document|chart configuration" docs/design/07-analytics-site.md
URL is the view: ... every chart configuration ...
  ... renders each tile in-document as a component ...
```

## Departures

None.

## Contradictions (not resolved here)

- Open issue 13 still says builder with zero dimensions and bucket `none` renders a chart with no valid type. Plan 14 **Domain: Dashboards** says that case renders the scalar and is a valid saved view. Left as-is because this unit only trims dashboard clauses in item 13, not builder text.

## Known problems outside done evidence

None found in scope.

## Unfinished work

None for this brief.
