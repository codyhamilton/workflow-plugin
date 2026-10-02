# Adversarial fold — Soft HOLD evidence from #105, #109, #110 (and #111)

> **Soft Standard HOLD.** Docs and recomputed evidence only. No hooks, no
> behaviour unlock, no runner change, no FP/miss board. This note reports no
> fire-versus-outcome comparison of any kind; it uses outcome labels only to
> describe **what the reference set can and cannot identify**.

**Seat:** Claude analysis (relaunch of the cancelled `bc-347187f3` seat).  
**Inputs:** [#105](https://github.com/codyhamilton/workflow-plugin/pull/105) corpus analysis,
[#109](https://github.com/codyhamilton/workflow-plugin/pull/109) GROWTH ranking and Flash vol2 glance,
[#110](https://github.com/codyhamilton/workflow-plugin/pull/110) growth-fill-v1 refill,
[#111](https://github.com/codyhamilton/workflow-plugin/pull/111) analysis fold, read against the
[white paper](../../PROPOSALS/2026-10-02-interception-steer-to-stop.md) and
[`ADVERSARIAL-GATE-opus.md`](ADVERSARIAL-GATE-opus.md).  
**Method:** every figure below was recomputed from landed files at `fc8171e`
(`typesafe-scenario-sweep/results.jsonl`, `meters.json`, `GROWTH-RANKING.json`,
`outcome-labels.jsonl`, `window_status_join.py` output, Wave-0 `results.jsonl`).
Recipe in [Appendix A](#appendix-a--recomputation-recipe).

## 0. Verdict

The landed numbers reproduce: 15,834 retained / 13,522 measured rows, 103/1,632
GROWTH fires, bands `334/31/16/4/5/2`, 10/192, 6/108, 4/84, and 9/4/3 label-join
coverage all match #105/#109/#110/#111. **No arithmetic error was found.**

The problems are in what the numbers can support. Five findings change the
white-paper recommendations (details in §1–§5; recommendations in §7):

1. **The preferred 12×9 cut cannot identify a miss.** All nine exact-labeled
   snapshots have `runaway_like=no`; eight are `no_steer_window`, one is
   `outside_steer_window`. It sits below the white paper's own labeled minimum
   on the runaway axis (0 of the required ≥4) and cannot supply the required
   non-Maps hold-out. Never-fire is therefore unbeatable on the miss column.
2. **Eight of the twelve preferred pairs are response-constant under TypeSafe.**
   The 10 preferred-cut fires come from two `markers_focus` pairs (9 + 1). The
   other ten pairs fire 0/16, including all eight `recent_delta_brief` pairs
   (0/128).
3. **The representation choice was not neutral.** The same question flips with
   state: `test_flake_loop` is 0/16 on the preferred `markers_focus` and 10/16
   on the rejected `phase_hints_focus`; `bash_retry_storm` 0/16 on preferred
   `recent_delta_brief` and 5/16 on `phase_hints_focus`. The ranking was an
   analytic selection after #110, so it cannot claim to have predicted this.
4. **The sweep's checkpoint is not T-independent.** `pick_rep_snap` takes the
   median of the *reached* checkpoint list, which is a function of session
   length. That is the Opus R3 failure mode reappearing in checkpoint
   *selection* rather than in the prompt.
5. **Every GROWTH-eligible session is `open-pajero-maps` and claude-code.** The
   white paper caps both at 40%. GROWTH evidence is a single-project,
   single-harness stratum with 16 sessions (14 plus 2 worktree variants).

None of this contradicts Soft HOLD. It means the next GROWTH spend should not
be sized in cells.

## 1. What the 12×9 cut can and cannot identify

Description from labels and join eligibility only. No response is used.

| Property of the nine `label_join_exact` snapshots | Value |
|---|---|
| `runaway_like_at_checkpoint` | **no 9 / yes 0** |
| `near_done_at_checkpoint` | yes 5 / no 4 |
| Derived `window_status` | `no_steer_window` 8, `outside_steer_window` 1, inside 0 |
| Project / harness | `open-pajero-maps`, claude-code (9/9) |

Across **all 20 labeled sessions** at their sweep checkpoint: runaway-like `no`
13, unlabeled 7, **`yes` 0**; `inside_steer_window` 1 (that session's
checkpoint outcomes are unlabeled); `outside` 2; `none` 17. The four
runaway-like slots in the sidecar (two sessions) sit at *other* checkpoints.

Consequences against the white paper's ranking gate
([§4](../../PROPOSALS/2026-10-02-interception-steer-to-stop.md)):

| White-paper requirement | 12×9 cut |
|---|---|
| ≥12 labeled sessions surviving to t=75 | 5 of 9 are at 75; the other four are at 45 or 60 |
| ≥4 sessions with runaway-like `yes` and a cited window | **0** |
| ≥4 `none`/near-done sessions | met (8 / 5) |
| Hold-out ≥4 labeled sessions incl. ≥1 non-Maps | **0 non-Maps possible** |
| Beat never-fire on `runaway_miss` inside a non-`none` window | never-fire scores 0 misses here; criterion unwinnable |

So a policy that never fires looks perfect on the miss column of this cut and
is penalised only on the near-done side by its competitors. The cut is a valid
**response-distribution** instrument. It is not a ranking instrument for any
framing, and a later "H1 beats nulls" statement drawn from it would be
vacuous on one half of the success definition. This is the same structural
point #106 made about `window_status`, now localised to the preferred cut.

Corollary for #105's Wave-0 provisional join: the 15 `runaway_miss_candidate`
cells come from **2 sessions** (the 27 near-done cells from 12; the 48
productive-interrupt cells from 9). Effective n for the miss side is 2.

## 2. Response structure of the refill

All counts are from the 1,632 post-fill GROWTH rows (102 scenarios × 16
sessions); 25 scenarios fire at all and 77 never do.

### 2a. The preferred cut is nearly constant

| Preferred pair | Fires /16 |
|---|---:|
| `markers_focus × idle_tool_spin` | **9** |
| `markers_focus × context_thrash_compact` | 1 |
| `markers_focus × dependency_wait`, `× test_flake_loop` | 0, 0 |
| `recent_delta_brief ×` eight questions | 0 each (0/128) |

Ten of 192 preferred cells fire; 90% of them belong to one pair. A paired
contrast between drivers or levers on ten of twelve pairs has no TypeSafe
variation to explain. That is a property of TypeSafe at this wording, not of
the other drivers (Flash fires 19–38% on finished slices), so a multi-driver
run still has information; a TypeSafe-only run on this cut mostly does not.

### 2b. Same question, different state

Fires per 16 sessions, every new GROWTH question under all three states (the
refill already contains this table; no new spend is needed):

| Question | Preferred state | markers | phase_hints | recent_delta |
|---|---|---:|---:|---:|
| `dependency_wait` | markers | 0 | 0 | 0 |
| `context_thrash_compact` | markers | **1** | 0 | 0 |
| `idle_tool_spin` | markers | **9** | 2 | 1 |
| `brief_abandon` | recent | 0 | 0 | 0 |
| `docs_only_drift` | recent | 2 | 0 | **0** |
| `scope_creep_silent` | recent | 0 | 0 | 0 |
| `edit_churn` | recent | 1 | 0 | **0** |
| `bash_retry_storm` | recent | 1 | **5** | **0** |
| `parallel_agent_thrash` | recent | 3 | 0 | **0** |
| `test_flake_loop` | markers | **0** | **10** | 0 |
| `speculative_rewrite` | recent | 0 | 0 | 0 |
| `deliverable_orphan` | recent | 0 | 0 | 0 |

Reading, with limits:

- Five questions (`dependency_wait`, `brief_abandon`, `scope_creep_silent`,
  `speculative_rewrite`, `deliverable_orphan`) are 0/48 under every state.
  Several concern exactly the scope/deliverable axes H4 and H8 care about.
  Zero-fire is **absent evidence**, not negative evidence: the cause may be
  wording, driver conservatism, or a genuinely quiet corpus, and nothing here
  separates them.
- `recent_delta_brief`, preferred for 8 of 12 questions, is the lowest-
  responding state: 1/192 on the new questions (17/544 overall, versus 51/544
  for `markers_focus`). It is not unresponsive: legacy `silent_stall` fires
  9/16 on it. The lever is question wording, not only state shape.
- New-question fire rate is **35/576 (6.1%)**; legacy-question rate on the
  same states is **68/1,056 (6.4%)**. The twelve purpose-written GROWTH
  questions did not produce a response different in kind from the pre-GROWTH
  wordings; legacy `silent_stall` (25 fires) and `output_starvation` (19) still
  lead the GROWTH block.
- The `test_flake_loop` 0 vs 10 and `bash_retry_storm` 0 vs 5 swings are on the
  same 16 sessions, so they are paired. They show the preferred-state rule
  ("most direct evidence") did not pick the highest-eliciting representation
  for those questions. That is not an argument that eliciting more is better
  (#109 is right that fire is not the objective). It is an argument that the
  representation contrast cannot be deferred to "later": for these pairs state
  shape moves the answer more than any other lever measured so far.

### 2c. Session concentration

GROWTH fires per session (of 102 scenarios): 18, 11, 11, 10, 9, 8, 8, 6, 5, 5,
4, 3, 3, 1, 1, 0. The top three sessions carry 40/103 (38.8%). In the
preferred exact-label cut, the six fires come from five sessions
(`2e083814b952` contributes two). Independent n is the session count:
**16 for GROWTH, 9 for the exact cut**, not 1,632 or 108.

Session propensity also travels across drivers and questions. On the 13
sessions present in both Wave-0 Flash and the GROWTH refill, per-session fire
rate correlates **ρ = 0.61** (exact permutation two-sided p ≈ 0.03, 20,000
shuffles; exploratory, n=13, not a registered contrast). `2e083814b952` fires
on every reached Wave-0 cell and 10/102 GROWTH cells; `a56bad1c7f13` fires on
5% of Wave-0 cells and 0/102. Either sessions differ in observable features the
state shows (plausible, and the point), or fire is partly a session-level
nuisance. This cannot be separated without session-level covariates
(tail length, turn count, activity density) and is the main reason cell volume
buys less than it looks.

## 3. Sweep-wide state eligibility (extends the #109 audit)

The #109 audit covered the original 200×41 sweep. Across the **13,522
measured rows** the same artifact is larger than the aggregate suggests.

| Slice | Fires / cells | Rate |
|---|---:|---:|
| All measured | 255 / 13,522 | 1.89% |
| claude-code (state-eligible) | 192 / 6,272 | 3.06% |
| Non-Claude (lite: opencode, codex, cursor) | 63 / 7,250 | 0.87% |
| …of which empty-state `tail_focus` / `delta_only` × `silent_stall` | 50 | — |
| All measured excluding those 50 | 205 / 13,472 | 1.52% |

State-level consequences:

- `delta_only`: **0/608 on claude-code** (25/950 on lite, all empty-state).
  The §2a statement "`delta_only` fires 2.18%" is entirely the empty-state
  artifact. On state-eligible sessions it never fires.
- `tail_focus`: 16/448 (3.6%) on claude-code; the lite 25/700 are the empty
  state.
- `window_delta_tools`: 0/1,148 across harnesses is a schema mismatch (#109),
  not a negative selector.
- The headline 1.89% and the pooled state ranking in `ANALYSIS.md` §2a mix a
  3.06% state-eligible stratum with a 0.87% stratum of which most fires are
  gating failures. Quote the claude-code stratum, or report both with the
  eligibility column, and never the pooled figure.

## 4. Checkpoint selection and T

`pick_rep_snap` in
[`run_typesafe_scenario_corpus_sweep.py`](../2026-10-02-interception-trials/batch-002/run_typesafe_scenario_corpus_sweep.py)
returns `cps[len(cps)//2]` of the *reached* checkpoint list. The list's length
is set by how long the session ran. Two consequences:

1. **Opus R3 returns through selection.** Prompts carry no `T`, but which
   checkpoint is judged depends on `T`: a short session's median checkpoint is
   close to its end; a long session's is not. The white paper's at-risk rule
   fixes the *schedule*; this selector reintroduces length into *which cell is
   scored*.
2. **Near-done is over-represented at the sampled cell.** At the sweep
   checkpoint, near-done is `yes` in 8 of 13 complete labeled sessions
   (62%); across all reached labeled checkpoint slots it is 24 of 67 (36%).
   n=13 and the slots are within-session-correlated, so this is a hypothesis,
   not a finding, but its direction is what the selector's design predicts.
   If true, a one-checkpoint-per-session sweep samples a harder near-done mix
   than the fixed schedule and cannot be read as base-rate-neutral.

Additionally, sessions whose median checkpoint is 35, 55 or 70 are off
`FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)`. They are the four
checkpoint-unlabeled and three session-unlabeled snapshots by construction.
Label coverage is a function of the checkpoint selector.

Recommendation: for any GROWTH replication, score on the **fixed schedule**,
every session at every checkpoint it reached, with n_at_risk beside each, as the
white paper already requires. Keep the median-of-reached sweep for
state/wording sensitivity only.

## 5. Pool composition against the white-paper caps

| Pool | Sessions | claude-code | `open-pajero-maps` |
|---|---:|---:|---:|
| Scenario sweep (non-GROWTH) | 41 | 16 (39%) | 16 (39%) |
| GROWTH refill | 16 | 16 (**100%**) | 16 (**100%**; 2 are worktree variants) |
| Preferred exact-label cut | 9 | 9 (**100%**) | 9 (**100%**) |

The white paper (§5) caps claude-code and Maps at 40% and requires that the
length lens keep its sign when Maps share is ≤40%. GROWTH cannot be tested
for that sign change until a non-Maps `tail` exists. The 25 gated sessions
(opencode 20, codex 3, cursor 2) hold the whole non-Maps and non-Claude
population. The #108 gate is right not to fabricate a tail. The consequence is
that **all GROWTH estimates are stamped Maps-concentrated and
claude-code-only**, and the Flash/Luna cross-driver contrast that the white
paper treats as a sensitivity column cannot be run on non-Claude sessions at
all.

## 6. Other fold points

**Flash vol2 `parse_miss=10` (#109).** The #109 conclusion (no landed raw, so
no root cause) stands. Add the inferential consequence: parse-miss cells are
removed from fire-rate denominators, and a whole-batch decode failure is
non-random with respect to content (long states, odd rationale). Treat Flash
rates from streams without a per-batch diagnostic sidecar as
**missing-not-at-random until shown otherwise**. The §2d "Flash 19–31% vs
TypeSafe 1.3%" contrast also rests on partially scored streams (`flash-scale`
250 of 2,400, `flash-mid` 50 of 1,600); the "expected given driver role"
explanation in `ANALYSIS.md` is untested.

**Label provenance.** All 20 labels are `chm-sol-adjudication`. The
independence attestation covers Flash rating/fire and leaked fields; it does
not address a Sol-family driver being scored against Sol-family labels, nor a
single adjudicator's error being shared across every join. Any driver from the
labeler's model family needs a stamped caveat, and a second adjudicator on the
nine exact-label sessions is cheaper than any new trial.

**Cut provenance.** #110 merged before #109, and the selection rule is
"evidence compatibility", reached by reading the refill's neighbourhood. #111
already says this is not preregistered. Add the quantitative reason to care:
the fire rate of the *non-preferred* GROWTH pairs (93/1,440, 6.5%) is close to
the preferred ones (10/192, 5.2%; cell-level rates, no session-clustered
interval computed), so the choice of 12 over 102 did not visibly isolate a
more responsive region.

**Stale text in `ANALYSIS.md`.** After #111, §4 (open gaps) and §5 (next
experiments) still describe the pre-#108 state. Updated in this PR.

## 7. Recommendations for the white paper

Appended to the white paper as an amendment (status unchanged,
`resolved-soft`). Each is docs-level and unlocks nothing.

| # | Recommendation | Evidence |
|---|---|---|
| A1 | Size GROWTH waves in **sessions with positives**, not cells. Add to the scale bar: a wave is not "ranking-ready" until the labeled pool meets the §4 minimum (≥12 at t=75, ≥4 runaway-like with a cited window, ≥4 near-done/none, ≥4 held-out incl. ≥1 non-Maps). Until then publish response-distribution diagnostics only. | §1: 0 runaway positives in the 12×9 cut; effective n 9 and 2 |
| A2 | Label before spending: adjudicate `runaway_like`/`ideal_steer_window_by_cp` on candidate checkpoints, and on the seven unlabeled GROWTH-eligible snapshots, **before** the next TypeSafe/Flash/Luna refill. Label blind to any response, as the outcome sheet already requires; add a second adjudicator on the nine exact sessions. | §1, §6 |
| A3 | Freeze pair IDs **and a state-contrast rule** before the next driver runs. Promote the representation contrast (all three states per question) from "later" to a paired control for every preferred question. Freeze the contrast list; publish all 36 question × state pairs. | §2b: state moves answers 0 → 10 |
| A4 | Report **response occupancy** per pair: fire count, session count with any fire, and an `all-defer` flag. A pair that is all-defer for a driver is marked uninformative for that driver and is not counted toward the trial floor. | §2a: ten of twelve pairs constant; five questions 0/48 |
| A5 | Replace the median-of-reached selector with the fixed schedule for any claim that touches near-done or runaway. Stamp one-checkpoint sweeps "state/wording sensitivity only; checkpoint choice depends on T". | §4 |
| A6 | Stamp every GROWTH and state-eligible-only estimate **Maps-concentrated, claude-code-only**. Prioritise a harness-native `tail` contract for one non-Claude harness before any GROWTH claim touches the 40% caps. | §5 |
| A7 | Never quote a pooled sweep fire rate or pooled state ranking without the state-eligibility column. Replace "`delta_only` 2.18%" with "0/608 state-eligible; 25 empty-state fires". | §3 |
| A8 | Persist the per-batch parse diagnostic sidecar (#109) **before** any further Flash volume; until then Flash rates are MNAR-stamped. | §6 |
| A9 | Add session-level covariates to the meter (tail length, turn count, activity density) so session propensity (ρ=0.61) can be adjusted rather than left as a nuisance. | §2c |

## 8. Open axes (not resolved here)

- Whether TypeSafe zero-fire on the scope/deliverable questions is wording,
  driver conservatism, or quiet corpus. Needs Flash/Luna on the same keys and
  a positive control (a session with a known scope drift).
- Whether the 62% vs 36% near-done mix at the sweep checkpoint is real (§4).
  A direct check is the fixed-schedule reach of the same 13 sessions.
- Session-level confounds behind ρ=0.61 (§2c).
- Whether any non-Claude harness can emit the minimum `tail` contract (#108)
  without hindsight fields.
- The `window_delta_tools` projection mismatch remains unfixed; no negative
  selector exists on that state.
- Labeler independence from the evaluated driver families (§6).
- Which framing wins is untouched, as required. H2 nulls were not computed
  for the 12×9 cut and should be before any card is drawn.

## 9. Non-authorization

Nothing here unlocks Soft Standard, hooks, Pilot, or live Jev. No cell was
re-scored, no label was joined to a response, and no FP/miss figure is
produced or implied.

## Appendix A — recomputation recipe

Run from the repository root at `fc8171e` or later. Assumes
`window_status_join.py` output at `/tmp/wmap.jsonl`.

```bash
B=docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002
python3 tools/interception/window_status_join.py \
  --labels $B/outcome-labels.jsonl \
  --results $B/typesafe-scenario-sweep/results.jsonl --output /tmp/wmap.jsonl
```

```python
import json, collections
B = 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/'
rows = [json.loads(l) for l in open(B + 'typesafe-scenario-sweep/results.jsonl')]
GROW = {'markers_focus', 'phase_hints_focus', 'recent_delta_brief'}
M = [r for r in rows if not (r['state_selection'] in GROW and not r.get('state_fill'))]
G = [r for r in M if r['state_selection'] in GROW]
fire = lambda S: (sum(r['fire'] == 'fire' for r in S), len(S))
pref = {p['scenario_id'] for p in json.load(open(B + 'GROWTH-RANKING.json'))['priority_pairs']}
W = {d['session_id']: d for d in map(json.loads, open('/tmp/wmap.jsonl'))}
exact = {s for s, d in W.items() if d['label_join_eligibility'] == 'label_join_exact'} \
        & {r['session_id'] for r in G}
print(fire(M), fire(G), fire([r for r in G if r['scenario_id'] in pref]))        # 255/13522 103/1632 10/192
print(fire([r for r in G if r['scenario_id'] in pref and r['session_id'] in exact]))  # 6/108
print(collections.Counter((W[s]['window_status'], W[s]['runaway_like']) for s in exact))
print(fire([r for r in M if r['harness'] == 'claude-code']))                      # 192/6272
print(fire([r for r in M if r['state_selection'] == 'delta_only' and r['harness'] == 'claude-code']))  # 0/608
```

The first block lists labels only. The `fire(...)` calls on the exact-label
subset reproduce #111's 6/108 denominator; no response is joined to a label
in this note.
