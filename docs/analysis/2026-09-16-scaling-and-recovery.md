# Where the workflow scales, and how it recovers

*workflow-plugin · thought experiment · 2026-09-16*

A limits-and-recovery pass over the design → refine → execute loop as it stands with the [phase driver](../plans/06-phase-driver/DESIGN.md) at checkpoint. Nothing here was run. The questions: what is the smallest problem the workflow is worth applying to; at what size does one design stop being enough and how is it decomposed; how phasing behaves under size; and, for each way a run goes wrong, what compensates, where the bound is, and what the current text leaves unsaid. Cost figures are the illustrative ones from [§7 of the field review](2026-09-08-workflow-vs-field.md), with that section's caveats.

## §1 · The frame: three containers, one shape

The workflow is the same shape three times. Each level bounds one context, has a cold-read point it can be resumed from, closes on something verifiable, and has a rule for being too big and a rule for being too small. Each "too big" bounces one level up; each "too small" folds one level down.

| Level | Bounds | Resumes from | Closes on | Too big → | Too small → |
|---|---|---|---|---|---|
| Design | one conversation, one PR | `DESIGN.md` | review passed, `done` trailer, PR | sign-off refuses: intent doc in `docs/design/` + a sequence of designs | skip rule: no design, brief inline |
| Phase | one orchestrator | `IMPLEMENTATION.md` + `Workflow-Phase:` trailers | outcome verified, closing commit | `refine` bounces: split the outcome | fold into the phase the outcome serves |
| Unit | one worker | the brief | done evidence | worker reports mis-sized; `refine` re-splits | "do not split to hit a count" |

Two of the six cells are stated as rules today; the design, phase and unit "too small" rules are in `design`, `refine` and `execute`, and the design "too big" rule is in `design`. Two are missing: nothing bounds units per phase, and nothing says what a phase that has exhausted its orchestrator does. §4 and §5 take those up. The frame matters because every question below has the same answer at every level: the boundary pays when what the inner context needs is a small subset of what the outer context read, and it costs one cold start plus one verification.

## §2 · Scaling down

### The ladder has three rungs, not two

- **No workflow.** The diff is one sentence and one surface, and no contract is touched. One agent, one context. This is the skip rule (§8.5 of the field review) and the design skill already defers to it: "the invoker has already decided this work deserves a design; do not relitigate that."
- **Design, then one session.** One phase, one unit. `refine` is skipped by its own rule; `execute` briefs inline. The design conversation is most of the cost: in §7's one-phase figure of $8.88, design is $6.86, about three quarters. The remaining quarter is a phase session and a wrap-up session.
- **The full loop.** Two or more phases, or a phase of more than one unit.

The floor of the workflow is the step from the first rung to the second, and it is a value question, not a size question. Design is worth three quarters of a one-phase run exactly when the design is what the work needs: the intent is loose, a contract has to be stated before anyone can build against it, or the outcome has to be made provable. When the request already is the brief, design restates it at a premium and the boundary is pure cold-start cost.

### The criterion for the design/execute boundary

The boundary is valuable because design goes wide and execution goes long, and execution does not need most of what design read. Stated as a test: **the boundary pays when Ground's surface is larger than the build's surface.** A one-file change whose design read fifteen files to bound it still benefits; the executor needs one file and the contract. A one-file change whose design read that one file gains nothing from the split. Design's "delegate Ground" rule already keeps the wide reading out of the design context, which lowers the cost of the design side; it does not change the test.

### The one-unit phase: the phase agent is the worker

At one unit there is nothing to coordinate. The question in the request — should the refiner do the work rather than add an agent — resolves as: there is no refiner at one unit (skipped), so it is whether the phase agent dispatches a worker for one brief or does the brief itself. `execute` currently makes this "a judgment call when no worker is running and the orchestrator's context is already hot with the design". At one unit it should be the rule, with two conditions kept:

