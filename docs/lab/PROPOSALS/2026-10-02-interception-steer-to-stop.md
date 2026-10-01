---
title: Interception / steer-to-stop
status: resolved-soft
disposition: recommendations recorded; product and hooks held; trial waves GO
date: 2026-10-02
updated: 2026-10-02
signal: Steer-to-stop has to catch jobs that would run long and leave near-done closing work alone; Wave-0 Flash trials exist and are not an FP/miss board.
owners: Workflow Optimiser, Cody
extends: docs/lab/PROPOSALS/2026-10-01-progressive-jev-session-gates.md
confidence: protocol-resolved; framings provisionally ordered; not score-ranked
---

# Interception / steer-to-stop

**Soft Standard HOLD — product and hooks only.** This paper does not ship behaviour, hooks, Pilot, Standard, Max, or live in-loop Jev. It does not pause trials. Flash, TypeSafe, and Luna measurement waves are GO without a further greenlight.

**Status: resolved-soft.** Recommendations below are the lab’s current reading of the pack, the adversarial gate, and Wave-0. They are not an accepted runtime policy. Cody’s accept is what would later turn a measured rule into product wiring.

Research pack: [`../RESEARCH/2026-10-02-interception-steer-to-stop/`](../RESEARCH/2026-10-02-interception-steer-to-stop/INDEX.md). Trials: [`../RESEARCH/2026-10-02-interception-trials/`](../RESEARCH/2026-10-02-interception-trials/INDEX.md).

This is the next layer after [`2026-10-01-progressive-jev-session-gates`](2026-10-01-progressive-jev-session-gates.md) (`status: researching`). That pack keeps the ~75 then ~15 re-check intuition and tried to tune it against multi-model gold (H5 failed, Krippendorff’s α 0.1189). This paper keeps the re-check intuition, rejects monitor agreement as gold, and scores fire-time against a non-length outcome sheet. It does not retune `A0`, `gate_thresholds.py`, or the resolved cheap-Jev use cases.

## Hold scope

| Surface | Disposition |
|---------|-------------|
| Hooks, `additionalContext`, parent-surface injection, `install.sh`, driver defaults, `assert_phase` defaults, `gate_thresholds.py`, `classify.py` | Held |
| Pilot, Standard, Max, live in-loop Jev | Held |
| Flash, TypeSafe (`jev-1.13.0`), and Luna **trial** waves on frozen prefix snapshots | **GO** — no behaviour greenlight required |
| FP/miss leaderboard | Starts when [`outcome-labels.jsonl`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md) exists and is joined |
| Variant generation | Runs in parallel with labeling |

### Resolved recommendations

Record the hold as two columns, not one lock. Product wiring stays off. The next measured corpus starts now, under the waves in [Next spikes](#next-spikes).

## Signal

Maps workers run far past a useful stop. The cheap-Jev maps pass scored 150 subagents; 24 (16%) were over the 50–75 turn band, and worker `92a48e004519` reached 296 API calls ([`2026-09-30-jev-cheap-judgement-signals`](2026-09-30-jev-cheap-judgement-signals.md)). The progressive pack notes that the closed gate logs `band_exit` once near turn 76 and does not ask again at 90, 105, and onward ([`2026-10-01-progressive-jev-session-gates`](2026-10-01-progressive-jev-session-gates.md)).

Cody’s success framing for interception, kept as one hypothesis among several in [`H1-DETAIL.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/H1-DETAIL.md) and pack §F:

- Trigger on jobs that would go long.
- Leave near-done closing work alone. A stop at 75 on a job that would finish near 85 is a bad interception. An intercept near 90 on a trajectory that would otherwise run toward 360 is a good one.
- If the checkpoint shows hard development and confidence backed by progress, let the job run and look again about 15 turns later.
- Measure `(state, question, response-class) → predictive rating → fire-time vs ideal steer`. LLMs drive lever volume. Multi-model agreement is not gold.

Wave-0 has already burned Flash on a provisional shortlist. Opus blocked score-ready claims on that first batch ([`ADVERSARIAL-GATE-opus.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/ADVERSARIAL-GATE-opus.md) R1–R3). batch-002 fixed the protocol. The non-length outcome sheet then landed as a labeling protocol with an empty sidecar ([`OUTCOME-SHEET.md`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md), [`EVIDENCE-LOG.md`](../RESEARCH/2026-10-02-interception-trials/EVIDENCE-LOG.md)).

