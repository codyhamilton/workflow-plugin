# Coding Harness Manager Interception / Steer-to-Stop — Adversarial Gate Review

**Date:** 2026-10-02
**Opus adversarial gate; docs only; Soft Standard HOLD**

---

## Verdict

**The pack is ready to land as a research-pack draft, but only after Section G is amended.** Sections A–F do what they say: H1 is clearly one candidate among several, H6 is rejected as gold, and no framing is picked as the winner.

The real collapse risk is outside the prose, in the code that already exists. `2026-10-02-interception-trials/batch-001/` is described as Wave-0, and it has three problems:

1. **It shows the model the final session length.** `run_batch001.py:542` sends `T_observed_session` with every cell, even though the cell is also tagged `shape_hint_withheld: true`. For non-Claude-Code harnesses, the lite states (`run_batch001.py:375-386`) also include `approx_progress_frac = cp/T`, `T_observed`, and `userish_count_full_session`. In the raw prompts the "Flash judge" (the deepseek-flash scorer) receives `"approx_progress_frac": 0.25` for checkpoint 176 of a 704-turn session.
2. **Its reference window is built from length alone.** `PROTOCOL.md:50-54` derives the "ideal steer window" from observed T only, so long sessions are labelled runaway by definition. Pack §A.3 rejects exactly this ("The number alone does not establish waste").
3. **Its checkpoint schedule depends on T and on H1.** Long sessions get H1's 75:15 cadence and shorter ones get T-proportional slices (`run_batch001.py:284-289`). That leaks length through the checkpoints, and H1's own parameters become everyone's sampling frame.

Any Wave-0 numbers from batch-001 therefore measure **how well the model predicts length when it is told the length**. They do not show whether any framing catches would-go-to-360 sessions or protects near-done work.

**Must stay open:**
- all of H1–H5 (no winner);
- the cost weights (premature 1.0 / near_done_fp 1.2 / runaway_miss 1.5 are an evaluation choice, not a finding);
- whether "avoidable continuation" can be identified from observational data at all;
- the action space (steer-to-stop versus other interventions; see H9).

---

## Risk table

