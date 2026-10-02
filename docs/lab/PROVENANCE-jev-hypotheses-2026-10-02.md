# Human provenance — Jev workflow hypotheses

**Source:** Cody's messages in this conversation, 2026-10-02 (Australia/Brisbane).  
**Status:** human input preserved verbatim below. The [agent-written hypothesis](JEV-HYPOTHESES.md) is a separate synthesis, not a replacement for these statements.

## Human input 1 — parent hypotheses

> I'd like to retune a bit and ground the hypothesis we are working from, from which all the research is meant to follow on from
>
> Our hypothesis:
> 1. Jev can help agents within a workflow make cheap decisions that will reduce LLM effort at specific structural decision points in a design->execute workflow. These are the gates between phases: exit from design, exit from refine, exit from build. Cheap analysis at these points will let us decide if we are confident of completion and can move to next phase, or it needs more work. We theorise that this will improve the quality of produced work and sometimes lead to less rework, and sometimes lowered cost due to work rightsizing (agent remit size), and sometimes reduce the number of reviews we subject work to.
> 2. Jev can help avoid agents blowing past the ideal session length windows to optimise agent cost. Sessions which go beyond 75 turns start to become cost inefficient due to cache read accumulation. It quickly becomes desirable to stop, compact or hand off to a new agent. Jev can help us avoid hard stops, by having it identify signals that will determine if work is nearly complete (or conversely is likely to run long), so we can decide if we steer the agent to ending with a message, or let it continue a bit longer.

## Human input 2 — correction to the session study

> Now the way the agents started this research I felt went down a suboptimal path. My judgement for the session length intervention is that we can't simply ask Jev "is this session going to go long". What we would do is find signals that could help predict whether work is likely to complete soon or run long. This could be n signals, not just one. E.g. one might be if tests have already passed. If this is something that typically happens within 10 turns of a session ending, that is focused on engineering work, then it's a signal. Jev is asked if the signal is present and returns a confidence rating. We collate all the signals into an overall rating that is like a confidence bar - if it passes, we let it run. Then in next 15 turns we do it again - this time we discount the confidence slightly, but if it still passes, it continues.
>
> The trick is theorising signals and then testing whether those signals accurately correlate to long running or nearly-finishing sessions. And testing these signals against different combinations of input state and matcher language to find the ideal combination - not easy, requires testing many variants. But this is cheap and we can do hundreds of thousands of tests for minor cost.
>
> So our work involves LLMs running qualitative analysis, theorising and building an inventory of candidate signals, then trialing variants of how we present that to jev, capturing those signals we find having fruitful correlations

## Human input 3 — structural boundary judgements

> For the phase decision boundaries I feel this is a much simpler problem, but the difficulty is we have a much smaller corpus of plans to test it against. However initial accuracy is much less important. Even a small drop in the amount of agent work will vastly outweigh the cost per jev call, so our success ratio only needs to be small. This leads us to conservatism - relying only on high confidence answers to strictly limit false positives. Better to miss many opportunities for no net negative outcome, than false positives causing misalignment. 
>
> I think also here it's not sufficient to ask "is this rightsized" as a brief. It's probably closer to provide the briefs and ask it to provide a size rating for each (float not categorisation) along with the scope of files required and then use this to priortise what we refine down further. The benefit is what we decide _not_ to review there, not what we review
>
> For design exit I wonder if a simpler test is sufficient - we ask a set of simple language yes/no questions on whether the design is addressing certain criteria, if the phase outcomes and brief success criteria are measurable, well defined and justified (not out of the air number). These provide back a set of confidence answers, which just becomes a bar to hit. Again simply having a low success rate is not a failure, more it's iterative minor benefits that nonetheless are worth the low decision cost

## Human input 4 — methodology and evidence priority

> Ok now lets take this to the next point. We need to design our methodology - I think a substantial amount is there already but lets clean up and refocus. We've had a few pivots already and this can create noise for agents picking this up

> The most valueably docs we have are our test results. Theories and plans are great but we have to ground everything in lab proven tests

> The way I want to treat this is we start with theory. we validate this against wide research. We consolidate this into a refined thesis. Then we test the thesis, analyse results and reach accepted facts.

> The reason for the white paper approach is we reach a consolidated set of facts that are all backed with data. What _does not_ work is just as important as what works. It helps narrow our decisions later and means we don't waste time trying the same failed things over and over

