# Stage A: next-round plan (draft, 2026-10-03)

Status: analysis A–D done, outcome labels built, **no new Jev calls made yet**. Data: `~/jev-lab-data/2026-10-03-stageA/`.

## What the 225k-row ledger taught us
| Axis | Finding | Consequence |
|---|---|---|
| State | Size doesn't buy signal; content family does. Turn-unit windows are worse than batch windows; first-prompt-only or no prompts beats all prompts; outputs ≥750 chars don't help. | Fix 2 states: `st-56e84daf55` (primary), `st-64837f4917` (no-prompt contrast); `st-6855387dcc` only for names-only signals. State is no longer a varied axis. |
| Markers | Hedging wording −0.15 AUC; "absent" polarity −0.15; falsify framing −0.08; ledger/accounting framing +0.065; direct strength wording +0.05. Length, quote-first, question-form are noise. Adding markers beyond ~3 barely helps. | 3–4 markers per signal, mean-scored; spend the budget on more signals, not more wordings. Handle `score: null` rows (choice/noul markers). |
| Repeats | Jev is near-deterministic (SD ~0.002). | One call per cell. |
| Sessions | The limit. Claude ≈22 usable sessions (≥8 turns), Cursor ≈271. 90% CI half-width 0.10 needs ~20–30 sessions; 0.05 needs ~80–110. | Cursor-heavy discovery; Claude is a replication set. Hooklog now captures Claude/Cursor/opencode for more data. |
| Labels | Fixed checkpoints 25/55/100 put ~half past the last human prompt; `prompt_soon` conflates "agent autonomy" and "session ended". | Checkpoints go *just before each human prompt*; label = what the human did next. |

## New outcome set (built)
`pairs_labelled.json`: 629 checkpoint-before-human-prompt pairs (discovery+dev only; the live authoring session is excluded), automated prompts removed, two independent DeepSeek labellers (temp 0, different shuffles). **Agreement 83%** ; after dropping pasted/automated prompts that slipped through the regex, **501 clean agreed pairs from 157 sessions**: question 144, redirect 117, approve 94, correct 63, refine 45, new_task 28, abort 8, other 2 (`adjust` positives: 108).
Targets: `adjust = refine|correct` (primary), `intervened = refine|correct|redirect|abort`, `negative = correct|abort`, `approve`. Use only the clean agreed pairs (`labels_clean.json`). Still to do: hand-check ~50.

## Round 6 design (small, wide)
- States: 2 fixed. Cells: the 501 labelled checkpoints (+ a matched sample of ~1 mid-run checkpoint per session as negatives).
- Signals: ~12 families × 3–4 markers (families from D: UI-iteration loop, user re-asking, done-without-verifying, scope creep, plan/design stage, autonomous run, error loop on external system, risky action, context pressure, decision-pending, task boundary, wrong-tool path, terse user, master "intervention-worthy"). Markers authored by DeepSeek under B's wording rules (ledger/direct-strength framing, no hedging, present-ness polarity), observability/duplication filtered.
- Size: ~12 × 4 × 2 states × ~700 cells ≈ 67k rows if everything is run; run the primary state first (≈34k calls, ≈$3–6). Held-out stays sealed until a final frozen panel.
- Analysis: rank AUC vs each label target, session-cluster bootstrap, discovery→dev selection check, per-signal marginal value over the master signal.

## Gate before spending
1. Hand-check ~50 labels. 2. Show this plan. 3. Author signals and review. 4. Run.

## Round 6 results (labelled checkpoints, 501 pairs, ~$1.20)

Setup: 16 signals x 4 framings x 3 states, one call per cell, human prompt at the checkpoint hidden
(`hide_next_prompt`). Target `adjust` = the human's next message refines or corrects. AUC of the mean marker
score per (state, signal); 90% session-cluster bootstrap lower bound in brackets.