| ID | Severity | Issue | Why it matters | Falsification / mitigation (docs-level only) |
|---|---|---|---|---|
| R1 | **BLOCK** | The outcome leaks into the inputs. Batch-001 prompts include `T_observed_session`. Lite states include `approx_progress_frac = cp/T`, `T_observed` and `userish_count_full_session`. | Every rating is contaminated by hindsight. "Fire inside the window" becomes reading a number back. This breaks pack §D.2 ("Future information … must not enter the checkpoint representation"). | Pack §G should require a written **leakage audit** (list every field in state and prompt, and flag any that depend on events after the checkpoint) before any batch counts as Wave-0. Batch-001 should be marked **non-evidential / plumbing-only** in the evidence log. |
| R2 | **BLOCK** | The reference window is a function of T alone (`PROTOCOL.md:50-54`). `near_done_fp` means "fired after T-20" and `runaway_hit` means "fired inside [T-90, T-30]". | This puts H2 inside the scoring rule and turns "long" into "runaway". It contradicts §A.3/§A.4. A session that was productive for 400 turns is scored as a runaway miss if the policy defers. | Pack §G.3 step 1 already asks for a frozen outcome sheet. It should state outright that **length-derived windows are not reference evidence**. Windows need closing-stage, thrash and requirement evidence taken from the transcript, and must be allowed to be `none` or `ambiguous`. |
| R3 | **BLOCK** | Checkpoint existence and schedule leak T. A short session (T<90) has no checkpoint at 90, and the schedule changes with T bands. | Even with the leaked fields removed, a policy of "fire at any checkpoint ≥ 90" gets **zero** near-done false positives on `short_natural`, because those cells don't exist. Survivorship bias wins the score. | Use T-independent schedules, the same for every session. Score any interception at turn t only against sessions that **survived to t**, i.e. conditional on still running at t (hazard framing, see H11). Report the never-reached cells. |
| R4 | ESCALATE | The corpus is selected on the dependent variable. The shortlist is length-first (disclosed in `PROTOCOL.md:26`) and concentrated in Maps / Claude Code. | Base rates of runaway are inflated, so fire-happy policies look good. Maps-family habits get treated as general. "Prefer T≥75 strata" in §G.2 makes this worse. | Pre-register strata **by shape evidence, not by T**. Include long-and-productive sessions and short sessions that were killed. Report results per project family. Variants from one session stay grouped (§D.2 already says this; G should repeat it). |
| R5 | ESCALATE | Observed T is censored and contaminated. Sessions end because a human interrupted, a cap or compaction hit, the user ran out of patience, or a crash. Human mid-session steers already exist in the traces. | "Natural continuation" is not natural. A 360-turn session may be 360 only because nobody intervened, or it may have been cut short by a human. Either way the reference future isn't the uninterrupted future. | Add a per-session field for **termination cause** and **count of human steers**. Treat human-ended sessions as censored, not completed. Note that existing human interrupts are already a confound for H5. |
| R6 | ESCALATE | H1 is the default scaffold for Wave-0. The batch-001 goal line *is* H1's chain. The H2–H5 work is labelled "thin probes" while H1 gets 100s–1k+ variants. | Volume asymmetry turns into evidence asymmetry: H1 ends up with the most rows, the richest Section C cells and the best-tuned prompts. That is a collapse by budget rather than by argument. | §G should state a **minimum per-framing evidence budget**, or require every scorecard to carry an "evidence volume vs H1" ratio. §H.2 rule 3 is necessary but not sufficient. |
| R7 | ESCALATE | Flash/Luna are drifting into judging. In batch-001 Flash returns the `rating` and `fire` that are then scored against the window, and Luna is "dual-label". | The pack calls Flash a *variation driver*. In practice it is the policy under test, and its outputs fill Section C. A "dual-label" step slides toward agreement as signal (H6 by the back door). | Name roles precisely in §G: **variant generator** (allowed), **policy-under-test** (allowed, labelled as such), **reference labeller** (forbidden). Dual-label output may only go to the H6 dissociation diagnostic. |
| R8 | WATCH | Variant count gets read as evidence. "Hundreds → 1k+" on ~30 sessions. | 1k variants on 30 sessions gives n≈30 for outcomes. The H.1 log has both n columns, but only in one shared cell. | Split the H.1 column into `n_sessions_independent` and `n_variants` as separate required fields. Rows with n_sessions < pre-registered minimum get the caveat "sensitivity only". |
| R9 | WATCH | Prompt-design overfitting / garden of forking paths. Many question × state × response-class cells get scored against the same ~30 sessions. | The best-scoring cell is mostly selection noise, and the shortlist gets tuned to the shortlist. | Pre-register the cells *and* a hold-out session set before the sweep. Report the full distribution across cells, not the best one. Give the hold-out to a different reviewer. |
| R10 | WATCH | `rating_plus_offset` / `fire_offset_turns` let a policy defer firing to a future turn it predicts. | An offset is a length prediction. Combined with R1–R3, it scores by guessing T-30. | Score offset fires only at the next real checkpoint. Treat the offset as a separate diagnostic column. |
| R11 | WATCH | The "would-go-to-360" success case has no operational definition in the pack. | Without one, any long session counts as a motivating win (the R2 failure under another name). | Define it in the docs: a long session where the transcript shows repetition, thrash, or post-boundary work with no demonstrated value for at least N turns. |
| R12 | WATCH | Steer execution is out of scope offline, but Section C cells will still read like system results. | §A.2 separates detection from steering, but scorecards may lose that distinction. | Every scorecard header states: "assessment/decision layer only; steer adherence unmeasured." |

---

## Missing framings (optional H7+ candidates, not winners)

- **H7: Revealed human steering.** Where Cody actually interrupted, redirected or abandoned a session is a separate, biased reference source: human timing is noisy, and human attention is unevenly distributed. It discriminates framings by asking which framing's fire times line up with real human interrupts. It is not gold, but it is the only non-model, non-length signal already on disk.
- **H8: Goal drift / scope divergence.** The agent is productive on the wrong target. H3 sees velocity, H4 sees no boundary, H2 sees budget left; none of them catch it. It needs a request-vs-activity alignment signal.
- **H9: Intervention-type selection.** Choose *which* steer to use (compact, re-scope, hand off, ask the human, stop) rather than *when* to stop. "Steer-to-stop" may be the wrong action for context-exhaustion or blocked sessions. This questions the pack's title assumption.
- **H10: Context / degradation health.** Quality decays with context saturation, compaction count, and rereads of the same paths. Stopping is a *reset* decision, not a waste decision. The snapshots already have `peak_ctx_tokens` and `reread_paths`.
- **H11: Hazard / survival framing.** Estimate the probability the session runs past 360 turns given that it is still running at t and given its features, with censoring treated properly. This is the right statistical frame for R3 and R5, and differs from H2 (fixed budget) and H5 (counterfactual value).
- **H12: Monitoring cost and observer effect.** Re-checks have a cost, and if checkpoints are ever visible to the agent, asking can change behaviour. This affects H1's 15-turn cadence most.
- **Cost-denominated variant of H2/H5.** Use dollars instead of turns. Turns vary a lot in cost (cache reads versus fresh context). The session→cost join is timestamp-only, via `cost_window.py` plus `pricing.json`, with no direct key.

