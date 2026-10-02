---
title: Interception / steer-to-stop
status: resolved-soft
disposition: recommendations recorded; behaviour ship held; continuous large-n trial waves are the evidence path
date: 2026-10-02
updated: 2026-10-02
signal: Steer-to-stop has to catch jobs that would run long and leave near-done closing work alone; Wave-0 Flash trials exist and are not an FP/miss board.
owners: Workflow Optimiser, Cody
extends: docs/lab/PROPOSALS/2026-10-01-progressive-jev-session-gates.md
confidence: protocol-resolved; framings provisionally ordered; not score-ranked
---

# Interception / steer-to-stop

**Parent hypothesis:** [`../JEV-HYPOTHESES.md`](../JEV-HYPOTHESES.md) H2 asks whether cheap Jev advice can reduce the *total* cost of long sessions while preserving useful completion. Fire-time and near-done protection are intermediate tests. An observed fire rate or a shorter session alone does not prove the hypothesis; compact/handoff overhead, steer adherence, deliverable quality, and cost remain outcome questions.

**Current research ordering (Cody, 2026-10-02):** establish which qualitative signals predict near useful completion or prolonged continuation, trial Jev confidence for each supported signal across state and matcher variants, and then test a combined, repeatedly discounted *continuation-confidence* policy. The rating-to-fire trials and provisional H1 ranking below remain recorded contrasts, not a shortcut past signal validity.

**Soft Standard HOLD — behaviour ship only.** This paper does not ship behaviour, hooks, Pilot, Standard, Max, or live in-loop Jev. It does not pause trials and it does not treat a thin pilot as evidence. The evidence path is continuous large-n waves on real transcripts, run by TypeSafe, Flash, and Luna, analysed with session-level statistics. Behaviour is built after that evidence is in the paper and Cody accepts it.

**Status: resolved-soft.** Recommendations below are the lab’s current reading of the pack, the adversarial gate, and Wave-0. They are not an accepted runtime policy. batch-002 (240 Flash cells, 22 sessions, one driver) is a decontaminated diagnostic. It is below the scale bar.

Research pack: [`../RESEARCH/2026-10-02-interception-steer-to-stop/`](../RESEARCH/2026-10-02-interception-steer-to-stop/INDEX.md). Trials: [`../RESEARCH/2026-10-02-interception-trials/`](../RESEARCH/2026-10-02-interception-trials/INDEX.md).

**2026-10-02 pointer (does not re-rank the bake-off below):** the next theory → signal → subset loop uses float closeness, and treats this paper’s H1 rating → fire chain as contrast. [`../RESEARCH/2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/SIGNAL-CLOSENESS-CONTRAST.md). Draft families named there are unsigned and are not a GO. `status: resolved-soft` is unchanged.

This is the next layer after [`2026-10-01-progressive-jev-session-gates`](2026-10-01-progressive-jev-session-gates.md) (`status: researching`). That pack keeps the ~75 then ~15 re-check intuition and tried to tune it against multi-model gold (H5 failed, Krippendorff’s α 0.1189). This paper keeps the re-check intuition, rejects monitor agreement as gold, and scores fire-time against a non-length outcome sheet. It does not retune `A0`, `gate_thresholds.py`, or the resolved cheap-Jev use cases.

## Hold scope

| Surface | Disposition |
|---------|-------------|
| Hooks, `additionalContext`, parent-surface injection, `install.sh`, driver defaults, `assert_phase` defaults, `gate_thresholds.py`, `classify.py` | Held |
| Pilot, Standard, Max, live in-loop Jev | Held |
| TypeSafe (`jev-1.13.0`), Flash, and Luna trial waves on real prefix snapshots | **GO** — continuous, large-n, no behaviour greenlight |
| Thin pilots (hundreds of cells, one driver, a few dozen sessions) | Below the bar. batch-002 stays on disk as a diagnostic and does not close the evidence path |
| FP/miss leaderboard | Starts when [`outcome-labels.jsonl`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md) exists and is joined |
| Variant generation | Runs in parallel with labeling, at thousands of trials |

### Resolved recommendations

The hold covers behaviour ship. It does not cover trial volume. The evidence path in [Scale bar](#scale-bar) and [Next spikes](#next-spikes) starts now and keeps going until the statistical estimates are in this paper. Building the steer waits on those estimates and on Cody’s accept.

## Scale bar

Cody’s bar for this work is **thousands of trials**, not a single batch that finishes the named grid. [`H1-DETAIL.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/H1-DETAIL.md) §4b already sets the planning band at **1,000–5,000 distinct lever variants** (a sketch of 24 state scenarios × 12 queries × 8 response classes = 2,304). Executed trials are that grid crossed with checkpoints, real sessions, and three drivers. batch-002’s 240 cells are about an order of magnitude under the variant floor, on one driver, and the 240 cap is why eight planned combos never ran.

