# Brief: 2-07 — Residual path comments

Consumer: a small fixer after 2-06. Comments only. No behaviour change.
Owned paths:
`packages/workflow/internal/ingest/normalise.go`,
`packages/hooklog/hooklog.py`,
`docs/plans/13-monorepo-restructure/reports/2-07-residual-path-comments.md` (new).
Touch nothing else.
Commits: Commit to the current branch (`cursor/restructure-plan-scope-93a1`) when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-07-residual-path-comments.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: 2-06.
Runs alongside: nothing.
Budget: 4 files to read, about 4 lines to change, 15 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 2 [cmd] old-path search. Live files exclude `docs/plans/`, `docs/lab/`, and earlier `CHANGELOG.md` entries. The new `2.11.0` entry may name the old spool path.
2. `packages/workflow/internal/ingest/normalise.go` — the comment on `normTable` that cites `tools/hooklog/hooklog.py`.
3. `packages/hooklog/hooklog.py` — the module docstring that cites `tools/workflow`.

## Goal

The phase 2 live search no longer hits these two comments.

## Contract

Cited, binding (Phase 2 [cmd]): searching live files for `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks` returns no hits, with the exclusions above.

## Changes

- In `normalise.go`, point that comment at `packages/hooklog/hooklog.py`.
- In `hooklog.py`, point that docstring at `packages/workflow`.
- Do not change functions, imports, or tests.

### Keep untouched

Everything except those two comment strings. The `2.11.0` changelog sentence that names `.../tools/hooklog/spool.sh` stays; the outcome allows it.

## Done evidence

- `rg 'tools/workflow|tools/hooklog' packages/workflow/internal/ingest/normalise.go packages/hooklog/hooklog.py` → no hits.
- `cd packages/workflow && go test ./internal/ingest/` → pass (GOTOOLCHAIN unset).
- `python3 -m unittest discover -s packages/hooklog/tests -v` → OK.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites.