| signal | AUC adjust (lower bound), per state |
|---|---|
| ui-visual-iteration-loop | 0.70 (0.64), 0.68 (0.61), 0.68 (0.62) |
| human-would-intervene-now | 0.65 (0.59), 0.66 (0.59) |
| claims-done-without-verifying | 0.65 (0.60), 0.64 (0.58), 0.65 (0.59) |
| scope-creep-beyond-request | 0.62 (0.55), 0.62 (0.56) |
| commit-boundary-reached | 0.60 (0.55), 0.62 (0.56), 0.59 (0.53) |
| serial-single-read-grind | 0.57-0.58 (0.51) |
| all others | at or near chance (terse-impatient-human 0.48-0.51; external-dependency-error-loop 0.48-0.53) |

Findings:
- Five signals clear chance with the lower bound above 0.5 in every state tested. Results agree across the three
  states, so state choice stays low-impact (one last-3-prompts state is enough).
- Baselines: checkpoint turn alone gives AUC 0.599 and state size gives 0.598. The mean of the five best signals
  (rank-averaged) gives 0.669, so the lift is about +0.07, not +0.17. Inside turn terciles the combination scores
  0.62, 0.67 and 0.58, so the lift is partly real and partly mixed with session length.
- Replication: cursor discovery 0.66, cursor dev 0.71 (n=140, 38 positives). Claude sessions are too few
  (42 pairs, 6 positives) to say anything.
- Framing: mean AUC across signals is 0.575-0.595 for the four panels, so wording matters less than which
  signal is asked.
- Weak: terse-impatient-human and the error-loop signals carry nothing here; drop them from the next round.

Next-round plan:
1. Keep the five signals, plus serial-single-read-grind for one more look.
2. Add more claude-harness labelled checkpoints (hooklog capture is accumulating) so the Claude side can be tested.
3. Test each signal's marginal value over human-would-intervene-now (the direct "would the human step in" question).
4. Fit nothing yet: held-out stays sealed until the signal list is frozen.

### Claude-harness check (no new spend)

More Claude checkpoints are not available from local data: only 24 Claude sessions pass the corpus filters (229
local transcripts, most are automated lab runs), and 61 clean labels with 9 `adjust` positives remain after
filtering. Relaxing labeller agreement adds 22 pairs and no positives. No new Jev calls were made; this re-cuts the
R6 ledger by harness (`analysis/R6_claude.py`).

| signal | Claude AUC (n=61, 9 pos), 90% CI | Cursor AUC (n=440, 99 pos), 90% CI |
|---|---|---|
| ui-visual-iteration-loop | 0.64 (0.43-0.85) | 0.70 (0.64-0.76) |
| human-would-intervene-now | 0.61 (0.44-0.72) | 0.67 (0.60-0.72) |
| claims-done-without-verifying | 0.62 (0.40-0.75) | 0.67 (0.62-0.73) |
| scope-creep-beyond-request | 0.55 (0.34-0.77) | 0.65 (0.59-0.70) |
| commit-boundary-reached | 0.48 (0.35-0.59) | 0.64 (0.59-0.70) |
| serial-single-read-grind | 0.44 (0.31-0.59) | 0.60 (0.55-0.66) |

Reading: Claude point estimates are in the same direction for the top three signals, but every interval includes
0.5, so Stage A makes no Claude-specific claim. Cursor results hold with tighter intervals. Cursor
transcripts carry no tool outputs, so the signals that work are ones readable from prompts, tool names and
arguments. Claude evidence needs new labelled Claude sessions (a data-collection problem, not a Jev one).
`commit-boundary-reached` and `serial-single-read-grind` are weakest and are the first to drop if the list shrinks.

### Value over `human-would-intervene-now` (Cursor, n=440, 99 `adjust`, no new spend)

Rank-sum of each signal with the direct "would the human step in" signal, against that signal alone
(`analysis/R6_incr.py`; mean over states and framings; session-cluster bootstrap 90% CI on the AUC difference).

