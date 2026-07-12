---
name: comprehensive-review
description: Conduct an independent review of a significant change, keyed to the plan's acceptance criteria. Use when reviewing a PR (locate the plan folder via its `Workflow-Plan:` marker) or after local plan execution.
---

# Comprehensive Review

Review is mandatory after plan execution, but the review shape should be right-sized to the change.

Generalized "review everything in parallel" tends to find the easiest measurable issues while missing the underlying problem. Prefer focused review intent.

This review is a pipeline stage: the `post-build` stage (or an equivalent automation) reads `REVIEW.md` as a checklist against `PLAN.md`'s acceptance criteria, branches on its verdict, and consumes remediation briefs untranslated. Write for that reader, not just for the current conversation.

## Inputs

- **The plan folder.** When reviewing a PR, locate it via the PR body's `Workflow-Plan: docs/plans/<NN>-<slug>/` marker line — the only mechanical location mechanism; do not scan or sort folders by number. When run locally (not against a PR), the plan folder is given directly.
- **The diff.** The PR's diff, or the working-tree change when run locally.
- **The plan's verbatim intent and assumption ledger**, read from `PLAN.md` (and `DESIGN.md` when present) in the plan folder.

If the PR body has no `Workflow-Plan:` marker (no plan folder), use the **No-Artifact Fallback** below before proceeding.

## Output Placement

- Findings land in `REVIEW.md` **in the plan folder**, committed to the PR branch when reviewing a PR. Key findings to `PLAN.md`'s acceptance criteria: assess each criterion explicitly, then list findings outside the criteria by severity. This keying is what lets the downstream post-build stage treat `REVIEW.md` as a checklist.
- Each **structural** finding additionally becomes a remediation brief at `briefs/remediation-<NN>.md` in the plan folder. You hold the hottest context on the defect, so you author the fix instruction: complete enough that a clean agent can execute it without reading the review conversation. Include the defect, where it lives, why it matters, the fix approach, and done evidence.
- Trivial findings do not get briefs — list them in `REVIEW.md` for inline fixing.

## No-Artifact Fallback

A PR arriving with no plan folder (a human or agent that skipped the workflow) does not break the review:

1. Create a plan folder using the normal path convention (`docs/plans/<NN>-<slug>/`, slug derived from the PR).
2. Reconstruct intent from the PR description, linked issue, and commit messages, and write it to `RECOVERED-INTENT.md` in that folder.
3. Note plainly that the intent is reconstructed, not authored, and therefore lower-confidence.
4. Proceed uniformly from here — `REVIEW.md` and remediation briefs land in this folder exactly as they would with an authored `PLAN.md`, but acceptance-criteria keying falls back to whatever `RECOVERED-INTENT.md` was able to establish.

## Default Review Shape

- Normal planned slice: one independent focused reviewer.
- Cross-cutting or risky slice: two to three focused reviewers in parallel.
- Explicit user request for a 3-way review: run three parallel focused reviewers.

## Review Lenses

Choose one or more explicit lenses for the review:

1. Contract and correctness
   - Does the change actually satisfy the plan and the relevant contracts?
   - Are acceptance criteria met in observable terms?
   - Are there hidden regressions, dead paths, or logic mismatches?

2. Intent and assumptions
   - Does the implementation match the plan's recorded verbatim intent, or did it drift while still technically satisfying the acceptance criteria?
   - Does each assumption-ledger entry still hold? A headless build's ledger records decisions nobody approved — challenging them is this review's unique responsibility.
   - An assumption that fails is a finding, sized by its blast radius, not automatically critical.

3. Failure modes and operability
   - What can fail across the changed surface?
   - Are failures captured, logged, surfaced, or honestly propagated?
   - Is the recovery model appropriate, rather than fake or misleading?

4. Real usefulness
   - Do the changes actually solve the intended problem?
   - Is there a deeper design issue hiding behind local fixes?
   - Are there key use cases or interactions the implementation failed to consider?

5. Optional domain lenses
   - Security
   - Performance
   - Migration or compatibility
   - Documentation or operational clarity

Only add optional lenses when the change shape warrants them.

## Workflow

1. Resolve inputs: locate the plan folder (via the PR marker, the local invocation, or the no-artifact fallback), then read `PLAN.md`/`DESIGN.md` (or `RECOVERED-INTENT.md`) and the diff.
2. Choose the lightest review shape that still protects the change.
3. Give each reviewer an explicit focus, always including the intent-and-assumptions lens. Do not ask one reviewer to "check everything" unless the change is tiny.
4. Assess each of `PLAN.md`'s acceptance criteria explicitly (met, partial, or not met, with evidence).
5. Collect remaining findings by severity and prioritize underlying risks over easy nits.
6. For each structural finding, write a remediation brief at `briefs/remediation-<NN>.md`. Leave trivial findings inline in `REVIEW.md`.
7. Record the plan-sufficiency judgment (below).
8. After one external review loop, fix issues that fit within scope, self-review the fixes, and report residual risks.
9. Write `REVIEW.md` (and any remediation briefs) into the plan folder. Do not default to repeated external review loops unless the user asks for them or the change is unusually risky.

## Plan-Sufficiency Judgment

Record a short judgment in `REVIEW.md`: was the plan sufficient to determine intent, place these findings, and derive a QA plan?

This is cold-reader pressure on plan quality. The judgment is a one-way artifact: workflow-tuning (lab) harvests it later to improve the plan skill. This skill never invokes or depends on workflow-tuning — do not read it, call it, or wait on it.

## Output Format

`REVIEW.md` should contain:

- Verdict: `PASS`, `PASS_WITH_FOLLOWUPS`, or `REMEDIATE` — machine-actionable, so a pipeline stage can branch on it without interpretation
- Reviewed SHA (when reviewing a PR)
- Acceptance criteria assessment (each `PLAN.md` criterion, met/partial/not met, evidence)
- Findings by severity (outside the acceptance criteria): `blocker`, `high`, `medium`, or `low`
- Intent and assumption-ledger assessment
- Plan-sufficiency judgment
- Fixes applied
- Residual risks
- Final assessment against the plan or contract

`REVIEW.md` accumulates across remediation: resolutions and re-review verdicts are appended against the new SHA; original findings are never erased or rewritten.

## Rules

- Independent review is mandatory after planned execution.
- Focus beats breadth. Explicit review intent is usually better than generic comprehensiveness.
- Small or local changes should usually get one reviewer, not three.
- Large cross-cutting changes may justify parallel focused reviewers. A simple starting point is no more than half as many agents as were used for the implementation.
- The review should challenge the intent and plan approach, not just naive implementation alignment — this is what the intent-and-assumptions lens is for.
- A PR with no plan folder still gets a full review via the no-artifact fallback; it must not be skipped or downgraded to a rubber stamp.
- Every structural finding gets a self-contained remediation brief; a fixing agent should never need the review conversation to act on it.
