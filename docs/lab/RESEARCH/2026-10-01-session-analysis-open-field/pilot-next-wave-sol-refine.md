# Pilot next-wave refine — Sol (high) + Sol adversarial second pass

**Machine:** codyh-ubuntu (`090ebdb6-1309-4527-9c34-1135deb7968b`)  
**Models:** `gpt-6.1-sol` reasoning_effort=high — pass 1 plan, pass 2 full regenerate (adversarial)  
**Opus:** SKIPPED — `claude` CLI present but not logged in (`Not logged in · Please run /login`); Sol second pass is the adversarial gate.  
**Saved:** `/tmp/pilot-next-wave-sol-refine.md`  
**Scope:** design/markdown only; no code; no secrets.

---

# Pilot next-wave refine (Sol — second adversarial pass)

**This Sol second pass is the adversarial gate because Opus is unavailable.** It strengthens the plan’s controls; it does not establish that execution gates have passed or authorize Standard release.

## 1. One-page refined next-wave plan

- Keep **wave-001 HOLD for Standard/Max**. Its supplied live Jev result remains **96/96 on a0310a0**; that evidence does not authorize wave-002 spend or promotion.
- Register exactly one new wave: **`pilot-wave-002-luna-swarm-dual-label`**.
- Preserve **`tournament-binary-foreshadow`** as the incumbent winner: thrash PASS. Kill **`tournament-monitor-called-out`**: prototypes + poll FP **15f24c7ba18c**.
- Demote the other ten registered slugs. Freeze the **four-member comparison pool**, inputs, framing, scoring rules, routes, and limits before dispatch.
- Apply the same **eight stratified workers to each candidate**, with independent poll and thrash labels. Run **Luna first**, then the identical gate on **Flash when green**. Account for all four candidates when budgeting.
- **More than 4/8 workers with conflict or parse failure kills that candidate’s approach on that engine.** Preserve each candidate/engine denominator. Other kill criteria apply independently.
- **No TypeSafe spend on volume fail.** No local-response repair through TypeSafe. Missing results, timeouts, or incomplete adjudication leave the relevant gate pending.
- Use existing, zero-call evidence first. If it separates the candidates under the frozen decision rule, **leave Jev idle**.
- Otherwise, only after every required gate clears, run **8 live Jev cases**, with one conditional extension to **16 total**. Count actual requests as well as cases; retries and candidate-specific evaluations cannot multiply the budget.
- Keep **Standard HOLD**, including Soft Standard. Progressive **`--call-jev` is out of scope**.
- An invalid comparison may receive a bounded, blinded replay only under a preregistered replay allowance. A genuine kill remains recorded and cannot be erased by replay.

## 2. Prune table (keep / kill / demote) + live pool 4–6

| Registered slug | Disposition | Next-wave role |
|---|---|---|
| `tournament-binary-foreshadow` | **KEEP** | Incumbent; live pool |
| `tournament-likert-collapsed` | **DEMOTE** | Parked |
| `tournament-monitor-called-out` | **KILL** | Excluded; retain its failure evidence |
| `tournament-no-story-beyond-counts` | **DEMOTE** | Bounded counts-only challenger; live pool |
| `pool-likert-foreshadow` | **DEMOTE** | Parked |
| `pool-echo-guard-reread` | **DEMOTE** | Parked |
| `pool-phase-hint-stats` | **DEMOTE** | Parked |
| `pool-anchor-agnostic` | **DEMOTE** | Bounded anchor sensitivity challenger; live pool |
| `pool-thrash-card-anchor` | **DEMOTE** | Parked |
| `pool-residual-baseline` | **DEMOTE** | Bounded baseline challenger; live pool |
| `signal-v0-default` | **DEMOTE** | Parked |
| `signal-v0-alt` | **DEMOTE** | Parked |

**Live pool: exactly four**, within the required 4–6 range:

1. `tournament-binary-foreshadow`
2. `tournament-no-story-beyond-counts`
3. `pool-anchor-agnostic`
4. `pool-residual-baseline`

The three demoted challengers receive comparison slots only; they are not promoted winners.

Freeze candidate versions and neutral identifiers. No mid-wave substitutions, extra registrations, reintroduction of killed slugs, or framing changes. A candidate killed during testing remains in the evidence record; its slot is not filled by another candidate.

## 3. Kill gates — Luna swarm wave (verbatim CANDIDATE-APPROACHES)

The supplied `segment-swarm-arbiter` kill criteria apply verbatim:

- Conflict or parse failure on more than **4 of the 8** stratified workers. The arbiter is then the whole panel, and this approach has collapsed into summary-then-judge at higher operational cost.
- A local response is repaired by a TypeSafe retry.
- A stable label of `thrash_bundle` on any poll-label worker in the 8. That kill fires even if Flash would have caught it, because the savings depend on trusting stable labels enough to skip Flash.
- Windows whose end is past `early_window_end` were sent.