- The cheap-tier verification of the outcome still happens, against real behaviour, before the closing commit. The phase closes on the outcome, not on who typed. "Reports are not verification" protects a phase built by workers; a phase built inline has no report at all, so the verify is all there is.
- The phase agent is on the model the worker would have been on. Under the §7 shape (a Composer-class orchestrator) it is. Under a premium orchestrator, inline work is the expensive path and dispatching the cheap worker is still right. The rule is "inline when the orchestrator is the cheapest agent likely to succeed", which is `execute`'s worker rule read reflexively.

Under the driver a one-phase design is two sessions: the phase (inline work, verify, closing commit, `Workflow-Phase: <slug>:1`) and wrap-up (`comprehensive-review`, close-out, `<slug>:done`). The agent-orchestrated path is the same two contexts. Nothing at the floor is special-cased; the trailer costs two lines.

## §3 · Scaling up: when one design is too many

### The signals, in the order they appear

The current rule is late: "a phase count that will not sign off is a design that is too big." Sign-off is the end of the conversation. Earlier signals, each of which is already visible to `design` at Ground:

1. **Ground fans out over disjoint code worlds.** Recon agents come back from parts of the codebase whose only relation is the request — a front end, a service, a schema migration — and no single contract joins their answers.
2. **A phase outcome depends on another component existing.** A candidate phase whose outcome reads "component X exists and works" is a design, not a phase. Its outcome cannot be stated as entry → action → result without describing X's whole behaviour.
3. **A seam with an open shape.** Two sides both need a contract (an API, a schema, an event, a file format) and the conversation cannot state it without designing one side first.
4. **The PR would be unreviewable.** A design is one PR by rule. The terminal review reads the whole diff against every phase outcome; `comprehensive-review` caps its parallelism at half the build's agent count. A diff the review cannot hold is a design the workflow cannot close.

Signal 4 is the hard ceiling and the other three are how it announces itself early. Phase count on its own is not the ceiling: each phase costs a cheap verify and a cold start, and §7's saving is per phase, so eight small phases in one PR are fine if one review can read the result.

### Decomposition strategy: cut at seams, fix the seams first

The intent doc in `docs/design/` is `DESIGN.md` one level up: verbatim intent, the components, the contracts *between* them, and a sequence of designs each with its own outcome. The decomposition rule is `refine`'s disjoint-paths rule raised a level: **designs that proceed independently own disjoint surfaces and share only a stated contract.** Front end and back end are two designs only if the API between them is a contract that can be promoted to `docs/design/` and refined against cold; if the API is open, it is one design first.

That first design is the one that fixes the seams, and it is usually thin: interfaces, schemas, and a walking skeleton that proves one request crosses every seam end to end. It is a convergent phase in principle 15's sense and deserves that principle's bar. After it, each side is a design of its own, refined against the promoted contract, and sides that share no surface can run as parallel PRs.

### The cost asymmetry, and the pressure it creates

Phase boundaries are cheap: a cheap-tier verify and one orchestrator cold start. Design boundaries are expensive: a conversation (the largest fixed line in every §7 column), a premium terminal review, and a PR. So the pressure runs one way: **pack as many phases into one design as one review can read, and split into designs only at real seams.** Splitting a design to make it feel smaller pays the design line twice for no saving; splitting a phase costs almost nothing. The failure to avoid is the opposite instinct — many small designs because phases feel heavy — which the numbers say is backwards.

### What is not mechanised, and need not be

A sequence of designs has no trailer and no driver. Which design is next is a human reading the intent doc, and each design ends in a PR, so the sequence is paced by merges. That is the right place for it: the seams are the decisions a human signs off, and the driver's non-goals already exclude running `design`. If a sequence ever needed to run unattended, the intent doc's design list is the analogue of `DESIGN.md`'s phase list and the PR's `Workflow-Plan:` marker is already the closure fact; nothing new would be invented. Not proposed.

## §4 · Phasing under size

### A phase's capacity is the orchestrator's routing budget

