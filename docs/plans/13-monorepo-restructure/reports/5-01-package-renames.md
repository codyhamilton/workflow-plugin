# Unit report: 5-01 — Package renames (git mv only)

**Status:** `done`

**Rename commit:** `1995a11` — Phase 5: git mv workflow packages to yakka directory names

## What moved

- `packages/workflow/**` → `packages/yakka/**` (Go module tree; bytes unchanged).
- `packages/workflow-analytics/**` → `packages/yakka-analytics/**`.
- `packages/opencode-workflow-hooks/**` → `packages/opencode-yakka-hooks/**`.
- `packages/hooklog/` left in place (per brief).

## Done evidence

```
test ! -e packages/workflow && test ! -e packages/workflow-analytics && test ! -e packages/opencode-workflow-hooks → exit 0
test -f packages/yakka/go.mod && test -f packages/yakka-analytics/package.json && test -f packages/opencode-yakka-hooks/package.json → exit 0
git show --stat --format= 1995a11 → 229 files changed, 0 insertions(+), 0 deletions(-); all renames
```

## `git diff --cached --stat` (rename commit, before commit)

229 files changed, 0 insertions(+), 0 deletions(-); staged diff showed only `{old => new}` renames.

## Deviations

None. Rename-only commit; no file content edits; imports, manifests, hooks, and path strings elsewhere were not updated (per brief).

## Unfinished work

Path-rewrite follow-on (Decision 1 commit 2): repo still references `packages/workflow`, `packages/workflow-analytics`, and `packages/opencode-workflow-hooks` in builds, configs, and docs until a later unit repoints them.

## Known problems

None for this unit’s done evidence. Builds and tests that resolve old package paths will fail until the path-rewrite unit lands.