| signal | alone | + intervene | delta 90% CI | corr with intervene |
|---|---|---|---|---|
| (baseline) human-would-intervene-now | 0.673 | | | |
| ui-visual-iteration-loop | 0.704 | 0.705 | [+0.013, +0.052] | 0.75 |
| claims-done-without-verifying | 0.670 | 0.682 | [-0.007, +0.025] | 0.82 |
| scope-creep-beyond-request | 0.648 | 0.670 | [-0.021, +0.013] | 0.81 |
| commit-boundary-reached | 0.642 | 0.682 | [-0.013, +0.032] | 0.66 |
| serial-single-read-grind | 0.602 | 0.660 | [-0.044, +0.020] | 0.60 |
| all six | | 0.692 | [-0.003, +0.046] | |

Reading:
- The direct intervene signal is already as good as any specific signal (0.67) and the specific ones are highly
  correlated with it (0.6-0.8), so most of their predictive content is shared.
- Only `ui-visual-iteration-loop` adds reliably (delta interval above zero), and it beats the master signal alone.
  It is also the least redundant with the others, so it is the best candidate for new variants and is the one to refine.
- Combining all six adds about +0.02 over the master signal alone, interval spanning zero. More signals of this
  kind will not buy much; the next gains need signals that are decorrelated from "the human would intervene".
- Implication for the next round: spend variants on (a) the master signal's wording/anchors and (b) new
  signals near `ui-visual-iteration-loop`: concrete, observable loops (repeated edits to the same file, repeated
  failing command, re-asks) rather than judgement-flavoured ones.

## Round 7 draft (registered, NOT run)

Registered (author claude-r7 / flash-r7-mk; ~4,000 cells, est. $0.80, 157 sessions, held-out sealed):
- 7 observable-loop signals, each with a zero-call detector: same-file-edit-churn, repeated-identical-command,
  corrective-language-in-recent-prompts, edit-then-revert-oscillation, long-unattended-tool-streak,
  wide-file-fanout, repeated-browser-check-without-progress.
- 4 new framings of human-would-intervene-now (peer, next-message, cost-of-continuing, evidence-list), 16 new
  markers in all x 4 panels, plus `ui-visual-iteration-loop` as the control in every panel.
- A wider state (14 batches, no outputs, last 3 prompts) because the count-based signals need more than 5 batches.
- Success test (in `r7-card.md`): a new signal whose delta AUC over the master signal has a 90% cluster CI above
  zero, replicated discovery -> dev. Master framings are judged against the R6 master AUC of 0.67.
Gate before running: Cody sees the card (cost is small, so the run can go ahead on the same terms as R6 if he
has not objected). Round file and specs live in the scratchpad `r7*`; archived under `~/jev-lab-data`.

## Round 7 results (run: 4,008 calls, 0 errors, $0.80; 501 labelled checkpoints incl. 61 Claude)

Markers were spot-checked first (32 of 32: four levels, higher-means-present, no hedging words). Scores are the
mean over framings and states; target `adjust`; 90% session-cluster CIs (`analysis/R7_an.py`, `R7_ctl.py`).

| signal | alone AUC (90% CI) | disc / dev | delta over (R6 master + turn) (90% CI) |
|---|---|---|---|
| ui-visual-iteration-loop (control) | 0.69 (0.63-0.75) | 0.71 / 0.65 | +0.016 to +0.049 |
| same-file-edit-churn | 0.67 (0.60-0.73) | 0.67 / 0.64 | -0.002 to +0.034 |
| repeated-browser-check-without-progress | 0.67 (0.60-0.72) | 0.67 / 0.64 | +0.006 to +0.047 |
| wide-file-fanout | 0.66 (0.60-0.71) | 0.63 / 0.70 | 0.000 to +0.030 |
| long-unattended-tool-streak | 0.66 (0.60-0.71) | 0.65 / 0.66 | +0.006 to +0.048 |
| edit-then-revert-oscillation | 0.62 (0.56-0.68) | 0.61 / 0.62 | -0.018 to +0.012 |
| repeated-identical-command | 0.57 (0.50-0.63) | 0.52 / 0.64 | -0.036 to +0.008 |
| corrective-language-in-recent-prompts | 0.54 (0.49-0.59) | 0.52 / 0.60 | -0.037 to +0.007 |

