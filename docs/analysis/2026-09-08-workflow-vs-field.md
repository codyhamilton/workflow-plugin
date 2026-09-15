# Is the cost sweet spot real, and does the workflow actually hit it?

Committed copy of the review published as an artifact at https://claude.ai/code/artifact/0978c22b-7ee9-4de1-a768-0b313c58bdc8. The artifact is the
canonical rendering (it carries the cost chart); this file is the repo record.

*workflow-plugin · critical review · 2026-09-08, extended 2026-09-15*

A review of the plan → refine → execute workflow and the two principles behind it, task focus and scope limiting, against current published practice from Anthropic, OpenAI, Cursor, GitHub, and the open frameworks (Spec Kit, Kiro, BMAD, superpowers, Ralph, Aider, Devin).

## §1 · Verdict at a glance

The architecture is mainstream and sound. The economics are right in shape but overstated in strength, and, more importantly, the sweet spot that "fundamentally underpins" the design is not encoded anywhere an agent would read it. The workflow enforces task focus on workers and forgets to enforce it on the two agents that actually blow through the budget: the execute orchestrator and refine.

| Claim | Verdict | Assessment |
|---|---|---|
| Cost is quadratic in turns | supported | Follows directly from published cache pricing. Your own garcia-music data (cache read 65 to 70% of spend) confirms it in the worker tier. |
| 50–75 turns / 100–125k is the sweet spot | partial | It is a crossover, not an optimum. Two-way split break-even lands at 35 to 75 turns depending on cold-start size and thinking volume. No published source names these numbers. |
| Decomposition is "nearly always" cheaper | unsupported | Savings past break-even are 3 to 30% and vanish with one redundant re-exploration. Anthropic's own docs put multi-agent at 4 to 7× tokens. Quality, not cost, is the stronger argument for small agents. |
| One task per agent | supported | Every leading system does this. Yours does it for workers only. |
| Three-stage flow | supported | Spec Kit, Kiro, BMAD and superpowers all have the same shape. Refine is Spec Kit's `/tasks` with a bounce contract. |
| Proxies are countable | not done | "We can count context" is true, but nothing in the skills counts, budgets, or tells a worker when to stop and hand off. |
| Execution quality vs field | ahead in places | Briefs by path, verifier ≠ reviewer ≠ fixer, exact-SHA gate, and falsifiable hypotheses are ahead of anything surveyed. Behind on test-first, worker budgets, orchestrator lifetime, and a lightweight entry path. |
| Model tiering | consistent | Cheap executors have the highest cache-read ratio, so decomposition pays earliest there; Fable's cheap reads make it the wrong model to decompose. Plan is ~45% of a run and the orchestrator's model × lifetime is the swing line. See §6. |
| Design, then phased refinement | likely better | Every plan record shows late-phase discovery. Refining one phase at a time, against real code, moves that drift out of the execute orchestrator and cuts a three-phase run ~20%, provided phases close on provable outcomes and the phase count is fixed at design sign-off. See §7. |

## §2 · The cost model, examined

### What the arithmetic says

With prompt caching, each turn reads the whole accumulated prefix at the cache-read rate and writes only the new increment. If context grows by *d* tokens per turn from a base *C₀*, the per-turn cost is linear in the turn number and the cumulative cost is quadratic. The 90% cache discount scales the quadratic term down. It does not remove it.

The chart below runs that model with a 40k cold start (system prompt, skill, brief, first code reads), 1.5k of tool output and 300 output tokens per turn, and the Anthropic multipliers of 0.1× read, 1.25× write, 5× output. Prices are in base-input units, so the curve shape holds for any model with those ratios. The ratios differ by model, and that moves the crossover: §6 reprices the same model on the fleet you actually run.

*Chart omitted in this copy; the table below carries the same series.* Cumulative cost (base-input token units) against total turns, one agent versus the same work split evenly. Each extra agent pays the 40k cold start again. Two agents overtake one at about 40 turns here; the cost-economics sweep, using Opus 5 rates and a 30k cold start, put the same crossover near 75 turns. Gains flatten past three or four agents, and with an 80k cold start the six-way split costs more than the four-way: the cold starts eat the saving.

| Total turns | One agent | Two agents | Saving | Final context, one agent |
|---|---|---|---|---|
| 20 | 0.23M | 0.26M | −14% | 76k |
| 30 | 0.35M | 0.36M | −3% | 94k |
| 40 | 0.49M | 0.46M | +5% | 112k |
| 60 | 0.81M | 0.70M | +14% | 148k |
| 100 | 1.68M | 1.28M | +24% | 220k |
| 150 | 3.17M | 2.21M | +30% | 310k |

### Where the principle is right

- **Cache read dominates the bill in the worker tier.** Your lesson 21 measured 65 to 70% of spend as cache read on composer and GLM. Sonar's public "context tax" post reports a single PR billing 156M context tokens with output at 0.19% of the total. The lever is real.
- **Quality degrades before cost does.** NoLiMa puts the effective context of GPT-4.1 at 16k and GPT-4o at 8k once lexical overlap is removed. Chroma's context-rot study shows a 30 to 60 point gap between a focused 300-token prompt and a 113k history. Anthropic's Claude Code docs state the operating assumption plainly: performance degrades as context fills. On quality grounds alone, a 100 to 125k budget is generous, not tight.
- **Fresh handoff beats resume.** Your WP1 post-mortem found a resume via SendMessage resets the cache regardless of elapsed time, costing 6 to 8× a normal call. Anthropic's long-running-agent harness reached the same conclusion from the quality side: summarization "wasn't enough", so it scopes one feature per session with a PROGRESS.md handoff.

### Where it is overstated

