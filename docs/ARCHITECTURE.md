# Workflow Plugin — Architecture

## Component Map

```
workflow-plugin/ (repo root — the `workflow` core plugin)
├── .claude-plugin/
│   ├── plugin.json            → core plugin manifest (name: workflow)
│   └── marketplace.json       → lists both plugins: workflow (source "./"), workflow-lab
├── .cursor-plugin/plugin.json → core plugin manifest for Cursor
├── skills/                    → core: cloud-safe, no interactive dead-ends
│   ├── plan/              → PLAN.md (+ DESIGN.md when warranted); owns intent + provenance capture
│   ├── execute/            → executes a plan; brief-based dispatch; progressive IMPLEMENTATION.md
│   ├── comprehensive-review/  → independent review keyed to PLAN.md's acceptance criteria
│   └── post-build/         → the pipeline stage: classify/right-size, review, remediation, checks wait, conditional QA/deploy proof
├── plugins/workflow-lab/      → lab: local and/or interactive; never required by the pipeline
│   ├── .claude-plugin/plugin.json
│   ├── .cursor-plugin/plugin.json
│   └── skills/
│       ├── setup/              → bootstraps docs/OVERVIEW.md + docs/ARCHITECTURE.md
│       ├── iterate/             → divergent-candidate exploration; composes plan/execute/comprehensive-review
│       ├── transcript-parser/   → session transcript → cost metrics
│       └── workflow-tuning/     → meta-skill: lessons corpus, evals, pipeline-outcomes harvest
├── docs/
│   ├── OVERVIEW.md        → this repo's overview (read first by plan)
│   ├── ARCHITECTURE.md    → this repo's architecture (this file)
│   └── plans/             → PLAN.md artifacts when dogfooding this plugin on itself
└── evals/
    ├── scenarios/         → fixture corpus for skill-prompt testing
    └── results/           → eval run results and comparison tables
```

Each plugin's source directory contains only its own skills: `skills/` at the repo root is core-only; `plugins/workflow-lab/skills/` is lab-only. `install.sh` and `marketplace.json` both key off this split.

## Skill Responsibilities

**plan** (core): captures intent and produces durable plan artifacts.
- Reads the target repo's stable docs (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/design/`); never hard-depends on `setup` having run.
- Writes `PLAN.md`'s Intent section verbatim, first, in every posture.
- Interactive posture: asks scope-shaping questions, records Q&A in `PROVENANCE.md`, holds the checkpoint before execution starts.
- Headless posture (declared by the invoker): records an honest assumption ledger in `PLAN.md` instead of asking; waves the checkpoint through; downstream review challenges the ledger.
- Runs one adversarial Challenge pass before finalizing.
- Does NOT implement; stops and returns to plan if architectural misalignment is detected.
- No folder-status taxonomy: one plan folder per change/PR at `docs/plans/<NN>-<slug>/`, slug is the unique key.

**execute** (core): orchestrates implementation of an existing plan.
- Confirms the plan is the right next slice and its contracts are explicit enough to delegate against.
- Sizes work via a recon-first ladder; delegation is a judgment call (harness capability, context economics), not a mandate.
- Dispatches workers with authored briefs (derived from `PLAN.md`/`DESIGN.md` at dispatch time, committed to `briefs/`) — never an orchestrator paraphrase.
- Writes `IMPLEMENTATION.md` progressively, starting with run identity, before implementation begins — a killed run must be resumable from this file alone.
- Runs review sized to the declared posture: **terminal** (mandatory independent review via `comprehensive-review`, writes `REVIEW.md`) or **pipeline** (pre-flight self-verification only; `REVIEW.md` is owned by the downstream pipeline stage).
- Lands a PR whose body's first line is the `Workflow-Plan:` marker. No status artifact exists to update — there is no `STATUS.md`.

