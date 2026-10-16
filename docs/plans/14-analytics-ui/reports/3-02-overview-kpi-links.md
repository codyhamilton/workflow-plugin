Status: done with concerns

## What changed

- **`+page.svelte`**: Added `kpiHref()` (mirrors layout `navHref`, sets `metric` on `/trends` links). Wrapped the nine `SPARKS` KPI tiles in `<a class="tile">` with solarized-safe link styling and `pointer-events: none` on sparklines so clicks reach the anchor.
- **`overview.spec.ts`**: Added `KPI links` describe with four navigation tests (conversations, artifact versions → trends + metric, hooks, usage).

## Done evidence

**Before** (KPI tests added, no links yet):

```
npx playwright test tests/e2e/overview.spec.ts -g "KPI"
# 4 failed — timeout waiting for locator('a').filter({ has: getByTestId('summary-…') })
```

**After**:

```
npx playwright test tests/e2e/overview.spec.ts -g "KPI"
# 4 passed (13.4s)
```

**Fixture regression check** (required by brief):

```
npx playwright test tests/e2e/overview.spec.ts -g "overview shows the fixture numbers"
# 1 failed — summary-unpriced_calls Expected "2" Received "1" (cost tile shows "$0.16, 1 unpriced")
```

Same failure with `+page.svelte` and KPI tests stashed (implementation reverted), so this is not caused by KPI links. Symptom: whole-window usage fields on `/` disagree with `USAGE_ALL` in `fixture.ts`. Location: e2e serve `GET …/analytics/summary` vs UI tiles `summary-unpriced_calls` / `summary-cost_usd`. Likely root cause: branch/worktree ledger or summary aggregation drift relative to hand-counted fixture (see also `fixture.spec.ts` conversation-row mismatch).

## Deviations

- Added `pointer-events: none` on in-tile sparklines so ECharts does not swallow anchor clicks (artifact-versions KPI was flaky without it).
- Artifact-versions KPI assertion uses `toHaveURL` (waits for navigation) instead of reading `page.url()` synchronously after click.

## Contradictions

- **DESIGN.md** (Report interaction) says trends links set query param **`measure`**. **`trends/+page.svelte`** and this brief use **`metric`**. Implementation follows the brief and existing trends page (sets `metric=`).

## Known problems (out of scope)

- `overview shows the fixture numbers` does not pass on this branch without this unit’s changes; not fixed here per brief scope.