### Resolved recommendations

Treat the signal as a timing problem with two failure prices: truncating closing work, and missing a trajectory that keeps spending turns after value has stopped. The measurement chain in `H1-DETAIL.md` is the scoring grammar for every later wave. Agreement among Flash, TypeSafe, and Luna stays an H6 footnote.

## Problem

A single `band_exit` row tells an archaeologist that a worker left the band. It does not decide whether **now** is a useful time to steer toward stopping. The pack’s chain is assessment → decision → timing → steer execution → outcome ([`RESEARCH-PACK.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/RESEARCH-PACK.md) §A.2). Offline replay can see the first three. Steer adherence is unmeasured. Fewer turns is not the objective: a long productive session is a success case for deferral, and a short natural completion has no steer window (`ideal_steer_window = none` in the outcome sheet).

Who pays today is concentrated. The cheap-Jev paper’s heaviest 5-hour window is about 63.35M tokens. A handful of fat workers dominate that burn. An always-on frontier review of every turn fights `GOALS.md`, which already lists per-turn Jev inside the worker loop as out of remit. A length cap fights the same evidence the adversarial gate named: batch-001’s ideal window was a function of final `T`, so “long” was scored as “runaway” ([`batch-001/PROTOCOL.md`](../RESEARCH/2026-10-02-interception-trials/batch-001/PROTOCOL.md), [`LEAKAGE-NOTE.md`](../RESEARCH/2026-10-02-interception-trials/batch-001/LEAKAGE-NOTE.md)).

### Resolved recommendations

Keep authoritative pass/fail on the existing deterministic phase assert. Interception, when it is eventually wired, is an advisory steer behind that kill line. Until then the lab’s job is a measured corpus: prefix-only state, several questions, several response classes, several instruments, joined later to human labels that do not use final length.

## Proposal

### 1. Protocol — R1, R2, R3

| Gate | batch-001 | batch-002 and the outcome sheet | Still empty |
|------|-----------|----------------------------------|-------------|
| **R1** outcome leak into the judge | Blocked. Prompts carried `T_observed_session`. Lite states carried `approx_progress_frac = cp/T`, `T_observed`, `userish_count_full_session` ([`LEAKAGE-NOTE.md`](../RESEARCH/2026-10-02-interception-trials/batch-001/LEAKAGE-NOTE.md)) | Fixed. Those fields are removed. [`LEAKAGE-AUDIT.md`](../RESEARCH/2026-10-02-interception-trials/batch-002/LEAKAGE-AUDIT.md) passes if the runner matches the table. Prompt leak spotcheck hits: **0** ([`METERS.md`](../RESEARCH/2026-10-02-interception-trials/batch-002/METERS.md)) | Re-audit every new state builder before that batch is called clean |
| **R2** length as the reference window | Blocked. `ideal_window(T)` tagged `near_done_fp` / `runaway_hit` / `runaway_miss_candidate` from observed T alone | The **protocol** is closed. [`OUTCOME-SHEET.md`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md) freezes near-done vs runaway-like observables, windows of `none` / `[t_start, t_end]` / `ambiguous`, and the sidecar schema. [`PROTOCOL.md`](../RESEARCH/2026-10-02-interception-trials/batch-002/PROTOCOL.md) §R2 sets `window_status = unidentified` and `reference_fire = null` | **Labels.** No `batch-002/outcome-labels.jsonl`. Every `results.jsonl` cell is `window_status=unidentified`, `outcome_tag=null` |
| **R3** schedule leaks T | Blocked. Long sessions used 75:15; shorter ones used T-proportional slices | Fixed. `FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)` for every session. Cells exist only when the session survived to t. `n_at_risk` and `n_never_reached` are in the meters | The schedule is a measurement scaffold. It is not a shipping cadence |

What the outcome sheet closes: the R2 documentation gate. Reviewers label from transcript and deliverable facts (closing work, thrash, post-boundary overrun, scope drift, natural completion). Runaway-like needs a pattern in the rationale, default span at least 8 assistant turns, not a large `T`. Final length, `cp/T`, Flash `rating` / `fire`, and “this checkpoint exists, therefore the session is long” are out of the label.

What the outcome sheet leaves open: the rows. `label_status` stays unfilled. FP/miss names in the sheet (`near_done_fp`, `runaway_hit`, `runaway_miss`, `productive_interrupt`) apply only after a join. Until that join, meters stay diagnostics.

Labeling runs **beside** the next waves. It does not block them. The labeler writes from the transcript before opening that session’s `results.jsonl` (outcome sheet independence rule). Flash, TypeSafe, and Luna stay out of the `labeler` field.

#### Resolved recommendations

Call R1 fixed, R3 fixed, and R2 closed at the protocol layer. Call the FP/miss board unopened until `outcome-labels.jsonl` is published and joined under the sheet. Start Wave-1 variant generation without waiting for that file.

### 2. batch-001 — quarantine

[`batch-001/LEAKAGE-NOTE.md`](../RESEARCH/2026-10-02-interception-trials/batch-001/LEAKAGE-NOTE.md) and the banner on [`batch-001/METERS.md`](../RESEARCH/2026-10-02-interception-trials/batch-001/METERS.md) already quarantine the batch: plumbing only, T leak, not score evidence. The same quarantine covers `batch-001/archive-skew-v0/`.

The outcome tags in that meters file (cell-level `defer_ok` 114, `runaway_miss_candidate` 50, `runaway_hit` 10, `premature` 6; session rollup hits 1 and misses 2 on `long_runawayish`; `near_done_fp` cells 0) are the R2 failure mode written down. They measure a judge that could see length, scored against a window built from length. Keep the files for a leak-ablation contrast. Quote them as contamination evidence only.

`batch-002/archive-t45-only/` is a discarded allocation run that only sampled checkpoint 45 ([`EVIDENCE-LOG.md`](../RESEARCH/2026-10-02-interception-trials/EVIDENCE-LOG.md)). It is not evidence either.

#### Resolved recommendations

Score from `batch-002/` onward. Leave batch-001 and both archives in place, unscored.

### 3. How to read batch-002 meters

Canonical diagnostic table: [`batch-002/METERS.md`](../RESEARCH/2026-10-02-interception-trials/batch-002/METERS.md) and [`meters.json`](../RESEARCH/2026-10-02-interception-trials/batch-002/meters.json). `meters_class` is `score-ready-path-diagnostics`. `score_ready_fp_miss_board` is false. Soft hold flags in the file: TypeSafe unused, Luna unused, hooks unused. Flash’s role is `policy-under-test`.

| Published figure | Value |
|------------------|-------|
| Packs (`n_sessions_independent`) | 22 |
| Cells (`n_variants`) | 240 |
| Flash batches / wall-sum | 24 / 464.5s |
| Parse-miss / fire_count | 0 / 75 |
| Prompt leak spotcheck | 0 hits |
| Harness cells | claude-code 181, opencode 35, cursor 12, codex 12 |
| Maps concentration | 14/22 sessions, 181/240 cells |
| Rating histogram | 0: 92, 1: 73, 2: 33, 3: 42 |

Survival, from the same meters file:

| t | n_at_risk | n_never_reached | fire rate among cells at t |
|---|-----------|-----------------|------------------------------|
| 45 | 21 | 1 | 0.25 (n=84) |
| 60 | 13 | 9 | 0.2692 (n=52) |
| 75 | 12 | 10 | 0.3947 (n=38) |
| 90 | 8 | 14 | 0.375 (n=24) |
| 105 | 8 | 14 | 0.3333 (n=24) |
| 120 | 6 | 16 | 0.4444 (n=18) |

Reading rules:

1. Quote fire rate next to `n_at_risk` and `n_never_reached`. A cell at t exists only for sessions that reached t. Late turns are a smaller, longer-lived set.
2. Rating 2 and rating 3 sum to 75, the same number as `fire_count`. On the maps that actually ran, fire is the rating threshold (`rating >= 2` for likert; binary and four-class maps in [`run_batch002.py`](../RESEARCH/2026-10-02-interception-trials/batch-002/run_batch002.py) land on the same split). The histogram and the fire count are one fact.
3. The aggregate climb from 0.25 at t=45 to 0.44 at t=120 is not a timing score. The 240-cell cap filled on the first four lever combos (`LEVER_COMBOS[:4]`). `hybrid_v0 × steer_now` is present at 45 and 60, almost gone at 75 (2 cells), and absent from 90 on. Later rows are three `stats_only` questions only.
4. Those four combos confound state, question, and response class. The other eight `LEVER_COMBOS` entries (index 4 onward in [`run_batch002.py`](../RESEARCH/2026-10-02-interception-trials/batch-002/run_batch002.py), also listed in [`grid.json`](../RESEARCH/2026-10-02-interception-trials/batch-002/grid.json)) did not execute. They are the only planned cells that use `near_done`, `defer_recheck`, `productive_arc`, `rating_plus_offset`, `stats_plus_delta`, or `compact_focus`.
5. Every `corpus_source` in `results.jsonl` is `deterministic_30`. The Flash qualitative shortlist did not enter this grid.
6. A unique-`cell_id` recount of `results.jsonl` is 236 ids across 240 lines (four identical repeats of codex `rollout-2026-04-07T04-10` at checkpoint 45). Some stored ids are sliced to 24 characters in the runner. Join future labels on the grid’s session key, drop duplicate `cell_id`s before a recount, and keep the published survival table as the canonical aggregate.

Question split on unique cells (reading aid, not a leaderboard). Same sessions, `stats_only`:

| Checkpoint | `continue_excessively` × likert | `steer_now` × binary | `thrash_bundle` × four_class |
|------------|----------------------------------|----------------------|------------------------------|
| 75 (12 sessions) | 10/12 fire | 1/12 fire | 3/12 fire |
| 90 (8 sessions) | 6/8 fire | 1/8 fire | 2/8 fire |

`continue_excessively` asks whether the job is likely to keep going. `steer_now` asks whether now is a useful time to steer without cutting productive or closing work. At the checkpoint Cody cares about, those two questions already disagree: most cells say the job may run on, and almost none say to steer now. That is evidence the levers separate the two halves of the success definition. It is not evidence that either answer is right. `window_status` is `unidentified` on all 240 lines, so none of these fires is a near-done false positive or a runaway hit.

Support at the re-check is thin: 8 sessions and 24 cells at t=90. Enough to see the question split. Too small to rank a policy even after labels, until a later wave adds sessions.

#### Resolved recommendations

Publish and quote the survival table as a diagnostic of the policy-under-test. Use the t=75 split (10/12 vs 1/12) as the reason the next wave must keep **both** questions, not as an accuracy result. Withhold every FP/miss ranking until the outcome-sheet join. Run the eight missing combos and the H3/H4 probes in the next batch rather than re-interpreting these 240 cells.

### 4. Framings — provisional primary, live runners-up, demotions

H6 stays rejected as gold ([`RESEARCH-PACK.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/RESEARCH-PACK.md) §H6, adversarial gate). Diagnostic agreement, if a later wave runs two instruments on the same cell, is recorded and then ignored for ranking.

