---
name: white-paper
description: Research a workflow or product hypothesis through iterative tests and write an evidence-backed white paper that consolidates supported, failed, null, and open findings. Use when the user wants a research methodology, lab study, or white paper; not for an ordinary implementation plan.
---

# White paper research

Produce a durable set of **facts backed by test data** that narrows later decisions. Preserve the human's original theory separately from agent synthesis when the distinction matters. The path is **theory → wide research → refined thesis → test → analysis → accepted facts**, repeated as evidence changes the thesis. Begin testing while the design is still rough. A useful failed test is progress.

## Work loop

1. **Theory.** State the proposed mechanism, decision it would change, expected outcome, plausible counterexamples, and what could show it is wrong. Keep hypothesis separate from observed fact.
2. **Wide research.** Read existing lab results first, including failures and nulls. Inspect real cases and current behavior; use external research where it bears on the mechanism. Note each source's population, instrument, and limits. Use qualitative work to generate candidate signals or explanations, not to certify them.
3. **Refined thesis.** Narrow to a specific population, input, proposed decision, comparison, outcome, and failure condition. A short test card is enough for an early probe. Avoid designing the full final policy before seeing results.
4. **Test and loop.** Run small exploratory probes, log raw rows and actual spend, analyse what failed, and revise. Be willing to spend a bounded amount to falsify a promising idea. Test many variants when cheap, while recognizing that many calls on the same cases do not create independent evidence. For a claim of general benefit, freeze the selected variant and protocol, then compare on independent or held-out cases with outcome labels that do not depend on the tested judge.
5. **Analyse.** Report the denominator, comparator, result, disagreement, missingness, failure cases, and cost. Separate whether an instrument measured the intended signal, whether the signal predicted the outcome, whether a decision rule chose well, and whether acting on it improved the real outcome. A test of one link does not establish the next.
6. **Consolidate.** Write the white paper after results exist. Give successful, failed, null, and inconclusive findings equal visibility. State what each result changes about the next decision. Loop again where evidence leaves a useful question open.

Use existing project locations for research notes, raw results, and white papers. Do not impose a new folder layout or fixed model roles. Do not treat a document called `resolved`, an accepted proposal, a working harness, or judge agreement as proof of an outcome it did not measure.

## Evidence and decision record

Keep a result register linked to raw or reproducible artifacts. For each test record the tested question and version, case population and denominator, inputs and comparator, predeclared expectation, observations, cost, validity issues, interpretation, and next decision. Preserve all attempted variants, including ones that failed to parse, returned constant answers, depended on missing state, or showed no gain.

Classify conclusions precisely:

- **Supported:** a bounded result holds on the tested population; name what still needs validation.
- **Failed:** the tested framing or policy failed its declared check; record its exact signature and avoid repeating it unchanged.
- **Null:** a valid test found no useful effect at its resolution; retain the denominator and uncertainty.
- **Inconclusive:** the test could not identify the effect because of weak labels, leakage, missing state, censoring, or too few cases; state the repair needed.

A negative result rules out only the tested formulation and conditions. A materially new formulation gets a new version and test; it does not erase the failure.

The white paper should include the originating theory and provenance, the research that shaped the refined thesis, a table of tests with direct evidence links, accepted facts with scope and limits, rejected approaches with reasons, unresolved questions, and the next experiments or decisions that follow. Label untested recommendations as hypotheses. If the paper is written before decisive tests, mark it as a research proposal and leave the fact claims open.

Runtime changes, publication, and external actions follow the user's authorization and the project's normal controls. Writing the paper does not itself authorise them.
