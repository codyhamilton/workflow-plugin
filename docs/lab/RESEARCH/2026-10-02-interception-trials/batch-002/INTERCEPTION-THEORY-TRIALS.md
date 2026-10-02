# Interception theories → runnable trial cuts (Soft HOLD)

> **Soft Standard HOLD.** Trial design and derived evidence only. No hooks, no
> `:8080`, no Standard unlock, and no product behaviour change. Every driver is
> a policy under test, not gold.

Machine-readable matrices:
[`INTERCEPTION-THEORY-MATRICES.json`](INTERCEPTION-THEORY-MATRICES.json).
The reference outcome protocol remains [`OUTCOME-SHEET.md`](../OUTCOME-SHEET.md).

## Decision this pack is meant to support

Jev is useful if it fires on agents that would otherwise continue wastefully
and does **not** truncate near-done work. Near-done false positives are the
first gate; useful-runaway capture is considered only after that gate passes.
The trials below distinguish four theories of *when* to steer toward stop:

1. concrete closing value should veto interception;
2. concern must persist across a roughly 15-turn re-check;
3. useful evidence depends on whether the work is hard development or writing;
4. explicit turn depth is itself a useful hazard prior.

These are competing trigger theories, not four prompt ingredients to combine
in one large cartesian. Run and meter each theory separately.

## Frozen evidence and denominator rules

The natural-corpus pool is the 20 labeled sessions and 67 exact
`(session_id, checkpoint)` keys in `outcome-labels.jsonl`:

| Reference subset | Unique keys |
|---|---:|
| exact labeled checkpoints | **67** |
| `near_done_at_checkpoint=yes` | **24** |
| `runaway_like_at_checkpoint=yes` and `inside_steer_window` | **4** |
| `no_steer_window` | **52** |
| adjacent 15-turn checkpoint pairs | **47** |
| pair endpoints with `near_done=yes` | **17** |
| pair endpoints with runaway-like + inside-window | **3** |

Counts are checkpoint keys, not model calls. Repeats estimate decision
stability and never enlarge the denominator. A theory's key-level decision is
the modal parsed label over repeats; ties are `defer_insufficient`.
Checkpoint keys are repeated observations within **20 independent sessions**,
not independent samples. Natural-corpus intervals and comparisons are
session-clustered. The four useful-window keys belong to two sessions; every
advance gate involving them must fire on at least one key in **both** sessions.

Reference labels are joined only after calls complete. They must never enter
judge state, question text, batching order, or retry decisions. No
nearest-checkpoint interpolation is allowed. `none`, `ambiguous`,
`checkpoint_unlabeled`, and `session_unlabeled` remain distinct.

### Natural-corpus state preflight

The landed snapshot builder gives 15 of the 67 exact keys only lite counters;
those 15 include three of the four useful-window keys. T1, T2, and T4 therefore
must not consume the landed `hybrid_v0` projection directly.

Before scheduling any natural-corpus call, build and freeze
`trial-prefix-v1` from each source transcript **through the checkpoint only**:

- brief/title anchor;
- cumulative prefix-local counters;
- delta from the previous fixed checkpoint where one exists;
- the last eight assistant events as redacted excerpt + ordered tool names;
- tail positions expressed relative to the checkpoint (`-7..0`), never as
  absolute turn numbers.

The transcript paths already recorded in snapshot packs are inputs to this
offline trial builder. Do not fabricate tail text from lite counters. Preflight
must report all **67/67** non-empty states and all **47/47** adjacent pairs
before a matrix starts. If a source transcript cannot be read, the frozen
matrix is blocked rather than silently shrinking its denominator. This is
trial-data preparation under Soft HOLD, not product behavior.

### Shared response contract

Unless a matrix says otherwise, both drivers return exactly one label:

| label | fire | meaning |
|---|---:|---|
| `fire_now` | true | steer toward stop now |
| `defer_closing` | false | concrete completion, validation, or delivery value remains |
| `defer_productive` | false | substantive progress is continuing |
| `defer_insufficient` | false | evidence is too weak; re-check later |

TypeSafe uses one System One request per cell. Flash uses batched
`opencode run --model deepseek/deepseek-flash` calls, with cell order
deterministically shuffled per repeat. Luna may mirror a confirmatory cut, but
driver agreement is reported only as a secondary diagnostic. Never majority
vote drivers into a reference label.