---

## Metric-gaming attack surface (concrete)

1. **Read T back.** Any policy given `T_observed_session` or `approx_progress_frac` can fire at about 0.75·T and score near-perfect `runaway_hit` with zero `near_done_fp`. This is live in batch-001.
2. **Constant-turn firing.** Under the [T-90, T-30] window for T ≥ 160, "always fire at 90" hits every long session with T between 160 and 180. Under the 75:15 schedule it never meets a short session at 90. A trivial clock beats a thoughtful policy.
3. **Never-fire on a short-heavy corpus.** If the corpus is rebalanced toward short sessions, deferring always earns `defer_ok`. The weights decide which degenerate policy wins.
4. **Weight arbitrage.** With runaway_miss = 1.5 and near_done_fp = 1.2, a policy that fires slightly early on every long session comes out ahead even if it truncates near-done work 1:1. Report the components; do not optimise the sum.
5. **Survivorship.** Scoring only checkpoints that exist rewards fires at late turns. Late turns exist only in long sessions.
6. **Response-class mapping.** `four_class` fires only on `likely_runaway`. Moving uncertain cases into `uncertain` (rating 1, no fire) cuts false positives with nothing changed underneath. Track the abstention rate as its own metric.
7. **Cherry-picking cells.** Report the best of about 96 (state × question × response-class) cells and you will find a winner by chance.
8. **Agreement inflation.** Feed Flash and Luna the same leaked state and their agreement goes up with no improvement in outcomes. This is H6's predicted failure, made easier by R1.
9. **Volume as rigour.** "1k+ variants" reads as coverage while independent n stays around 30.

---

## Challenges to Wave-0 / evidence fold-in (Sections G/H)

- **"Ready to run" in §G is false while R1–R3 stand.** Change the status to "ready after leakage audit + T-independent schedule + evidence-based outcome sheet". Batch-001 should be logged in H.1 as `plumbing-only; contaminated (T leak)`, not as the first evidence row.
- **"Soft Standard HOLD ≠ pause" is fine, but "do not wait for perfect theory" is being used to skip §D.2's own leakage rule.** Throughput is not the constraint; validity is.
- **The outcome sheet must be frozen *before* any Flash cell runs, by someone other than the policy-under-test.** §G.3 lists it as step 1 but doesn't make it a gate. Batch-001 ran without one: its windows are computed inline.
- **The shortlist is reused, not pre-registered for this question.** §G.2 says "reuse, don't invent", but the #96 shortlist was built for a different purpose (inventory, ranked by length). Reuse carries its selection bias forward (R4).
- **§H.1's `.scratch/` intake** may keep the evidence log out of git and out of review. Move it to the research tree from the first row.
- **§H.2 rule 2 ("prefer fire-time vs ideal")** gives the ideal window a privileged place before it can be defended. Add: "only where the window has transcript-evidence support; otherwise report `window: unidentified`."
- **Missing discriminating experiment:** a **leak-ablation pair**, the same cells with and without T-derived fields. If scores barely move, the policy wasn't using the state. If they collapse, earlier results were reading the answer.
- **Missing null baselines:** constant-turn firing, never-fire, and random fire at the same rate must be scored next to every framing. Without them no scorecard means anything.

---

## Explicit non-authorization

This review **does not authorize**:
- unlocking Soft Standard;
- any use of TypeSafe;
- any hooks unlock;
- Pilot live Jev;
- any shipping behaviour change.

No framing is selected, no hybrid is endorsed, and favourable Wave-0 scores do not release any hold.

---

## Recommended Composer land path

```
docs/lab/RESEARCH/2026-10-02-interception-steer-to-stop/
  RESEARCH-PACK.md                 # Sections A–H as drafted, with §G amended per R1–R3/R6/R7
  ADVERSARIAL-GATE-opus.md         # this review, verbatim
  OPEN-FRAMINGS-H7plus.md          # candidates only, explicitly not promoted
  EVIDENCE-LOG.md                  # §H.1 table, in-tree (not .scratch/); first row = batch-001 "plumbing-only; T-leak contaminated"
  WAVE-0-PREREG.md                 # leakage audit checklist, T-independent schedule, frozen outcome-sheet criteria, null baselines, hold-out set
docs/lab/RESEARCH/2026-10-02-interception-trials/batch-001/   # leave as-is; add LEAKAGE-NOTE.md cross-referencing R1–R3
docs/lab/RESEARCH/INDEX.md         # add one line pointing at the pack dir
```
