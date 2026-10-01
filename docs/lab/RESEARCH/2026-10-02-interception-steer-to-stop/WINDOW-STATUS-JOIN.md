# Window-status identification — batch-002

> **Soft Standard HOLD.** Evidence and derived mappings only. No hooks, Standard
> behavior, score threshold, or FP/miss product claim is authorized here.

This note extends the corpus analysis landed in #105 at `bfdf21d`. It does not
repeat the fire-rate distributions in [`ANALYSIS.md`](ANALYSIS.md). Its narrower
purpose is to turn the independent outcome sidecar into an explicit,
non-destructive `window_status` mapping and to say exactly which joins remain
partial.

Reproduce the mapping with
[`tools/interception/window_status_join.py`](../../../../tools/interception/window_status_join.py):

```bash
LABELS=docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/outcome-labels.jsonl
BATCH=docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002

# All 240 original Wave-0 rows pass both coverage gates.
python3 tools/interception/window_status_join.py \
  --labels "$LABELS" --results "$BATCH/results.jsonl" \
  --require-all-labeled --require-checkpoint-outcomes

# The 200 × 41 sweep intentionally reports partial coverage.
python3 tools/interception/window_status_join.py \
  --labels "$LABELS" \
  --results "$BATCH/typesafe-scenario-sweep/results.jsonl"
```

Pass `--output /tmp/window-map.jsonl` for a source-row-keyed derived table.
`derived_row_id` combines the source `cell_id` with its one-based row number,
because the Wave-0 source contains repeated cell IDs. The tool never rewrites a
source `results.jsonl`, reads no judge rating/fire field, and computes no
FP/miss metric.

## Identification method

Join on exact `session_id`, then classify each result checkpoint `t` from the
label's window:

1. Require a unique sidecar row with the complete `outcome-sheet-v1` schema:
   valid label/termination enums, matching fixed-schedule checkpoint maps,
   allowed pattern tags, a ≤200-word rationale, and all three independence
   attestations set to `false`.
2. Select `ideal_steer_window_by_cp[str(t)]` when present; otherwise use the
   session-level `ideal_steer_window`. The session-level value is the protocol's
   default, not a missing value.
3. Map the effective value without consulting final length, model output, or
   whether the model fired.
4. Join `near_done_at_checkpoint[str(t)]` and
   `runaway_like_at_checkpoint[str(t)]` separately. A known window does **not**
   make these checkpoint outcomes known.

| Effective label at `t` | Derived `window_status` | Meaning |
|---|---|---|
| finite `[start,end]`, `start ≤ t ≤ end` | `inside_steer_window` | The observed checkpoint lies inside the labeled useful-steer interval |
| finite `[start,end]`, `t` outside | `outside_steer_window` | The session has a window, but this checkpoint is outside it |
| `none` | `no_steer_window` | The labeled session has no appropriate steer window |
| `ambiguous` | `ambiguous` | Adjudication intentionally retains uncertainty |
| missing/non-labeled sidecar row | `unidentified` | No outcome-label basis for a window claim |

`outside_steer_window` and `no_steer_window` are deliberately distinct. The
first can coexist with another checkpoint that is inside a finite window; the
second is a session-level negative control. Missing data remains
`unidentified`, never `no_steer_window`.

The derived row also carries an orthogonal `label_join_eligibility`:

| Eligibility | Meaning |
|---|---|
| `label_join_exact` | Session label and both checkpoint outcome fields exist at exact `t` |
| `session_unlabeled` | No sidecar row exists for the result session |
| `checkpoint_unlabeled` | The session window is known, but near-done/runaway labels do not exist at exact `t` |
| `session_not_labeled` | A sidecar row exists with `label_status=not_labeled` |
| `label_excluded` | A sidecar row explicitly excludes the session |

No nearest-checkpoint interpolation is allowed.

The source labels were adjudicated from blind transcript digests under
`outcome-sheet-v1`; their rationales cite turns and artifact facts. The join
uses those labels as the reference sidecar. It does not infer windows from
snapshot counters or tail text. In particular, `T_eligibility_only`,
checkpoint survival, rating, and fire are forbidden inputs to this mapping.

## Provisional mapping

The sidecar has 20 labeled sessions: 17 `none`, no `ambiguous`, and three
finite windows.

| Session | Labeled window | Wave-0 observed checkpoints | Wave-0 mapping | Scenario representative checkpoint |
|---|---:|---|---|---|
| `a56bad1c7f13` | `[55,62]` | 45, 60, 75, 90, 105, 120 | 60 inside; five outside | 75 outside |
| `ses_1a0328cd5ffe6iabFeMK` | `[22,164]` | 45, 60, 75 | all three inside | 55 inside, but checkpoint outcomes absent at 55 |
| `ses_1a0369734ffeqlVOz4S8` | `[161,174]` | 45, 60, 75, 90, 105, 120 | all six outside | 75 outside |

The remaining 17 labeled sessions map every observed checkpoint to
`no_steer_window`.

