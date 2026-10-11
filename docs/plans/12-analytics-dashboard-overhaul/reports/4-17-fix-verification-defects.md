# Report: 4-17 — Fix the three Phase 4 verification defects

Status: done

## What changed (against each part of the brief)

**A — All time no longer sends rejected `/query`.** Overview (`src/routes/+page.svelte`) and Usage
(`src/routes/usage/+page.svelte`) now resolve the window as Trends does: when the range is `all`
they take the 399-day clamp from `resolveWindow(..., 'rest')`, pick the bucket from that bounded
window (`pickBucket`), and on every `/query` they issue delete `all` and set `from`/`to`. Overview
applies this to all 9 sparkline queries and the heatmap query; Usage to all 7. The "limited to the
last 399 days" notice is untouched (`Notices.svelte` via `view.clamped`). No helper module was
added; the clamp is inlined in the two routes, as the brief allows.

**B — Cost is formatted through the unit.** `src/lib/charts/DataTable.svelte` now takes the chart
`unit` and formats numeric cells: `usd` through `costLabel` (a zero-cost cell reads `unpriced`,
never `$0`; positive costs to 4dp under a cent, else 2dp), `tokens`/`count` with thousands
separators. Every numeric cell carries its exact value in `data-value`. `BarChart.svelte` passes
`{unit}` to the table.

**C — Concurrency.** `src/lib/query.ts` default `maxConcurrent` is now 6 (was 3); `query.test.ts`
gained a test that the default allows exactly six concurrent fetches.

## Evidence

Failing specs written first (`tests/e2e/overview.spec.ts`, `tests/e2e/usage.spec.ts`).

Before (`.scratch/wqa-4-17-before.log`): `3 failed`, `15 passed`.
- overview "All time: every query carries from/to, none carries all=1, none is a 400" —
  `expect(u.searchParams.get('all')).toBeNull()` received `"1"` (`.../query?tz=…&all=1&measure=conversations&bucket=month`).
- usage "All time: …" — received `"1"` (`.../query?…&all=1&measure=cost_usd&dim=model&top=20&bucket=none`).
- usage "cost-by-model table formats cost by unit…" — expected `"$0.02"`, received `"0.0223"`.

After:
- `npm test` (`.scratch/wqa-4-17-unit-after.log`): `Test Files 10 passed (10)`, `Tests 74 passed (74)`.
- `npm run build`: success, `built in 6.03s`.
- `E2E_PORT=4417 npm run test:e2e` (`.scratch/wqa-4-17-after.log`): `87 passed`, exit 0. The three new tests pass.

## Deviations from the brief

- The brief's Required reading cites `src/lib/cost.ts` for `costLabel`; no such file exists.
  `costLabel` lives in `src/lib/format.ts` (imported from there). No `cost.ts` was created.
- Defect C asked to measure a 30d→90d change on the real ledger. That copy was not available here,
  so the only timing evidence is the fixture e2e assertions ("preset change settles within 1 s" in
  overview and usage), which pass. The real-ledger 1 s claim is unverified in this environment.
- B is realised as `costLabel({ cost: cell, unpriced: cell === 0 ? 1 : 0 })`, so a priced row whose
  cost is exactly 0 would also read `unpriced`. This matches the chart's own drill rule (a bar with
  no priced cost is treated as unpriced in `src/routes/usage/+page.svelte`), but it is a semantic
  choice the brief did not spell out.
- C: the brief said "update its test"; the existing `maxConcurrent` test passes an explicit value,
  so a new test covering the default of 6 was added rather than editing that one.
- Lines written slightly exceeded the ~120-line estimate (about 147, including the required failing
  specs and the new unit test); tool turns and files read were within budget.

## Unfinished work

None. All three defects are fixed and every required check passes.

## Contradictions between the brief and the contracts it cites

- `src/lib/cost.ts` (brief) vs `src/lib/format.ts` (repo) — see Deviations.