Findings:
- Observable-loop signals match or beat the judgement-flavoured master signal alone (R6 master 0.66 on all 501;
  checkpoint turn 0.60). Four of them (churn, browser-check, fanout, streak) are at 0.66-0.67 and replicate
  discovery -> dev. They are far less correlated with each other and with the master (0.35-0.6) than the R6
  signals were (0.6-0.8).
- Mean of the five best observable signals: AUC 0.709 alone, and 0.708 on top of R6 master + turn (delta CI
  +0.024 to +0.086, above zero). This is the first result that beats the master baseline with an interval above
  zero, and it is a +0.05-0.06 lift over the best single prior signal; still modest.
- The four new master framings did worse (0.61; per framing 0.56-0.64) than the R6 master (0.66), and adding them
  to R6 lowers it. Reframing the master signal is not a productive direction; stop spending variants on it.
- Weak/drop: corrective-language-in-recent-prompts (0.54) and repeated-identical-command (0.57); with Cursor
  transcripts lacking outputs, identical-command repeats cannot show failure, which probably explains it.
- Caveat: signals correlate 0.34-0.56 with turn index (longer sessions score higher on counts), so some lift is
  session-length structure; the delta-over-turn rows above control for it. Held-out has not been touched.

Next: (1) variants of the four replicating observable signals (thresholds, window sizes, framing) and 2-3
more concrete loop signals; (2) do not add more judgement signals; (3) a combined score over the best 4-5 is the
candidate for the held-out test, to be frozen only after a dev-replicated round and Cody's agreement on the freeze.

## Round 8 results and the zero-call control (6,012 calls, 0 errors, $1.20)

Setup: 11 new signals (threshold variants of the four replicating R7 signals; four new concrete signals) x 4
framings x 3 windows (8, 14, 24 batches), with the R7 originals and ui-visual as controls
(`analysis/R8_an.py`; target `adjust`, 501 labels).

- Thresholds and windows barely matter. Variants of the same signal land within ~0.02 AUC of each other (churn 2+/5+
  0.675/0.671 vs 0.669; fanout 3+/8+ 0.664/0.652 vs 0.652; streak 6+/20+ 0.654/0.677 vs 0.657). Best single
  signals sit at 0.66-0.69 and none is distinguishable from its neighbours. Window 8 is as good as 24 (state tokens
  scale with the window, so the 8-batch state is the cheapest and loses nothing; ui-visual and fanout are slightly
  better at 8). Framing means are all 0.63-0.64.
- New concrete signals are weak: shell-heavy-window 0.54, new-file-creation-burst 0.56 (both hurt the baseline),
  destructive-shell-commands 0.60, edit-without-prior-read 0.63 (no value over baseline).

Zero-call control (`analysis/R8_zero.py`): the same four counts computed by plain code from the transcripts, no model.

| feature | zero-call AUC | Jev (matching signal) | corr Jev vs counter |
|---|---|---|---|
| max edits to one file (14 batches) | 0.647 | 0.675 | 0.77 |
| distinct files edited | 0.634 | 0.664 | 0.74 |
| batches since last human prompt | 0.669 | 0.677 | 0.89 |
| browser/screenshot calls | 0.544 | 0.663 | 0.43 |
| sum of the four | 0.683 | 0.706 | |

- A free counter reproduces most of the "observable-loop" lift. Jev's score tracks the counters (corr 0.74-0.89);
  adding the four Jev signals to the four counters lifts AUC 0.683 -> 0.702 (delta CI +0.007 to +0.032), while
  adding the counters to Jev does nothing (-0.016 to +0.007).
