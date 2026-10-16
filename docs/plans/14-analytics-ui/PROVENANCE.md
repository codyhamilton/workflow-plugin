# Provenance: Analytics UI

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 16, 2026)
- Timestamp: 2026-10-16T11:47:42Z
- CWD: /home/codyh/workspace/workflow-plugin (HEAD `bbb3818`)

## Initial Request (verbatim)

> /design improvements to the analytics UI. it's extremely basic at the moment, needing:
> - Cleaner style, make it minimalistic but clean, well spaced and modern. Go with a solarized inspired theme (light/dark modes)
> - All charts and reports should be interactive where reasonable, with drill down and time window selection, dynamic filtering
> - Have separate subagents look at each of the pages and dashboards and reimagine them. We want to be able to compare model against model, trend changes and visualise distributions using appropriate graph types, it should be rich and interactive

## Design Conversation

### Turn 1

**Agent asked:** How far the analytics API should move (site-only composition of today's routes, or site plus the read aggregates the reimagined views need). Which tree the design should name, given plan 13 will move `tools/workflow`. Whether dashboard tiles keep their own windows or share a dashboard-level window.

**User responded:** Site plus the read aggregates (percentiles or bins for cost and tokens by model, score series over time, execution shape by bucket, usage columns on the conversation list, server-side shape filter), with no ingest changes. The current tree; plan 13 rebases onto it. On dashboards: "don't use iframes, this is a svelte app it doesn't need to be this way. structure it like a proper dynamic modern app."

**Agent decisions:**

- The new reads are in the design, computed at read time on existing columns, inside the 400-day cap.
- Surfaces stay `packages/workflow-analytics` and `tools/workflow`.
- A dashboard tile is a report component in the same document. It does not keep a private window or a private filter set. The dashboard URL's filter bar is the only one. A saved view stores chart controls, not filters.

## Agent Decisions

- **Plan folder**: `docs/plans/14-analytics-ui/`. Rationale: plan 13 is the highest number, and it is an open monorepo design, not this work.
- **Ground**: one recon pass per page group, plus the analytics API. The site already has ECharts, a URL filter set, brush-to-zoom on some time charts, and drill on some bars. The chrome is a flat link list on a generic gray palette that follows the system scheme only. Several pages never wire the interactions design 7 already requires.
- **Chart grammar**: stay on ECharts, with Perspective only on Explore. Rationale: design 7 forbids a second chart grammar, and the missing chart types (histogram, box, stacked share, small multiples) are ECharts series.
- **Routes**: keep the current route set. Reimagine what each page shows. Rationale: the request is about those pages, not a new information architecture.
- **Distribution honesty**: no `__other__` bucket. Fixed bin edges so models share an axis. Heatmap cells do not become filters.
- **Conversation totals**: `totals` is the whole run; a window slice has its own `window_totals`, and the event list is not filtered by the window. Rationale: a capped event list cannot be the denominator for a window comparison, and the run outside the window stays visible. This was not in the session's API answer; the session named list usage columns.
- **Adversarial pass**: applied the contract fixes (error strings, `n` vs `unpriced`, ignored filters, no `partial` on column scans, bucket `t`, shape OR, import keeps 12, phase-1 color check, token histogram, hooks via `/query`, brush on the new time axes, distinct-content link measure). Dropped the prior-window KPI badge and the explore stale-row fix. Kept five phases with a required bullet per route. The shared dashboard filter was struck until asked.

### Turn 2

**Agent asked:** When a saved view is placed on a dashboard, does the tile follow the dashboard's window and filters, or keep the ones from when it was saved?

**User responded:** The dashboard's. One filter bar and one window for every tile. A saved view stores the chart only, not the filters that were on screen when it was saved.

**Agent decisions:**

- `params` holds chart controls only. A migrated URL keeps chart keys and drops window and filter keys. Changing the dashboard window updates every tile.

### Turn 3

**Agent asked:** nothing. Execute had stopped on Phase 1.

**User responded:** "Update the design to make this workable."

**Agent decisions:**

- Phase 1's color outcome stays a whole-site rule. Its surfaces gain every file that sets a stylesheet hex today: the chart components, the filter bar, and the conversation, conversations, executions, explore, repos, and builder pages. A test stub is excluded from that scan. Notices reuse `danger`, `surface`, `text`, and `border` rather than a new hex. The space scale applies to the shell's own padding and control gaps, not to a route's section gap, because usage, trends, and dashboards are not in this phase. Phase 1 stays one unit.