### Coverage, not a scoreboard

Counts below measure mapping completeness. Cell counts are repeated lever or
scenario rows; the `(session, checkpoint)` column prevents that replication
from looking like independent evidence.

| Corpus | Unique `(session,checkpoint)` | Cell rows | inside | outside | no window | ambiguous | unidentified | Checkpoint outcomes complete |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Wave-0 Flash `results.jsonl` | 67 | 240 | 4 / 15 | 11 / 36 | 52 / 189 | 0 / 0 | 0 / 0 | 67 / 240 |
| TypeSafe scenario sweep | 41 | 8,200 | 1 / 200 | 2 / 400 | 17 / 3,400 | 0 / 0 | 21 / 4,200 | 13 / 2,600 |

Each status cell is `unique / rows`. This table makes no claim about model
quality. It shows that the original 240-row join is mechanically complete,
while the scenario join is not.

Eligibility makes the incomplete scenario rows explicit: 2,600 are
`label_join_exact`, 1,400 are `checkpoint_unlabeled`, and 4,200 are
`session_unlabeled`. All 240 Wave-0 rows are `label_join_exact`.

The TypeSafe lever-wave follow-up applies the same eligibility contract across
four committed `Wave-0-multi` streams. All **5420/5420** rows, **20/20**
sessions, and **67/67** unique `(session_id, checkpoint)` keys are
`label_join_exact`; no committed lever row remains unlabeled. The separate
`typesafe-k4` meters report 1500 cells but have no committed `results.jsonl`,
so their row-level join coverage is unknown rather than inferred. See
[`../2026-10-02-interception-trials/batch-002/typesafe-outcome-join/COVERAGE.md`](../2026-10-02-interception-trials/batch-002/typesafe-outcome-join/COVERAGE.md).
This is a coverage result, not an FP/miss board.

Wave-0 has 236 unique `cell_id` values across 240 rows. Four IDs each occur
twice, and each pair is byte-for-byte identical at the parsed-object level.
The status derivation preserves all source rows and reports the collision; a
future scoreboard must choose and document a deduplication rule before setting
independent denominators.

## Relationship to #105 provisional tags

The #105 row table remains useful as a fire-bearing **provisional** table.
Window identity should be added as a separate derived field using the mapping
above.

Do not promote `PROVISIONAL_runaway_miss_candidate` directly to the formal
`runaway_miss` in [`OUTCOME-SHEET.md`](../2026-10-02-interception-trials/OUTCOME-SHEET.md).
The candidate in #105 requires non-fire plus `runaway_like=yes`; the formal
rule additionally requires a finite labeled window and `t` inside that window.
The status join supplies that missing gate. It intentionally does not count the
result.

Likewise, an `inside_steer_window` row with missing `runaway_like` is only
window-identified. It is not a hit or miss row. A `no_steer_window` row may
support timing analysis, but it is not automatically a productive checkpoint;
near-done/runaway checkpoint labels remain separate axes.

## What still blocks a full join

1. **Scenario label coverage:** 21 of 41 scenario sessions have no sidecar
   label, accounting for 4,200 rows. They remain `unidentified`.
2. **Checkpoint-axis coverage:** seven of the 20 labeled scenario sessions use
   representative checkpoints not present in their near-done/runaway maps
   (1,400 rows). Their session window is identifiable, but component outcomes
   are not. Label those exact checkpoints; do not copy the nearest fixed
   checkpoint.
3. **Positive-window support:** only three sessions have finite windows. The
   fixed Wave-0 schedule never reaches `[161,174]`; this is observed schedule
   coverage, not evidence that the window is absent.
4. **Digest audit trail:** the sidecar and its turn-citing rationales are
   landed, but the blind transcript-digest inputs used for adjudication are not
   present as immutable corpus artifacts. That does not prevent a mechanical
   join; it does prevent independent replay of digest → label decisions.
5. **Adjudication/versioning:** there is one labeler identity and no recorded
   second-pass agreement or adjudication state. Any added labels or overrides
   need a new `protocol_rev` (or an explicit amendment record), not silent
   mutation.
6. **Row identity:** `cell_id` is not unique in Wave-0 (four exact duplicate
   pairs). A full join must use source-row identity while deriving, then apply
   an explicit provenance-preserving deduplication rule.
7. **Metadata drift:** `grid.json` reports 22 sessions and 21 at risk at turn
   45, while the empirical Wave-0 result file contains 20 sessions, all at turn
   45. Derived denominators must come from validated joined rows until that
   metadata discrepancy is annotated or corrected.
8. **Scoreboard aggregation:** after coverage closes, meter generation still
   needs session-clustered denominators and explicit handling for `ambiguous`,
   `excluded`, censoring, and repeated cells. Cell-level counts are not
   independent trials.

None of these gaps authorizes filling a missing label from Flash, Luna,
TypeSafe, result rationales, final session length, or checkpoint survivorship.
Soft HOLD remains unchanged after the join becomes mechanically complete.