No Wave-0 number ranks H1–H5. batch-002 exercised a slice of the H1 chain and one thrash question. It did not run a horizon rule, a boundary question, or a counterfactual. The order below is the bake-off design that the next waves **execute**, with an explicit provisional primary so the lab is not waiting on a framing debate.

| Framing | Wave-1 role | Why |
|---------|-------------|-----|
| **H1 progressive re-check** | **Provisional primary** (decision grammar) | Matches the success split already visible in the meters: predict a long continuation, and separately decide whether now is a steer. Operating rule to measure, not to ship: at t=75, defer when `steer_now` does not fire, including when `continue_excessively` does fire; look again at the next schedule point (90). Fire when `steer_now` fires. That is “hard development at ~75 → let it run → re-check ~15 later,” written as the two questions that already ran |
| **H4 deliverable boundary** | **Live runner-up. Must be measured** | Near-done protection is half of Cody’s cost. The `near_done` combo was named and did not run. A boundary probe that never executes cannot be ranked, and H1’s `steer_now` question only approximates it |
| **H3 progress velocity** | **Live runner-up. Must be measured** | The outcome sheet’s runaway-like class is thrash, low checkable progress, post-boundary overrun, and scope drift. `thrash_bundle` ran only as one confounded combo (3/12 fires at t=75). Plateau features belong in **state**, with a one-checkpoint recovery allowance so a temporary stall is a defer |
| **H2 horizon control** | **Demoted to a required null baseline. Still computed every wave** | R2 showed what happens when a horizon defines the label. Constant-turn fires (first checkpoint ≥ 75, first checkpoint ≥ 90) and never-fire are computed from the schedule with no model. They sit beside every scorecard. H2 does not supply `ideal_steer_window` |
| **H5 counterfactual waste** | **Demoted from winner contention. Component rows still emitted** | Observational replay has one future. Each wave emits the component fields (avoidable continuation, useful work at risk, closing cost, overhead) as `unidentified` when no paired branch exists. A causal net-benefit claim waits on paired branches. The row is still written |
| **H6 monitor agreement** | **Rejected as gold** | Flash vs TypeSafe vs Luna agreement is a dissociation column. It cannot confirm a window or release the product hold |
| H7–H12 | Not promoted | `termination_cause` and `human_steer_count` are already label fields (H7 as a biased reference, not gold). At-risk scoring (H11) is already the R3 rule |