The orchestrator does not build; it dispatches, waits, reads a report of one or two thousand tokens, and records. Its lifetime is fixed overhead (cold read of the design and record, the refine dispatch, verification, the closing record) plus a per-unit increment. Under §7's shape of roughly 70 to 80 turns per phase, that is on the order of six to eight units before the orchestrator's own context is the cost the boundary was meant to bound. The number is an estimate from the shape, not a measurement; the driver's per-phase turns and cost print is the instrument that would calibrate it.

### The bound that is missing

`refine` bounces on a weak contract, a boundary it cannot set, an outcome no evidence would satisfy, or a carried item that touches design. It does not bounce on "this phase is too many units". §8.4 of the field review proposed exactly that bounce; §7 replaced it with the design-level "phase count that will not sign off", which bounds the design and leaves the phase unbounded. The gap is real: a phase whose outcome refines to fifteen units passes every current check and produces an orchestrator that runs to the end of its context.

The compensation is one bounce condition in `refine`: **a phase that refines to more units than one orchestrator can route bounces with the seam named** — "this outcome is two outcomes; split at X". Design then revises phases above the highest closed index, which the trailer contract already permits (`N` grows; closed trailers still resolve; the next run resolves the new phase as open). This is a bounce with real code to point at, and re-entry is the same command.

### The driver enforces the bound the agent path only asks for

The driver's per-session `max_turns` (or budget) is the countable orchestrator ceiling §8.3 asked for, and it exists only on the driver path. When a phase does not fit, the session ends without a report, the driver re-dispatches once, and the fresh agent reads `IMPLEMENTATION.md` — units with a recorded outcome are done — and continues. That is two orchestrator lifetimes for one phase, which is a bounded compensation for a mis-sized phase, and its exhaustion (`blocked` after one re-dispatch) is the signal that the phase should have bounced at `refine`. The agent-orchestrated path has no enforced ceiling: a too-large phase there is discovered by the orchestrator's degradation, late. That asymmetry is the strongest argument for the driver as the measurement tool it was designed to be.

### Too small

Two provable outcomes on one surface, with nothing learned between them and no reason for a human to stop, are one phase with two units. The design skill's fold rule covers "not a real outcome"; it does not cover "a real outcome, but the boundary buys nothing". Both cost the same: a verify and a cold start for no re-grounding. A phase boundary is worth having where refinement should re-ground against real code, where a human might stop, or where the outcome is convergent enough to deserve its own verification. Absent all three, fold.

### What scales with the diff, not with phases

The terminal review and the PR. Per-phase verification is cheap and linear in phase count; the review reads the whole result once. This is why the ceiling on a design (§3) is the review, and why more phases never fix a design that is too big — they make the review's input larger while making each orchestrator smaller.

## §5 · Failure and recovery

Each failure class, what detects it, what compensates, where the bound is, and what the current text leaves unsaid. The property that holds across all of them: **every recovery ends in re-running the same command.** The coordinator or driver resolves the open phase from the trailers, and nothing has to be reset, edited, or remembered. That is the payoff of a closure fact that restates nothing.

### 5.1 · A phase too large or unachievable

- **Detected by:** `refine` (cannot brief; or, with the §4 addition, too many units); `execute` (verification cannot be made to hold; retries exhausted → `blocked`); the driver (incomplete twice → `blocked`).
- **Compensation:** bounce to `design`. Phases at or below the highest closed index keep their trailers and are not revised; the design splits, restates, or removes phases above it. Re-run; the open phase resolves to the first revised one.
- **Bound:** `execute`'s one retry per unit; the driver's one re-dispatch per phase; then a human.
- **Unsaid:** the unit-count bounce (§4). Also "unachievable" as distinct from "unprovable": `refine`'s first-pass coarse check asks whether an outcome is provable, not whether it can be made true; the latter is only discovered by trying, which is the correct place, and `blocked` is the correct report.

### 5.2 · An architecturally significant pivot from implementation

