# Brief: 7-06 — CHANGELOG scan cut and full-repo residual scan

Consumer: a phase 7 close-out worker after `7-01` through `7-05` are merged on the branch.
Owned paths:
`tools/release/scan_residual_names.py`,
`tools/release/test_scan_residual_names.py`,
`docs/plans/13-monorepo-restructure/reports/7-06-scan-changelog-cut-and-full-scope.md` (new).
Touch nothing else. Do not weaken `--scope phase5` or `--scope phase6`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-06-scan-changelog-cut-and-full-scope.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `7-01`, `7-02`, `7-03`, `7-04`, `7-05`.
Runs alongside: nothing.
Budget: 10 files to read, about 80 lines to change, 40 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [cmd] full residual scan.
2. `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md` — **Contract** (exclusions, forbidden patterns, trailer exceptions, CHANGELOG rule).
3. `docs/plans/13-monorepo-restructure/briefs/6-06-residual-scan-phase6.md` — settled: Phase 7 owns `--scope all` after CHANGELOG rename entry.
4. `tools/release/scan_residual_names.py` — `rename_changelog_cutoff`, `globally_excluded`, `design_sections_to_skip`.

## Goal

Implement CHANGELOG line-level exclusion after the rename entry and prove the full-repo residual scan is clean.

## Contract

Cited, binding (Phase 7 outcome): "[cmd] The residual-name scan over its whole scope reports nothing outside its exceptions."

Cited, binding (`5-05` brief **Contract**, unchanged): Residual-name scan runs case-sensitive over `git ls-files`. **Excluded paths:** `docs/plans/`; `docs/lab/`, `docs/analysis/`, `evals/results/`; `tools/quality/`; in `CHANGELOG.md`, every entry up to and including the rename entry (not yet written — exclude nothing in CHANGELOG until Phase 7 adds that entry, so treat all CHANGELOG lines as excluded only when the rename entry exists); in `docs/design/*.md`, sections whose heading contains `YYYY-MM-DD`. **Forbidden patterns (extended regex):** `WORKFLOW_` not followed by `QUALITY_`; `\bbin/workflow\b`, `\bcmd/workflow\b`, `\bpackages/workflow\b`; `\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b`; `\bopencode-workflow-hooks\b`, `WorkflowSignalsPlugin`; `\bworkflow-(darwin|linux)-`; `workflow (version|<version>)` at the start of a `--version` string; `\bworkflow:(design|refine|execute|close-out|comprehensive-review|post-build|plan|setup)\b`; `(\.local/(share|state)|\.config|\.cache)/workflow\b`; `\.cursor/(plugins/local|skills)/workflow\b`; `"workflow"\s*:` in JSON, `\[mcp_servers\.workflow\]`, `mcp__plugin_workflow_`; `Workflow-(Phase|Plan)\b`, `workflow-report\b`. **Allowed exceptions for the last line only:** `tools/driver/`; `evals/scenarios/trailer-completeness/`; one legacy-forms sentence per reading skill; Go test fixtures under `packages/yakka/` with recorded commit text.

Cited, binding (`5-05`): A failing run prints `file:line:pattern` and exits non-zero.

Settled: when `rename_changelog_cutoff()` is true, replace whole-file CHANGELOG skip with **line-level** skip: from the `## … rename …` heading through end of file (that section plus every older entry below it). Only lines **before** that heading — future release sections added above the rename block — are scanned.

## Changes

- Add `changelog_sections_to_skip(text)` (or equivalent): locate the first `##` heading whose text matches `\brename\b` (case-insensitive); skip from that heading's start through EOF. Scan any content above it.
- Wire it in `scan_file` for `CHANGELOG.md` when `rename_changelog_cutoff()` is true; remove the `globally_excluded` whole-file CHANGELOG skip that blocks line-level cut.
- `test_scan_residual_names.py`: add `test_all_clean_in_repo` subprocess for `--scope all`.
- If `--scope all` still fails after `7-01`–`7-05`, stop and report `blocked` with the file list — do not edit doc surfaces outside this unit's owned paths.

### Keep untouched

`PATTERNS`, `phase5`/`phase6` scope roots, trailer exceptions, and `tools/quality/` skip.

## Done evidence

Before (requires `7-01` rename section on branch): `python3 tools/release/scan_residual_names.py --scope all` → exit 1 with hits outside excluded paths.

After:

- `python3 tools/release/scan_residual_names.py --scope phase5` → exit 0, no output.
- `python3 tools/release/scan_residual_names.py --scope phase6` → exit 0, no output.
- `python3 tools/release/scan_residual_names.py --scope all` → exit 0, no output.
- `python3 -m unittest tools/release/test_scan_residual_names.py` → OK (including `test_all_clean_in_repo`).

## Report back

Under 1,500 tokens. Status, all three scan commands before/after, deviations, contradictions.
