# Terms — progressive Jev session gates

**Status:** definitions for an offline study. **Confidence: not high.** §§1–10 drafted before first replay; §11 for `shape-signal-panel-v1`; §§12–13 WSM progressive revalidation + validation-phase handoff (Cody design fold 2026-10-01); §14 for `shape-qual-full-maps-v1` (full T≥75 Maps qual + early-signal ≤~120T).

These terms are the contract for [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md), [`TUNING-PLAN.md`](TUNING-PLAN.md), and [`proofs/README.md`](proofs/README.md). If a later harness uses a different meaning, it is a different study.

The resolved cheap-Jev constants stay in `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py`. This file does not change them. It names them when the replay needs a baseline.

## 1. Turn

Three counters exist in the predecessor. This study uses one of them.

| Name | Definition | Where it is used |
|------|------------|------------------|
| `api_turn` | 1-based count of JSONL records with `type=assistant` and `isSidechain` absent or false, in file order. If `message.id` is present, duplicate ids count once, first wins. | **The schedule, the gold labels, and every metric** |
| `post_tool_batch_turn` | Count of Claude `PostToolBatch` events for one `(session_id, agent_id)`. The predecessor hook increments this when the transcript cannot be read. | Not used in offline replay. Documented so a future live hook is not silently substituted |
| `tool_assistant_turn` | An `api_turn` whose message contains a tool call | Reported beside `api_turn` on the manifest. The schedule does not move to this counter |

`PostToolBatch` fires once per model step after a parallel tool batch, not once per assistant message. An assistant message with no tool call does not produce that event, so a live hook counter can be lower than `api_turn`. Maps turn counts are deduped assistant API calls. The replay matches maps.

Sidechain rows are excluded, matching `post_tool_batch_signal.py`. Parent sessions and subagent files are separate transcripts. A worker id is the subagent file identity (`92a48e004519`), not the parent session id.

`T` is the largest `api_turn` in the file. `prefix(c)` is the records that contribute to turns `1..c` plus the non-assistant records that sit before turn `c+1`.

## 2. Checkpoint schedule

A parameter pair `(first_at, interval)` with `first_at` and `interval` positive integers.

```
checkpoints(first_at, interval, T) =
  { first_at + k * interval | k = 0, 1, 2, ... and first_at + k * interval <= T }
```

If `T < first_at`, the set is empty. The worker is `never_gated` under that pair.

**Proposal defaults, unvalidated:** `first_at = 75`, `interval = 15`.

For a transcript with `T = 296` that is turns 75, 90, 105, …, 285 (15 checkpoints). For `T = 154` that is 75, 90, 105, 120, 135, 150 (6 checkpoints). For `T = 70` the default pair fires nothing.

**Sweep grid:** `first_at ∈ {60, 75, 90}`, `interval ∈ {10, 15, 20}`.

**Sensitivity, not a grid axis:** `first_at = 76`, `interval = 15`. Turn 76 is the closed `band_exit` constant. The default of 75 is Cody’s example (the inclusive top of the 50–75 band). One turn should not be treated as the same policy until the sensitivity is computed.

The same analysis runs at every checkpoint. “Same” means the same question id, the same instructions, and the same snapshot *mode*. The snapshot *contents* change because the prefix grew. There is no per-checkpoint prompt rewrite in v0.

### Repeated tests

A transcript that reaches 285 turns is judged at 15 default checkpoints. A transcript that ends at 80 turns is judged once. Under a fixed per-checkpoint error rate, the long transcript has more chances to receive a checkout. That is the mechanism behind “harder to run away,” and it is also a false-early risk. Metrics are stratified by `T` for that reason (§8). The v0 bar does not rise with `k`. A **decaying** `confidence_min` across rounds is Cody’s live-design intent (§12); a rising bar is still an open contrast axis. Neither is in the default grid.

### What 75 is, and what it is not

The in-house band of 50–75 turns and 100–125k context is a cost crossover on cache reads. The field note rates that claim as partial and says no published source names those numbers (`docs/analysis/2026-09-08-workflow-vs-field.md`). Public agent traces that do report step counts, notably SWE-agent, cluster much lower on successes (median 12 steps for GPT-4 on SWE-bench). See [`LITERATURE.md`](LITERATURE.md). `first_at = 75` is a proposal carried forward from the band, not a result of this pack and not a citation.

## 3. Continue, inconclusive, checkout

At checkpoint `c` the Jev choice `checkout_now` is one of:

