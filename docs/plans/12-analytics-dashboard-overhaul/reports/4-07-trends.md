# Report: 4-07 — Trends: any measure over time, in-range buckets and brush-to-zoom

Status: **done with concerns**.

## What changed

- `packages/workflow-analytics/src/routes/trends/+page.svelte` — rewritten on `view`, the client
  (`getJSON`) and `TimeChart`. Schema-driven measure and group lists (`analytics/schema`, slot
  `trends-schema`, fetched once and cached); `/query` through `view.paramsFor('query', {measure,
  bucket, dim?, top:'8'})` (slot `trends-main`); bucket control offers only buckets with
  `bucketCount(...) <= 400`, defaults to `pickBucket` and falls back when the window moves; route
  params `metric`/`bucket`/`group` via `view.setParam` (defaults `hook_events`, auto, none; test ids
  `trends-metric`/`trends-bucket`/`trends-group` unchanged); brush calls `view.setWindow`; the chart
  is `testid="trends-chart"`; missing buckets zero-filled (own fill for all four units).
- `packages/workflow-analytics/tests/e2e/trends.spec.ts` — rewritten against the recounted fixture
  (`HOOK_EVENTS_BY_DAY`): default render via the data table, `cost_usd` by model (two priced days),
  group list excludes a non-dim, `range=all` bucket range, brush, 1 s timing, and a five-change burst
  issuing one request. `test.use({ timezoneId: 'UTC' })` so the UTC fixture days land on the buckets.

## Check output

- Old spec against the new page: **3 failed** — every `series-<key>-<t>` cell is gone
  (`trends shows the per-day hook_events counts`, `group=harness ...`, `metric=conversations ...`).
- `npm test` → **76 passed** (11 files). `npm run build` → **passes**.
- `E2E_PORT=4407 npx playwright test trends.spec.ts` → **7 passed**, including brush, the all-time
  bucket test and the timing assertion.

## Departures from the brief

1. **All time is not `all=1`; it is clamped to 399 days.** The brief (L28, L37) says the page sends
   `all=1` with a bucket "in range". Impossible against the code the brief cites: `parseFilter` maps
   `all=1` to `from = Unix(0)` (`serve/analytics.go:120-125`) and `/query` rejects when
   `bucketSpan(from,to,bucket) > 400` (`serve/analytics_query.go:81`). Over the whole ledger every
   unit exceeds 400 (month ≈ 682, week ≈ 2965), so `all=1` + any bucket is `400 "range too wide"` —
   verified with a built `serve`. So the page uses the same 399-day clamp the shell already applies
   to rest routes (`resolveWindow(..., 'rest')`), which the `notice-clamped` shell notice reports.
   The all-time test therefore asserts the outgoing request is in range (bounded, `bucket=week`, no
   error) instead of `all=1`, and says so in a comment.
2. **`fillBuckets` from `src/lib/series.ts` is not reused.** The brief (L33) offers it for
   `day`/`week`, but `/query` `t` is RFC3339 in the request tz (`localBucket`/`bucketExprSQL`), while
   `fillBuckets` parses `p.t` as date-only; they do not compose. The page zero-fills all buckets from
   the returned `t` set with a DST-safe calendar step.
3. **No `notice-ignored` spec test.** The brief's changes list (L37) does not require one, and the
   shell drops the notice (bug below), so a test would fail for reasons outside this unit.

## Contradictions (not resolved silently)

- Brief L28/L37 (`all=1` + a time bucket) vs brief 4-02 L29 and `serve/analytics_query.go:81` +
  `serve/analytics_bench_test.go:333-334` (the benchmark skips every non-`none` bucket for `all`).
  See departure 1.
- Brief L33 (`fillBuckets` for `day`/`week`) vs the `/query` RFC3339 `t` contract it also cites.
  See departure 2.

## Bug outside done evidence (not fixed here)

- **Symptom:** `notice-ignored` / `notice-partial` never render; an `ignored_filters` response (e.g.
  `hook_events` + `kind=brief`) sets the notice and it vanishes immediately.
- **Location:** `src/routes/+layout.svelte:32-37` (the route/search `$effect` calls `clearNotices()`)
  and `src/lib/state.svelte.ts:35-37` (`clearNotices` reads `Object.keys(notices)`).
- **Root cause:** reading `notices` inside the effect subscribes it to `notices`; the client's
  `setNotice` (for the slot) invalidates the effect, which re-runs and deletes the notice. Confirmed
  with instrumented logs (`setNotice trends-main …` immediately followed by `clearNotices
  {"trends-main": …}`). Every route's ignored/partial notice is affected. Fix belongs to the shell
  unit (4-05), not here.

## Concerns / limits

- The brush test's "narrower" is measured from the URL `from`/`to` span (< 30 d); brushing 25–75% of
  the default window selects a stretch with no fixture rows, so the chart is legitimately empty.
- The timing test uses `expectSettled` literally as the brief asks; that helper can pass before a
  refetch settles (the old chart stays `data-ready="true"`), so it bounds, not proves, latency.
- Group options are the measure's schema dims verbatim, which includes `hour_of_day`, `weekday` and
  `conversation_id`; that follows "offered only if it is in the measure's dims".

Reproduce: from `packages/workflow-analytics`, `npm test`, `npm run build`,
`E2E_PORT=4407 npx playwright test trends.spec.ts`.