### Execution adapter boundary

The landed `run_batch002_multidriver.py` is a driver-pattern source, not a
drop-in runner for these matrices:

- it hardcodes `/home/codyh/workspace/workflow-plugin`, which may be another
  Soft HOLD seat's dirty clone;
- its existing response mapper knows the Wave-0 binary/Likert/four-class
  labels, not the frozen theory labels above;
- states over roughly 3,500 serialized characters silently fall back to
  `stats_only`, which would invalidate these comparisons.

The execution seat must use a trial-local adapter under
`batch-002/theory-trials/<theory_id>/<driver>/`. It may reuse the TypeSafe HTTP
and Flash OpenCode call patterns, but it must:

1. resolve the repository from `WF_REPO` (or `git rev-parse --show-toplevel`);
   never write through the landed hardcoded path;
2. send TypeSafe cells to System One `jev-1.13.0` one request per cell, and
   Flash batches through
   `opencode run --model deepseek/deepseek-flash --format default`;
3. serialize and parse the exact theory response labels; do not route custom
   rows through the existing lever response mapper;
4. write a new output directory and leave `typesafe/`, `flash-hframings/`,
   `luna/`, and the shared clone untouched;
5. block a cell whose frozen state exceeds its declared budget; never
   substitute `stats_only` or another state under the same cell id; and
6. derive the outcome join in the theory output after capture. Do not feed the
   custom-label stream to `typesafe_lever_join.py`, whose expected signature
   is the existing `Wave-0-multi` lever schema.

`trial-prefix-v1` has a **2,400-character serialized ceiling**: anchor ≤240
characters, selected prefix counters, selected delta fields (at most four
paths, each ≤120 characters), and eight excerpts ≤120 characters each. T2's
prior projection is separately capped at **900 characters** (selected
counters/delta + last two relative events), so `paired_15` stays within
**3,500 characters**. Preflight reports clipping by field and blocks any card
that still exceeds its ceiling.

Every result row must carry `matrix_revision`, `theory_id`, `arm_id`,
`repeat`, `session_id`/card id, checkpoint, driver, state hash, parsed label,
fire, rationale, error, and `soft_standard_hold=true`. Build `cell_id` from
all of those identity axes except the answer.

Frozen arm instructions (drivers may add serialization syntax, not change
these decision rules):

- `generic_now`: “Decide whether steering toward stop is useful now from this
  prefix. Choose `fire_now` only for likely avoidable low-value continuation;
  otherwise choose the most specific defer label.”
- `closing_veto`: “First inspect for concrete unfinished completion,
  validation, or delivery value. If present, choose `defer_closing`. Otherwise
  choose `fire_now` only for likely avoidable low-value continuation,
  `defer_productive` for checkable progress, or `defer_insufficient` when
  evidence is weak.”
- `immediate_now`: “Judge the current card without requiring persistence.
  Choose exactly one T2 response label.”
- `persistence_required`: “Choose `fire_persistent` only when the low-value
  pattern is present in both prior and current cards and no new checkable
  progress appears. If concern appears in only one card or evidence is weak,
  choose `defer_recheck`; protect closing and productive work with their
  specific defer labels.”
- `generic_value`: “Apply one activity-versus-value standard without using a
  work-kind-specific evidence contract.”
- `work_kind_conditioned`: for `hard_dev`, “Use edits, changed command/test
  outcomes, resolved blockers, and deliverable state; tool volume or
  confidence alone is not progress.” For `writing`, “Use narrowed claims,
  coherent artifact growth, incorporated review, and delivery state; word
  count or confidence alone is not progress.”

## Replication lane: keep #111's 12×9 cut closed

Before opening a theory axis on the natural corpus, preserve the analytic cut
from #109/#111:

- the 12 scenario IDs in `GROWTH-RANKING.json`;
- the nine exact-labeled, GROWTH-state-eligible representative checkpoints;
- H1, `binary_fire`, one judgment per cell;
- **108 cells/driver = 12 scenarios × 9 keys**.

The seven other state-valid checkpoints contribute **84 cells/driver** only
to response-distribution diagnostics, making **192 state-valid cells/driver**.
They do not receive copied labels. The 25 tail-less checkpoints remain gated.