- **The crossover moves a lot.** With heavy thinking (5k output tokens a turn) the per-turn cost rises 1.7× over 100 turns instead of 3.8×, and cache reads are 44% of the bill rather than 89%. On Fable-class pricing, where reads are 0.025× and output is expensive, the context tax nearly disappears. The principle is strongest for exactly the cheap, thinking-light worker tier you allocate to workers. It should not be stated as universal, and it does not apply with the same force to an orchestrator on a premium thinking model.
- **Turns are the wrong unit.** Cost is context × turns. A 75-turn agent at 60k is cheaper than a 40-turn agent at 150k. The controllable lever is context growth per turn, which is tool-output verbosity. Nothing in the workflow addresses it.
- **Decomposition has a cold-start bill and a lossy channel.** A subagent does not inherit the parent's cache; its first request is a fresh write at 1.25×. Claude Code's own cost docs put agent teams at roughly 7× a standard session. A budget-controlled Stanford study (arXiv 2604.02460) found single agents match or beat multi-agent systems on reasoning tasks when thinking tokens are held equal, because each handoff is a lossy channel. Decomposition wins when units are file-disjoint and read-heavy; it loses when phases share context or the split adds coordination turns.

> **Restated principle.** Cost per unit of work is the accumulated context integrated over turns. Decomposition pays when the saved reads exceed the added cold starts, which is roughly past 40 to 75 turns for a cheap worker and later for a thinking-heavy one. Context rot argues for smaller agents than cost does. The lever you control most directly is how fast context grows, not how many turns run.

## §3 · Task focus and the proxies

### One task per agent is the field consensus

Every system surveyed lands here, in almost identical words. Claude Code: write the spec, then "start a fresh session to execute it". superpowers: "dispatch fresh implementer subagent per task". BMAD's build step one is "Start a Fresh Chat". Devin: "one Devin session for each sub-task". Anthropic's long-running harness: "work on exactly one item from PROGRESS.md per session". Ralph is a shell loop that starts a new process each iteration with all state on disk.

Your workers get this treatment. Your orchestrators do not. The execute orchestrator holds recon, sizing, brief routing, progressive IMPLEMENTATION.md, review dispatch, close-out and the PR in one context. The post-build orchestrator holds classification, review, remediation, verification, QA planning, checks, deploy proof, QA and the report. In the garcia-music run the orchestrator produced 268 parent messages across 67 dispatches, and GLM, mostly orchestration, was 23.6M tokens. That is the single largest departure from the principle, and the field has three answers to it:

- **Make the orchestrator a script.** Ralph and Claude Code's dynamic workflows keep orchestration in code so "Claude's context holds only the final answer". State lives in the dispatch list and the progress file, which you already have.
- **Keep the orchestrator but starve it.** Anthropic's rule that subagents return "a condensed, distilled summary, often 1,000 to 2,000 tokens"; Cognition's revised position that "one main loop carries state, subagents are stateless workers with narrow scope". Your briefs ask for "a short summary" with no cap.
- **Re-dispatch a fresh orchestrator per unit.** Your resume rule (dispatch list × recorded outcomes) already makes this possible. Nothing tells the orchestrator to use it before it has to.

### Proxies: yours are qualitative, the field's are countable

| System | Unit-size proxy | Kind |
|---|---|---|
| this workflow | "one main contract, a file surface it can read without exhausting its context, a done state it can verify"; disjoint paths; ~10 turns as the floor below which delegation is waste | qualitative, plus one floor |
| superpowers | each step 2 to 5 minutes; exact file paths and code; test cycle per task | time, files |
| BMAD | one story per session, about 500 lines of code | lines |
| OpenAI Codex (own repo) | changes under 800 lines; modules under 500 | lines |
| Claude Code agent teams | "a function, a test file, or a review"; 5 to 6 tasks per teammate; skip the plan if the diff fits in one sentence | deliverable shape |
| Anthropic multi-agent | delegate when a sub-task produces over 1,000 tokens of mostly irrelevant output; return 1 to 2k summaries | tokens |
| Ralph / snarktank | one story per iteration, "small enough to complete in one context window" | context |
| Devin | sub-tasks under 3 hours of human time, machine-checkable success | time |

Nobody uses turn counts as a trigger. They are monitoring signals, read from a status line or a usage command. The trigger proxies are lines, files, tokens of output, and "one deliverable". Refine's decomposition questions are the right questions, but a worker never sees a number it could check itself against, and a worker that finds itself past the budget has no instruction to stop, write a handoff, and return.

## §4 · The three-stage architecture

Plan → refine → execute is the converged shape of the field. Spec Kit runs specify → clarify → plan → tasks → implement. Kiro runs requirements → design → tasks. BMAD runs PRD → architecture → story. superpowers runs brainstorm → design doc → writing-plans → per-task execution. In each, a separate task-breakdown stage sits after design and before code, and its output is a file with exact paths, dependencies, and a parallelism marker. Refine is that stage, and its two additions, the bounce as a success condition and the disjoint-ownership hard rule, are good ones.

### What is distinctive and defensible

- **Verbatim intent.** Only Spec Kit's spec header does anything similar, recording the raw user input. Your lesson 20 natural experiment (gate prompts decaying 1199 → 213 chars inline, holding at 2800 to 3700 once moved to briefs) is better evidence for verbatim routing than anything the leaders publish.
- **The assumption ledger.** Spec Kit's `/clarify` writes a Q → A log and caps `[NEEDS CLARIFICATION]` markers at three with informed guesses for the rest. Yours is the headless-posture equivalent and adds "if wrong", which nobody else records.
- **Posture declared, never inferred.** No surveyed system states this, and several suffer for it. Keep it.
- **Close-out.** No surveyed system deletes artifacts. Spec Kit takes the opposite view: "maintaining software means evolving specifications". But OpenAI's harness-engineering post reports the failure your close-out targets: a single big AGENTS.md "became stale, agents could not tell what was still true", so they now run garbage-collection agents. Böckeler's spec-first camp treats specs as disposable input. Close-out is a defensible, unproven bet in a live disagreement. Its real risk is that acceptance criteria and briefs leave the working tree, where a future agent could have grepped them.

