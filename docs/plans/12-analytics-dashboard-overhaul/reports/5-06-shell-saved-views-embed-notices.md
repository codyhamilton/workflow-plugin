# Report: 5-06 — Shell: save-view control, nav, embed mode, notices that persist

Status: **done**

## What changed (against each part of the brief)

- `src/lib/components/SaveView.svelte` (new). Uses `store` from `views.ts` (5-01) and a reactive copy refreshed by `store.subscribe` (unsubscribed via the effect's teardown). Saves `page.url.pathname + search` under the entered name with `store.saveView`; the stored url has `embed` removed, so it never contains `embed=1`. Renders exactly the required ids: `saveview-name` (input), `saveview-save` (button), `saveview-menu-toggle` (button, `aria-expanded`), `saveview-item` (a link per saved view, `href` = stored url), `saveview-delete` (per item). Empty name is a no-op; a save error is shown.
- `src/routes/+layout.svelte`. Nav gains `/builder` ("Builder") after Trends and `/dashboards` ("Dashboards") before Settings; `navHref` and the error panel are unchanged. Added `embed` (`page.url.searchParams.get('embed') === '1'`); when set, the layout renders only `{@render children()}` (no header, nav, FilterBar, chips, notices, save control or error panel), and filters still come from the URL. `chrome` (FilterBar, FilterChips, Notices, and now SaveView) is off on `/settings`, `/conversation` and also `/dashboards`.
- `src/lib/state.svelte.ts` + `src/lib/components/Notices.svelte` (notices fix). A notice now carries the `pathname + search` it was set for (`Notice.view`). The layout registers the current view in an `$effect.pre` (flushes before regular effects), so a notice a request sets for this view is tagged with it. The layout effect now calls `pruneNotices()` instead of `clearNotices()`; `pruneNotices` drops only notices belonging to another view, so the current view's notice survives the navigation that triggered it. `Notices.svelte` renders only notices whose `view` matches the current view. `query.ts` (5-11) was not touched.
- `tests/e2e/shell.spec.ts`. Four tests added: saved view listed + survives reload; `?embed=1` hides header/presets/save control while the chart renders; `/builder` and `/dashboards` nav links exist; the `hook_events` + `kind=brief` Trends notice persists 500 ms after a preset click whose query is a cache hit.

## Check output

Before (notice regression test, code unchanged):

```
tests/e2e/shell.spec.ts:116 › an ignored-filter notice survives a view change that re-requests it
Error: expect(locator).toBeVisible() failed
Locator: getByTestId('notice-ignored')  Expected: visible  Received: element(s) not found
          at shell.spec.ts:118
1 failed (exit 1)
```

A diagnostic spec confirmed the cause: `/v1/analytics/query?...&kind=brief&measure=hook_events...` returns `{"ignored_filters":["kind"],...}`, so the notice is set, but it was never observed visible at 100 ms…5100 ms — the layout's `clearNotices` erased it within a frame.

After (`E2E_PORT=4506 npm run test:e2e -- shell.spec.ts`):

```
10 passed (15.7s)
  ✓ a saved view is listed and survives a reload
  ✓ embed mode renders the page without the shell
  ✓ the nav links to Builder and Dashboards
  ✓ an ignored-filter notice survives a view change that re-requests it
```

`npm test`: `Test Files 12 passed (12) / Tests 117 passed (117)`. `npm run build`: exit 0, `Wrote site to "build" ✔ done` (only the pre-existing chunk-size warning).

## Deviations

1. **Notices mechanism.** The brief's example was to clear a slot's notice when the slot *starts a new request*. `query.ts` (5-11) exposes no request-start hook and is off-limits, so the notice is instead keyed to the view (`pathname + search`), the layout registers the view in `$effect.pre`, and `pruneNotices` drops other-view notices. This meets the stated outcome ("a notice set by a request for the current view survives until that view changes again") without editing `query.ts`. Reported here as a departure from the suggested mechanism, not the contract.
2. **`clearNotices` is kept** (still exported, no longer called by the layout). Removing it would touch nothing else but the brief did not ask for removal, and a caller outside the owned paths could rely on it.
3. **Save control placement** is inside the `chrome` block (with FilterBar/chips), which resolves to exactly the required route set; the brief did not specify placement.

## Contradictions

None material. The brief says a notice should survive "until that view changes again" and clear "not on navigation": these are consistent if "view" is the URL — a same-URL navigation keeps the notice, and a new URL drops it (and re-sets it if the new view's request produces one). The slot-request mechanism example is the only departure (above).

## Unfinished

None. `/builder` and `/dashboards` routes are owned by 5-07/5-08; the shell links to them (SPA fallback, no prerender, so the build does not require them).

## Known problems

- The self-clear was worse than "a frame": on initial load the notice was effectively never seen at the diagnostic's 100 ms sampling. Same root cause, now fixed.
- No other non-trivial bug found.
