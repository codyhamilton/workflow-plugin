# Workflow Plugin — Architecture

This file describes the **seams**: what each skill owns, what passes between them, and the
invariants that hold across all of them. It deliberately does not restate skill behavior — each
`SKILL.md` is the authority on its own workflow, and a prose copy here would only drift from it.

## Component Map

```
workflow-plugin/ (repo root — the `workflow` core plugin)
├── .claude-plugin/
│   ├── plugin.json            → core plugin manifest (name: workflow)
│   └── marketplace.json       → lists both plugins: workflow (source "./"), workflow-lab
├── .cursor-plugin/plugin.json → core plugin manifest for Cursor
├── skills/                    → core: cloud-safe, no interactive dead-ends
│   ├── plan/
│   ├── refine/
│   ├── execute/
│   ├── comprehensive-review/
│   ├── close-out/
│   └── post-build/            → briefs/{fixer,verifier,qa-planner,qa-driver}.md
├── plugins/workflow-lab/      → lab: local and/or interactive; never required by the pipeline
│   ├── .claude-plugin/plugin.json
│   ├── .cursor-plugin/plugin.json
│   └── skills/{setup,iterate,transcript-parser,workflow-tuning}/
├── docs/
│   ├── OVERVIEW.md        → what the plugin is and why
│   ├── ARCHITECTURE.md    → this file
│   ├── automation/        → operator guides for wiring stages into external triggers
│   └── plans/             → plan artifacts from dogfooding this plugin on itself
└── evals/{scenarios,results}/
```

Each plugin's source directory contains only its own skills: `skills/` at the repo root is
core-only; `plugins/workflow-lab/skills/` is lab-only. `install.sh` and `marketplace.json` both key
off this split.

**A skill directory holds only what an agent loads while working** — `SKILL.md`, `templates/`,
`briefs/`, `scripts/`. Design rationale about a skill lives in `workflow-tuning/principles.md`;
operator guides live under `docs/`. (`workflow-tuning`'s own `principles.md` and `reference.md` are
the exception that proves the rule: they are its working material, not commentary on itself.)

## The Loop

```
plan → refine → execute → review → close-out
        (skip)              │
                            ├── terminal:  comprehensive-review in-run, then close-out, then PR
                            └── pipeline:  PR → post-build → merge → close-out
```

| Skill | Plugin | Owns | Writes |
|---|---|---|---|
| `plan` | core | Intent capture, scope validation, drift detection, acceptance criteria | `PLAN.md`, optional `DESIGN.md`, optional `PROVENANCE.md` |
| `refine` | core | Decomposition into executable units; brief authorship; the executability verdict | `briefs/<NN>-<slug>.md`; rewrites `PLAN.md`'s Execution Phases |
| `execute` | core | Orchestration: routing briefs, sizing, worker allocation, the PR | `IMPLEMENTATION.md` (progressive), `REVIEW.md` in terminal posture |
| `comprehensive-review` | core | Independent assessment against acceptance criteria; in-place fixes; remediation briefs | `REVIEW.md`, `briefs/remediation-<NN>.md`, `RECOVERED-INTENT.md` |
| `post-build` | core | The pipeline stage against a PR: classify, review, remediate, QA, checks gate | Nothing itself — its workers write; its report is external |
| `post-build-{fixer,verifier,qa-planner,qa-driver}` | core | One dispatched phase each | Per their brief; `QA.md` (planner) |
| `close-out` | core | Ending a plan: the outcome record and the collapse | `docs/plans/<NN>-<slug>.md`; deletes the folder |
| `setup` | lab | Bootstrapping stable docs | `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` |
| `iterate` | lab | Long-horizon divergent exploration, composing the core skills | `OUTCOMES.md`, per-cycle artifacts |
| `transcript-parser` | lab | Session transcript → cost metrics | A `cost-comparison.md`-schema section |
| `workflow-tuning` | lab | The workflow itself: principles, lessons, evals, outcome harvest | `principles.md`, `reference.md` |

## Cross-Skill Contracts

**plan → refine**: `plan` produces `PLAN.md` (+ `DESIGN.md` when used) with explicit scope,
contracts, light phasing, and QA-drivable acceptance criteria. `refine` reads them cold and must be
able to decompose them into units with disjoint ownership and runnable done evidence. If it cannot,
it records the specific gaps in `PLAN.md`'s Open Questions and returns to `plan` — the bounce is a
contract, not a failure path.