| Choice | Meaning in this study |
|--------|------------------------|
| `continue` | The prefix supports more work by this worker. The next look, if the transcript reaches it, is `c + interval` |
| `inconclusive` | The snapshot does not support a checkout. The worker is not stopped. Next look is `c + interval` |
| `checkout` | Continuing this worker past `c` is a mistake: hand the remaining work to a fresh worker, or stop. In replay this is a candidate `gate_exit`. It is not a live kill |

`inconclusive` is a judgement that the evidence is thin. It is not a third product action. Parent surfacing and hook `additionalContext` are out of scope (deferred landing). The choice set has no `monitor` value. The resolved `session-progress` choice `monitor` appears only in the legacy baseline, where the sweep maps it to `inconclusive`.

**Decision rule `R(t)`.** Checkout fires at `c` when both hold:

- `checkout_now == checkout`
- `checkout_confidence >= t`

`t` is `confidence_min`. Proposal default `t = 3` on the 0–3 score in §6. Sweep `{2, 3}`.

Scores other than `checkout_confidence` do not fire the rule. A `runaway_pattern` of 3 with choice `continue` does not checkout. Those scores exist so a later table can show whether the choice agrees with the rubric patterns. A firing is flagged `ungrounded_choice` when `runaway_pattern` and `scope_drift` are both in `{0, 1}` and `progress_since_prior` is in `{2, 3}`: the choice says checkout while the pattern scores say little thrash, little drift, and real progress. Low progress is not part of that flag. A progress score of 0 or 1 is evidence on the rubric’s low-progress axis, so a checkout beside it is grounded even if the other two scores are quiet. The flag does not by itself change `gate_exit`.

**`gate_exit(P)`** is the smallest checkpoint at which `R(t)` fires, or null if none does.

**`max_allowed_turns(P)`** is `gate_exit(P)` when that is non-null, otherwise `T`. It is how far the stored transcript would have been allowed to run under `P` in this counterfactual. It is not a number of turns a future hook will permit.

## 4. Fail-open and fail-closed

**Fail-open (the worker policy under test).** A checkpoint that does not fire `R(t)` leaves the counterfactual worker running. The next evaluation is one interval later, not an immediate retry. Non-firing includes:

- choice `continue`
- choice `inconclusive`
- choice `checkout` with `checkout_confidence < t`
- no answer: API error, timeout, dry-run, invalid JSON, or a snapshot that cannot be shrunk under the state guard (§5)

Cody’s “if the check fails, try again 15 turns later” is this policy. “Fails” here means “does not establish checkout.”

Missing answers are recorded as `decision = missing`. They are not recorded as `continue`. A rate that mixes them hides outages inside the false-late number. The sweep reports `missing_rate` separately. For `gate_exit`, missing is fail-open: it does not fire.

**Fail-closed (a contrast policy in the sweep, not the proposal).** `on_uncertain = closed` fires checkout on `inconclusive`, on `checkout` below `t`, and on `missing`. Choice `continue` still does not fire. This policy is how we measure the cost of treating uncertainty as a stop. It is not the design Cody described.

| `on_uncertain` | `continue` | `inconclusive` | `checkout` below `t` | `missing` |
|----------------|------------|----------------|----------------------|-----------|
| `open` (default) | run | run | run | run |
| `closed` | run | checkout | checkout | checkout |

Fail-open is about the counterfactual worker. It is not a licence to treat an unrun study as successful. Absence of a replay is `missing` at the pack level: confidence stays not high.

## 5. Snapshot

Jev never receives the raw JSONL. Worker `92a48e004519` is 12.7MB. The predecessor guard rejects state JSON over **12_000** characters (`jev_signal_schemas._size_guard`). Request blobs in that pack’s tests stay under **16_000** characters. Questions sit outside `state` and count toward the 16_000 figure only.

`STATE_CHAR_LIMIT = 12000`  
`REQUEST_CHAR_SOFT = 16000`

Character length is `len(json.dumps(state, ensure_ascii=False))`, the same function as the guard.

### Modes

| Mode id | Contents | Known risk |
|---------|----------|------------|
| `stats_only` | Cumulative structured stats for `prefix(c)`, plus the brief anchor. No prose tail | Misses drift that has not yet shown up as a repeated path |
| `last_n_turns` | Brief anchor plus the last `N` assistant turns, excerpted | Drops the cumulative re-read and compaction record. At turn 285 the early thrash is gone |
| `last_k_chars` | Brief anchor plus the last `K` characters of concatenated assistant text | Cuts mid-message. No tool histogram |
| `hybrid_v0` | Stats, brief anchor, delta since the previous checkpoint, and a tail of `N` turns | Can still bury a mid-transcript event. Shrink order below can delete the tail |
| `recursive_summary` | A summary of summaries of the prefix | **Not in the v0 grid.** Another model would be inside the state. Wu et al. show the technique and the loss: the judge never sees the source. Revisit only after hybrid is measured |

