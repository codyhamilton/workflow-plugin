# Brief: 2-04 — Python maintainer tooling paths

Consumer: a phase 2 worker running after `2-01`.
Owned paths:
`tools/quality/**` (catalogue files are gone; repoint reads to `packages/workflow/catalogue/`),
`tools/jev-variants/**`,
`tools/release/**`,
`docs/plans/13-monorepo-restructure/reports/2-04-python-tooling-paths.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-04-python-tooling-paths.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`).
Depends on: `2-01`.
Runs alongside: `2-02`, `2-03`, `2-05`.
Budget: 40 files to read, about 250 lines to change, 80 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 2 surfaces (Python path fixes, Build), Packages catalogue contract (`tools/quality` reads catalogue from package).
2. `tools/quality/quality.py` — `criteria.json` load path; grep `hooklog` and `parents` under `tools/quality/`.
3. `tools/jev-variants/runner.py`, `events.py`, `build_corpus.py`, `case2/*`, `case4/*` — `sys.path` into sibling `hooklog`.
4. `tools/release/build.sh`, `phase5_outcome.py`, `test_release.py` — `tools/workflow` and `tools/hooklog` literals.

## Goal

Maintainer Python tools import hooklog from `packages/hooklog`, load checks from `packages/workflow/catalogue/`, and release scripts build from `packages/workflow`.

## Contract

Cited, binding: "`tools/quality` reads `criteria.json` and `checks/` from there" (`packages/workflow/catalogue/`). Release: "`tools/release/build.sh` builds `packages/workflow-analytics` and copies … then cross-compiles from `packages/workflow`."

Assumption 10: `tools/quality` stays a tool; only imports and catalogue reads change. Assumption 5: do not move `tools/cloud-env` or `tools/driver`.

## Changes

- Repoint `quality.py` and any loader to `packages/workflow/catalogue/criteria.json` and `checks/` (not a copy left in `tools/quality/`).
- Change hooklog `sys.path` inserts from `../hooklog` to `../../packages/hooklog` (or equivalent correct relative path from each file).
- Update `tools/release/build.sh` site copy and `go build` cwd to `packages/workflow`; update `phase5_outcome.py` and `test_release.py` path lists accordingly.
- Update jev-variants README/skill-cross-refs only if owned here: `.claude/skills/jev-variants/SKILL.md` is **not** owned (unit `2-06`).

### Keep untouched

`tools/quality/server.py` listen address, systemd unit template path `%REPO%/tools/quality/server.py`, and scoring behaviour.

## Done evidence

- `python3 -m unittest discover -s tools/quality/tests -v` → OK (if present; else `python3 -m unittest tools/quality/test_*.py` per repo convention).
- `python3 -m unittest discover -s tools/jev-variants/tests -v` → OK.
- `python3 -m unittest tools/release/test_release.py -v` → OK.
- `rg "tools/hooklog|tools/workflow|tools/quality/criteria|tools/quality/checks" tools/quality tools/jev-variants tools/release` → no hits.

## Report back

Under 1,500 tokens. Status, test output, deviations.

## Amendment

`bin/workflow` path literals belong to 2-02. That unit already replaced `tools/workflow` with `packages/workflow` there. A re-dispatch does not edit `bin/workflow`. The release suite's `test_6_no_go_no_asset` fails when `/usr/bin/go` exists and `packages/workflow/go.mod` is present; hide that binary for the run.