**comprehensive-review** (core): independent review keyed to the plan's acceptance criteria.
- Locates the plan folder via the PR's `Workflow-Plan:` marker (or a direct local invocation); for functional/material no-plan PRs, falls back to reconstructing intent into `RECOVERED-INTENT.md`; trivial non-functional work may skip ceremony when the invoker classifies it as absorbable.
- Assesses each `PLAN.md` acceptance criterion explicitly (met/partial/not met); applies an intent-and-assumptions lens that challenges the headless posture's assumption ledger.
- Writes `REVIEW.md` (findings by severity, plan-sufficiency judgment) and a remediation brief per structural finding, into the plan folder.
- Never invokes or depends on `workflow-tuning` (lab) — the plan-sufficiency judgment is a one-way artifact `workflow-tuning` harvests later, not a call.

**post-build** (core): orchestrates the pipeline stage against a PR — the stage execute's pipeline posture declares.
- Resolves plan context: `Workflow-Plan:` marker first, then a bounded diff-based fallback (never tie-broken by number or recency), then tiered no-plan handling (ad-hoc for trivial non-functional; `RECOVERED-INTENT.md` for functional/material).
- Classifies the change (intent source × surface × size) and right-sizes: orchestrator may absorb trivial/small non-functional work; functional work gets independent review.
- Dispatches `comprehensive-review` when review is needed, then bounded finding-scoped remediation (briefs routed verbatim) and one fresh re-review; stops while any `blocker`/`high` finding stands.
- Waits reactively for adapter-named required checks on the candidate SHA before merge-readiness (and before any QA-driven deploy).
- Derives `QA.md` (matrix only, committed before the candidate SHA) and runs exact-SHA deploy proof + deployed browser QA **only when** the surface is functional/mixed with driveable user-facing need; otherwise records an explicit skip.
- Reports merge-readiness and stops — it never merges.
- Repo-specific mechanics (production boundaries, required checks, deploy-proof commands, QA credentials/environment, worker routing) come from a per-repo **adapter skill**; garcia-music's `post-build-automation` is the reference adapter.

**setup** (lab): bootstraps missing stable docs.
- Reconnaissance → permission gate → optional consolidation of partial/legacy docs → one-question-per-round guided conversation (capped at 3 rounds) → writes docs.
- Writes `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` only. Does not create `docs/ROADMAP.md` — no canonical schedule doc; folds an optional Non-Goals note into `docs/ARCHITECTURE.md` instead.
- Does NOT plan or execute; hooks into `plan` afterward.

**iterate** (lab): drives long-horizon work with no fixed spec.
- Composes `plan`, `execute`, and `comprehensive-review` rather than reimplementing them; the orchestrator delegates every substantive step and never decides on its own.
- Sequential divergent candidates (never parallel) built via `plan`+`execute`, each seeing prior builds as a working spec; a clean approver gates challengers on a divergence bar.
- Cross-candidate synthesis revises `OUTCOMES.md`, selects a foundation, and harvests ideas — one delegated read, then stops.
- Consolidation captures (additive), then a bounded sequential harden relay verifies and locks the base, using `comprehensive-review` against a deliverable bar.
- Declares posture explicitly on every `plan`/`execute` dispatch (headless for `plan`; terminal or pipeline for `execute`, depending on whether harden is the downstream review stage) — iterate's own gates, not a composed skill's checkpoint, own user interaction.
- Its own plan folder follows the same plain `docs/plans/<NN>-<slug>/` convention as everything else, with `iteration-NN/` subfolders per cycle; each candidate's own `plan`/`execute` artifacts live on its own branch.

**transcript-parser** (lab): extracts cost metrics from a session transcript.
- Locates the transcript by harness (opencode/Claude Code, Cursor, GitHub Copilot) using per-harness path formulas.
- Runs `scripts/parse_session.py` for opencode/Claude Code (covers parent + subagents in one pass); applies the Cursor/Copilot formulas by hand.
- Outputs a `cost-comparison.md`-schema section; marks unavailable fields explicitly rather than estimating.