**Proposal default, unvalidated:** `hybrid_v0` with `N = 8` and `excerpt = 400`.

### Hybrid v0 fields

```
question_id: session-checkout
jev_model: jev-1.13.0
worker_id
checkpoint_turn
prior_checkpoint_turn          # null at the first checkpoint
schedule: {first_at, interval}
brief_anchor                   # see below, cap 500 characters
cumulative:                    # computed on prefix(c) only
  api_turns
  peak_ctx_tokens              # max of input_tokens, cache_read_input_tokens,
                               # cache_creation_input_tokens on assistant usage;
                               # null if usage is absent
  prefix_bytes                 # byte length of the serialized prefix; null if not computed
  tool_histogram               # top 8 tools by count
  reread_paths                 # up to 8 paths read >= 3 times, with counts
  distinct_read_paths          # integer
  compaction_event_count       # integer, 0 if the file has no detectable compaction marker
  assistant_text_chars
delta_since_prior:             # empty object when prior_checkpoint_turn is null
  new_read_paths               # cap 8
  tool_histogram_delta         # top 8
tail:                          # last N assistant turns, oldest first
  [{turn, excerpt, tool_names}]
```

`brief_anchor` is the first user text in the worker file, truncated to 500 characters. If the file has no user text, the field is the string `missing`, and gold judges are told the anchor is missing. Do not invent a design-outcome line.

Tool results and tool-call arguments are not copied into `tail`. `tool_names` only. Excerpts are assistant visible text. Secrets are redacted with the same patterns as `tools/transcript/lib/snapshot.py` before truncation.

### Why this shape is the one to test first

Long-context models use the start and the end of a context more reliably than the middle (Liu et al., TACL 2024; [`LITERATURE.md`](LITERATURE.md)). The brief anchor is placed first so the original task is in the primacy position. The tail is placed last so the latest work is in the recency position. Cumulative counts are structured fields, not a prose block stuffed between them. That is a hypothesis about judge behaviour, tested as H2. It is not a finding.

Maps already shows why stats alone are attractive and incomplete. `92a48e004519` has six paths re-read at least three times, about sixty compact-ish events, and a handful of sleep/poll bash calls. A histogram can represent the re-reads and the compactions. It cannot say whether the latest turn is still the brief. The tail is there for that sentence, and it is small because of the guard.

### Shrink order

When hybrid state exceeds 12_000 characters, apply in order and stop at the first version that fits:

1. Drop tail turns from the oldest of the window until `N = 4`, then until the tail is empty.
2. Cut remaining excerpts from 400 to 200 characters.
3. Replace `reread_paths` entries with `{count_only: <n>}` (no path strings).
4. Drop `delta_since_prior`.
5. If it still does not fit, mark the checkpoint `missing` with reason `state_over_budget`. Fail-open. Do not send the oversize state.

Record `shrink_steps` on the cache row. A default that often reaches step 5 is not a usable default, even if some other mode looks good. That check is stage 2 of the proof plan and does not need a Jev call.

### Sweep of snapshot parameters

| Mode | Parameter values |
|------|------------------|
| `stats_only` | none |
| `last_n_turns` | `N ∈ {4, 8, 16}`, excerpt 400 |
| `last_k_chars` | `K ∈ {2000, 4000, 8000}` |
| `hybrid_v0` | `N ∈ {4, 8, 16}` × excerpt `{200, 400}` |

Thirteen snapshot cells. The schedule does not multiply Jev calls: the cache key is `(worker, checkpoint_turn, mode, mode_params, question_set)`. Confidence and fail-open are applied after the call.

### Judge bundle is larger than Jev state on purpose

Gold judges do not see the raw file either, and they are not held to 12_000 characters. Their bundle is specified in [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) and capped at **60_000** characters so models with different windows are shown the same bytes. The gap between that bundle and the Jev state is a measured quantity (`bundle_minus_state_chars`, and H2). Using the Jev state as the judge’s only view would make the gold depend on the instrument being tested.

## 6. Question set v0

Pin `jev-1.13.0`. Question id **`session-checkout`**. Do not add these questions to the resolved `session-progress` builder.