### Where the shape costs you

- **Three cold reads of the same code before a line changes.** Plan reads stable docs, refine does recon, every worker reads again. This is the Stanford lossy-channel objection made concrete, and it is the price of the reviewable gate. The field's mitigation is to make the upstream artifact name the files: Claude Code's spec advice is to "name the files and interfaces involved"; Spec Kit tasks carry exact paths; superpowers plans carry paths and line ranges. Your PLAN.md template has no files-or-interfaces section, so plan withholds the one thing that would make refine's recon cheap.
- **No lightweight entry.** Plan says "don't spend time deciding whether planning is warranted". Claude Code says "if you could describe the diff in one sentence, skip the plan". Böckeler's critique of spec-driven tooling, "excessive review overhead, a false sense of control", cites a Kiro spec producing sixteen acceptance criteria for a trivial bug. Post-build right-sizes by classification; plan has no equivalent absorb path.
- **Refine has no ceiling of its own.** Kiro's guidance: "a spec with 30 requirements and 100 tasks is too large; start with a minimal version, then create new specs". Refine bounces plans that are too weak. It does not bounce plans that are too big, and for a large plan refine itself, reading the whole surface and writing every brief, is the agent most likely to blow the budget.

## §5 · Execution against the field

The matrix compares the mechanics. Rows are practices the field agrees matter; the shaded column is this workflow.

| Practice | this workflow | Spec Kit | Kiro | superpowers | Ralph / Anthropic cwc | Claude Code guidance |
|---|---|---|---|---|---|---|
| Task breakdown as its own stage | refine, skippable, bounces | /tasks | tasks.md | writing-plans | IMPLEMENTATION_PLAN / PROGRESS.md | plan mode, single plan |
| Fresh context per unit | yes for workers; orchestrator long-lived | implied per phase | per task wave | fresh implementer per task | new process per iteration; no orchestrator | fresh session after spec |
| Worker direction as a file, routed by path | yes, static/dynamic split | agent reads tasks.md | agent reads tasks.md | task-brief file | PROGRESS.md read cold | inline spawn prompt |
| Countable unit ceiling | none; ~10-turn floor only | exact file paths | "single concern" | 2 to 5 minutes, paths + code | one story per context window | function / test file / review |
| Worker stop-and-handoff rule | none (only "report contradictions") | none | none | DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT | write PROGRESS.md, exit | /clear after two failed corrections |
| Report-size cap | "a short summary" | n/a | n/a | report file, not inline history | n/a | 1 to 2k token summaries |
| Test-first per unit | done evidence, run after | optional unless asked; constitution says tests first | no | mandatory red-green per step | test-results.json default false, evidence hook | "give Claude a check it can run" |
| Independent reviewer, fresh context | yes; verifier ≠ reviewer ≠ fixer | /analyze consistency | no | two-stage review, no self-spawned reviewer | evaluator with no write tools | adversarial subagent on the diff |
| Fix-loop bound | 1 cycle, then human | 3 | n/a | 5, escalate model at 4 | max-iterations | stop hook ends after 8 |
| Disjoint file ownership for parallel work | hard rule, stated as paths | [P] marker | waves | yes | single writer | "each teammate owns different files" |
| Sub-spawn control | observed leak, unruled | n/a | n/a | implementer never spawns reviewer | one builder, many readers | 3 nesting levels, 20 concurrent |
| Gate bound to exact SHA, no commit after test | yes | no | no | no | no | no |
| Artifacts at end | collapsed to one record, folder deleted | kept as living spec | kept | kept | kept | session-scoped unless saved |
| Hypotheses stated as falsifiable | yes, six in README | no | no | no | no | no |

### Ahead of the field

- **Briefs by path with a static/dynamic split.** superpowers and BMAD do the file half; nobody keeps the brief text out of the orchestrator's context on purpose. Your commit 916930a made that explicit.
- **Three-way separation of reviewer, fixer and verifier.** Anthropic's evaluator has no write tools, superpowers separates implementer from reviewer, but a distinct fresh verifier for delegated fixes is yours alone. It matches the Huang et al. and Kambhampati findings that self-critique collapses and external verification gains.
- **Exact-SHA gating and "no commit after the tested commit".** Nothing surveyed states this. Copilot's coding agent runs its own checks on its own diff but does not bind them to the merge SHA.
- **Cost harvest already feeding rules.** The WP1 post-mortem produced four skill changes (path routing, no SendMessage resume, split at long subprocess, ad-hoc fixer). That is the eval loop working without an eval harness.

### Behind the field

- **Verification comes last, not first.** Briefs carry done evidence "expressed as commands where possible", run after the change. superpowers, Harper Reed, Spec Kit's constitution and Willison all put the failing check before the change. Anthropic's harness goes further: a test-results ledger that defaults to false, and a hook that refuses to mark a test passing until the evidence file has been read.
- **No worker budget, no handoff instruction.** The brief template's report-back covers contradictions and deferred bugs. It has no status enum and no "if you are past your budget, write a handoff and stop". Ralph and cwc make the handoff the normal exit; superpowers gives the controller four statuses to route on.
- **One fix cycle may be too tight for the wrong reason.** Bounded loops are correct and yours are the tightest surveyed. superpowers keeps a bound of five but escalates to a stronger model at round four, on the theory that a second failure on the same model is evidence about the model, not only the problem. One escalated retry before HUMAN_ACTION_REQUIRED would cost little and probably clear a class of stops.
- **Context growth is unmanaged.** "Required reading, in order" is good. Nothing says "read nothing else without a reason", nothing prefers grep and ranged reads over whole-file reads, nothing truncates tool output. Sonar's framing: the cost of a read is its size times the number of turns it survives.
- **Sub-spawning is observed but unruled.** Lesson 24 notes nine of 67 workers spawned their own agents and leaked model selection. The field's answer is a single-writer rule in the worker's own brief.
- **The eval corpus is empty.** README is honest about this. But the number that underpins the design has no measurement in the loop, while transcript-parser can already emit turns and context per agent. That is the cheapest instrument available and it is not running.

