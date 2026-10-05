# Brief: 2-01 — Site shell, API client, filters, overview and settings

Consumer: a worker dispatched by the plan 10 phase 2 orchestrator. Units 2-02, 2-03 and 2-04 build
their report routes on the client, filter state, layout and e2e harness this unit leaves; the
orchestrator verifies the phase outcome with the e2e suite this unit starts.
Owned paths: everything new under `packages/workflow-analytics/` except `src/routes/{trends,repos,hooks,quality,executions,conversations,explore}/`, `src/lib/charts/`, `src/lib/components/Pager.svelte` and their e2e specs (those belong to 2-02..2-04); plus `docs/plans/10-workflow-analytics/reports/2-01-site-shell.md`. Touch nothing else — not `tools/`, not other packages, not the repo root.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/2-01-site-shell.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing in this phase (phase 1's `/v1/analytics/*` routes are on this branch).
Runs alongside: nothing. 2-02, 2-03 and 2-04 start after this commit, one at a time.
Budget: 12 files to read, about 1,200 lines to write including tests and config (lockfile excluded), 90 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — Solution Shape (lines 29-47), "Shared filter" and the `facets` / `summary` contracts (lines 62-94), "Browser access" (175-179), "Domain: Analytics site" (181-187), Phase 2 Outcome (line 290). Binding.
2. `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` — Phase 1 Carried, item 2.
3. `tools/workflow/internal/serve/analytics_test.go` lines 83-200 — how a fixture tenant is posted through `POST /v1/ingest` (fact fields, `artifact_version` / `commit` / `hook_event` shapes, `payload.tool_name`). Mirror it in TypeScript.
4. `tools/workflow/cmd/workflow/main.go` lines 74-110 and 136-161 — `workflow serve` env: `WORKFLOW_SERVE_ADDR`, `WORKFLOW_SERVE_DATA`, `WORKFLOW_SERVE_KEYS` (`tenant=key`), `WORKFLOW_SERVE_CORS_ORIGINS`, `WORKFLOW_CHECKS_DIR`.
5. `packages/opencode-workflow-hooks/package.json` — the repo's package metadata conventions (license, repository block).

Go is at `~/.local/go/bin` (add it to `PATH`); Node 22 and npm 10 are installed; Playwright's Chromium is already cached in `~/.cache/ms-playwright` (pin `@playwright/test` to a version whose browser revision is one of those directories, or let `npx playwright install chromium` fetch it). Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

A SvelteKit static site exists at `packages/workflow-analytics` whose shell every report shares: the connection settings, an API client that honours them, the shared filter held in the page URL, the overview report at `/`, and an e2e harness that runs the built site against a real phase-1 `workflow serve` holding a known fixture.

## Contract

- "SvelteKit built with the static adapter to a directory of HTML, CSS, and JS (no SSR server)." Package name `@codyhamilton/workflow-analytics`.
- "`/settings` saves an API base URL and a bearer token in the browser's `localStorage` for that origin under the keys `workflow-analytics-base` and `workflow-analytics-key`. An empty base URL means same-origin relative `/v1`. The token is sent only as `Authorization: Bearer`. It is never written into the built assets or the repo." "The site sends `Authorization` only when a token is configured."
- "Every report except `/settings` shares one filter set, stored in the page URL: window, `repo_id`, `harness`, `kind`, `plan`. Changing a filter refetches and the URL is the shareable report."
- Shared filter parameters: `from`, `to` (RFC3339), and repeatable `repo_id`, `harness`, `kind`, `plan` (DESIGN.md lines 64-69). `kind` ∈ `design`, `brief`, `report`.
- `/` is "Overview counts for the window: volume of conversations, hooks, artifacts by kind, commits, rejections, screens" from `GET /v1/analytics/summary` (shape at DESIGN.md lines 87-91).
- Error bodies are `{"error":"<text>"}`.

Decisions settled at refine (do not re-derive):

1. **Stack:** Svelte 5, SvelteKit 2, `@sveltejs/adapter-static` with `fallback: 'index.html'`, `ssr = false` and `prerender = false` in the root `+layout.ts` (a pure client SPA; output directory `build/`). TypeScript. npm with a committed `package-lock.json` in the package; `node_modules/`, `build/`, `.svelte-kit/`, `test-results/`, `playwright-report/` ignored by a package-local `.gitignore`. `"private": true`, license MIT.
2. **All runtime dependencies for the phase are installed here,** so later units never edit `package.json` or the lockfile: `layerchart` (the Svelte 5 compatible release) and the Perspective packages `/explore` needs (`@perspective-dev/client`, `@perspective-dev/viewer`, and the viewer's datagrid plugin plus any server/WASM package the client version requires). Dev: `vitest`, `@playwright/test`. Do not wire Perspective into `vite.config.ts`; 2-04 owns that.
3. **Scripts:** `dev`, `build`, `preview`, `test` (vitest, unit only), `test:e2e` (Playwright), `check:bundle` (see 9).
4. **API client** `src/lib/api.ts`: `apiGet(path, params)` builds `<base>/v1/...` where base is `localStorage['workflow-analytics-base']` trimmed of a trailing `/` (empty → relative `/v1`), appends repeatable params, sets `Authorization: Bearer <key>` only when `localStorage['workflow-analytics-key']` is non-empty, and throws an error carrying the status and the body's `error` text on non-2xx. Reads `localStorage` inside try/catch on each call (no module-level caching, so `/settings` takes effect without reload). Typed response interfaces for all seven analytics routes and `/v1/baselines` (`{"kind":"…","checks":{"<name>":{"n":0,"p25":0,"median":0,"p75":0}}}`, from `tools/workflow/internal/serve/reads.go` `baselines`) live in `src/lib/types.ts`.
5. **Filter state** `src/lib/filters.ts`: pure functions `parseFilter(URLSearchParams)` → `{from?, to?, repo_id[], harness[], kind[], plan[]}` and `filterParams(filter)` → the API query (same parameter names as the API, so the page URL and the API query are the same keys). Unknown `kind` values are dropped. Reports read the filter from `page.url` (`$app/state` or `$app/stores`) and refetch when it changes; a filter change is a `goto` with the new query (`keepFocus`, `noScroll`), so reload and back/forward reproduce the report. Route-specific params (`metric`, `group`, `bucket`, …) are allowed in the URL and are preserved by the filter bar.
6. **Filter bar** `src/lib/components/FilterBar.svelte`, rendered by the root layout on every route except `/settings`: date inputs for `from`/`to` (a date maps to `T00:00:00Z` / `T23:59:59Z`; empty means the server default window), multi-selects for `repo_id`, `harness`, `kind`, `plan` populated from `GET /v1/analytics/facets` for the current window. **Carried item 2:** empty-string facet values are hidden from these controls (the API's `""` means "missing", and filtering on it is not a lens this phase offers). Elsewhere, any empty key a report displays (series keys, table cells) is rendered as `(none)`; export a `label(key)` helper from `src/lib/format.ts` for that.
7. **Layout:** nav links to all nine routes in Solution Shape order; a visible error panel showing the API's `error` text when a fetch fails (and a hint to open `/settings` on 401 or a network error). Plain CSS; no UI framework. Create placeholder `+page.svelte` files for the seven routes other units own **only if** the build requires them — prefer not creating them (nav links to not-yet-built routes are fine; the SPA fallback handles them).
8. **Overview `/`:** tiles for every scalar in the summary response (`conversations`, `hook_events`, `artifact_versions`, `distinct_content`, `commits`, each `by_kind`, `by_source`, `rejections`, `screens` key) with the window `from`–`to` shown. Each number element carries `data-testid="summary-<field>"` (nested keys joined with `-`, e.g. `summary-by_kind-brief`) so e2e asserts are stable. No chart needed here.
9. **No secret in the build:** `scripts/check-bundle.mjs` (run by `check:bundle`) scans every file under `build/` and fails if it finds the value of `E2E_FORBIDDEN` (comma-separated strings passed in env) or the string `Bearer ` followed by a non-placeholder token literal. The e2e global setup runs `npm run build` with `WORKFLOW_SERVE_KEYS` and a dummy `PUBLIC_`/`VITE_` token variable set in the environment, then runs the check with those values in `E2E_FORBIDDEN`, proving the build does not read them.
10. **E2E harness** (`playwright.config.ts`, `tests/e2e/`):
    - Global setup: `go build` `tools/workflow/cmd/workflow` into a temp dir; start a **local-mode** serve (`WORKFLOW_SERVE_ADDR=127.0.0.1:<free port>`, fresh `WORKFLOW_SERVE_DATA`, `WORKFLOW_CHECKS_DIR=<repo>/tools/quality`) and a **keyed** serve (`WORKFLOW_SERVE_KEYS=e2e=<random 32-hex key>`, `WORKFLOW_SERVE_CORS_ORIGINS=http://127.0.0.1:<preview port>`); wait on `/v1/health`; post the same fixture to both via `POST /v1/ingest`; write the two base URLs and the key to a JSON file the specs read; teardown kills both. Run the bundle check (decision 9) before the preview starts.
    - `webServer`: `vite preview --host 127.0.0.1 --port <fixed port>` over `build/` (the preview origin is loopback, so phase 1's loopback-origin CORS rule lets the local serve answer it).
    - `tests/e2e/fixture.ts` exports the facts and **hand-counted expected numbers** for every lens the phase checks: summary fields for the whole window and for `repo_id=<one repo>`; per-repo, per-harness, per-`event` and per-`tool` hook counts; series per day for at least `hook_events`; execution shapes per brief; conversation rows. Shape it like the Go fixture: two repos, two harnesses, at least three conversations, hook events with and without `payload.tool_name`, design / brief / report / commit facts with a complete, an unreported and a started brief. Timestamps are whole hours on UTC days 1–6 days before now, so the default 30-day window holds all of them; export the day strings too. Leave room (comments, exported constants) for 2-02..2-04 to read expectations without editing this file; if they need a number you did not export, they compute it in their spec from the exported facts.
    - `tests/e2e/helpers.ts`: `useServe(page, 'local' | 'keyed')` sets `workflow-analytics-base` (and for keyed, `workflow-analytics-key`) through `page.addInitScript` before navigation.

### Keep untouched

Everything outside `packages/workflow-analytics/` and the report path. The Go module and its tests do not change.

## Done evidence

Write the failing checks first and report their output before and after. Why: every later unit and the orchestrator's phase check run on this harness, so it has to prove three things the phase outcome names before any report exists — the filter survives a reload, the token reaches a cross-origin serve only as a bearer header, and the build carries no secret.

- `npm ci && npm run build` in `packages/workflow-analytics` → `build/index.html` exists, and `npm run check:bundle` with `E2E_FORBIDDEN` set passes.
- `npm test` → vitest passes for `filters.ts` (round trip of repeated params; unknown `kind` dropped; route params preserved) and `api.ts` (URL with empty and non-empty base; `Authorization` present only when a key is set; error text surfaced), using a stubbed `fetch` and `localStorage`.
- `npm run test:e2e` → passes, with at least these specs:
  - `overview.spec.ts`: `/` against the local serve shows every `summary-*` value equal to the fixture's expected numbers; `/?repo_id=<repo>` shows the filtered numbers; `page.reload()` keeps the filter and the numbers; choosing a repo in the filter bar changes the URL to include `repo_id` and the numbers to the filtered ones; no empty option appears in any filter control.
  - `settings.spec.ts`: on `/settings`, enter the keyed serve's base URL and key and save; `localStorage` holds both keys; navigating to `/` sends `GET <keyed base>/v1/analytics/summary` whose request headers carry `authorization: Bearer <key>` (assert via `page.waitForRequest`) and the overview shows the fixture numbers; clearing the key and reloading `/` shows the 401 error panel.
- `git status --porcelain` after the run shows no tracked build output, no `node_modules`, and no file containing the e2e key.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, the exact dependency versions installed (2-02..2-04 rely on them), the fixture's exported names, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in phase 1's routes): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
