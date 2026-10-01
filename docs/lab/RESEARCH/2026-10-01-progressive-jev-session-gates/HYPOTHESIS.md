# Hypotheses — progressive Jev session gates

**Status:** pre-registered for the first replay. **Confidence: not high.** No hypothesis below has been tested. A pass on one cell is not a licence to skip the reliability floor in H5.

Definitions: [`TERMS.md`](TERMS.md). Data plan: [`TUNING-PLAN.md`](TUNING-PLAN.md). Citations: [`LITERATURE.md`](LITERATURE.md).

All comparisons use gold rule `A0` (earliest unanimous checkout), workers with `T >= 75` and a powered panel, and the length-bin table from TERMS §8. The smoking-gun slice is `92a48e004519` and `bb6165018de0` when their JSONLs are in the manifest. Until those files exist, every hypothesis is blocked, not falsified.

## H1 — Progressive checkpoints beat the single-shot baseline

**Claim.** There exists a cell `P` in the pre-registered grid with `on_uncertain = open` and `gold_rule = A0` such that, relative to baseline `B` (one legacy Jev call at the first closed `jev_eligible` turn):

- median `overshoot` on workers where both exits exist is strictly smaller for `P` than for `B`, and
- `false_early_rate(P) <= false_early_rate(B) + 0.05`, and
- `false_late_rate(P) <= false_late_rate(B)`.

**Primary cell to report even if it loses:** `P0` = `(75, 15, hybrid_v0 N=8 excerpt=400, Y_full, confidence_min=3, open, A0)`.

**Also report** turn-cap baseline `C` (`gate_exit = first_at`). If the best Jev cell does not beat `C` on the same three inequalities, the questions are not earning the call.

**Falsify H1** when no grid cell meets the three inequalities, or when the cell that meets them does so only inside a single length bin while another bin’s `false_early_rate` exceeds `B` by more than 0.05. The second clause is the repeated-testing check: fifteen looks at a 296-turn file are not the same policy as one look at an 80-turn file.

**What would not falsify H1.** A loss on `A1` or `A2`. Those are robustness columns. A win only on hindsight gold. A win on the two smoking guns with a loss on the rest of the corpus.

## H2 — Hybrid snapshot beats stats-only and tail-only on the smoking guns

**Claim.** Holding schedule `(75, 15)`, question set `Y_full`, `confidence_min = 3`, and `on_uncertain = open` fixed, `hybrid_v0` with `N = 8` and excerpt 400 has a smaller mean absolute overshoot on the smoking-gun slice than:

- `stats_only`, and
- `last_n_turns` with `N = 8` and excerpt 400.

If a gun has a null on one side so overshoot is undefined, count a false early or false late as a miss worth one interval (15 turns) for this comparison only, and say so in the table.

**Falsify H2** when either simpler mode is within one interval of hybrid on both guns, or when either simpler mode is strictly better on both guns.

**Mechanism this is about.** Liu et al. found a U-shaped use of long context: the start and the end are used, the middle is not. Hybrid puts the brief anchor at the start and the tail at the end, and keeps cumulative thrash as fields. If stats-only wins, the prose tail is not carrying the decision and the default should change. If tail-only wins, the cumulative block is not carrying it.

**Related measurement, not a separate pass/fail.** Median `shrink_steps` on hybrid for `92a48e004519`. If the median reaches the step that deletes the tail, H2 is not interpretable for that worker: the harness did not send a hybrid state.

## H3 — The v0 question set matches gold at least as well as the resolved pair

**Claim.** Under `P0`’s snapshot and schedule, `Y_full` has median absolute overshoot less than or equal to `Y_legacy`, and `false_early_rate(Y_full) <= false_early_rate(Y_legacy) + 0.05`.

**Falsify H3** when `Y_legacy` has a smaller median absolute overshoot and a false-early rate no worse than `Y_full` by more than 0.05.

**Diagnostic the table must include.** The share of `Y_full` firings flagged `ungrounded_choice`, as defined in TERMS §3: checkout while runaway and drift are in `{0, 1}` and progress is in `{2, 3}`. A high ungrounded share means the choice is not using the rubric axes. That does not by itself falsify H3. It blocks describing `Y_full` as a rubric-shaped test.

`Y_choice_only` is reported, not hypothesised. If it ties `Y_full`, the three pattern scores are for analysis, not for the decision, and a later pack can drop them. This pack does not drop them in advance.