One thing that is fine: skill size. SKILL.md files run 1.5k to 3.7k tokens; the execute orchestrator loads about 7.5k across its run. That is well inside the budget and inside Claude Code's own guidance on instruction-file length.

## §6 · Model choice

The analysis above priced everything in one model's units. In practice this workflow runs a mixed fleet: cheap, cheap-cache-read models (Composer 2.5, Kimi, GLM) for execution, and Opus- or Fable-class models only for planning and refinement. That changes two things. It changes where the quadratic cost actually bites, and it changes which agents the cost principle should bind to.

### The price sheet, and the one ratio that matters

What shapes a long agent's bill is not the input price. It is the cache-read price relative to everything else, because past the first few turns almost every token the model sees is a cache read. Anthropic first-party rates, Cursor and Moonshot list prices, September 2026:

| Model | Input $/M | Cache write | Cache read | Output | Read ÷ input | Cache-read share of a 100-turn agent |
|---|---|---|---|---|---|---|
| Fable 5.1 | 10.00 | 12.50 | 0.25 | 50.00 | 0.025 | 43% |
| Opus 5 | 5.00 | 6.25 | 0.50 | 25.00 | 0.10 | 75% |
| Sonnet 5 | 2.00 | 2.50 | 0.20 | 10.00 | 0.10 | 75% |
| Haiku 4.5 | 1.00 | 1.25 | 0.10 | 5.00 | 0.10 | 75% |
| Composer 2.5 | 0.50 | 0.50 | 0.20 | 2.50 | 0.40 | 93% |
| Kimi K2.6 | 0.95 | 0.95 | 0.16 | 4.00 | 0.17 | 86% |
| GLM 5.2 | 1.30 | 1.30 | 0.26 | 4.40 | 0.20 | 89% |

Three things follow, and the first is the opposite of the intuition that cheap models make the cost argument go away.

**The quadratic term is strongest on the cheap executors.** Composer's cache read is 40% of its input price, four times Anthropic's ratio, so a 100-turn Composer agent spends 93% of its bill on re-reading its own context. Your garcia-music measurement (70% for Composer, 65% for GLM, 41% for Sonnet) is this table read off a real run. Decomposition therefore breaks even earliest on exactly the models you use for execution: 74 turns for a two-way split on Composer at a 30k cold start, 92 on Sonnet or Opus, 134 on Fable. Fable's cache read is so cheap that a two-way split at 120 turns *loses* 10%. The principle is most true where you apply it and least true where you don't, which means your tiering is consistent with the arithmetic even though the README states the principle model-free.

**The absolute stakes in the worker tier are small, and smaller than the sticker gap.** At Anthropic first-party rates Sonnet 5's cache read equals Composer's, so a 100-turn agent costs $2.34 on Composer and $2.91 on Sonnet 5. That is a 1.25× gap, not the 4× the input price suggests. Opus is 3×, Fable 2.7×. Two caveats: Cursor bills Claude models at its own rates, and Sonnet 4.6 reads at $0.30, so check the rate you actually pay. The decomposition saving on a $3 agent is about 30 cents. In the worker tier, quality is the reason to keep agents small. Cost is a rounding error.

**A 20k base moves the break-even earlier, not later.** A smaller fixed prefix means more of each turn's read is the growing part, so the crossover comes sooner. Claude Code's base with a typical MCP tool set is 40 to 60k, which is why it looks less quadratic. Trim the tool surface for workers regardless of model. The tokens you never load are the cheapest.

### Where the money actually is: the pipeline

Price a full run under your allocation: plan on Opus 5, refine on Sonnet 5, six workers of 60 turns on Composer, review on Opus, verifier on Composer, and vary the execute orchestrator. Plan is modelled as 60 interactive turns reading broadly with heavy thinking. Rough, but the proportions are the point.

| Orchestrator model, lifetime | Plan | Refine | Orchestrator | 6 workers | Review | Verifier | Total |
|---|---|---|---|---|---|---|---|
| Composer, 80 turns | $9.37 (46%) | $1.14 | $1.43 (7%) | $5.86 (29%) | $2.42 | $0.26 | $20.48 |
| Sonnet 5, 80 turns | $9.37 | $1.14 | $1.88 (9%) | $5.86 | $2.42 | $0.26 | $20.92 |
| Opus 5, 80 turns | $9.37 | $1.14 | $4.69 (20%) | $5.86 | $2.42 | $0.26 | $23.74 |
| Composer, 200 turns | $9.37 | $1.14 | $6.68 (26%) | $5.86 | $2.42 | $0.26 | $25.73 |
| Opus 5, 200 turns | $9.37 | $1.14 | $19.25 (50%) | $5.86 | $2.42 | $0.26 | $38.29 |

Two lines dominate. **Plan is close to half the run** at any orchestrator choice, and it is the one agent that ends far outside the sweet spot: 60 turns of broad reading with thinking lands at roughly 310k context. **The orchestrator is the swing line.** Bounded and cheap it is 7%; expensive and unbounded it is half the bill, more than plan and all six workers together. Model choice and lifetime multiply. Review on Opus costs $2.42 against $0.56 on Composer; that $1.86 is discussed below.

### Planning: don't decompose the judgment, decompose the reading

