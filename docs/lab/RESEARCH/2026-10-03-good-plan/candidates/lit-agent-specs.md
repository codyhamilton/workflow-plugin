# Candidates from the agent-task-specification literature (lit-agent-specs)

Lens: how specification quality affects LLM coding agents. Written blind to the repo's existing criteria. Sources were fetched or surfaced by search on 2026-10-03; where I could not re-fetch a number it is marked.

### C1: Done evidence is a runnable check
- subject: brief
- claim: The brief names at least one concrete command or observable (test path, build exit code, grep, endpoint response) that, if it passes, means the work is done.
- failure_prevented: Unverifiable "done"; worker declares success on plausible-looking code.
- evidence: Anthropic Claude Code best practices (https://code.claude.com/docs/en/best-practices) says to give Claude a check it can run (tests, build, screenshot) so it can confirm success independently. SWE-bench Verified (https://openai.com/index/introducing-swe-bench-verified/) rests on tests that actually validate the described behavior.
- checkable_by: deterministic
- check_recipe: Regex the done-evidence section for a command in backticks or a test identifier/path that exists in the repo; fail if only prose ("works correctly", "tests pass" with no target).
- counterexample: A doc-only brief whose done evidence is "file X contains section Y" passes via grep, which is fine; a brief with `npm test` but no test covering the change satisfies the regex and is still bad (see C2).
- confidence: high

### C2: Done check discriminates (fails before, passes after)
- subject: brief
- claim: The brief states which check fails on the current repo and passes after the change, or says why none can.
- failure_prevented: Vacuous verification (check already passes, or passes on wrong solutions).
- evidence: SWE-bench Verified construction used FAIL_TO_PASS tests; OpenAI's annotation also flagged tests that reject valid solutions or test unrelated behavior (https://openai.com/index/introducing-swe-bench-verified/; I recall about 61% of sampled tasks had test problems and about 68% were filtered overall in combined screening, not re-fetched, page returned 403). UTBoost (https://arxiv.org/pdf/2506.09289) finds insufficient tests in SWE-bench let wrong patches pass.
- checkable_by: jev
- check_recipe: L0 no check named; L1 check named but nothing says it currently fails; L2 names check and its expected before/after state; L3 also names a negative case or a wrong-solution the check would reject.
- counterexample: Pure refactors have no failing-before test (behavior-preserving); a good brief says so and cites the existing suite as the guard.
- confidence: medium

### C3: Requirements and interfaces are stated, not left to be inferred
- subject: brief
- claim: Every name, signature, file path, or output format the work must expose and that a checker depends on is written in the brief.
- failure_prevented: Correct-in-spirit work fails the check because of an unstated name or shape; worker guesses.
- evidence: SWE-Bench Pro (https://arxiv.org/abs/2509.16941) adds human-written requirements and interface specs to each problem statement to avoid false negatives from tests expecting specific APIs; the paper reports degraded results for GPT-5 and Claude Opus 4.1 without them (exact deltas not retrieved).
- checkable_by: jev
- check_recipe: Extract identifiers the done evidence refers to; L0 none appear in changes section; L1 some; L2 all appear; L3 all appear with signature/shape.
- counterexample: A brief for a one-line bugfix needs no interface section.
- confidence: medium

### C4: No unresolved ambiguity in the problem statement
- subject: both
- claim: The text contains no open questions, TBDs, or "either X or Y" choices that the consumer must resolve to proceed; real choices are decided with a reason.
- failure_prevented: Worker guesses wrong or asks nothing and builds the wrong thing.
- evidence: Ambig-SWE (https://arxiv.org/abs/2502.13069): models do not reliably detect underspecification, and answering clarifications raised performance up to 74% over non-interactive; briefed workers cannot ask, so the brief must pre-answer. SWE-bench Verified removed issues annotated as underspecified (https://openai.com/index/introducing-swe-bench-verified/). "Ask or Assume" (https://arxiv.org/abs/2603.26233) reaches 69.40% resolve on underspecified SWE-bench Verified with explicit clarification-seeking, closing most of the gap to full specs.
- checkable_by: deterministic
- check_recipe: Grep for TBD, TODO, "?" at sentence end in decision sections, "or alternatively", "decide", "figure out", "as appropriate"; count must be zero outside a section named Non-goals or Open risks (and those must say who decides).
- counterexample: A brief can contain a deliberate "worker decides X within bounds Y"; that is bounded and fine. A brief with no flagged words can still omit a needed decision.
- confidence: medium

### C5: Context is carried in full, with decisions upstream stated
- subject: brief
- claim: The brief restates the design decisions and constraints that affect this unit (with the reasons), rather than pointing at "see design" as the only source.
- failure_prevented: Parallel workers make conflicting implicit decisions; output does not merge.
- evidence: Cognition, "Don't Build Multi-Agents" (https://cognition.com/blog/dont-build-multi-agents): principle 1 "Share context, and share full agent traces, not just individual messages"; principle 2 "Actions carry implicit decisions, and conflicting decisions carry bad results"; Flappy Bird example where two subagents built mismatched parts. Anthropic multi-agent research system (https://www.anthropic.com/engineering/multi-agent-research-system): vague delegation led to subagents misinterpreting tasks or duplicating searches.
- checkable_by: jev
- check_recipe: L0 brief only says "per design"; L1 names the design but no decisions; L2 lists the applicable decisions; L3 lists them with rationale and states which decisions the worker must not revisit.
- counterexample: Copying the whole design into every brief satisfies "full" but violates C13 (noise) and wastes budget.
- confidence: medium

### C6: Explicit scope boundary including what not to do
- subject: brief
- claim: The brief lists owned paths and states at least one thing adjacent workers or other units own that this worker must not touch.
- failure_prevented: Duplicated work, overlapping edits, scope creep, merge conflicts.
- evidence: Anthropic multi-agent research system: good delegation includes objective, output format, tool guidance, and clear task boundaries; their example had one subagent on 2021 chip crisis and two duplicating the 2025 supply chain search. https://www.anthropic.com/engineering/multi-agent-research-system
- checkable_by: deterministic
- check_recipe: Owned paths list non-empty, all resolve to existing or to-be-created paths in the repo; a "not in scope"/"do not touch" line present; owned path sets of sibling briefs in the same phase are disjoint.
- counterexample: Single-unit phases have no siblings; a nonempty exclusion line is still cheap to demand but can be boilerplate.
- confidence: medium

### C7: Required reading is minimal, named, and each item has a purpose
- subject: brief
- claim: Required reading lists specific files (or file:line / symbol) each with the reason to read it, and no more than needed.
- failure_prevented: Worker explores blindly, burns budget, or misses the one file that constrains the change.
- evidence: Gloaguen et al., "Evaluating AGENTS.md" (https://arxiv.org/abs/2602.11988): repo context files gave no significant success gain and raised inference cost over 20%; extra requirements made tasks harder; authors advise minimal requirements. They also found context files did not work as effective repository overviews. Claude Code best practices say to reference files directly and that performance degrades as context fills (https://code.claude.com/docs/en/best-practices).
- checkable_by: deterministic
- check_recipe: Each reading entry is a path that exists, plus a reason clause; flag directory-only or glob entries and entries without a reason; report count.
- counterexample: A brief with 2 well-chosen files can still omit the key one; resolvable paths do not prove relevance.
- confidence: medium

### C8: Every change in the brief maps to an owned path and every owned path to a change
- subject: brief
- claim: The set of paths mentioned in the changes section equals the owned paths set.
- failure_prevented: Missing scope (change with no owner) or silent extra edits (owned path with no stated reason).
- evidence: speculative (derived from the scope-boundary guidance in C6; no direct study found).
- checkable_by: deterministic
- check_recipe: Extract path tokens from changes and owned-paths sections; compute set difference both ways; pass when empty.
- counterexample: A brief where changes are expressed as symbols ("add X to the router") with no paths gives a false failure.
- confidence: low

### C9: Each design phase closes with an outcome that is observable
- subject: design
- claim: Each phase states an outcome as a behavior or artifact a third party can observe, with the means of observing it.
- failure_prevented: Phases that complete without the intended capability; unverifiable phase boundaries.
- evidence: Same basis as C1 at design level (Claude Code best practices on runnable checks; SWE-bench Verified's insistence on valid tests). No study measuring phase-level outcomes in plans found: speculative for the design-level application.
- checkable_by: jev
- check_recipe: L0 outcome is an activity ("implement X"); L1 outcome is a state without a means to observe it; L2 observable with a named check; L3 observable with a named check that the briefs' done evidence composes into.
- counterexample: Early scaffolding phases may only have "builds and existing tests still pass", which is weak but honest.
- confidence: medium

### C10: User intent preserved verbatim and every requirement in it is traced
- subject: design
- claim: Each distinct requirement in the quoted user intent appears in at least one phase outcome or is explicitly deferred with a reason.
- failure_prevented: Requirements silently dropped between request and design (missing scope).
- evidence: Ambig-SWE (https://arxiv.org/abs/2502.13069) and Cognition principle 1 (https://cognition.com/blog/dont-build-multi-agents) both locate failures in information lost between requester and doer; direct measurement for plans not found: speculative.
- checkable_by: jev
- check_recipe: Small LLM lists requirements in the intent block (atomic clauses), then for each finds a phase outcome or deferral. L0 under 50% traced; L1 50-79%; L2 80-99%; L3 100%.
- counterexample: Intent that is itself vague yields a requirement list that traces trivially.
- confidence: medium

### C11: Contracts between units are written down once
- subject: design
- claim: For every boundary where two units/phases exchange data or calls, the design gives the shape (names, fields, errors) in one place that briefs can quote.
- failure_prevented: Independently built units that do not integrate; conflicting implicit decisions.
- evidence: Cognition principle 2 (conflicting implicit decisions) at https://cognition.com/blog/dont-build-multi-agents; SWE-Bench Pro interface specs (https://arxiv.org/abs/2509.16941). No direct plan-level study.
- checkable_by: jev
- check_recipe: Identify cross-unit interactions from phase text; L0 none described; L1 interaction named without shape; L2 shape given; L3 shape plus error/edge behavior and owner.
- counterexample: Single-owner designs have no contracts to state.
- confidence: medium

### C12: Budget and stop condition stated in proportion to the task
- subject: brief
- claim: The brief gives a budget (turns, files, time, or tokens) and says what to do when it is hit (stop and report, not continue).
- failure_prevented: Runaway cost, unbounded exploration, silent partial work.
- evidence: Anthropic multi-agent research system embeds effort-scaling rules in prompts ("simple fact-finding requires just 1 agent with 3-10 tool calls") because agents overinvest on simple queries; reports about 15x token use for multi-agent. https://www.anthropic.com/engineering/multi-agent-research-system. AGENTS.md study shows over 20% cost increase from extra context (https://arxiv.org/abs/2602.11988).
- checkable_by: deterministic
- check_recipe: Budget field is a number with unit; a stop/report-back instruction exists.
- counterexample: A number copied from a template satisfies it with no relation to the task.
- confidence: medium

### C13: Brief contains no restated repo boilerplate
- subject: brief
- claim: The brief does not duplicate repo-wide conventions already in the repo's agent context file or code (style rules, general architecture tours).
- failure_prevented: Wasted context; dilution of the task-specific instructions; extra cost and harder tasks.
- evidence: Gloaguen et al. (https://arxiv.org/abs/2602.11988): context files increased cost over 20% without significant gains and made tasks harder through unnecessary requirements.
- checkable_by: jev
- check_recipe: L0 more than half of text is general conventions; L1 a section of general guidance; L2 only task-specific plus a pointer; L3 same and every constraint is tied to a changed path.
- counterexample: A repo with no agent context file may need a one-line convention in the brief.
- confidence: low

### C14: Verification is not left to the worker's own judgment of its work
- subject: both
- claim: The done evidence can be produced and judged by someone other than the author (a command output, a diff property), with no "worker confirms".
- failure_prevented: Self-reported success with no independent check.
- evidence: Claude Code best practices (https://code.claude.com/docs/en/best-practices) on runnable checks; UTBoost (https://arxiv.org/pdf/2506.09289) shows weak checks admit incorrect patches. Overlaps C1.
- checkable_by: deterministic
- check_recipe: Flag done evidence phrases of self-attestation ("verify that", "ensure", "confirm") with no accompanying command or file/pattern.
- counterexample: UI work may need a screenshot a human compares.
- confidence: low

### C15: Consumer stated and the text is addressed to it
- subject: brief
- claim: The brief names who consumes its output (next unit, phase gate, reviewer) and the form the output must take for them.
- failure_prevented: Output in a shape the consumer cannot use; rework at handoff.
- evidence: Anthropic multi-agent research system lists output format as part of a good delegation (https://www.anthropic.com/engineering/multi-agent-research-system). Direct study of briefs: speculative.
- checkable_by: deterministic
- check_recipe: Consumer field non-empty and references an existing unit/phase id or role; output form (file path, report fields) present.
- counterexample: Terminal units' consumer is the user; a field saying "user" is trivially true.
- confidence: low

## Does not work

- Length or word count of a brief or design: AGENTS.md study (https://arxiv.org/abs/2602.11988) shows more context raises cost without gains; longer is not better, and shorter may omit interfaces (C3).
- Counting sections or checklist items present: gameable by filling headings with boilerplate. Presence checks should be paired with content checks (paths resolve, commands exist).
- "Brief is clear" or "design is well-reasoned" as a holistic rating: the SWE-bench Verified annotation worked because it used specific questions with severity levels, not a general quality score.
- Number of phases or units: no evidence tying count to outcome. Cognition's argument is about shared context, not count.
- Presence of a test command alone: SWE-bench test-insufficiency findings (UTBoost) show a passing command can be uninformative; hence C2.
- Detailed step-by-step implementation instructions: sounds like thoroughness, but I found no evidence it helps; over-specifying how can encode wrong decisions and conflicts with the AGENTS.md finding on unnecessary requirements. Unfalsified, treat as speculative either way.

## Gaps

- No study measures planning artifacts (designs/briefs) directly against downstream rework; all evidence here is from issue/task statements, benchmarks, and agent-context files, applied by analogy.
- I could not re-fetch the OpenAI SWE-bench Verified page (403); the filtered percentages quoted in C2 are from memory and should be verified before use.
- SWE-Bench Pro's ablation deltas and the Ambig-SWE per-model numbers were not retrieved, only the headline claims.
- Spec-driven-development tooling writeups and the Anthropic/OpenAI delegation guidance beyond the sources above were not reviewed; no empirical evidence found for them.
- Whether a small LLM can reliably apply C4/C10 rubrics is untested.
