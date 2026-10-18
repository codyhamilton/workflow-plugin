# Brief: 6-06 — Phase 6 residual-name scan

Consumer: a phase 6 worker running after `6-01`, `6-02`, `6-03`, `6-04`, and `6-05`.
Owned paths:
`tools/release/scan_residual_names.py`,
`tools/release/test_scan_residual_names.py`,
`tools/README.md`,
`docs/plans/13-monorepo-restructure/reports/6-06-residual-scan-phase6.md` (new).
Touch nothing else. Do not weaken Phase 5 `--scope phase5` behaviour.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-06-residual-scan-phase6.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `6-01`, `6-02`, `6-03`, `6-04`, `6-05`.
Runs alongside: nothing.
Budget: 15 files to read, about 120 lines to change, 45 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcome [cmd] residual scan scope; Domain: Names (scan exclusions and patterns unchanged).
2. `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md` — full residual-name **Contract** (patterns, exclusions, trailer exceptions).
3. `tools/release/scan_residual_names.py` — existing `--scope phase5`, `TRAILER_EXCEPTION_PREFIXES`, `is_reading_skill_legacy_line`.

## Goal

Extend the committed residual-name scan with a `phase6` scope matching the Phase 6 outcome paths; fix the last `tools/` index typo; prove a clean tree.

## Contract

Cited, binding (Phase 6 outcome): "[cmd] The residual-name scan reports nothing under `skills/`, `.claude/skills/`, the plugin manifests, `install.sh`, `.gitignore` or `tools/`."

Cited, binding (Domain: Names): "The residual-name scan from the folded design is the done check. Its exclusions, forbidden patterns and allowed exceptions are unchanged."

Cited, binding (`5-05` refine choice, extend not replace): `python3 tools/release/scan_residual_names.py --scope phase5` limits to Phase 5 runtime roots. Add `--scope phase6` without changing phase5 file sets.

**Phase 6 scope definition (implement exactly):**

- Prefixes: `plugins/yakka/skills/`, `.claude/skills/`, `tools/` (entire tree subject to `globally_excluded`, including `tools/quality/` skip).
- Exact files: `install.sh`, `.gitignore`, `plugins/yakka/.claude-plugin/plugin.json`, `plugins/yakka/.cursor-plugin/plugin.json`, `plugins/yakka/.codex-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `.claude-plugin/marketplace.json`.
- Patterns, exclusions, and trailer exceptions: same as quoted in `5-05` brief **Contract** (including `tools/driver/`, `evals/scenarios/trailer-completeness/`, reading-skill legacy sentence, Go test fixtures under `packages/yakka/` — the latter are outside phase6 scope but must not be broken).

Settled: Phase 7 owns full-repo `--scope all` after CHANGELOG rename entry. Phase 6 does not add line-level CHANGELOG cutting.

## Changes

- Implement `in_phase6_scope(rel)` and `--scope phase6` in `scan_residual_names.py`. Reuse `scan_file`, `PATTERNS`, and `globally_excluded`.
- `test_scan_residual_names.py`: add `test_phase6_clean_in_repo` (subprocess like phase5).
- `tools/README.md`: fix package index line to `packages/yakka` (not `packages/workflow`).
- If `python3 tools/release/scan_residual_names.py --scope phase6` still reports hits in owned scope after depending units, fix only violations in `tools/README.md` or correct gaps in scan scope wiring — do not reopen `6-01`–`6-05` surfaces except the README line this unit owns.

### Keep untouched

Phase 5 scope roots and `phase5_outcome.py`. `CHANGELOG.md`. Package and plugin runtime trees already clean under `--scope phase5`.

## Done evidence

Before (after `6-01`–`6-05` merged in branch, before this unit's scan wiring):

- `python3 tools/release/scan_residual_names.py --scope phase6` → unknown scope or non-zero (record).

After:

- `python3 tools/release/scan_residual_names.py --scope phase5` → exit 0, no output.
- `python3 tools/release/scan_residual_names.py --scope phase6` → exit 0, no output.
- `python3 -m unittest tools/release/test_scan_residual_names.py` → OK.

## Report back

Under 1,500 tokens. Status, both scan commands stdout/stderr before/after, deviations.