You judge planning hard to decompose because it needs broad context and several live priorities. That is right, and the field agrees: no surveyed system splits plan authorship. What the field does split is *context acquisition*. Plan's Ground phase currently has the expensive model read the codebase itself. If Ground dispatches cheap read-only recon agents that return bounded summaries (files, interfaces, constraints, contradictions with the request), the expensive model holds the synthesis and the priorities while its own context grows at half the rate. In the model above that takes plan from $9.37 to $7.73 and final context from 310k to 232k, and the quality argument is stronger than the cost one: 310k is deep into the range where recall degrades, on the one agent whose judgment you are paying for. Fable and Opus cost about the same for this session ($11 vs $9.4) because Fable's cheap cache read offsets its output price, so the choice between them is capability, not cost.

Refine sits between: it needs the whole plan but only one phase's code surface at a time. Coarse decomposition by execution phase, one refine agent per phase reading the plan plus that phase's surface, keeps each agent bounded and is the split you already describe as "coarsely" possible. Sonnet-class is enough; the hard judgment was made in plan.

### Review: spend the premium where it catches cheap-model errors

After the garcia-music correction, review ran on Composer, the same model that wrote the code. That saves about $1.90 per run and gives up the one thing review is for. Reviewer and worker on the same model share blind spots; the self-correction literature and Anthropic's own multi-agent guidance both argue for a different model, and ideally a different family, in the verifier role. A review agent is short (20 to 40 turns on the diff and acceptance criteria), so it is cheap even on Opus. Keep the verifier on the cheap tier: its job is mechanical, run the check and compare evidence.

### Recommended allocation

| Role | Lifetime | Tier | Effort | Why |
|---|---|---|---|---|
| plan | One session, interactive | Opus / Fable | high or xhigh | Judgment and priorities; the only agent where capability is the constraint. Delegate Ground reads to cheap recon agents. |
| plan recon | ≤ 20 turns, read-only | Composer / Haiku | low | Returns a bounded summary; never writes. |
| refine | One agent per phase | Sonnet-class | medium | Decomposition and brief authorship; needs the plan, not deep reasoning. |
| execute orchestrator | Re-dispatched per phase, ≤ 80 turns | Composer / Sonnet | low | Routes by path and reads capped reports. Judgment calls (contradictions, re-plan) go to a fresh Opus agent with a brief, not to a bigger orchestrator. |
| worker | ≤ 60 turns, budget in brief | Composer / Kimi / GLM | n/a | Where the cache-read curve is steepest and where absolute cost is lowest. Briefs must be more explicit for this tier: verification first, evidence default-false. |
| reviewer | 20–40 turns | Opus, different family from worker | high | Catches what the worker's model cannot see. Short, so the premium is small. |
| fixer | ≤ 40 turns | Composer | n/a | Mechanical from a brief. |
| verifier, QA driver | ≤ 30 turns | Composer | n/a | Run the check, compare evidence; no judgment beyond pass or fail. |
| escalation retry | One, on failure | Next tier up | high | Cheap-first with one escalation beats starting expensive. Caches are model-scoped, so the retry is a cold start; hand it the brief and the handoff, not the transcript. |

> **Make model a brief field.** The execute skill's allocation table is advice to the orchestrator; nothing in a brief says which model reads it, and lesson 24 records nested spawns leaking model selection. The 6.3M-token Sonnet review burst in garcia-music was a wrong-model dispatch. Add `Model:` beside `Consumer:` in the brief template, have the orchestrator pass it verbatim, and have transcript-parser report dollars per role per model. Its `--substitute` flag already prices the counterfactual; the missing piece is the role tag.

## §7 · Design, and what closes a phase

The proposal on the table: `plan` is misnamed. It starts from a problem statement and maps it to a solution shape, which is design. Design should bound and assign ownership, not flesh out detail. Refinement should then break the next phase down, execution should build it, and the following refinement should pick up whatever that phase left behind, so that late-phase discoveries are absorbed by the stage built to absorb them instead of by the execute orchestrator. This section asks whether that improves quality and cost, and settles the one question the proposal turns on: what a phase is.

### The problem is real, and already on record

Every closed plan record in `docs/plans/` carries a Deviations section, and the shape is consistent: discovered while building, late.

- **04:** both design deviations landed in phase 4, "discovered while writing the contract". Close-out's placement, settled at plan time, turned out to delete live inputs of the phases that followed it.
- **03:** "the most consequential thing the change did" (the QA.md semantics) was a mid-execution discovery, and scope grew mid-PR.
- **05:** the single largest addition (`cost_window.py`) was "driven by using the toolkit rather than by the plan".
- **01:** OVERVIEW.md was added because the planned scope produced a loop with no exit, found in execution.

One caveat keeps this honest. None of those runs exercised refine-all-then-execute as designed: 04 skipped refine, 03 had no briefs, 05 predates it. The records prove that plans drift; they do not yet measure how much up-front briefing gets wasted. The waste is predicted, not observed. But the current design already concedes the problem: `execute`'s "contradictions amend the brief" rule is a repair path for stale briefs, and it puts the repair in the execute orchestrator, the one context `refine` exists to keep decomposition out of. Under today's shape, drift lands in the most expensive and least suited place.

### The change is smaller than it sounds

Three things already lean this way. `plan` says phases are "light phasing, enough to show the shape and order of the work, not a dispatch list" and "phases can stay indicative and contracts cannot", which is the design posture: bounding and ownership, not detail. `execute` already runs per phase ("prefer phased execution by default: one plan folder or one executable slice at a time"). And principle 13, "prior work is the cheapest spec", is the plugin's own argument for refining against code that exists rather than code the plan imagines. The only stage that is not per phase is `refine`, which writes every brief up front and rewrites the whole dispatch list in one pass. The delta is: delegate Ground (§6), trim the design artifact to bounding, and make `refine` refine one phase at a time.

### A phase is closed by a provable outcome, not by a surface

Two definitions compete. A phase can be *what changes*: a domain boundary, a set of paths, a subsystem. Or a phase can be *what becomes true*: an observable result that either holds or does not. The second is the right one at the phase level, for four reasons, and the first survives one level down.