Scores use four criteria. In this repo a score of that shape is read as an integer **0–3** (`workflow_alignment` in `tools/transcript/lib/jev_client.py`; FINDINGS 2026-09-30). Criterion index 0 is score 0.

Polarity differs by question. Implementers must not treat “higher” as “checkout” for every field.

| Id | Type | Higher means | Feeds `R(t)` |
|----|------|--------------|--------------|
| `runaway_pattern` | Score 0–3 | More thrash | No. Diagnostic |
| `progress_since_prior` | Score 0–3 | More checkable progress | No. Diagnostic |
| `scope_drift` | Score 0–3 | More drift off the brief anchor | No. Diagnostic |
| `checkout_now` | Choice | — | Yes, must be `checkout` |
| `checkout_confidence` | Score 0–3 | More sure of the choice | Yes, only when the choice is `checkout` |

### Instructions and criteria

`runaway_pattern`

> On this prefix snapshot, how strong is repeated thrash (re-reading the same paths, polling or sleeping, compaction churn) relative to new work?

| Score | Criterion |
|-------|-----------|
| 0 | No repeated thrash in the snapshot |
| 1 | A small repeat or stall that still has a next step |
| 2 | Clear re-reads, polls, or compaction churn, with weak new output |
| 3 | Thrash is the dominant pattern in the snapshot |

`progress_since_prior`

> Since `prior_checkpoint_turn` (or since the start, when that field is null), how much checkable progress does the snapshot show against `brief_anchor`?

| Score | Criterion |
|-------|-----------|
| 0 | No new artifact, edit, test outcome, or narrowing decision |
| 1 | Motion without a checkable step (more reads, a restated plan) |
| 2 | One checkable step: an edit, a test result, or a decision that narrows the brief |
| 3 | Clear delivery against the brief anchor |

`scope_drift`

> How far is the latest work from `brief_anchor`?

| Score | Criterion |
|-------|-----------|
| 0 | The latest work matches the brief anchor |
| 1 | Adjacent exploration that still serves the anchor |
| 2 | Substantial work on a different task |
| 3 | The latest work is a different task from the anchor |

`checkout_now`

> Should this worker be checked out now (stop continuing this worker; hand off or end the run)? Judge only the snapshot. Later turns are not in the snapshot. This is a counterfactual label for offline tuning.

| Choice | Criterion |
|--------|-----------|
| `continue` | The worker should keep going until the next checkpoint |
| `inconclusive` | The snapshot does not justify checkout |
| `checkout` | Continuing past this checkpoint is a mistake |

`checkout_confidence`

> How sure are you of `checkout_now`? Score the confidence of that choice, not the severity of the task.

| Score | Criterion |
|-------|-----------|
| 0 | A guess |
| 1 | Weak; a careful reader could easily disagree |
| 2 | Moderate; a careful reader might disagree |
| 3 | The snapshot would convince a careful reader |

### Why these five, and what stays out

The choice is the decision. The three pattern scores match the rubric’s runaway, low-progress, and drift axes so the sweep can see a choice that the patterns do not support. Context thrash is scored inside `runaway_pattern` (compaction and re-read), not as a fourth score, to keep the request small. A separate thrash score can be added only if H3 fails and the error table shows checkout misses that the rubric called thrash while `runaway_pattern` stayed low.

`confidence_min = 3` means “fire only when Jev marks the top of its own 0–3 scale.” That phrase is not Cody’s design-level “high confidence.” A cell can require score 3 and the design can still be unvalidated.

The resolved pair `progress_vs_scope` plus `handoff_recommended` (`continue | monitor | handoff_soon`) is baseline `Y_legacy`. Mapping for the decision rule: `handoff_soon → checkout`, `monitor → inconclusive`, `continue → continue`. `Y_legacy` has no confidence score; `R(t)` treats `handoff_soon` as firing at every `t`. That asymmetry is intentional and must be written on the results row so a legacy win is not read as a stricter test.

### Question-set cells

| Cell | Questions |
|------|-----------|
| `Y_full` | All five above. **Proposal default** |
| `Y_choice_only` | `checkout_now`, `checkout_confidence` |
| `Y_legacy` | Resolved `session-progress` pair, same snapshot |

### Size budget for the questions

The five instruction blocks above are short on purpose. The proof’s schema stage records the request length. A `Y_full` request over 16_000 characters fails the soft guard for that snapshot cell. The fix is a smaller snapshot, not a cut to the criteria, unless the criteria themselves are what overflowed.

