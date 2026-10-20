# Brief: 2-02 — Chart frame

Consumer: the phase 2 chart-frame worker.
Owned paths: `packages/yakka-analytics/src/lib/analysis/chart-frame/` (new), `packages/yakka-analytics/src/lib/analysis/chart-frame.test.ts` (or colocated `*.test.ts` under that tree). Touch nothing else except imports from existing `src/lib/analysis/` token exports (read-only).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/2-02-chart-frame.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `2-01-analysis-shell` (analysis color tokens and theme switching must exist under `src/lib/analysis/`).
Runs alongside: nothing.
Budget: 12 files to read, about 400 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Component and style system (chart frame bullets); Phase 2 outcome (system includes chart frame as part of the domain, even though shell e2e does not exercise charts yet).
2. `packages/yakka-analytics/src/lib/analysis/` — token CSS and any exports from `2-01` (read what exists after that unit lands).
3. `packages/yakka-analytics/src/lib/charts/EChart.svelte` — grep props (`build`, `onclick`, `onbrushend`) only; this is the old frame, not to extend.
4. `docs/design/07-analytics-site.md` — Drill-down and window sentences (grep `brush` and `shift-click`) for handler semantics only.
5. `packages/yakka-analytics/src/lib/types.ts` — grep `QueryResponse`, score types if present; use as hints, not as the phase 3 boundary contract.

Read ranges and grep; do not read all of `src/lib/charts/`.

## Goal

Add the package-owned **chart frame** for the analysis system: a presentational component layer that can draw trend, breakdown, distribution, and quality score-band views from data passed in, with slots/callbacks for hover, brush, and drill, without fetching.

## Contract

Cited from `DESIGN.md`, Domain: Component and style system. Settled.

> The chart frame renders a series, a breakdown, a distribution, or a score band. The chart frame's input is the boundary result for `trend`, `breakdown`, `distribution`, and `quality`, and the view passes hover, brush, and drill. The frame does not fetch.
>
> A screen this redesign adds takes its layout, color, and chart frame from this system. It does not take them from `src/lib/theme.css`, from `FilterBar` / `FilterChips` / `SaveView` / `DashboardTile`, or from `src/lib/charts/`.
>
> A library may implement the chart frame or the tokens. This design names no library and no version.

Implementation decision (not design): you may choose a chart library inside this unit; the design names none. Say so in the report if you choose one.

Phase 3 owns the aggregation boundary. This unit defines **frame-level** TypeScript props that mirror the boundary `ask` shapes described in DESIGN (trend points + optional breakdown dim, breakdown rows, distribution bins, quality score band + baseline). Stub or minimal structs are fine; do not call `/v1/analytics/*` or add the boundary module.

## Changes

Under `src/lib/analysis/chart-frame/`:

- Export a small set of Svelte components (or one component with a `kind` prop) covering at least: **trend** (time series), **breakdown** (categorical rows), **distribution** (bins), **quality** (score band beside baseline + bucketed series with gaps allowed).
- Read colors and type from analysis tokens (`getComputedStyle` on the analysis root or imported token helpers from `src/lib/analysis/`). No solarized hex literals in the frame source.
- **Callbacks** — expose optional handlers for element hover, time-axis brush end (window change intent), and drill on a filter dim value. Document in props which marks are drillable; non-drillable dims match design 7 (`__other__`, empty key, `hour_of_day`, `weekday` are not drill targets). Shift-click exclude is a view concern; the frame may surface a click event with modifier keys so phase 5 can wire exclude.
- **No fetch** — no `getJSON`, no `api.ts`, no `query.ts` imports.
- Do not import from `src/lib/charts/` or mount `EChart.svelte` inside the new frame.
- Do not wire the frame into `+page.svelte`, report routes, or layout in this unit (phase 4/5 integrate). A vitest harness with fixture data is enough.

Prefer one module entry (`index.ts`) exporting the public components and prop types.

### Keep untouched

`src/lib/charts/`, `src/lib/theme.css` (except via computed tokens), layout, session gate, report pages, `query.ts`, `view.svelte.ts`, `api.ts` analytics paths.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npm test -- src/lib/analysis/chart-frame` → all new tests pass; at least one test per `kind` (trend, breakdown, distribution, quality) asserting the component renders without throwing and uses a non-empty series color from tokens (not `#002b36` / `#fdf6e3`).
- `cd packages/yakka-analytics && npm test` → full package unit suite passes.
- Observable: no new imports from `src/lib/charts/` under `src/lib/analysis/chart-frame/`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, library choice if any, deviations, and contradictions. Do not spawn subagents beyond read-only helpers.