**Pilot aggregate kill:** Local conflict **> 4 / 8**; poll flags co-occur with thrash prototypes; unregistered framing.

### Frozen gate and accounting

- Freeze eight stratified workers: **four poll-label and four thrash-label**, including **15f24c7ba18c** and thrash prototypes.
- Identify every worker’s evidence, expected labels, stratum, and window boundaries before execution. Missing required evidence prevents launch.
- Apply these same eight workers to each of the four candidates on Luna and, after Luna clears, Flash: **32 candidate-worker slots per engine; 64 across both engines**, before any separately budgeted health checks or permitted replay.
- Require separate poll and thrash outputs. Neither label may be derived from the other, and the output format must permit both labels to be evaluated independently.
- Freeze the definitions of conflict, parse failure, stable label, and aggregate poll/prototype co-occurrence before outputs are visible.
- Count a worker with conflict, parse failure, or both **once** toward the combined volume threshold. Preserve both underlying flags.
- Evaluate the threshold separately for every candidate/engine pair. Do not pool workers across candidates or engines.

### Completion and stop rules

- **5/8 kills; 4/8 does not clear the whole gate.** At 4/8, all other kill checks and the registered conflict-resolution requirements still apply.
- Missing outputs and timeouts cannot count as clean workers. Keep the denominator at eight and mark the gate pending.
- Record initial responses before any permitted local retry or adjudication. A later response cannot overwrite an initial failure.
- On volume fail, stop that approach: **no TypeSafe repair, arbitration, or live Jev spend**. Do not continue paid testing merely to rehabilitate it.
- Any other kill criterion stops the affected approach or run immediately. A dispatched late window kills the run even if its response is discarded.
- For any surviving candidate used to justify Jev spend, both required engine gates must be complete and clear. Flash health or execution timeouts keep Flash pending.
- Every original comparison slot must have a documented disposition. Quietly dropping a failed candidate or worker invalidates the comparison.

## 4. When to re-spend live Jev (microbatch ≤8–16 OR idle)

**Default: Jev idle.** Existing evidence is reviewed before any new model calls; “zero-call” does not mean an unmetered fresh swarm run.

Re-spend only if the registered comparison leaves a concrete unresolved distinction:

1. Complete the required Luna and Flash gates for the surviving candidates relevant to that distinction.
2. Confirm pricing directly in the **TypeSafe console** and reserve the microbatch within the registered all-in ceiling.
3. Record the unresolved question, candidate comparison, expected decision, and exact first-batch case manifest before dispatch.
4. Run **8 live Jev cases**, covering poll-FP exposure, thrash prototypes, and the relevant candidate disagreements.
5. Stop at eight if the frozen decision rule separates the candidates.
6. Extend once, by at most eight cases, only if the first batch passes every registered check, remains within budget, and leaves a specifically recorded uncertainty.

**Hard caps: 16 live Jev cases and 16 actual live Jev requests for this wave.** Retries, failed billable requests, candidate-specific requests, and replay requests consume the request cap. Register an execution schedule that can cover the required comparison within both caps.

A kill, volume failure, pending gate, cost stop, or separation already established at zero calls means **idle**. An inconclusive result at the cap means **inconclusive**, not permission for another batch.

Microbatch success does not release Standard.

## 5. New registration

**ID: `pilot-wave-002-luna-swarm-dual-label`**

Complete this single registration before dispatch. It must contain:

- The four frozen candidate slugs, versions, dispositions, and neutral identifiers.
- The eight-worker manifest, four/four stratification, expected labels, required evidence, and window boundaries.
- Independent poll/thrash output requirements and frozen conflict, parse, stability, and co-occurrence definitions.
- Luna-first execution, Flash health criteria, and the identical Flash repeat.
- Initial-response retention, per-candidate/per-engine accounting, and kill versus pending dispositions.
- Blinding controls, adjudication rules, and the decision rule for separation, ties, and inconclusive evidence.
- Known poll-FP evidence **15f24c7ba18c** and the identified thrash prototypes.
- The zero-call decision, conditional **8–16 Jev** schedule, and actual-request accounting.
- Console-confirmed pricing, numeric all-in ceiling, maximum billable work, and stop-before-dispatch checks.
- Bounded health-check, local-retry, arbitration, and blinded-replay allowances. **An unspecified allowance is zero.**
- CHM’s Soft routing decision, verified WSM configuration, actual engine identity, and execution configuration.
- Evidence required for a later release review and the named release decision owner.

