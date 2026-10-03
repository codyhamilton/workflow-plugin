# Candidates from failure literature (lens: how plans fail)

Sources actually consulted (web search results, not full-paper reads unless noted):
- Boehm & Basili, "Software Defect Reduction Top 10 List", IEEE Computer 34(1), Jan 2001: fixing after delivery is "often" ~100x costlier than in requirements/design; ~5:1 for small noncritical systems.
- Lutz, "Analyzing software requirements errors in safety-critical embedded systems", IEEE RE 1993 (Voyager/Galileo): main source of safety-related software errors was functional and interface requirements (summary via blog.acolyer.org/2017/12/01/...).
- Leveson, Mars Polar Lander analysis and STPA material (cs.washington.edu/homes/leveson/papers/jsr.pdf; MIT 16.863J notes): all components met requirements, but requirements omitted a known false touchdown signal. STPA treats flawed or missing requirements and unsafe interactions as accident causes; unsafe control action types: not given, given wrongly, wrong timing, stopped too soon or too long.
- NASA Mars Climate Orbiter MIB (summarised at nssdc.gsfc.nasa.gov/planetary/text/mco_pr_19991110.txt): English vs metric units across an interface; contributing: no end-to-end verification.
- Kahneman & Tversky 1979; Buehler, Griffin & Ross 1994: planning fallacy; inside view vs outside view. Students predicted thesis finish 22 days early on average.
- Mitchell, Russo & Pennington 1989 / Klein premortem: prospective hindsight raised correct identification of failure reasons by about 30% (secondary summaries only).
- Eveleens & Verhoef, "The Rise and Fall of the Chaos Report Figures", IEEE Software 27(1), 2010: Standish "success" is just estimate accuracy, one-sided; on 5,457 forecasts of 1,211 projects the Standish figures did not match reality. Consequence: do not cite CHAOS-style numbers, and do not treat "met the estimate" as quality.

Caveat on all: these studies are about human software projects. The mapping to LLM-agent plans is by analogy. Each candidate is a hypothesis to test against the repo's outcome labels.

### C1: Assumptions are listed with a verification status
- subject: both
- claim: The artifact has an explicit assumptions/unknowns section in which each item names what it is about and says either how it was verified (command, file path, observed result) or that it is unverified and which step checks it.
- failure_prevented: Work built on an unchecked belief about the environment, API, or existing code; discovered late as rework or a wrong-shaped deliverable (Mars Polar Lander: known sensor behaviour absent from requirements).
- evidence: Leveson MPL analysis (all components met requirements; requirements omitted the false touchdown signal). Lutz 1993: requirement errors dominate safety-related defects. Boehm & Basili 2001 for cost of late discovery.
- checkable_by: jev
- check_recipe: Levels: 0 = no assumptions stated anywhere; 1 = assumptions stated as prose facts with no verification information; 2 = assumptions listed, some carry a verification (path, command, or "unverified"); 3 = every load-bearing assumption listed with verified/unverified status and, for unverified ones, the step or phase that tests it.
- counterexample: A trivial one-line rename brief needs no assumptions (violates, still good). A bad plan can satisfy it with invented "verified" claims, so the check must require a concrete path or command.
- confidence: medium

