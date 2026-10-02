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
