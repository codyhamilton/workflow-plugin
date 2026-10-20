# Brief: 1-01 — Session gate

Consumer: the phase 1 implementation worker.
Owned paths: `packages/yakka-analytics/src/routes/+layout.svelte`, `packages/yakka-analytics/src/routes/+layout.ts`, `packages/yakka-analytics/src/lib/api.ts`, `packages/yakka-analytics/src/lib/session-gate.ts`, `packages/yakka-analytics/src/lib/session-gate.test.ts`, `packages/yakka-analytics/src/routes/login/+page.svelte`, `packages/yakka-analytics/src/routes/oauth/callback/+page.svelte`, `packages/yakka-analytics/src/routes/device/+page.svelte`, `packages/yakka-analytics/src/routes/+page.svelte`, `packages/yakka-analytics/tests/e2e/session.spec.ts`, `packages/yakka-analytics/tests/e2e/settings.spec.ts`, `packages/yakka-analytics/tests/e2e/helpers.ts`, `docs/design/07-analytics-site.md`. Touch nothing else. A shared me result may live in `src/lib/session-gate.ts` (or `session-gate.svelte.ts` if `$state` is required). No other new files.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/1-01-session-gate.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit. Test results, not a file list, model, or cost.
Depends on: nothing.
Runs alongside: nothing.
Budget: 14 files to read, about 350 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Session gate, and Phase 1 — Session gate. Those two sections are the contract.
2. `packages/yakka-analytics/src/lib/api.ts` — `configuredBase` (private), `isCollectorMode`, `oauthLoginPath`, `fetchMe`, `TOKEN_KEY`, `BASE_KEY`. Read those functions, not the whole file twice.
3. `packages/yakka-analytics/src/routes/+layout.svelte` — the 401 error-panel link and the `noTenant` derived. This is what the gate replaces as the send.
4. `packages/yakka-analytics/src/routes/+layout.ts` — `ssr = false`.
5. `packages/yakka-analytics/src/routes/+page.svelte` — the `fetchMe` / `sessionTenant` / `withTenant` effect only (about lines 57–88).
6. `packages/yakka-analytics/src/routes/login/+page.svelte` — `oauthLoginPath` is called with no return.
7. `packages/yakka-analytics/src/routes/oauth/callback/+page.svelte` — the `return` path check (starts with `/`, not `//`).
8. `docs/design/07-analytics-site.md` — `## The site`, the first bullet only.
9. `packages/yakka-analytics/tests/e2e/helpers.ts` — `useServe`.
10. `packages/yakka-analytics/tests/e2e/session.spec.ts` and `packages/yakka-analytics/tests/e2e/settings.spec.ts` — the checks this unit must keep or change.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

After the document loads, one predicate on `GET /v1/me` either leaves the person on the opened route or sends them to `/login` or `/profile`, as Phase 1 states. The package does this send today only as an error-panel link.

## Contract

Cited from `DESIGN.md`, Domain: Session gate, and Phase 1. Settled.

> after the document loads, the gate calls `GET /v1/me` only, and the cases below are the whole predicate. The navigation is in the package (`src/routes/+layout.ts` sets `ssr = false`).
>
> - Loopback with an empty configured base stays on the opened route, even though `/v1/me` is 401 and `isCollectorMode()` is true.
> - A 200 stays. The aggregation boundary sends `?tenant=` from that body.
> - A 401 with a stored bearer and a non-empty base stays.
> - A 401 with no bearer, on any host that is not the local case, navigates to `/login?return=` the opened path and query. `/login`, `/oauth/callback`, and `/settings` stay. `/settings` is how the bearer gets stored. The GitHub link on `/login` passes that `return` through `oauthLoginPath`.
> - A 403 `no such tenant` goes to `/profile` only when `me` returned no tenant.

Non-goals in that domain: an HTTP redirect before the document is painted (`packages/yakka/internal/serve/serve.go` is out of scope). A flash of the document before the client navigates is accepted. Do not rework GitHub OAuth, the session cookie, or token issuance.

Phase 3 owns the aggregation boundary. This unit does not add it. The overview's existing `?tenant=` send is the stand-in the outcome names, until that boundary exists. Do not remove the overview's KPI tiles, the report nav, or `src/lib/theme.css`. Those are later phases.

## Changes

The predicate is a pure function in `src/lib/session-gate.ts`. The layout fetches and navigates. Do not put `goto` in `api.ts`. Do not change `fetchMe`'s transport, `isCollectorMode`, or `oauthLoginPath`'s shape.

Evaluate in this order. This is the whole predicate.

