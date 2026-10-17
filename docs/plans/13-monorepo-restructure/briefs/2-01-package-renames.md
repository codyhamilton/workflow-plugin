# Brief: 2-01 — Package renames (git mv only)

Consumer: the worker dispatched first in phase 2. This commit is rename-only; no content edits.
Owned paths:
`tools/workflow/**` (moves to `packages/workflow/**`),
`tools/hooklog/**` (moves to `packages/hooklog/**`),
`tools/quality/criteria.json`,
`tools/quality/checks/**` (move into `packages/workflow/catalogue/`),
`docs/plans/13-monorepo-restructure/reports/2-01-package-renames.md` (new).
Touch nothing else. Do not edit file contents, `hooks/`, `bin/`, `skills/`, docs, or manifests.
Commits: Commit to the current branch (`cursor/restructure-plan-scope-93a1`) when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-01-package-renames.md` (rubric in `tools/quality/checks/execution-report.json` until later units repoint prose).
Depends on: Phase 1 closed on this branch.
Runs alongside: nothing.
Budget: 15 files to read, 0 lines of content change, 25 tool turns. Past the budget, stop: hand off in `IMPLEMENTATION.md` under this brief's name, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — `### Phase 2: Runtime units become packages` (Surfaces: Moves), Decision 1 (two-commit move shape).
2. `ls` of `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks/`.

## Goal

Land Decision 1's rename-only commit: runtime trees and the scorer catalogue exist under `packages/` with unchanged file bytes.

## Contract

Cited, binding (Decision 1): "each move lands as two commits. 1. A rename-only `git mv` commit, with no content edits. 2. A path-rewrite commit."

Cited, binding (Phase 2 surfaces): "`tools/workflow/**` → `packages/workflow/**`"; "`tools/quality/{criteria.json,checks/**}` → `packages/workflow/catalogue/`"; "`tools/hooklog/**` → `packages/hooklog/**`."

Cited, binding (Packages contract): "The catalogue lives at `packages/workflow/catalogue/`, which holds `criteria.json` and `checks/*.json`."

## Changes

- Use `git mv` only. Create `packages/workflow/catalogue/` by moving `criteria.json` and the `checks/` directory out of `tools/quality/` (leave other `tools/quality/` files in place).
- After this unit, `tools/workflow` and `tools/hooklog` must not exist; `packages/workflow` and `packages/hooklog` must exist with the same trees as before.
- Do not change `go.mod`, imports, hooks, `bin/workflow`, or any string inside a file.

### Keep untouched

Every byte inside moved files; only paths on disk change.

## Done evidence

- `test ! -e tools/workflow && test ! -e tools/hooklog` → exit 0.
- `test -f packages/workflow/go.mod && test -f packages/hooklog/spool.sh && test -f packages/workflow/catalogue/criteria.json` → exit 0.
- `git diff --cached --stat` shows renames only (no "insertions" from content edits in the same commit). If you must fix a git mistake, reset and redo; do not patch content in this commit.

## Report back

Under 1,500 tokens. Status, what moved, `git diff --cached --stat`, any deviation. Do not fix path references here.