**refine → execute**: the handoff is `briefs/` plus `PLAN.md`'s rewritten Execution Phases, which is
the definitive ordered dispatch list naming each unit's brief and dependencies. `execute` routes
those briefs verbatim; it does not re-derive them. `refine` is **skipped** for single-worker slices,
where `execute` authors inline at dispatch time instead.

**plan/refine → execute (cold read)**: `execute` reads the committed artifacts cold, even
immediately after `plan` or `refine` ran in the same session. Composition is dispatch, not inlining;
the cold read is load-bearing.

**execute → comprehensive-review**: mandatory in **terminal** posture (the default, absent a
declaration); dropped to pre-flight self-verification in **pipeline** posture, where a downstream
orchestrated review stage is declared to exist.

**execute → post-build**: `execute`'s pipeline posture exists because `post-build` (or an equivalent
automation) picks the PR up. The handoff is the PR itself: branch, commits, and the `Workflow-Plan:`
marker. No live call in either direction.

**post-build → comprehensive-review**: `post-build` classifies the change, then dispatches
`comprehensive-review` when independent review is needed, and branches on `REVIEW.md`'s verdict
(`PASS` / `PASS_WITH_FOLLOWUPS` / `REMEDIATE`) without interpretation, routing remediation briefs
verbatim to fixers.

**post-build ↔ repo adapter (external)**: the adapter supplies production boundaries, required
checks, deploy-proof mechanics, QA environment, and worker routing; `post-build` supplies the
portable stage semantics. Authority on conflict: repo hard limits → adapter → `post-build` →
triggering prompt. See [automation/post-build.md](automation/post-build.md) for wiring.

**→ close-out**: `close-out` consumes the whole plan folder — `PLAN.md` included — and leaves one
record file, `docs/plans/<NN>-<slug>.md`, whose structure the skill defines. Its placement is
posture-determined and is a hard constraint, not a preference:

- **Terminal**: `execute` runs it after review settles, as the last commit before the PR.
- **Pipeline**: it runs **after the PR merges**, on the default branch. It cannot run inside
  `post-build` — `REVIEW.md` and `QA.md` are live inputs to the phases that follow them, and a commit
  removing them would either break a later phase or become the trailing commit that unbinds the
  tested SHA.

**setup → plan**: filesystem presence only. `plan` reads the stable docs at Ground and never
hard-blocks on their absence.

**iterate → plan/refine/execute/comprehensive-review**: `iterate` (lab) composes core skills as
dispatched subagents, passing drift-sensitive context verbatim from its own `briefs/`. Lab skills may
compose core skills; core skills never depend on lab skills.

**comprehensive-review → workflow-tuning**: one-way, artifact-only. The plan-sufficiency judgment is
written as part of normal review output; `workflow-tuning` reads it later across many merged PRs.
`comprehensive-review` never invokes or waits on `workflow-tuning`.

## PR Artifact Seam

The contract an external pipeline automation codes against, so it can locate and extend a build's
plan folder mechanically:

- **Location**: `docs/plans/<NN>-<slug>/` on the PR branch when a plan folder exists. `NN` is
  best-effort ordering only; the slug is the unique key. The PR body's first line,
  `Workflow-Plan: docs/plans/<NN>-<slug>/`, is the only mechanical location mechanism — nothing scans
  or sorts folders by number. Ad-hoc trivial non-functional PRs may have no plan folder.