1. Call `fetchMe` once per document load from the layout, including when `isCollectorMode()` is false. That call is the gate's only HTTP request. Children do not mount until this call has settled, so a redirect does not also request `/v1/analytics/*`. A flash of the header is acceptable.
2. Stay paths for the 401 rule: pathname is exactly `/login`, `/oauth/callback`, or `/settings`. Do not add `/device` or `/profile` to this list. `/device` on a logged-out non-local host goes to login with `return` set to that path and query. Leave the device page's own sign-in link in place for loads that stay.
3. Local case: `location.hostname` is `localhost`, `127.0.0.1`, or `::1`, and the configured base is empty. Configured base is `localStorage` key `yakka-analytics-base`, trimmed, trailing slashes stripped, matching `configuredBase` in `api.ts`. This case stays, including when `fetchMe` is 401. `isCollectorMode()` is true here because an empty base returns true. That flag is not the login signal. Do not treat `!isCollectorMode()` as "send to login".
4. `fetchMe` 200: stay. Remember the body. The overview reads that body and sets `tenant` from the first `tenants[].name` when it is non-empty, on the analytics requests it already makes (`withTenant`). It does not call `fetchMe` itself. An empty `tenants` list sends no `tenant`. Do not build a new query layer.
5. `fetchMe` 401, stored bearer, non-empty configured base: stay. The bearer is `localStorage` key `yakka-analytics-key`, trimmed, non-empty. Read storage at decision time.
6. `fetchMe` 401, no bearer, not the local case, not a 401 stay path: navigate to `/login?return=` plus `encodeURIComponent(pathname + search)`. `search` includes the leading `?` when present.
7. Any other `fetchMe` result (network error, non-JSON, 500): stay. Do not treat it as logged out.
8. After a stay, when the layout's existing fetch error is status 403 and message exactly `no such tenant`, and the remembered me body is a 200 with no tenant name: navigate to `/profile`. When me returned a tenant, do not navigate. When me did not return a 200 body, do not navigate. When the pathname is already `/profile`, stay.

`/login` reads the `return` query and passes it to `oauthLoginPath(hostname, return)` only when it starts with `/` and does not start with `//`, the check `oauth/callback/+page.svelte` already uses. Otherwise call `oauthLoginPath` with no return. Missing `return` stays the current call.

`+layout.ts` stays `ssr = false` and `prerender = false`. No server `load`.

`oauth/callback/+page.svelte` and `device/+page.svelte`: leave their jobs. Touch them only if a stay-path bug cannot be fixed from the layout.

`docs/design/07-analytics-site.md`, `## The site`, first bullet: replace the sentence that says an unauthenticated analytics GET is 401 and the layout sends the browser to `/login`. State the predicate above, including the local stay, the 200 tenant send, the bearer stay, the `return` query, the three stay paths, the GitHub link, and the 403 rule. Keep the cookie, admission, and `POST /logout` sentences in that bullet. Do not edit the Theme sentences.

`tests/e2e/helpers.ts` `useServe(page, 'local')` stores a non-empty base and no bearer. `GET /v1/me` on that serve is 401 (`sessionOnly` rejects a missing session). That is the redirect case, so those tests would leave the opened route. Do not widen the predicate to keep them green. Also store `yakka-analytics-key` to the literal `e2e-local-stay` for the local helper only, which is the contract's "401 with a stored bearer and a non-empty base stays". Local-mode serve authorizes before it reads a bearer. No e2e spec asserts that local analytics requests omit `Authorization`. Keyed `useServe` is unchanged.

`tests/e2e/settings.spec.ts`: with the key cleared and the keyed base still stored, `goto('/')` is the redirect case. The error-panel assertion on `/` becomes: the URL path is `/login` and the `return` query decodes to `/`. The earlier assertion, bearer sent on summary while the key is stored, stays.

### Keep untouched

Report nav, theme switch, `FilterBar`, charts, and the overview's KPI tiles. Phase 2 and phase 4 own those. `packages/yakka/internal/serve` and every other workspace package. `isCollectorMode` and the OAuth callback's exchange. Profile, settings, and device page jobs other than the gate's navigation around them.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `npm test -- src/lib/session-gate.test.ts` in `packages/yakka-analytics` → fails before the predicate exists; passes after, with one case each for: loopback empty base + 401 stays (`localhost` and `127.0.0.1`); `yakka.build` empty base + 401 + no bearer navigates to login with the opened path as `return`; 401 + bearer + non-empty base stays; 401 + no bearer + non-empty base on `127.0.0.1` navigates to login; 200 stays; 403 `no such tenant` + 200 with no tenants navigates to `/profile`; the same 403 + 200 with a tenant stays; `/login`, `/oauth/callback`, and `/settings` with 401 + no bearer + non-empty base stay; a non-401 `fetchMe` failure stays.
- `npx playwright test tests/e2e/session.spec.ts tests/e2e/settings.spec.ts` in `packages/yakka-analytics` → passes, including the two session tests already in that file, and these new ones:
  - empty base, `/v1/me` routed to 401, `goto('/trends?range=7d')` stays on that path and query, and the first `/v1/` request is `/v1/me`
  - `localStorage` base `https://collector.example`, no key, `/v1/me` routed to 401, `goto('/usage?range=7d')` ends on `/login` whose `return` decodes to `/usage?range=7d`, and no request URL contains `/v1/analytics/`
  - that same base with `yakka-analytics-key` set, `/v1/me` 401, stays on `/usage?range=7d`
  - that base, no key, `goto('/settings')`, `/v1/me` 401, stays on `/settings`
  - `goto('/login?return=' + encodeURIComponent('/trends?range=7d'))` on the preview host: the `login-link` href is `/oauth/login?return=` plus the encoded path
  - `/v1/me` 200 with `tenants: []`, summary routed to 403 `{ "error": "no such tenant" }`, `goto('/')` ends on `/profile`
  - `/v1/me` 200 with `tenants: [{ name: 'acme' }]`, summary 403 `no such tenant`, the path is not `/profile`
  - the existing "collector overview sends tenant from /v1/me on summary" test still sees `tenant=acme`
- `npm test` in `packages/yakka-analytics` → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