- **Backward signal.** A phase that closes on a verifiable outcome tests more than its own code. It tests the design's contract for that outcome and the refinement that decomposed it. When the outcome cannot be made true, the failure names something specific: the contract was wrong, the decomposition missed a surface, or the outcome was mis-stated. A phase defined by surface can complete without proving anything, and its problems surface two phases later as "unplanned work".
- **Refinement bound.** "What it takes to make this outcome true" is a natural scope for one refinement pass. The surface follows from the outcome; the outcome does not follow from the surface. Refine's recon becomes a directed question rather than a survey.
- **Predetermined iterations.** Phases are enumerated at design sign-off, each with its outcome. The number of refine/execute cycles is fixed there, not discovered. Discoveries re-order phases, re-scope a phase's units, or bounce to design; they do not add phases on their own. This is what separates the proposal from a backlog loop or from Ralph: the loop is bounded by the design's phase count, and a phase count that changes is a design change with a sign-off, not a reprioritisation inside the loop.
- **Segmentation of certain from uncertain.** Some phases have a provable outcome and a known approach; they run straight. Some have a provable outcome and no settled approach. Design flags those, and they run under `iterate`'s challenger mechanism with the phase outcome as the fixed yardstick. That is a narrower use of `iterate` than it was built for. Its premise is that criteria are not knowable up front; here the criterion is known and only the approach is open, so the divergence gate and synthesis apply but the criteria-discovery machinery (`OUTCOMES.md` revised each cycle) does not. The design's outcome for the phase is the yardstick, fixed, and synthesis selects the approach that best makes it true. The flag is set at design time, per phase, in the design conversation, which is exactly where a human should be deciding to spend a multiple on a phase.

The surface definition is still needed, one level down. Inside a phase, `refine`'s hard constraint stands: units that may run in parallel own disjoint paths. Outcomes define phases; surfaces define units. The two never compete because they answer different questions: *when is this done* and *who may edit what*.

The test for a candidate phase is the one `refine` already applies to units, moved up a level: a phase whose outcome cannot be stated as entry point → action → observable result (or as a plain observable statement for internal contracts) is not a phase. Fold it into the phase whose outcome it serves. Refactors, migrations and scaffolding are the usual offenders, and the fold is the right answer: a migration's outcome is the behaviour that runs on the migrated shape. This also resolves what happens to `plan`'s acceptance criteria. They become per-phase. The design's acceptance criteria are the union of its phases' outcomes, so post-build's QA derivation is unchanged.

### What a phase boundary is for

The boundary does three jobs, and each is a place the current workflow has no natural stop.

- **An optional stop.** The branch is resumable from `IMPLEMENTATION.md` and the dispatch list at every boundary. A human can gate here, a headless run can pass through. Same posture rule as everywhere else: declared by the invoker, default to holding.
- **A review point.** Cheap-tier verification that the phase outcome holds: run the check, compare evidence, smoke the path. Not a premium review per phase; §6's numbers below show why. The one premium review runs once, at the end, against the design. A phase the design flags as high-risk can be declared an exception.
- **A refinement bound.** The next `refine` reads the design, `IMPLEMENTATION.md` as it stands, and the closed phase's carried items, and writes briefs for the next phase only, against the code the closed phase actually left.

Carried items are the part that needs care, because they are where a backlog would creep in. A phase closes with its outcome verified and a short list of what it carries forward: contradictions amended in its briefs, deferred bugs from worker reports, verify findings that were not blocking. That list is a section of the phase's outcome record in `IMPLEMENTATION.md`, not a new artifact, and it has one consumer: the next refinement. It is ordered and it has no status column. Principle 8 holds because the list is work not yet refined, not a tracker. The bound on it is the same as `refine`'s bounce rule: a carried item that touches a contract, a boundary, or a phase outcome goes back to design; one that does not is absorbed into the next phase's units.

### Quality

Where it helps. Phase N+1's briefs are written against the code phase N left, so the contradiction-amendment path becomes rare instead of routine. Leftovers have a home: today deferred bugs go to an ad hoc fixer the orchestrator dispatches, review findings go through a remediation loop, and open questions sit in PLAN.md; a phase record consumed by the next refinement reprioritises all three against the design. Bouncing gets cheaper and more specific: a phase whose outcome cannot close after two phases are built is a bounce with real code to point at, not a whole-plan rejection.

Where it risks, and what closes each. **Hill-climbing into a local optimum:** greedy per-phase refinement can let phase 1's shape quietly constrain phase 3. The guard is that outcomes and contracts are fixed at design and the loop refines within them; a discovery that touches either bounces. The loop is safe exactly to the extent that design is a real bounding document with a real sign-off. **Losing the whole-plan cold read:** today `refine` is "the first honest test of the plan" because it must decompose all of it. Refining only the next phase would find an undecomposable phase 4 at phase 4. So the first refinement also runs one coarse pass over every phase: can its code surface be located, is its contract stated, is its outcome provable, is its dependency order real. Recon-level, no briefs, and it keeps the pressure. **Convergence:** principle 15 says additive phases produce a whole no review has seen. The terminal premium review against the design is that verification, and it is not optional.

### Cost

The §6 model, on a three-phase, six-unit change with two mid-run discoveries invalidating later briefs, the shape the records show. Parameters are illustrative, with the same caveats as §6.

| Line | Today: refine all, one orchestrator carries every phase and absorbs drift | Design + phased refine/execute, cheap verify per phase, one terminal review | Same, but premium review per phase |
|---|---|---|---|
| Design / plan | $9.37 | $6.08 + $0.39 recon + $0.39 feasibility | $6.87 |
| Refine | $1.14 (40 turns) | $1.39 (3 × 18) | $1.39 |
| Execute orchestrator | $6.68 (200 turns) | $3.49 (3 × 70) | $3.49 |
| Workers | $5.86 + $1.02 re-dispatched | $5.86 | $5.86 |
| Review | $2.42 | $0.96 verify + $2.42 terminal | $5.85 + $2.42 |
| Total | $26.49 | $20.99 (−21%) | $25.88 (−2%) |

