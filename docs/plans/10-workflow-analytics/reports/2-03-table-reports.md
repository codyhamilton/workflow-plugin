# Report: 2-03 quality, executions and conversations reports

Status: done.

## Done against the brief

- `src/lib/components/Pager.svelte`: "Load more" calls the same route with the first page's params plus `cursor=<next>`, appends rows through `onpage`, and is hidden when `next` is absent. The cursor is in memory only. A response that arrives after the params changed is dropped.
- `/quality`: uses the first valid `kind` in the URL (default `design`), shows a note when the URL holds several, and has kind buttons that set a single `kind`. It reads `GET /v1/analytics/scores` (shared filter, one kind) and `GET /v1/baselines?kind=<k>` (all-time, no other parameters) in parallel. One row per check in response order: window `n,min,p25,median,p75,max`, then all-time baseline `n,p25,median,p75`, blank when the baseline has no entry. Test ids `q-<check>-w-<field>` and `q-<check>-b-<field>`. No chart. It reads both and writes nothing.
- `/executions`: three count tiles (`exec-count-<shape>`), a table with `exec-row` per row, the Pager. `/conversations`: table with `conv-row` and `conv-<id>-<field>` on the three counts, the Pager. A `limit` URL param is passed to the API; empty values go through `label()`.
- Specs: `quality.spec.ts` (3), `executions.spec.ts` (3), `conversations.spec.ts` (3).

## Check output

- Before (specs only, no routes): 9 failed (all nine new tests).
- After: `npm run test:e2e` (whole suite) 22 passed, including the 9 new tests; the zero-scorer run, the stubbed run (every `q-*-w-*` and `q-*-b-*` cell, all requests `GET`), repo filter with reload, and both `limit=1` paging walks equal to the unpaged rows.
- `npm run build` succeeds; the bundle check runs inside the e2e web server command (`scripts/e2e-build.mjs`) with the `E2E_FORBIDDEN` values and passed as part of that run.

## Departures

- Quality has no chart (optional in the brief).
- The stubbed quality spec adds `access-control-allow-origin: *` to fulfilled responses, because the page and the serve are cross-origin.
- Row table keys are by index, since rows have no unique key field.

## Contradictions and gaps

- None between the brief and its cited contracts. No shared file needed a change. Carried item 1 (paging loads the full sorted set) is untouched.
- Bundle check was not re-run standalone; `svelte-check` is still not installed.

## Unfinished

Nothing in this unit.