- Where Jev gains is where a detector is hard to write: the browser/UI-loop signal (0.66 vs 0.54 for a name regex),
  and ui-visual-iteration-loop (0.69). Where a count is enough, code is as good and costs nothing.
- Revised reading for the white paper: Jev adds a small but real increment over cheap counters, concentrated in
  signals that need a judgement over tool names/arguments; its main use is as a way to find and express such signals
  and as a candidate scorer when no regex exists, not as a better counter. All AUCs stay modest (0.65-0.71).

Next: (1) stop sweeping thresholds/windows (flat); (2) hunt judgement-needing signals where counters fail
(ui/visual loops, "same goal retried by different means", "agent re-doing what it did earlier") and measure their
increment over the zero-call baseline, not over the master signal; (3) add the zero-call counter baseline to every
analysis from now on. Held-out remains sealed; no freeze.

## Round 9 results: judgement-needing signals against the zero-call baseline

Eight new signals (same goal by different means, redoing earlier work, work diverges from request, workaround instead of root fix, exploring without converging, fixing its own earlier edit, still working after request met, agent should have asked), 4 framings each, state st-6cde963701 (8-batch window), 501 labelled checkpoints (108 adjust), 2004 calls, $0.40, no errors. Reference: zero-call counters (churn, fanout, streak, browser) 0.683, plus turn 0.691.

- Alone: agent-should-have-asked 0.673, fixing-its-own-earlier-edit 0.660, redoing-earlier-work 0.627, still-working-after-request-met 0.632, workaround 0.631, same-goal-different-means 0.612; exploring-without-converging 0.476 and work-diverges-from-request 0.515 are at chance. ui-visual (control) 0.690.
- Over counters+turn: no signal adds reliably. Deltas range -0.018 to +0.009; every CI includes 0 (work-diverges is reliably negative). Mean of the six that score >=0.6: 0.664 alone, +0.001 over counters+turn (CI -0.010..+0.011). The R6 master signal over counters+turn: 0.693, i.e. +0.002.
- The new signals correlate 0.58-0.69 with the counters and 0.68-0.78 with the master signal; the two with low correlation are the two at chance.

Reading: the hypothesis that judgement signals recover what counters miss is not supported on this label set. R8's small Jev increment (+0.007 to +0.032) over counters does not grow with more judgement-style signals; the jev scores largely re-express activity volume. The white paper should report Jev at about parity with cheap counters (0.65-0.71) on this outcome, with the label noise ceiling as a likely limit. Held-out stays sealed; nothing pushed. Next candidates: a different outcome target (e.g. abort/redirect) where counters may fail, or hand-checking labels.

## Round 9b: other outcome targets (no new Jev calls)

Same R9 scores (13 markers x 4 panels, 8-batch window) and counters, re-scored against other next-message labels (analysis `R9_tgt.py`). Labels: question 144, redirect 117, approve 94, correct 63, refine 45, new_task 28, abort 8 (too few to measure; abort+redirect = 125 is the nearest proxy). AUC < 0.5 means the signal is anti-predictive (higher activity, lower chance of the outcome).

| target | pos | turn | counters4 | counters+turn | master | mean of all Jev signals | Jev over counters+turn (CI) |
|---|---|---|---|---|---|---|---|
| adjust (refine/correct) | 108 | .599 | .683 | .691 | .663 | .679 | +.002 (-.006..+.007) |
| correct | 63 | .601 | .673 | .687 | .648 | .661 | -.003 (-.014..+.006) |
| refine | 45 | .570 | .645 | .644 | .639 | .652 | +.007 (+.001..+.013) |
| redirect | 117 | .440 | .387 | .379 | .379 | .385 | .000 |
| abort+redirect | 125 | .457 | .391 | .388 | .398 | .393 | .000 |
| any intervention | 233 | .535 | .542 | .546 | .534 | .541 | .000 |
| question | 144 | .380 | .430 | .391 | .453 | .426 | +.010 (+.003..+.020) |
| approve | 94 | .609 | .618 | .641 | .591 | .636 | -.002 |
| new_task | 28 | .485 | .258 | .322 | .280 | .229 | -.039 (-.062..-.020) |