**Wave-001 stays HOLD.** This registration neither edits nor supersedes that status. An incomplete registration authorizes no execution.

## 6. Standard HOLD + progressive out of scope

**Standard HOLD remains in force**, including Soft Standard until the swarm conflict gate passes on Luna. Passing that gate is necessary, not sufficient, for release.

Pilot Standard/Max remains HOLD pending completed next-wave evidence and an explicit release decision. Neither **96/96**, incumbent retention, Luna PASS, Flash recovery, nor a successful microbatch supplies automatic promotion authority.

The release review must identify the exact candidate, configuration, routes, evidence, and scope being considered. A Pilot result cannot silently become authorization for Soft Standard or Max.

**Progressive `--call-jev` is explicitly out of scope.** This plan permits only the registered bounded microbatch after gates clear. No background continuation, automatic expansion, or renamed progressive run may bypass that boundary.

## 7. Soft / Luna / Flash / WSM routing

- **Soft:** Use effort×fit; obtain **CHM’s routing decision before execution** and record it. Soft naming does not exempt Luna work from the gate or budget.
- **Luna:** First route for the Pilot swarm. Include all candidate-worker slots, conflicts, permitted retries, timeouts, and arbiter work in total cost.
- **Flash:** Repeat the same frozen gate once healthy. The supplied Flash OpenCode history includes hangs/timeouts. Register a bounded health check with an explicit timeout and pass rule; health-check success does not count as gate success.
- **Local :8080:** Supplied evidence is **16/18 timeouts**. Keep it outside the accepted execution route until a bounded health check passes. Any later use must already be covered by the frozen routing policy.
- **WSM:** Track **bc-92263e85 / pending PR** for pruning monitor-called-out and wiring Flash/Luna swarm defaults. Verify merged configuration and the actual routes before execution. Pending work is not completed wiring.
- **TypeSafe:** Direct-console pricing only. No local-response repair and no spend after volume failure.
- **Route integrity:** Record the engine and configuration actually used. Silent fallback, changed defaults, or mismatched candidate versions invalidate affected evidence and stop dependent spend.

## 8. Open risks and MUST RESOLVE

These are execution blockers until resolved in the registration; none may be deferred to the release review.

| MUST RESOLVE | Required closure |
|---|---|
| **Poll-FP coverage** | Identify 15f24c7ba18c, the thrash prototypes, and the four/four sampling manifest. Search-stratum `poll_monitor` PASS is insufficient coverage. |
| **Independent labels and stable-label meaning** | Freeze separate label definitions, the stability rule, and the aggregate poll/prototype kill interpretation. Do not infer stability from an unregistered rerun. |
| **Volume and completion accounting** | Freeze the combined conflict/parse count, eight-worker denominators, timeout handling, and how permitted unresolved conflicts become resolved. No pending item counts as PASS. |
| **False winner echo** | Blind candidate identity and incumbent outputs during independent labeling and adjudication. Check prompt provenance, ordering, and shared context for answer leakage. |
| **Decision rule** | Define separation and tie handling before results. If the incumbent is retained without separation, report retention and uncertainty; do not claim a new comparative win. |
| **Soft Luna cost ceiling** | Enter a numeric all-in ceiling using console pricing. Budget every candidate, engine, health check, permitted retry, arbitration step, replay, and conditional Jev request. |
| **Flash and local health** | Freeze bounded health criteria and timeout limits. Pending health or gate evidence keeps dependent Jev idle. |
| **Boundary enforcement** | Validate every window against `early_window_end` before dispatch and retain evidence of the actual dispatched boundaries. |
| **CHM and WSM routing** | Obtain CHM’s route decision; verify merged wiring and actual configuration. No silent fallback. |
| **Replay and release authority** | Freeze the replay allowance and name the release decision owner. A replay cannot erase a kill; a plan review cannot release Standard. |

Check **spent cost plus committed in-flight cost plus the next dispatch’s worst-case cost** against the ceiling. Stop before that sum would exceed it. No retrospective ceiling increase during the wave.

## 9. Adversarial attacks — Sol gate

