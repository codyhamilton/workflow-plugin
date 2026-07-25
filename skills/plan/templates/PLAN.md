# <Plan Title>

## Intent

User request, verbatim:

> <copy the full prompt or the exact relevant portion verbatim>

## Why This Plan Exists

<explanation of the problem being solved and why it matters now>

## Scope

<2-3 sentence high-level scope>

## Architectural Implications

- <stable doc or architectural assumption affected>
- <sequencing or downstream-plan implication>
- <boundary or ownership implication>

## Intent Validation

- <decision or clarification that materially shapes scope, sequencing, boundaries, non-goals, or acceptance criteria>
- <question asked and answer received, or state "None">

## Assumption Ledger

<Headless posture only — one entry per question the skill would otherwise have asked a human. For interactive sessions, state "None — interactive session; see PROVENANCE.md.">

### Assumption N

- **Question:** <what would have been asked>
- **Answer chosen:** <the decision made>
- **Rationale:** <why this answer, not another>
- **If wrong:** <what changes about the plan or its execution if this assumption doesn't hold>

## Open Questions

- <question that must be resolved, or state "None">

## Execution Phases

<Light phasing at plan time — the shape and order of the work, not a dispatch list. `refine` rewrites this section into the definitive ordered dispatch list, each phase naming its brief file and its dependencies.>

1. <define or land the next executable slice>
2. <implement the core behavior or contract>
3. <integrate, verify, and remove superseded behavior>

## Acceptance Criteria

User-facing (entry point → action → observable result):

- <entry point> → <action taken> → <observable result>

Non-user-facing (observable statement):

- <observable success condition>

## Provenance Notes

See `PROVENANCE.md` in this plan folder, when present, for the plan conversation record — verbatim initial request, Q&A turns, and agent decisions written progressively during interactive sessions. Headless one-shot runs have no `PROVENANCE.md`; the Assumption Ledger above and this section together carry the full record.

- <important rationale, tradeoff, or decision future agents should understand>

<!--
## Outcome

Appended by `close-out` when the work lands — what was built, what changed, deviations from plan
wording and why, review verdict and resolutions, QA result, residual risks, and where each follow-up
went. Do not write this section at plan time; do not leave a placeholder for it.
-->

