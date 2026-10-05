# Brief: 2-03 — Quality, executions and conversations reports

Consumer: a worker dispatched by the plan 10 phase 2 orchestrator. The orchestrator verifies the phase outcome by running this unit's e2e specs with the rest of the suite.
Owned paths: `packages/workflow-analytics/src/routes/quality/`, `src/routes/executions/`, `src/routes/conversations/`, `src/lib/components/Pager.svelte` (new), `tests/e2e/quality.spec.ts`, `tests/e2e/executions.spec.ts`, `tests/e2e/conversations.spec.ts` (all under `packages/workflow-analytics/`), plus `docs/plans/10-workflow-analytics/reports/2-03-table-reports.md`. Touch nothing else — in particular not `package.json`, `package-lock.json`, `vite.config.ts`, `svelte.config.js`, `src/lib/api.ts`, `src/lib/filters.ts`, `src/lib/types.ts`, `src/lib/components/FilterBar.svelte`, the root layout, `src/lib/charts/` (2-02's), or `tests/e2e/fixture.ts` (report a gap instead of changing them).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/2-03-table-reports.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: 2-01 and 2-02 (committed on this branch; 2-02's routes and specs must keep passing).
Runs alongside: nothing (shares the e2e harness's `build/` directory and ports; runs after 2-02).
Budget: 10 files to read, about 700 lines to write including specs, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — the `scores`, `executions` and `conversations` contracts (lines 120-161), "Domain: Analytics site" (181-187), Phase 2 Outcome and Guards (lines 290-291). Binding.
2. `docs/plans/10-workflow-analytics/reports/2-01-site-shell.md` — client, filter helpers, `label()`, fixture exports, how to run the suites.
3. `packages/workflow-analytics/src/routes/+page.svelte` — the overview, as the idiom for a report route.
4. `packages/workflow-analytics/src/lib/api.ts`, `src/lib/filters.ts`, `src/lib/types.ts`, `tests/e2e/fixture.ts`, `tests/e2e/helpers.ts` — by export list first (`grep -n export`), then the parts you call.
5. `tools/workflow/internal/serve/reads.go` lines 61-85 — the `/v1/baselines` response (`checks` is an object keyed by check name with `n`, `p25`, `median`, `p75`; absent when nothing is scored).

Run commands from `packages/workflow-analytics`; Go is at `~/.local/go/bin`. Read ranges and grep; do not read a whole file to find one section, and truncate long tool output.

## Goal

Three report routes show score distributions against the all-time baseline, the per-brief execution shape, and one row per agent conversation, for the URL filter, with paging that follows the API's cursor.

## Contract

- `/quality` — "Score distributions: per check, for one artifact kind, against the existing all-time baseline." "`GET /v1/analytics/scores` … requires exactly one `kind` parameter." "This is not `GET /v1/baselines`, which stays all-time … The quality view reads both and shows the window against that baseline. It does not write a new baseline." Outcome: "`/quality` shows each check's window percentiles beside the `/v1/baselines` figures." Guards against "a quality view that quietly replaces the agent baseline."
- `/executions` — "Design → brief → commit → report: derived execution shape from design 1, per brief." Response `counts` + `rows` + `next` (DESIGN.md lines 144-150).
- `/conversations` — "Agent runs: one row per `conversation_id`." (lines 152-161).
- Paging: "`limit` default 100, maximum 500 … `cursor` from a previous `next`. `next` is absent on the last page." "A `cursor` whose filters differ from the request returns 400 `{"error":"cursor mismatch"}`."

Decisions settled at refine (do not re-derive):

1. **Quality kind:** the route uses the first valid `kind` in the URL filter, default `design`; a kind selector on the page sets `kind` to that single value. When the URL holds several kinds, the page says which one it shows. It calls `GET /v1/analytics/scores?kind=<k>` with the shared filter and `GET /v1/baselines?kind=<k>` (no other parameters; it is all-time) in parallel.
2. **Quality layout:** one table row per check in the `scores` response order, columns window `n`, `min`, `p25`, `median`, `p75`, `max` and baseline `n`, `p25`, `median`, `p75` (blank, not zero, when the baseline has no entry for that check), headed so "window" and "all-time baseline" are unmistakable. Test ids `q-<check>-w-<field>` and `q-<check>-b-<field>`. A chart is optional; if you draw one, use LayerChart directly in the route, not 2-02's wrappers.
3. **Pager** (`src/lib/components/Pager.svelte`): "Load more" appends the next page by calling the same route with the same filter params plus `cursor=<next>`; hidden when `next` is absent. The cursor is in-memory, not in the URL; a filter change resets rows and cursor. A `limit` URL param, when present, is passed through to the API (so a spec can force paging on a small fixture); absent, the API default applies.
4. **Executions:** `counts` as three tiles (`data-testid="exec-count-<shape>"`), then a table of rows (repo, plan, conversation, brief path, harness, shape, ts) with `data-testid="exec-row"` per row, and the Pager.
5. **Conversations:** a table of rows (conversation, harness, repos, first/last ts, hook events, artifact versions, commits, kinds) with `data-testid="conv-row"` per row and `data-testid="conv-<conversation_id>-<field>"` on the counts, and the Pager.
6. Empty values display through `label()` as `(none)`.
7. **Carried item 1** (paging loads the store's full sorted set; unmeasured at scale) is not addressed here; do not change paging semantics.

### Keep untouched

2-01's files listed under Owned paths. If a shared file needs a change, report it as a gap and compute what you need in your spec from the exported fixture facts.

## Done evidence

Write the failing specs first and report their output before and after. Why: these specs are the phase outcome for three of the eight report routes and for the quality guard — the window figures sit beside, and never overwrite, the agent's all-time baseline. The zero-scorer run proves the page renders the catalog when nothing is scored, which is the live state without a scorer key. The stubbed run proves each window and baseline cell is bound to the right field. The GET-only assert is the "does not write a new baseline" guard. The paging walks prove the Pager neither drops nor repeats rows across the cursor.

- `npm run test:e2e -- quality.spec.ts executions.spec.ts conversations.spec.ts` → passes, with at least:
  - `quality.spec.ts`: against the local serve (which has no scorer, so every catalog check has `n` 0), `/quality` lists one row per catalog check of kind `design` with window figures 0 and blank baseline cells, and `?kind=brief` switches to the brief checks; with `page.route` stubbing `/v1/analytics/scores` and `/v1/baselines` to known non-zero numbers, every `q-*-w-*` and `q-*-b-*` cell shows its stubbed value; every request the page makes is a `GET`.
  - `executions.spec.ts`: counts and per-brief shapes equal the fixture (complete, unreported, started); `repo_id=<repo>` changes them and survives reload; `?limit=1` shows one row, and pressing "Load more" until it disappears yields the same rows, in order, as the unpaged page.
  - `conversations.spec.ts`: one row per fixture conversation in `last_ts` descending order with the expected counts; `repo_id` filters; `?limit=1` paging walk equals the unpaged rows.
- `npm run build && npm run check:bundle` (with the `E2E_FORBIDDEN` the 2-01 report names) → passes.
- `npm run test:e2e` (whole suite) → passes.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence (including in phase 1's routes or 2-01's shell): report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