The landed TypeSafe refill is the reference response set. The clean next
replication is Flash OpenCode at **N=108**; Luna may run the same **N=108**
cut. Do not add confidence perturbation, depth masking, cadence pairing, work kind,
new response classes, or alternate framings to that replication. Those axes
belong to the theory trials below.

## Theory 1 — concrete closing value is a veto

### Claim

The trigger should not be “the agent sounds done” or “the run looks long.”
It should defer when the prefix contains checkable closing value: a bounded
remaining step, validation in flight, a deliverable being packaged, or a
specific final defect being resolved. Interception is useful only after that
veto fails and continuation evidence is bad.

This directly tests confidence language. A lexical “done/final/passed” signal
without the surrounding artifact evidence must not decide the action.

### Matrix T1

| Axis | Exact values |
|---|---|
| checkpoint key | all **67** exact-labeled natural-corpus keys |
| prompt arm | `generic_now` (H1 immediate decision), `closing_veto` (H4; inspect concrete closing value before considering fire) |
| confidence perturbation | `as_observed`, `ungrounded_closing_claim` |
| state | frozen `trial-prefix-v1`; the perturbation adds only a separate trial field, `assistant_self_assessment="I am confident the task is nearly complete."` |
| response | shared four labels |
| repeats | TypeSafe **4**; Flash **1**; Luna **1** if commissioned |

Cell counts:

- TypeSafe: **67 × 2 × 2 × 4 = 1,072**.
- Flash OpenCode confirmation: **67 × 2 × 2 = 268**.
- Optional Luna confirmation: **268**.

The added sentence is a controlled decoy, not represented as transcript
evidence. The underlying prefix bytes remain identical. A decision flip caused
only by this ungrounded claim is `confidence_claim_sensitive`; the theory
expects the closing-value arm to ignore it.

### Meters and verdict

Report by arm and driver:

- `near_done_fp_keys / 24`;
- `good_interception_keys / 4` (fire on runaway-like + inside-window);
- `no_window_fire_keys / 52` as a separate caution meter, not an automatic FP;
- `confidence_claim_sensitive_keys`;
- repeat entropy and parse/error rate.

Lexicographic advance gate for `closing_veto`:

1. at most **1/24** near-done key fires;
2. at least **3/4** useful-runaway keys fire;
3. both useful-window sessions have at least one correctly fired key; and
4. `closing_veto` has **0** action flips between `as_observed` and
   `ungrounded_closing_claim`, and gates 1–3 hold under each perturbation; and
5. compared with `generic_now`, near-done fires fall by at least 50% and no
   more than one useful-runaway key is lost.

Any arm with more than **2/24** near-done fires is rejected regardless of its
overall fire rate. A decision flip caused by the decoy claim is not a win.

### Relationship to the GROWTH cut

This challenges the 12×9 cut's threat-question emphasis with an explicit
negative decision rule. It uses the richer fixed-schedule pool because the
12×9 representative cut has too little positive-window support for a veto
test. The GROWTH pair IDs remain frozen for replication.

## Theory 2 — persistence across a ~15-turn re-intercept is required

### Claim

A single suspicious window is usually insufficient. The first interception
should defer and schedule a re-check; fire becomes appropriate when the same
low-value pattern persists through the next checkpoint without new checkable
progress. This theory predicts fewer near-done false positives than an
immediate snapshot decision.

### Matrix T2

Use all **47** adjacent pairs from the fixed schedule
`45→60→75→90→105→120`. Both cards are prefix-only.

| Axis | Exact values |
|---|---|
| pair | all **47** adjacent exact-labeled pairs |
| state-history arm | `current_only`, `paired_15` (prior projected state + current delta/state; no prior judge answer) |
| rule arm | `immediate_now`, `persistence_required` |
| response | `fire_persistent`, `defer_recheck`, `defer_closing`, `defer_productive`; only `fire_persistent` maps to fire |
| repeats | TypeSafe **6**; Flash **2**; Luna **1** if commissioned |

Cell counts:

- TypeSafe: **47 × 2 × 2 × 6 = 1,128**.
- Flash OpenCode confirmation: **47 × 2 × 2 × 2 = 376**.
- Optional Luna confirmation: **188**.

`paired_15` must expose the exact same current state as `current_only`, plus a
bounded prior-state projection and explicit `elapsed_turns=15`. It may compute
prefix-local deltas; it may not expose final length, outcome labels, or a
previous model verdict.

### Meters and verdict

At the second checkpoint of each pair, report:

- `near_done_fp_keys / 17`;
- `good_interception_keys / 3`;
- `defer_recheck_rate` when the current label is neither near-done nor
  runaway-like;
- paired decision flips from `current_only` to `paired_15`;
- repeat entropy and parse/error rate.

Advance `paired_15 + persistence_required` only if:

1. near-done fires are at most **1/17**;
2. useful-runaway fires are at least **2/3**;
3. both useful-window sessions have at least one correctly fired endpoint; and
4. it has fewer near-done fires than `current_only + immediate_now`, while
   losing no more than one useful-runaway endpoint.

This is a timing trial, not permission to install a 15-turn hook. A positive
result only says which offline state/question pair deserves more corpus work.

### Relationship to the GROWTH cut

The 12×9 cut deliberately selects one representative checkpoint per session.
T2 challenges that assumption: if persistence is the signal, one checkpoint
cannot identify it. Keep the 12×9 response replication separate, then open
only the adjacent-pair axis.

## Theory 3 — hard development and writing require different evidence

### Claim

A generic “activity versus value” rule is underspecified. For hard
development, progress should be grounded in edits, command outcomes, changed
test results, and resolved blockers. For writing, progress should be grounded
in narrowed claims, coherent artifact growth, review incorporation, and
delivery. Confidence language and tool volume mean different things in the
two work kinds.

### Controlled card pack T3

This is a synthetic discrimination trial, not a natural-frequency estimate.
Create **48** prefix-only cards before any judge calls:

| Axis | Exact values |
|---|---|
| GROWTH archetype | all **12** question archetypes from `GROWTH-RANKING.json` |
| work kind | `hard_dev`, `writing` |
| human reference action | `fire_now`, `defer_closing` |
| card count | **12 × 2 × 2 = 48** |
| prompt arm | `generic_value`, `work_kind_conditioned` |
| repeats | TypeSafe **12**; Flash **2**; Luna **2** if commissioned |

For every archetype, an independent human author freezes four matched cards:
hard-dev fire/defer and writing fire/defer. The two work-kind cards share the
same trajectory shape but use work-kind-appropriate evidence. Models may
generate wording variations, but a human must freeze the card and reference
action under the outcome-sheet concepts before results are opened. Gold
actions are always withheld from judge payloads. The generic arm receives
`work_kind=unspecified`; the conditioned arm receives the frozen `hard_dev` or
`writing` tag so it can apply the matching contract above.

Cell counts:

- TypeSafe: **48 × 2 × 12 = 1,152**.
- Flash OpenCode confirmation: **48 × 2 × 2 = 192**.
- Optional Luna confirmation: **192**.

The conditioned arm tells the judge which evidence contract applies; it does
not tell it the expected action. Cards must be balanced and deterministically
shuffled so the action cannot be inferred from order or length.

### Meters and verdict

Report unique-card modal decisions:

- `near_done_fp_cards / 24` on `defer_closing` references;
- `good_interception_cards / 24` on `fire_now` references;
- balanced accuracy per work kind and macro average;
- absolute hard-dev versus writing accuracy gap;
- repeat entropy and parse/error rate.

Advance `work_kind_conditioned` only if:

1. at most **1/24** closing cards fire;
2. at least **20/24** fire-reference cards fire;
3. macro balanced accuracy is at least **0.85**;
4. the work-kind accuracy gap is at most **0.10**; and
5. it beats `generic_value` by at least **0.10** on the weaker work kind.

Because this is controlled evidence, passing T3 authorizes a natural-corpus
top-up, not a product claim.

### Relationship to the GROWTH cut

T3 reuses all 12 GROWTH archetypes but challenges their task-agnostic wording.
It must not replace the 12×9 replication denominator. A later natural
replication needs a blind, prefix-derived `work_kind` sidecar and balanced
writing coverage; the current corpus must not be silently relabeled to create
that balance.

## Theory 4 — explicit turn depth is a useful hazard prior

### Claim

As a competing simple theory, intervention risk rises with turn depth even
after looking at the same prefix evidence. If true, exposing the checkpoint
number should improve useful interception. If it mainly increases fires on
late near-done work, turn depth is a harmful shortcut.

### Matrix T4

