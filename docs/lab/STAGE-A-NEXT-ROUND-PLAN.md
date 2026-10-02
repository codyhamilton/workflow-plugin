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
`pairs_labelled.json`: 650 checkpoint-before-human-prompt pairs (discovery+dev only, 168 sessions: Cursor 539, Claude 111), automated prompts removed, two independent DeepSeek labellers (temp 0, different shuffles). **Agreement 83%** (540 agreed pairs): question 146, redirect 138, approve 94, correct 65, refine 47, new_task 30, other 12, abort 8.
Targets: `adjust = refine|correct` (primary), `intervened = refine|correct|redirect|abort`, `negative = correct|abort`, `approve`. Use only the 540 agreed pairs. Still to do: hand-check ~50.

## Round 6 design (small, wide)
- States: 2 fixed. Cells: the 540 labelled checkpoints (+ a matched sample of ~1 mid-run checkpoint per session as negatives).
- Signals: ~12 families × 3–4 markers (families from D: UI-iteration loop, user re-asking, done-without-verifying, scope creep, plan/design stage, autonomous run, error loop on external system, risky action, context pressure, decision-pending, task boundary, wrong-tool path, terse user, master "intervention-worthy"). Markers authored by DeepSeek under B's wording rules (ledger/direct-strength framing, no hedging, present-ness polarity), observability/duplication filtered.
- Size: ~12 × 4 × 2 states × ~700 cells ≈ 67k rows if everything is run; run the primary state first (≈34k calls, ≈$3–6). Held-out stays sealed until a final frozen panel.
- Analysis: rank AUC vs each label target, session-cluster bootstrap, discovery→dev selection check, per-signal marginal value over the master signal.

## Gate before spending
1. Hand-check ~50 labels. 2. Show this plan. 3. Author signals and review. 4. Run.