## 7. Gold exit

`gold_exit_turn` is the first `api_turn` at which continuing the worker was a mistake, under the aggregation rule, or null if the panel does not establish that.

**Primary gold is prefix-causal.** A judge asked about turn `c` sees `prefix(c)` only, in the judge bundle. The judge does not see turns after `c`. Process labels and outcome labels answer different questions (Lightman et al.; [`LITERATURE.md`](LITERATURE.md)). Tuning Jev to a judge who has already read the ending measures hindsight.

**Labeled turns.** Every 15 assistant turns from 60 through `T`: 60, 75, 90, … as long as the turn is `<= T`. This grid includes every default checkpoint and every `first_at` in `{60, 75, 90}`. Checkpoints the grid does not hit (for example turn 70 when `interval = 10`, or turn 80 when `interval = 20`) inherit the latest labeled turn `<=` that checkpoint. The results row carries `gold_resolution = 15` so a one-interval miss is not over-read. Denser labels (every 5 turns) are a sensitivity on the two smoking guns only, run after the 15-turn gold exists.

**Hindsight gold is secondary.** One extra call per judge per worker sees the whole bundle of the full transcript and names a first checkout turn or null. Store as `gold_exit_turn_hindsight`. Do not select parameters against it. Report the signed gap `hindsight − primary` so the pack can see how much the ending moves the label.

### Panel

Independent sessions. No judge sees another judge’s answer, rationale, or the Jev cache.

| Seat | Model |
|------|--------|
| Required | Grok 4.7 high |
| Required | Claude Sonnet (the current Sonnet Cody has on the run) |
| Required | Claude Opus (the current Opus on the run) |
| When the API is available | Composer |

Record the exact model id on every label row. “Current” is not stable across months.

A worker’s primary gold is computed only when at least **three** judges returned a label at each labeled turn used in the aggregate. Fewer than three: `panel = underpowered`, excluded from the primary metric, included in a sensitivity table. Do not impute a missing judge.

### Aggregation

**Default `A0`: earliest unanimous checkout.** Walk labeled turns in order. `gold_exit_turn` is the first turn at which every judge who returned a label at that turn said `checkout`. If there is no such turn, `gold_exit_turn` is null.

`A0` is conservative. Disagreement delays the gold exit, which makes false early harder to avoid and false late easier to incur. That matches an advisory gate that should not be tuned to a single model’s impatience. It is still an untested choice.

Compute these alternatives. Do not pick a winner until the agreement table exists. Do not tune the Jev grid to more than one gold rule in the same pass; the pre-registered rule is `A0`. The others are robustness columns.

| Id | Rule |
|----|------|
| `A1` | Earliest majority. Majority is more than half the returned labels at that turn, rounding up (2 of 3, 3 of 4) |
| `A2` | Median of the per-judge first-checkout turns. A judge who never checks out contributes no number. If fewer than half the panel have a finite turn, the result is null. If the median falls off the labeled grid, round **up** to the next labeled turn (later exit) |
| `A3` | Dawid–Skene latent label per prefix, then the earliest turn whose latent class is checkout. **Inapplicable** when the corpus has fewer than 30 workers. The model is not identified on a handful of transcripts |
| `A4` | Median of hindsight turns, same null rule as `A2`. Secondary only |

### Agreement, before any Jev interpretation

On the binary label `{not_yet, checkout}` at each prefix:

- Krippendorff’s alpha across the panel (handles a missing Composer seat).
- Pairwise raw agreement and Cohen’s kappa, as a diagnostic when alpha is disputed.
- Per worker, the spread `max(judge_first_checkout) − min(judge_first_checkout)` among judges who named a turn. A judge who said null is included in a separate `never_checkout` count, not as turn 0.

**Pre-registered floor:** alpha **≥ 0.40** on the pooled prefix labels. Landis and Koch (Biometrics, 1977) call 0.21–0.40 fair and 0.41–0.60 moderate. The floor is the bottom of the moderate band. It is a stop rule, not a claim that 0.40 is good. Below the floor: revise the rubric or the bundle, re-label, and do not sweep Jev into a recommendation. Hypothesis H5 states this gate.

Alpha among language models is not agreement with a person. Zheng et al. measured LLM–human agreement on chat preferences. This pack does not have a human rater in the primary panel. Say that in the lock memo. A human audit of the smoking-gun prefixes is desirable and is not required to *compute* the metrics. It is required before anyone describes the gold as human-valid.

