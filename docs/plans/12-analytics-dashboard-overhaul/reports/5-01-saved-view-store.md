# Report: 5-01 — Saved-view and dashboard store

Status: **done**

## What changed (against each part of the brief)

- `packages/workflow-analytics/src/lib/views.ts` (new), pure TS, no Svelte/`$app`. Exports `SavedView`, `Dashboard`, `ViewStore`, `ImportError`, `createStore(storage?)`, `store`. Implements all twelve `ViewStore` methods plus `isValidViewUrl` (shared by `saveView` and import). Storage keys `workflow-analytics-views:views` / `:dashboards`, JSON arrays. `saveView` replaces a same-name view in place (keeps id) and validates the url. `deleteView` cascades into every dashboard. `exportDashboard` emits exactly `{"version":1,"name":…,"views":[{"name":…,"url":…}]}` in dashboard order, no ids. `importDashboard` validates first (parse, `version===1`, array `views`, every url), and on any failure throws `ImportError` writing nothing; on success it allocates a de-duplicated name (` (2)`, …), reuses an existing view with the same name+url or creates one, and returns the new dashboard. Every read/write is try/catch; corrupt JSON reads as `[]`; ids use `crypto.randomUUID()` else a module counter; `createStore()` probes `localStorage` in try/catch, else an in-memory backing. `subscribe` notifies after every write and on the window `storage` event when `window` exists, and returns an unsubscribe.
- `packages/workflow-analytics/src/lib/views.test.ts` (new), 20 vitest cases over an injected fake in-memory `Storage`: save/replace keeps id; url rule on `saveView`; delete cascade; dashboard add/move/remove with duplicates; exact export string; export→import into a second store reproduces name/order/urls; duplicate-name bump + view reuse; eight `ImportError` cases each asserting `setItem` never called and both lists empty; the 2000-char boundary; throwing storage still works in memory; corrupt JSON reads empty; subscribe/unsubscribe.
- `api.ts` and every other file untouched.

## Check output

Before (`npm test -- views`, files absent):

```
No test files found, exiting with code 1
filter: views
```

After (`npm test -- views`):

```
✓ src/lib/views.test.ts (20 tests) 24ms
Test Files  1 passed (1)
     Tests  20 passed (20)
```

`npm test` (all suites):

```
Test Files  11 passed (11)
     Tests  94 passed (94)
```

`npm run build`:

```
✓ built in 9.31s
Run npm run preview to preview your production build locally.
  Wrote site to "build"
  ✔ done
```

## Deviations

1. **Extra exports beyond the brief's list.** Also export `VIEWS_KEY`, `DASHBOARDS_KEY`, and `isValidViewUrl`. Reason: tests assert the key names and the boundary rule directly; the validator is reused by both `saveView` and import. All required names are present with the specified signatures.
2. **`store` is `createStore()` (no argument).** The brief writes `createStore(localStorage when usable, else in-memory)`; calling `createStore()` performs exactly that probe/fallback internally, so behaviour matches.
3. **Import name is not type-checked.** A non-string `name` is coerced to `''` rather than rejected; the brief lists the `ImportError` cases and missing-name is not among them. Url validation is exactly as specified.
4. **Out-of-range `moveInDashboard`/`removeFromDashboard` are no-ops** (unknown dashboard id still throws a plain `Error`). Unspecified by the brief.
5. **Tests inject a fake `Storage`** rather than `vi.stubGlobal('localStorage', …)`; the brief requires a fake in-memory `Storage`, and a throwing-storage test cannot use the stub flavour. Style otherwise matches `api.test.ts` (vitest, colocated, `vi.fn`).

## Contradictions

None between the brief and the contracts it cites (DESIGN.md "Saved views and dashboards" / "The URL is the view"; `urlstate.ts`; `api.ts`). The only tension is the phrase "Export exactly": it constrains the runtime export string (which matches byte-for-byte), while the module additionally exports the storage keys and validator for testability — a superset, not a conflict.

## Unfinished

None.

## Known problems

- **In-memory arrays are a snapshot loaded at `createStore()`.** A `storage` event notifies subscribers but the store does not reload, so a listener that re-`list`s on another tab's write sees this store's stale snapshot. The brief only requires the notification, so this is by design; a consumer needing live cross-tab state should create a fresh store or the unit should be extended to reload on the event.
