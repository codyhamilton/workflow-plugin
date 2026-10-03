# Candidates: requirements engineering and work-item quality lens

Author: lit-requirements. Worked blind (did not read criteria.json, QUALITY-CRITERIA.md, or other candidates).

Source notes. Fetched/searched this session:
- ISO/IEC/IEEE 29148 (summary via search result pages, not the paid standard): nine characteristics of a good requirement: necessary, appropriate, unambiguous, complete, singular, feasible, verifiable, correct, conforming.
- Bill Wake, INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) and SMART tasks, as summarized at https://innolution.com/resources/glossary/invest/ and https://www.visual-paradigm.com/scrum/write-user-story-smart-goals
- Basecamp Shape Up ch. 6 "Write the pitch": https://basecamp.com/shapeup/1.5-chapter-06 (problem, appetite, solution, rabbit holes, no-gos).
- Cucumber "Better Gherkin": https://cucumber.io/docs/bdd/better-gherkin/ (one behavior per scenario; declarative over imperative).
- Veizaga, Shin, Briand, "Automated Smell Detection and Recommendation in Natural Language Requirements", https://arxiv.org/abs/2305.07097 (2,725 requirements, 13 financial systems; smell detection 89% precision/recall; shows smells are machine-detectable, does not measure downstream cost).
- "Characterizing Requirements Smells", https://arxiv.org/abs/2404.11106 : ambiguity and verifiability rated most severe by practitioners; ambiguity and complexity most frequent; says smells can cause delay and rework.
- A systematic mapping (found via search, https://arxiv.org/pdf/2408.10886 area; exact title not verified) reports few studies show the impact of quality defects empirically and most ignore confounders. Treat "defect X causes rework Y" as weakly evidenced across this literature.

Honest caveat: the RE literature mostly validates criteria by expert opinion and detectability, not by measured downstream cost. Every confidence below is capped accordingly. These sources address human-team requirements; transfer to LLM worker agents is an assumption (agents guess instead of asking, which plausibly makes ambiguity worse).

### C1: Done evidence is an executable or observable check
- subject: both
- claim: Each unit of work (brief) or phase (design) names its completion proof as a concrete command, test, file state, or observable output, with an expected result.
- failure_prevented: Unverifiable "done"; worker declares success on vibes; reviewer cannot reproduce.
- evidence: ISO 29148 "verifiable" characteristic (fulfilment can be proven or measured); Wake INVEST "Testable"; practitioner survey (arXiv 2404.11106) ranks verifiability among the most severe smells.
- checkable_by: jev
- check_recipe: L0 no done evidence; L1 prose assertion only ("works correctly"); L2 names a check but no expected result or no way to run it; L3 a runnable command/test/observable state plus expected outcome for each done item.
- counterexample: A refactor brief whose true proof is "diff is behavior-neutral" may legitimately cite the existing test suite passing, which scores L3 but proves little if coverage is thin.
- confidence: high

### C2: Every requirement-like statement is singular and has a pass/fail reading
- subject: both
- claim: Each stated change or outcome contains one assertion that can be judged true or false, not a bundled "and/or" list.
- failure_prevented: Partial completion reported as complete; reviewer cannot say which half failed.
- evidence: ISO 29148 "singular" and "unambiguous"; Cucumber Better Gherkin, one behavior per scenario.
- checkable_by: jev
- check_recipe: L0 outcomes are directions ("improve X"); L1 mixed, mostly compound; L2 mostly singular, a few compound; L3 all outcomes singular and independently checkable.
- counterexample: A cohesive atomic change (rename across files) is naturally one assertion with many "and" clauses in its text.
- confidence: medium

### C3: Vague-term density is low
- subject: both
- claim: The text contains few unquantified weasel words (appropriate, robust, fast, as needed, etc., TBD, should handle, where possible) in normative statements.
- failure_prevented: Worker guesses interpretation; divergent implementations; review disputes.
- evidence: Femmer-style requirements smells and Paska tool (arXiv 2305.07097) detect vague/ambiguous terms at 89% precision/recall; arXiv 2404.11106 finds ambiguity is the most frequent and most severe smell.
- checkable_by: deterministic
- check_recipe: Regex a fixed lexicon of vague terms and "TBD/TODO/etc./and so on/as appropriate"; count per 1000 words outside quoted user intent; threshold from the corpus distribution.
- counterexample: A good brief may say "robust" inside a quoted user request. A bad brief can avoid every lexicon word while remaining vague.
- confidence: medium

### C4: Explicit non-goals / out-of-scope list
- subject: both
- claim: The artifact states at least one thing deliberately excluded, with the reason or boundary.
- failure_prevented: Scope creep; worker "helpfully" edits adjacent code; missing-scope disputes.
- evidence: Shape Up ch. 6 lists "no-gos" as a required pitch element (https://basecamp.com/shapeup/1.5-chapter-06). No quantitative evidence; speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 no exclusions; L1 generic ("no unrelated changes"); L2 specific exclusions without reason; L3 specific exclusions, each naming what is excluded and why or where it goes instead.
- counterexample: A one-line typo fix brief needs no non-goals; absence is correct.
- confidence: medium

### C5: Bounded budget/appetite stated and used to constrain the solution
- subject: both
- claim: The artifact states a size or effort bound (time, steps, token budget, files touched) and the scope is fitted to it, with what to cut named if the bound is hit.
- failure_prevented: Open-ended work, cost overrun, gold-plating, worker never stops.
- evidence: Shape Up "appetite" (ch. 6): the bound is part of the problem definition and constrains the solution. Estimation research in general shows scope-to-budget fitting beats estimating open scope, but I did not verify a specific citation; speculative for agents.
- checkable_by: jev
- check_recipe: L0 no bound; L1 bound with no relation to scope; L2 bound plus scope plausibly fitting; L3 bound plus named cut line (what drops first).
- counterexample: A tiny change with a generous default budget is fine; a budget number alone is trivially gameable.
- confidence: low

### C6: Inputs are named, not discovered
- subject: brief
- claim: The brief lists every file path, symbol, interface, or doc the worker must read or may edit, so a clean-context worker needs no exploratory search to find them.
- failure_prevented: Worker guessing; edits in wrong files; wasted exploration cost; ownership collisions between parallel workers.
- evidence: ISO 29148 "complete" (all information needed present); INVEST "Independent"/"Estimable" (enough known to proceed). Agent-specific effect: speculative.
- checkable_by: deterministic
- check_recipe: Extract path-like tokens from owned-paths and reading sections; verify each exists in the repo at the brief's base commit (or is marked new); fail on empty owned paths, or on paths in changes text not listed as owned.
- counterexample: A discovery/spike brief legitimately has "find where X lives". A brief can list real paths that are irrelevant.
- confidence: medium

### C7: Referenced entities resolve
- subject: both
- claim: Every file path, function, command, and phase/brief ID cited in the artifact exists in the repo or in the artifact set.
- failure_prevented: Stale or hallucinated references; worker follows a dead pointer and invents.
- evidence: ISO 29148 "correct" and "conforming" (consistent with the real system and referenced items). Speculative as to frequency.
- checkable_by: deterministic
- check_recipe: Extract backticked paths/identifiers/IDs; resolve each with the filesystem and grep; score as resolved fraction, flag any unresolved not marked "new".
- counterexample: A design proposing new modules cites paths that do not yet exist; needs a "new" marker to avoid false failures.
- confidence: medium

### C8: Intent traceability
- subject: design
- claim: Each phase and each major contract traces to a quoted part of the user's stated intent, and every part of the intent maps to some phase or an explicit deferral.
- failure_prevented: Missing scope (intent dropped); invented scope (work nobody asked for).
- evidence: ISO 29148 "necessary" (removing it causes a deficiency) and traceability as a core RE practice; no cited quantitative evidence for LLM designs; speculative on effect.
- checkable_by: jev
- check_recipe: L0 no link between intent and phases; L1 loose theme match; L2 most phases cite intent, some intent items unmapped; L3 bidirectional: every intent clause maps to a phase or deferral and every phase cites a clause.
- counterexample: A necessary enabling phase (migration scaffolding) cites no user clause directly but is justified by dependency; allow "enables <phase>".
- confidence: medium

### C9: Phase outcome is observable from outside the implementation
- subject: design
- claim: Each phase outcome is stated as behavior or state a third party can observe (declarative), not as an activity or an implementation step.
- failure_prevented: Phase "closed" by effort rather than result; outcome tied to one implementation so refinement cannot change approach.
- evidence: Cucumber Better Gherkin: declarative scenarios describe behavior not mechanics and survive implementation change; INVEST "Valuable". Transfer to phase outcomes is by analogy.
- checkable_by: jev
- check_recipe: L0 outcome is an activity ("implement X"); L1 names a component built; L2 names behavior but not how to observe; L3 behavior plus the observation method independent of implementation.
- counterexample: An internal-infrastructure phase may only be observable via a test, which reads imperative yet is correct.
- confidence: medium

### C10: Unknowns and risks are named with a disposition
- subject: both
- claim: The artifact lists known open questions, assumptions, or risk points ("rabbit holes") and states for each what the worker or refiner should do (decide, ask, avoid, stop).
- failure_prevented: Worker silently decides a design question; late discovery of a blocker; rework after wrong assumption.
- evidence: Shape Up "rabbit holes" element (ch. 6). INVEST "Estimable": inability to estimate signals unresolved unknowns (Wake). No quantitative data; speculative as to effect.
- checkable_by: jev
- check_recipe: L0 none and complex task; L1 generic risks ("may be hard"); L2 specific risks without handling; L3 specific risks each with a decision or stop rule.
- counterexample: A trivial brief has no risks; "none" is correct. Invented risks can be padding.
- confidence: low

### C11: Brief is a vertical slice with a single reason to change
- subject: brief
- claim: A brief's changes live in one cohesive area (single consumer or single owned-path cluster) and deliver one outcome, rather than touching unrelated layers.
- failure_prevented: Briefs too large for one clean context; merge conflicts among parallel workers; partial failure blocks everything.
- evidence: INVEST "Small" and "Independent" (Wake). Story-splitting guidance in general; no measured effect for agent briefs; speculative for agents.
- checkable_by: deterministic
- check_recipe: Count distinct top-level directories among owned paths and number of distinct "changes" items; flag above corpus percentile; check owned-path sets of sibling briefs for overlap (should be empty).
- counterexample: A cross-cutting rename is legitimately wide yet single-outcome. A small brief can be the wrong slice.
- confidence: low

### C12: Dependencies and order between units are explicit and acyclic
- subject: design
- claim: Phases state what each depends on and what it unblocks, and the dependency graph has no cycles or hidden shared owned paths.
- failure_prevented: Parallel work collisions; a phase starts before its prerequisite; deadlock.
- evidence: INVEST "Independent"; ISO 29148 "consistent" across a set of requirements (set-level characteristics). Speculative for agents.
- checkable_by: deterministic
- check_recipe: Parse phase dependency lines; build the graph; fail on cycle, on undefined referenced phase, or on two phases claiming the same path without an order edge.
- counterexample: A strictly linear 2-phase design needs no explicit graph; absence of the field is fine if order is obvious.
- confidence: medium

### C13: Contract examples are concrete
- subject: design
- claim: Each interface or contract in the design includes at least one concrete example (signature, payload, input/output pair, or file schema), not only a description.
- failure_prevented: Producer and consumer implement different readings of the contract; integration rework.
- evidence: Gherkin/BDD "specification by example" (Cucumber docs, https://cucumber.io/docs/bdd/); ISO 29148 "unambiguous". Effect size not verified; speculative.
- checkable_by: deterministic
- check_recipe: For each contract section, require a code fence or a table with example values; count contracts lacking one.
- counterexample: A code fence may hold pseudo-code that restates the prose and adds nothing; a purely behavioral contract may need no schema.
- confidence: low

### C14: Intent is preserved verbatim and separated from interpretation
- subject: design
- claim: The user's request appears as an unedited quote, and interpretations or assumptions about it are labeled separately.
- failure_prevented: Intent drift through paraphrase; refiner and worker optimize a reworded goal.
- evidence: ISO 29148 "appropriate"/"correct" (stated at the right level, traceable to stakeholder need). Speculative for agents; matches the workflow's own design rule.
- checkable_by: deterministic
- check_recipe: Compare the quote block to the stored original prompt (exact string match); verify an assumptions section exists and does not contain text duplicated into the quote.
- counterexample: A quote can be intact while the design ignores it.
- confidence: medium

### C15: Acceptance examples include a negative or edge case
- subject: both
- claim: Done evidence or outcome includes at least one failing-path or boundary case (error, empty input, permission denied), not only the happy path.
- failure_prevented: Defects in error handling pass review; "done" proves only the demo path.
- evidence: Gherkin practice of scenario coverage including exceptions (Cucumber docs, Better Gherkin); ISO 29148 "complete". No measured effect cited; speculative.
- checkable_by: jev
- check_recipe: L0 no cases; L1 happy path only; L2 one edge case mentioned, no check; L3 negative/edge case each with a concrete check and expected result.
- counterexample: Pure documentation or config briefs have no meaningful negative path.
- confidence: low

## Does not work

- Length or word count of design/brief (either direction). Size proxy; long can mean thorough or padded; INVEST "Small" is about scope, not text.
- Presence of section headings or template conformance alone. Gameable by filling headings with filler; useful only as a precondition for the content criteria above.
- A done-evidence field "exists". Weaker than C1; "tests pass" with no named test satisfies it.
- SMART as a whole checklist (Specific, Measurable, Achievable, Relevant, Time-bound). Achievable and Relevant are not text-checkable; Time-bound maps poorly to agent work (see C5 for the usable part).
- INVEST "Estimable" scored by whether an estimate number is present. Gameable; the underlying value (unknowns resolved) is C10.
- Number of acceptance criteria. More is not better; rewards enumeration and splitting hairs.
- Gherkin Given/When/Then syntax as a requirement. Format compliance does not imply a good scenario; the transferable parts are one-behavior-per-scenario and declarative style (C2, C9).
- "Passes ISO 29148 nine characteristics" as a single holistic score. Appropriate, correct, and feasible cannot be judged from text alone without the system; only verifiable, singular, unambiguous, complete in part are usable.
- Requirements smell counts as proof of downstream cost. Detection is accurate (Paska 89%), but the mapping literature reports weak empirical evidence that smells cause measured rework.

## Gaps

- No measured link between any requirements-quality attribute and rework for LLM-agent workers; all agent transfer is by analogy. The proxy-outcome mining in the repo is the only way to test these.
- Could not access ISO/IEC/IEEE 29148 full text (paywalled); characteristics taken from secondary summaries.
- Did not find a verified citation for estimation research that says appetite-fitted scope beats estimating open scope; C5 stays low confidence.
- The title and authors of the systematic mapping study on quality-defect impact were not verified; I describe its claim only loosely and do not rely on it for any single criterion.
- Thresholds (vague-term density, directory count) need calibration on the repo's own artifacts.
- Optimal granularity of "singular" for briefs that deliberately bundle atomic changes is unresolved.