## 8. Metrics

For worker `w` with length `T` and parameter cell `P` (schedule, snapshot, question set, `confidence_min`, `on_uncertain`, gold rule):

| Symbol | Definition |
|--------|------------|
| `gate_exit` | §3, or null |
| `gold_exit` | §7 under the chosen rule, or null |
| `overshoot` | `gate_exit − gold_exit` when both are non-null. Positive: the gate was later than gold. Negative: the gate was earlier |
| `false_early` | True when `gate_exit` is non-null and (`gold_exit` is null or `gate_exit < gold_exit`) |
| `false_late` | True when `gold_exit` is non-null and (`gate_exit` is null or `gate_exit > gold_exit`) |
| `on_time` | Both non-null and equal |
| `within_one_interval` | Both non-null and `abs(overshoot) <= interval` of `P` |
| `max_allowed_turns` | §3 |
| `missing_rate` | Share of checkpoints in `P`’s schedule with `decision = missing` |

`on_time` at 15-turn resolution is a harsh bar. `within_one_interval` is the coarser bar. Report both. Do not replace overshoot with a single accuracy.

**Corpus aggregates,** on workers with `T >= 75` and `panel` powered, under gold rule `A0`:

- `false_early_rate`, `false_late_rate` (means of the booleans)
- median `overshoot` on the subset where both exits exist
- median `max_allowed_turns`
- the same four numbers on the smoking-gun slice alone
- the same four numbers in bins `T < 100`, `100 <= T <= 150`, `T > 150`

The length bins are how repeated testing shows up. A cell that never fires has `false_early_rate = 0` and `false_late_rate = 1` on every worker with a gold exit. Minimising false early alone selects that cell. The lock rule in [`TUNING-PLAN.md`](TUNING-PLAN.md) therefore constrains both.

**Single-shot baseline `B`.** The predecessor’s first `jev_eligible` turn: the first `api_turn` at which the closed rule is true (`handoff` and (`api_turns >= 85` or peak `>= 128_000` or transcript bytes `>= 3MiB`)), using peak and bytes as of that prefix. One `Y_legacy` call at that turn. If it maps to checkout, `gate_exit_B` is that turn; otherwise null. `B` does not look again. H1 compares progressive cells to `B`.

**Turn-cap baseline `C`.** `gate_exit_C = first_at` when `T >= first_at`, else null, with no Jev call. This is the “stop at the first checkpoint no matter what the snapshot says” policy. If `C` matches gold as well as Jev, the questions are not earning their keep. Report `C` in every results table.

### Worked counterfactuals (arithmetic, not results)

These rows fix the metric definitions. They are not measurements of Jev.

| Worker | `T` | Imagined `gold_exit` | Imagined `gate_exit` | `overshoot` | `false_early` | `false_late` | `max_allowed_turns` |
|--------|-----|----------------------|----------------------|-------------|---------------|--------------|---------------------|
| `92a48e004519` | 296 | 105 | 105 | 0 | no | no | 105 |
| `92a48e004519` | 296 | 105 | 285 | +180 | no | yes | 285 |
| `92a48e004519` | 296 | 105 | null | — | no | yes | 296 |
| `92a48e004519` | 296 | null | 75 | — | yes | no | 75 |
| `bb6165018de0` | 154 | 150 | 135 | −15 | yes | no | 135 |
| `6c87c96bd9bb` | 70 | — | not in corpus | — | — | — | — |

The negative control is a separate assertion: under every cell with `first_at >= 75`, `checkpoints` for `T = 70` is empty and `max_allowed_turns = 70`. A harness that emits a gate exit for that file has the wrong turn counter.

## 9. Parameter cell

`P` is the tuple:

```
(first_at, interval, snapshot_mode, snapshot_params,
 question_set, confidence_min, on_uncertain, gold_rule)
```

**Proposal cell `P0`, unvalidated:**

```
(75, 15, hybrid_v0, {N: 8, excerpt: 400},
 Y_full, 3, open, A0)
```

`P0` is what the hypotheses name as the proposed design. Beating `B` at `P0` is H1’s primary comparison. The grid exists because `P0` is expected to move if the numbers say so. Moving it inside this document, before the numbers, is not allowed.

## 11. Shape-signal vocabulary (`shape-signal-panel-v1`)

Added 2026-10-01 for experiment **`shape-signal-panel-v1`**. These terms do **not** replace `gold_exit_turn` under `A0` (§7). They are the seat contract when the study asks for shape and early-signal agreement instead of three-model exact exit agreement.

