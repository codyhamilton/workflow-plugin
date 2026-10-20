# Remediation 01: logged-out navigation still mounts the dashboard

Severity: high.
Owned paths: `packages/yakka-analytics/src/routes/+layout.svelte`, `packages/yakka-analytics/tests/e2e/session.spec.ts`. Do not change `decideAfterMeFetch` or `shouldNavigateToProfile` in `src/lib/session-gate.ts` unless a test shows the pure predicate is wrong. Do not touch `packages/yakka`.

## Defect

The layout gate in `src/routes/+layout.svelte` (the `$effect` that calls `fetchMe`, about lines 58–97) does not keep a logged-out person out of the dashboard.

1. The effect calls `beginSessionGate()`, then `await fetchMe()`, then reads `page.url.pathname` and `page.url.search`. Those reads happen after `await`, outside the effect's update cycle, so they are not dependencies. The effect runs once per layout mount. A later client navigation does not re-run it. The header is rendered on `/login` and links to `/`. Load `/login` while logged out (stay path), then follow Overview. The predicate does not run again, `sessionGate.ready` is already true, and `LandingView` mounts.

2. When the decision is `{ login }`, the effect still calls `finishSessionGate` immediately after starting `goto`. `ready` becomes true while the URL is still the guarded route, so `{#if sessionGate.ready}` renders that route's children before navigation finishes. On `/` that starts `aggregate` (`/v1/analytics/facets` and `/v1/analytics/query`). The phase 1 contract says children do not mount until the call has settled, so a redirect does not also request analytics. `tests/e2e/session.spec.ts` "no analytics requests" opens `/usage`, which is now a retirement stub and does not fetch, so it does not catch this.

`decideAfterMeFetch` itself matches the document-load cases (loopback empty base stays, 200 stays, 401 with bearer and non-empty base stays, 401 with no bearer otherwise returns the login path, stay paths stay). Do not widen those cases.

## Why it matters

Phase 1 exists so a logged-out person does not remain in the shell. The shell's own Overview link is a path back in, and a direct open of `/` can start analytics reads before `/login` is shown. That is the failure the outcome names: an error panel, or the dashboard, instead of login.

## Fix approach

Keep one `fetchMe` per document load. Re-evaluate `decideAfterMeFetch` when `page.url.pathname` changes, using the remembered `me` body. Do not call `fetchMe` again on that re-check.

Do not call `beginSessionGate()` on a pathname change. That sets `ready` false and unmounts an investigation that is allowed to stay. Query-string changes on the same path (brush, drill, preset) must not refetch `/v1/me` and must not clear `ready`.

Render route children only when `ready` is true and `decideAfterMeFetch` for the current pathname returns `'stay'`. When it returns `{ login }`, `goto('/login?return=' + encodeURIComponent(pathname + search))` and do not render children for that pathname, so `/` does not start analytics. `/login`, `/oauth/callback`, and `/settings` stay, including when `/v1/me` is 401. The local empty-base case, the 200 case, and the 401-with-bearer-and-non-empty-base case stay, including after a client navigation onto those routes.

Leave the 403 `no such tenant` effect as it is.

## Done evidence

From `packages/yakka-analytics`:

- Add a Playwright case: non-empty base, no bearer, `GET /v1/me` is 401, open `/login`, click the header Overview link. The URL is `/login` with `return` decoding to `/`, and no request URL contains `/v1/analytics/`.
- Add a Playwright case: same session, `goto('/')` directly. End on `/login?return=/` (return decodes to `/`), and no request URL contains `/v1/analytics/`.
- Existing `tests/e2e/session.spec.ts` stays green, including empty-base stay, bearer stay, `/settings` stay, tenant on the landing query, and both 403 `no such tenant` cases.
- `tests/e2e/investigation-shell.spec.ts` stays green: a preset click and a brush still update the investigation URL and do not send the browser to `/login`.
- `npm test -- src/lib/session-gate.test.ts` passes without changes to the predicate cases.
