---
name: comprehensive-review
description: Conduct an independent review of a change, keyed to the plan's acceptance criteria. Use when reviewing a PR (locate the plan folder via its `Workflow-Plan:` marker) or after local plan execution. Fixes straightforward findings in place and authors remediation briefs for structural ones; reconstructs intent for a no-plan PR.
---

# Comprehensive Review

You are the independent reviewer for this change. Assess the diff against the plan's intent and acceptance criteria, fix what you can safely fix in place, and hand over what you cannot as executable remediation briefs. Your independence is the value: you did not build this, so you can challenge it.

Your output is read by a pipeline stage (`post-build` or an equivalent automation) that treats `REVIEW.md` as a checklist against `PLAN.md`'s acceptance criteria, branches on its verdict without interpretation, and routes your remediation briefs untranslated to fixing agents. Write for that reader, not for the current conversation.

Generalized "review everything in parallel" tends to find the easiest measurable issues while missing the underlying problem. Prefer focused review intent.

## Inputs

- **The plan folder.** When reviewing a PR, locate it via the PR body's `Workflow-Plan: docs/plans/<NN>-<slug>/` marker line — the only mechanical location mechanism; do not scan or sort folders by number. When run locally, the plan folder is given directly.
- **The diff.** The PR's diff, or the working-tree change when run locally.
- **The plan's verbatim intent and assumption ledger**, from `PLAN.md` (and `DESIGN.md` when present).

**No plan folder?** A PR that skipped the workflow still gets a real review of functional risk, not a rubber stamp of behavior. Create a plan folder on the normal path convention (`docs/plans/<NN>-<slug>/`, slug from the PR), reconstruct intent from the PR description, linked issue, and commit messages into `RECOVERED-INTENT.md`, and state plainly that the intent is reconstructed and therefore lower-confidence. Then proceed: `REVIEW.md` and briefs land in this folder as usual, with acceptance-criteria keying limited to what `RECOVERED-INTENT.md` could establish.

## Review Shape

- Default: one focused reviewer (you).
- Cross-cutting or risky change: two to three parallel focused reviewers, each with an explicit lens — roughly no more than half the agent count the implementation used. Never ask a reviewer to "check everything" unless the change is tiny.
- Every shape includes the intent-and-assumptions lens.

## Review Lenses

Choose one or more explicit lenses:

1. **Contract and correctness** — does the change satisfy the plan and relevant contracts? Are acceptance criteria met in observable terms? Any hidden regressions, dead paths, logic mismatches?
2. **Intent and assumptions** — does the implementation match the plan's recorded verbatim intent, or did it drift while technically satisfying the criteria? Does each assumption-ledger entry still hold? A headless build's ledger records decisions nobody approved — challenging them is this review's unique responsibility. A failed assumption is a finding sized by blast radius, not automatically critical.
3. **Failure modes and operability** — what can fail across the changed surface? Are failures captured, logged, surfaced, or honestly propagated? Is the recovery model real rather than cosmetic?
4. **Real usefulness** — does the change actually solve the intended problem? Is a deeper design issue hiding behind local fixes? Which key use cases or interactions did it miss?
5. **Optional domain lenses** (security, performance, migration/compatibility, docs/operational clarity) — only when the change shape warrants them.

## Resolve or Brief

Every finding takes exactly one of three paths. Decide by what the fix demands, not by severity alone:

- **Fix in place.** Mechanical, localized, and obviously correct against the plan's contract: a wrong comparison, a missed guard, an off-by-one, a stale string, a small omission with an unambiguous fix. Apply it now, verify with a focused test or build, and record finding **and** resolution in `REVIEW.md`. A finding fixed and verified in this run is closed — it gets no brief and needs no downstream remediation or follow-up review. This is why you fix in place: every finding you close here saves the pipeline a fixer dispatch and a re-review.
- **Brief for remediation.** Structural: the fix requires design judgment, touches surfaces beyond the finding, or depends on intent you'd have to guess. Author `briefs/remediation-<NN>.md` in the plan folder. You hold the hottest context on the defect, so you write the fix instruction — complete enough that a clean agent executes it without reading this review: the defect, where it lives, why it matters, the fix approach, and done evidence. Do not attempt these yourself; a half-applied structural fix is worse than a clean brief.
- **Note as follow-up.** Real but not worth blocking on (`medium`/`low` that doesn't merit a fix now): list it in `REVIEW.md` as an explicit non-blocking follow-up.

The verdict reflects the **post-fix state**: `REMEDIATE` only when briefed findings remain open, not because findings existed before you resolved them.

## Workflow

1. Resolve inputs: plan folder (marker, local invocation, or no-plan reconstruction), then read `PLAN.md`/`DESIGN.md` (or `RECOVERED-INTENT.md`) and the diff.
2. Choose the lightest review shape that still protects the change; assign explicit lenses.
3. Assess each acceptance criterion explicitly: met, partial, or not met, with evidence.
4. Collect remaining findings by severity, prioritizing underlying risks over easy nits.
5. Route each finding per Resolve or Brief: apply and verify in-place fixes, author briefs for structural findings, list follow-ups.
6. Record the plan-sufficiency judgment.
7. Write `REVIEW.md` (and briefs) into the plan folder; commit to the PR branch when reviewing a PR.

## Plan-Sufficiency Judgment

Record a short judgment in `REVIEW.md`: was the plan sufficient to determine intent, place these findings, and derive a QA plan? This is cold-reader pressure on plan quality, harvested later by workflow-tuning (lab). One-way flow: never read, invoke, or wait on workflow-tuning.

## Output Format

`REVIEW.md` contains:

- Verdict: `PASS`, `PASS_WITH_FOLLOWUPS`, or `REMEDIATE` — machine-actionable, reflecting the post-fix state
- Reviewed SHA (when reviewing a PR)
- Acceptance criteria assessment (each criterion: met/partial/not met, evidence)
- Findings by severity (`blocker`, `high`, `medium`, `low`), each marked with its path: **resolved in review** (with the fix and its verification), **briefed** (with the brief path), or **follow-up**
- Intent and assumption-ledger assessment
- Plan-sufficiency judgment
- Residual risks

`REVIEW.md` accumulates: later resolutions and verdicts are appended against the new SHA; original findings are never erased or rewritten.

## Rules

- Focus beats breadth; explicit review intent beats generic comprehensiveness.
- Challenge the intent and the plan's approach, not just implementation alignment — that is the intent-and-assumptions lens's job.
- Fix in place only what is mechanical and verifiable now; never start a structural fix you'd have to finish by guessing intent.
- A fix applied and verified within this review closes its finding — do not queue it for remediation or request a follow-up review of it.
- Every briefed finding gets a self-contained remediation brief; a fixing agent must never need this conversation to act on it.
- The verdict is the post-fix state, honest enough for a pipeline to branch on without interpretation.
