# 5-09 — Executions sankey and link filter

Status: **done**

Commit: `e10b812` — "Add executions sankey with link-filtered table".

## What changed

`src/routes/executions/+page.svelte` (+74/-4):

- Added `NODES` (`design`, `brief`, `commit`, `report`, `nocommit`, `noreport`) and `LINKS` with the
  brief's five edges and their shape sets; link values computed from the loaded `counts`.
- Added `selected` (page-local `?shape=` param via `view.setParam`), `empty`, `linkData`,
  `filteredRows`, `sameSet`, `applyShapes`, `onLinkClick`. A link click toggles: same set -> clear
  (`shape=null`), else set. design→brief has `shapes: []` so it always clears.
- Markup: above the table, `<SankeyChart testid="exec-sankey" .../>` plus one plain
  `<button data-testid="exec-link-<source>-<target>" aria-pressed=...>` per link calling the same
  handler. Table body now iterates `filteredRows` (client-side shape filter). When all counts are 0:
  `<p data-testid="exec-empty">No executions in this window</p>` and no chart.
- Tiles still show the unfiltered `counts`; `Pager`, endpoint, query construction and `exec-*` ids
  unchanged.

`tests/e2e/executions.spec.ts` (+23): two tests — sankey + all five link controls visible; clicking
`exec-link-commit-report` sets `shape=complete`, narrows to the one `complete` row, survives reload,
and clicking again restores all three rows. Existing 7 tests unchanged.

## Check output

BEFORE (only the two new tests added, page unmodified):

```
9 tests: 2 failed, 7 passed
  ✘ shows the execution sankey and its link controls
  ✘ clicking a sankey link filters the table and toggles off
```

AFTER (page implemented):

```
9 passed (17.1s)   # stable across two runs
```

`npm test`: 15 files, 148 tests passed. `npm run build`: passed, site written to `build`.

## Departures from the brief

1. **Fetch-key guard implementation.** The brief's plan guard (`lastKey` early-return before the
   cleanup) broke every existing test: a skipped re-run still runs the previous effect's cleanup
   (`live=false`), which cancelled the in-flight request when a late facet response recomputed
   `params` to an equal query, so counts never loaded. Replaced it with a correct stable-key guard:
   the effect depends on `queryKey = $derived(params?.toString() ?? null)` and reads `params` with
   `untrack` (the codebase convention in `routes/+page.svelte:64` and `usage/+page.svelte:65`). A
   `shape`-only URL change (or an equal-query facet recompute) does not change `queryKey`, so the
   effect does not re-run and the in-flight request survives. Same intent, different mechanism.
2. **No per-row design reference (requested deviation note).** `/executions` rows begin at a brief
   and carry no design reference, so `design→brief` represents the whole window (value
   `complete+unreported+started`) and its click clears the filter rather than narrowing. Recorded as
   the brief required, not hidden.
3. **Node ids vs labels.** Ids are `nocommit` / `noreport` (needed for space-free
   `exec-link-brief-nocommit` / `exec-link-commit-noreport` test ids); labels are `no commit` /
   `no report`. The brief asks for exactly this.

## Contradictions between the brief and the contracts it cites

None found. The settled `SankeyChart`/`sankey.ts` props, `view.setParam`, `urlstate.toSearch` and
the fixture all match the brief.

## Known problems (plain)

- The chart-edge click path (`onlink` from an ECharts `edge`) is wired but untested; only the button
  path is covered. Chart clicks are geometry-dependent, so the brief allows this.
- `design→brief` never shows `aria-pressed="true"`: its shape set is empty (it clears), and the
  markup only marks a pressed link when `shapes.length > 0`. Matches the toggle contract.
- The empty-window message only appears once a response with all-zero counts arrives; before the
  first response the block does not render at all (unchanged from the brief's "counts && params"
  gate).

## Unfinished work

None. All four owned changes (chart, buttons, client filter, filtered table) and both tests are in
place and green.