Three readings. **Per-phase refinement itself costs slightly more** ($1.14 → $1.39): three Sonnet cold starts to avoid a quadratic that is small at 40 turns, and Sonnet's split break-even is about 92 turns. It does not matter; refine is 5% of the run. **The saving is the orchestrator.** One orchestrator carrying three phases and their drift runs to about 200 turns, and §6 identified that lifetime as the swing line. The phase boundary bounds it structurally, at one phase each, and Composer's split break-even of about 74 turns means a fresh orchestrator per phase pays on cache economics alone, before counting the re-dispatches it avoids. **Premium review per phase eats the whole saving.** Cheap-tier verification at each boundary plus one premium review against the design keeps it, which is §6's review conclusion arrived at from the other side. For a one-phase change the loop collapses to today's flow ($9.90 → $8.88, and the difference is delegated Ground), so `refine`'s skip rule survives unchanged.

### The closest field analogue

BMAD's architecture-then-story cycle: an up-front Architecture document, then a Scrum Master agent drafts one story at a time from it after the previous story lands, a dev agent implements, QA reviews, and the next story is drafted against the code that now exists. Spec Kit and Kiro are the up-front-tasks shape this moves away from; Ralph is the loop with no bounding document. The proposal sits where BMAD does, with a smaller design artifact, phases closed by outcomes rather than by story count, and cheaper executors. BMAD calling its artifact "Architecture" rather than "Plan" is a point in favour of the rename.

### The shape

```
design    interactive, Opus/Fable; Ground delegated to cheap recon agents
          → problem, solution shape, boundaries, contracts, ownership,
            phases each with a provable outcome and an approach-known flag,
            Challenge pass, sign-off held
per phase, in the order the design fixed
  refine    Sonnet, ~20 turns: design + IMPLEMENTATION.md + carried items
            → briefs for this phase only; first pass also runs the coarse
              all-phase feasibility check; bounce → design if a carried
              item touches a contract, boundary, or outcome
  execute   fresh Composer orchestrator ≤ 80 turns; workers per brief
            (an approach-unknown phase runs iterate's challenger + synthesis
             here, with the phase outcome as the fixed yardstick)
  verify    cheap tier: outcome check, done evidence, smoke
  close     outcome record + carried items in IMPLEMENTATION.md;
            optional human stop
terminal review   Opus, once, against the design → close-out
```

### Decisions this forces

- **The rename ripples.** `DESIGN.md` already exists as plan's optional contracts document; `docs/plans/`, `PLAN.md` and the `Workflow-Plan:` marker are load-bearing in `post-build`, `comprehensive-review` and `close-out`. The cheapest honest version: the skill becomes `design` and always writes `DESIGN.md`, today's PLAN.md and the optional DESIGN.md merged, with the folder path and the marker left alone. Renaming the marker is a breaking change across adapters for no behavioural gain.
- **Carried items live in the phase record, not in a backlog file.** The line between "work the next refinement absorbs" and "a shadow tracker" is principle 8, and a per-phase section of `IMPLEMENTATION.md` stays on the right side of it. A standalone `BACKLOG.md` would not, and would grow.
- **Termination is the phase count.** Bounded per principle 6 by construction: the loop ends when the last designed phase closes, or when a bounce reopens design. No cycle cap is needed because the design already is one. A run that wants more phases than it was signed off with has found a design problem, and should say so.

> **Effect on §8.** This absorbs three of the ten recommendations there. Recommendation 3 (bound the orchestrators) becomes "re-dispatch per phase", with the boundary now defined. Recommendation 4 (a Surfaces section, refine bounces "too big") becomes: design records surfaces per phase, and "too big" is a phase count that will not sign off. Recommendation 5 (a skip rule) becomes "a design with one phase and one unit goes straight to execute". Recommendation 7 (one escalated retry) is unchanged and applies within a phase.

## §8 · What to change, in order of leverage

### Put a countable ceiling and a stop rule in every brief

*1 · brief template, refine*

Add to refine's unit test a ceiling in the field's units: files to read, lines to change, and a token budget for the run. Write the budget into the brief. Add to the report-back a status enum (done / done with concerns / blocked / needs context / over budget) and the instruction: past the budget, write a handoff section into IMPLEMENTATION.md against your brief name, commit, and return. The orchestrator already knows how to resume from that state.

### Verification first, evidence default-false

*2 · brief template*

Reorder the brief so the worker identifies or writes the failing check before it changes code, and reports the check's before and after output as evidence. Consider cwc's pattern for functional work: an evidence ledger that starts false and can only be flipped by a reviewer who has read the artifact.

### Bound the orchestrators the way you bound the workers

*3 · execute, post-build*

Cheapest step: cap worker reports at roughly 1 to 2k tokens and forbid the orchestrator from reading anything a worker wrote beyond its report. Next step: have execute re-dispatch a fresh orchestrator per unit or per phase, resuming from the dispatch list and IMPLEMENTATION.md, which is already the documented resume path. §7 makes the phase boundary that re-dispatch point. The post-build operator guide argues one long parent is needed to hold cross-phase state; that state fits in an uncommitted file or a PR comment, and phase independence already comes from fresh workers.

### Give plan a files-and-interfaces section, and let refine bounce "too big"

*4 · plan template, refine*

Plan's Ground phase already looks at the code surface; record what it saw. A short "Surfaces" section naming files, modules and interfaces makes refine's recon a check instead of a rediscovery. Then give refine a second bounce condition: the plan needs more than N units or more than one PR, so split it into a design-intent doc plus a sequence of plans, which is a shape you already describe. Under §7 the surfaces are recorded per phase and "too big" is a phase count that will not sign off.

### Add a one-sentence skip rule

