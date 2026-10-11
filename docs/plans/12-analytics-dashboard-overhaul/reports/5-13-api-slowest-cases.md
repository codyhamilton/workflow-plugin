# Report: 5-13 — Speed up the slowest Overview and Usage requests

Status: done with concerns

## What changed (against each part of the brief)

Lever used: a missing index (first lever). No rollup was added.

- `tools/workflow/internal/store/rollup.go`: new `ensureUsageIndex`, creating `facts_usage_ts ON facts(type, norm_event, ts)` and running `ANALYZE facts_usage_ts` (that index only) when it is first created. It is called from `ensureConversationRollupIndex`, so it runs on every open and is a no-op once the index exists.
- `tools/workflow/internal/store/usage.go`: the `usage_u` CTE now selects only the 11 columns the read uses (plus `_mid`) instead of `SELECT *`, so the window-function sort no longer carries the `raw` blob.
- `tools/workflow/internal/store/usage_test.go`: `TestUsageIndexDrivesUsageRead` (index exists after open; the usage CTE plan names `facts_usage_ts`).
- `tools/workflow/internal/serve/reads_test.go`: one token added (`DROP INDEX facts_usage_ts`), see Departures.

Root cause (from 5-12's plan): the usage CTE ran as `SCAN facts USING INDEX facts_conv_page` (the planner walks that index to avoid a sort, then does a table lookup for each of 435,608 rows) although only 33,464 rows are usage rows. With the new index the plan is `SEARCH facts USING INDEX facts_usage_ts (type=? AND norm_event=? AND ts>? AND ts<?)` plus a sort of the 33k rows.

## Evidence

Failing check first: 5-12's `TestAnalyticsPageSet` on `/var/tmp/p4verify/data/local` (before, same code as 5-12 at HEAD): the slowest requests were 571, 548, 543 ms p50.

Before and after p50 / max (ms), `WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local go test ./internal/serve -run TestAnalyticsPageSet -v -count=1` (this run's own before, the ranking order is this run's):

| Request | before p50 / max | after p50 / max | ratio |
| --- | --- | --- | --- |
| usage/all `query bucket=week&measure=tokens_out` | 571 / 637 | 277 / 320 | 0.48 |
| overview/all `summary` | 548 / 556 | 282 / 301 | 0.51 |
| overview/all `query bucket=week&measure=cost_usd` | 543 / 556 | 259 / 273 | 0.48 |

Every other usage-measure request on All time moved the same way (0.47 to 0.51); the slowest request anywhere after the change is 282 ms p50 (was 571). All three target requests are at or below 70%.

Other done evidence:

- `go vet ./...`: pass. `go test -count=1 ./...` in `tools/workflow`: all packages pass except `internal/secrets` `TestEnvAssignmentCorpus` (see Known problems; it fails identically with my changes stashed).
- `TestAnalyticsBench` on the same copy (`WORKFLOW_BENCH_DIR=/var/tmp/p4verify/data/local WORKFLOW_BENCH_OUT=... go test ./internal/serve -run 'TestAnalyticsBench$' -v -timeout 40m`): `2063 cases, 9m21.9s elapsed`, `--- PASS`, 0 over 500 ms; worst `series/90d` 465.5, `series/30d` 451.2, `series/7d` 401.9, `conversations/30d` 397.2 ms p95.

## Departures from the brief, with reasons

- **Edited `internal/serve/reads_test.go` (outside owned paths).** `TestAdvisoryReads/backfill` rebuilds a version-1 database by dropping indexes and then `ALTER TABLE facts DROP COLUMN norm_event`; SQLite refuses while any index references the column. It needed `DROP INDEX facts_usage_ts` in its list. One token; no other test change.
- **Covering index from the previous worker not used.** A covering index cannot help: the CTE reads `raw` (`json_extract(raw,'$.backfill.ref')`), which is not indexable cheaply. Plain `(type, norm_event, ts)` gives the win only once the planner picks it (it does, with the CTE narrowing).
- **Index choice took three tries.** A bare `(type, norm_event, ts)` without stats was also picked for `type='artifact_version'` queries and `scores/7d` went from 33 ms to 5,000 ms p95 (the first full bench failed on `scores/*` at 5.9 to 6.8 s). Running `ANALYZE facts_usage_ts` at creation fixed it (scores/7d 30.5 ms). Partial indexes `(ts)` and `(conversation_id, ts) WHERE type='hook_event' AND norm_event='usage'` were tried and the planner did not choose them over `facts_conv_page`.
- 5-12's contradiction about `all=1` is untouched; this unit measured the clamped 399-day windows as 5-12 did.

## One-time cost at open

The index is built at the first open of an existing ledger: about 0.7 s on a 435k-row copy, plus a few ms for the single-index `ANALYZE`. It is built in the open path under the writer connection, so a very large uncompacted ledger delays that first open proportionally to its row count. Later opens only check `sqlite_master`. The ledger grows by one index (about 15 MB on 435k rows is not measured; the copy was not sized after the build).

## Unfinished / carried

- The usage read still sorts 33k rows and calls `json_extract` over `raw` for Claude rows (the remaining ~250 ms); a usage rollup (hourly by harness, repo, model, conversation, with the dedupe applied) would remove it but needs 3-12's rules and was not needed for the target. Owner: a later unit if p95 on All time must drop below ~300 ms.
- The brief allowed three requests; the one index fixed all usage-measure requests together, so nothing in 5-12's ranked list over 500 ms remains.

## Known problems / limits

- `internal/secrets` `TestEnvAssignmentCorpus` fails before and after (false positives in `docs/plans/12-analytics-dashboard-overhaul/reports/4-04-echarts-components.md:26`); not caused by this unit, not fixed here.
- Timings have 5 to 10 % run-to-run variance; bench p95 near the top (`series/90d` 454 to 567 ms in different runs) moves with machine load: one run, taken while `go test ./...` ran concurrently, showed 567 ms. The final clean run is 465.5 ms.
