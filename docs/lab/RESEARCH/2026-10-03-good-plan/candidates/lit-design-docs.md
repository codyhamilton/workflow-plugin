# Candidates from design-doc / ADR practice (lens: lit-design-docs)

Sources actually consulted (web search summaries, this session):
- Ubl, "Design Docs at Google": https://www.industrialempathy.com/posts/design-docs-at-google/
- Nygard, "Documenting Architecture Decisions" (2011), as summarized by arc42: https://docs.arc42.org/tips/9-5/
- Rust RFC template: https://github.com/rust-lang/rfcs/blob/master/0000-template.md
- Kubernetes KEP template / KEP-1194 production readiness review: https://www.kubernetes.dev/resources/keps/1194/
- Parnas 1972, "On the Criteria To Be Used in Decomposing Systems into Modules" (via https://blog.acolyer.org/2016/09/05/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/)
- Amazon PR/FAQ (secondary summaries only): https://www.koji.so/docs/working-backwards-pr-faq-guide
- Review-effectiveness figures (secondary, uneven quality): https://accendoreliability.com/software-defect-phase-containment/

Note on evidence: these practices are mostly craft guidance, not controlled studies. Where I say `speculative` there is no outcome data, only a practitioner template that asks for the thing.

### C1: Non-goals are named and are real candidates
- subject: design
- claim: The design lists at least one explicit non-goal that is a plausible in-scope item (not a negated goal like "must not crash"), each with a one-clause reason.
- failure_prevented: Scope creep; workers or refiners building adjacent work; reviewers unable to tell "forgotten" from "excluded".
- evidence: Ubl, Design Docs at Google: non-goals "aren't negated goals ... but things that could reasonably be goals, but are explicitly chosen not to be goals." Practitioner guidance, no outcome data. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 no non-goals section or content; L1 non-goals present but only negated goals/boilerplate; L2 at least one plausible-but-excluded item; L3 each non-goal also says why excluded or where it goes instead.
- counterexample: A tightly scoped one-phase bugfix design can have no sensible non-goals and still be good. A bad design can list padded non-goals ("won't rewrite the OS").
- confidence: medium

### C2: Alternatives considered with a reason for rejection tied to a stated constraint
- subject: design
- claim: The design names at least one rejected alternative to its main solution shape and gives a rejection reason that references a goal, constraint, or measured fact stated elsewhere in the design.
- failure_prevented: Refiner or worker silently re-deciding the settled question; later "why not X?" rework; anchoring on the first idea.
- evidence: Ubl: the design doc is where trade-offs and "alternative designs and why they were not chosen" are written; Rust RFC template section "Rationale and Alternatives" asks "why is this design the best in the space of possible designs?"; Nygard ADR keeps rationale so later decisions do not defeat earlier ones. No outcome data. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 no alternative; L1 alternative named without reason; L2 reason given but generic ("more complex"); L3 reason cites a specific stated constraint/goal/fact.
- counterexample: Strawman alternatives satisfy L3 wording while being fake. A design for a mandated approach has no real alternatives.
- confidence: medium

### C3: Each phase outcome is an observable check naming the command or artifact that proves it
- subject: design
- claim: Every phase has an outcome stated as something observable (a command with expected result, a file/endpoint/test that exists and its expected behavior), not an activity ("implement X", "refactor Y").
- failure_prevented: Unverifiable "done"; phases closed on effort rather than result; verifier guessing what to check.
- evidence: Kubernetes KEP template requires per-stage graduation criteria and a test plan before sign-off (KEP-1194 / release signoff checklist). Task context in TASK.md names unverifiable "done" as a downstream failure. Direct outcome data: none. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 outcome is activity or missing; L1 states a state change but no way to observe it; L2 observable but check method implicit; L3 names the concrete command/test/artifact and the expected result.
- counterexample: "`make test` passes" is L3 but proves little if the tests do not touch the change. See Does not work.
- confidence: high

### C4: Contracts at boundaries are stated as shapes, not prose
- subject: design
- claim: For each boundary between domains/owners, the design gives the interface in concrete form (signature, schema, message fields, file format, or example payload) including error/absence behavior.
- failure_prevented: Two workers implementing both sides of an interface differently; integration rework; workers inventing the contract.
- evidence: Parnas 1972: modules are separated by interfaces that reveal as little as possible so parts can be built in parallel with "little need for communication"; this only works if the interface is specified. Contract-first practice (OpenAPI etc.) is the same idea. Parnas is argument, not measurement.
- checkable_by: jev
- check_recipe: L0 boundary mentioned with no interface; L1 interface described in prose only; L2 names fields/signatures but omits errors/edge behavior; L3 concrete shape plus failure behavior.
- counterexample: A design where one worker owns both sides needs no boundary contract. A bad design may paste a signature that does not match the code.
- confidence: medium

### C5: Each decision to hide is named (the secret of each module)
- subject: design
- claim: For each domain/module, the design states what decision it encapsulates (what may change without touching other modules), or states the boundary rule that decides ownership.
- failure_prevented: Boundaries drawn along processing steps or file layout so one change fans out across owners; overlapping ownership between briefs.
- evidence: Parnas 1972: start with difficult or likely-to-change decisions and give each its own module; decomposing by processing order is the worse criterion. Argument plus a small worked example, not a study.
- checkable_by: jev
- check_recipe: L0 no boundary rationale; L1 modules listed by name only; L2 responsibility stated per module; L3 each module states the decision it hides and what depends on it.
- counterexample: A small design with a single module has nothing to hide. Plausible-sounding "secrets" are easy to write falsely.
- confidence: low

### C6: Every requirement or user-intent item maps to a phase outcome (and nothing in phases lacks intent)
- subject: design
- claim: Each distinct ask in the verbatim user intent is covered by at least one phase outcome, and each phase outcome traces to an ask.
- failure_prevented: Missing scope discovered at review or after delivery; gold-plating phases with no requirement behind them.
- evidence: Requirements defects of incorrectness/incompleteness are the largest and costliest class (reported 61% in one summary, see accendoreliability link; secondary source, weak). Traceability is standard requirements practice. Medium on mechanism, weak on numbers.
- checkable_by: jev
- check_recipe: L0 intent items not enumerable or mostly uncovered; L1 some uncovered; L2 all covered but mapping implicit; L3 explicit mapping and no orphan phases.
- counterexample: Exhaustive 1:1 mapping of a badly decomposed intent still yields a bad design.
- confidence: medium

### C7: Unresolved questions are listed with an owner/resolution point, and none is hidden in prose
- subject: design
- claim: Open questions appear in one labeled place, each saying who or what (which phase, which experiment) resolves it; the design contains no unlabeled "TBD", "maybe", or "to be decided" elsewhere.
- failure_prevented: Workers guessing at undecided points; refiner discovering gaps late and bouncing the design.
- evidence: Rust RFC template "Unresolved Questions" separates what is resolved before merge from what is resolved during implementation. Process guidance only. speculative as to effect size.
- checkable_by: deterministic
- check_recipe: grep for TBD/TODO/"to be decided"/"maybe"/"?" outside the open-questions section = violations; each listed question must contain a resolver (phase id or named owner).
- counterexample: A design with zero open questions is fine; a design with a section that lists vague questions satisfies the grep.
- confidence: medium

### C8: Risks and failure modes are stated with a mitigation or detection step
- subject: design
- claim: The design lists specific ways it can fail (not generic risk words), each with how it is detected or rolled back.
- failure_prevented: Surprises in production; no rollback path; same class of failure repeating without a check.
- evidence: Kubernetes production readiness review (KEP-1194) requires features be observable, supportable, and "disabled or rolled back" if they cause failures. Amazon PR/FAQ asks "what can go wrong?" (secondary summary). Rust RFC "Drawbacks": "why should we not do this?" No outcome data. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 none; L1 generic ("may be hard"); L2 specific failure, no response; L3 specific failure with detection or rollback tied to a phase.
- counterexample: Cheap reversible changes need little here. Invented risks pad the section.
- confidence: low

### C9: Brief states done evidence as a runnable check with expected output
- subject: brief
- claim: The brief's done evidence includes at least one command or inspection and its expected result, executable using only the brief and repo.
- failure_prevented: Worker declares done without proof; verifier and worker disagree on what done means.
- evidence: Same mechanism as C3 at unit level; KEP test-plan requirement. No data. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 absent or "works correctly"; L1 names a test file with no expectation; L2 command given, expected result implicit; L3 command, expected result, and what failure looks like.
- counterexample: Command exists but tests something unrelated to the changes.
- confidence: high

### C10: Every identifier the brief relies on is verifiable in the repo or in the brief
- subject: brief
- claim: Each file path, function, or symbol the brief names as existing resolves in the repo at the brief's base commit; things to be created are marked as new.
- failure_prevented: Worker with clean context hunting for or inventing nonexistent code; wrong-file edits.
- evidence: Brief consumers have "only the brief and the repo" (TASK.md). Mechanism is direct; no external study. speculative as to effect size.
- checkable_by: deterministic
- check_recipe: Extract backticked paths/symbols; test path existence and symbol grep; count unresolved that are not marked new. Zero unresolved passes.
- counterexample: A brief that cites only real paths but the wrong ones passes.
- confidence: medium

### C11: Owned paths are listed and no other brief or phase owns an overlapping path
- subject: both
- claim: Each unit lists its owned paths explicitly, and across sibling briefs of a phase the sets are disjoint (or overlap is declared with an order).
- failure_prevented: Merge conflicts; two workers changing the same file; unowned files edited out of scope.
- evidence: Parnas 1972 rationale (parallel work with little communication needs separated responsibilities). Direct consequence stated in the workflow's own briefs spec. speculative as to empirical size.
- checkable_by: deterministic
- check_recipe: Parse owned-paths lists; compute set intersections across briefs in a phase; flag non-empty undeclared overlap. For designs, check each path appears under one domain.
- counterexample: Disjoint but wrong ownership (file really needs both).
- confidence: medium

### C12: Required reading is a short list of specific sections that the changes actually depend on
- subject: brief
- claim: Required reading names specific files/sections (not "the repo" or "docs/"), and each is referenced by something in the changes or contract.
- failure_prevented: Worker missing a constraint documented elsewhere; or burning budget reading irrelevant material.
- evidence: Nygard: nobody reads large documents, so keep what must be read small and relevant. Secondary via arc42. speculative as to effect size for agents.
- checkable_by: jev
- check_recipe: L0 none or "see repo"; L1 directories only; L2 specific files; L3 specific files/sections each tied to a change or constraint in the brief.
- counterexample: A needed constraint not listed passes; a long irrelevant list passes L2.
- confidence: low

### C13: Brief includes a stop condition for when its premise is false
- subject: brief
- claim: The brief says what the worker must do (stop and report) when an assumption listed in the brief does not hold in the code, and lists at least one assumption.
- failure_prevented: Worker working around a stale design, producing wrong but plausible changes; silent scope drift.
- evidence: Plan staleness between design and code is the reason refinement exists (TASK.md context). No external source. speculative.
- checkable_by: jev
- check_recipe: L0 neither; L1 assumptions but no stop rule; L2 stop rule generic; L3 specific assumptions each with the observable that falsifies it and the stop action.
- counterexample: Trivial briefs with no assumptions.
- confidence: low

### C14: Intent is carried verbatim and the design's solution does not contradict it
- subject: design
- claim: The user's request appears verbatim, and no solution statement or phase outcome conflicts with any sentence of it.
- failure_prevented: Intent drift during design; solving a reworded problem.
- evidence: Amazon PR/FAQ and Ubl both anchor the doc on the problem statement before the solution; the "verbatim" part is this workflow's own rule. speculative.
- checkable_by: jev
- check_recipe: L0 intent missing or paraphrased; L1 verbatim present, not referenced; L2 referenced; L3 verbatim and each sentence mapped, no contradictions found.
- counterexample: Verbatim, contradictory intents by the user.
- confidence: low

### C15: Decision records carry consequences, including the negative ones
- subject: design
- claim: For each major decision the design states at least one cost or negative consequence it accepts.
- failure_prevented: Decisions presented as free; downstream workers unaware of the cost they inherit; one-sided rationale that cannot be reviewed.
- evidence: Nygard ADR: consequences section lists "all consequences ... not just the positive ones." Rust template "Drawbacks." No outcome data. speculative as to effect size.
- checkable_by: jev
- check_recipe: L0 no consequences; L1 only benefits; L2 a cost mentioned in passing; L3 each major decision lists a concrete cost and who bears it.
- counterexample: A dominant choice with no real cost; invented costs satisfy the check.
- confidence: low

## Does not work

- Length, section count, or "has all template headings." Template presence is trivially gamed and Ubl himself says the design doc should be as short as the content allows; the KEP/RFC headings do not themselves show quality.
- "Has diagrams" (C4/arc42 style). No evidence found that diagram presence predicts fewer defects; only the content matters.
- "Reviewed by N people" or peer-review count. Not a text claim, and reported review effectiveness varies from 20% to 60% in practice (secondary source above).
- Cost-of-late-defect multipliers (100x etc.) as justification. These figures are widely repeated but contested; the 5:1 figure for small systems appears in the same summary, and Menzies et al. (Empirical Software Engineering, circa 2017, "Are delayed issues harder to resolve?") report finding no strong escalation in modern projects. I did not re-fetch that paper this session. Use them as motivation only.
- "Done evidence exists" without checking it exercises the changed code (gameable by a green unrelated test).
- Reading-time or word-count budgets as a quality proxy (Amazon's six pages is a discipline, not evidence).

## Gaps

- No controlled study found that links the presence of any design-doc section (non-goals, alternatives, etc.) to downstream defect or rework rates. Everything above rests on practitioner templates and argument. Confidence ratings reflect plausibility, not data.
- No direct evidence about agent-consumed briefs from this literature; transfer from human design docs is assumed.
- Did not retrieve full text of Parnas, Nygard, or Menzies; used search summaries and the Rust template page text. Amazon details are from secondary summaries, not the book.
- Did not find studies of what design reviews catch broken down by category (interface errors vs. missing requirements).