- **Detected by:** a worker's contradiction report; `execute`'s cold read ("a design that no longer matches the architecture or the intent stops the run"); `refine`'s carried-item rule (touches a contract, boundary, or outcome → bounce); `comprehensive-review`'s "deeper design issue behind local fixes" lens.
- **Compensation:** two cases, split by what changed.
  - *How* changed, *what* did not: bounce to `design`; intent stays verbatim; the revision is phases above the highest closed index. If a closed phase's work is invalidated by the new contract, its trailer stands — it was verified against the design as it was — and the rework is a **new phase** whose outcome is the behaviour under the new contract. The trailer log is append-only in the same way `IMPLEMENTATION.md` is, and for the same reason: history is not edited to look consistent.
  - *What* changed: intent is untouchable, so a pivot in what is wanted is a **new design** with a new slug. The old one closes out on what it achieved, with the close-out record saying what was abandoned and why. The branch is merged if what it holds is coherent on its own, or dropped.
- **Bound:** every bounce returns to a human at sign-off (interactive) or to the ledger (headless). Neither the coordinator nor the driver re-runs `design`; both stop and relay. The design↔refine loop is bounded by a human by construction, and a driver that "helpfully" re-ran design on bounce would remove the only bound it has. The non-goal in the driver's contract is load-bearing.
- **Unsaid:** `design` has no stated revision posture. Its Outcome describes producing a design; a bounce arrives through Open Questions and the skill is silent on what a revision may and may not touch. The trailer contract implies the rule (closed phases are read-only; revisions are above the highest closed index; `PROVENANCE.md` gets a turn), but it should be said where `design` reads it.

### 5.3 · Bugs within a phase

- **Detected by:** worker reports; verification at the boundary.
- **Compensation:** all present. A contradiction amends the brief and the amended brief is what any re-dispatch reads; a deferred bug gets a small fresh fixer after the reporting unit; a failed unit gets one retry on the next tier; a verification that does not hold keeps the phase open — no trailer, no closure — and the phase agent works to closure inside its lifetime, which is the "within a phase, the execution agent owns refinement to closure" rule from the design conversation.
- **Bound:** one retry per unit, one re-dispatch per phase, then `blocked`.
- **Unsaid:** a verification attempt that fails is not recorded until the phase closes, because the record "closes with the verification result". A re-dispatched agent after an orchestrator death mid-verification re-verifies blind. Recording verification attempts progressively, as unit outcomes already are, closes it at no cost.

### 5.4 · A later phase finds a bug in an earlier closed phase

This is the case the request calls phase tweaking, and it tests what a trailer means.

- **What the trailer means:** a point-in-time attestation that the outcome was verified and accepted then. It is not a claim that the outcome holds now. Phase 4 finding that phase 2's implementation is wrong does not falsify phase 2's closure; it is either work or a bounce.
- **Compensation:**
  - *The fix is local and touches no contract:* it is phase 4's work. A worker reports it, a fixer fixes it, or the next `refine` places it from Carried. Phase 2's trailer stands.
  - *Phase 2's outcome no longer holds and re-establishing it is in phase 4's scope:* phase 4's verification includes it. Still phase 4's work.
  - *It touches a contract or an outcome:* bounce, per 5.2.
  - *The backstop:* the terminal review assesses **every** phase outcome against the final code, so a regression of phase 2 by phase 4 that nobody noticed is caught before the PR. Principle 15 is exactly this.
- **Bound:** the terminal review is one pass; findings go through its fix-in-place / brief / follow-up paths with `execute`'s one clean-agent pass and one retry.
- **Unsaid, two things.** First, the cheap-tier verify at each boundary checks *this* phase's outcome only. Re-running the earlier outcomes the phase's surfaces touch is cheap, linear in phase count, and would catch the regression at the boundary instead of at review; it is the natural regression rule and it is not written. Second, the last phase's Carried section has "one consumer: the next refinement", and after the last phase there is none. The wrap-up path should name it as an input to review — deferred bugs with no next phase are review findings, not lost.

### 5.5 · The orchestrator dies mid-phase