**Gold protocol note.** Unanimous A0 / “≥ 2 non-null A0” is **not** the hard gate for this experiment. Multi-model agreement on **early signals**, **shape**, and **inflections** is worth more than exact exit-turn match. Exit-turn spread across seats is a **secondary metric**, not a hard fail.

| Term | Definition |
|------|------------|
| `late_pivot` | Session shape: the worker shows usable progress for a long stretch, then a clear change of fortune (stall, thrash, drift, or brief abandonment) after which continuing is a mistake. The recommended exit is near that **pivot**, not at the first minor wobble. |
| `early_thrash` | Session shape: repeated thrash, low progress, or runaway wait/poll is already the dominant pattern **early** (often by the first or second `75:15` checkpoint). Extending the run does not recover a productive trajectory. |
| `early_signal` | A concrete, **turn-anchored** observation in `prefix(c)` (tool histogram skew, re-read loop, compaction surge, sleep/poll burst, brief abandonment in the tail, frozen progress) that foreshadows the eventual shape/outcome. Must cite turns ≤ `c` present in the judge pack. **Hard window (Cody / WSM):** predictive `early_signals` MUST fall in the **first ~120 turns**. Anything later is **outcome**, not early foreshadowing — do not credit mid/late-run symptoms as early signals (see §14). |
| `inflection` | A turn **range** (e.g. 120–150) where the trajectory’s character changes: what was true before the range is no longer true after. Seats name the range **and** what changed (not only a single turn number). |
| `recommended_exit` | The seat’s best checkout turn under the shape rule: for `late_pivot`, near the pivot; for `early_thrash`, at the **first clear thrash** checkpoint where continuing is already a mistake. May differ across models; spread is secondary. |
| `earliness` | How early `recommended_exit` is relative to an ideal: for `late_pivot`, distance before/after the pivot; for `early_thrash`, distance after the first clear thrash. Report qualitatively (too early / on time / too late) with turn anchors when possible. |

### Per-seat questions (shape-signal panel)

Each seat, given hybrid_v0 packs for a worker, answers:

1. **Shape:** `late_pivot` or `early_thrash` (or `unclear` with why).
2. **Why T is large:** what kept the transcript long (productive work, thrash, wait/poll, census, compaction churn, …), turn-anchored.
3. **Inflection points:** turn ranges + what changed.
4. **Early signals:** concrete foreshadowing of the outcome, turn-anchored, only from evidence ≤ each cited checkpoint **and ≤ ~120T** (later symptoms are outcome, not early).
5. **Recommended exit + earliness:** exit turn under the shape rule above, and earliness vs ideal.

Do not require three seats to name the same exit turn. Prefer agreement notes on (1), (3), and (4).

## 12. Progressive revalidation and decaying confidence bar (design — not in P0 grid)

**Status:** Cody design fold 2026-10-01. **Workflow System Manager** orchestration intent only. **Not shipped.** Does not change `P0`, the sweep grid, or hook behaviour until a follow-on experiment clears (see [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) **`progressive-decay-bar-v1`**).

Each successive ~15-turn revalidation round (same `interval` as §2) gives the judge more prefix to **accumulate stop-signals** — pattern scores in §6, plus shape and early-signal agreement when §11 seats exist. Across rounds the policy **may lower `confidence_min`** required for `R(t)` to fire: a **decaying confidence bar**.

Two exit paths at checkpoint `c` with bar `t_k` on round index `k` (0 at the first scheduled checkpoint that runs the test):

1. **Leap:** `checkout_now == checkout` with `checkout_confidence >= t_k` when the snapshot (and, when available, multi-model shape/signal notes) support **near-done** — high agreement on early signals, shape, or inflections, not merely one noisy score. Clears the **current** bar early without waiting for weaker signals to stack.
2. **Accumulate:** Checkpoints where stop-signals keep appearing but confidence stays below `t_k`. Each round lowers `t_k` (decay schedule is harness work; pre-register before any live run). Guarantees counterfactual exit within a few rounds if stop-signals persist, without a turn cap that bypasses Jev.