**workflow-tuning** (lab): improves the workflow itself; never executes target work.
- Holds a numbered lessons corpus (`reference.md`) and a retro staging area (`retros/`), consumed and folded in, then deleted.
- Harvests merged PRs' pipeline outcomes (`REVIEW.md` incl. plan-sufficiency judgments, `QA.md`, remediation briefs) as a second eval corpus, alongside retros — a one-way read; it never calls `comprehensive-review`.
- Runs full end-to-end evals (`plan` + `execute` on a fixture scenario) comparing a candidate skill change to a baseline and a known reference implementation.
- `disable-model-invocation: true` — user-invoked only, never auto-triggered.

## Cross-Skill Contracts

**plan → execute**: `plan` produces durable `PLAN.md` (+ `DESIGN.md` when used) with explicit scope, contracts, and QA-drivable acceptance criteria. `execute` reads these cold from committed artifacts — even immediately after a plan run in the same session — never from orchestrator memory of the planning conversation (composition is dispatch, not inlining; the cold read is load-bearing). `execute` stops and returns to plan if alignment breaks.

**execute → comprehensive-review**: mandatory when execute runs in **terminal** posture (the default, absent a declaration); dropped to pre-flight self-verification in **pipeline** posture, where a downstream orchestrated review stage is declared to exist. Posture is always declared by the invoker, never inferred.

**execute → post-build**: `execute`'s pipeline posture exists because `post-build` (or an equivalent automation) picks the PR up. The handoff is the PR itself: branch, commits, and the `Workflow-Plan:` marker. No live call in either direction.

**post-build → comprehensive-review**: `post-build` classifies the change, then dispatches `comprehensive-review` when independent review is needed (not on the absorb path for trivial/small non-functional work). It branches on `REVIEW.md`'s verdict (`PASS` / `PASS_WITH_FOLLOWUPS` / `REMEDIATE`), routing remediation briefs verbatim to fixers. Review locates the plan folder via the PR body's `Workflow-Plan:` marker (or recovered-intent folder) and writes `REVIEW.md` plus remediation briefs back into that folder on the PR branch. See PR Artifact Seam below.

**post-build ↔ repo adapter (external)**: the adapter supplies production boundaries, required checks, deploy-proof mechanics, QA environment, and worker routing; `post-build` supplies the portable stage semantics. Authority on conflict: repo hard limits → adapter → `post-build` → triggering prompt.

**setup → plan**: `setup` creates `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md`; `plan` reads those docs at its Ground phase. No code coupling — the dependency is filesystem presence, and `plan` never hard-blocks on their absence.

**iterate → plan/execute/comprehensive-review**: `iterate` (lab) composes all three core skills as dispatched subagents, passing drift-sensitive context verbatim from its own `briefs/`. Lab skills may compose core skills; core skills never depend on lab skills.

**comprehensive-review → workflow-tuning**: one-way, artifact-only. `comprehensive-review` writes `REVIEW.md`'s plan-sufficiency judgment as part of its normal output; `workflow-tuning` reads it later, across many merged PRs, as eval-corpus input. `comprehensive-review` never invokes or waits on `workflow-tuning`.

## PR Artifact Seam

The contract an external cursor/pipeline automation codes against, so it can locate and extend a build's plan folder mechanically:

- **Location**: `docs/plans/<NN>-<slug>/` on the PR branch when a plan folder exists. `NN` is best-effort ordering only; the slug is the unique key. The PR body's first line, `Workflow-Plan: docs/plans/<NN>-<slug>/`, is the only mechanical location mechanism — nothing scans or sorts folders by number. Ad-hoc trivial non-functional PRs may have no plan folder.
- **Build-stage contents** (owned by plan + execute, written before PR creation): `PLAN.md` (required), `DESIGN.md` (when contracts need reification), `IMPLEMENTATION.md` (required, written progressively), `briefs/` (committed dispatch briefs).
- **Pipeline-stage contents** (owned by `post-build`, committed back to the PR branch **before the candidate SHA** when those phases run): `REVIEW.md` (verdict + findings keyed to `PLAN.md`'s acceptance criteria, accumulating across remediation), `QA.md` (matrix only — one case per user-facing criterion with stable ID, entry point → action → expected result, evidence requirements; undriveable criteria listed with reason; no pre-execution pass/fail; **omitted when QA is not applicable**), `briefs/remediation-<NN>.md`.
- **External-only outputs**: classification, check-wait outcomes, final SHA-specific QA results and media go to the PR conversation or automation output, never a trailing commit — a commit added after testing changes the SHA, and the merged commit must be the tested commit. Classification is report control state, not a new durable status file.
- **Fallback**: a PR with no plan folder does not break the pipeline — functional/material changes reconstruct intent into `RECOVERED-INTENT.md` and proceed; trivial/small non-functional changes may be absorbed without inventing plan ceremony.

## Artifact Taxonomy

- **Durable — intent and outcome**: `PLAN.md`, `DESIGN.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`. Survive the merge; the provenance record.
- **Run-scoped — coordination**: briefs (`briefs/` in the plan folder, or a skill's own `briefs/` for drift-sensitive internal context like iterate's). Committed for provenance and debugging; no future agent is required to read them.
- **Skill-scoped — design record**: `reference.md` beside a `SKILL.md`. Holds persuading-why relocated out of the skill body. Consumers: `workflow-tuning` and anyone revising the skill. Not loaded during normal execution.
- **Status**: carried by nothing in the repo. PRs, branches, and the tracker carry status. Deferred work becomes a design-intent doc (`docs/design/`) or a tracker issue — never a stale plan folder, never a `ROADMAP.md`.

## Postures

- **plan**: interactive (default) or headless, declared by the invoker (skill argument or explicit statement in the dispatching prompt). Never inferred from TTY or environment. Absent a declaration, assume a human is reachable and hold the checkpoint.
- **execute's review**: terminal (default) or pipeline, declared the same way. One-shot cloud composition still runs plan and execute as separately dispatched contexts, handed off through the plan folder's committed artifacts.

## Key Invariants

1. User intent is always captured verbatim in `PLAN.md`'s `## Intent` section, never paraphrased.
2. Coordination between agents travels as authored briefs, routed verbatim by orchestrators — never as paraphrase. This is a plugin-wide invariant, not specific to any one skill.
3. Nothing in the repo carries status. A plan folder existing on a branch means the work is being built or was built — nothing else; there is no `ROADMAP.md`, no `STATUS.md`, no folder-status taxonomy.
4. Execute's independent review is mandatory in terminal posture (the default); pipeline posture substitutes pre-flight self-verification because a downstream review stage is declared to exist — never silent, always one or the other.
5. Plans are never implementation specs; they are intent, scope, implications, and QA-drivable acceptance criteria.
6. `DESIGN.md` is optional, only when it reifies contracts or target shape not cheaply inferable from code and stable docs.
7. Core skills (`plan`, `execute`, `comprehensive-review`) never depend on lab skills. Lab skills may compose core skills. Data may flow lab-ward only as artifacts already written for another consumer (e.g. `workflow-tuning` harvesting `REVIEW.md`), never as a live call.
8. `workflow-tuning` never auto-runs; user-invoked meta-skill only (`disable-model-invocation: true`).
9. Deployed QA runs only when classification says it is applicable (functional/mixed with driveable user-facing need), only against a deployment proven to match the exact candidate SHA on a non-production target, and its results are never committed after testing. Required checks are waited for reactively before merge-readiness. `post-build` reports merge-readiness; nothing in this plugin merges.

## Data Flows

**Planning session** (either posture):
1. User or dispatcher → `plan` skill, with posture declared (or defaulted to interactive).
2. `plan` reads stable docs, captures intent verbatim first, resolves scope-shaping decisions (Q&A in `PROVENANCE.md`, or ledger entries in `PLAN.md`), runs an adversarial Challenge pass.
3. Interactive: `plan` → user: "Here is the plan and the ledger, if any; shall I proceed?" (held checkpoint). Headless: checkpoint waved through; the plan folder is the handoff.

**Execution session**:
1. Dispatcher → `execute` skill, with review posture declared (or defaulted to terminal).
2. `execute` reads `PLAN.md`/`DESIGN.md` cold, sizes the slice, dispatches workers with committed briefs, writes `IMPLEMENTATION.md` progressively.
3. `execute` runs review per posture: terminal → `comprehensive-review` → `REVIEW.md` in the plan folder; pipeline → pre-flight self-verification recorded in `IMPLEMENTATION.md`.
4. `execute` pushes commits and opens/updates the PR with the `Workflow-Plan:` marker as the first body line.

**Post-build session** (against a PR; triggered by an automation, an operator, or the user):
1. Trigger → `post-build`, alongside the repo's adapter skill. Preflight + plan discovery (marker → diff fallback → tiered no-plan) + change classification (intent source × surface × size).
2. Absorb path (trivial/small non-functional): light skim, wait for required checks, report. Otherwise dispatch `comprehensive-review`: acceptance-criteria assessment, lenses (always including intent-and-assumptions), `REVIEW.md` with verdict, remediation briefs, plan-sufficiency judgment.
3. On `REMEDIATE`: finding-scoped fixers consume the remediation briefs untranslated; one fresh re-review updates the verdict.
4. Wait for required checks on the candidate SHA. When QA applies: commit `QA.md` (matrix), prove the exact-SHA deployment via adapter mechanics, run deployed browser QA. When QA does not apply: record the skip. Emit the merge-readiness report externally. Merging stays with the human or a separate automation.

**Setup session**:
1. User → `setup` skill.
2. `setup` reads existing docs, asks permission, conducts a capped guided conversation.
3. `setup` writes `docs/OVERVIEW.md` + `docs/ARCHITECTURE.md` (folding any Non-Goals content in, no `ROADMAP.md`).
4. `setup` → user: "Docs are in place; run `/workflow:plan`."

**Iterate session** (lab, composing core):
1. User → `iterate` skill with a broad goal and loop-control choice.
2. `iterate` dispatches research, then `plan` (headless) + `execute` (terminal) for candidate 1, then gated challengers, then synthesis (gated selection), then consolidation `plan` (headless) + `execute` (pipeline), then a harden relay via `comprehensive-review` (deliverable bar), then extrapolation (gated next-step selection).
3. `iterate` → user at each gate; the hardened commit becomes the next cycle's base.

**Eval / tuning session** (meta):
1. User → `workflow-tuning` skill.
2. `workflow-tuning` runs a scenario through the real `plan` + `execute` skills, captures cost metrics via `transcript-parser`, and compares to baseline/reference.
3. Separately, `workflow-tuning` harvests retros and merged PRs' `REVIEW.md`/`QA.md`/remediation briefs, folding lessons into `reference.md` and, where warranted, into the skills themselves.

## Stable References

- [OVERVIEW.md](OVERVIEW.md) — what the plugin is and why
- [../README.md](../README.md) — install instructions, skills table, operating hypotheses
- [../skills/plan/SKILL.md](../skills/plan/SKILL.md), [../skills/execute/SKILL.md](../skills/execute/SKILL.md), [../skills/comprehensive-review/SKILL.md](../skills/comprehensive-review/SKILL.md), [../skills/post-build/SKILL.md](../skills/post-build/SKILL.md) — core skill prompts
- [../skills/post-build/automation.md](../skills/post-build/automation.md) — wiring the post-build stage into an automation trigger
- [../plugins/workflow-lab/skills/iterate/SKILL.md](../plugins/workflow-lab/skills/iterate/SKILL.md) — the composition pattern in practice
- [../plugins/workflow-lab/skills/workflow-tuning/reference.md](../plugins/workflow-lab/skills/workflow-tuning/reference.md) — observed lessons corpus
- [../docs/plans/02-pivot-consolidate-focus/DESIGN.md](../docs/plans/02-pivot-consolidate-focus/DESIGN.md) — the full binding-contract record this architecture summarizes (plan-scoped; this file is the durable summary going forward)
