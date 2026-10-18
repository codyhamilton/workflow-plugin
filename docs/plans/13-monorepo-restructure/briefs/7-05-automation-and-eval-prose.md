# Brief: 7-05 — Automation post-build and eval fixture prose

Consumer: a phase 7 worker on the restructure branch after Phases 5 and 6 are closed.
Owned paths:
`docs/automation/post-build.md`,
`evals/scenarios/trailer-completeness/source.md`,
`docs/plans/13-monorepo-restructure/reports/7-05-automation-and-eval-prose.md` (new).
Touch nothing else. Do not edit `evals/scenarios/trailer-completeness/verify.py` or `reference/*`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-05-automation-and-eval-prose.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phases 5 and 6.
Runs alongside: `7-01`, `7-02`, `7-03`, `7-04`.
Budget: 8 files to read, about 60 lines to change, 30 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 Surfaces (`docs/automation/post-build.md`); Domain: Names repo URL; plugin name `yakka`.
2. `docs/automation/post-build.md` — full file.
3. `evals/scenarios/trailer-completeness/source.md` — Repo URL line.
4. `plugins/yakka/skills/post-build/SKILL.md` — skill name and `Yakka-*` protocol (for prompt alignment only).

## Goal

Automation and eval scenario prose name the `yakka` plugin install layout and repo URL without forbidden residual literals.

## Contract

Cited, binding (Domain: Names): "Repo URL `https://github.com/codyhamilton/yakka` everywhere a repo URL appears."

Cited, binding (Phase 6 / install): Cursor project skills under `.cursor/skills/yakka/`; plugin `yakka` at `plugins/yakka`.

Cited, binding (residual scan, `5-05` brief **Contract**): forbidden patterns include `\bworkflow-(plugin|…)\b` and `\.cursor/(plugins/local|skills)/workflow\b`. `evals/scenarios/trailer-completeness/` has trailer-pattern exceptions only for `Workflow-Phase` / `workflow-report` lines, not for `workflow-plugin` URLs.

## Changes

- `post-build.md`: replace "workflow plugin" product references with `yakka` where they mean this marketplace plugin; skills path `.cursor/skills/yakka/`; load `post-build` skill from `plugins/yakka`; canonical prompt may still say "post-build workflow" only if it means the method, not the plugin name.
- `source.md`: Repo URL → `https://github.com/codyhamilton/yakka`. Keep task text that exercises both `Workflow-Phase` and `Yakka-Phase` keys (trailer-exception paths).

### Keep untouched

`verify.py`, `reference/`, and `baseline/` fixtures. Do not change eval behaviour.

## Done evidence

Before: `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^(docs/automation/post-build|evals/scenarios/trailer-completeness/source)'` → non-zero.

After:

- Same command → no output.
- `rg 'github.com/codyhamilton/yakka' evals/scenarios/trailer-completeness/source.md` → match on Repo URL line.
- `rg '\.cursor/skills/yakka' docs/automation/post-build.md` → at least one match.

## Report back

Under 1,500 tokens. Status, scan before/after, deviations, contradictions.
