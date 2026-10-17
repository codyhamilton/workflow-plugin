# Unit report: 2-01 — Package renames

**Status:** `done`

**Rename commit:** `cff6f64` — Move workflow, hooklog, and scorer catalogue under packages/

## What moved

- `tools/workflow/**` → `packages/workflow/**` (Go module tree unchanged on disk bytes).
- `tools/hooklog/**` → `packages/hooklog/**`.
- `tools/quality/criteria.json` → `packages/workflow/catalogue/criteria.json`.
- `tools/quality/checks/**` → `packages/workflow/catalogue/checks/**`.
- Other `tools/quality/` files left in place.

## Done evidence

**Before**

```
test ! -e tools/workflow && test ! -e tools/hooklog → exit 1 (paths still present)
test -f packages/workflow/go.mod → exit 1
```

**After** (commit `cff6f64`)

```
test ! -e tools/workflow && test ! -e tools/hooklog → exit 0
test -f packages/workflow/go.mod && test -f packages/hooklog/spool.sh && test -f packages/workflow/catalogue/criteria.json → exit 0
git show --stat --format= cff6f64 → 119 files changed, 0 insertions(+), 0 deletions(-); all renames
```

## Deviations

None. Rename-only commit has no content edits; path references elsewhere were not updated (per brief).

## Contradictions

None between this brief and cited DESIGN.md Phase 2 / Decision 1 contracts.

## Problems outside done evidence

Repo-wide builds, hooks, and imports still point at old `tools/` paths until the follow-on path-rewrite unit.
