# Batch-003 adversarial-gap trial designs — Soft HOLD

> **Soft Standard HOLD.** This package contains trial designs, frozen cell
> manifests, and offline validation only. It authorizes no hooks, `:8080`,
> Standard/Pilot/Max unlock, live in-loop Jev, product wiring, or FP/miss
> scoreboard. A favorable result would not release the hold.

## Intent

Design concrete next trials that close the gaps identified by
[#115](https://github.com/codyhamilton/workflow-plugin/pull/115): the missing
labeled runaway/non-Maps minimum, state-representation flips, single-stratum
GROWTH pool, missing H2 nulls, and five questions that were 0/48 under all
three GROWTH states. Freeze cells, drivers, N, metrics, and burn order so
TypeSafe, Flash, and Luna execution seats do not select them after seeing
responses.

This design is based on master `06776c47` (post-[#112](https://github.com/codyhamilton/workflow-plugin/pull/112))
and reads #115 at commit `2fd769c`. #115 is not merged at this design's base,
so this package cites the PR rather than adding a broken relative link to its
`ADVERSARIAL-FOLD-soft-hold.md`.

Machine-readable contracts:

- [`TRIAL-MATRIX.json`](TRIAL-MATRIX.json) — axes, exact N, wordings, nulls,
  gates, metrics, and burn order.
- [`SESSION-STRATA.json`](SESSION-STRATA.json) — frozen 28-session,
  four-harness t=45 corpus in seven execution blocks.
- [`materialize_plan.py`](materialize_plan.py) — emits frozen core cell rows;
  makes no judge call.
- [`validate_design.py`](validate_design.py) — checks counts, caps, label facts,
  checkpoint reach, and Soft HOLD assertions; makes no judge call.

## Why the next spend cannot be another 12×9 refill

The required facts reproduce from landed artifacts and #115:

| Gap | Current fact | Consequence |
|---|---:|---|
| Labeled minimum | 20 labeled sessions, but only **2** runaway-like sessions / **4** positive checkpoint slots | The ≥4-session runaway minimum is not met |
| t=75 support | Exactly **12** current snapshots reach t=75; all are already labeled | Relabeling the current corpus cannot add two new positive sessions |
| Preferred exact cut | **9** Maps/claude-code sessions; runaway-like `yes` **0**, non-Maps **0** | Never-fire is vacuously unbeatable on misses |
| Representation | `test_flake_loop` 0/16 vs 10/16; `bash_retry_storm` 0/16 vs 5/16 across states | State must be a paired, frozen axis |
| Corpus | GROWTH eligibility **16/16** claude-code Maps; other **25** sessions lack native `tail` | Cell volume does not create stratum diversity |
| Occupancy | Five questions are **0/48** across all states | Wording, driver, and corpus must be separated |

The current 21 unlabeled snapshots all stop before t=75. The ranking gate
therefore requires new right-sized transcripts, not more labels on the same
41-session pool.

## Design A — label and corpus qualification before judge burn

### A1. New t=75 acquisition

Acquire a first tranche of **16 new non-Maps sessions that genuinely reach
fixed checkpoint 75** from the landed
[`stats.json`](../../2026-10-02-local-session-inventory/stats.json) inventory.
The number is session N, not cell N.

Selection is response-blind:

1. Deduplicate logical sessions.
2. Build prefix checkpoints and discard candidates that do not reach t=75.
3. Round-robin harness, then project; take at most two from one
   harness-project stratum per pass.
4. Within a stratum, sort by prefix turn count descending and `session_id`
   ascending.
5. Label every selected session before opening its TypeSafe, Flash, or Luna
   output. If fewer than 16 candidates survive, label all and report inventory
   exhaustion.

Each new session gets two independent human reviews under
[`OUTCOME-SHEET.md`](../OUTCOME-SHEET.md). A third blind human resolves
disagreement. Also second-adjudicate the **nine** existing exact-cut sessions.
Labels include per-checkpoint near-done/runaway values, a cited
`ideal_steer_window(_by_cp)`, and independence attestations.

### A2. Terminal gate

The outcome-linked ranking extension remains closed until all are true:

- ≥12 labeled sessions survived to t=75;
- ≥4 distinct sessions have runaway-like `yes` and a cited non-ambiguous
  window;
- ≥4 sessions have defended near-done intervals or window `none`;
- ≥4 sessions are frozen as response-blind hold-out, including ≥1 non-Maps;
- claude-code and Maps shares are each ≤40%.

Failure is a valid result: publish response-distribution diagnostics and
write `ranking_ready=false`. Do not compensate with more cells.

## Design B — paired state sensitivity on a multi-stratum corpus

### B1. Corpus

[`SESSION-STRATA.json`](SESSION-STRATA.json) freezes **28** sessions at fixed
checkpoint 45:

| Stratum | Sessions | Share |
|---|---:|---:|
| claude-code / Maps | 11 | 39.3% |
| opencode / non-Maps | 13 | 46.4% |
| codex / non-Maps | 2 | 7.1% |
| cursor / non-Maps | 2 | 7.1% |
| **Total** | **28** | **100%** |

There are six projects. Maps and claude-code are each 11/28, below the 40%
cap. `B02` is the four-session response-blind hold-out and includes all four
harnesses.

### B2. Harness-native state prerequisite

The 17 non-Claude sessions must gain a prefix-only, harness-native contract
for `tail`, `markers`, `phase_hints`, `recent`, `brief_anchor`, and
`delta_since_prior`. The contract is not permission to fabricate empty state:

- `tail` is the last three ordered assistant/tool records at or before t=45;
- deltas compare with the immediately prior fixed checkpoint;
- no `T`, `cp/T`, final length, post-checkpoint event, label, or judge response;
- the projected-state hash must be identical across all three drivers;
- unsupported state gates the session instead of silently thinning it.

This is lab extraction only. It does not change a hook or runtime state.

### B3. Cell matrix

Every driver receives the exact same non-driver cell keys:

| Axis | Values | N |
|---|---|---:|
| Sessions | frozen t=45 set | 28 |
| Questions | #109 twelve GROWTH IDs | 12 |
| States | `markers_focus`, `phase_hints_focus`, `recent_delta_brief` | 3 |
| Response | binary fire/defer | 1 |
| **Per driver** | 28 × 12 × 3 | **1,008** |
| **TypeSafe + Flash + Luna** | 1,008 × 3 | **3,024** |

This clears the white-paper floor of 1,000 new trials per driver while making
state a paired axis rather than a post-hoc choice. The independent unit is the
session, never the 3,024 cells.

The block order is `B01`, `B03`–`B07`, then hold-out `B02`. Finish each block
on all three drivers before starting the next; no driver may run more than one
block ahead.

### B4. Driver contract

| Driver | Pin | Existing reference | Batch-003 adapter requirement |
|---|---|---|---|
| TypeSafe | `jev-1.13.0` | [`run_typesafe_growth_volume.py`](../batch-002/run_typesafe_growth_volume.py) | Consume materialized cells; preserve state/question bytes |
| Flash | `deepseek/deepseek-flash` | [`run_batch002_multidriver.py`](../batch-002/run_batch002_multidriver.py) | Same, plus persistent per-batch parse sidecar before volume |
| Luna | `gpt-6-luna` | [`run_batch002_flash_luna_b.py`](../batch-002/run_batch002_flash_luna_b.py) | Same state/question bytes through the codex CLI |

The execution seat adds a lab-only manifest adapter under `batch-003/`; the
three existing runners do not currently consume this common manifest. The
adapter must emit `window_status=unidentified`, `outcome_tag=null`,
`judge_role=policy-under-test`, state hash, parse status, and session
covariates. It must not contact localhost or product code.

Materialize and inspect the frozen plan now:

```bash
cd docs/lab/RESEARCH/2026-10-02-interception-trials/batch-003
python3 validate_design.py
python3 materialize_plan.py --driver typesafe --block B01 --summary
python3 materialize_plan.py --driver typesafe --block B01 \
  --output /tmp/batch003-typesafe-B01.jsonl
```

`B01` is a reusable **144-cell per-driver canary**: 4 sessions × 12 questions
× 3 states. Advance only with complete state-hash parity, zero leak hits,
every cell accounted for, a Flash parse sidecar, and ≥99% parse completeness.

## Design C — five 0/48 questions: wording × driver × corpus

The five frozen IDs are:

`dependency_wait`, `brief_abandon`, `scope_creep_silent`,
`speculative_rewrite`, and `deliverable_orphan`.

First, a human blind to judge outputs annotates target evidence at t=45 as
present, absent, or ambiguous. For each question, freeze:

- 6 target-evidence-positive sessions;
- 6 harness/project-matched quiet sessions;
- 0 ambiguous sessions.

If six positives do not exist, expand the corpus before spending. Do not turn
ambiguous or empty-state sessions into controls.

Run two wordings on the canonical #109 state:

- `w0`: the exact batch-002 wording;
- `w1`: the decision-aligned wording in
  [`TRIAL-MATRIX.json`](TRIAL-MATRIX.json), which asks whether steering now is
  useful and removes the `dependency_wait` “steer moot” inversion.

The analysis matrix is:

| Axis | Values |
|---|---|
| Questions | 5 |
| Wordings | 2 |
| Corpus | 6 positive + 6 matched quiet per question |
| Drivers | TypeSafe, Flash, Luna |
| State | one frozen canonical state per question |
| **Analysis N** | **120 cells/driver; 360 total** |
| Reused from Design B | w0 canonical-state cells |
| **New calls** | **60/driver; 180 total** |

Read all three axes from the same exact cells:

- wording: within-session `fire(w1) - fire(w0)`;
- corpus: positive-panel minus quiet-panel fire;
- driver: exact-cell discordance and paired fire differences.

The readout is not “more fire is better.” It is:

- **wording-supported** if w1 changes occupancy on the positive panel while
  quiet stays lower;
- **quiet-corpus-supported** if both wordings distinguish positive from quiet
  in at least two drivers;
- **driver-supported** if one driver has occupancy where another remains
  all-defer on exact cells;
- **unresolved** if every wording and driver remains all-defer on the
  evidence-positive panel.

## Design D — H2 nulls and the fixed-schedule ranking extension

### D1. Zero-burn 12×9 null table

Compute three deterministic policies for all **108** existing exact-cut cells:

| Null | Rule on the representative checkpoint | Fire cells |
|---|---|---:|
| `never_fire` | always defer | 0 |
| `constant_turn_75` | fire when checkpoint ≥75 | 60 |
| `constant_turn_90` | fire when checkpoint ≥90 | 0 |

This yields **324 derived policy rows** and no judge call. Publish the critical
stamp beside them: the cut has zero runaway-positive snapshots and zero
non-Maps sessions, so a runaway-miss comparison is unidentifiable and
never-fire is vacuously unbeatable.

### D2. Ranking extension after Design A passes

Freeze 12 labeled sessions, including four response-blind hold-outs, and run
the #109 preferred state/question pairs at **every reached checkpoint** in
`(45, 60, 75, 90, 105, 120)`. Never use the median-of-reached selector.

| Quantity | N |
|---|---:|
| Sessions | 12 |
| Preferred scenarios | 12 |
| Minimum reached checkpoints/session | 3 (45, 60, 75) |
| **Minimum cells/driver** | **432** |
| Maximum if all reach t=120 | 864 |
| **Minimum all-driver calls** | **1,296** |

Meters include `n_at_risk` and `n_never_reached` at every checkpoint, plus
never-fire, constant-75, and constant-90 fire times. If Design A misses its
terminal gate, this matrix is not materialized.

## Success metrics

### Trial integrity

- ≥99% parsed rows per driver; every miss is explicit.
- Zero leak-key hits and exact projected-state hashes across drivers.
- All pre-registered cells present or explicitly failed.
- Flash parse diagnostics persisted per batch; until then Flash estimates are
  stamped missing-not-at-random.
- `tail_length`, prefix turn count, activity density, harness, project, Maps
  flag, and corpus source persisted.

### Response occupancy

For every driver × question × state, publish fire count, N, sessions with any
fire, and `all_defer`. An all-defer pair is uninformative for that driver and
does not count toward an informative-cell floor.

### State sensitivity

Report three within-session paired fire differences, state flip rate, and
session-clustered bootstrap intervals, separately by driver and Maps versus
non-Maps.

- **Sensitive:** absolute paired difference ≥0.20, 95% interval excludes zero,
  and held-out sign agrees.
- **Representation-robust:** every absolute difference ≤0.10 and every 95%
  interval lies inside `[-0.15, 0.15]`.
- Otherwise: **unresolved**; no post-hoc preferred state.

### Outcome-linked card

Only after Design A passes:

- near-done side: fewer `near_done_fp` and `productive_interrupt` fires than
  constant-75 and constant-90, components separate;
- runaway side: fewer `runaway_miss` cells than never-fire inside cited,
  non-`none`, non-ambiguous windows;
- session-clustered intervals and strata are mandatory;
- winning one side and losing the other is not a win.

## Ranked burn order

| Rank | Work | Judge calls | Stop condition |
|---:|---|---:|---|
| 0 | Materialize current 12×9 H2 nulls | 0 | 324 rows + unidentifiable stamp |
| 1 | Acquire/double-label 16 new non-Maps t=75 sessions; second-adjudicate nine exact sessions | 0 | Labels frozen or inventory exhausted |
| 2 | Build and leak-test 17 non-Claude state adapters | 0 | Non-empty, prefix-only, cross-driver hash parity |
| 3 | B01 canary, all drivers interleaved | 432 | Parse/state gates pass |
| 4 | B03–B07, then hold-out B02 | 2,592 | Core reaches 1,008/driver |
| 5 | Five-question w1 add-on | 180 | Positive/quiet panels complete |
| 6 | Fixed-schedule ranking extension | ≥1,296 | **Only** if labeled gate passes |

This order spends zero judge calls on the two structural blockers, prevents a
new TypeSafe-only pool, and prevents Flash parse loss from being discovered
after the other drivers have already consumed the wave.

## Decision ledger

| Decision | Rationale | If wrong |
|---|---|---|
| t=45 for state sensitivity | It is the first fixed checkpoint shared by the frozen four-harness corpus | Rebuild the whole frozen matrix at another common fixed checkpoint; do not mix checkpoints |
| 28 sessions | 28 × 12 × 3 = 1,008/driver and permits Maps/claude shares of 11/28 | Expand in complete stratified blocks; never drop below the per-driver floor |
| First label tranche N=16 | Current corpus cannot create new t=75 positives; a non-Maps tranche can close both deficits | If inventory has fewer, label all and report ranking blocked |
| Binary response for the paired core | Keeps the measured axis state, not response schema | A response-schema study is a separate preregistered matrix |
| Sensitivity/equivalence margins | Makes “flip” and “robust” falsifiable before results | Publish raw intervals and mark unresolved; never tune margins after hold-out |

## Explicit non-authorization

The package designs lab trials only. It does not implement a behavior runner,
change `assert_phase`, modify a hook, open `:8080`, choose a winning framing,
or authorize a scoreboard. It leaves H1/H3/H4 ranking closed until the label
gate passes, and it leaves Standard under Soft HOLD regardless of results.
