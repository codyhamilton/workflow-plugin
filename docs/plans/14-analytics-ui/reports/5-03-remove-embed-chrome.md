# Execution report: 5-03 — Remove embed mode, dashboard chrome

**Status:** done

## What changed

- **`+layout.svelte`**: Removed the `embed` derived flag and `{#if embed}` branch; header and main always render. `chrome` is now true on every route except `/settings`, so `/dashboards` gets FilterBar, FilterChips, Notices, and SaveView.
- **`shell.spec.ts`**: Replaced the embed-only-shell test with one that asserts `/dashboards?range=7d` shows `preset-7d` pressed and `saveview-save`, and that `/trends?range=7d&embed=1` still shows one header plus filter chrome and the trends chart.

## Check output

**Before** (old embed test still in tree; `E2E_PORT=4423 npx playwright test tests/e2e/shell.spec.ts -g "embed|dashboards"`):

```
2 passed (17.8s)
  ✓ embed mode renders the page without the shell
  ✓ the nav links to Builder and Dashboards
```

The replaced test would fail against pre-change layout: `/dashboards` hid filter chrome and `embed=1` skipped the header.

**After:**

```
2 passed (51.5s)
  ✓ dashboards shares filter chrome; embed=1 no longer hides the shell
  ✓ the nav links to Builder and Dashboards
```

No test navigates to `embed=1` expecting a hidden shell.

## Departures

None.

## Contradictions

None between this brief and DESIGN Phase 5 / Dashboards domain (single shell, no embed branch, dashboards share the dashboard URL window).

## Known problems

None in done-evidence scope. Other code paths may still emit or link `embed=1`; out of scope for this unit.