*5 · plan*

Post-build right-sizes by classification; plan does not. Adopt the Claude Code test: if the diff can be described in one sentence and touches one surface, skip plan and refine, write the brief inline, and go straight to execute in the single-worker rung. Record the skip, as post-build records absorption. Under §7: a design with one phase and one unit.

### Manage context growth explicitly

*6 · brief template*

Extend "required reading, in order" with reading discipline: ranged reads and grep over whole files, no re-reading a file already in context, truncate long tool output. This is the lever the cost model says matters most, and it costs a paragraph.

### One escalated retry before the human

*7 · post-build, execute*

Keep the bound at one cycle on the allocated model, then allow exactly one retry on the next model tier before HUMAN_ACTION_REQUIRED. This keeps cost predictable and matches superpowers' round-four escalation.

### Single writer, no sub-spawn

*8 · worker briefs*

Put in the worker's own brief, where the worker reads it: do not spawn agents; if the unit needs one, report that the unit was mis-sized. Read-only research helpers can be the exception, as Ralph allows.

### Instrument the number the design rests on

*9 · workflow-tuning, transcript-parser*

Have every run emit, per agent, turns and final context, and record them against the budget in reference.md. No eval harness needed; the WP1 post-mortem shows this loop already produces rules. Two or three runs of data would either confirm the 100 to 125k band or move it, which is more than any external source can do.

### Restate the principle in the units that are true

*10 · README, principles.md*

Replace "50 to 75 turns and 100 to 125k context" with: cost is context integrated over turns; decomposition pays when saved reads exceed added cold starts, roughly past 40 to 75 turns for a cheap worker; quality rot argues for smaller than cost does; the controllable lever is context growth. Note which model tiers the cache-read argument applies to: strongest on Composer-class executors, weakest on Fable (§6).

## §9 · Evidence and limits

Model prices in §6: Anthropic first-party rates from the Claude API reference (cache read 0.1× input, 0.025× on Fable 5.1; write 1.25×); Composer 2.5 $0.50 / $0.20 / $2.50 and Kimi K2.6 $0.95 / $0.16 / $4.00 from vendor pricing as reported by TokenCost, Vantage, DataCamp and OpenRouter, since cursor.com was unreachable; GLM 5.2 from OpenRouter and pricepertoken. Composer's cache-write price is not published and is assumed equal to input. The pipeline table uses illustrative turn counts and growth rates, not measured ones, and so does §7's comparison; the two mid-run re-dispatches it charges to today's shape are an assumption drawn from the plan records' Deviations sections, not a measured count.

**What was checked directly.** All ten SKILL.md files, templates and briefs at db78e3e; README, OVERVIEW, ARCHITECTURE; principles.md and reference.md; the two garcia-music analyses; the WP1 cost post-mortem commit; all five plan records, 01 to 05, and their Deviations sections; the `iterate` skill and its briefs. Skill token sizes were measured. The cost model in §2 is my own arithmetic on standard cache multipliers, cross-checked against the research sweep's independent model on Opus 5 list prices.

**Sourcing caveat.** The research agents ran behind a proxy that blocked most primary hosts (anthropic.com, openai.com, cursor.com, kiro.dev, arxiv.org, martinfowler.com, docs.devin.ai). Claude Code docs at code.claude.com, the Anthropic API docs, and GitHub-hosted originals (Spec Kit templates, superpowers skills, BMAD, Ralph, cwc-long-running-agents, NoLiMa) were read in full. Quotes from the blocked hosts came through search snippets and mirrors and should be spot-checked before being cited formally. No external source names a 50 to 75 turn or 100 to 125k sweet spot; those figures are your own reading of the curve, and the arithmetic supports the band as a crossover region.

**What no public evidence settles.** No controlled study measures coding-agent success against turn count or context size while holding task difficulty constant; trajectory-length papers explicitly warn that longer failed runs may reflect harder tasks. No benchmark compares compaction to fresh handoff on coding work. The fresh-context-reviewer advantage over same-context self-review is practitioner consensus backed by adjacent self-correction research, not a direct measurement. Your empty evals directory is where those answers would come from.

### Primary sources read

- Claude Code best practices, sub-agents, workflows, agent teams, costs, prompt caching: [code.claude.com](https://code.claude.com/docs/en/best-practices)
- Anthropic prompt caching pricing: [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Anthropic long-running agent harness: [cwc-long-running-agents](https://github.com/anthropics/cwc-long-running-agents)
- GitHub Spec Kit templates and spec-driven.md: [github/spec-kit](https://github.com/github/spec-kit)
- obra/superpowers writing-plans and subagent-driven-development: [obra/superpowers](https://github.com/obra/superpowers)
- BMAD-Method build docs and story template: [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)
- Ralph loop: [ghuntley/how-to-ralph-wiggum](https://github.com/ghuntley/how-to-ralph-wiggum), [snarktank/ralph](https://github.com/snarktank/ralph)
- NoLiMa effective context lengths: [adobe-research/NoLiMa](https://github.com/adobe-research/NoLiMa)
- Aider architect/editor mode: [Aider docs](https://github.com/Aider-AI/aider/blob/main/aider/website/docs/usage/modes.md)

### Via search snippets (spot-check before formal citation)

- Anthropic: Building effective agents; Effective context engineering; multi-agent research system; when to use multi-agent
- Chroma, Context Rot; Liu et al., Lost in the Middle; Stanford budget-controlled multi-agent study (arXiv 2604.02460); Huang et al. on self-correction (arXiv 2310.01798); Kambhampati et al. (arXiv 2402.08115)
- Cognition, Don't Build Multi-Agents, and Walden Yan's 2026 revision; OpenAI harness engineering and Codex best practices; Cursor plan mode and agent best practices; Kiro specs and best practices; Devin guidelines; Böckeler on spec-driven development at martinfowler.com; Sonar, Stop the Context Tax

