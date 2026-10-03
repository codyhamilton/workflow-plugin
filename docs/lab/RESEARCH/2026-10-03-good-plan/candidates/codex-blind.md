### C1: Observable design outcome
- subject: design
- claim: The design states the user-visible or operational change as an observable before-and-after outcome, including who or what receives it.
- failure_prevented: A plausible implementation is built that does not solve the user's problem.
- evidence: [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf), Appendix C asks whether requirements are complete, necessary, and traceable to stakeholder expectations; [OpenAI's Codex goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) calls for a measurable outcome and a verification surface.
- checkable_by: jev
- check_recipe: Score only the stated outcome, without judging whether it is the right outcome.
  L0: No intended change is stated.
  L1: A change is named, but its beneficiary or observable effect is absent.
  L2: Beneficiary and observable effect are stated, but the before/after difference is unclear.
  L3: Beneficiary, current behavior, and intended observable behavior are explicit.
- counterexample: A polished design can state a precise but mistaken outcome because it misunderstood the user.
- confidence: high

### C2: Cross-boundary contracts
- subject: design
- claim: For each named boundary between components or domains, the design says what crosses it and the behavior each side can rely on.
- failure_prevented: Independently implemented parts disagree at integration.
- evidence: [NASA NPR 7123.1B](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7123_001B_&page_name=ALL) requires documenting interface origin, destination, stimulus, special characteristics, and validation with both sides.
- checkable_by: jev
- check_recipe: Treat a boundary as named when the design says two parts interact; do not require a contract where the design names no interaction.
  L0: Interacting parts are named with no exchange or behavior.
  L1: The exchange is named, but its direction or expected behavior is missing.
  L2: Direction and normal behavior are described, with material input/output semantics left open.
  L3: Direction, exchanged data or call, and expected behavior are stated for every named interaction.
- counterexample: A good single-component change may have no cross-component boundary to document.
- confidence: high

### C3: Ownership of changes
- subject: design
- claim: Each proposed change has one identified owning component or domain, and shared responsibilities have an explicit owner or handoff.
- failure_prevented: Work is duplicated, omitted, or assigned to conflicting workers during refinement.
- evidence: [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf) describes allocating requirements to subsystems, people, or processes; [NASA NPR 7123.1B](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7123_001B_&page_name=ALL) requires managing interfaces across product layers.
- checkable_by: jev
- check_recipe: Judge allocation in the text, not whether the chosen owner matches the repo.
  L0: No component or domain owns any proposed change.
  L1: Some changes have owners; others are unassigned or multiply assigned without explanation.
  L2: All major changes have owners, but a named shared responsibility lacks a handoff.
  L3: Every proposed change has one owner, and every named shared responsibility has an owner or handoff.
- counterexample: A design may assign every change cleanly to the wrong components.
- confidence: medium

### C4: Phase closure evidence
- subject: design
- claim: Every phase names an artifact or observable state that will exist at its end and a way to verify that state.
- failure_prevented: A phase is declared done after activity without evidence that its intended result exists.
- evidence: [OpenAI's Codex goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) says completion should be checked against files, tests, logs, benchmarks, or other concrete evidence; [DORA's small-batch guidance](https://dora.dev/capabilities/working-in-small-batches/) says each batch should be testable and independently validated.
- checkable_by: jev
- check_recipe: Inspect every phase, including the last; a verb such as "implement" alone is not a result.
  L0: Phases have no closing result.
  L1: At least one phase lists an activity as its result or gives only a vague completion claim.
  L2: All phases name results, but one or more lacks a checkable verification method.
  L3: Every phase names a concrete result and a check that could establish it.
- counterexample: A phase can pass its stated check while missing an important user scenario.
- confidence: high

### C5: Phase dependency order
- subject: design
- claim: Where one phase needs an output from another, the design names that dependency and orders the phases accordingly.
- failure_prevented: Refinement dispatches a worker before the prerequisite contract or artifact exists.
- evidence: [DORA's small-batch guidance](https://dora.dev/capabilities/working-in-small-batches/) recommends independently completable, testable batches and rapid feedback; [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf) describes allocating derived requirements and integrating products across levels.
- checkable_by: jev
- check_recipe: Score only dependencies inferable from the design's own named inputs and outputs.
  L0: A phase explicitly needs a later phase's output with no resolution.
  L1: Dependencies are implied, but no prerequisite is identified.
  L2: Prerequisites are identified, but at least one phase lacks a clear entry condition.
  L3: Each stated dependency points to an earlier phase or a named available input.
- counterexample: A good design with one independent phase has no dependency to name.
- confidence: medium

### C6: Material failure behavior
- subject: design
- claim: For each named external interaction or state-changing operation, the design states the expected behavior when that interaction fails or the operation is interrupted.
- failure_prevented: The happy path works while retries, partial writes, or unavailable dependencies cause defects.
- evidence: [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf), Appendix C calls for complete interface and environmental requirements; [NASA NPR 7123.1B](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7123_001B_&page_name=ALL) includes interface stimulus and special characteristics in interface management.
- checkable_by: jev
- check_recipe: Assess only operations the design itself identifies; a purely static change can be marked not applicable.
  L0: Failure or interruption is ignored for all named operations.
  L1: Failure is mentioned generically without a resulting state or response.
  L2: Some named operations have failure behavior, while another material one does not.
  L3: Each material named operation has a specified response or resulting state on failure or interruption.
- counterexample: A good static documentation edit has no external interaction or state change.
- confidence: medium

### C7: Open decisions are bounded
- subject: design
- claim: Every explicit unknown that could change a contract, scope, or phase outcome has a resolution owner and a point before which it must be resolved.
- failure_prevented: An unresolved design choice becomes an implicit worker guess or late rework.
- evidence: [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf), Appendix C says unresolved values should carry rationale, a resolution action, an owner, and a deadline.
- checkable_by: jev
- check_recipe: Search for TBD, open question, assumption, depends, and equivalent language; judge only unknowns the text exposes.
  L0: A material unknown is left open with no treatment.
  L1: Material unknowns are listed but lack a resolution owner or point.
  L2: Each has an owner or resolution point, but at least one lacks the other.
  L3: Each material unknown has both an owner and a resolution point before dependent work.
- counterexample: A design can hide an unknown entirely and score well.
- confidence: medium

### C8: Brief deliverable and consumer
- subject: brief
- claim: The brief names the consumer of the work and the concrete artifact or behavior the worker must hand back to that consumer.
- failure_prevented: A worker produces plausible changes that cannot be used by the next step.
- evidence: [OpenAI's Codex goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) recommends a clear finish line and inspectable evidence; [OpenAI's Codex task guidance](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) recommends issue-like prompts with concrete components and files.
- checkable_by: jev
- check_recipe: Identify the named recipient and what they receive, without checking whether the recipient really exists.
  L0: Neither consumer nor deliverable is stated.
  L1: One is stated, or both are only generic (for example, "the team" and "the feature").
  L2: Both are named, but the deliverable's usable form is unclear.
  L3: A specific consumer and inspectable handoff artifact or behavior are stated.
- counterexample: A brief can identify a consumer and deliverable precisely yet ask for the wrong feature.
- confidence: high

### C9: Brief edit boundary
- subject: brief
- claim: The brief lists the paths or components the worker may edit and says how to handle a needed change outside them.
- failure_prevented: Parallel workers collide or a worker silently expands the task.
- evidence: [OpenAI's Codex task guidance](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) says prompts benefit from file paths and component names; [Anthropic's context engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) stresses clear, bounded instructions for agents.
- checkable_by: jev
- check_recipe: Check for an explicit editable set and an escalation or stop rule for out-of-scope edits; do not verify path existence.
  L0: No edit boundary appears.
  L1: An area is named vaguely, with no identifiable paths or components.
  L2: Editable paths or components are identifiable, but out-of-bound changes are unaddressed.
  L3: Editable paths or components and an out-of-bound rule are explicit.
- counterexample: A good exploratory brief may intentionally allow the whole repository and state that boundary explicitly.
- confidence: medium

### C10: Brief reading route
- subject: brief
- claim: The brief points the worker to the specific existing files, decisions, or interfaces needed before editing, and states what to extract from each.
- failure_prevented: A clean-context worker guesses conventions or spends its budget searching unrelated material.
- evidence: [OpenAI's Codex task guidance](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) recommends paths, component names, diffs, and relevant document snippets; [Anthropic's context engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) explains that excess context consumes attention while vague guidance lacks useful signals.
- checkable_by: jev
- check_recipe: Judge whether references are actionable and tied to a needed decision; do not verify their contents or existence.
  L0: No relevant reading is identified.
  L1: Only broad directions such as "read the repo" appear.
  L2: Specific references appear, but why they matter is unstated for at least one material reference.
  L3: Each required reference identifies a path or document and the decision, convention, or contract to take from it.
- counterexample: A self-contained one-file task may need no prior reading beyond the target file.
- confidence: medium

### C11: Brief done evidence
- subject: brief
- claim: The brief gives checks tied to its requested behavior and specifies what passing evidence the worker must report.
- failure_prevented: A worker reports completion based on code written rather than verified behavior.
- evidence: [OpenAI's Codex goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) requires completion evidence from tests, files, logs, or artifacts; [DORA's small-batch guidance](https://dora.dev/capabilities/working-in-small-batches/) calls for testable batches and feedback.
- checkable_by: jev
- check_recipe: A check may be a test, inspection, demonstration, or benchmark; it must relate to the requested outcome.
  L0: No completion check is given.
  L1: Generic "test it" or "works" language appears with no check target.
  L2: Concrete checks are given, but expected evidence or behavior is missing.
  L3: Concrete checks cover the requested behavior and name the result or artifact to report.
- counterexample: A brief can demand a passing test suite that lacks a test for the actual requirement.
- confidence: high

### C12: Single bounded work unit
- subject: brief
- claim: The brief has one coherent deliverable and explicitly separates any prerequisite or follow-on work from this worker's assignment.
- failure_prevented: The worker spends its budget on an oversized bundle and leaves an unreviewable partial result.
- evidence: [DORA's small-batch guidance](https://dora.dev/capabilities/working-in-small-batches/) recommends independently completable, testable units; [OpenAI's Codex task guidance](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) says Codex works best with well-scoped tasks.
- checkable_by: jev
- check_recipe: Judge coherence and boundary from stated deliverables, not word count or a fixed file limit.
  L0: Multiple independent deliverables are bundled without a common completion point.
  L1: One headline deliverable hides unrelated required changes.
  L2: Work is mostly coherent, but a prerequisite or follow-on is ambiguously included.
  L3: One coherent deliverable is stated and adjacent work is clearly included or excluded.
- counterexample: A migration may require several coordinated file edits yet still be one bounded, reviewable unit.
- confidence: medium

### C13: Budget and stop condition
- subject: brief
- claim: The brief gives a work budget and tells the worker what evidence or blocker to report if the budget is exhausted before the deliverable is complete.
- failure_prevented: An agent spends unbounded time or claims success after an incomplete attempt.
- evidence: [OpenAI's Codex goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) describes scoped completion contracts, budget limits, and evidence-based completion; [OpenAI's Codex task guidance](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) favors bounded tasks.
- checkable_by: deterministic
- check_recipe: Search for a numeric time, token, cost, or iteration budget plus an explicit instruction to report remaining work or a blocker when it is reached; both must be present.
- counterexample: A good brief in a platform with an enforced external budget could omit the budget from its text.
- confidence: medium

## Does not work

- **Length, section count, or file count.** These are easy to pad and can penalize a concise design for a small change. [Anthropic's context engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) says useful context is the smallest sufficient set, not necessarily the shortest set.
- **Presence of headings such as "Risks" or "Tests".** A heading is easy to add without a decision, failure behavior, or checkable evidence.
- **"No ambiguous words" as a raw keyword ban.** Words such as "fast" can be vague, but a quoted user requirement or a bounded qualitative objective can use them legitimately; [NASA's checklist](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf) treats ambiguity as a requirements-quality issue, not a document-wide word count.
- **Exactly N phases or N files per brief.** Batch independence and verification matter more than a fixed count; [DORA](https://dora.dev/capabilities/working-in-small-batches/) defines useful batches by independent value and testability.
- **"Technically correct" or "best architecture" from text alone.** These require the user request, repository, and runtime evidence, so they cannot be scored reliably from the artifact by itself.

## Gaps

- Text alone cannot verify that a design quotes the user's intent verbatim, that referenced paths exist, or that stated contracts match the current code.
- The sources support the direction of these criteria, but do not establish weights, optimal level thresholds, or predictive validity for this specific workflow. Those need comparison against downstream rework, defect, and worker-cost data.
- A criterion may be inapplicable to a small or static change; scoring should record "not applicable" rather than force a low score for absent interfaces, failure paths, or dependencies.