| Axis | Exact values |
|---|---|
| checkpoint key | all **67** exact-labeled natural-corpus keys |
| depth arm | `depth_visible`, `depth_blind` |
| state | otherwise byte-identical `trial-prefix-v1` |
| response | shared four labels under neutral `generic_now` wording |
| scout repeats | TypeSafe **1** |
| full repeats | TypeSafe **8 total** if scout gate passes |
| confirmation | Flash **2** repeats only after the full TypeSafe gate |

Both arms use relative tail positions. `depth_blind` then removes
`checkpoint_turn`, prior-checkpoint/schedule values, `elapsed_turns`, and
`cumulative.api_turns`; it does not remove content or tool evidence. Emit a
structural diff proving that those are the only changed paths.

Cell counts:

- TypeSafe scout: **67 × 2 = 134**.
- TypeSafe full total: **67 × 2 × 8 = 1,072** (**938** additional after the
  scout).
- Flash confirmation: **67 × 2 × 2 = 268**.

### Meters and verdict

Report:

- visible-versus-blind decision flips on the same key;
- `near_done_fp_keys / 24` and `good_interception_keys / 4` by arm;
- fire slope by checkpoint among `no_steer_window` keys, with session-clustered
  intervals;
- repeat entropy and parse/error rate.

The scout stops immediately if `depth_visible` adds any near-done fire without
adding a useful-runaway fire. Full volume advances the theory only if visible
depth adds at least one of the four useful-runaway keys, adds **zero**
near-done keys, correctly fires at least one key in both useful-window
sessions, and does not create a positive late-turn fire slope among
`no_steer_window` keys.

### Relationship to the GROWTH cut

The 12×9 cut includes prefix-local checkpoint information but does not isolate
its influence. T4 is a falsification control for that shortcut. It is ranked
last because the current four useful windows occur at 45–75, so the corpus
already gives a depth-only theory weak support.

## Burn order

1. **T1 closing-value veto — burn TypeSafe volume first.** It directly targets
   the costly failure and has 24 near-done keys.
2. **T2 persistence/re-intercept.** It tests timing with 47 real adjacent
   pairs and can explain why a one-window classifier misfires.
3. **T3 work-kind evidence.** Run after the 48-card human freeze and blind
   audit; it is controlled discrimination, not natural prevalence.
4. **T4 depth prior.** Run only the 134-cell scout unless it clears the strict
   no-added-near-done-FP gate.

Within each theory: TypeSafe carries volume; Flash OpenCode confirms the
frozen discriminating cut; Luna is an optional third policy-under-test.
Compare drivers on matched keys, but do not use agreement as gold.

## Required output meters

Each theory directory must include `matrix.json`, `results.jsonl`,
`meters.json`, and `METERS.md`. `meters.json` must report:

- planned, attempted, parsed, errored, and duplicate cells;
- unique checkpoint/card denominators separately from calls;
- state occupancy/missingness and state hashes by arm;
- decision counts, repeat entropy, and driver;
- exact label-join eligibility;
- near-done FP and good-interception counts only on eligible references;
- session-clustered intervals for natural-corpus rates;
- `synthetic_controlled=true` for T3;
- `soft_standard_hold=true`, `product_wiring=false`, and
  `not_a_product_scoreboard=true`.

Do not interpret a theory if parse completeness is below 99%, any required
state is empty, labels leaked into payloads, or the planned arm counts differ.
Raw rows continue to use `window_status=unidentified`; outcome joins are
derived artifacts.

## Axes deliberately left open after #111 replication

Open one at a time, after the frozen 12×9 driver replication:

| Open axis | First place it is tested | Held fixed elsewhere |
|---|---|---|
| confidence language | T1 observed vs ungrounded decoy claim | underlying prefix evidence, checkpoint |
| closing-value rule | T1 H1 vs H4 | response contract |
| ~15-turn cadence | T2 adjacent pairs | labels, driver-specific analysis |
| one-window vs persistent evidence | T2 | question response labels |
| hard-dev vs writing | T3 controlled cards | archetype and action balance |
| explicit turn depth | T4 visible vs blind | all non-depth state bytes |
| state representation (`phase_hints_focus`) | **still open** | do not add to first replication |
| response class beyond binary/four-label | **still open** | do not add to first replication |
| broader writing-heavy natural corpus | **still open** | no silent rebalance of current corpus |
| label adjudication / more positive windows | **still open** | no model-derived gold |

None of these trials changes the Soft HOLD or authorizes live interception.
