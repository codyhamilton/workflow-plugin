# Execution report: 3-06 — Repos cost ranking

**Status:** done

## What changed

- `/repos` fetches five `analytics/query` calls (`hook_events`, `conversations`, `artifact_versions`, `commits`, `cost_usd`) with `dim=repo_id`, `bucket=none`, `top=100`.
- Added `repos-rank` select (default `hook_events`) driving bar chart values and sort; table keeps four count columns sorted by `hook_events`.
- Bar chart uses `unit=usd` when ranking by `cost_usd`. Repo row/chart drill unchanged; `__other__` still inert.

## Done evidence

**Before (baseline on unmodified page):** `export E2E_PORT=4394 && npx playwright test tests/e2e/repos.spec.ts` — 7 passed; load test expected 4 query requests.

**After:** same command — 8 passed (added cost-ranking test; load tests expect 5 queries).

## Departures

- Cost-ranking e2e asserts r1 > r2 by live `data-value` (r1 priced usage on fixture, r2 zero), not `USAGE_ALL.cost_usd`, because per-repo totals include read-time pricing beyond the hand-counted summary constant. Order and “all cost on r1” match the fixture intent.

## Contradictions

- Brief allows default rank `hook_events` or `cost_usd`; DESIGN Phase 3 says “ranks by cost_usd” as outcome. Chose `hook_events` default for backward compatibility per brief Changes section; control still ranks by `cost_usd`.

## Problems

None known.