| Requirement | Rule |
|-------------|------|
| Volume | Continuous waves, starting now. Each wave adds at least **1,000 new trials per driver** (TypeSafe, Flash, and Luna). Keep going until the running total per driver is in the thousands. A few hundred cells are a wave in progress, not a finished corpus |
| Drivers | The same trial list on all three drivers. Each driver is a policy-under-test. Cross-driver disagreement is a sensitivity column. It is not a vote and not a label |
| Variants | Move four axes, first one at a time, then crossed: **longer vs shorter state**, **deterministic trimming** (counts-only, trimmed tool payloads, hybrid), **state window** (cumulative prefix, delta since the prior checkpoint, tail-only, brief-anchor plus tail), **query** (including the unrun `near_done`, `defer_recheck`, and `productive_arc` texts). The existing 12,000-character state guard is one of the length caps, not the only one |
| Sessions | **As many right-sized real transcripts as the inventory and stored JSONLs contain.** Right-sized means the session survives to the checkpoint under analysis, the prefix can be built without post-checkpoint fields, and the logical session is deduped. Cover productive-at-75, closing, thrash, and natural completion. Length-max ranking is not the sampler |
| Analysis | Statistical, on those transcripts. The independent unit is the **session**. Cells are repeated measures. See [Measurement](#measurement) |
| Order | Waves and human labels run together. Estimates land in this paper as waves complete. Behaviour build comes after the large-n estimates are written down and Cody accepts behaviour |

A few hundred coherent cells remain useful as a leakage and plumbing check. They are not the result.

### Resolved recommendations

Set the evidence path at thousands of trials per driver, on as many right-sized sessions as exist, with the four variant axes above, analysed by session-clustered contrasts. Keep batch-002 as the decontamination record. Do not ship behaviour off it, and do not stop the waves when the eight missing combos have a handful of cells.

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

Publish and quote the survival table as a diagnostic of one thin pilot. Use the t=75 split (10/12 vs 1/12) as a paired contrast the large-n waves must re-estimate with session-clustered intervals, not as an accuracy result. Withhold every FP/miss ranking until the outcome-sheet join. The eight missing combos and the H3/H4 probes enter the first standing wave at the scale bar, rather than as another few hundred cells.

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
| **H6 monitor agreement** | **Rejected as gold** | Flash vs TypeSafe vs Luna agreement is a sensitivity column. It cannot confirm a window or release the behaviour hold |
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

The balanced slice starts at 24 sessions (at most 10 claude-code, at most 10 Maps, at least 4 opencode, 3 codex, and 3 cursor) and then **keeps growing**. Twenty-four is the first check that the 40% caps are enforceable. It is not the corpus. The corpus is every right-sized real transcript the inventory and stored JSONLs can supply. Dedup before rank: codex rollouts that share a `session_id` are one session (called out in `SHORTLIST.md`). If a quota cannot be filled, score inside the strata that exist, record the gap, and keep adding sessions that do exist. Backfill is not more Maps length.

The length lens remains the corpus rule only if labeled component rates keep the same sign when Maps share drops from batch-002’s 14/22 to 40% or below. If the sign flips, the length lens is retired as the sampling rule and the balanced pool replaces it.

#### Resolved recommendations

Keep both shortlists as evidence of lenses, not as the sample. Stamp any estimate that uses only the current Maps-heavy packs as Maps-concentrated. Sample onward under the 40% caps until right-sized sessions run out. Do not promote either shortlist to a committed selector.

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

Leave behaviour unwired. Spend the lab effort on the standing large-n waves and the growing label sidecar. Fold each wave’s statistical table back into this paper. A later behaviour accept reads those tables. This merge does not build the steer.

## Economics

The burn being targeted is the fat tail already measured: multi-hundred-turn Maps workers inside windows of tens of millions of tokens ([cheap-Jev proposal](2026-09-30-jev-cheap-judgement-signals.md)). A checkpoint schedule of six prefix snapshots is the monitoring shape that matches that tail. batch-002’s Flash wall-sum was 464.5 seconds for 240 cells, with TypeSafe unspent. That is the right order of measurement cost for a lever sweep. It is not an accuracy claim.

Per-turn frontier review of the worker loop stays out of remit (`GOALS.md`). A hard turn cap is cheaper to compute and, on this evidence, the wrong objective: batch-001’s length window would have scored a productive 400-turn session as a runaway miss if the policy deferred (adversarial gate, R2). The expensive error is asymmetric and only visible in components: cutting a job that is in closing work (stop at 75, finish near 85) versus missing a thrash tail that would have run toward 360.

The spend this paper authorizes is continuous TypeSafe, Flash, and Luna calls at survived checkpoints, on prefix-only state, cached, at the scale bar (at least 1,000 new trials per driver per wave, thousands accumulated per driver). batch-002’s 464.5 seconds for 240 Flash cells is the unit cost of a thin pilot, useful for planning throughput, not a reason to stay at 240. Hook installation and live Pilot Jev are a different spend, and they stay unauthorized. Variant count and session count stay separate columns, as [`H1-DETAIL.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/H1-DETAIL.md) §4b and the evidence log already require. Reaching a thousand trials does not release the behaviour hold. Stopping at a few hundred does not finish the evidence path.

### Resolved recommendations

Pay for continuous large-n waves on all three drivers across as many right-sized sessions as exist. Report `n_sessions_independent` and `n_trials` separately, with session-clustered intervals. Keep per-turn live Jev and length caps out of the budget. Build the product steer after those estimates are in the paper and Cody accepts behaviour.

## Non-goals

- Shipping hooks, Pilot, Standard, Max, or live in-loop Jev.
- Pausing Flash, TypeSafe, or Luna trial waves pending a behaviour greenlight.
- Filling `outcome-labels.jsonl` by invention, or publishing an FP/miss board from unidentified windows.
- Scoring batch-001, `archive-skew-v0`, or `archive-t45-only`.
- Using model agreement as a gold exit turn (progressive-pack gold and H6).
- Retuning the resolved cheap-Jev thresholds or turning `classify.py` into a KPI.
- Treating the provisional H1 defer rule as a runtime default.
- Collapsing H2–H5 out of the measured corpus because H1 is the provisional primary.
- Treating batch-002, or any later few-hundred-cell batch, as enough evidence to build.

### Resolved recommendations

The non-goals are the behaviour hold and the banned scoreboards. Trial volume stays open, at the scale bar, until the statistical estimates are written back into this paper.

## Measurement

Analyse real transcript trials with statistics. Do not read a point fire rate off a few dozen sessions as a result.

| Estimator | Rule |
|-----------|------|
| Independent unit | The session. Resample **sessions** (percentile bootstrap, 1,000 draws) for every interval. A cell is a repeated measure inside its `session_id` |
| Paired lever contrast | Same session, same checkpoint, same driver, two variants that differ on one axis (state length, trim, window, or query). Report the mean paired fire difference and its session-clustered interval |
| At-risk rate | Fire rate at t uses `n_at_risk(t)`, as batch-002 already does, plus the session-clustered interval. Publish `n_never_reached` beside it |
| Strata | Repeat the paired contrast inside harness and inside Maps vs other projects. A pooled estimate that hides a sign change across strata is not used |
| Drivers | Fit the same contrasts separately for TypeSafe, Flash, and Luna. Cross-driver discordance on the same cell is a sensitivity column (H6). It does not pick the fire |
| Multiplicity | Pre-register the contrast list for the wave. Publish every contrast. The most extreme cell is a description, not the finding (adversarial gate R9) |
| Labels, when present | The same paired estimator on `near_done_fp`, `productive_interrupt`, and `runaway_miss`, against the H2 nulls, components kept separate. Until the sidecar exists, the statistical object is lever sensitivity, not accuracy |
| Stability | A contrast is stable when a later wave’s **held-out** sessions show the same sign. If the inventory of right-sized sessions is exhausted and the interval still covers zero, record the lever as unresolved and leave it out of any behaviour proposal |

`classify.py` is not in this measurement. Steer adherence stays unmeasured. The meter header stays the batch-002 line: assessment and decision layer only.

A wave succeeds when it is leakage-clean, hits the per-driver trial floor, covers the pre-registered contrasts, and adds a statistical table. A framing is ahead only under the labeled component test in §4, at large session n, on held-out sessions. Those are different exits.

### Resolved recommendations

Every standing wave publishes session-clustered paired contrasts for the four variant axes, separately per driver, with strata and the full contrast list. batch-002’s point rates stay a thin-pilot diagnostic. Behaviour build uses the stable large-n table, after Cody accepts it.

## Next spikes

batch-002 `results.jsonl` stays frozen. Every later batch gets a new id. The standing wave does not wait for labels, and labels do not wait for the wave to “finish.” There is no last thin pilot.

| Step | What runs | Floor |
|------|-----------|-------|
| **Standing wave, from batch-003 onward** | Same trial list on **TypeSafe (`jev-1.13.0`), Flash, and Luna**. Prefix-only state, R1 field ban, `FIXED_SCHEDULE`, at-risk denominators. Axes in the [scale bar](#scale-bar): state length, deterministic trim, state window, query. The eight combos batch-002 skipped are in the first wave’s query and state lists, at this floor, not as a 240-cell sequel. H2 never-fire and constant-turn nulls are computed in the meter script every wave. H3 plateau features and H4 boundary markers are state variants in the same list. H5 component rows are emitted as `unidentified` until a paired branch exists | **≥ 1,000 new trials per driver per wave.** Running total in the thousands per driver. Leakage audit before the wave is called clean. `judge_role` set per driver. No hook and no `assert_phase` default change |
| **Sessions, continuous** | Add every right-sized real transcript still unused. First balanced slice is the 24-session check in §5; sampling continues under the 40% caps | Stop adding only when the inventory of right-sized sessions is exhausted. Maps-only estimates stay stamped Maps-concentrated |
| **Statistics, every wave** | Session-clustered paired contrasts from [Measurement](#measurement), full contrast list, strata, held-out sessions once the pool can support a hold-out | A table appended to the evidence log and folded back into this paper. Point fire rates without intervals do not count as the wave’s result |
| **Labels, parallel** | Human `outcome-labels.jsonl` per [`OUTCOME-SHEET.md`](../RESEARCH/2026-10-02-interception-trials/OUTCOME-SHEET.md), growing as sessions are added | Draft written before that session’s judge file is opened. Drivers stay out of `labeler` |
| **Ranked card, when labels and n allow** | Join labels. Compare H1, H3, H4, and the H2 nulls on the component test in §4, with session-clustered intervals, on held-out sessions | Publish the card only at the labeled minimum in §4 **and** after each driver is in the thousands of trials. Otherwise the report stays a lever-sensitivity table and the standing wave continues |
| **Build** | Behaviour wiring (hooks, Pilot, live in-loop Jev, cadence defaults) | Starts after the large-n tables are in this paper and Cody accepts behaviour. Not after the first clean thousand, and not from batch-002 |

### Resolved recommendations

Run continuous large-n TypeSafe, Flash, and Luna waves on real right-sized transcripts, analyse them with session-clustered contrasts, and write the estimates back into this paper. That is the evidence path. Behaviour ship stays held until Cody accepts it. No framing is built from this merge.

## Amendment — Soft HOLD evidence fold (#105, #109, #110, #111)

Source: [`ADVERSARIAL-FOLD-soft-hold.md`](../RESEARCH/2026-10-02-interception-steer-to-stop/ADVERSARIAL-FOLD-soft-hold.md). Status stays `resolved-soft`. These are evidence-quality amendments to the scale bar and measurement rules above. They add no FP/miss claim and unlock no behaviour.

The scale bar counts trials per driver. The GROWTH refill shows why that count over-states information: 1,632 post-fill cells are 16 sessions; the preferred 12×9 cut is 9 sessions with zero runaway-like positives; ten of its twelve pairs are all-defer under TypeSafe. Cells are repeated measures of sessions (Measurement, above), and here the sessions are also one project and one harness.

| # | Amendment | Fold § |
|---|-----------|--------|
| A1 | A wave is **ranking-ready** only when the labeled pool meets the §4 minimum (≥12 sessions at t=75, ≥4 runaway-like with a cited window, ≥4 near-done or `none`, ≥4 held-out including ≥1 non-Maps). The ≥1,000 trials/driver floor still applies to diagnostics, but a cell count does not satisfy the ranking gate. | 1 |
| A2 | Adjudicate outcome labels, blind to responses, before the next refill; add a second adjudicator on the nine exact-label sessions. | 1, 6 |
| A3 | Freeze pair IDs and the contrast list before each driver runs; run all three states per preferred question as a paired control. | 2b |
| A4 | Report response occupancy (fires, sessions with any fire, all-defer flag) per pair and driver; all-defer pairs do not count toward the trial floor for that driver. | 2a |
| A5 | Near-done and runaway claims use `FIXED_SCHEDULE` only. One-checkpoint sweeps (median of reached) are state/wording sensitivity, because the selector depends on session length. | 4 |
| A6 | Stamp state-eligible-only estimates (all GROWTH) Maps-concentrated and claude-code-only; a harness-native `tail` contract for one non-Claude harness is the unblocker. | 5 |
| A7 | Quote sweep fire rates only with the state-eligibility column (claude-code 3.06% vs lite 0.87%; `delta_only` 0/608 state-eligible). | 3 |
| A8 | Treat Flash rates without a per-batch parse sidecar as missing-not-at-random. | 6 |
| A9 | Add session-level covariates to the meter (tail length, turn count, activity density); per-session fire propensity correlates across drivers (ρ=0.61, n=13, exploratory). | 2c |

### Resolved recommendations

Size and report GROWTH work in sessions with identified positives, not cells. Label first, freeze the contrast list, publish response occupancy, and stamp every GROWTH estimate Maps-concentrated and claude-code-only. Behaviour ship stays held.
