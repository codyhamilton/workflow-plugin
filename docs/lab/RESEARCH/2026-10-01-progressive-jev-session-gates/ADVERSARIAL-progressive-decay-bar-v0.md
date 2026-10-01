# Progressive decay-bar adversarial track (WSM deliverable)

**Grounding:** master `6957b5b` `DESIGN-progressive-decay-bar-v0.md` (PR #91 merged). Design only. Progressive `--call-jev` out of scope. No Pilot live Jev / swarm / TypeSafe / hooks / secrets.

**Headline:** Preserve registered **D0** as comparison; propose **D1** (evidence-gated lowering, floor **2**, challenger **D1-F1**). Leap/phase/metric-gaming escalated. Not shipped.

---

# Part 1 — Codex Sol high (design-grounded, verbatim)

# Grounded adversarial review — progressive decay and validation handoff

**Date:** 2026-10-01, Australia/Brisbane  
**Status:** DESIGN ONLY; proposed revision, not shipped or validated.  
**Confidence:** Not high.

**Primary authority:** [DESIGN v0](/tmp/wsm-adversarial/DESIGN-progressive-decay-bar-v0.md), identified by the requester as master `6957b5b`, merged PR #91.  
**Secondary:** [Opus review](/tmp/wsm-adversarial/opus-out.md), remapped below onto authoritative D0.  
**Definitions:** [TERMS][terms] §§3–4, 6, 8, 11–14.

**Recommendation:** Preserve D0 as the registered comparison. Propose **D1** with the same `75:15` checkout grid, evidence-gated lowering no earlier than 105, and floor **2**. Keep floor **1** as a separately identified challenger. Resolve firing qualification and handoff arbitration before harness acceptance.

## 1. Executive table

`KILL` rejects the named proposal or interpretation. `FORK` retains alternatives for comparison. `ESCALATE` identifies a contract ambiguity that blocks acceptance.

| # | Attack axis | Verdict | Grounded finding | Falsifier |
|---|---|---|---|---|
| 1 | D0 decay too slow or fast | **FORK** | Real D0 is `3,3,2,2,1…`, reaching floor at 135. Retain those turn anchors; compare evidence-gated D1. | F1/F4: D1 fails to improve late misses, or worsens premature checkout. |
| 2 | Calendar versus evidence-gated decay | **FORK** | D0 lowers by round index even without persistent evidence. It still requires a checkout choice; elapsed time alone does not fire. | F2: calendar lowering adds supported late exits without added unsupported exits, defeating the preference for D1. |
| 3 | Leap agreement on 92a48e | **ESCALATE** | Shortlist: three-way split. Full Maps: 2/3 thrash. Neither whole-run result establishes action agreement at a particular prefix. | F3: a leap depends on future evidence, label majority alone, or an unsupported action inference. |
| 4 | Floor 1 versus floor 2 | **FORK** | Prefer moderate-confidence floor 2; retain weak-confidence floor 1 as challenger. | F4: floor 1 yields additional supported exits without additional unsupported early exits. |
| 5 | Reset on progress=3 | **KILL** proposed reset | Real D0 has no reset clause. Preserve that property; recovery breaks evidence persistence rather than resetting `k` or the bar. | F5: stale evidence still authorizes checkout after recovery. |
| 6 | Phase checks and checkout collision | **ESCALATE** | Preserve 50/60/75 and 75:15. Specify same-prefix evaluation, action precedence, and distinction between checkout candidate and applied action. | F6: ordering changes outcomes, duplicates steer, or records steer as checkout. |
| 7 | Ignored soft steer | **KILL** automatic hard escalation | Noncompliance is not evidence that continuation is a mistake. Record failed handoff; require independent checkout evidence. | F7: ignored steer alone produces checkout or a success claim. |
| 8 | Metric gaming | **ESCALATE** | Rare thrash positives, uncertain negatives, short horizons, and missing answers can manufacture apparent success. | F8: gains disappear when controls, null exits, exposure, and missingness are included. |
| 9 | Shortlist versus full-Maps unlock | **ESCALATE** | Full-Maps agreement exists; “wait for seats” is stale. Absorb its evidence and provenance without treating it as policy validation. | F9: acceptance relies only on shortlist positives or treats qualitative labels as cached checkout answers. |
| 10 | Authority and silent shipping | **KILL** implicit unlock | D0 already resides in merged DESIGN. Design registration does not authorize harness, hooks, or live behavior. | F10: an implementation cites this report or qualitative agreement as sufficient shipping authority. |

## 2. Per-axis notes

### 1. Decay shape

- Authoritative D0: `k0@75=3`, `k1@90=3`, `k2@105=2`, `k3@120=2`, `k4+@135+=1`.
- Opus’s floor-at-105 attack targets the obsolete strawman.
- D0 already delays its first reduction until `k=2`; DESIGN §6 question 1 partly restates existing behavior.
- `ca977`’s recommended 75–90 exit tests leap behavior while D0 remains at 3.
- `ca977` ends at 109, so it cannot validate either D0’s floor at 135 or prolonged floor exposure.
- **FORK:** retain timing; require evidence before lowering. **Falsifier:** F1/F4.

### 2. Calendar versus evidence-gated decay

- Real D0’s threshold follows `k`; absence of stop-signals does not hold the bar.
- This increases vulnerability to a later weak checkout, but does not force checkout on `continue`, `inconclusive`, or missing.
- Age is exposure, not proof of accumulated evidence.
- D1 must name the evidence predicate, persistence requirement, and handling of missing answers.
- Using diagnostic scores to control lowering creates a new policy beyond frozen P0; disclose and version it.
- **FORK:** compare D0 with D1 rather than declaring an unmeasured winner. **Falsifier:** F2.

### 3. Leap agreement and 92a48e

- [Shortlist agreement][shortlist]: Composer `late_pivot`, Grok `early_thrash`, Sonnet `unclear`; exits 180/90/null.
- [Full-Maps agreement][fullmaps]: Composer `late_pivot`, Sonnet/Grok `early_thrash`; shared thrash cues at 75–90.
- These are different experiments; retain both results and their provenance.
- Require agreement on why **continuing at this prefix is a mistake**, not merely matching labels.
- Two agreeing causal assessments can suffice; unanimity remains a sensitivity comparison.
- Full-run labels may inform evaluation but cannot be fed backward into the policy.
- **ESCALATE:** full-Maps 2/3 makes 92a48e a leap candidate, not an established leap. **Falsifier:** F3.

### 4. Floor confidence

- TERMS §6: score **0 = guess**, **1 = weak**, **2 = moderate**, **3 = convincing**.
- Opus incorrectly assigns “guess” to 1 and “weak” to 2.
- Floor 2 is a conservative preference, not demonstrated safety.
- Floor 1 needs evidence of incremental usefulness under the same persistence and qualification rules.
- The full-Maps master table has six workers reaching 135; overall `n=34` overstates floor exposure.
- `unclear` does not establish that every checkout would be false; it can reflect incomplete visibility.
- **FORK:** D1 floor 2 versus D1-F1 floor 1. **Falsifier:** F4.

### 5. Progress recovery and reset

- D0 contains no reset-on-progress clause; no reset defect is established.
- Do not add an upward reset based on one score or one Edit/Write.
- Conversely, an old thrash episode must not authorize a later checkout after genuine recovery.
- Keep the bar monotone; break the consecutive-evidence streak on recovery, contradiction, or missing evidence.
- A low bar remains insufficient without current firing qualification.
- **KILL:** proposed single-score reset. **Falsifier:** F5.

### 6. Phase/checkpoint collision

- Phase checks at 50/60/75 do not advance `k`; 75 remains checkout round 0.
- Dropping the 75 phase check changes the registered phase design and is unnecessary to establish ordering.
- Evaluate both questions against the same frozen prefix before applying either result.
- At 75, “not in validation” selects steer-only under §3; retain any checkout candidate in the audit.
- “Already in validation” permits qualified checkout; missing/inconclusive phase evidence requires explicit arbitration.
- At 76, preserve the closed `band_exit` meaning while preventing duplicate product actions.
- **ESCALATE:** combined-policy accounting and arbitration must be registered. **Falsifier:** F6.

### 7. Ignored additionalContext

- Delivery, acknowledgement, and successful handoff are different outcomes.
- Ignoring steer does not independently establish runaway behavior.
- A worker that avoids tests after steer may be complying; “still not in validation” cannot diagnose failure.
- Best-effort steering leaves a real efficacy gap, which must remain visible.
- Checkout may subsequently occur only through qualified leap/accumulate.
- **KILL:** automatic hard escalation for ignored steer; any stronger mechanism needs a separate experiment. **Falsifier:** F7.

### 8. Metric gaming

- Full Maps contains two strong thrash workers, not a broad demonstrated population of decay successes.
- P0 A0, shortlist shape recommendations, and full-Maps qualitative findings are different targets.
- Do not turn minority recommended exits into unanimous gold or revive rejected relabels.
- Report null exits and missing answers; paired-exit median overshoot alone hides failures to fire.
- Keep productive builds, sanctioned waits, poll/monitor workers, and Composer-only thrash cases in evaluation.
- Compare the turn-cap baseline C so early stopping alone cannot earn credit.
- **ESCALATE:** require coverage and counterexample reporting. **Falsifier:** F8.

### 9. Full-Maps unlock

- The inspected full-Maps report describes 102 seat verdicts across 34 workers and Phase 2 close-out.
- Opus’s assertion that full-Maps seats have not run is stale.
- That report also says seat verdict PRs are not merged; retain that provenance limitation.
- Its distinct poll/monitor family and weak Composer-only thrash cases materially challenge generic low-progress gating.
- It confirms qualitative evidence, not checkout calibration or successful handoff.
- **ESCALATE:** reconcile artifacts and review D1; do not wait for an already reported study. **Falsifier:** F9.

### 10. Placement and authority

- D0 already exists in DESIGN §2.2 with schedule identity and TERMS linkage.
- Opus’s claim that D0 exists only in a temporary context pack is obsolete.
- Preserve D0; identify this proposal as D1 rather than rewriting D0 silently.
- A reviewed canonical DESIGN table referenced from TERMS is sufficient; duplicating tables risks divergence.
- Register evidence rules, action semantics, gold protocol, and holds alongside the schedule.
- **KILL:** any inference that merged design or agreement permits implementation. **Falsifier:** F10.

## 3. Revised schedule: D1

**Identity:** `D1` — proposed, awaiting review and a TERMS §12 version note.  
**Grid:** `first_at=75`, `interval=15`, using TERMS `api_turn`.  
**Phase anchors:** 50/60/75 unchanged.  
**Floor:** 2.  
**Reset:** none.

D0 remains unchanged as the comparison:

| Round | Turn | D0 | D1 |
|---|---:|---:|---|
| 0 | 75 | 3 | 3 |
| 1 | 90 | 3 | 3 |
| 2 | 105 | 2 | 2 only if the preceding two checkpoints qualify; otherwise 3 |
| 3 | 120 | 2 | Retain 2 if lowered; otherwise lower only on qualifying preceding evidence |
| 4+ | 135+ | 1 | Same evidence-gated rule; floor remains 2 |

### Evidence required before lowering

A checkpoint supplies qualifying accumulation evidence only when all hold:

1. A valid `checkout_now == checkout` answer exists.
2. `runaway_pattern >= 2` **or** `scope_drift >= 2`.
3. `progress_since_prior <= 1`.
4. The available snapshot contains a concrete, turn-anchored observation supporting the concern.
5. The concern is not explained by an on-brief external wait, bounded validation work, or another supported productive trajectory.

Confidence below the current bar may qualify for accumulation; confidence alone does not qualify. Low progress alone also does not qualify.

If the benign-wait distinction cannot be established, that checkpoint does not supply lowering evidence. This conservative predicate is a hypothesis to test, not a finding.

### Transition rule

At checkpoint `c`, determine the bar from **earlier** checkpoints:

- Keep 3 through rounds 0 and 1.
- At `k≥2`, lower to 2 only after two immediately preceding scheduled checkpoints supplied qualifying evidence for the same continuing concern.
- Missing, inconclusive, recovery, or contradictory evidence breaks that streak.
- Once lowered, retain 2. Do not reset `k`, restore 3, or fall below 2.

Thus evidence at 75 and 90 first permits lowering at 105. Evidence first appearing at 90 and 105 first permits lowering at 120.

### Numeric bar versus authorized firing

D0 §2.1 defines firing through `R(t_k)`, while §2.3 adds substantive conditions for leap and persistence for accumulate. The document does not specify whether these are enforceable conditions or retrospective labels.

D1 resolves this explicitly: **meeting the numeric bar is necessary but insufficient**. A candidate fires only through a qualified path:

| Path | Qualification |
|---|---|
| **Leap** | `R(t_k)` passes, and current-prefix evidence supports near-done or a clear mistake-to-continue. When causal panel assessments exist, require at least two supporting the action and compatible factual cues. |
| **Accumulate** | The bar has been lowered; `R(2)` passes; the current and immediately preceding checkpoints supply qualifying evidence for the continuing concern. |

When causal panel assessments are unavailable, leap requires an auditable snapshot rationale with concrete supporting observations. Whole-run qualitative labels cannot substitute for that rationale.

A three-way split blocks a **panel-backed leap** unless action-level agreement is separately established. It does not permanently prevent evidence-based accumulation.

The full-Maps 92a48e majority satisfies neither path automatically: shape agreement is not a checkout answer or prefix-causal action judgement.

### Floor-1 challenger

**Identity:** `D1-F1`, a separate contrast cell.

Use D1’s evidence, persistence, qualification, and no-reset rules, but permit floor 1 from `k≥4` when preceding evidence qualifies. Its accumulate path requires `R(1)` plus the same current persistence requirement.

Compare:

- Fixed P0, bar 3.
- Fixed bar 2.
- Authoritative D0.
- Proposed D1.
- D1-F1.
- Turn-cap baseline C.

D1-F1 is not the preferred default.

### Limits and non-goals

- No changed checkpoint or phase anchors.
- No automatic parent-pull or hard exit for ignored steer.
- No diagnostic score directly replacing the checkout choice.
- No modification of P0, its gold, or the resolved question builder.
- No unconditional bounded-exit guarantee.

Persistent concern does not guarantee that `checkout_now` or confidence will ever satisfy the rule. Even D0 cannot guarantee checkout when confidence remains 0, choices remain inconclusive, or answers are missing. D1 intentionally allows persistent weak evidence to remain unresolved.

## 4. Offline falsifiers

**These are proposed checks, not reported replay results.** Use existing, compatible artifacts only. Qualitative seats are not substitutes for missing instrument answers. Missing evidence remains missing.

| ID | Offline check | What falsifies the proposal or claim |
|---|---|---|
| **F1** | Trace all registered schedules on identical available checkpoint answers; distinguish numeric candidates from qualified firings. | D1 produces no late benefit, materially delays supported stops, or increases premature exits beyond its registered gate. A 75–90 miss on ca977 specifically challenges leap adequacy. |
| **F2** | Trace quiet prefixes, sanctioned waits, and isolated weak checkout answers with no prior persistent concern. | D1 lowers before qualifying evidence, lowers before 105, or turns missing evidence into persistence. Calendar D0 outperforming D1 safely challenges the evidence-gating preference. |
| **F3** | Audit every leap’s cited turns and action rationale. Keep shortlist and full-Maps 92a48e assessments separate. | Future turns, whole-run shape labels, or label majority alone authorize an earlier leap. |
| **F4** | Compare D1 and D1-F1 only on workers reaching relevant rounds; report every floor-1-only exit. | Floor 1 introduces an unsupported premature exit on an adjudicated protected control. Conversely, supported incremental exits without added harm challenge floor 2’s preference. |
| **F5** | Walk concern → recovery → renewed concern sequences, including 92a48e’s disputed recovery arc. | A single progress score resets the bar, or pre-recovery evidence qualifies post-recovery accumulation. |
| **F6** | Inspect the 75/76 decision ledger under alternate evaluation orders. | Different orders change the applied action; phase checks alter `k`; duplicate steer occurs; steer is counted as `gate_exit`. |
| **F7** | Audit existing handoff drafts and any available outcome records. | Delivered steer is counted as successful handoff, ignored steer independently causes checkout, or cleaner-context benefit is asserted without evidence. |
| **F8** | Report all controls, null exits, missingness, length bins, floor exposure, and baseline C. | Claimed improvement depends on omitting negatives, non-firings, missing answers, short horizons, or baseline comparison. |
| **F9** | Reconcile the full-Maps inventory, master table, summaries, and seat provenance. | Inconsistent counts or unavailable source rows underpin acceptance; qualitative findings are presented as calibrated policy results. |
| **F10** | Review canonical registration and proposed unlock language. | D1 overwrites D0, lacks a TERMS version note, or design approval is treated as implementation or shipping approval. |

The full-Maps tier subtable currently sums to **33**, while the headline counts and master table describe **34**. Reconcile that discrepancy before using tier percentages as acceptance evidence.

Retain DESIGN’s proposed `false_early_rate ≤ P0 + 0.05`, lower false-late rate on long workers, smaller paired-exit overshoot, and no increased missingness. Pre-register how shape targets produce those measurements before calculating them.

Report counts and denominators beside rates. Under a fully powered 34-worker comparison, two additional false-early events would exceed a five-percentage-point allowance; the small sample cannot establish a general safety margin. An unsupported checkout on a specifically adjudicated productive/wait control should block the preferred default even when pooled metrics look favorable.

## 5. Explicit holds

| Hold | Required next gate |
|---|---|
| **No `--call-jev`** | Separate authorization and experiment scope; this report releases nothing. |
| **No Pilot live Jev** | Separate live-experiment approval. |
| **No swarm** | Separate authorization. |
| **No TypeSafe work** | Question-contract decisions remain design proposals. |
| **No code, hooks, plugin behavior, or harness edits** | Reviewed canonical design, versioned policy contract, then separately scoped harness work. |
| **No secrets or raw transcript dumping** | This review uses named design documents and aggregate evidence. |
| **No parent-pull revival** | A separately registered proposal with its own evidence and stop rules. |
| **No floor-1 default** | D1-F1 must establish incremental benefit under identical qualifications and negative controls. |
| **No behavior unlock from qualitative agreement** | Offline policy evidence and explicit acceptance remain necessary. |

## 6. Answers to DESIGN §6 open questions

| # | Answer |
|---|---|
| **1. D0 binding** | D0 already begins lowering at `k=2`, turn 105. Preserve it as comparison. Prefer proposed D1’s evidence gate at the same earliest anchor and floor 2. Any accepted revision needs its own schedule identity and TERMS note. |
| **2. Leap agreement** | Prefer at least **2-of-3 prefix-causal action assessments** with compatible factual evidence. Shape-label majority alone is insufficient. Compare unanimity as sensitivity; do not automatically block signal agreement because coarse labels differ. |
| **3. Separate question ID** | **Yes**, propose `validation-phase-v0` with its own definition, uncertainty handling, and provenance. Keep phase detection separate from checkout choice/confidence. No TypeSafe implementation in this fold. |
| **4. 50/60/75 versus band_exit 76** | Retain all anchors. Evaluate phase and checkout on the same frozen prefix at 75. Phase “not in validation” selects steer-only; “already in validation” permits qualified checkout. Log numeric candidates separately. At 76 preserve the closed baseline event and deduplicate product actions without retuning constants. |
| **5. Channel ownership** | WSM prose is sufficient for a steer **draft**. Measured orchestration needs structured records distinguishing judgement, attempted delivery, acknowledgement, spawn, and outcome, with source checkpoint and policy identity. |
| **6. New-agent contract** | Propose a fresh validation context containing the brief, acceptance criteria, artifact/commit identity, build summary, known failures, validation plan, and necessary bounded excerpts. The driver owns identities and parent-child lineage. A full-context fork cannot be claimed to provide cleaner context without measurement. |
| **7. Gold target** | **Yes:** shape/early-signal/inflection evidence governs decay acceptance; P0 retains A0. Version the shape evaluation protocol and retain uncertainty. Whole-run evidence can describe outcomes but cannot become an earlier policy input. |
| **8. Cell naming** | Use progressive `proofs/` for explicitly named future cells such as `P_decay_D0`, `P_decay_D1`, and `P_decay_D1_F1`, cross-linked from the matrix. Record evidence rule, firing qualification, gold version, and action semantics; never rewrite frozen P0. |
| **9. Inconclusive phase check** | **Fail-open silent; retry at the next existing anchor.** Do not infer “not in validation,” steer, or checkout from uncertainty. At the shared 75 checkpoint, retain the independent checkout candidate for analysis but apply no phase-dependent product action without resolving the phase uncertainty. |
| **10. Confidence versus decay** | **Keep distinct.** Per-seat claim confidence concerns an asserted observation; checkout confidence concerns the checkout choice; `confidence_min` is a policy threshold. None converts directly into another. |

**Disposition:** D0 remains the authoritative registered comparison. D1 is the preferred design proposal, with D1-F1 as challenger. Neither is implemented, validated, or authorized to ship by this review.

[terms]: /home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/TERMS.md
[shortlist]: /home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md
[fullmaps]: /home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-qual-full-maps-v1/AGREEMENT-SUMMARY.md

---

# Part 2 — WSM synthesis (DESIGN + remapped Opus)

# Adversarial review — progressive decay bar D0 (WSM synthesis)

**Date:** 2026-10-01 (Australia/Brisbane, AEST)  
**Ground truth:** master `6957b5b` `DESIGN-progressive-decay-bar-v0.md` (PR #91)  
**Inputs:** Sol high Part 1; Opus Part 3 remapped off strawman onto real D0; TERMS §§11–14; shape-signal + full-maps agreement summaries  
**Out of scope:** `--call-jev`, Pilot live Jev, swarm, TypeSafe, hooks, secrets, code

## Authoritative D0 (DESIGN §2.2)

| Round k | Turn | t_k |
|---------|------|-----|
| 0 | 75 | 3 |
| 1 | 90 | 3 |
| 2 | 105 | 2 |
| 3 | 120 | 2 |
| 4+ | 135+ | 1 |

## Executive kill/fork/escalate (aligned with Sol; notes where Opus differed)

| # | Axis | Verdict | Note |
|---|------|---------|------|
| 1 | Decay shape slow/fast | **FORK** | Real D0 already delays first drop to k=2/105 (Opus “too fast to 105” was strawman). Compare evidence-gated **D1**. |
| 2 | Calendar vs evidence-gated | **FORK** (Sol) / prefer evidence gate | Pure round-index lowering without persistent stop-evidence is the attack; Sol notes checkout still required to fire. |
| 3 | Leap on 92a48e shape split | **ESCALATE** | Shortlist three-way split vs full-maps 2/3 thrash — keep separate; need prefix-causal leap predicate, not label majority alone. |
| 4 | Floor t=1 vs 2 | **FORK → prefer 2** | Floor 1 = challenger **D1-F1** only. |
| 5 | Bar reset on progress=3 | **KILL** (adding reset) | DESIGN omits reset — keep omission. Recovery breaks evidence streak; does not raise bar. |
| 6 | 50/60/75 vs 75:15 + band_exit@76 | **ESCALATE** | Sol: keep anchors, specify same-prefix precedence. Opus preferred phase 50/60 only — treat as fork option under escalation. |
| 7 | Soft steer ignored → escalate? | **KILL** auto hard escalate | Record failed handoff; independent checkout evidence only. |
| 8 | Metric gaming thrash-only | **ESCALATE** | Stratify non-thrash; include nulls/exposure/missingness. |
| 9 | Unlock shortlist vs full-maps | **ESCALATE** | Sol: full-maps agreement exists — “wait for seats” stale; still not policy validation / ship unlock. |
| 10 | Where D0 lives / silent-ship | **KILL** implicit unlock | DESIGN on master is correct home; registration ≠ hooks/`--call-jev`. |

## Revised D1 (pre-registration)

- Keep `(75,15)` grid; new id **D1** (do not silently edit D0).
- Evidence-gated credit before lowering `t`; earliest drop still ≥105.
- Floor **t=2**; challenger **D1-F1** floor 1.
- Leap: ≥2-of-3 **prefix-causal action** assessments + compatible facts (Sol); shape-label majority alone insufficient; shortlist 3-way split blocks casual leap.
- No upward bar reset.
- Phase/checkout at 75: same-prefix eval; steer ≠ `gate_exit`; inconclusive phase → fail-open silent.
- Gold: shape/earliness for §12; P0 keeps A0 (two fit rules).

## Offline falsifiers

F1–F10 as in Sol Part 1 (late-miss improvement, calendar vs evidence, leap dependency, floor1 unique false-early, recovery/stale evidence, phase ordering, ignored-steer alone, gaming controls, shortlist-only acceptance, silent-ship citation).

## Holds

No `--call-jev`, hooks, Pilot live Jev, swarm, TypeSafe, harness behaviour, parent-pull gold, or behaviour unlock from qualitative agreement alone.

---

# Part 3 — Opus 4.6 first pass (strawman-grounded; remapped in Parts 1–2)

# Adversarial design review — `progressive-decay-bar-v1` / `validation-handoff-steer-v1`

**Reviewer:** Opus 4.6 (design-only, no code, no `--call-jev`)
**Date:** 2026-10-01 (Brisbane)
**Grounding:** context-pack.md; TERMS §§11–14; NEXT-EXPERIMENTS; shape-signal-agreement-SUMMARY-20261001; GUIDANCE; CANDIDATE-APPROACHES; CYCLE-LOG

---

## Executive kill/fork/escalate table

| # | Axis | Verdict | One-line rationale |
|---|------|---------|-------------------|
| 1 | D0 decay shape too slow/fast? | **FORK** | 3→2→1 in two intervals (~30 turns) may be too fast for `late_pivot` shapes; too slow for `early_thrash` where ca977 unanimous exit is 75–90. Need two schedules or evidence-gated speed. |
| 2 | Calendar vs evidence-gated decay | **KILL** (calendar-only) | Calendar decay rewards quiet thrash that produces no stop-signals at each checkpoint. Evidence-gated decay is strictly more informative and avoids the P0 A0-null family where 5/7 workers are `unclear` with no stop-signals at any checkpoint. |
| 3 | Leap agreement when shape split (92a48e) | **ESCALATE** | 92a48e has a three-way shape split (late_pivot/early_thrash/unclear). Leap requires "near-done agreement" but the only shared signal is thrash@~90 — and Composer exits@180, Grok@90, Sonnet@null. Leap's agreement threshold is undefined. |
| 4 | Floor t=1 vs stay at 2 | **FORK** | t=1 fires on guesses (confidence criterion: "a guess"). t=2 fires on "weak; a careful reader could easily disagree." Neither has offline evidence. Fork: run both in the counterfactual sweep and measure false-early rate. |
| 5 | Bar reset on progress=3? | **KILL** (as specified) | A single progress=3 score resetting the bar creates a ratchet exploit: one productive-looking turn resets decay, then thrash resumes. The 92a48e worker had productive stretches between thrash bouts (Composer saw late_pivot for exactly this reason). Reset must require sustained progress, not a single score. |
| 6 | 50/60/75 phase vs 75:15 checkout collision | **ESCALATE** | At c=75, both validation-phase-detect AND the first P0 checkout fire simultaneously. Which runs first? If phase-detect says "not in validation" and steers to a new agent, the checkout signal is swallowed. If checkout fires first, the steer never happens. Ordering is unspecified. |
| 7 | Soft additionalContext ignored → escalate? | **FORK** | §13 says "prefer additionalContext (or parent steer)" but the context-pack notes this is a later product decision (non-goal). Fork: define a concrete escalation path when the soft channel is ignored (the agent continues building past the steer), vs leaving it as best-effort with no fallback. |
| 8 | Metric gaming (thrash-only earliness) | **ESCALATE** | The only non-null A0 in the entire study is ca977@90 — a unanimous early_thrash worker. D0 tuned on this single positive example will overfit to zero-Edit/Write, high-reread, high-compaction shapes. The five `unclear` workers (majority of the shortlist) have no checkout at any bar, so D0 cannot be falsified on them. |
| 9 | Unlock on shortlist vs wait full-maps | **FORK** | shape-signal-panel-v1 agreement exists on 7 workers (2 with usable signal, 5 unclear). shape-qual-full-maps-v1 has 34 workers packed but seats not run. D0 designed on 7 may not survive 34. Fork: write D0 now but hold harness until full-maps seats land. |
| 10 | Where D0 lives so agents can't silent-ship hooks | **KILL** (current placement) | D0 strawman lives in the context-pack, not in TERMS. An agent editing hooks could claim D0 authority from an unversioned scratch doc. D0 must live in TERMS (as a new §, or appended to §12) with the same sign-off chain as §§1–14. |

---

## Per-axis deep notes

### 1. D0 decay shape too slow/fast?

The strawman decays 3→2→1 over two consecutive accumulate-eligible rounds, meaning the floor is reached ~30 turns after first test (at c=75, floor by c=105). For ca977 (unanimous early_thrash, exits 75–90), this is **too slow**: the panel says continuing past 75–90 is already a mistake, but D0 at t=3 requires maximum confidence at c=75 — exactly the bar that P0 already uses and that produced A0=null on the original panel (α=0.1189). For 92a48e (T=296, shape split), the floor at c=105 means 191 more turns at t=1, which fires on guesses. The decay shape needs to be **conditional on signal strength**, not a fixed calendar ramp. **Falsification:** counterfactual sweep with D0 on the 7 shortlist workers; compare `gate_exit` under D0 vs fixed t=3 vs fixed t=2. If D0's `gate_exit` on ca977 is later than the panel's recommended exit (75–90), the schedule is too slow.

### 2. Calendar vs evidence-gated decay

D0 strawman: "one decay step per scheduled checkpoint interval (~15 turns), if stop-signals present; else hold bar." The "if stop-signals present" clause makes this evidence-gated in name. But what counts as a stop-signal? If it's `checkout_now==checkout` at any confidence, then every Jev response that says checkout (even at confidence 0) triggers decay — effectively calendar. If it's the pattern scores (`runaway_pattern>=2` or `progress_since_prior<=1`), those are diagnostic scores that §6 explicitly says "do not feed R(t)." Using them for decay but not for firing creates a shadow decision rule. **Kill the calendar-only version.** Evidence-gated decay must be defined against an explicit signal predicate, written in the same style as R(t), before the schedule is pre-registered. The 5/7 workers with majority-`unclear` shape and null exits across all seats show that stop-signals may simply never appear for most sessions — calendar decay on those would hit the floor and fire on noise.

### 3. Leap agreement when shape split (92a48e)

Leap requires "checkout_confidence >= t_k AND near-done agreement (shape/early-signal not merely single score)." On 92a48e: Grok says early_thrash@90 (confidence presumably high — it recommended exit); Composer says late_pivot@180 (different shape entirely); Sonnet says unclear@null (no exit). At c=90, a leap would need to evaluate "near-done agreement" across these seats. But the seats **disagree on whether the session is near done at all**. Composer thinks productive work continues until 180. The definition of "near-done agreement" is load-bearing and missing. Is it unanimous shape? Majority? Signal overlap (thrash@~90 appears in >=1 seat)? If signal overlap suffices, then Grok's single early_thrash vote plus shared thrash indicators could clear leap — but that's "one noisy score" dressed up. **Escalate:** define the agreement predicate for leap before pre-registration. Propose: leap requires >=2 seats with compatible shape labels (early_thrash+early_thrash, or late_pivot+late_pivot) AND shared early signals. A three-way split blocks leap; accumulate only.

### 4. Floor t=1 vs stay at 2

t=1 criterion: "a guess." t=2 criterion: "weak; a careful reader could easily disagree." The gap between these is whether Jev's self-reported confidence of 1 (out of 3) should trigger checkout. On P0 with fixed t=3, α was 0.1189 and A0 was null — the panel couldn't agree at maximum confidence. Lowering to t=1 means checkout fires when even Jev isn't sure. The false-early risk is acute: on the 5 unclear workers, any stray checkout@confidence=1 at the floor round fires the gate. On ca977, t=1 is irrelevant (unanimous early_thrash; confidence presumably 3). **Fork:** run the counterfactual at both floors. Measure false-early rate on the unclear workers at t=1 vs t=2. If t=1 produces false-early on any worker where all three shape-signal seats said `unclear` with null exit, t=1 is killed. Stay at t=2 as the default floor.

### 5. Bar reset on progress=3?

D0 strawman: "if progress score returns to healthy (e.g. progress=3 / productive Edit/Write resume), reset t toward 3." This creates a **pump** exploit visible in the 92a48e empirics: Composer labeled it `late_pivot` precisely because there was productive work between thrash bouts. At checkpoint ~105 the worker might show progress=3 (one checkable step in the delta), resetting the bar to 3, then thrash resumes by ~120, and the bar has to decay all over again. Over 296 turns, this reset could fire multiple times, each time buying ~30 turns before the floor is re-reached. The parent-pull-v1 experiment already showed overfire risk (@255) when Sonnet was too eager — a reset mechanism amplifies this by making the bar oscillate. **Kill as specified.** Replace with: bar never resets upward. Once decayed, it stays. If the session genuinely recovers, that's a leap opportunity (high confidence + near-done agreement), not a bar reset. The decay is a ratchet, not a pendulum.

### 6. 50/60/75 phase vs 75:15 checkout collision

§13 says validation-phase checks fire at ~50, 60, 75, then continuing on §2 schedule. §12/P0 says first checkout at 75, interval 15. At c=75: (a) phase-detect asks "is the agent in validation?" and (b) the first session-checkout R(t) fires. Three collision scenarios:

- **Phase-detect first, says "not in validation":** steer fires, tells builder to wrap up, hands to new agent. The checkout signal at the same turn is now about a builder that's being steered away — does it still apply? If so, the steer and the checkout contradict (steer says "hand off gracefully" while checkout says "stop now").
- **Phase-detect first, says "in validation":** falls through to §12. Checkout fires normally. No collision, but the validation label might be wrong at c=75 (agent could still be building at turn 75 in many sessions).
- **Checkout first, fires:** the agent is checked out before phase-detect runs. The steer path is dead.

**Escalate:** specify ordering. Recommend: phase-detect runs at 50, 60 only (before the checkout schedule starts). At 75+, only §12 runs. This eliminates the collision entirely and preserves the steer window (50–60) for build-vs-validation detection before checkout is even possible.

### 7. Soft additionalContext ignored → escalate?

The context-pack explicitly says "feedback channel (parent vs additionalContext) is later product decision; pack does not design/prove that channel." §13 says "prefer" soft steer but has no fallback. If the agent ignores `additionalContext` (which is plausible — it's a hint, not a hard stop), the builder continues past the steer point. With no escalation path, the only remaining gate is §12 accumulate, which takes ~30 turns to reach the floor. That's 30 turns of build work that should have been handed off.

**Fork:** (A) Define an escalation: if the agent's next 2 checkpoints show no validation-phase behavior after a steer was sent, treat it as a failed steer and escalate to a hard parent-pull or checkout. (B) Accept that soft steer is best-effort and rely entirely on §12 decay. Option A requires product wiring that's out of scope. Option B is the current default but should be written down as an explicit acceptance of the gap, not left implicit.

### 8. Metric gaming (thrash-only earliness)

The entire gold corpus has exactly **one** non-null A0: ca977@90. The only workers with unanimous shape agreement are ca977 (early_thrash) and the five unclear workers (which all agree on "nothing to checkout"). D0's decay schedule can only be evaluated against ca977 as a positive example. Any schedule that fires at 90 on ca977 "works" — including turn-cap baseline C (which fires at 75 with zero Jev calls and is strictly earlier than A0@90). The §8 baselines already flag this: "if C matches gold as well as Jev, the questions are not earning their keep."

92a48e is the only other worker with shared thrash signals, but its shape is split and it has no A0. D0 cannot be falsified on it because there's no gold exit to measure overshoot against. The 5 unclear workers contribute only false-early checks (any gate_exit is false-early on a null-gold worker).

**Escalate:** D0 must not be tuned on 1 positive example. Hold D0 pre-registration until shape-qual-full-maps-v1 Phase 2 seats run (n=34). If that still yields <=2 non-null A0 equivalents (under signal-agreement rather than unanimous exit), the decay schedule cannot be empirically validated and should be flagged as convention, not result.

### 9. Unlock on shortlist vs wait full-maps

shape-signal-panel-v1 agreement exists (7 workers). shape-qual-full-maps-v1 Phase 1 is done (34 workers packed, 104 rows). Phase 2 seats are held. The GUIDANCE doc says "hold until shape-signal agreement lands" — that's met. But §14 expands the aperture to 34 workers with an early-signal window ≤120T that doesn't exist in the 7-worker shortlist analysis.

Risk of designing D0 on shortlist only: the 27 un-seated workers may include shapes D0 doesn't handle (e.g., productive-build-to-commit workers where the session is long but healthy — D0's decay would fire on noise). The phase-1a marker screen (CYCLE-LOG) already showed strict thrash shape is **empty** outside ca977 in the maps pool. D0 designed against that pool has no thrash-positive validation set beyond one worker.

**Fork:** write D0 now (design authority from shortlist agreement), but gate harness implementation on full-maps Phase 2 landing. D0 becomes a pre-registered hypothesis that full-maps either confirms or kills. This avoids blocking the design while protecting against premature shipping.

### 10. Where D0 lives so agents can't silent-ship hooks

The D0 strawman currently lives in the context-pack (a `/tmp/` file) and is described as "NOT in TERMS yet." TERMS §12 says "harness work; pre-register before any live run" but doesn't contain the actual schedule. An agent with hook-editing permissions could write a decaying bar into the harness citing "§12 intent" without a signed D0. The GUIDANCE doc says "no hooks, no `--call-jev`" but references the agreement prerequisite (now met), creating ambiguity about whether the hook hold is still active.

**Kill current placement.** D0 must be:
1. Written as TERMS §15 (or §12.1) with the same "NOT SHIPPED" header as §§12–13.
2. Carry an explicit `status: pre-registered, not shipped` and a version hash.
3. GUIDANCE must be updated to say "hold hooks until D0 schedule in TERMS is reviewed" (not just "until agreement lands," which is now met).

Without this, the next agent session that reads GUIDANCE will see the agreement prerequisite as cleared and may attempt hook work.

---

## Revised D0 (pre-registration grade)

Based on the kills and forks above, the D0 strawman is revised. This is a **design proposal**, not a shipped schedule.

### D0-revised

```
name: progressive-decay-bar-d0-revised
status: pre-registered, not shipped, not in TERMS
version: 2026-10-01-adversarial-fold

schedule:
  first_at: 75
  interval: 15

bar:
  t_0: 3
  decay_trigger: evidence-gated (NOT calendar)
  decay_predicate: >
    checkout_now == checkout at ANY confidence
    at checkpoint c, AND at least one of:
      runaway_pattern >= 2
      progress_since_prior <= 1
    (pattern scores used as decay gate only, not as R(t) firing)
  decay_step: 1 per eligible round
  floor: 2 (NOT 1)
  reset: NEVER (bar is a ratchet, not a pendulum)

sequence: 3 → 2 (floor)
  - t_0 = 3 at c=75
  - first eligible decay: earliest c >= 90 where decay_predicate holds
  - floor t=2 thereafter; no further decay

leap:
  requires:
    - checkout_now == checkout
    - checkout_confidence >= current t_k
    - shape/signal agreement: >= 2 seats with compatible shape
      labels AND shared early signals (when seats exist)
    - a three-way shape split BLOCKS leap; accumulate only

accumulate:
  requires:
    - decay_predicate true at >= 2 consecutive checkpoints
    - bar at floor (t=2)
    - R(2) fires: checkout_now == checkout AND confidence >= 2

validation_phase:
  phase_detect_at: [50, 60]  # BEFORE checkout schedule starts
  checkout_starts_at: 75     # phase-detect does NOT run at 75+
  steer: soft additionalContext (best-effort; no escalation in v1)
  fallback: §12 decay (accepted gap; product wiring later)

non-goals:
  - bar reset on progress recovery (killed)
  - t=1 floor (forked; requires false-early evidence on unclear workers)
  - calendar-only decay (killed)
  - escalation on ignored steer (forked; product wiring)
  - tuning on <3 positive gold exits (escalated)
```

### Key changes from strawman

| Strawman | Revised | Reason |
|----------|---------|--------|
| Floor t=1 | Floor t=2 | t=1 fires on self-reported guesses; unacceptable false-early risk on 5/7 unclear workers |
| Calendar decay | Evidence-gated with explicit predicate | Calendar rewards quiet thrash; evidence gate uses the diagnostic scores §6 already defines |
| Bar reset on progress=3 | No reset ever | 92a48e shows productive stretches between thrash bouts; reset creates a pump exploit |
| Phase-detect at 50/60/75 | Phase-detect at 50/60 only | Eliminates collision with first checkout at c=75 |
| Leap agreement undefined | >=2 compatible seats + shared signals; split blocks | 92a48e three-way split shows undefined agreement is not falsifiable |
| Lives in context-pack | Must be TERMS §15 or §12.1 | Prevents silent hook shipping by agents reading met-agreement GUIDANCE |

---

## Offline falsifiers (no `--call-jev`)

These tests use existing artifacts only — no Jev calls, no swarm, no live hooks.

### F1. Counterfactual sweep on shortlist (7 workers)

Using the signed P0 panel verdicts and shape-signal seat verdicts, compute `gate_exit` under:
- D0-revised (evidence-gated, floor=2, no reset)
- D0-strawman (calendar, floor=1, reset on progress=3)
- Fixed t=3 (P0)
- Fixed t=2
- Turn-cap baseline C

**Kill D0-revised if:** `gate_exit` on ca977 is later than panel recommended exit band (75–90), OR any unclear worker gets a false-early gate_exit.

### F2. Reset pump test on 92a48e

Walk the 15 checkpoints of 92a48e (75–285). At each, apply the D0-strawman reset rule (progress=3 resets bar). Count how many times the bar cycles 3→2→1→3. If cycles > 1, the reset is confirmed as a pump. Already killed in revised D0; this falsifies the strawman.

### F3. Phase-detect collision audit

List all workers where T >= 75. At c=75, check if the phase-detect question ("in validation?") and the checkout question would give contradictory signals. Use the existing hybrid_v0 pack at c=75 to assess whether the worker is building or validating. If >50% of workers at c=75 are still building, phase-detect at 75 would trigger steer on the majority — swamping the checkout signal.

### F4. Floor sensitivity on unclear workers

For each of the 5 unclear workers (bb6165, 0aab88, 036ff3, 7b0022, 5163c2), check: at what bar level does the first stray `checkout` verdict (if any exists in the P0 panel) fire R(t)? If any fires at t=1 but not t=2, that's a false-early unique to t=1 — confirms the floor=2 fork.

### F5. Evidence-gate predicate coverage

On the P0 panel's diagnostic scores (runaway_pattern, progress_since_prior), count how many checkpoints across all 7 workers would trigger the decay predicate (`checkout_now==checkout AND (runaway_pattern>=2 OR progress_since_prior<=1)`). If the predicate fires on <2 checkpoints total, evidence-gated decay never actually decays and is operationally equivalent to fixed t=3 — the gate is too strict.

### F6. Full-maps early-signal density

When shape-qual-full-maps-v1 Phase 2 seats land, count workers with >=1 shared early signal (<=120T) that foreshadows checkout. If that count is <=2 (i.e., only ca977 + possibly 92a48e), D0 has no validation corpus and must be flagged as convention.

---

## Explicit holds

| Hold | Reason | Release gate |
|------|--------|--------------|
| No `--call-jev` | GUIDANCE + TERMS §12 "not shipped" | D0 in TERMS, reviewed, + full-maps Phase 2 seats |
| No hook bytes | GUIDANCE "no hooks" | D0 reviewed + counterfactual sweep (F1) shows D0 beats P0 on gold-relevant metrics |
| No Pilot live Jev | Out of scope for this fold | Separate experiment registration |
| No swarm runners | Out of scope | Separate experiment registration |
| No TypeSafe | Out of scope; open-field candidate approaches are independent | Their own kill/gate criteria |
| No parent-pull-v1 | Experiment (b) FAILED (overfire @255) | New experiment with pre-registered stop rules |
| No bar reset | Killed in this review (pump exploit) | Would require sustained-progress definition + counterfactual evidence on >=3 positive exits |
| No t=1 floor | Forked pending false-early evidence | F4 must show t=1 does not false-early on unclear workers |
| GUIDANCE update | Agreement prerequisite is met; GUIDANCE must now reference D0 review as the new hold | Write updated GUIDANCE after D0 enters TERMS |
| D0 placement | Currently in /tmp context-pack | Must be TERMS §15 or §12.1 before any harness work |