| Attack | Concrete adversarial attempt | Required response and evidence |
|---|---|---|
| **ESCALATE — HOLD bypass** | Cite wave-001’s 96/96 or a0310a0 as authority for wave-002 spend; relabel held work as a continuation. | Block dependent spend and promotion. Preserve wave-001 and Standard/Max HOLD. Require the new registration and completed prerequisites; record the attempted authorization shortcut. |
| **FORK — false winner echo** | Hide the incumbent slug but leak its answer through prompt text, shared context, candidate order, or adjudicator instructions. Declare agreement a win. | Invalidate contaminated comparison evidence. Preserve it for audit. Run a blinded replay only within the frozen allowance and budget, with independently produced answers and labels frozen before unblinding. No Jev confirmation of contaminated results. Without an allowance, stop and escalate. |
| **KILL — poll-FP sampling dodge** | Fill poll slots with easy search-stratum examples; omit 15f24c7ba18c, alter its window, duplicate easy cases, or remove prototype overlap. | Reject the gate as invalid before dispatch where possible. Retain the original evidence if already run. A permitted replay must use the exact frozen manifest; no worker replacement. Apply stable `thrash_bundle` and aggregate co-occurrence kills even if overall accuracy looks strong. |
| **ESCALATE — Soft Luna cost blowup** | Price eight workers while executing four candidates, hide Flash/retries/arbitration, or spend past the cap using concurrent calls. | Stop before the all-in committed ceiling would be exceeded. Reconcile every request to the ledger. Missing prices or an incomplete ledger block execution. A TypeSafe local-response repair **kills** the approach outright. |
| **ESCALATE — premature Standard** | Promote after Luna PASS while Flash is pending; describe Soft Standard as exempt; treat microbatch success as release authority. | Preserve all applicable HOLD states. Require complete evidence for the exact proposed route and configuration plus the explicit release decision. Check actual defaults as well as the written status. |
| **KILL — volume laundering** | Average Luna and Flash, pool candidates, count conflict and parse separately to distort the denominator, or replace failed workers until the result appears ≤4/8. | Preserve original eight-worker denominators and union accounting per candidate/engine. More than 4/8 kills that approach. No TypeSafe repair, arbitration, or live Jev spend after volume failure. |
| **ESCALATE — timeout laundering** | Report missing workers as clean, call a health-check PASS a Flash gate PASS, or invoke silent fallback. | Keep the gate pending; invalidate mismatched-route evidence. Stop dependent Jev spend until the registered engine completes the required gate. |
| **KILL — label coupling** | Produce thrash as the inverse of poll, suppress one label, or change the stability/co-occurrence rule after seeing a false positive. | Reject the gate as invalid for violating frozen framing and independent-label requirements. Retain the original outputs and apply any independently observed kill. No post hoc rule change rescues the result. |
| **KILL — late-window or framing escape** | Trim a late window only after dispatch, reintroduce monitor-called-out under an alias, or change prompts mid-wave. | Kill the run for a dispatched late window; kill unregistered framing. Check dispatched inputs and candidate versions, not only the final report. |
| **ESCALATE — microbatch multiplication** | Call eight unique cases “eight” while evaluating each against four candidates, retry freely, or reset the cap in a replay. | Enforce both case and actual-request caps across the whole wave. Stop at the cap; report unresolved evidence as inconclusive. No additional registration or progressive continuation. |
| **KILL — replay resurrection** | Use a blinded replay to erase a genuine stable-label, TypeSafe-repair, volume, or boundary kill. | Preserve the original kill. A replay may address invalid comparison evidence only; it cannot rehabilitate a killed approach within this wave. |

**Adversarial gate disposition:** The strengthened plan specifies responses for HOLD bypass, false winner echo, poll-FP sampling, Soft Luna cost blowup, and premature Standard. Execution remains blocked until every MUST RESOLVE item is closed.

## 10. SUCCESS CRITERIA

The next wave succeeds only when all applicable criteria below are evidenced:

1. **Scope and pruning:** Exactly one new registration; all twelve dispositions retained; the four-member pool frozen; monitor-called-out excluded.
2. **Gate integrity:** The same registered eight-worker manifest applied to each candidate, with independent poll/thrash labels, per-engine evidence, fixed denominators, and enforced boundaries.
3. **Kill enforcement:** Every verbatim and aggregate kill checked independently. No killed approach is rescued through averaging, replacement, repair, or replay.
4. **Poll-FP exposure:** Required poll-FP evidence and thrash prototypes are present. Narrow search-stratum PASS is not presented as broader coverage.
5. **Comparison validity:** Blinding and provenance checks pass; the frozen decision rule supports any claimed separation. Ties and uncertainty remain explicit.
6. **Routing and cost:** CHM routing, WSM wiring, actual engines, console pricing, numeric ceiling, and complete committed-cost accounting are verified.
7. **Jev restraint:** Jev remains idle when evidence already separates candidates or prerequisites are incomplete. Any necessary spend follows the conditional 8–16 schedule and both hard caps.
8. **Release restraint:** Wave-001 and Standard/Max HOLD remain intact unless a separate explicit release decision is recorded. Progressive `--call-jev` remains out of scope.
9. **Reviewable outcome:** Evidence supports a documented separation, retained incumbent with uncertainty, killed approach, or inconclusive result. A pending gate is never reported as a completed PASS.
