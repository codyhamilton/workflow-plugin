# Workflow Plugin — Architecture

The seams: what each skill owns, what passes between them, and the invariants that hold across all of them. Each `SKILL.md` is the authority on its own behaviour.

## Component Map

```
workflow-plugin/ (repo root — the `workflow` core plugin)
├── .claude-plugin/{plugin.json, marketplace.json}
├── .cursor-plugin/plugin.json
├── skills/                    → core: cloud-safe, no interactive dead-ends
│   ├── design/                → templates/{DESIGN,PROVENANCE}.md
│   ├── refine/                → templates/brief.md
│   ├── execute/
│   ├── comprehensive-review/
│   ├── close-out/
│   └── post-build/            → briefs/{fixer,verifier,qa-planner,qa-driver}.md
├── plugins/workflow-lab/      → lab: local and/or interactive; never required by the pipeline
│   └── skills/{setup,iterate,transcript-parser,workflow-tuning}/
├── docs/{OVERVIEW,ARCHITECTURE}.md, docs/automation/, docs/plans/, docs/analysis/
└── evals/{scenarios,results}/
```

A skill directory holds only what an agent loads while working: `SKILL.md`, `templates/`, `briefs/`, `scripts/`. Rationale lives in `workflow-tuning/principles.md`; operator guides under `docs/`.

## The Loop

```
design ──sign-off──▶ ┌ per phase, in the design's order ┐ ──▶ review ──▶ close-out
                     │ refine → execute → verify → close │
                     └───────── hold | continue ─────────┘
                                                   terminal:  comprehensive-review in-run, close-out, PR
                                                   pipeline:  PR → post-build → merge → close-out
```

| Skill | Owns | Writes |
|---|---|---|
| `design` | Intent, problem, solution shape, contracts, phases with provable outcomes | `DESIGN.md`, optional `PROVENANCE.md` |
| `refine` | Decomposing one phase into briefed units; the coarse all-phase check; the verdict | `briefs/<phase>-<NN>-<slug>.md`; the phase's Units list in `DESIGN.md` |
| `execute` | One phase: routing, verification, the phase record; after the last phase, review posture and the PR | `IMPLEMENTATION.md` (progressive, per unit and per phase, with Carried); `REVIEW.md` in terminal posture |
| `comprehensive-review` | Independent assessment against phase outcomes; in-place fixes; remediation briefs | `REVIEW.md`, `briefs/remediation-<NN>.md`, `RECOVERED-INTENT.md` |
| `post-build` | The pipeline stage against a PR | Nothing itself; workers write `QA.md` and `REVIEW.md` updates; the report is external |
| `close-out` | Ending a plan | `docs/plans/<NN>-<slug>.md`; deletes the folder |
| `setup` (lab) | Bootstrapping stable docs | `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` |
| `iterate` (lab) | Divergent exploration; approach-open phases | `OUTCOMES.md`, per-cycle artifacts |
| `transcript-parser` (lab) | Transcript → cost metrics | a `cost-comparison.md` section |
| `workflow-tuning` (lab) | The workflow itself | `principles.md`, `reference.md` |

## Cross-Skill Contracts

**design → refine**: `DESIGN.md` with contracts precise enough to cite and phases each stating an outcome, surfaces, an approach flag, and dependencies. `refine` reads it cold. The first refinement coarse-checks every phase; each refinement briefs one phase. A missing contract, boundary, or provable outcome is recorded in Open Questions and bounced to `design`.

**execute → refine → execute**: `execute` builds the next phase without a Units list by dispatching `refine` as a separate context, then routing its briefs. A one-unit phase is briefed inline by `execute`. The handoff into the next phase is `IMPLEMENTATION.md`'s closed phase record, including its Carried section, which the next `refine` must place or bounce.

**phase boundary**: an optional stop (posture hold/continue, declared), a cheap-tier verification of the phase outcome, and the refinement bound for the next phase. A fresh orchestrator per phase. Termination is the design's phase count; more phases than signed off is a design change.

**approach-open phases**: `execute` holds at the boundary unless the invoker declared how they run. `iterate` (lab) is the intended method, with the phase outcome as a fixed yardstick; core never depends on it.

**cold read**: every stage reads the committed artifacts, never the previous stage's context, even in the same session.

