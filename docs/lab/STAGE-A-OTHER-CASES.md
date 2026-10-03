# Use cases 2-4: what Stage A discipline requires, and what data exists (2026-10-03)

Source of the cases: [use-cases-cody-locked.md](RESEARCH/2026-09-30-jev-cheap-judgement-signals/use-cases-cody-locked.md). Case 1 is covered by [STAGE-A-WRITEUP.md](STAGE-A-WRITEUP.md). The objection that settled case 1 ("a counter does the same job, so why check") is weaker here: the input is text a counter cannot read. It is not absent: each case has a zero-call baseline that must be beaten first.

| Case | Jev judges | Zero-call baseline | Outcome label (not the model's own opinion) |
|---|---|---|---|
| 2. After refine | brief complexity, to review largest before dispatch | brief line/char count, number of files or acceptance items named | unit later exceeded its budget: worker turns, cost, "done with concerns", splits or re-briefs |
| 3. Unit complete | does the closing record need review? | trailer present, headings, verifier exit code | review or rework found real defects after the unit; a later fix commit touching the same files |
| 4. Phase complete | does the report align with phase intent? | `tools/driver/phase_assert.py --deterministic` | later rework of the phase, or a plan-level revision |

## Data inventory (found, not yet analysed)

- About 133 distinct brief files (md5-unique) across real consumer repos in `~/workspace` (open-pajero-maps, garcia-music, silver-chronicle, chm-briefs, corpus-ops, free-frontier), after excluding workflow-plugin's own worktrees and the many clones of the same repos.
- Unit outcomes in git: e.g. open-pajero-maps has 338 commits with unit-level subjects ("Plan 04 Phase 3 unit 3-14 ... done with concerns", merges), and per-plan `IMPLEMENTATION.md` files.
- Driver run records (`tools/driver/.run-record.jsonl`) hold provider cost/turns and the last workflow-report per invocation, where runs were made.
- Worker transcripts per brief exist for projects with Claude/Cursor sessions (the Stage A corpus partly covers them).

## Caveats to settle before any measurement

- Many briefs are duplicated across worktrees and clones: split by brief id (content hash), never by directory, or the held-out set leaks.
- Outcome labels need to be derived mechanically from git/driver data first (turns, cost, "concerns", follow-up fixes) and hand-checked on a sample, as Stage A showed label error is one-sided and caps AUC.
- Case 4's baseline already exists and is authoritative; the Jev question there is only whether it flags drift the assert passes.
- Held-out for these cases is separate from Stage A's and stays sealed until a dev-replicated result exists.

## Proposed order

1. Case 2 first: most data (133 briefs), cleanest mechanical outcome (budget overrun), and a trivial baseline (length).
2. Case 3: derive "later fix to same files" from git; needs more care on label noise.
3. Case 4: fewest samples; likely a descriptive section, not a test.

## Case 2 first run (brief complexity, 78 briefs)

Scripts: `tools/jev-variants/case2/` (pair -> label2 -> facts -> base -> doc_runner -> score/incr). Data (briefs, labels, Jev responses) is in the lab archive `case2/`, not the repo. 78 briefs x 3 states x 5 questions = 234 calls, 0 errors, cents of spend.

States: **A** brief text only. **B** brief plus a deterministic FACTS table (owned/required-reading paths: exists or not, lines, bytes, parsed budget). **C** FACTS only, no prose.
Outcome: `process_trouble` (10 units; the worker hit unplanned work), from an LLM label with an evidence quote; STRICT = 7 hand-checked; proc+neg = 14. All positives are in open-pajero-maps (10 of 55); silver-chronicle (18) and garcia-music (5) have none.

| Score (AUC vs process_trouble) | all | 90% CI | strict | proc+neg |
|---|---|---|---|---|
| zero-call `owned_new_files` | 0.76 | [0.65, 0.86] | 0.69 | 0.71 |
| zero-call `budget_turns` | 0.62 | [0.45, 0.79] | 0.63 | 0.64 |
| Jev A "unplanned trouble?" | 0.76 | [0.58, 0.89] | 0.82 | 0.73 |
| Jev A "overall complex?" | 0.74 | [0.65, 0.83] | 0.67 | 0.78 |
| Jev B (brief + facts) trouble / complex | 0.57 / 0.73 | | 0.61 / 0.63 | 0.60 / 0.75 |
| Jev C (facts only) trouble / complex | 0.48 / 0.31 | | | |
| rank-sum Jev A trouble + new_files | 0.83 | | 0.83 | 0.78 |

Reading, with the caveats it needs:
- Jev on the brief prose alone ties the best counter (0.76) and is only weakly correlated with it (rho 0.18 with new-file count), so the combination (0.83) is plausibly additive. That is the first case where Jev has something a counter does not.
- Adding the deterministic FACTS table did **not** help; it hurt the trouble question (0.76 -> 0.57). Facts-only is at or below chance. The facts are most useful as zero-call baselines, not as Jev context.
- 15 Jev comparisons were run and the positive set is 10 (7 strict) from one project, so the CIs are wide and the headline number is not corrected for multiplicity. Nothing has been replicated; there is no held-out or second-project positive.
- Next: freeze one question (trouble), wait for new briefs/outcomes as a replication set, and label the 3 other projects' units for a negative-result check. Case 3 follows.

## Case 3 first run (unit complete: "needs review?" / will need a fix)

Scripts: `tools/jev-variants/case2/c3*.py` (c3b candidates -> c3_facts -> c3_run -> c3_score). Data in the lab archive `case2/`.

**Units.** The briefed units in case 2 only yield 51 units with resolvable commits and 6 fix-like follow-ups, mostly weeks later, so they cannot carry a test. Instead the unit is a non-fix, first-parent commit (601 across open-pajero-maps 116, silver-chronicle 41, garcia-music-opt-18 444). **Outcome:** a later `fix`/`revert`/`bug`/`regress` commit within 72h (also 7d) touching the same files. Only garcia has enough positives (78 under the strict rule), so all scoring is garcia-only (n=444).
**States** (1803 calls, 0 errors): A message + diffstat + 14k-char diff; B = A + deterministic facts (files, lines, test files, prior-30d fix commits on those files); C = message + diffstat + facts, no diff body. Five questions: fix-needed, review-warranted, risk, partial/loose ends, complexity.

**Outcome-definition trap (found, not fixed by the data).** The first outcome ("fix covers >=50% of the original's files") is size-confounded: small commits hit it easily, so zero-call `files` scores AUC 0.22 and every Jev score (which tracks size) is "anti-predictive" (0.32-0.47). Size-stratified AUCs (strata 1 / 2 / 3-4 / 5+ files) remove this.

| size-stratified AUC, garcia | strict outcome (>=50% overlap, 72h) | any overlap 72h | any overlap 7d |
|---|---|---|---|
| zero-call prior fix commits on files (30d) | 0.62 [0.54, 0.70] | 0.58 | 0.57 |
| zero-call message length | 0.61 [0.55, 0.68] | 0.56 | 0.63 |
| zero-call lines added | 0.42 | 0.59 | 0.58 |
| Jev A fix / review / risk / complex | 0.40 / 0.39 / 0.44 / 0.45 | 0.50 / 0.54 / 0.55 / 0.58 | 0.57 / 0.54 / 0.56 / 0.57 |
| Jev C (no diff body) fix / complex | 0.46 / 0.46 | 0.56 / 0.59 | 0.58 / 0.59 |

Reading: **no signal.** Under the size-neutral outcomes Jev sits at 0.50-0.59, the same as the zero-call baselines (prior-fix history, lines added), with no state beating the diff-free state C. Under the strict outcome Jev is at or below chance. The outcome is itself weak: in a hot, fix-heavy repo (garcia: 62% of commits have some later fix touching the same file) a later "fix" commit is mostly unrelated churn on a shared file, not a defect in this unit. So this is "no evidence", not "evidence of absence". Better labels (line-level overlap via blame of the fix hunks against the unit's added lines, or a human review verdict) would be needed before spending more on case 3. Case 4 remains: it has the fewest samples and a deterministic baseline (`phase_assert.py --deterministic`).

## Case 4 first run (phase-complete alignment sanity) — descriptive only

**Data.** 11 labelled phase events from 4 IMPLEMENTATION.md files (open-pajero-maps plans 03/04, silver-chronicle plans 01/02), split into phase-run blocks (`tools/jev-variants/case4/`). Labels from the closing record: 3 `not_closed` (p03 phase 2 run 1, restart, grounded), 6 `closed`, 1 `closed_with_debt`, 1 `closed_with_concerns`. Strict outcome = not_closed (3 pos); soft = anything not clean-closed (5 pos). The three not_closed events are successive attempts at one phase, so they are not independent. Historical phases have no trailer or workflow_report, so only the heading/evidence sub-checks of `phase_assert.deterministic_outcome_evidence` apply.

**States.** A: work record with verdict/verification/carried sections and status lines stripped; B: A plus a counted-facts line; C: facts only; D: full record including verdict (ceiling, label leaks by design). 5 questions, 55 calls, 0 errors.

**Result (AUC, n=11, no CIs worth quoting).**

| state | notdone | digdeeper | unresolved | concerns | claimed |
|---|---|---|---|---|---|
| A strict | 1.00 | 0.75 | 0.83 | 0.75 | 0.44 |
| B strict | 0.96 | 0.73 | 0.81 | 0.75 | 0.48 |
| C strict | 0.71 | 0.75 | 0.71 | 0.67 | 0.40 |
| D strict | 1.00 | 1.00 | 1.00 | 0.98 | 0.46 |
| A soft | 0.90 | 0.80 | 0.87 | 0.73 | 0.60 |

Zero-call counters (strict / soft): chars 0.75/0.80, bounce 0.67/0.62, over_budget 0.67/0.70, concerns 0.35/0.62, units 0.31/0.53.

**Versus the deterministic baseline.** The assert's evidence sub-check passes 10 of 11 events, including two of the three not_closed ones; verification-heading and carried-heading checks are mixed and do not track the label (each passes some not_closed and fails some closed). So there is drift the deterministic checks pass that Jev flags: on the stripped record `notdone` ranks all 3 not_closed events above all 8 others. The kill line (Jev disagrees with a deterministic check in the same state) would fire here on the evidence check, which suggests those sub-checks are too weak for the historical shape rather than that Jev is wrong, since the failed-gate text is visible in the work record.

**Caveats.** n=11 with 3 non-independent positives; a failed gate described in the body is not "alignment drift" Jev discovered, it is easy reading; the stripping is regex-based and may leave residual cues (leak check found none of the obvious strings); chars alone gets 0.75–0.80, so the size confound is not excluded; the one closed-with-debt/concerns pair is where Jev is weakest (`notdone` 1.1–2.2). Facts-only (C) is clearly worse than the record, so Jev is reading content. The real question — drift that later forces rework of a phase that the assert passed — needs prospectively collected `--live` pairs; this run cannot answer it. Report as descriptive.

Data: `~/jev-lab-data/2026-10-03-stageA/case4/` (items4.json, run4.jsonl, blocks.json).
