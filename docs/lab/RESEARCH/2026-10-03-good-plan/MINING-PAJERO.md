# Mining Pajero maps: human interventions and executor complaints

Two bottom-up sources, both scrubbed (`hooklog.scrub`) before going to Flash. Anecdotal, one project, Flash-labelled: use as candidate evidence for criteria, not as validation.

## 1. Human interventions (145 rows, `interventions-classified.json`)
Types: question 33, ack_continue 29, new_task 27, scope_add 15, other 13, correction 8, clarify_intent 7, relay 6, missing_requirement 4, rejected_result 3.
Rework 20 (14%). Rework by last workflow skill: none 3/54, execute 6/31, design 5/22, refine 4/19, comprehensive-review 2/10, close-out 0/7.
Flash cause for the 20 rework rows: brief_gap 5, agent_drift 5, design_gap 4, unproven_assumption 2, arbitrary_threshold 2, none 2.
Spot-check: some ack_continue rows are wrongly flagged rework, some "prevent" text draws on assistant context, many are orchestration drift (run the phase yourself, polling waits), several are relayed messages. Cause labels are unreliable; treat counts as upper bounds.

## 2. Executor complaints about their brief (156 passages, 129 subagent transcripts)
Regex-selected assistant messages, then Flash judged "does the defect come from the TASK text". 120 parsed (36 timed out or were unparseable, not retried).
not_about_plan 78, self_inflicted 18, plan_defect 21 (9 at confidence >= 0.7, 9 distinct subagents), ambiguity 1, stale_reference 1, unproven_assumption 1.

The 9 high-confidence defects are mechanical, not judgement calls:
- Done-evidence that cannot pass as written (COORD_RANGE grep passes only if out-of-scope files are edited; a done-evidence command that contradicts itself).
- Scope self-contradiction (must remove a function that is used in a file the brief forbids editing; required plumbing lands in a file not in owned paths).
- Owned-path names a file that does not exist.
- Premise stated as fact and never checked ("G lacks cells R has" was false; pipeline emission contract contradicted the real table).
- Same-fix-in-several-places: an amendment authorised one copy of a formula, three others exist.
- Unresolved internal contradiction (a cap of 400 vs 200).

## What this says about U1 (evidentiary chain / unproven assumptions)
- Supported by direct user statements (b9eb9e9a "do not gate on arbitrary brief numbers", "10k had none"; bd4f6c0d#13 phase gates need explicit measures), but only 4 of 20 rework rows were Flash-tagged that way.
- Executors rarely name unproven assumptions (1 of 120). Humans surface them; executors surface *mechanical* inconsistencies. So U1 is a human-detected failure class, and the executor-detected class is a different, more checkable one.

## Candidate criteria that are deterministic (feed stage 5 cheap checks)
1. Every owned path exists (or is marked new).
2. Every symbol the brief removes/renames has its callers inside owned paths, or the outside callers are listed.
3. Every done-evidence command is runnable and its pass condition is satisfiable under the brief's own scope (grep-style checks name the files they cover).
4. Premises about current behaviour are tagged with how they were verified (command + date) or marked unverified.
5. A fix described for one occurrence lists all occurrences (grep result attached).
6. No two numbers in the brief disagree (caps, counts).
Criteria 1, 5, 6 are fully scriptable; 2 and 3 are partly scriptable; 4 needs Jev or a human.

## Next
Backtest criteria 1/5/6 as scripts over the Pajero briefs and check agreement with the 9 known defects; extend extraction to other projects; second-pass the 20 rework rows with human-only context.

## U2 (from Cody): implicit authority and missing scepticism
Agents treat a number in a formal acceptance criterion as binding authority. "x must not exceed 10k" triggers stop-and-ask when reality breaches it; "10k because it feels about right" would not, and "10k because we measured that it explodes above it" would stop for the right reason. Acceptance criteria are end-of-chain outputs, so an unjustified number also marks the research and direction above it as unjustified. Requiring provenance on each criterion forces the backward audit: if you can't say why it is x, re-walk the chain until you can.

Criterion candidate (C-prov): every threshold / success criterion states a provenance class (measured | derived | external | judgement) and an evidence pointer (command+date, document, or the inputs it derives from). Measured/derived without a pointer counts as unproven. Judgement is allowed but must be labelled, and labelled thresholds are advisory (flag and proceed), not gates.

Backtest plan: extract numeric thresholds from Pajero briefs' acceptance/done-evidence text; classify provenance present/vague/absent; compare absent-provenance briefs with the stop-and-ask events and rework rows (b9eb9e9a#23/#24 "10k had none" is the known positive). Falsified if provenance does not separate churn from clean briefs.