Findings:
- Counters do not do worse on redirect/abort; they do the same as Jev (both about 0.38-0.39, i.e. 0.61-0.62 inverted). Redirect and new_task follow quiet, finished-looking checkpoints, not busy ones. new_task is the clearest: activity counters reach 0.74 inverted, Jev 0.77 inverted (mean of all signals 0.229).
- Any-intervention is near chance (0.53-0.55) for every predictor, because adjust and redirect pull opposite ways. A pooled "human intervenes" target hides the signal; adjust must stay the primary target.
- Jev adds a significant but tiny increment on refine (+0.007) and question (+0.010). Nothing near the +0.03-0.09 seen in R6-R7 against the weaker master baseline.
- Aborts (8) cannot be measured on this corpus.

Reading for the paper: the signals track "how much is the agent doing without a human in the loop", which predicts correction and refinement positively and redirect and new-task negatively. Cheap counters capture this equally well. A claim that Jev reads something counters cannot is not supported by any target tested.

## Label hand-check (40 labels) and noise sensitivity

I read 40 labelled checkpoints (20 adjust positives and 20 non-adjust, random, seed 7; `analysis/hand_sample.json`), judging each human message against the agent context. One reader, and the same model family as the two LLM labelers, so this is not an independent audit. (`labels_clean.json` holds only pairs where both labelers agreed, so the 100% agreement there is by construction, not a quality measure.)

- Positives: 20/20 reasonable (refine/correct). One (#9) mixes both.
- Non-adjust: 6/20 arguably adjust. Redirect after a plan or while the agent worked ("seems odd to use opacity... what about a line light source?"; feedback on a plan's design; "add into the plan...") and new_task for a bug report on the agent's just-finished feature. The rest (question, approve, genuine redirect/new_task) fine. With n=20 the true rate is wide (roughly 12-54%).
- So label error is one-sided: the positive class is clean, the negative class contains hidden adjusts, which only lowers measured AUC.

Sensitivity of AUCs to the label set (`R9_noise.py`; counters4 / counters+turn / master / Jev mean / ui-visual):

| label set | n (pos) | counters4 | counters+turn | master | Jev mean | ui-visual |
|---|---|---|---|---|---|---|
| baseline | 501 (108) | .683 | .691 | .663 | .679 | .690 |
| drop plan-context checkpoints | 464 (102) | .681 | .689 | .670 | .685 | .696 |
| plan-context redirects counted as adjust | 501 (125) | .659 | .657 | .633 | .649 | .658 |
| drop all redirect | 384 (108) | .665 | .672 | .642 | .658 | .668 |
| drop no-tool checkpoints | 392 (95) | .687 | .689 | .650 | .666 | .688 |
| tool-work checkpoints only | 355 (89) | .683 | .683 | .653 | .670 | .694 |

- Ranking and gaps between predictors do not move under any of these cuts; counters stay at or above Jev, ui-visual stays top among Jev signals. The result is not an artefact of one label subset.
- Making the plan-context redirect relabel (the cut that moves hidden adjusts to positive by my rule) lowers every AUC by 0.02-0.03; my rule is crude, so this is not evidence of a better label.
- Ceiling: a predictor that perfectly separates the current positives would score 0.87 / 0.79 / 0.74 if 10% / 20% / 30% of negatives were really adjust. My 6/20 estimate sits in the 20-30% range, which puts the achievable ceiling near 0.74-0.79. The observed 0.65-0.70 is therefore not far below it, and label noise alone could explain why nothing exceeds about 0.71.

Conclusion for Stage A: the label noise caps AUC but does not change any predictor comparison. Remaining improvement would need cleaner labels (an independent human pass on negatives, especially redirect and new_task) before any further signal work is measurable. Held-out stays sealed; nothing pushed.
