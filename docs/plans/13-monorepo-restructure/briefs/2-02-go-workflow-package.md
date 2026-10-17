# Brief: 2-02 — Go workflow package and bin resolver

Consumer: a phase 2 worker running after `2-01`.
Owned paths:
`packages/workflow/**`,
`bin/workflow`,
`.gitignore` (only if a path literal must change),
`docs/plans/13-monorepo-restructure/IMPLEMENTATION.md` (add Phase 2 subsection with the recorded rewrite command only),
`docs/plans/13-monorepo-restructure/reports/2-02-go-workflow-package.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-02-go-workflow-package.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`).
Depends on: `2-01`.
Runs alongside: `2-03`, `2-04`, `2-05` (disjoint paths).
Budget: 45 files to read, about 120 lines to change, 80 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Packages (`packages/workflow` row, Catalogue, Sibling depth), Phase 2 outcomes tagged [test] and [cmd] for `bin/workflow --version` and `go test ./...`.
2. `packages/workflow/go.mod` and grep `github.com/codyhamilton/workflow-plugin/tools/workflow` under `packages/workflow/`.
3. `bin/workflow` — step 4 source-build paths (`tools/workflow`).
4. Grep `../../../quality` and `quality` under `packages/workflow/**/*_test.go` (catalogue paths after the move).

## Goal

The Go module is `packages/workflow`; `bin/workflow` source-builds from it; tests load the catalogue from `packages/workflow/catalogue/`.

## Contract

Cited, binding: module `github.com/codyhamilton/workflow-plugin/packages/workflow` (Packages table). "`WORKFLOW_CHECKS_DIR` names this directory" (`packages/workflow/catalogue/`). "`bin/workflow` … step-4 source build reads `packages/workflow` when the checkout contains it." Sibling depth: "`packages/workflow` and `packages/hooklog` are siblings … `../../../hooklog/...` … resolve unchanged."

Assumption 3 is settled: directory `packages/workflow`, not renamed before phase 5.

## Changes

- Rewrite `go.mod` module path and every internal import from `.../tools/workflow/...` to `.../packages/workflow/...`.
- Update `bin/workflow` to probe and build under `packages/workflow` (replace `tools/workflow` literals).
- Repoint all `WORKFLOW_CHECKS_DIR` and `LoadChecks` test paths from `tools/quality` / `../../../quality` to `packages/workflow/catalogue` (use paths relative to each test file; `screen_wiring_test.go` and `scorer` tests are called out in DESIGN surfaces).
- Repoint `pricing_test.go` to `tools/transcript/pricing.json` at the correct depth from `packages/workflow/internal/store/`.
- Leave `../../../hooklog/...` fixture paths as-is where sibling depth still resolves to `packages/hooklog`.
- In `IMPLEMENTATION.md`, under a new `### Phase 2` heading, record the exact command(s) you used for the module-path rewrite (for Decision 1 rebase protocol). Do not close the phase or write Carried.

### Keep untouched

Runtime behaviour, env var names, release asset names, embedded site paths under `internal/serve/site/`, and hooklog capture logic.

## Done evidence

Identify failing check before edits; report before and after.

- `cd packages/workflow && GOTOOLCHAIN=local go test ./...` → pass (or document environment Go version if `go 1.27.1` blocks local run, with the same mitigation phase 1 used in verification).
- `grep -r 'tools/workflow' packages/workflow` → no hits in non-comment code (comments may be updated if they falsely claim old paths).
- `grep 'tools/workflow' bin/workflow` → no hits.

## Report back

Under 1,500 tokens. Status, rewrite command recorded, test output, deviations.