The offline sweep still uses fixed `confidence_min = 3` (§6, §9). §12 is the intended live policy once shape-signal agreement lands; harness seats stay separate from WSM docs. Agreement SUMMARY for `shape-signal-panel-v1` is now at [`proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md) (ca977 unanimous early_thrash; 92a48e shape split with ~90 thrash signals). **Still not shipped** — no `--call-jev`, no hook behaviour from this fold alone.

**Gold and agreement weight:** Multi-model agreement on **early signals**, **shape**, and **inflections** (§11) matters more than exact exit-turn match when interpreting leap vs accumulate or tuning decay. Exit-turn spread across seats is **secondary**, not a hard fail — same weighting as `shape-signal-panel-v1`.

## 13. Validation-phase handoff (design — not shipped)

**Status:** Cody design fold 2026-10-01. WSM-owned. No hook bytes, no `--call-jev`, in this fold.

At **progressive validation checks** — nominally ~**50**, **60**, and **75** `api_turn`, then continuing on the §2 schedule — ask Jev (or an equivalent soft judge): is the agent **already in validation**?

**Validation** means the worker is in a reactive read/fix/test loop (CI, lint, failing tests) rather than forward build or delivery against `brief_anchor`.

| Answer | Preferred action |
|--------|------------------|
| **Not** in validation | **Steer**; do not hard-exit the builder. Prefer Claude/Cursor hook `additionalContext` (or equivalent parent steer): stop before running tests; wrap build work; hand validation to a **new agent**. Rationale: validation handoff is an ideal **inflection** (§11); build context decays once the loop is reactive read/fix. |
| **Already** in validation | Use §12 **leap** / **accumulate** and the decaying bar. Do **not** invent a third hard-exit without replay evidence. |

The 50/60/75 anchors are for **phase detection and steer** only. They do not replace `session-checkout` gold labels or the P0 `(75, 15)` grid until measured separately. Paired hold: [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) **`validation-handoff-steer-v1`**.


## 14. Full Maps qualitative shape (`shape-qual-full-maps-v1`)

Added 2026-10-01 for experiment **`shape-qual-full-maps-v1`**. Expands qualitative shape labeling from the 7-worker `shape-signal-panel-v1` shortlist to **ALL** open-pajero-maps Claude workers with **T ≥ 75** (inventory **n = 34**; no excludes for already labeled). Vocabulary in §11 still applies; this section adds the full-corpus seat contract and the early-signal window.

**Early-signal hard window (Cody / WSM constraint):**

| Rule | Detail |
|------|--------|
| Window | `early_signals` MUST be evidenced in the **first ~120 turns** (`api_turn` ≤ ~120) |
| Later | Observations after ~120T are **outcome / mid-late symptoms**, not predictive early foreshadowing |
| Pack note | Judge packs may include checkpoints past 120 (schedule `75:15` through T). Seats may describe phases and narrative shape across the full prefix, but **must not** list post-~120 symptoms under `early_signals` |

**Per-seat questions (qualitative — supersede shortlist-only prompts for this experiment):**

1. **Narrative shape:** How the run looked (free prose + optional §11 labels `late_pivot` / `early_thrash` / `unclear`).
2. **Phases contained:** Ordered phases (e.g. productive build → validation pivot; early thrash; wait/implement; census; sleep/poll). Turn-anchor each phase.
3. **Early signals (≤ ~120T):** Turn-anchored foreshadowing of how it played out; **only** evidence from turns ≤ ~120. Do not credit mid/late-run symptoms as early.

**Secondary (report, not optimize / not hard fail):** recommended exit turn and earliness. Do **not** optimize for `A0` or exit-turn agreement.

**Agreement weights:** shared **early signals (≤~120)** + **phases / narrative shape** first ≫ exact exit turn.

**Seats:** Composer / Sonnet / Grok. **No** `--call-jev`. Hold Jev behaviour ship.

**Pack schema note:** hybrid_v0 (`N=8`, excerpt 400) omit-state safe packs under [`proofs/validated/gold/packs/`](proofs/validated/gold/packs/). Combined inventory [`INVENTORY-shape-qual-full-maps-v1-20261001-214046.json`](proofs/validated/gold/packs/INVENTORY-shape-qual-full-maps-v1-20261001-214046.json). Reuse prior packs where present; gap packs from run `20261001-214046`. `pack_meta.early_signal_window` on combined rows restates the ≤~120 rule for seat scaffolding.

## 10. Out of scope for these terms

- The bytes of a Claude hook response, including `additionalContext`.
- Any message the parent orchestrator would display.
- `assert_phase`, `decision_source`, and `outcome-evidence`.
- Classify labels as a score or as a filter.
- A live counter stored under `~/.cache/workflow-plugin/signal-state/`.
- Retuning `BAND_EXIT_TURNS`, `HANDOFF_SIGNAL_TURNS`, or the context and byte thresholds.
