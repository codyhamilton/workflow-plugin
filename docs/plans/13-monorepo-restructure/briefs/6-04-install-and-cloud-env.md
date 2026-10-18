# Brief: 6-04 — Install routes and cloud bootstrap

Consumer: a phase 6 worker on the monorepo-restructure branch.
Owned paths:
`install.sh`,
`.gitignore`,
`tools/cloud-env/**`,
`docs/plans/13-monorepo-restructure/reports/6-04-install-and-cloud-env.md` (new).
Touch nothing else. Do not edit `tools/driver/**` except you may not; `6-03` owns driver tests after this unit lands.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-04-install-and-cloud-env.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 5 closed. Prefer after `6-01` so default clone URL and plugin name align with `yakka` (may run alongside `6-01` if you only touch install paths and env names).
Runs alongside: `6-01`, `6-02`, `6-05`.
Budget: 15 files to read, about 250 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcome [test] for `install.sh` and bootstrap; Domain: Names (state paths, repo URL, install paths, bootstrap script name).
2. `install.sh` — Cursor local path, cloud/workspace skills name, env vars.
3. `tools/cloud-env/bootstrap-workflow-skills.sh` and `tools/cloud-env/README.md`.

## Goal

Every install mode and the cloud bootstrap script install core skills/plugin material under `yakka`-named paths, using `YAKKA_*` install env vars and `plugins/yakka` for Cursor.

## Contract

Cited, binding (Phase 6 outcome): "[test] `install.sh` in each mode, and `tools/cloud-env/bootstrap-yakka-skills.sh`, install into the `yakka`-named locations, with Cursor installing `plugins/yakka`."

Cited, binding (Domain: Names): "`install.sh` installs Cursor to `~/.cursor/plugins/local/yakka` from `plugins/yakka`." "The bootstrap script is `tools/cloud-env/bootstrap-yakka-skills.sh`." "Repo URL `https://github.com/codyhamilton/yakka` everywhere a repo URL appears." "`WORKFLOW_*` becomes `YAKKA_*` with the same suffix, except `WORKFLOW_QUALITY_`."

Cited, binding (Domain: Names, paths table): "`~/.cache/workflow-plugin` (cloud-env checkout)" → "`~/.cache/yakka/src`"; `.gitignore` change "`.cursor/skills/workflow/` → `.cursor/skills/yakka/`"."

Cited, binding (Domain: Plugin): "`install.sh` (every mode) and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only." (script filename updates to `bootstrap-yakka-skills.sh` per Names domain.)

Settled: Assumption 5 kept the old bootstrap URL for deployed environments; Phase 6 is the hard-break cut. No forwarding stub at the old URL (Names domain). Phase 7 CHANGELOG documents maintainer URL updates; do not write the migration entry here.

Settled: `WORKFLOW_INSTALL_LAB=1` remains accepted and ignored (Phase 1). `6-03` updates `tools/driver/tests/test_install_route.py` expectations after this unit; do not edit driver tests here.

Settled: Phase 3 Carried item 1 is not this unit.

## Changes

- Rename `tools/cloud-env/bootstrap-workflow-skills.sh` → `tools/cloud-env/bootstrap-yakka-skills.sh` (`git mv`). Update `tools/cloud-env/README.md` examples to the new filename and `yakka` paths/URLs.
- `install.sh`: default repo URL `https://github.com/codyhamilton/yakka`; Cursor plugin dir `~/.cursor/plugins/local/yakka`; workspace skills dir `.cursor/skills/yakka/`; install src cache `~/.cache/yakka/src` (or equivalent per Names table); rename install env vars `WORKFLOW_*` → `YAKKA_*` (same suffixes, no `WORKFLOW_QUALITY_` here). Keep materializing `plugins/yakka` for Cursor local install.
- `.gitignore`: track comment and path `.cursor/skills/yakka/` instead of `workflow/`.

### Keep untouched

`tools/driver/**`, plugin `skills/`, `CHANGELOG.md`, and `packages/**`. Do not change hook or binary behaviour.

## Done evidence

Before:

- `python3 -m unittest tools/driver/tests/test_install_route.py` → fails on path/env expectations (record failing assertion).

After (driver tests may still fail until `6-03`; this unit's owned checks must pass):

- `bash -n install.sh` and `bash -n tools/cloud-env/bootstrap-yakka-skills.sh` → exit 0.
- `WORKFLOW_INSTALL_SKIP_REFRESH=1 WORKFLOW_INSTALL_LAB=1` dry run: invoke `install.sh --print-route` paths documented in install.sh still execute; with `YAKKA_*` names after rename, document the equivalent `YAKKA_INSTALL_SKIP_REFRESH=1` probe in the report.
- Observable: `test -f tools/cloud-env/bootstrap-yakka-skills.sh && test ! -f tools/cloud-env/bootstrap-workflow-skills.sh` → exit 0.
- `rg '\\.cursor/skills/workflow' install.sh .gitignore tools/cloud-env` → no hits.

## Report back

Under 1,500 tokens. Status, `bash -n` and rg before/after, note install-route unittest status if still waiting on `6-03`.