Ranking gate, applied **after** labels exist, on components reported separately. The weighted sum in batch-001 (premature 1.0 / near-done 1.2 / runaway miss 1.5) stays an evaluation choice from the adversarial gate, not a finding, and is not the decision statistic.

A framing is ahead of the nulls only when, on the labeled set, both of these hold:

- fewer `near_done_fp` and `productive_interrupt` fires than always-fire at ≥75 and always-fire at ≥90, and
- fewer `runaway_miss` cells than never-fire, inside a labeled window that is neither `none` nor `ambiguous`.

A framing that wins one column and loses the other stays a runner-up. H3 and H4 each need at least half the executed cell count of the H1 question-pair on the shared sessions, or the card is stamped volume-asymmetric and cannot place them. Hold out at least four labeled sessions, including one non-Maps session, before reading hold-out fire times. Report every combo, not the best cell.

Minimum labeled support before that comparison is meaningful: at least 12 sessions that survived to t=75, at least four with `ideal_steer_window = none` or a defended near-done interval, and at least four with runaway-like `yes` whose window is a cited turn range. Below that minimum the wave still runs and still publishes diagnostics.

#### Resolved recommendations

Adopt H1’s two-question defer rule as the provisional policy-under-test. Put H4 and H3 on the same sessions in the next batch at the cell budget above. Compute H2 nulls in every meter file. Emit H5 component rows as `unidentified` until a paired branch exists. Keep H6 off the scoreboard. Do not declare a winner from batch-002.