### C2: Every cross-boundary interface has a named owner and a stated contract
- subject: design
- claim: For each seam between two domains, units of work, or phases, the design names the producer, the consumer, and the shape of what crosses (types, units, format, error behaviour) in one place.
- failure_prevented: Unowned interfaces: each side meets its own spec and the integration fails (Mars Climate Orbiter units; Lutz's interface requirement errors). In agent terms, two briefs implement incompatible halves.
- evidence: NASA MCO MIB summary (English vs metric across an interface, no end-to-end verification). Lutz 1993 (interface requirements a major error source).
- checkable_by: jev
- check_recipe: Levels: 0 = multiple units/domains, no interfaces mentioned; 1 = interfaces mentioned by name only; 2 = producer and consumer named, shape vague; 3 = producer, consumer, shape (including units/format/errors) and who changes it are all stated. Deterministic pre-filter: count of domains/briefs > 1 and presence of an interface/contract heading.
- counterexample: A single-domain design has no seams and is fine. A bad design can have a table of interfaces whose shapes are copy-paste noise.
- confidence: medium

### C3: Phase outcome is checked end to end, not only per unit
- subject: design
- claim: At least one phase outcome (the last at minimum) is an observable behaviour exercised across all the units that were built, stated as a command, test, or observation, rather than a conjunction of per-unit completions.
- failure_prevented: Every part passes its own check but the whole does not work (MCO lacked end-to-end verification; MPL components all "met requirements").
- evidence: NASA MCO MIB contributing cause "lack of complete end-to-end verification"; Leveson MPL.
- checkable_by: jev
- check_recipe: Levels: 0 = outcomes are "implement X, Y, Z"; 1 = outcomes per unit are checkable but none spans units; 2 = a cross-unit outcome exists but is vague ("system works"); 3 = a cross-unit outcome is named with a concrete command or observable and expected result.
- counterexample: A design for independent, parallel utilities may have no cross-unit behaviour (fine). A bad design can name an end-to-end command that does not exercise the new code.
- confidence: medium

### C4: Done evidence is an executable check with an expected result
- subject: brief
- claim: The brief's done evidence names a runnable command or inspectable artifact and the expected output or state, such that a reader could say pass/fail without judgement.
- failure_prevented: Unverifiable "done"; the worker reports success on inspection, requirement drift goes unseen until review.
- evidence: Boehm & Basili 2001 (late detection cost); Eveleens & Verhoef 2010 shows "done on estimate" is not a quality signal, so evidence must be behavioural. Otherwise speculative for agents.
- checkable_by: deterministic
- check_recipe: Done section contains a fenced or inline command (regex for backticked command or test path) AND an expected-result phrase (exit 0, output contains, file exists, N tests pass). Both present = pass; command without expectation = partial; neither = fail.
- counterexample: A brief whose command is `true` passes the regex (gameable); a research brief whose done evidence is a written finding is good yet fails.
- confidence: medium

### C5: Done evidence can fail before the change and pass after
- subject: brief
- claim: The done check is stated so that it would fail on the repo as it stands now (a new test, a changed output, a missing file), and the brief says what it currently shows.
- failure_prevented: Vacuous verification that passes regardless of the work (a green check that proves nothing), so wrong or absent changes are accepted.
- evidence: speculative for plans; analogous to test-first discipline and Leveson's point that satisfying stated requirements is not the same as being right.
- checkable_by: jev
- check_recipe: Levels: 0 = no check; 1 = check exists and is plausibly already true; 2 = check relates to the change but baseline unstated; 3 = baseline state stated (fails now / currently outputs X) and the check differs after the change.
- counterexample: A refactor brief whose done evidence is "existing tests still pass" is good and by design passes before and after.
- confidence: low

### C6: Out-of-scope is stated and non-obvious neighbours are excluded by name
- subject: both
- claim: The artifact lists what it will not do, naming at least one adjacent thing a reader might plausibly assume is included, and the brief's owned paths are explicit files or directories.
- failure_prevented: Scope creep and uncoordinated overlap between workers editing the same files; agents expanding to adjacent code.
- evidence: Scope creep is widely listed as a failure cause in project-failure literature, but I did not obtain a primary quantitative source in this session. Mostly speculative; owned-path overlap is directly detectable.
- checkable_by: deterministic
- check_recipe: Non-goals/out-of-scope section present and non-empty; brief owned paths parse to concrete paths with no wildcard-only root (`**`, `src/`); across briefs of one phase, owned path sets are disjoint (set intersection empty).
- counterexample: A small brief with an obvious boundary needs no non-goals; a bad plan can list generic non-goals ("no unrelated changes").
- confidence: medium

### C7: Open questions are resolved or assigned, not left dangling
- subject: both
- claim: Any question, TBD, "decide later", or "figure out" in the artifact is either absent or carries an owner and a decision point (phase or step) before the work that depends on it.
- failure_prevented: The worker guesses on an undecided point; or a phase starts whose inputs are not yet decided; requirements-defect origin (omission) turning into code.
- evidence: Lutz 1993 (omitted/incorrect requirements as primary defect origin); Boehm & Basili 2001. For agent guessing, speculative.
- checkable_by: deterministic
- check_recipe: Grep for TBD, TODO, "to be decided", "?" at sentence end in requirement text, "figure out", "if possible", "as appropriate". Count unresolved hits not accompanied within the same line by an owner/phase reference. Brief: zero unresolved hits to pass; design: hits allowed only if tied to a later phase.
- counterexample: A design in an exploratory phase can legitimately hold open questions; a bad brief can avoid trigger words while still being vague.
- confidence: medium

### C8: Failure modes are enumerated with a response (premortem)
- subject: design
- claim: The design lists specific ways the plan could fail (a concrete event, not "risks exist"), each with a detection signal or mitigation or a decision to accept.
- failure_prevented: Failures nobody looked for; late discovery of predictable problems.
- evidence: Mitchell, Russo & Pennington 1989 as cited for premortem: prospective hindsight improves identification of reasons for failure by ~30% (secondary sources only; I did not read the primary paper). Klein's premortem.
- checkable_by: jev
- check_recipe: Levels: 0 = no risks section; 1 = generic risks ("may take longer", "complexity"); 2 = specific risks without response; 3 = specific risks each naming a signal/mitigation/acceptance and tied to a phase or interface.
- counterexample: A small design with no real risk should say so briefly; a bad design may carry boilerplate risks that score 2.
- confidence: low

### C9: Unsafe-action prompts per interface (STPA-style: missing, wrong, early/late, too long)
- subject: design
- claim: For each contract or control point that matters, the design says what happens if it is absent, wrong, late, or repeated (for example failure, retry, partial write, concurrency) rather than only the happy path.
- failure_prevented: Happy-path-only designs; failures in error, ordering and timing cases surfaced in review or production.
- evidence: Leveson/STPA four unsafe-control-action types (not provided, provided wrongly, wrong timing/order, stopped too soon/applied too long); Lutz 1993 behavioural faults ~47-52% of safety-related errors.
- checkable_by: jev
- check_recipe: Levels: 0 = only happy path; 1 = one generic "handle errors" line; 2 = failure behaviour given for some interfaces; 3 = for each listed interface at least absent/invalid/ordering behaviour stated with a concrete outcome (error code, retry, abort).
- counterexample: A pure formatting or doc change has no such cases. A bad design can name the four cases with filler answers.
- confidence: low

### C10: Estimate or budget is anchored on a comparable past artifact
- subject: both
- claim: The budget or phase size cites a reference point from past work (a prior plan, commit, or measured cost for a similar change) rather than only an unreasoned number.
- failure_prevented: Planning-fallacy underestimates; budgets that are exhausted mid-task and abandoned work.
- evidence: Kahneman & Tversky 1979 and Buehler, Griffin & Ross 1994 (inside view underestimates; outside-view reference classes correct it; 22-day average thesis underestimate). Not tested on agent budgets; the repo has cost data that could test it.
- checkable_by: jev
- check_recipe: Levels: 0 = no budget; 1 = bare number; 2 = number with a rationale about this task only; 3 = number tied to a named comparable (earlier plan id, commit, or measured run) and its actual cost.
- counterexample: Budget numbers from a fixed tier rule are reasonable and consistent without a named comparable.
- confidence: low

### C11: Intent is verbatim and every phase/brief traces to it
- subject: design
- claim: The user's request is quoted without paraphrase, and each phase or deliverable can be tied to a clause of it (by explicit reference), with no deliverable that has no clause.
- failure_prevented: Requirements drift away from intent and gold-plating; paraphrase loses a constraint; deliverables nobody asked for.
- evidence: Lutz 1993 and Boehm & Basili 2001 on requirement-origin defects (omission/misstatement). Traceability benefit specifically for agents is speculative.
- checkable_by: jev
- check_recipe: Levels: 0 = no intent section; 1 = intent paraphrased; 2 = verbatim but phases do not reference it; 3 = verbatim and each phase maps to named clause(s) with all clauses covered. Deterministic part: verbatim section is a blockquote and phase sections reference clause markers.
- counterexample: A good short design for a one-sentence request has trivial traceability; a bad design can map phases to clauses incorrectly.
- confidence: medium

### C12: Brief names required reading as concrete files/sections the worker lacks context for
- subject: brief
- claim: The brief lists the exact files, symbols, or docs the worker must read, and states any repo fact the change depends on (so no search is needed to learn the key constraint).
- failure_prevented: Worker with clean context guesses at conventions or edits the wrong place; unowned knowledge (the "interface nobody documented").
- evidence: speculative for agents; analogous to unowned-interface incident findings (MCO: inconsistent communication and training between teams).
- checkable_by: deterministic
- check_recipe: Required-reading section lists >= 1 path; every listed path exists in the repo at the stated commit (file system check); symbols named exist (grep). Fail on dangling paths.
- counterexample: A brief to create a new standalone file may need no reading. A bad brief can list many real files that are irrelevant (size proxy).
- confidence: medium

### C13: Sequencing dependencies are explicit and acyclic
- subject: design
- claim: Where a phase or brief needs output from another, the dependency is named and the producer comes earlier or in the same phase; no brief consumes something no brief produces.
- failure_prevented: A worker blocked or inventing a missing input; parallel briefs that collide.
- evidence: speculative (derived from the unowned-interface cases above).
- checkable_by: deterministic
- check_recipe: Parse consumer/produces fields; build graph; check every consumed artifact has a producer in an earlier or equal phase or exists in the repo; check no cycles.
- counterexample: Fully independent briefs have no dependencies; a bad plan can have consistent but wrong dependencies.
- confidence: medium

### C14: Success is defined by behaviour, not by estimate-conformance
- subject: design
- claim: Phase outcomes describe what is observably true of the product, and none is only "within budget/on schedule/all tasks complete".
- failure_prevented: Declaring success because the plan was followed while the result is wrong.
- evidence: Eveleens & Verhoef 2010: Standish counts success as meeting estimated cost, time and scope, and its figures do not match 1,211 projects' data; steering on that definition perverts estimation.
- checkable_by: deterministic
- check_recipe: Each phase outcome line must contain an observable verb/command (runs, returns, outputs, test passes, file contains); flag outcomes matching only "complete", "implemented", "done", "delivered".
- counterexample: Doc phases may be validly "document published at path". Easy to game by adding "tests pass".
- confidence: low

## Does not work

- Length or section count as a quality proxy: longer plans are not shown to be better in any source above; trivially gamed.
- "Risk section exists": satisfied by boilerplate. Only specific, response-bearing risks (C8) carry any signal, and even that is low confidence.
- Estimate accuracy as plan quality: Eveleens & Verhoef show estimate-conformance measures are one-sided and misleading.
- Standish/CHAOS success percentages as a baseline: critiqued as meaningless; do not use for calibration.
- Boehm "100x" as a constant: the authors themselves hedge ("often", ~5:1 for small systems). It supports "catch errors at plan time" in general but cannot justify a numeric weight, and agent rework cost is unmeasured.
- Counting the number of requirements or briefs: no evidence of direction.
- Mentioning STPA or premortem vocabulary: keyword presence is gameable; only concrete content counts.

## Gaps

- No primary source obtained for scope creep as a measured cause; claims here are plausible, not evidenced.
- Premortem 30% figure comes from secondary web summaries; primary paper not read.
- Lutz 1993 percentages for interface errors were not retrievable in this session.
- None of the literature is about LLM-agent plans. Whether the failure modes transfer (for example, unstated assumptions causing worker guessing) must be tested on the repo's outcome labels.
- Did not determine how these candidates correlate with each other; C1, C7, C9 may overlap.
