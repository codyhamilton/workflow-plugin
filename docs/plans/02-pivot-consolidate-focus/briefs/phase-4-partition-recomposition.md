# Brief: Phase 4 — Partition and re-composition

Consumer: the implementation worker for Phase 4. Runs **after** Phases 1–3 have revised `skills/plan/`, `skills/execute/`, and `skills/comprehensive-review/` — read the revised versions, not your memory of the old ones. Owned paths: everything Phases 1–3 did not own — manifests (`.claude-plugin/`, `.cursor-plugin/`), `install.sh`, `skills/iterate/**`, `skills/setup/**`, `skills/transcript-parser/**`, `skills/workflow-tuning/**`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `README.md`. Do not edit `skills/plan/`, `skills/execute/`, or `skills/comprehensive-review/`. Do not run git commit or push — leave changes in the working tree.

## Required reading, in order

1. `docs/plans/02-pivot-consolidate-focus/PLAN.md` — the model (binding)
2. `docs/plans/02-pivot-consolidate-focus/DESIGN.md` — binding contracts, especially "Plugin Partition"
3. The **revised** `skills/plan/SKILL.md`, `skills/execute/SKILL.md`, `skills/comprehensive-review/SKILL.md` (Phases 1–3 output)
4. `skills/iterate/SKILL.md`, `skills/setup/SKILL.md`, `skills/transcript-parser/SKILL.md`, `skills/workflow-tuning/SKILL.md`
5. `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `install.sh`, `README.md`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`

## Goal

Split the plugin into a cloud-safe core and a local lab; re-compose the lab skills over the revised core; update the stable docs and README to the new model.

## Changes

### Plugin partition

- **Core** (`workflow`): plan, execute, comprehensive-review. **Lab** (`workflow-lab`): setup, iterate, transcript-parser, workflow-tuning.
- Restructure so each plugin's source directory contains only its own skills, and `marketplace.json` lists both plugins. Choose the minimal-churn layout that makes this true (e.g. `plugins/workflow/` and `plugins/workflow-lab/` each with their own `.claude-plugin/plugin.json` and `skills/`, with marketplace `source` fields pointing at them) — the binding requirement is behavioral: installing core yields exactly the three core skills; installing lab yields exactly the four lab skills.
- Update `install.sh` and the `.cursor-plugin` manifest for the new layout. Keep the installer's no-flags/ask-first behavior.
- Bump plugin versions (this is a breaking change — see README below).

### iterate re-composition

- iterate composes plan, execute, and comprehensive-review — verify every reference to those skills' behavior still holds against the revised versions and fix the ones that don't. Known drift points: it references `[NEW]-<goal>` parent program folders (dead convention — its per-goal folder should follow the plain `docs/plans/<NN>-<slug>/` convention with `iteration-NN/` subfolders as today); it relies on execute's mandatory review (now posture-parameterized — iterate's candidates should declare terminal posture so per-candidate review still runs); it dispatches plan subagents (they should declare headless posture explicitly — iterate's gates, not plan's checkpoint, own its user interaction).
- Move the "Reasoning" section of `skills/iterate/SKILL.md` to `skills/iterate/reference.md` (consumers: workflow-tuning and skill revisers; not loaded during normal execution — say so at its top). Workflow, Model allocation, Artifacts, and Invariants stay. Where an invariant leans on reasoning that moved, keep a one-line orienting version inline.
- Leave `skills/iterate/briefs/` untouched — the briefs pattern is now plugin-wide doctrine and iterate's briefs are already correct.

### setup slim

- setup stops creating `docs/ROADMAP.md` as a canonical schedule (the backlog is dead; PRs and trackers carry status). It bootstraps `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` only. Preserve the anti-scope-creep value of the old "Not In Scope" section by folding an optional "Not in scope / non-goals" note into OVERVIEW or ARCHITECTURE.
- Remove the ROADMAP phase content and references; keep the permission gate, one-question-per-round conversation, and consolidation behavior. Update the Phase 6 hook text to match reality.

### transcript-parser

- Move the inline Python extraction script from SKILL.md into `skills/transcript-parser/scripts/parse_session.py` (skill bodies carry instructions, not code payloads). SKILL.md tells the agent to run the script and describes inputs/outputs; keep the per-harness path formulas as short reference material in the skill or a reference.md, whichever reads cleaner.

### workflow-tuning

- Add the pipeline-outcomes harvest: executed plan folders on merged PRs — REVIEW.md (including plan-sufficiency judgments), QA.md, remediation briefs — are an eval corpus the skill consumes alongside retros. One short subsection; do not restructure the skill.
- Update its references to plan/execute behavior that Phases 1–3 changed (e.g. STATUS.md no longer exists; ROADMAP no longer canonical).

### Stable docs and README

- `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md`: update to the new model — seven skills across two plugins, the artifact taxonomy (durable intent/outcome, run-scoped briefs, nothing carries status), the briefs invariant, the PR artifact seam, postures, and the revised cross-skill contracts. Fix stale invariants (e.g. invariant 3's ROADMAP references, the four-skill framing).
- `README.md`: update the skills table and structure section for the two plugins and install instructions; add a prominent **breaking-change callout**: the folder-status taxonomy (`[NEW]-` prefixes, renumbering, ROADMAP-as-schedule) is removed — repos that adopted the old convention via this plugin get no automated migration; existing numbered folders remain valid as historical provenance. Do not touch the "Operating hypotheses" / "Variants worth testing" sections beyond making surrounding content consistent.

## Done evidence

- `marketplace.json` lists two plugins; each plugin source contains only its own skills; `install.sh` works against the new layout (dry-read the script logic — no need to run installs).
- `grep -rn "\[NEW\]\|ROADMAP" skills/iterate/ skills/setup/ skills/workflow-tuning/` returns only intentional survivals (e.g. historical mentions in reference files), each of which you can defend.
- `skills/iterate/reference.md` exists; iterate's SKILL.md has no "Reasoning" section but its Workflow/Invariants still stand alone coherently.
- transcript-parser's SKILL.md contains no inline multi-line Python; the script exists under `scripts/`.
- README has the breaking-change callout and accurate install/structure sections; stable docs describe the new model without referencing dead conventions.

## Report back

A short summary: the layout you chose for the partition and why, what you changed in each lab skill, any deviation from this brief, and any contradiction you found between this brief, the revised core skills, and the DESIGN.md contracts (report, don't silently resolve).
