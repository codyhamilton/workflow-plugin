# Brief: 4-03 — Fixture with usage facts, recounted constants, e2e helpers and a configurable port

Consumer: a TypeScript worker (flash-tier); every Phase 4 route spec imports the fixture and helpers.
Owned paths: `packages/workflow-analytics/tests/e2e/fixture.ts`, `global-setup.ts`, `helpers.ts`, the existing specs (`overview`, `trends`, `repos`, `hooks`, `quality`, `executions`, `conversations`, `explore`, `settings`, `fixture` under `tests/e2e/`, edited only where a recounted number forces it), and `packages/workflow-analytics/playwright.config.ts`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/4-03-fixture-usage-e2e-helpers.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 4-01, 4-02, 4-04.
Budget: 8 files to read, about 250 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

Run npm commands from `packages/workflow-analytics`. The first `npm run test:e2e` builds the Go binary (Go is at `$HOME/.local/go/bin`) and needs network only if `node_modules` or the Playwright browser is missing.

## Required reading, in order

1. `packages/workflow-analytics/tests/e2e/fixture.ts` — the whole file. Its header says: do not edit counts to match a failing report, recount by hand from the facts.
2. `packages/workflow-analytics/tests/e2e/global-setup.ts` and `playwright.config.ts` — how the Go binary and the two serves start, and the fixed preview port 4391.
3. `tools/hooklog/tests/fixtures/ingest_policy.json` lines 236 to 265 (Claude `transcript.assistant_message`) and 862 to 895 (OpenCode `transcript.assistant_message`) — the payload shapes the ingest normaliser turns into usage.
4. `tools/workflow/internal/store/pricing.go` and `pricing_table.json` (via grep) — which models are priced. Claude and local models are not; OpenCode reported `cost` passes through.
5. The existing specs, by grep for the constants they import.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The e2e serves hold usage, model and cost facts, so the usage views and the conversation timeline can be tested against hand-counted numbers, and several e2e runs can share a machine.

## Contract

- `/query` measures include `model_calls`, `tokens_in`, `tokens_out`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning`, `cost_usd`, `unpriced_calls`. `/conversation?id=` returns `totals` of the same names plus `events`.
- A reported OpenCode `cost` greater than 0 passes through as `cost_usd`; a call with no reported cost and a model absent from the pricing table counts in `unpriced_calls` and adds 0 to `cost_usd`. Claude calls are deduped by `message_id` (largest output kept) — give every message a distinct id.
- Existing counts change when facts are added; recount every constant by hand. The existing suite must pass against the unchanged site: it proves the retained route shapes did not regress.

## Changes

1. `fixture.ts`: add one conversation `c5` (harness `opencode`, repo `r1`) with three `transcript.assistant_message` facts on whole hours inside days 1 to 5 before today, plus one Claude `transcript.assistant_message` on `c1`:
   - `c5`, model `claude-sonnet-5-5`, `cost: 0.0123`, tokens `{input: 1000, output: 200, reasoning: 50, cache: {read: 3000, write: 400}}`: priced.
   - `c5`, model `qwen3-coder:30b-a3b-q4_K_M`, no `cost`, tokens `{input: 500, output: 100, reasoning: 0, cache: {read: 0, write: 0}}`: unpriced.
   - `c5`, a second priced call on `claude-sonnet-5-5` on a different day (so a cost series has two points): `cost: 0.0100`, tokens of your choice.
   - `c1`, model `claude-opus-5-5`, usage `{input_tokens: 2, output_tokens: 5505, cache_read_input_tokens: 96297, cache_creation_input_tokens: 922}`: unpriced.
   Use the payload shapes from `ingest_policy.json`. Then export hand-counted constants: `USAGE_ALL` (`model_calls`, `unpriced_calls`, token sums, `cost_usd` = 0.0223), `USAGE_BY_MODEL` (calls, unpriced, cost per model), `USAGE_C5` (the `totals` of `c5`), and add `'opencode'` to `HARNESSES`. Recount `SUMMARY_ALL`, `SUMMARY_R1`, `HOOKS_BY_*`, `HOOK_EVENTS_BY_DAY`, `CONVERSATION_ROWS` (c5 is a new row; c1 gains a hook event) and anything else the new facts move. Write each recount as a comment-free literal; do not compute it from `FACTS`.
2. Prove the numbers against the real server, not only by reading: start the local serve as `global-setup.ts` does (or run the suite), `curl` `analytics/query?measure=cost_usd&dim=model`, `…measure=unpriced_calls`, `…/conversation?id=c5`, and `summary`, and compare with your literals. A mismatch means recount by hand again, or report a server bug; never edit a literal to match.
3. `helpers.ts`: add
   - `trackRequests(page, pattern: string | RegExp): {count(): number, urls(): string[], reset(): void}` (a `page.on('request')` counter),
   - `clickBar(page, testid: string, index: number, opts?: {shift?: boolean})`: clicks the centre of bar `index` of a horizontal `BarChart` (4-04 fixes the grid at `left 120, right 24, top 8, bottom 24` in px, categories listed top to bottom in data order; bar centre y = top + (index + 0.5) × (height − top − bottom) / N; N is the number of rows read from `<testid>-table`),
   - `expectSettled(page)`: waits until no `[data-ready="false"]` exists and at least one `[data-ready="true"]` exists,
   - `brush(page, testid: string, fromFrac: number, toFrac: number)`: mouse down at `fromFrac` of the chart box width and up at `toFrac`, at mid height.
   `clickBar` and `brush` cannot be exercised until 4-04 lands; write them against the contract above and say so in the report.
4. Port: `playwright.config.ts` and `global-setup.ts` read `E2E_PORT` (default `4391`) for the preview origin and the keyed serve's `WORKFLOW_SERVE_CORS_ORIGINS`, so two worktrees can run the suite at once with different ports.
5. Existing specs: edit only where a recounted number or a new harness forces it. `test:e2e` must pass.

### Keep untouched

The keyed-serve and bearer-token tests, the `E2E_KEY` and dummy-token handling, and `scripts/e2e-build.mjs` (it runs `check:bundle`).

## Done evidence

Before adding facts, run `npm run test:e2e` and report the pass count (26 expected).

- `npm run test:e2e` → all pass after the change, with the recounted constants.
- The `curl` comparison in step 2 is in the report, one line per number.
- `E2E_PORT=4393 npm run test:e2e -- fixture.spec.ts` → passes with the preview on 4393.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
