# Brief: 6-02 — Core skills protocol and `yakka-tuning`

Consumer: a phase 6 worker on the monorepo-restructure branch.
Owned paths:
`plugins/yakka/skills/**`,
`.claude/skills/workflow-tuning/` → rename to `.claude/skills/yakka-tuning/` (git mv the directory),
`.claude/skills/setup/SKILL.md`,
`.claude/skills/transcript-parser/SKILL.md`,
`docs/plans/13-monorepo-restructure/reports/6-02-skills-and-tuning-rename.md` (new).
Touch nothing else. Do not edit plugin manifests (`6-01`), `tools/driver/check_skills.py` (`6-03`), or `CHANGELOG.md`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-02-skills-and-tuning-rename.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 5 closed.
Runs alongside: `6-01`, `6-04`, `6-05`.
Budget: 25 files to read, about 200 lines to change, 55 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcome [judgement]; Domain: Names (writers/readers, fences, skill-prefix note lives in Phase 7 CHANGELOG — still rename slash-invocation examples in maintainer skills when they use forbidden `workflow:` skill ids).
2. `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md` — residual-name **Contract** (patterns unchanged).
3. `plugins/yakka/skills/execute/SKILL.md`, `design/SKILL.md`, `post-build/SKILL.md`, `comprehensive-review/SKILL.md`.

## Goal

Shipped core skills tell agents to emit `Yakka-*` trailers and the `yakka-report` fence; skills that read plan markers document legacy `Workflow-*` / `workflow-report` in one sentence. The maintainer skill is `yakka-tuning`, not `workflow-tuning`.

## Contract

Cited, binding (Phase 6 outcome): "[judgement] Each reading skill writes the `Yakka-*` forms and names the legacy forms it accepts in one sentence."

Cited, binding (Domain: Names): "Writers emit `Yakka-Phase: <slug>:<n>`, `Yakka-Phase: <slug>:done`, a PR body starting `Yakka-Plan: docs/plans/<NN>-<slug>/`, and a `yakka-report` fence. Readers accept `Workflow-Phase` / `Yakka-Phase`, `Workflow-Plan:` / `Yakka-Plan:`, and both fences, permanently, through one shared key list in `tools/driver/`."

Cited, binding (Domain: Maintainer skills): "The existing `name:` frontmatter works unchanged." After directory rename, set `name: yakka-tuning` in the maintainer skill frontmatter.

Cited, binding (residual scan, unchanged patterns): `\bworkflow:(design|refine|execute|close-out|comprehensive-review|post-build|plan|setup)\b` and `\bworkflow-tuning\b` are forbidden outside allowed exceptions.

Settled: `6-03` updates `tools/driver/check_skills.py` `MAINTAINER_SKILLS` to `yakka-tuning`. This unit renames the directory and fixes prose references (`comprehensive-review`, other `.claude/skills/` files).

Settled: Phase 3 Carried item 1 is not this unit.

## Changes

- **`plugins/yakka/skills/`** — In every skill that specifies phase trailers, plan markers, or the execute report fence, make **writers** use `Yakka-Phase:`, `Yakka-Plan:`, and a fenced block tagged `yakka-report`. Skills that **read** markers (`comprehensive-review`, `post-build`, and any execute prose that still describes resolution) add exactly one sentence naming the legacy forms (`Workflow-Phase`, `Workflow-Plan`, `workflow-report`) as accepted when present in git history or old agent output.
- **`.claude/skills/workflow-tuning/`** — `git mv` to `.claude/skills/yakka-tuning/`. Update `name:` to `yakka-tuning`. Fix internal paths and titles that still say `workflow-tuning`.
- **`.claude/skills/setup/SKILL.md`** — Replace slash-command examples `workflow:…` with `yakka:…` for the six core skills (forbidden pattern).
- **`.claude/skills/transcript-parser/SKILL.md`** — Remove or reword `workflow-plugin` product path literals that trip the residual scan (`workflow-plugin` suffix pattern); keep repo-relative `tools/transcript/` commands.

### Keep untouched

Plugin manifests, `tools/driver/`, `install.sh`, and `refine/templates/brief.md` catalogue path (already `packages/yakka/catalogue/…` from Phase 5). Do not change skill behaviour beyond naming/protocol prose.

## Done evidence

Before edits, run a focused grep or the phase 6 scan stub (once `6-06` lands, use the committed command). Minimum before check:

- `rg 'Workflow-Phase|Workflow-Plan|workflow-report' plugins/yakka/skills/` → hits on writer lines that should become `Yakka-*` / `yakka-report`.

After:

- `rg 'workflow-tuning' plugins/yakka/skills .claude/skills` → no hits (use `yakka-tuning`).
- `rg 'workflow:(design|refine|execute)' .claude/skills/setup` → no hits.
- `test -d .claude/skills/yakka-tuning && test ! -e .claude/skills/workflow-tuning` → exit 0.
- Judgement self-check: each of `comprehensive-review`, `post-build`, and `execute` contains one legacy-acceptance sentence and writer forms use `Yakka-*` / `yakka-report` where they instruct agents to emit artifacts.

## Report back

Under 1,500 tokens. Status, grep/scan before and after, deviations.
