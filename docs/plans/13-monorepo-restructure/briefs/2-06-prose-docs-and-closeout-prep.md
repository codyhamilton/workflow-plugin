# Brief: 2-06 — Prose, stable docs, and changelog

Consumer: the phase 2 worker that runs after `2-02`, `2-03`, `2-04`, and `2-05` have landed on the branch.
Owned paths:
`skills/execute/SKILL.md`,
`skills/refine/templates/brief.md`,
`.claude/skills/jev-variants/SKILL.md`,
`.claude/skills/workflow-tuning/reference.md`,
`docs/design/01-event-model-and-ingest.md`,
`docs/design/03-remote-service.md`,
`docs/design/05-distribution.md`,
`docs/design/07-analytics-site.md`,
`README.md`,
`CHANGELOG.md`,
`.claude-plugin/plugin.json`,
`.cursor-plugin/plugin.json`,
`.codex-plugin/plugin.json`,
`docs/plans/13-monorepo-restructure/reports/2-06-prose-docs-and-closeout-prep.md` (new).
Touch nothing else. Do not edit `DESIGN.md` or close `IMPLEMENTATION.md` Carried.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/2-06-prose-docs-and-closeout-prep.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`).
Depends on: `2-02`, `2-03`, `2-04`, `2-05`.
Runs alongside: nothing.
Budget: 25 files to read, about 150 lines to change, 50 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 2 [cmd] old-path search, Architectural Implications list, Plugin version-bump bullets, Packages catalogue citation for skills.
2. `CHANGELOG.md` — `## 2.10.0` pattern; add a new section for this phase's user-visible moves.
3. Grep live tree for forbidden old paths (same patterns as Phase 2 outcome).

## Goal

Core skill prose and stable docs describe `packages/workflow`, `packages/hooklog`, and `packages/workflow/catalogue`; plugin manifests bump one minor; CHANGELOG warns about hard-coded spool paths.

## Contract

Cited, binding (Phase 2 [cmd]): live search excludes `docs/plans/`, `docs/lab/`, earlier `CHANGELOG.md` entries; forbidden: `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks`, segment forms listed in DESIGN.

Cited, binding (Packages): rubric path becomes `packages/workflow/catalogue/checks/execution-report.json` in `skills/execute/SKILL.md` and `skills/refine/templates/brief.md`.

Cited, binding (Plugin): minor bump together on Claude, Cursor, Codex manifests when shipped plugin files change; `bin/VERSION` unchanged.

Compatibility note in DESIGN: "A user-pasted Cursor config that hard-codes an absolute `.../tools/hooklog/spool.sh` … will break silently … Phase 2 CHANGELOG entry calls this out."

## Changes

- Repoint skill and doc path literals per Phase 2 surfaces; update layout tables in `docs/design/05-distribution.md` and path mentions in 01, 03, 07.
- Bump plugin manifest versions `2.10.0` → `2.11.0` (all three plugin.json files).
- Add `CHANGELOG.md` entry above `2.10.0` documenting package moves and the Cursor absolute-spool migration note.
- Run the DESIGN old-path search across the live tree; if hits remain outside exemptions, report `blocked` with file list (do not fix files outside owned paths).

### Keep untouched

Historical `docs/plans/` and dated `docs/lab/` content; `bin/VERSION`; hook command shapes in `hooks/` (owned by `2-03`).

## Done evidence

- `rg` (or equivalent) for `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks` on live files per DESIGN exclusions → no hits.
- `rg 'tools/quality/checks/execution-report' skills` → no hits; `packages/workflow/catalogue/checks/execution-report.json` cited instead.
- Manifest versions are `2.11.0` in all three plugin.json files.

## Report back

Under 1,500 tokens. Status, search command output, deviations. Phase-level [cmd] outcomes (Claude hook session, `bin/workflow --version` with cache cleared, full `tools/release/build.sh`) are orchestrator verification, not this unit's done evidence unless you ran them.