### 5. Session selection

[`SHORTLIST.md`](../RESEARCH/2026-10-02-local-session-inventory/SHORTLIST.md) is a provisional input. The deterministic list is length-first with a soft Maps preference (9 of the top 15 are `open-pajero-maps`). The Flash qualitative list adds harness spread and is also provisional. batch-002 inherited the bias: 14/22 sessions and 181/240 cells are Maps, and the grid sampled `deterministic_30` only. Opus R4 stands. Length-only is not the corpus rule.

Next selection trial, run as its own labeled pool in parallel with Wave-1 on the current packs (the current packs stay the first measured corpus; this trial stops them from becoming the only one):

| Lens | Rule | Role in the trial |
|------|------|-------------------|
| Length | Current deterministic rank by `user_turns` / norm length | Disclosed baseline |
| Shape × thrash | Sessions with thrash, a visible closing sequence, or a human stop, including sessions that miss the length top 15 | Supplies near-done and censored rows the length list undersamples |
| Harness balance | Cap claude-code at 40% of the pool and `open-pajero-maps` at 40%. Fill from qualitative rows already named: opencode lemmings, llama.cpp, free-frontier; codex garcia-music and lemmings; cursor garcia-music | Moves the base rate off one project family |

Pool target once labels are being written: 24 sessions, at most 10 claude-code, at most 10 Maps, at least 4 opencode, 3 codex, and 3 cursor. Dedup before rank: codex rollouts that share a `session_id` are one session (called out in `SHORTLIST.md`). If a quota cannot be filled from the inventory, score inside the strata that exist and record the gap in the evidence log. Backfill is not more Maps length.

