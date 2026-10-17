# Brief: 5-01 — Package renames (git mv only)

Consumer: the worker dispatched first in phase 5. This commit is rename-only; no content edits.
Owned paths:
`packages/workflow/**` (moves to `packages/yakka/**`),
`packages/workflow-analytics/**` (moves to `packages/yakka-analytics/**`),
`packages/opencode-workflow-hooks/**` (moves to `packages/opencode-yakka-hooks/**`),
`docs/plans/13-monorepo-restructure/reports/5-01-package-renames.md` (new).
Touch nothing else. Do not edit file contents, `plugins/yakka/`, `tools/`, docs, or manifests. `packages/hooklog/` stays at that path.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-01-package-renames.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json` after this unit; until then use the path that exists on disk before the mv).
Depends on: Phase 4 closed on this branch.
Runs alongside: nothing.
Budget: 15 files to read, 0 lines of content change, 25 tool turns. Past the budget, stop: hand off in `IMPLEMENTATION.md` under this brief's name, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — `### Phase 5: Runtime runs as yakka` (Surfaces), Decision 1 (two-commit move shape), Domain: Names (`packages/yakka`, npm package names).
2. `ls` of `packages/workflow`, `packages/workflow-analytics`, `packages/opencode-workflow-hooks`.

## Goal

Land Decision 1's rename-only commit for the runtime package directories that take the `yakka` name before any import or string rewrites.

## Contract

Cited, binding (Decision 1): "each move lands as two commits. 1. A rename-only `git mv` commit, with no content edits. 2. A path-rewrite commit."

Cited, binding (Phase 5 surfaces): "`packages/workflow` → `packages/yakka`"; "`packages/workflow-analytics` → `packages/yakka-analytics`"; "`packages/opencode-workflow-hooks` → `packages/opencode-yakka-hooks`"; "`packages/hooklog`" remains.

Cited, binding (Decision 3): "The binary package is `packages/yakka`, from `packages/workflow`."

## Changes

- Use `git mv` only for the three trees above.
- After this unit, `packages/workflow`, `packages/workflow-analytics`, and `packages/opencode-workflow-hooks` must not exist; the `yakka`-named directories must exist with the same trees as before.
- Do not change `go.mod`, imports, `plugins/yakka/bin/workflow`, hooks, or any string inside a file.

### Keep untouched

Every byte inside moved files; only paths on disk change. `packages/hooklog/` is not moved.

## Done evidence

- `test ! -e packages/workflow && test ! -e packages/workflow-analytics && test ! -e packages/opencode-workflow-hooks` → exit 0.
- `test -f packages/yakka/go.mod && test -f packages/yakka-analytics/package.json && test -f packages/opencode-yakka-hooks/package.json` → exit 0.
- `git diff --cached --stat` shows renames only (no content insertions from edits in the same commit).

## Report back

Under 1,500 tokens. Status, what moved, `git diff --cached --stat`, any deviation.
