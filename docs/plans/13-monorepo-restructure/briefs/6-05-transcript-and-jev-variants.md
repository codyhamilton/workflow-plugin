# Brief: 6-05 — Transcript and jev-variants identifiers

Consumer: a phase 6 worker on the monorepo-restructure branch.
Owned paths:
`tools/transcript/**`,
`tools/jev-variants/**`,
`docs/plans/13-monorepo-restructure/reports/6-05-transcript-and-jev-variants.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-05-transcript-and-jev-variants.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 5 closed.
Runs alongside: `6-01`, `6-02`, `6-04`.
Budget: 20 files to read, about 80 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 surfaces (`tools/transcript/` and `tools/jev-variants/` identifiers); Domain: Names (`WORKFLOW_*` → `YAKKA_*` except `WORKFLOW_QUALITY_`).
2. `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md` — residual-name pattern `WORKFLOW_(?!QUALITY_)`.
3. `tools/transcript/lib/jev_client.py`, `tools/jev-variants/case4/build4.py` (and any other files under owned paths that still match the scan).

## Goal

Maintainer transcript and jev-variants tooling uses `YAKKA_*` identifier prefixes where the residual scan forbids `WORKFLOW_*`, without changing Jev question semantics.

## Contract

Cited, binding (Domain: Names): "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`."

Cited, binding (Phase 6 outcome, scan scope includes `tools/`): residual-name scan must report nothing under `tools/` (with existing global exclusions).

Settled: Common-noun "workflow" in prose (`iterate workflow`, CLI flag `--no-workflow-alignment`) is not an env identifier; rename only Python constants/env-style names that match `WORKFLOW_` (e.g. `WORKFLOW_ALIGNMENT_*` → `YAKKA_ALIGNMENT_*`). Keep user-facing English that describes the method.

Settled: Phase 5 Carried item 3 is closed in driver via `6-03`; this unit does not edit `tools/driver/`.

## Changes

- `tools/transcript/lib/jev_client.py`: rename `WORKFLOW_ALIGNMENT_*` symbols and dict keys to `YAKKA_ALIGNMENT_*` / `yakka_alignment` if the JSON question id must stay stable for stored results, document the id in the report; prefer stable external ids only when tests assert them.
- `tools/jev-variants/`: replace hard-coded `workflow-plugin` install paths in fixtures with `yakka` repo paths where they are product identifiers (`github.com/codyhamilton/yakka`, `~/.cache/yakka`, etc.). Corpus token `workflow-plugin` in `case2/pair.py` may stay if it names an external repo slug in research data — if the scan flags it, use an allowed exception only when it is historical corpus text; otherwise rename to `yakka`.

### Keep untouched

`tools/driver/`, `tools/quality/`, `packages/**`, and plugin trees.

## Done evidence

Before:

- `python3` scan snippet or `rg 'WORKFLOW_' tools/transcript tools/jev-variants` → lists hits (record lines).

After:

- `python3 -m unittest discover -s tools/transcript/tests -p 'test_*.py' 2>/dev/null; python3 -m unittest discover -s tools/jev-variants/tests -p 'test_*.py'` → run whichever suites exist on this branch; all OK (if a tree has no tests, run the tool's documented smoke command from its README instead and record exit 0).
- `rg 'WORKFLOW_(?!QUALITY_)' tools/transcript tools/jev-variants` → no hits in `.py` files.

## Report back

Under 1,500 tokens. Status, rg and unittest output, deviations.