- **Build-stage contents** (owned by `plan`/`refine`/`execute`, written before PR creation):
  `PLAN.md` (required), `DESIGN.md` (when contracts need reification), `briefs/` (the dispatch
  briefs, amended in place where workers reported contradictions), `IMPLEMENTATION.md` (required,
  written progressively, recording each unit's outcome against its brief).
- **Pipeline-stage contents** (owned by `post-build`, committed back to the PR branch **before the
  candidate SHA** when those phases run): `REVIEW.md` (verdict + findings keyed to acceptance
  criteria, accumulating across remediation), `QA.md` (matrix only — one case per user-facing
  criterion with stable ID, entry point → action → expected result, evidence requirements;
  undriveable criteria listed with reason; no pre-execution pass/fail; **omitted when QA is not
  applicable**), `briefs/remediation-<NN>.md`.
- **External-only outputs**: classification, required-checks outcomes, final SHA-specific QA results
  and media go to the PR conversation or automation output, never a trailing commit.
- **Post-merge**: `close-out` collapses the folder into the single record file
  `docs/plans/<NN>-<slug>.md` and deletes the folder. A merged PR's marker path therefore resolves to
  the folder's history and to the record file that took its name.
- **Fallback**: a PR with no plan folder does not break the pipeline — functional/material changes
  reconstruct intent into `RECOVERED-INTENT.md` and proceed; trivial/small non-functional changes may
  be absorbed without inventing plan ceremony.

## Artifact Taxonomy

Four states, and every artifact is in exactly one:

- **Durable** — the close-out record file `docs/plans/<NN>-<slug>.md`, and any `DESIGN.md` promoted
  to `docs/design/`. Produced by close-out. This is the record.
- **Consumed** — `PLAN.md`, `PROVENANCE.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, `briefs/`
  (including remediation briefs), `RECOVERED-INTENT.md` — the whole plan folder. Load-bearing while
  the change is open; carried into the record and deleted at close-out; recoverable from branch
  history and the PR forever.
- **Promoted** — follow-ups that became tracker issues or design-intent docs in `docs/design/`.
- **Status** — carried by nothing. PRs, branches, and the tracker carry status. Deferred work becomes
  a design-intent doc or a tracker issue, never a stale plan folder, never a `ROADMAP.md`, never a
  status field.

## Postures

Declared by the invoker (skill argument or explicit statement in the dispatching prompt), never
inferred from TTY or environment. Every posture has a stated safe default for when nobody declares.

| Skill | Postures | Default |
|---|---|---|
| `plan` | interactive (checkpoint held) / headless (assumption ledger) | interactive |
| `execute` review | terminal (in-run independent review) / pipeline (pre-flight only) | terminal |
| `close-out` | terminal (before the PR) / pipeline (after merge) | follows `execute`'s |

## Key Invariants

1. User intent is captured verbatim in `PLAN.md`'s `## Intent` section, never paraphrased.
2. Context authors write once, in full, addressed to the consumer; orchestrators route verbatim,
   never paraphrase. Plugin-wide, not specific to any one skill.
3. Nothing in the repo carries status. A plan folder existing on a branch means the work is being
   built or was built — nothing else. No `ROADMAP.md`, no `STATUS.md`, no folder-status taxonomy, no
   version or completion field in any artifact.
4. Review is never silent: terminal posture runs mandatory independent review, pipeline posture
   substitutes pre-flight self-verification because a downstream stage is declared to exist.
5. Plans are intent, scope, implications, and QA-drivable acceptance criteria — never implementation
   specs. Executable detail lives in briefs, which are consumed at close-out.
6. `DESIGN.md` is optional, only when it reifies contracts or target shape not cheaply inferable from
   code and stable docs.
7. Core skills never depend on lab skills. Lab skills may compose core skills. Data flows lab-ward
   only as artifacts already written for another consumer, never as a live call.
8. `workflow-tuning` never auto-runs; user-invoked meta-skill only (`disable-model-invocation: true`).
9. No commit follows the tested commit. Deployed QA runs only when classification says it applies,
   after review has settled the code, only against a deployment proven to match the exact candidate
   SHA on a non-production target; its results are never committed. Required checks are read once,
   after the last code-changing phase. `post-build` reports merge-readiness; nothing in this plugin
   merges.
10. Every plan ends. Work that lands is closed out; work that is abandoned is closed out as abandoned
    or deleted. A plan folder that has simply stopped is a defect.

## Stable References

- [OVERVIEW.md](OVERVIEW.md) — what the plugin is and why
- [../README.md](../README.md) — install instructions, skills table, operating hypotheses
- [automation/post-build.md](automation/post-build.md) — wiring the post-build stage into an
  automation trigger
- [../plugins/workflow-lab/skills/workflow-tuning/principles.md](../plugins/workflow-lab/skills/workflow-tuning/principles.md)
  — the design principles behind these seams
- [../plugins/workflow-lab/skills/workflow-tuning/reference.md](../plugins/workflow-lab/skills/workflow-tuning/reference.md)
  — observed lessons corpus
- Each `SKILL.md` is the authority on its own behavior.