> Previous attempts at this tried too hard to reach a perfect design before attempting testing and validation, but this is the opposite. You simply can't theorise into a correct design, you have to loop and test and loop. You have to be willing to burn resources to fail

> A lot of what I'm describing is in fact completely abstract and probably best encapsulated in a white paper skill

> Go tighter then, lets start at 60 turns given our ideal window is ~50 or under

## Human input 5 — hook-event state track (2026-10-03)

> Another, perhaps harder approach would be to not use full transcripts, but instead use the information available in the hooks we have. E.g. we can collect UserPromptSubmit and PostToolBatch, pass these to Jev and so contain our state just to "what the user said and what the agent is doing" rather than full output. This simplifies input data to Jev since we no longer have to rely on transcript segments, but it changes the signals we will test and the state we decide to pass. E.g. we might keep the last 5 tool calls, or all user prompts. Calling jev with such small state is cheap enough we could do it more often, and with tighter scope

Agent treatment: H2 track B in [`JEV-HYPOTHESES.md`](JEV-HYPOTHESES.md) and the matching section in [`JEV-METHODOLOGY.md`](JEV-METHODOLOGY.md). Open: which state window, which signals survive without outputs, and the call cadence are all untested.

## How the synthesis maps to the input

| Human phrase | Agent-written treatment | Interpretation still open |
|---|---|---|
| “exit from design, exit from refine, exit from build” | H1 uses exactly these three structural gates. | The specific state, question, and action at each gate need trials. |
| “sometimes” less rework, lower cost, fewer reviews | H1 treats these as separate possible effects to measure. | Which effects occur, and on which tasks, are unknown. |
| “find signals” before asking Jev | H2 orders qualitative discovery and outcome association before Jev matcher trials. | The signal inventory is not yet signed. |
| “if tests have already passed” | H2 keeps this as a candidate engineering signal, not a validated one. | Its timing and predictive value require data. |
| “confidence bar - if it passes, we let it run” | H2 describes a continuation-confidence policy. | The signal weights, bar, and treatment of missing signals are not specified by the human input. |
| “in next 15 turns ... discount the confidence slightly” | H2 describes a re-check with modest discount. | The discount formula and magnitude are not specified by the human input. |
| “different combinations of input state and matcher language” | H2 separates signal validity from Jev state/wording optimisation. | Trial grid, hold-out corpus, and call budget remain to be set. |
| “relying only on high confidence answers to strictly limit false positives” | H1 defaults to the current workflow when confidence is low or absent. | The confidence threshold and acceptable false-positive rate require evidence. |
| “size rating for each (float not categorisation) along with the scope of files required” | H1 refine-exit asks for continuous per-brief size and expected file scope. | Rating scale, file-scope representation, and validation against actual work remain open. |
| “The benefit is what we decide _not_ to review” | H1 treats avoided low-value brief review as the prospective saving. | Skipped-review quality must be checked, especially on a small corpus. |
| “simple language yes/no questions” with “a set of confidence answers” | H1 design-exit tests separate criteria, each answered with confidence before a conservative advance decision. | Exact criteria, calibration, and combination rule remain open. |
| “start with theory ... wide research ... refined thesis ... test ... analyse results ... accepted facts” | The [`white-paper` skill](../../plugins/workflow-lab/skills/white-paper/SKILL.md) uses these as the research stages; the [Jev methodology](JEV-METHODOLOGY.md) adds domain-specific tests. | The scope of “wide research” and acceptance bars for each thesis are set per study. |
| “What _does not_ work is just as important as what works” | The white-paper skill requires supported, failed, null, and inconclusive results with data and decision consequences. | A failure remains bounded to its tested population, instrument, and conditions. |
| “loop and test and loop” and “willing to burn resources to fail” | The white-paper skill allows early exploratory probes and repeated theory revisions, with short test cards and recorded failures. | The spend limit for a wave is set by its expected learning value, not a requirement for a perfect design. |
| “start at 60 turns” and “ideal window is ~50 or under” | H2's first candidate observation moves to turn 60, with later looks around 15 turns apart. The 75-turn cost concern remains the original motivation. | The ideal window and 60-turn intervention benefit still require empirical cost and outcome testing. |

The prior exact-exit, rating-to-fire, and stop-confidence research documents remain on disk as research history. Their presence does not turn them into Cody's stated starting hypothesis above.