The length lens remains the corpus rule only if labeled component rates keep the same sign when Maps share drops from batch-002’s 14/22 to 40% or below. If the sign flips, the length lens is retired as the sampling rule and the balanced pool replaces it.

#### Resolved recommendations

Keep both shortlists as evidence of lenses. Run Wave-1a/1b on the existing batch-002 packs immediately, stamped Maps-concentrated. Open the three-lens pool as a parallel corpus, with the 40% caps as the sampling rule under test. Do not promote either shortlist to a committed selector.

### 6. Product landing vs trial landing

**Not unlocked**, even after a clean FP/miss card:

- Claude or Cursor hooks, OpenCode plugin install, `additionalContext`, parent-surface steering
- Pilot, Standard, Max, and live Jev inside the worker loop, the driver, or `assert_phase --live` as a new default
- Edits to `gate_thresholds.py`, `jev_signal_schemas.py`, `install.sh`, `classify.py`
- Promoting `FIXED_SCHEDULE` or “defer at 75, re-check at 90” into a user-facing cadence
- Treating batch-002 fire rates, or any later unlabeled rates, as a ship decision

**Ready now, as docs:** this proposal, the outcome-sheet protocol, the batch-002 leakage audit, and the evidence log. A future behaviour greenlight can point at those files. It still needs its own accepted wiring change. This paper does not add a `GUIDANCE-*.md` for operators and does not install a hook.

**Ready to run now, as trials:** the waves below. TypeSafe calls in those waves use pin `jev-1.13.0` on compact prefix state, logged as research batches under `docs/lab/RESEARCH/2026-10-02-interception-trials/`. They are not the assert hook and not Pilot.

#### Resolved recommendations

Leave product surfaces untouched. Spend the next lab effort on batch-003 and the label sidecar. A later greenlight reads this file; it does not get new behaviour from the merge of this file.

## Economics

The burn being targeted is the fat tail already measured: multi-hundred-turn Maps workers inside windows of tens of millions of tokens ([cheap-Jev proposal](2026-09-30-jev-cheap-judgement-signals.md)). A checkpoint schedule of six prefix snapshots is the monitoring shape that matches that tail. batch-002’s Flash wall-sum was 464.5 seconds for 240 cells, with TypeSafe unspent. That is the right order of measurement cost for a lever sweep. It is not an accuracy claim.

Per-turn frontier review of the worker loop stays out of remit (`GOALS.md`). A hard turn cap is cheaper to compute and, on this evidence, the wrong objective: batch-001’s length window would have scored a productive 400-turn session as a runaway miss if the policy deferred (adversarial gate, R2). The expensive error is asymmetric and only visible in components: cutting a job that is in closing work (stop at 75, finish near 85) versus missing a thrash tail that would have run toward 360.

Conditional TypeSafe and Flash calls at survived checkpoints, cached and prefix-only, are the spend this paper authorizes. Hook installation and live Pilot Jev are a different spend, and they stay unauthorized. Volume targets in `H1-DETAIL.md` (hundreds, then a working band of 1,000–5,000 lever variants, with variant count reported separately from independent sessions) are sweep targets for these trials. Hitting a count does not release the product hold. A thin unlabeled pilot also does not.

### Resolved recommendations

Pay for multi-approach trial volume (Flash, TypeSafe, Luna subsample) on prefix snapshots. Report `n_sessions_independent` and `n_variants` separately, as the evidence log already requires. Keep per-turn live Jev and length caps out of the budget.

## Non-goals

- Shipping hooks, Pilot, Standard, Max, or live in-loop Jev.
- Pausing Flash, TypeSafe, or Luna trial waves pending a behaviour greenlight.
- Filling `outcome-labels.jsonl` by invention, or publishing an FP/miss board from unidentified windows.
- Scoring batch-001, `archive-skew-v0`, or `archive-t45-only`.
- Using model agreement as a gold exit turn (progressive-pack gold and H6).
- Retuning the resolved cheap-Jev thresholds or turning `classify.py` into a KPI.
- Treating the provisional H1 defer rule as a runtime default.
- Collapsing H2–H5 out of the measured corpus because H1 is the provisional primary.

