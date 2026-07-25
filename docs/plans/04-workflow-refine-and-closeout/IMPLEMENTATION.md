# Implementation — Workflow Refinement and Close-Out

## Run

- Tool: Claude Code (local, interactive)
- Session/Run ID: `6a34afe2-e572-49d4-9348-7e597cd5d26f`
- Started: 2026-07-26

## Deviation from execute's own rules, recorded first

This file was written **at the end of the run, not progressively**, and no workers were dispatched —
the user directed a single holistic pass ("We shouldn't really need to delegate this much, it's
mainly prose and helps to be done wholistically"). `refine` was therefore not run against this plan
either, so there are no briefs and `PLAN.md`'s Execution Phases remain the plan's light phasing.

Both are knowing deviations, and both are the honest reading of the work: the change is one
interlocking prose revision across eleven files where every seam has to agree with every other, which
is exactly the case `refine`'s skip rule and `execute`'s delegation-judgment call exist to permit. The
cost paid is the one the rules protect against — a killed run would have left nothing resumable.

## What was built

### The `refine` skill (`skills/refine/`)

New core skill plus `templates/brief.md`. Owns: the skip rule (single-worker slices stay with
`execute`), a recon pass over the code surface the plan implies, decomposition into ordered units
under two hard constraints (parallel units own disjoint paths; a unit that cannot be named clearly is
not a unit), the brief anatomy, the rewrite of `PLAN.md`'s Execution Phases into the definitive
dispatch list, and the executability verdict — proceed, or bounce to `plan` with the specific gaps
recorded in Open Questions.

### The `close-out` skill (`skills/close-out/`)

New core skill. Appends `## Outcome` to `PLAN.md`, promotes a `DESIGN.md` that reifies lasting
contracts to `docs/design/` or deletes it, routes follow-ups to issues or design docs, deletes the
consumed artifacts, and commits once. Guards: never close unfinished work, never close over an open
`blocker`/`high`, never close a branch a pipeline stage is still working. Abandoned work is closed out
as abandoned rather than left.

### `execute` adapted to consume briefs

`Brief-Based Dispatch` became `Brief Routing and Authorship`: routing-first when `refine` has run,
inline authorship only for the skipped case. Added the contradiction-amendment rule (a worker's
reported mismatch edits the brief file, never conversation alone), per-brief outcome recording in
`IMPLEMENTATION.md`, and the resume path (dispatch list × recorded outcomes). `Sizing Method` trimmed
to the ladder plus a "this should have been refined" signal. Model allocation folded in from the
deleted `reference.md`; session-ID formulas dropped in favour of `transcript-parser`, which owns them.
`Required Completion Artifacts` became `Run Artifacts`, reflecting that they are consumed.

### Reference-doc consolidation

`plugins/workflow-lab/skills/workflow-tuning/principles.md` — 16 cross-cutting principles, each
naming the skills that instantiate it and, where one exists, where it is deliberately *not* applied.
Deleted `skills/{plan,execute,post-build}/reference.md` and
`plugins/workflow-lab/skills/iterate/reference.md`. Moved `skills/post-build/automation.md` to
`docs/automation/post-build.md` under the new rule that a skill directory holds only what an agent
loads while working.

`workflow-tuning/reference.md` repaired and extended: dead exemplar paths replaced with repo-level
attribution, lesson 2 marked Retired, lesson 19 written (it was referenced by lesson 18 but never
existed), the stranded Priority 2/3 backlog dropped, every landed lesson marked **Landed** with where.
Numbering preserved for citation stability.

### Docs

`docs/ARCHITECTURE.md` rewritten to seams, contracts, and invariants — the per-skill
"Skill Responsibilities" prose (which restated each `SKILL.md` in worse words) replaced by a one-row
table, and the "Data Flows" section dropped as the same cascade. Artifact taxonomy gained its terminal
states (durable / consumed / promoted / status-carried-by-nothing); invariant 10 added ("every plan
ends"). `docs/OVERVIEW.md` and `README.md` updated for the new loop and skills. Manifests bumped to
2.3.0; `install.sh` skill lists updated.

### Install drift

`~/.claude/plugins/marketplaces/workflow-plugin` fast-forwarded `8095d5a` → `9930a57`; the `[NEW]-`
instruction is gone from that clone. **The loaded copy is still stale** — Claude Code serves
`~/.claude/plugins/cache/workflow-plugin/workflow/1.1.0/`, and only `/plugin update
workflow@workflow-plugin` re-pins it. README gained a "Which install is live?" section covering both
install paths, how they drift, how to tell which is serving, and how to update each.

### Migration and dogfooding

- `docs/plans/03-integrate-post-build-stage/` closed out — first live application of the contract.
- `docs/plans/[NEW]-conversation-indexer/` committed (so history is genuinely the archive), then
  migrated: `docs/design/conversation-indexer.md` carries the durable contracts; the shipped slice
  became `docs/plans/05-cursor-toolkit/PLAN.md`, closed out.
- `docs/analysis/` committed and harvested into lessons 20–25.

## Design deviations from PLAN.md

Two, both in phase 4, both discovered while writing the contract:

**1. Close-out cannot run inside `post-build`.** The plan placed it "after remediation and QA
planning, before the candidate SHA". That breaks: `REVIEW.md` is the QA planner's input for residual
risks, `QA.md` is the QA driver's matrix, and remediation fixers record resolutions into `REVIEW.md` —
so a close-out at that point deletes live inputs to the phases that follow it. Moving it later makes
it the trailing commit that unbinds the tested SHA. The constraint the plan identified was real; its
placement was not. Close-out in pipeline posture runs **after the PR merges, on the default branch**,
where the tested commit is untouched and the deletion is a plain docs commit. Recorded as a posture on
the skill, in `post-build`'s rules, in its report schema, and in `ARCHITECTURE.md`.

**2. `close-out` is a normal skill, not dispatch-only.** The plan specified a dispatch-only worker
like `post-build-fixer`. But deviation 1 means a human invokes it directly after a merge — the
pipeline path is *the* common path — and a dispatch-only description would discourage exactly that.
Its description names both entry points instead.

## Deliberately not done

- **`01-workflow-improvements` and `02-pivot-consolidate-focus` were not closed out.** Out of the
  plan's scope, which named only `03` and the `[NEW]-` folder, and `02`'s briefs are currently cited
  as the worked example of brief anatomy in the lessons corpus. A separate decision.
- **`evals/`** left as-is; the plan flagged it as an open question, not a decision.
- **No independent review has run**, so this plan is not closed out. That is the remaining step.

## Validation

- `grep -rn "\[NEW\]" --include=*.md --include=*.sh .` outside `docs/plans/` returns only the README's
  breaking-change callout and lesson 28, both of which are about the removal.
- No file under `skills/` or `plugins/*/skills/` is anything but `SKILL.md`, a template, a brief, or a
  script — except `workflow-tuning`'s two corpora, which are that skill's working material.
- Every relative link in the changed docs resolves.
- `docs/plans/03-integrate-post-build-stage/` and `docs/plans/05-cursor-toolkit/` each contain
  `PLAN.md` alone, with an Outcome section.
- Removed an empty `skills/workflow-tuning/retros/` directory left behind by the phase-4 partition
  move — untracked, so invisible to git status, and it made the core plugin look like it shipped a lab
  skill.
