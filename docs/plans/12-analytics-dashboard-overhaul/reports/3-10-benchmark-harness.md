# 3-10 — Benchmark harness

Status: done with concerns

## What changed

- `tools/workflow/internal/serve/analytics_bench_test.go` (new). It adds:
  - `TestAnalyticsBench` — env-gated. `WORKFLOW_BENCH_DIR` names a source tenant dir;
    `WORKFLOW_BENCH_OUT` writes the table; `WORKFLOW_BENCH_RUNS` (default 3, after one
    discarded warm-up) sets timed runs; `WORKFLOW_BENCH_FILTER` is a case-name substring;
    `WORKFLOW_BENCH_P95_MS` (default 500) is the bound. It copies only `ledger.db` and its
    `-wal`/`-shm` siblings into `t.TempDir()`, opens the copy there, and never opens or writes
    the source. It refuses a source under `~/.local/share/workflow` unless
    `WORKFLOW_BENCH_ALLOW_LIVE=1` (the copy is still made). `to` is the copy's `max(ts)`; the
    presets are `24h/7d/30d/90d` back from it plus `all`. Cases: each route per servable preset,
    `schema` once, `conversation` for the three busiest conversations (ids read from the copy,
    renamed `conv#1..3`), `query` for every measure x 0/1/2 dims at `bucket=none` per preset,
    and every in-cap bucket at 0 dims and first dim per preset. p95 is nearest rank; a non-200
    fails the case; the table is `case/status/runs/p95_ms/rows`; over-bound cases are listed.
  - `TestAnalyticsBenchSmoke` (ungated): builds a synthetic tenant, asserts route/preset/measure
    coverage and that every case is 200, then that a zero bound reports over-bound cases.
  - `TestAnalyticsBenchCopyIsNonMutating`: asserts the source `ledger.db` bytes, size and mtime
    are unchanged after a run on a tempdir fixture.
- It lives in `internal/serve`, not `store`, because it drives HTTP routes and `store` cannot
  import `serve`.

## Checks

- Before: file absent; no `AnalyticsBench` test compiled.
- After, `gofmt -l internal/serve` → no output (exit 0).
- `go vet ./internal/serve` → no output (exit 0).
- `go test ./internal/serve -run AnalyticsBench -v`:
  - `--- SKIP: TestAnalyticsBench` (0.00s) — no `WORKFLOW_BENCH_DIR`.
  - `--- PASS: TestAnalyticsBenchSmoke` (1.70s)
  - `--- PASS: TestAnalyticsBenchCopyIsNonMutating` (0.02s)
  - `ok .../internal/serve 1.728s`.
- `go test ./internal/serve` → `ok .../internal/serve 4.819s`.

## Deviations

- The `all` preset is **not** sent to the window-capped legacy routes (`facets`, `summary`,
  `series`, `scores`, `executions`, `conversations`, `explore`, `conversation`): `parseFilter`
  rejects an epoch-to-max window with `400 range too wide`. The five presets are still covered
  for those routes via the four relative windows, and `all` is covered through the `/query`
  cases, which validate the 400-day cap per bucket itself. `benchPreset.servable()` gates only
  the legacy routes, so no case is silently dropped: `/query` still runs every preset.
- `TestAnalyticsBenchSmoke` asserts preset coverage via the `/query` cases (a suffix match on
  case names), which is the only place `all` appears; this is consistent with the deviation above.
- The report is titled `done with concerns` only because of the brief-vs-`parseFilter`
  contradiction below (the contract asked for "every analytics route with each preset",
  which the handler cannot serve for `all`).

## Contradictions

1. Brief (and the DESIGN contract it cites) says "every analytics route with each preset",
   including `all`. But `parseFilter` applies a 400-UTC-day cap to every non-`query` route
   *regardless of whether that route buckets*, and rejects `all` with `400 range too wide`,
   whereas DESIGN frames the cap as per bucket unit. So `all` is unservable on the legacy
   routes today. Not resolved here; flagged.
2. `all=1` sets `from` to the Unix epoch rather than the ledger's earliest fact, so `all` can
   never satisfy a capped route even if the ledger is younger than 400 days. Not resolved here.

## Unfinished

None.
