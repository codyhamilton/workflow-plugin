# Brief: 5-05 — Release tooling, residual scan, package index

Consumer: a phase 5 worker running after `5-02`, `5-03`, and `5-04`.
Owned paths:
`tools/release/**`,
`tools/release/test_layout.py` (only the `plugins/yakka/bin/` path literal),
`packages/README.md`,
`packages/yakka/README.md`,
`packages/yakka-analytics/README.md`,
`packages/opencode-yakka-hooks/README.md`,
`docs/plans/13-monorepo-restructure/reports/5-05-release-scan-and-index.md` (new).
Touch nothing else. Do not edit plugin manifests, `skills/`, or `install.sh` (Phase 6).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-05-release-scan-and-index.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `5-02`, `5-03`, `5-04`.
Runs alongside: nothing.
Budget: 30 files to read, about 350 lines to change, 80 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 5 outcome [cmd] residual-name scan scope; Domain: Names (`yakka` release artifacts); Packages README fields.
2. Residual-name scan contract (binding; patterns unchanged from folded rename design), quoted in this brief's **Contract** section.
3. `tools/release/build.sh`, `test_release.py`, `phase5_outcome.py`.
4. `tools/release/test_layout.py` — `bin/workflow` path in plugin scan.

## Goal

Release scripts build `yakka` artifacts from `packages/yakka`, the release test suite exercises `plugins/yakka/bin/yakka`, a committed residual-name scan enforces Phase 5's runtime scope, and package READMEs/index match the renamed directories.

## Contract

Cited, binding (Phase 5): "[cmd] The residual-name scan reports nothing under the runtime packages (`packages/yakka`, `packages/hooklog`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`), `plugins/yakka`'s `bin/`, `hooks/`, `script/` and MCP configs, and `tools/release/`."

Cited, binding (folded rename design, unchanged): Residual-name scan runs case-sensitive over `git ls-files`. **Excluded paths:** `docs/plans/`; `docs/lab/`, `docs/analysis/`, `evals/results/`; `tools/quality/`; in `CHANGELOG.md`, every entry up to and including the rename entry (not yet written — exclude nothing in CHANGELOG until Phase 7 adds that entry, so treat all CHANGELOG lines as excluded only when the rename entry exists); in `docs/design/*.md`, sections whose heading contains `YYYY-MM-DD`. **Forbidden patterns (extended regex):** `WORKFLOW_` not followed by `QUALITY_`; `\bbin/workflow\b`, `\bcmd/workflow\b`, `\bpackages/workflow\b`; `\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b`; `\bopencode-workflow-hooks\b`, `WorkflowSignalsPlugin`; `\bworkflow-(darwin|linux)-`; `workflow (version|<version>)` at the start of a `--version` string; `\bworkflow:(design|refine|execute|close-out|comprehensive-review|post-build|plan|setup)\b`; `(\.local/(share|state)|\.config|\.cache)/workflow\b`; `\.cursor/(plugins/local|skills)/workflow\b`; `"workflow"\s*:` in JSON, `\[mcp_servers\.workflow\]`, `mcp__plugin_workflow_`; `Workflow-(Phase|Plan)\b`, `workflow-report\b`. **Allowed exceptions for the last line only:** `tools/driver/`; `evals/scenarios/trailer-completeness/`; one legacy-forms sentence per reading skill; Go test fixtures under `packages/yakka/` with recorded commit text.

Refine choice: commit the scan as `tools/release/scan_residual_names.py` (stdlib only) invokable as `python3 tools/release/scan_residual_names.py --scope phase5` limiting roots to the Phase 5 outcome list above. A failing run prints `file:line:pattern` and exits non-zero.

Cited, binding: Release "Artifact names (`workflow-<os>-<arch>`)" become `yakka-<os>-<arch>` per Domain: Names.

## Changes

- Update `build.sh` to build from `packages/yakka`, embed from `packages/yakka-analytics`, output `yakka-*` binaries.
- Update `test_release.py`: wrapper `plugins/yakka/bin/yakka`, version regex `^yakka 0\.…`, cache dir `yakka`, env `YAKKA_*`, paths `packages/yakka`, binary names `yakka-linux-amd64`, etc. `test_1_clean_cache_build` must pass (fixes Phase 4 Carried item 3 when combined with `5-03`).
- Update `phase5_outcome.py` paths and env vars for yakka names; keep clause shape.
- Implement `tools/release/scan_residual_names.py` per contract; wire a unittest or document the exact command in done evidence.
- Repoint `test_layout.py` plugin bin scan to `bin/yakka`.
- Update `packages/README.md` and per-package README **Consumers** paths to the new directory names; keep the four labelled fields.

### Keep untouched

Phase 6 surfaces (`skills/`, manifests, `install.sh`, `tools/driver` env renames). `CHANGELOG.md` migration entry (Phase 7).

## Done evidence

- `python3 -m unittest discover -s tools/release -p 'test_*.py'` → pass (including layout and release suites; Go 1.27+ on PATH for wrapper build tests).
- `python3 tools/release/scan_residual_names.py --scope phase5` → exit 0, no output.
- `python3 tools/release/phase5_outcome.py` → all clauses PASS (report stdout).

## Report back

Under 1,500 tokens. Status, test and scan output, deviations.