- **Detected by:** no report block in final output → incomplete.
- **Compensation:** re-dispatch once. The fresh agent reads `IMPLEMENTATION.md` cold; recorded units are done; it continues. This is the case the design was built for and it works because unit outcomes are written as they land.
- **Bound:** one re-dispatch.
- **Unsaid, and the largest gap in this pass:** **in-flight work.** A worker that was running when the session died leaves uncommitted changes in the working tree, and the closure mechanism describes only commits. The fresh agent's cold read must include the tree. A dirty tree is never assumed done: it is either checked against the running unit's brief and done evidence and then recorded, or it is set aside and the unit re-dispatched with its brief amended to say a partial attempt exists. Silently building on it trusts an unverified state; silently discarding it may throw away most of a unit. One rule in `execute`'s cold read closes this.

### 5.6 · Trailer errors

- **Malformed** (wrong key, bad slug, wrong shape): never counts. The phase resolves open; the re-dispatched agent finds the record closed and verified and writes the trailer-only closing commit. The repair path is already in the contract.
- **Duplicate** for one phase: harmless; resolution is set-membership.
- **Stray**: a trailer for phase 5 written while 3 is open. Lowest-missing resolves 3, then 4, and then every index has a trailer and the run resolves to wrap-up with phase 5 never built. The driver cannot see this — it reads only trailers, by design. The compensation is that the phase agent reads deeper: `execute`'s wrap-up path already reads `IMPLEMENTATION.md`, and a phase with a trailer and no closed record is not closed; the agent reports `blocked` with the reason rather than reviewing. The trailer is necessary for the driver and not sufficient for the agent, which is the "never trusted across a process boundary" rule applied to the agent's own inputs. Low likelihood — it takes an agent writing the wrong index on a closing commit — and the terminal review's per-outcome assessment is the second net.

### 5.7 · Concurrency and base drift

Two runs on one branch are two writers; the branch is the lock and this pass assumes one. Base drift is handled: resolution reads `<default>..HEAD`, so merging the default branch into the plan branch to resolve conflicts changes nothing the resolver sees.

## §6 · What this suggests for the design

For the checkpoint. None applied; each is small and lives in the workflow's text rather than in the driver.

1. **`refine` bounces on unit count.** A phase that refines to more units than one orchestrator can route is two phases; bounce with the seam named. Surface: `skills/refine/SKILL.md` Bounce. The ceiling is an estimate until the driver measures it. (§4)
2. **`execute` at one unit does the work itself**, when the orchestrator is the cheapest agent likely to succeed, and still verifies the outcome against real behaviour. Turns the existing judgment call into the rule at the floor. Surface: `skills/execute/SKILL.md` Workers. (§2)
3. **`execute`'s cold read includes the working tree.** A dirty tree is checked against the in-flight unit's brief or set aside and the unit re-dispatched; never assumed done. Surface: `skills/execute/SKILL.md` opening paragraph. Belongs in phase 1's scope since it is what makes re-dispatch safe. (§5.5)
4. **Boundary verification covers earlier outcomes the phase's surfaces touch.** Cheap, linear, and moves regression detection from the review to the boundary. Surface: `skills/execute/SKILL.md` Outcome of a phase. (§5.4)
5. **`design` states its revision posture.** On a bounce after closure: phases at or below the highest closed index are read-only; revisions and rework are phases above it; a change to what is wanted is a new design. Surface: `skills/design/SKILL.md`. The trailer contract already implies it. (§5.2)
6. **Wrap-up names the last Carried section as review input**, and verification attempts are recorded progressively. Surface: `skills/execute/SKILL.md` After the last phase; Outcome of a phase. (§5.3, §5.4)
7. **Design's "too big" signals are named at Ground** — disjoint code worlds, a component-shaped phase, an open seam, an unreviewable PR — and the decomposition rule is stated: cut at seams, fix the seams first, promote seam contracts to `docs/design/`, prefer many phases in one design over many designs. Surface: `skills/design/SKILL.md` Phases. (§3)

Items 3 and 5 are the ones that make the driver's recovery story true rather than assumed; the rest are the workflow tightening around it. The one thing this pass argues *against* changing: the driver and the coordinator must never run `design` on a bounce. That non-goal is what bounds the outer loop.
