# Brief: 5-06 — Quality catalogue path and skill citations

Consumer: a phase 5 worker running after `5-01`.
Owned paths:
`tools/quality/{quality.py,server.py,hookevents.py,interventions.py,thresholds.py,executor_reports.py}` (catalogue reads only),
`plugins/yakka/skills/execute/SKILL.md`,
`plugins/yakka/skills/refine/templates/brief.md`,
`docs/plans/13-monorepo-restructure/reports/5-06-quality-catalogue-and-skill-citations.md` (new).
Touch nothing else. Do not rename skill `name:` frontmatter or `workflow:` command prefixes (Phase 6).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-06-quality-catalogue-and-skill-citations.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `5-01`.
Runs alongside: `5-02`, `5-04`.
Budget: 20 files to read, about 40 lines to change, 35 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Packages catalogue contract; Phase 5 outcome "[cmd] … Catalogue citations in the skills are repointed here too"; Domain: Names (`WORKFLOW_QUALITY_*` stays on the legacy service).
2. Grep `packages/workflow/catalogue` under `tools/quality/`.
3. Grep `packages/workflow/catalogue` under `plugins/yakka/skills/execute` and `plugins/yakka/skills/refine/templates/brief.md`.

## Goal

Maintainer quality tooling and the execute/refine skill templates cite `packages/yakka/catalogue`, matching the renamed binary package, without changing broader skill naming (Phase 6).

## Contract

Cited, binding: "The rubric citation in `skills/execute/SKILL.md` and `skills/refine/templates/brief.md` becomes `packages/workflow/catalogue/checks/execution-report.json`." (Phase 2 wording — Phase 5 updates `workflow` → `yakka` in that path only.)

Cited, binding: "`tools/quality` reads `criteria.json` and `checks/` from there." (catalogue at `packages/yakka/catalogue/` after rename.)

Cited, binding: Legacy quality service keeps `WORKFLOW_QUALITY_*`; do not rename quality service env vars or schema.

## Changes

- Replace path literals `packages/workflow/catalogue` → `packages/yakka/catalogue` in the owned `tools/quality` modules (ROOT joins and comments that name the catalogue location).
- Replace the same path in the two skill files only where the execution-report rubric is cited; leave other `workflow` product naming in skill prose untouched.

### Keep untouched

`tools/quality/server.py` behaviour beyond catalogue path joins. Other skills. `README.md` at repo root (Phase 4 Carried item 2 on signal-log prose is Phase 7 unless this file is not in owned paths — it is not).

## Done evidence

- `python3 -m unittest discover -s tools/quality -p 'test_*.py' -v` → pass.
- `grep -r 'packages/workflow/catalogue' tools/quality plugins/yakka/skills/execute plugins/yakka/skills/refine` → no hits.

## Report back

Under 1,500 tokens. Status, test output, deviations.
