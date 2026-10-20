# Brief: 2-01 — Analysis shell and tokens

Consumer: the phase 2 shell worker.
Owned paths: `packages/yakka-analytics/src/lib/analysis/` (new), `packages/yakka-analytics/src/routes/+layout.svelte`, `packages/yakka-analytics/src/routes/login/+page.svelte`, `packages/yakka-analytics/src/routes/profile/+page.svelte`, `packages/yakka-analytics/src/routes/settings/+page.svelte`, `packages/yakka-analytics/src/routes/device/+page.svelte`, `packages/yakka-analytics/src/routes/oauth/callback/+page.svelte`, `packages/yakka-analytics/src/lib/theme.css`, `packages/yakka-analytics/tests/e2e/shell.spec.ts`, `packages/yakka-analytics/tests/e2e/analysis-shell.spec.ts` (new), `docs/design/07-analytics-site.md` (Theme paragraph only). Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title, and push to `origin` branch `cursor/analytics-dashboard-redesign-ef13`. Do not open a pull request. Do not add a `Yakka-Phase` or `Workflow-Phase` trailer; the orchestrator closes the phase.
Report: before committing, write `docs/plans/17-analytics-dashboard-redesign/reports/2-01-analysis-shell.md` (handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: phase 1 (session gate on `+layout.svelte` must keep working).
Runs alongside: nothing (`2-02-chart-frame` depends on this unit's token surface).
Budget: 16 files to read, about 450 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/17-analytics-dashboard-redesign/DESIGN.md` — Domain: Component and style system; Phase 2 — Analysis component and style system.
2. `packages/yakka-analytics/src/routes/+layout.svelte` — header, nav, chrome, session gate, theme buttons, global body styles.
3. `packages/yakka-analytics/src/lib/theme.css` — current solarized tokens.
4. `packages/yakka-analytics/src/lib/charts/theme.ts` — `ThemePreference`, `initTheme`, `getThemePreference`, `setThemePreference`, `THEME_KEY` (grep the exports; do not absorb this file into `src/lib/analysis/`).
5. `packages/yakka-analytics/src/routes/login/+page.svelte`, `profile/+page.svelte`, `settings/+page.svelte`, `device/+page.svelte`, `oauth/callback/+page.svelte` — markup and local styles.
6. `docs/design/07-analytics-site.md` — the **Theme** sentence block (solarized hex list).
7. `packages/yakka-analytics/tests/e2e/shell.spec.ts` — tests from `the dark scheme swaps` through `system mode follows` (solarized assertions).
8. `packages/yakka-analytics/tests/e2e/helpers.ts` — `useServe` only.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Ship the analysis **frame** and **type, color, and space** tokens for the routes Phase 2 names, with the report nav still in the shell, so a logged-in `/` and `/login` share the same non-solarized background and body type color, and identity or connection routes use that same frame.

## Contract

Cited from `DESIGN.md`, Domain: Component and style system. Settled unless noted.

> A screen is a composition of this system: a **frame** (regions for the view and for sign-in, identity, and connection), **type, color, and space** tokens, and a **chart frame**.
>
> Color tokens are not the solarized hexes design 7 lists (`#002b36`, `#fdf6e3`, `#839496`, `#657b83`, and that series palette). A light/dark/system preference may remain. If it does, it switches this system's color.
>
> `/login`, `/profile`, `/settings`, `/device`, and `/oauth/callback` use the same system, so the package has one visual language.
>
> A library may implement the chart frame or the tokens. This design names no library and no version.

Phase 2 outcome (yardstick):

> Logged-in `/` and `/login` show the same background and the same type color, and that background is neither `#002b36` nor `#fdf6e3`. `/profile`, `/settings`, `/device`, and `/oauth/callback` show that same frame. The report nav stays in the shell.

Invoker: the report nav stays through this phase. Package boundary stays `packages/yakka-analytics`. The design names no chart or token library.

This unit does **not** own the chart frame (`2-02-chart-frame`). It does not remove KPI tiles, change overview data loading, or migrate report routes off `src/lib/charts/`.

## Changes

Add `src/lib/analysis/` as the home of the new system. At minimum:

- **Tokens** — CSS custom properties for background, surface, text, muted, border, accent, danger, a non-solarized series scale, and the space scale (4/8/16/24/32 px). Light and dark (and system-driven switching) must not use `#002b36`, `#fdf6e3`, `#839496`, or `#657b83` as `--bg` or `--text` on analysis surfaces. Series colors must not be the design 7 solarized series list verbatim (`#268bd2`, `#859900`, … `#2aa198` as the full set).
- **Frame** — a small shell composition (Svelte components and/or layout structure) with regions for: app chrome (title, theme control, **report nav**), main content, and sign-in / identity / connection pages styled inside the same language. Export what `2-02` needs: stable token variable names and how light/dark is applied on the document.

**Route policy**

- **Analysis frame routes** (new tokens on the document root for shell + main): `/`, `/login`, `/profile`, `/settings`, `/device`, and paths under `/oauth/`.
- **Legacy report routes** (keep solarized `theme.css` values for page content and filter chrome until later phases): `/trends`, `/builder`, `/usage`, `/repos`, `/hooks`, `/quality`, `/executions`, `/conversations`, `/conversation`, `/explore`, `/dashboards`, and any other report path that still mounts `FilterBar` today. Scope legacy tokens so analysis routes are not forced back to solarized (for example a `data-legacy-theme` wrapper or equivalent on legacy mains only).
- **Report nav** — keep the existing `nav` array and links in `+layout.svelte`; restyle with analysis tokens. Do not remove Builder, Dashboards, or other report destinations.

**Theme preference** — keep `localStorage` key `yakka-analytics-theme` and the three buttons (system / light / dark). Preference must switch the **analysis** token set. Legacy report routes may keep reading solarized vars inside their scoped wrapper. `src/lib/charts/theme.ts` may keep reading `--bg` etc. from whatever element wraps a chart; do not rewrite `src/lib/charts/` in this unit.

**Identity and login pages** — restyle with analysis tokens (replace hard-coded hex on `/login` denied state). Preserve each page's behavior (OAuth link, profile forms, settings base/token, device grant, callback redirect).

**`docs/design/07-analytics-site.md`** — amend the **Theme** paragraph to describe the analysis token system (preference key, `data-theme` or equivalent, non-solarized surfaces, space scale, body type). State that legacy report pages may still use the prior solarized sheet until the investigation phase replaces them. Do not edit Site, Data layer, or route tables in this unit.

**Tests** — add `tests/e2e/analysis-shell.spec.ts` for Phase 2 outcome checks. Update `shell.spec.ts` solarized assertions: on analysis routes, backgrounds must not be `#002b36` or `#fdf6e3`; theme toggle tests should assert analysis tokens, not design 7 hexes. Legacy-only tests may still expect solarized inside a legacy report route if you keep that wrapper.

### Keep untouched

`src/lib/session-gate.ts`, `session-gate.svelte.ts`, session gate effects in layout, `src/lib/charts/` (except reading CSS vars as today), report page modules under `src/routes/*/`, overview KPI/sparkline/heatmap logic in `+page.svelte` (no feature changes), `packages/yakka`, aggregation code (`query.ts`, `view.svelte.ts`, etc.). Do not remove `FilterBar` / `FilterChips` / `SaveView` from legacy report routes.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/yakka-analytics && npx playwright test tests/e2e/analysis-shell.spec.ts` → all pass; asserts logged-in `/` and `/login` share the same computed `--bg` and `--text`, and neither mode uses `#002b36` or `#fdf6e3` as `--bg` on those routes; `/profile` uses the same `--bg` as `/`.
- `cd packages/yakka-analytics && npx playwright test tests/e2e/session.spec.ts tests/e2e/shell.spec.ts` → all pass (update expectations where this unit intentionally changes theme assertions).
- `cd packages/yakka-analytics && npm test` → all unit tests pass.
- Observable: `+layout.svelte` still renders the full report nav including Overview and Settings links.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, check output before and after, deviations, and any contradiction with cited contracts. Do not spawn subagents beyond read-only helpers.
