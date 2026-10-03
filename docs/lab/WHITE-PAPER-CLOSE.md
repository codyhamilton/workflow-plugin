# Stage A close: what is established, what is a hypothesis, what is open (2026-10-03)

Scope: a characterisation of in-session size signals (use case 1), a feasibility result for scoring plan text against concrete criteria (use cases 2-4, descriptive), and a data-collection design for the rest. `STAGE-A-WRITEUP.md` is the use case 1 paper; `STAGE-A-OTHER-CASES.md`, `QUALITY-CRITERIA.md` and `RESEARCH/2026-10-03-good-plan/` are its appendices. Held-out is sealed and was never scored. Nothing here claims an effect of acting on a score.

## 1. Established (replicated, or independent of the noisy label)

| # | Finding | Basis | Limit |
|---|---|---|---|
| E1 | Criteria-style Jev questions are effectively deterministic: test-retest rho 0.96-1.00 (case 2: 8 criteria x 78 briefs; case 4: 6 x 11); run-to-run SD about 0.002; about $0.0002 per call. | Re-run of identical inputs | Stable is not correct |
| E2 | In-session signals measure how long and broadly the agent worked without a human. They predict "adjust" (AUC 0.65-0.71), and predict against redirect and new_task. | Discovery-to-dev replication; six alternative label cuts; ranking of predictors never changed | One developer, mostly one repo family; Cursor-heavy; CI half-width about 0.05 |
| E3 | A zero-call counter ties Jev: Jev adds +0.007 to +0.032 over counters, counters add nothing over Jev; eight further judgement signals add 0.001 (CI -0.010 to +0.011). | Incremental AUC, session-cluster bootstrap | Same corpus |
| E4 | Wording, state size and thresholds matter little; hedging and "absent" polarity each cost about 0.15 AUC. | 225k early rows | Internal to the method |
| E5 | Label noise one-sidedly lowers measured AUC; achievable ceiling is about 0.74-0.79. | Hand check of 40 labels | One reader, same model family: the level is soft, the direction is not |
| E6 | Jev's self-reported confidence does not flag its errors; probabilities add nothing over the score. | Case 4 | n=11 phases |
| E7 | Anchoring each level to concrete content fixes a saturated or ambiguous question (`unresolved` 0.87 to 1.00) but not one whose answer is absent from the text. | Case 4 tuned; case 2 untuned replication showed no gain | Case 4 was tuned |
| E8 | Pairwise comparison is about as good as absolute scoring (80-84% of pairs right), with no position bias. | Cases 2 and 4 | 10 positives on case 2 |
| E9 | Null results: P0 exit-point panel failed its reliability floor (alpha 0.12-0.18); template-compliance criteria do not predict trouble; threshold provenance did not separate churn (16 vs 15 Pajero briefs); executor reports find mechanical plan defects only (1 of 120 named an unproven assumption). | As registered | Pajero only for the last two |

## 2. Hypotheses with the test that would settle each

| Hypothesis | Present evidence | Settling test |
|---|---|---|
| `b.discovery_free` (no step left for the worker to discover) predicts process trouble | AUC 0.84 (0.89 with new-files counter); best of 8; all positives from open-pajero-maps | Same criterion, a second project, and fresh briefs; AUC CI above 0.5 on 2 projects |
| `rework` and `failed_gate_open` track phase non-closure | AUC 0.92 / 0.79 strict, n=11 | More phases from other projects |
| Jev beats a code counter on browser/UI loops | 0.66 vs 0.54 name regex, one corpus | A held-out test of counters plus the best UI signal against counters alone (pre-registered) |
| Unproven acceptance criteria cause stop-and-ask churn (U1, U2) | User observation; backtest could not test it | Large linked dataset (runs across models and repos); intervention rows joined to briefs |
| The 23 candidate clusters in `CONSOLIDATED.md` | LLM-sourced convergence only | Stage 5: rho >= 0.9, AUC CI > 0.5 on 2 projects, adds signal beyond size/new-files |

## 3. Open (unanswered)

Held-out performance; Claude Code in-session signals (61 labelled checkpoints, 9 positives); any benefit from acting on a score; whether failed plan checks predict execution cost; use cases 2-4 beyond the descriptive runs.

## 4. Next stage

Collect, do not judge: runs posted through the quality service (plans, briefs, executions with ids in frontmatter and commit titles, hook events, stored text) across models and repos; keep all checks live; then test the hypotheses in section 2 and the check-to-cost link. See `QUALITY-SERVICE.md`.
