# Brief: 6-07 — Clear phase 6 residual scan hits

Consumer: a phase 6 fixer running after `6-06`.
Owned paths:
`tools/cloud-env/README.md`,
`tools/cloud-env/bootstrap-yakka-skills.sh`,
`tools/driver/README.md`,
`tools/driver/report.py`,
`tools/jev-variants/case2/pair.py`,
`docs/lab/bootstrap/cursor-cloud-setup.sh`,
`tools/driver/tests/test_install_route.py` (only the two `test_cursor_setup_*` skip guards),
`docs/plans/13-monorepo-restructure/reports/6-07-clear-phase6-scan-hits.md` (new).
Touch nothing else. Do not change `tools/release/scan_residual_names.py` patterns or exceptions.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-07-clear-phase6-scan-hits.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `6-06`.
Runs alongside: nothing.
Budget: 10 files to read, about 40 lines to change, 30 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/reports/6-06-residual-scan-phase6.md` — the twelve hits.
2. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcome residual-scan clause; Domain: Names (`WORKFLOW_` except `WORKFLOW_QUALITY_`).
3. `tools/release/scan_residual_names.py` — `trailer_exception` applies only to `Workflow-Phase`, `Workflow-Plan`, and `workflow-report` lines.

## Goal

Make `python3 tools/release/scan_residual_names.py --scope phase6` exit 0, and make the two cursor-cloud setup tests run against `bootstrap-yakka-skills.sh`.

## Contract

Cited, binding (Phase 6): "[cmd] The residual-name scan reports nothing under `skills/`, `.claude/skills/`, the plugin manifests, `install.sh`, `.gitignore` or `tools/`."

Cited, binding (Domain: Names): "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`."

`WORKFLOW_INSTALL_LAB` is no longer read. Do not reintroduce that identifier. Say the legacy install-lab setting is not read, without spelling the old name.

## Changes

- `tools/cloud-env/README.md` and the comment in `bootstrap-yakka-skills.sh`: drop the `WORKFLOW_INSTALL_LAB` spelling. Keep the fact that maintainer skills are not installed.
- `tools/driver/README.md`: examples use `YAKKA_INSTALL_MODE`, `YAKKA_INSTALL_SKIP_REFRESH`, and `.cursor/skills/yakka`. Rephrase the `workflow-plugin` CI sentence so it does not contain `workflow-plugin`.
- `tools/driver/report.py`: rename `WORKFLOW_REPORT_FENCE` to `REPORT_FENCE`. Leave `parse_workflow_report` and the dual-read fence strings. `tools/driver/` is already exempt for `workflow-report` lines.
- `tools/jev-variants/case2/pair.py`: replace the corpus slug `workflow-plugin` with `yakka`. Do not keep both spellings.
- `docs/lab/bootstrap/cursor-cloud-setup.sh`: exec `tools/cloud-env/bootstrap-yakka-skills.sh`. Comments use `YAKKA_WORKSPACE`, not `WORKFLOW_WORKSPACE`.
- `test_install_route.py`: remove the two `skipTest` guards that exist only while the wrapper still calls `bootstrap-workflow-skills.sh`.

### Keep untouched

Scan patterns, phase 5 scope, plugin manifests, `install.sh`, skills, and `CHANGELOG.md`.

## Done evidence

Before: `python3 tools/release/scan_residual_names.py --scope phase6` exits 1 and lists the hits in the 6-06 report.

After:

- `python3 tools/release/scan_residual_names.py --scope phase6` → exit 0, no output.
- `python3 tools/release/scan_residual_names.py --scope phase5` → exit 0, no output.
- `python3 -m unittest tools/release/test_scan_residual_names.py` → OK.
- `python3 -m unittest tools/driver/tests/test_install_route.py` → OK, and the two `test_cursor_setup_*` tests are not skipped.

## Report back

Under 1,500 tokens. Status, scan and unittest output before and after, deviations, and any contradiction with this brief.
