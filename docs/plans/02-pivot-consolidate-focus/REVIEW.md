# Review: Pivot, Consolidate, Focus (plan-stage adversarial review)

Independent adversarial review of the plan artifacts by a clean subagent (Sonnet), per the plan skill's mandated review pass. Findings below with dispositions; all accepted findings are applied in this folder and the README.

## Outcome

Plan judged well-structured and executable as separate slices, with one severe internal contradiction and eleven contract/consistency gaps. All twelve findings accepted and applied.

## Findings and dispositions

1. **[High] Re-litigation contradiction.** The Model claimed decisions 1 and 6 were "not open for re-litigation during execution" while Phase 1 exists to test the hypotheses under them (H3, H5) and claimed findings could re-scope later phases. *Applied:* Model preamble rewritten — decisions are user-settled bets, not axioms; a falsifying eval result halts execution and returns to a plan conversation with the user (same rule execute already applies); executors get no silent-redesign license. Phase note now distinguishes findings within the model (re-scope directly) from findings against it (halt and return).
2. **[High] Plan-folder `NN` collision under concurrent build agents.** *Applied:* DESIGN.md — uniqueness from slug, `NN` best-effort ordering only, the PR marker line is the sole mechanical location mechanism, nothing scans by number.
3. **[Medium] Acceptance criterion demanded eval coverage "per testable hypothesis" while Phase 1 scopes only H2/H3/H5.** *Applied:* criterion narrowed to H2/H3/H5 with per-hypothesis findings notes stating what result changes which decision; H1/H4/H6 given explicit validation routes (observational, via workflow-tuning harvest) in PLAN.md and README.
4. **[Medium] `STATUS.md` in the current execute skill contradicts "nothing carries status" and no phase removed it.** *Applied:* explicit Phase 3 bullet removing STATUS.md; progressive IMPLEMENTATION.md is the recovery mechanism.
5. **[Medium] `reference.md` introduced without a named consumer, violating the plan's own artifact rule.** *Applied:* added to the Artifact Taxonomy as a skill-scoped design record; consumers: workflow-tuning and skill revisers; not loaded during normal execution.
6. **[Medium] Phase 4's "feeding workflow-tuning" risked a core→lab dependency the partition forbids.** *Applied:* clarified in both PLAN.md and DESIGN.md — one-way artifact flow; the judgment lands in REVIEW.md, workflow-tuning harvests later, comprehensive-review never invokes it.
7. **[Medium] QA.md shape claimed as "defined" but specified in one clause.** *Applied:* DESIGN.md now specifies it — one step per user-facing acceptance criterion (criterion, entry point → action → observed result, pass/fail), free-prose findings section, undriveable criteria listed with reasons.
8. **[Medium] One-shot composition mechanism unspecified (shared context vs dispatch).** *Applied:* DESIGN.md — plan and execute run as separately dispatched contexts even within one run; handoff is the plan folder's artifacts, because inlining destroys the cold-read pressure H3 depends on.
9. **[Medium] Headless posture detection undefined, risking divergent mechanisms across Phases 2 and 3.** *Applied:* DESIGN.md — posture is declared by the invoker, never inferred; absent declaration, assume a human is reachable and hold the checkpoint.
10. **[Low] The orienting-why acceptance criterion is judgment-based but listed beside grep-checkable ones.** *Applied:* marked as a reviewer-judgment criterion verified by the slice's independent review.
11. **[Low] transcript-parser script move was ungoverned scope.** *Applied:* kept, with its rationale stated (partition hygiene — skill bodies carry instructions, not code payloads).
12. **[Low] No breaking-change note for external plugin consumers on the old folder convention.** *Applied:* Phase 5 now includes a README breaking-change callout, and it is an acceptance criterion.

## Residual risks

- The reviewer's core verdict stands as the plan's biggest execution risk even after the fix: Phase 1 must state, per hypothesis, what result would change what — the findings-note acceptance criterion now encodes that, but the Phase 1 executor still has to honor it.
- H4 and H6 have no fast feedback loop; observational validation arrives only after the pipeline runs at some volume.

## Final assessment

Plan is internally consistent after applied fixes and executable slice-by-slice against the DESIGN.md contracts.
