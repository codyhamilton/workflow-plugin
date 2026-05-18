---
name: comprehensive-review
description: Conduct an independent review of a significant change. Use when requested to conduct a review or 3way review, or after implementation of a planned work package.
---

# Comprehensive Review

Review is mandatory after plan execution, but the review shape should be right-sized to the change.

Generalized "review everything in parallel" tends to find the easiest measurable issues while missing the underlying problem. Prefer focused review intent.

## Default Review Shape

- Normal planned slice: one independent focused reviewer.
- Cross-cutting or risky slice: two to three focused reviewers in parallel.
- Explicit user request for a 3way review: run three parallel focused reviewers.

## Review Lenses

Choose one or more explicit lenses for the review:

1. Contract and correctness
   - Does the change actually satisfy the plan and the relevant contracts?
   - Are acceptance criteria met in observable terms?
   - Are there hidden regressions, dead paths, or logic mismatches?

2. Failure modes and operability
   - What can fail across the changed surface?
   - Are failures captured, logged, surfaced, or honestly propagated?
   - Is the recovery model appropriate, rather than fake or misleading?

3. Real usefulness
   - Do the changes actually solve the intended problem?
   - Is there a deeper design issue hiding behind local fixes?
   - Are there key use cases or interactions the implementation failed to consider?

4. Optional domain lenses
   - Security
   - Performance
   - Migration or compatibility
   - Documentation or operational clarity

Only add optional lenses when the change shape warrants them.

## Workflow

1. Read the relevant plan artifacts and execution artifacts first.
2. Choose the lightest review shape that still protects the change.
3. Give each reviewer an explicit focus. Do not ask one reviewer to "check everything" unless the change is tiny.
4. Collect findings by severity and prioritize underlying risks over easy nits.
5. After one external review loop, fix issues that fit within scope, self-review the fixes, and report residual risks.
6. Do not default to repeated external review loops unless the user asks for them or the change is unusually risky.

## Output Format

Each review should produce:

- Outcome
- Findings by severity
- Fixes applied
- Residual risks
- Final assessment against the plan or contract

## Rules

- Independent review is mandatory after planned execution.
- Focus beats breadth. Explicit review intent is usually better than generic comprehensiveness.
- Small or local changes should usually get one reviewer, not three.
- Large cross-cutting changes may justify parallel focused reviewers. A simple starting point is no more than half as many agents as were used for the implementation.
- The review should challenge the intent and plan approach, not just naive implementation alignment
