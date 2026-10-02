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