### Resolved recommendations

The non-goals are the product hold and the banned scoreboards. They are not a hold on the next batch.

## Measurement

Success for a **trial wave** is a clean batch: leakage audit pass, fixed schedule, at-risk denominators, every live framing present at the cell budget in §4, null baselines in the meter file, `n_sessions` and `n_variants` split, Maps share disclosed.

Success for a **ranking** is the component test in §4 on a labeled join. `classify.py` is not in that test. Steer adherence stays unmeasured and the meter header keeps the batch-002 line: assessment and decision layer only.

A wave that is clean and unlabeled is a successful wave. It publishes diagnostics and feeds the next sweep. It does not publish a winner.

### Resolved recommendations

Split “wave succeeded” from “framing is ahead.” batch-002 succeeded as a decontaminated diagnostic and failed as a ranking, because the labels and the missing combos are absent. The next wave’s exit condition is the clean multi-approach batch, not a greenlight and not an FP/miss table.

## Next spikes

Run these in order. 1a, 1b, and the label sidecar start together. 1a does not wait for labels or for 1c. New batches get new ids. batch-002 `results.jsonl` stays frozen.

| Wave | What to run | Instrument | Done when |
|------|-------------|------------|-----------|
| **1a. Finish the named grid** | The eight `LEVER_COMBOS` entries that batch-002 did not execute, on the same packs and `FIXED_SCHEDULE`, prefix-only state, same R1 field ban. New directory `batch-003/` | Flash as policy-under-test, same role as batch-002 | Leakage audit pass, leak spotcheck 0, cells for `near_done`, `defer_recheck`, `productive_arc`, `rating_plus_offset`, `stats_plus_delta`, `compact_focus` present, meters labeled diagnostic |
| **1b. Second instrument** | The four executed combos plus the 1a eight, same prefixes | TypeSafe `jev-1.13.0` Choice/Score, trial wave, GO. Luna on a pre-registered subsample of the same cells | TypeSafe rows logged beside Flash with `judge_role` set. Agreement counted only under an H6 column. No hook, no `assert_phase` default change |
| **1c. Framing probes and nulls** | H2 constant-turn and never-fire baselines (no model). H3 plateau features inside state, one-checkpoint recovery. H4 `near_done` plus a post-boundary marker in state. H5 component row, `unidentified` without a paired branch. Cell budget: H3 and H4 each ≥ half the H1 pair’s cells on shared sessions | Flash and TypeSafe for H3/H4; script for H2 nulls | Scorecard shows all five framings plus nulls, or an explicit volume-asymmetric stamp. Still no FP/miss board |
| **Labels (parallel)** | Human sidecar `batch-002/outcome-labels.jsonl`, then the same schema on batch-003 sessions, per [`OUTCOME-SHEET.md`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md) | Human reviewer. Not Flash, not TypeSafe, not Luna | Draft written before that session’s judge file is opened. `independence` attestation present |
| **1d. Selection pool** | Three-lens pool in §5, same schedule and the H1 pair plus H3 and H4 probes | Same instruments as 1b | Pool meets the quotas or the evidence log records the unfilled stratum. Rankings that use only the Maps-heavy packs stay stamped Maps-concentrated |
| **1e. First ranked card** | Join labels to fire/defer under the outcome-sheet meter definitions. Compare H1, H3, H4, and the H2 nulls on the component test | Derived meters in a new report. Historical `results.jsonl` kept | Card published only if the minimum labeled support in §4 is met. Otherwise the report stays diagnostic and 1a–1d continue |

After 1a–1c, push sparse cells (near-done checkpoints and runaway-like checkpoints, once any labels exist) toward the `H1-DETAIL.md` band of 1,000–5,000 variants. Variant count is not session count. Source-session dependence stays grouped.

### Resolved recommendations

The immediate work is batch-003 (the eight missing combos) and a TypeSafe pass on the same prefixes, with labeling in parallel and H2 nulls in the meter script. That is the measured multi-approach corpus. The product hold remains. No framing is shipped from this merge.
