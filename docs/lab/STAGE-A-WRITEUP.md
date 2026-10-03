# Stage A write-up: what Jev signals measure, and how well (paper draft, 2026-10-03)

Status: draft for the white paper. Data archive: `~/jev-lab-data/2026-10-03-stageA/` (ledger, registry, analysis scripts). Round-by-round detail and numbers: `STAGE-A-NEXT-ROUND-PLAN.md`. Held-out sessions are sealed and have not been scored. Nothing here has been pushed or published.

## 1. Question

Can a cheap model read a compact snapshot of an agent session (recent tool calls, optionally the human's prompts) and score named *signals* ("the human would intervene now", "agent is editing the same file repeatedly") well enough to be useful as a live indicator? Stage A answers this offline, on past sessions, and tests whether the scores carry anything a free code counter does not.

## 2. Method

- **Scorer.** Jev (a DeepSeek-Flash-class model) answers a score question per marker on a state snapshot. Near deterministic (run-to-run SD about 0.002), so one call per cell; about $0.0002 per call.
- **Registry.** Every axis is a content-hashed variant: signals (`sig-`), states (`st-`), marker wordings (`mk-`), panels (`pn-`). Variants are authored by DeepSeek agents or by me, each with rationale and provenance. Every call is a ledger row (cell = panel x state x session x checkpoint; one row per marker). About 1.4M ledger rows in total by round 9.
- **Corpus.** 157 labelled sessions (Cursor-heavy; Claude Code 61 labelled checkpoints, 9 adjust positives). Sessions are split by id hash: 60% discovery, 20% dev, 20% held-out. Only discovery and dev have been used. The live authoring session is excluded. A secret scrub runs before anything is sent to Jev.
- **Outcome.** Each checkpoint sits just before a human prompt; the label is what the human did next (two independent DeepSeek labelers at temperature 0, 83% raw agreement; the 501 pairs where both agreed are used). Classes: question 144, redirect 117, approve 94, correct 63, refine 45, new_task 28, abort 8, other 2. Primary target `adjust` = refine or correct (108 positives, 99 on Cursor).
- **Leak guard.** The human prompt that arrives at the checkpoint is removed from the state, so the outcome cannot be read from the input.
- **Statistics.** Rank AUC, 90% session-cluster bootstrap intervals, discovery-to-dev replication, incremental AUC over baselines. Baselines: the checkpoint turn index; the R6 master signal ("human would intervene now"); and, from round 8, **zero-call counters** computed by plain code from the same transcripts (max edits to one file, distinct files edited, batches since the last human prompt, browser calls).

## 3. Results

1. **Wording and state matter little; the signal family matters.** From 225k early rows: hedging words cost 0.15 AUC, "absent" polarity 0.15, ledger/direct-strength framing helps 0.05-0.07; state size buys nothing; an 8-batch window is as good as 24; thresholds are flat (variants land within 0.02 AUC).
2. **Judgement signals are modestly predictive.** The R6 master "human would intervene now" scores 0.66 on adjust (turn index alone 0.60). Five of sixteen R6 signals reach 0.60-0.70; combined 0.67.
3. **Observable-loop signals match or beat the master.** Same-file edit churn, wide file fanout, long unattended tool streak, repeated browser checks: 0.66-0.67 each, replicating discovery to dev; mean of the best five 0.709 (+0.02 to +0.09 over master plus turn).
4. **A free counter does as well.** Zero-call versions of the same four counts score 0.683 summed (0.691 with turn) against Jev's 0.706. Jev tracks the counters at 0.74-0.89 correlation. Adding Jev to counters adds +0.007 to +0.032; adding counters to Jev adds nothing. Jev leads only where no simple detector exists: browser/UI loops (0.66 against 0.54 for a name regex) and `ui-visual-iteration-loop` (0.69).
5. **More judgement does not rescue it (round 9).** Eight new signals that need judgement (same goal by different means, redoing work, workaround instead of fix, should-have-asked, and others) score 0.48-0.67 alone and add 0.001 (CI -0.010 to +0.011) over counters plus turn; the master adds 0.002.
6. **Other outcomes show the same thing.** On redirect, new_task and abort+redirect, both counters and Jev are anti-predictive (about 0.38-0.39, i.e. 0.61-0.62 inverted; new_task 0.74-0.77 inverted): the human redirects after quiet, finished-looking checkpoints. Pooling all interventions hides the signal (0.53-0.55) because adjust and redirect pull in opposite directions. Jev adds a significant but tiny increment on refine (+0.007) and question (+0.010).
7. **Claude Code: no claim.** 61 labelled checkpoints and 9 positives cannot support one; more would need hook capture, which is out of scope for Stage A.

**What this proves.** The signals measure how long and how broadly the agent has worked without a human in the loop. That predicts correction and refinement and predicts against redirect and new_task. Jev reproduces it at about 0.65-0.71 AUC, equal to cheap counters within noise. It does not show that Jev reads something code cannot; the only support for that is the UI/browser loop family, small and single-corpus.

**What it does not prove.** Anything about held-out data; anything for Claude Code; any deployed benefit; any effect on outcomes of acting on the score.

## 4. Label-noise ceiling

I read 40 labels (20 adjust, 20 other; one reader, same model family as the labelers, so not an independent audit; `analysis/hand_sample.json`).

- Adjust labels: 20/20 reasonable.
- Non-adjust labels: 6/20 arguably adjust (redirect on feedback about the agent's plan or approach; new_task on a bug report about the just-finished feature). Wide interval (roughly 12-54%).
- The error is one-sided: hidden adjusts sit among the negatives and can only lower measured AUC.
- A predictor that perfectly separates the current positives would reach 0.87 / 0.79 / 0.74 if 10% / 20% / 30% of negatives are hidden adjusts. My estimate falls in the 20-30% range, so the ceiling is about 0.74-0.79 and the observed 0.65-0.71 is not far under it.
- Predictor comparisons are stable across six alternative label cuts (drop plan-context, drop redirect, drop no-tool checkpoints, tool-work only, and others): counters stay at or above Jev; ranking never changes. Label noise limits the absolute level, not the comparison.

An independent audit protocol is in `STAGE-A-LABEL-AUDIT.md`; it fixes the level question and is the gate for any further signal work.

## 5. Limits to state in the paper

- One labeler family; the hand-check is not independent. Negatives (redirect and new_task) are the weak part.
- Cursor transcripts carry no tool outputs, so signals about failures and test results cannot be read there.
- 157 sessions from one developer's workflow, mostly one repository family; 90% CI half-widths on a single AUC are about 0.05-0.06.
- Many variants were run across rounds; selection was done on discovery and checked on dev, but dev has been read many times. Held-out is the only clean test and has not been used.
- Baselines: counters were built after round 7, from the findings of the first rounds, so their feature choice is informed by the same data (they are not tuned against held-out).

## 6. What would change the conclusion

- A cleaned label set in which Jev's lead on judgement signals appears (the audit);
- more Claude Code data with tool outputs, where failure-and-verification signals become readable;
- a held-out test of the pre-registered combination: counters plus the best Jev UI/browser signal against counters alone.

Freeze rule: held-out is scored once, after a dev-replicated round and Cody's agreement on the frozen panel. Not yet frozen.

## 7. Scope: Stage A covers use case 1 only

Stage A tested use case 1 (in-session size/progress check at `PostToolBatch`). Its conclusions do not extend to use cases 2-4 (brief complexity after refine, unit needs-review, phase alignment), which are judgements over text a counter cannot read. See [STAGE-A-OTHER-CASES.md](STAGE-A-OTHER-CASES.md).

Implication for use case 1 (Cody, 2026-10-03): the trigger is a soft message the agent can weigh, not a hard stop. Together with the results above (Jev ties cheap counters, adds nothing material over them, and no signal separates good long runs from bad ones inside the counter-high stratum; Round 10), the default for case 1 should be a zero-call counter-timed nudge. Jev stays an optional arm. Whether a gated or more specific message beats a plain nudge is a behavioural question (agent reaction, human corrections, wasted turns, token cost of the nudge) that offline AUC against human labels cannot answer; it needs the Stage B live or controlled trial: no nudge vs counter nudge vs Jev-gated nudge.