**execute → comprehensive-review**: once, after the last phase, in terminal posture. Pipeline posture substitutes pre-flight self-verification because `post-build` exists downstream.

**execute → post-build**: the PR itself — branch, commits, `Workflow-Plan:` marker. No live call.

**post-build → comprehensive-review**: dispatched by name; `post-build` branches on the verdict without interpretation and routes remediation briefs by path.

**post-build ↔ adapter**: the adapter supplies repo mechanics; authority on conflict is repo limits → adapter → `post-build` → prompt. See [automation/post-build.md](automation/post-build.md).

**→ close-out**: consumes the whole folder. Terminal: the last commit before the PR. Pipeline: after merge, on the default branch, never inside the stage.

**setup → design**: filesystem presence only; `design` never blocks on stable docs.

**comprehensive-review → workflow-tuning**: one-way, artifact-only, via the plan-sufficiency judgment.

## PR Artifact Seam

- **Location**: `docs/plans/<NN>-<slug>/` on the PR branch. The PR body's first line, `Workflow-Plan: docs/plans/<NN>-<slug>/`, is the only mechanical locator. `NN` is best-effort ordering; the slug is the key.
- **Build-stage contents**: `DESIGN.md` (required; phases carry their Units lists once refined), `briefs/` (amended in place on reported contradictions), `IMPLEMENTATION.md` (required; per-unit outcomes, per-phase verification and Carried sections), optional `PROVENANCE.md`.
- **Pipeline-stage contents**, committed before the candidate SHA: `REVIEW.md`, `QA.md` (matrix only, omitted when QA does not apply), `briefs/remediation-<NN>.md`.
- **External-only**: classification, checks outcomes, SHA-specific QA results and media.
- **Post-merge**: `close-out` collapses the folder into `docs/plans/<NN>-<slug>.md`; the marker resolves to the folder's history and the record that took its name.
- **Fallback**: a PR with no plan folder reconstructs intent into `RECOVERED-INTENT.md` when functional, or is absorbed when trivial and non-functional.

Folders created before this version carry `PLAN.md` in place of `DESIGN.md`; skills read whichever exists.

## Artifact Taxonomy

- **Durable**: the close-out record; contracts promoted to `docs/design/`.
- **Consumed**: `DESIGN.md`, `PROVENANCE.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, `briefs/`, `RECOVERED-INTENT.md` — the whole folder, deleted at close-out, recoverable from history.
- **Promoted**: follow-ups that became tracker issues or design-intent docs.
- **Status**: carried by nothing. Carried items in a phase record are work not yet refined, with one consumer; they are not a tracker.

## Postures

Declared by the invoker, never inferred. Every posture has a safe default.

| Skill | Postures | Default |
|---|---|---|
| `design` | interactive (checkpoint held) / headless (assumption ledger) | interactive |
| `execute` boundary | hold / continue | hold |
| `execute` review | terminal / pipeline | terminal |
| `close-out` | terminal (before the PR) / pipeline (after merge) | follows `execute` |

## Key Invariants

1. Intent is captured verbatim in `DESIGN.md`'s Intent section.
2. Context authors write once, addressed to the consumer; orchestrators route verbatim.
3. Nothing in the repo carries status.
4. Review is never silent: terminal runs independent review; pipeline substitutes pre-flight because a downstream stage is declared.
5. A phase closes on a provable outcome, verified against real behaviour. Outcomes define phases; surfaces define units.
6. Refinement is per phase, against the code as it stands; the design's phase count bounds the loop.
7. Core never depends on lab; lab may compose core.
8. `workflow-tuning` never auto-runs.
9. No commit follows the tested commit. Nothing in this plugin merges.
10. Every plan ends in one record file.

## Stable References

- [OVERVIEW.md](OVERVIEW.md)
- [../README.md](../README.md)
- [automation/post-build.md](automation/post-build.md)
- [../plugins/workflow-lab/skills/workflow-tuning/principles.md](../plugins/workflow-lab/skills/workflow-tuning/principles.md)
- [../plugins/workflow-lab/skills/workflow-tuning/reference.md](../plugins/workflow-lab/skills/workflow-tuning/reference.md)
- [analysis/2026-09-08-workflow-vs-field.md](analysis/2026-09-08-workflow-vs-field.md) — the review this shape came from
