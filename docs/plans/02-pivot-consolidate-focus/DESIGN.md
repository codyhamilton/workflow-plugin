# Pivot, Consolidate, Focus — Design

Cross-implementor contracts for the revised workflow model. Consumers: the Phase 2–5 execution slices of this plan, and the external cursor automation that orchestrates review/QA/merge-babysitting against PR branches. These contracts are what "pivot, consolidate, focus" consolidates *onto* — the skill revisions implement them; the pipeline codes against them.

## Outcome

One workflow model shared by human and cloud processes. A change is planned and executed against explicit contracts; the PR branch carries a plan folder that downstream automation can mechanically locate; review and QA outcomes land back in that folder; coordination between agents travels as authored briefs, never orchestrator paraphrase; nothing in the repo encodes work status.

## Domain: PR Artifact Seam

Ownership:

- The build stage (plan + execute, in one run or two) owns creating the plan folder and everything in it up to PR creation.
- The orchestrated pipeline stage (review, QA, babysit) owns REVIEW.md, QA.md, and remediation briefs, written back to the same folder via commits on the PR branch.

Contracts:

- Plan folder path: `docs/plans/<NN>-<slug>/` on the PR branch. One folder per change/PR.
- The PR body contains a marker line pointing at the plan folder: `Workflow-Plan: docs/plans/<NN>-<slug>/`.
- Build-stage contents: `PLAN.md` (required), `DESIGN.md` (only when contracts need reification), `IMPLEMENTATION.md` (required, written progressively during execution), `briefs/` (committed dispatch briefs).
- Pipeline-stage contents: `REVIEW.md` (findings keyed to PLAN.md acceptance criteria), `QA.md` (QA plan derived from intent + scope, and its results), `briefs/remediation-<NN>.md` (per-finding fix briefs).

Required behavior:

- A plan folder existing on a branch means the work is being built or was built. No folder is created for deferred or speculative work.
- IMPLEMENTATION.md is written progressively, not at completion — a killed run must leave a branch resumable from its artifacts alone.
- **Fallback**: a PR arriving with no plan folder (human or agent that skipped the workflow) does not break the pipeline. The review stage reconstructs intent from the PR description, linked issue, and commits into `RECOVERED-INTENT.md` in a newly created plan folder, then proceeds uniformly.

Non-goals:

- No status fields, scores, or state machines in any artifact — PR state is the status. (Status metadata invites Goodhart gaming; same reasoning as iterate's artifact rules.)
- The seam does not prescribe the pipeline's internal orchestration, only what it reads and where it writes.

Acceptance criteria:

- Given only a PR, an agent can locate the plan folder from the marker line without heuristics.
- Given only the PR branch (no run context, no transcripts), an agent can state the change's intent, what was built, what was reviewed, and what remains — from the folder alone.
- A PR with no plan folder still flows through the pipeline via the fallback.

## Domain: Artifact Taxonomy

Ownership:

- Durable artifacts are owned by the role that authors them (plan → PLAN.md/DESIGN.md, execute → IMPLEMENTATION.md, review → REVIEW.md/QA.md).
- Run-scoped artifacts (briefs) are owned by their author and addressed to a named consumer.

Contracts:

- **Durable — intent and outcome**: PLAN.md, DESIGN.md, IMPLEMENTATION.md, REVIEW.md, QA.md. These survive the merge and are the provenance record.
- **Run-scoped — coordination**: briefs. Committed to `briefs/` in the plan folder for provenance and debugging, but no future agent is required to read them to understand the change.
- **Status**: carried by nothing in the repo. PRs, branches, and the tracker carry status. Deferred work becomes a design-intent doc (`docs/design/`) or a tracker issue. Multi-PR programs become a stable design-intent doc that each PR's PLAN.md references, plus a sequence of self-contained plan-execute runs.

Required behavior:

- Plans state intent verbatim (the triggering request, issue, or task — whatever the human actually said), an assumption ledger for decisions made without a human, scope, and QA-drivable acceptance criteria.
- User-facing acceptance criteria state entry point → action → observable result, sufficient for a computer-use QA agent to derive its plan mechanically.

Non-goals:

- No folder taxonomy encoding lifecycle (`[NEW]-` prefixes, renumbering ceremonies, ROADMAP-as-schedule).
- Existing numbered folders (`01-workflow-improvements`) are historical provenance; no migration.

Acceptance criteria:

- Every durable artifact names (implicitly by contract or explicitly) who consumes it; an artifact with no consumer or gate does not exist.
- The QA stage can derive an executable QA plan from PLAN.md's intent + scope + acceptance criteria without asking anything.

## Domain: Briefs Invariant

Ownership:

- Whoever holds the hottest context for a piece of work authors the brief for it. The planner briefs implementation contracts; the reviewer briefs remediations.

Contracts:

- Plugin-wide invariant, stated once and inherited by all skills: **context authors write once, in full, addressed to the consumer; orchestrators route verbatim, never paraphrase.** Orchestrators handle pointers and routing, not translation.
- Brief files live in the plan folder's `briefs/` directory; drift-sensitive skill-level briefs (iterate's) stay in the skill's own `briefs/` and are passed verbatim, as today.

Required behavior:

- Execute derives worker briefs from PLAN.md/DESIGN.md contracts while its context is hot, at dispatch time — not pre-written into the plan (that was the backlog's decomposition residue).
- Review writes each structural finding as a remediation brief a fixing agent can execute without the reviewer or orchestrator re-explaining it.

Non-goals:

- This is not "write more artifacts." The invariant is authorship + verbatim routing; the artifact is just the medium. Skills must not respond by producing documentation cascades — a brief with no named consumer is ceremony.

Acceptance criteria:

- In an execute run, worker prompts consist of the routed brief (plus mechanical pointers), not an orchestrator summary of the plan.
- A remediation brief is sufficient for a clean agent to fix the finding without reading the full review conversation.

## Domain: Plugin Partition

Ownership:

- One repo, two plugin manifests in `marketplace.json`.

Contracts:

- **Core** (`workflow`): plan, execute, comprehensive-review. Installable in cloud build environments and the pipeline harness. No interactive gates that dead-end headless; no local-filesystem dependencies.
- **Lab** (working name `workflow-lab`): setup, iterate, transcript-parser, workflow-tuning. Interactive and/or local-filesystem-bound; never required by the pipeline.

Required behavior:

- Core skills carry both postures (interactive checkpoint held / headless waved through) in one skill body — posture is a runtime condition, not a plugin split.
- Lab skills may compose core skills (iterate does); core skills never depend on lab skills.

Acceptance criteria:

- Installing core in a fresh cloud environment yields a working plan → execute → PR flow with no interactive dead-ends.
- `iterate` still runs locally end-to-end after re-composition over the revised core skills.
