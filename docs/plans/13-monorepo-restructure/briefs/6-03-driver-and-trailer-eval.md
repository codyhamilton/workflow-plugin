# Brief: 6-03 — Driver dual-read and trailer-completeness eval

Consumer: a phase 6 worker on the monorepo-restructure branch.
Owned paths:
`tools/driver/**`,
`evals/scenarios/trailer-completeness/**`,
`docs/plans/13-monorepo-restructure/reports/6-03-driver-and-trailer-eval.md` (new).
Touch nothing else. Do not extend `tools/release/scan_residual_names.py` (`6-06`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-03-driver-and-trailer-eval.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `6-02` (maintainer skill `yakka-tuning`), `6-04` (`install.sh` / bootstrap paths and `YAKKA_*` install env names).
Runs alongside: nothing.
Budget: 45 files to read, about 400 lines to change, 90 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcomes [test] for driver and trailer-completeness eval; Domain: Names (dual-read rule, `YAKKA_*`, signal-log path).
2. `tools/driver/resolve.py`, `status.py`, `trigger.py`, `report.py`, `jev_signal_log.py`.
3. `evals/scenarios/trailer-completeness/verify.py` and `reference/expected.json`.
4. `docs/plans/13-monorepo-restructure/IMPLEMENTATION.md` — Phase 5 Carried item 3 (`jev_signal_log` vs OpenCode default).

## Goal

`tools/driver` reads both legacy and yakka git trailers and report fences through one shared key list; install-route tests match `6-04` paths; the trailer-completeness eval passes for each phase-trailer key.

## Contract

Cited, binding (Phase 6 outcome): "[test] `tools/driver` resolves a branch whose closing commits carry `Workflow-Phase: <slug>:1` and `Yakka-Phase: <slug>:2` to phase 3 through `resolve`, `status` and `trigger`, and `report.py` parses both fences."

Cited, binding (Phase 6 outcome): "[cmd] The trailer-completeness eval passes for each key."

Cited, binding (Domain: Names): "Readers accept `Workflow-Phase` / `Yakka-Phase`, `Workflow-Plan:` / `Yakka-Plan:`, and both fences, permanently, through one shared key list in `tools/driver/`."

Cited, binding (Domain: Names): "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`. No code reads the old env vars or the old state paths." (Apply under `tools/driver/`.)

Cited, binding (Assumption 11, state path): OpenCode and driver signal log default `${XDG_STATE_HOME:-~/.local/state}/yakka/jev-signal-log.jsonl`, overridable by `YAKKA_JEV_SIGNAL_LOG`. Phase 5 Carried item 3: bring `tools/driver/jev_signal_log.py` in line with `packages/opencode-yakka-hooks`.

Settled: `TRAILER_EXCEPTION_PREFIXES` in `scan_residual_names.py` keeps `tools/driver/` and `evals/scenarios/trailer-completeness/` allowed to mention legacy trailer strings in fixtures. Do not remove those exceptions in this unit.

Settled: Phase 3 Carried item 1 is not this unit. Do not require a logged-in Cursor session.

## Changes

- Add one shared module under `tools/driver/` (e.g. `trailer_keys.py`) exporting the canonical ordered list of git trailer **keys** (`Workflow-Phase`, `Yakka-Phase`, and plan keys if `resolve`/`status` need them) and report fence tags (`workflow-report`, `yakka-report`). `resolve.py`, `status.py`, `trigger.py`, and `git_trailer_lines` merge values from every key on the list (same value grammar: `<slug>:<n>`, `<slug>:done`).
- `report.py`: parse either fence; tests cover both.
- Rename driver env vars and defaults: `WORKFLOW_*` → `YAKKA_*` (except `WORKFLOW_QUALITY_` if present). Update `check_skills.py`: `WORKSPACE_SKILLS_NAME` default `yakka`, `MAINTAINER_SKILLS` includes `yakka-tuning` not `workflow-tuning`, Cursor path `.cursor/skills/yakka/`, bootstrap path `tools/cloud-env/bootstrap-yakka-skills.sh`, cache `~/.cache/yakka/src`, plugin `~/.cursor/plugins/local/yakka`.
- `jev_signal_log.py`: `YAKKA_JEV_SIGNAL_LOG` and default `~/.local/state/yakka/jev-signal-log.jsonl`.
- Tests: add a resolve/status case with two commits on a fixture branch, trailers `Workflow-Phase: demo:1` and `Yakka-Phase: demo:2`, three phases in DESIGN → open phase 3. Extend `trigger.py`/`run.py` skip messages to mention either key where they today say only `Workflow-Phase`.
- `evals/scenarios/trailer-completeness/verify.py`: parameterize the git trailer key. Run the full check sequence once per key in the shared list (at minimum `Workflow-Phase` and `Yakka-Phase`). `reference/expected.json` may gain a per-key variant or the verifier loops keys with the same commit values. Exit 0 only when every key passes checks 1–4 from `source.md`.
- Update `evals/scenarios/trailer-completeness/source.md` task text to name both keys without removing the Workflow-Phase example.

### Keep untouched

`tools/release/scan_residual_names.py`, `install.sh` (already updated in `6-04`), plugin manifests, and `CHANGELOG.md`. `tools/quality/` keeps `WORKFLOW_QUALITY_*`.

## Done evidence

Before:

- `python3 -m unittest tools/driver/tests/test_jev_signal_log.py` → default path still under `workflow/` (record output).
- `python3 evals/scenarios/trailer-completeness/verify.py` → pass on `Workflow-Phase` only (baseline).

After:

- `python3 -m unittest discover -s tools/driver/tests -p 'test_*.py'` → OK.
- `python3 evals/scenarios/trailer-completeness/verify.py` → exit 0; stdout documents each trailer key exercised.
- New or extended unittest: branch with `Workflow-Phase: t:1` then `Yakka-Phase: t:2` → `status.py` / `resolve` open phase 3.
- `python3 -c` importing `report.parse_report` on fixture text with `yakka-report` and `workflow-report` fences → both succeed.

## Report back

Under 1,500 tokens. Status, unittest and verify.py output before/after, deviations.