## H4 — Requiring confidence 3 reduces early stops without a large late penalty

**Claim.** Under `P0` with only `confidence_min` changed, `t = 3` has a lower `false_early_rate` than `t = 2`, and the median overshoot (both exits non-null) at `t = 3` is at most 15 turns higher than at `t = 2`.

**Falsify H4** when the two rates and the two medians are equal, or when `t = 3` raises median overshoot by more than one interval, or when `t = 3` has the higher false-early rate.

H4 is about the threshold inside one question set. It is not the claim that the design is high-confidence.

## H5 — The panel is reliable enough to tune against

**Claim.** Krippendorff’s alpha on pooled prefix-level binary labels is **≥ 0.40**.

**Falsify H5** when alpha is below 0.40. Consequence, pre-registered: do not interpret H1–H4 or H6–H7 as evidence for a parameter change. Revise [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) or the judge bundle and re-label. Tuning Jev to a panel that does not agree is fitting noise.

0.40 is the bottom of Landis and Koch’s “moderate” band. It is a floor. An alpha of 0.41 does not make the gold strong. Report the alpha, the pairwise kappas, and the per-worker spread beside it.

**This alpha is model–model.** It does not satisfy the human half of an eval-of-evals. Zheng et al. is the public comparison point for LLM–human agreement, on a different task. R-Judge is the public comparison point for trajectory judgement, and most models there did not beat a weak baseline. Expect the alpha to be modest. Write the number next to those papers in the lock memo rather than assuming we will match GPT-4’s MT-Bench agreement.

## H6 — The smoking gun is not allowed to run to 296 under P0

**Claim.** On `92a48e004519`, `P0` yields `max_allowed_turns < 296`.

**Falsify H6** when `gate_exit` is null for that file under `P0`.

H6 is a sanity check that the proposed cell can fire on the worst published worker. A pass of H6 with a fail of H1 means the cell stops the famous file and still loses to the single-shot rule on the corpus. Do not promote H6 alone.

No analogous claim is pre-registered for `bb6165018de0`. That file may be a long success. Forcing a checkout there would bake in the conclusion.

## H7 — On gold-positive workers the checkout evidence does not get weaker as the prefix grows

**Claim.** Among workers with `gold_exit` non-null under `A0`, and under `P0`’s snapshot and `Y_full`, the mean of `runaway_pattern` on checkpoints at or after `gold_exit` is greater than or equal to the mean on checkpoints before `gold_exit`.

**Falsify H7** when the later mean is lower by more than 0.25 (a quarter of one score point).

H7 is the “increasingly hard” claim that can be tested without raising the bar. The schedule already adds more chances to fail (H1’s length bins). H7 asks whether the cumulative snapshot actually looks worse after the gold exit. If it does not, a fixed question on a growing transcript is not getting harder; it is only being repeated. That result would push the open axis “rising bar” from a footnote into the next grid. It would not authorise turning the bar up inside this study.

Checkpoints after `gate_exit` are still scored for H7. The counterfactual stop does not delete later prefixes from the cache. Otherwise H7 could only be computed on workers the gate failed to stop.

## What is deliberately not hypothesised

- That `first_at = 75` equals a published optimum. The field note says otherwise.
- That fail-closed beats fail-open. Fail-closed is reported so its false-early cost is visible. Cody’s policy under test is fail-open.
- That any cell should be wired into Claude, the driver, or `additionalContext`.
- That a dry-run of the schema validates H1–H4 or H6–H7. A dry-run can only reject a snapshot that overflows 12_000 characters.
- That agreement among Grok, Claude, and Composer is agreement with Cody. A human review of the smoking-gun gold is a separate, optional column.

## Reporting order

When the replay exists, publish in this order, and stop at the first failure of the stop rules:

1. Corpus manifest counts (blocked today).
2. Alpha and spread (H5). Stop if H5 fails.
3. Baseline `B` and baseline `C` against `A0`.
4. `P0` against `B` and `C`, with length bins (H1, H6).
5. Snapshot ablation (H2) and question ablation (H3, H4).
6. H7.
7. Robustness columns for `A1` and `A2`, without changing the selected cell.
8. Only then a lock memo. The proposal stays `researching` until that memo, and the memo is what could later support a confidence claim. This file is not that memo.
