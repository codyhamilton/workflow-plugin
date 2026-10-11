# Report: 4-09 — Repos: a fixed number of requests, not one per repo

Status: **done with concerns**

## What changed

- `packages/workflow-analytics/src/routes/repos/+page.svelte`: rewritten on `view` and the client
  (`getJSON`). Four slots — `repos-hook_events`, `repos-conversations`, `repos-artifact_versions`,
  `repos-commits` — each issue one `analytics/query` with `measure=<m>`, `dim=repo_id`, `top=100`,
  `bucket=none` (built with `view.paramsFor('query', extra)`). The four responses are joined by
  `k[0]`; a repo absent from a measure counts 0; `__other__` sorts last and is not clickable.
  `BarChart testid="repos-chart"` charts `hook_events` by repo. A row click or bar select calls
  `view.drill('repo_id', repo, { shift })`; shift excludes. Cell ids `repo-<repo>-<field>` are kept
  for the four measures.
- `tests/e2e/repos.spec.ts`: rewritten to 7 tests (counts from the hand-counted fixture; `?repo_id`
  filter and reload; exactly four `analytics/query` and no `analytics/summary` on load; a 40-repo
  `page.route` still exactly four; row click → include chip, shift-click → exclude chip dropping the
  repo; `__other__` inert; a filter change settles within 1 s).

## Check output

Before rewriting the spec, the old spec ran against the new page:

```
2 failed
  › both fixture repos appear with their own counts — getByTestId('repo-r1-by_kind-design'): element not found
  › repo_id in the URL shows only that repo        — getByTestId('repo-r1-by_kind-design'): element not found
```

Both stop at the first removed `by_kind-*` cell; the four measure cells asserted correctly. After:

```
npm test                                       11 files, 76 tests passed
npm run build                                  adapter-static wrote site, done
E2E_PORT=4409 npm run test:e2e -- repos.spec.ts  7 passed
```

## Deviations

1. `+page.svelte` returns early until `view.facets !== null` before issuing its queries. Reason: the
   effect re-ran on the facets null→object transition, and the client's supersede path aborted and
   re-sent the in-flight queries (observed 6–7 requests, variable). With the guard, load is exactly
   four. See the bug note.
2. The brief words the count test as `trackRequests(page, /analytics\//)` "counts four
   analytics/query requests". That pattern also matches the shell's `analytics/facets`, so I filter
   the tracked URLs down to `/analytics/query` before asserting length 4, and separately assert no
   `/analytics/summary`. Same intent, and it also pins `dim=repo_id`, `top=100`, `bucket=none`.

## Contradictions

- DESIGN.md ("`/repos` issues one request, not one per repo") vs the brief's contract of four
  `/query` requests, one per column measure. Implemented per the brief; reporting it, as the brief
  requires, as the loosest reading of "one request". The count is fixed and independent of the repo
  count — the substance of the DESIGN goal — but it is not literally one request.
- The brief's `/analytics\//` regex contradicts its own "counts four `analytics/query`" (deviation 2).

## Bug outside this brief's done evidence

Symptom: re-running a page effect with identical params can issue duplicate HTTP requests.
Location: `src/lib/query.ts`, the client's supersede path — a new call on a slot rejects the previous
call and releases its fetch; the release drops the shared in-flight entry, so the new call re-sends
even though the normalised cache key is unchanged. Root cause: on supersede the in-flight entry is
removed rather than retained for same-key joiners. `/repos` avoids it with the guard above; sibling
units (4-06..4-15) whose effect re-runs on a window change and again when facets resolve may hit it.
Not fixed here.
