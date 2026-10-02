# ANALYSIS — interception lab corpus (batch-002 + streams)

> **Soft Standard HOLD** — docs and measured artifacts only. No hooks, no Soft Standard unlock, no product behaviour change. Nothing here is an FP/miss **scoreboard**; provisional joins are explicitly tagged.

**Generated:** 2026-10-02 (UTC artifacts via [`analyze_corpus.py`](../2026-10-02-interception-trials/batch-002/analyze_corpus.py))  
**Reproduce:** `python3 docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/analyze_corpus.py`

**Sibling outputs:** [`METERS-APPENDIX.md`](METERS-APPENDIX.md) (packed tables; [#109](https://github.com/codyhamilton/workflow-plugin/pull/109)/[#110](https://github.com/codyhamilton/workflow-plugin/pull/110)/[#111](https://github.com/codyhamilton/workflow-plugin/pull/111)) · [`analysis/ARTIFACT-INVENTORY.json`](analysis/ARTIFACT-INVENTORY.json) · [`analysis/scenario-fire-rankings.json`](analysis/scenario-fire-rankings.json) · [`analysis/PROVISIONAL-join-summary.json`](analysis/PROVISIONAL-join-summary.json) · [`analysis/PROVISIONAL-join-wave0-flash.jsonl`](analysis/PROVISIONAL-join-wave0-flash.jsonl)

**Window-status refinement:** [`WINDOW-STATUS-JOIN.md`](WINDOW-STATUS-JOIN.md)
derives explicit `inside` / `outside` / `none` / `ambiguous` / `unidentified`
states from the outcome sidecar, separates window identity from checkpoint
outcome coverage, and documents the remaining full-join gates. It adds no
FP/miss metric.

---

## 1. What exists on disk (inventory)

### Outcome labels (#103)

| Artifact | Rows | Key fields |
|----------|-----:|------------|
| [`batch-002/outcome-labels.jsonl`](../2026-10-02-interception-trials/batch-002/outcome-labels.jsonl) | **20** | `session_id`, `near_done_at_checkpoint`, `runaway_like_at_checkpoint`, `ideal_steer_window`, `pattern_tags`, `independence` |

All 20 rows: `label_status=labeled`, `labeler=chm-sol-adjudication`, `protocol_rev=outcome-sheet-v1`. Independence attestation: no Flash rating/fire, no leaked fields.

### Result streams (batch-002 tree)

Sixteen `results.jsonl` files under `batch-002/` (full table in [`analysis/ARTIFACT-INVENTORY.json`](analysis/ARTIFACT-INVENTORY.json)). Highlights:

| Stream | Rows | Scored | Fire rate (scored) | Sessions | Driver | Notes |
|--------|-----:|-------:|-------------------:|---------:|--------|-------|
| `results.jsonl` (Wave-0 Flash) | 240 | 240 | **31.3%** | 20 | Flash (`policy-under-test`) | 4/12 lever combos only; canonical decontam path |
| `typesafe-scenario-sweep/` | **15,834** | 13,522‡ | **1.89%‡** | 41 | TypeSafe | **392 measured scenarios**; mixed 41/16-session denominators; 1 mid checkpoint/session |
| `typesafe-k1/` | 2500 | 2500 | **1.4%** | 3* | TypeSafe | Lever grid; H1–H5 interleaved |
| `typesafe-k2/` | 2500 | 2500 | **1.3%** | 3* | TypeSafe | k2 duplicate scale |
| `flash-scale/` | 2400 | 250† | 38.4%† | — | Flash | Streaming; partial score |
| `flash-mid/` | 1600 | 50† | 22.0%† | — | Flash | T≥30 expand; partial |
| `luna-scale/` | 960 | 90† | 20.0%† | — | Luna | Partial |
| `luna-mid/` | 640 | 30† | 16.7%† | — | Luna | Partial |
| `flash-hframings-b/` | 360 | 360 | 26.7% | 20 | Flash | H-framing b-wave |
| `luna-b/` | 180 | 180 | 19.4% | 20 | Luna | |
| `archive-t45-only/` | 240 | 240 | 22.5% | 20 | Flash | **Excluded** — allocation bug |

† Incomplete streams at land time per [`CUMULATIVE-STREAM.md`](../2026-10-02-interception-trials/batch-002/CUMULATIVE-STREAM.md).

‡ Post-#110 meters exclude 2,312 stale, empty-field GROWTH rows. The 102
filled GROWTH scenarios have 16 eligible sessions; the other 290 scenarios
have 41. Raw rows are retained for provenance.

`typesafe-review-check/results.jsonl` (1744 rows) uses a **review-axis schema** (`answers`, `axis`, `builder`) — not comparable fire rates without a separate mapper.

Supporting meters: `meters.json` / `METERS.md` per stream; scenario progress in [`typesafe-scenario-sweep/meters.json`](../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/meters.json) and [`SCENARIO-PROGRESS.md`](../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/SCENARIO-PROGRESS.md).

### Quarantine / decontam (do not score)

- **`batch-001/`** — T leak ([`LEAKAGE-NOTE.md`](../2026-10-02-interception-trials/batch-001/LEAKAGE-NOTE.md)).
- **`batch-002/archive-t45-only/`** — discarded t=45-only run ([`EVIDENCE-LOG.md`](../2026-10-02-interception-trials/EVIDENCE-LOG.md)).
- **`typesafe-scenario-sweep/SUPERSEDED-NOTE.json`** — documents superseded cartesian attempt only.

---

## 2. Exploratory findings

### 2a. Scenario corpus (200 × 41) — TypeSafe (#104)

Progress metric is **`n_distinct_scenarios` (200)**, not raw cell count (8200 = scenarios × sessions at one representative checkpoint each). `window_cartesian=false`.

**Overall fire (TypeSafe `fire_now=fire`):** 116 / 8200 = **1.41%**.

**Question format dominates** (aggregated across state selections):

| Question format | Fire rate | Fires / cells |
|-----------------|----------:|--------------:|
| `silent_stall` | **20.1%** | 66 / 328 |
| `reread_loop` | 4.0% | 13 / 328 |
| `output_starvation` | 3.8% | 11 / 287 |
| `late_miss_risk` | 3.1% | 9 / 287 |
| `activity_without_value` | 2.8% | 7 / 246 |
| Most other `q.*` | **0%** | 0 |

**State selection** (same questions pooled):

| State selection | Fire rate | Notes |
|-----------------|----------:|-------|
| `tail_focus` | **3.57%** | Highest among new §D states |
| `brief_cum_no_tail` | 2.44% | |
| `delta_only` | 2.18% | |
| `window_delta_tools` | **0%** | Zero fires across 1148 cells |
| `state_length_mid` / `chars_budget_1200` | &lt;1% | |

**Top scenario pairs** (full list: [`analysis/scenario-fire-rankings.json`](analysis/scenario-fire-rankings.json)):

1. `state.tail_focus|q.silent_stall` — **80.5%** (33/41) — wording asks about “silent stall”; fires often.
2. `state.delta_only|q.silent_stall` — **61.0%** (25/41).
3. Next tier ≤17% (`brief_cum_no_tail` × `reread_loop`, `silent_stall`, etc.).
4. **175 / 200 scenarios never fire** on any of the 41 sessions (at the representative checkpoint).

**Interpretation (diagnostic, not policy):** TypeSafe deferral is the default; high fire rates cluster on **stall/thrash-shaped question text**, especially with `tail_focus` / `delta_only` state builders. That is lever sensitivity, not validated near-done/runaway accuracy — labels are not joined at scenario checkpoints.

**Post-#108 missing-evidence audit:** the aggregate above materially
overstates state evidence. All 25 non-Claude-Code representative snapshots
(20 OpenCode, 3 Codex, 2 Cursor) lack both `tail` and
`delta_since_prior`. Nevertheless, all 25 fire for
`tail_focus × silent_stall` (empty `tail=[]`) and all 25 fire for
`delta_only × silent_stall` (empty `delta_since_prior={}`). Those empty-state
cells account for **50/66 (75.8%)** of all `silent_stall` fires and **50/116
(43.1%)** of all fires in the 200×41 sweep. Among the 16 Claude-Code
snapshots, `delta_only × silent_stall` fires 0/16 and
`tail_focus × silent_stall` fires 8/16. The question wording therefore drives
most of the headline concentration; only the latter eight cells support a
rich-tail sensitivity hypothesis.

`state.window_delta_tools` has a separate schema mismatch: all four projected
delta values are null at all 41 representative snapshots. The runner requests
`tool_histogram`, but rich snapshots expose `tool_histogram_delta`; its other
requested numeric delta keys are absent. Its **0/1,148** result is not evidence
for a useful negative state selector. Future comparisons must report
state-field eligibility/missingness and gate unsupported cells, as the
post-#107 GROWTH fill does.

### 2b. Post-fill GROWTH evidence and preferred reporting cut (#109/#110)

The post-#108 refill in
[#110](https://github.com/codyhamilton/workflow-plugin/pull/110) processed
2,042 new cells with zero errors. Of those, 1,632 were `growth-fill-v1`
GROWTH cells (102 scenarios × 16 state-eligible Claude-Code snapshots):
**103 fire / 1,529 defer**. The runner gated 2,550 unsupported cells
(102 × 25 tail-less snapshots) instead of substituting empty state, and the
meters excluded all 2,312 stale pre-fill GROWTH rows.

The mutually exclusive scenario-level fire-rate bands from the resulting
392-scenario meters are:

| Scope | 0 | (0, 0.10] | (0.10, 0.25] | (0.25, 0.50] | (0.50, 0.75] | >0.75 |
|---|---:|---:|---:|---:|---:|---:|
| All measured scenarios (392) | **334** | 31 | 16 | 4 | 5 | 2 |
| Filled GROWTH only (102) | **77** | 8 | 8 | 4 | 4 | 1 |

The maximum is 0.875. These bands show a mostly-zero response distribution;
they are not accuracy bands and do not identify an FP or miss.

[#109](https://github.com/codyhamilton/workflow-plugin/pull/109) ranks one
state for each of the 12 GROWTH questions in
[`GROWTH-RANKING.json`](../2026-10-02-interception-trials/batch-002/GROWTH-RANKING.json).
The selection rule is evidence compatibility, not highest observed fire:

- `markers_focus` supplies direct wait, compaction, silent/repeated-tool, and
  verification/error markers for four questions.
- `recent_delta_brief` supplies the brief plus recent tool/text and interval
  delta for the other eight.
- `phase_hints_focus` is retained as a representation contrast, but its coarse
  tool-class mix lacks brief, path, command-outcome, and artifact-result
  identity, so it is not preferred for this first cut.

Exact-checkpoint join coverage then determines the reporting denominator:
**12 × 9 = 108 exact-labeled cells per evaluated driver**. The other seven
state-valid snapshots (four checkpoint-unlabeled and three session-unlabeled)
contribute **12 × 7 = 84 diagnostic cells** only; no nearest-checkpoint label
is copied. The 25 tail-less snapshots remain gated.

The #110 TypeSafe refill already contains this cut. Across all 16 state-valid
snapshots it fires 10/192: `markers_focus × idle_tool_spin` contributes 9/16
and `markers_focus × context_thrash_compact` 1/16; the other ten preferred
pairs are 0/16. Restricting to the nine exact-labeled snapshots gives
**6/108** (5 and 1 respectively); the seven diagnostic snapshots contribute
4/84. This is response evidence only. It does not compare fire with labels or
produce a product board.

The repository does not establish an independent preregistration timestamp
for this cut (#110 merged before #109). Treat it as an evidence-compatible
analytic selection, not a claimed preregistered evaluation. A replication
should freeze the 12 pair IDs before another driver is run.

### 2c. Wave-0 Flash lever slice (240 cells, 20 labeled sessions)

Only **four** of twelve planned combos ran (240-cell cap); eight combos in [`grid.json`](../2026-10-02-interception-trials/batch-002/grid.json) never executed ([`analysis/wave0-lever-combos.json`](analysis/wave0-lever-combos.json)):

| State × question × response | Fire rate |
|-----------------------------|----------:|
| `stats_only` + `continue_excessively` + `likert_0_3` | **63%** |
| `stats_only` + `steer_now` + `binary_fire` | 24% |
| `stats_only` + `thrash_bundle` + `four_class` | 16% |
| `hybrid_v0` + `steer_now` + `likert_0_3` | 14% |

**Session clustering:** fire rates span **0%–100%** across sessions (e.g. `2e083814b952` always fires at reached checkpoints; several rollout/codex sessions **never** fire). Maps concentration remains as in [`METERS.md`](../2026-10-02-interception-trials/batch-002/METERS.md) (14/22 sessions in grid; **20** sessions with cells in `results.jsonl`).

**Rating / fire:** Wave-0 meters already note rating ≥2 aligns with `fire` on executed maps; 75 fires / 240 cells.

### 2d. Multi-driver contrast (same protocol family)

At full stream completion, Flash family fire rates (**~19–31%** on finished slices) sit **an order of magnitude above** TypeSafe k1/k2 (**~1.3%**) on overlapping lever semantics — expected given driver role (`policy-under-test` vs System One mapping) and different question grids. **Do not** treat cross-driver fire rate as comparable without session-clustered contrasts on identical `(session_id, checkpoint, state, question)` keys.

### 2e. Outcome labels (reference sidecar)

From 20 sessions × 6 checkpoints:

- **24** checkpoint slots with `near_done=yes` (17 sessions have ≥1).
- **4** checkpoint slots with `runaway_like=yes` (2 sessions).
- **`ideal_steer_window`:** `none` (17), turn-range **3** sessions (`a56bad1c7f13` [55,62]; `ses_1a0369734ffeqlVOz4S8` [161,174]; `ses_1a0328cd5ffe6iabFeMK` [22,164]).

---

## 3. Why `window_status` stays `unidentified` in `results.jsonl`

Per [`PROTOCOL.md`](../2026-10-02-interception-trials/batch-002/PROTOCOL.md) §R2 and [`OUTCOME-SHEET.md`](../2026-10-02-interception-trials/OUTCOME-SHEET.md):

1. **Emit-time rule:** Cells are written with `window_status: "unidentified"` and `outcome_tag: null` so length-derived oracles never appear in the trial corpus.
2. **Sidecar separation:** Human labels live only in `outcome-labels.jsonl`; the protocol forbids silent backfill into historical `results.jsonl`.
3. **Scoreboard gate:** FP/miss rows are **derived** after join + meter regeneration; labels landed **after** Wave-0 emit, and join/report was explicitly **TBD** ([`EVIDENCE-LOG.md`](../2026-10-02-interception-trials/EVIDENCE-LOG.md)).

### Measured join path (provisional)

Apply [`OUTCOME-SHEET.md`](../2026-10-02-interception-trials/OUTCOME-SHEET.md) §“Checkpoint join” to `(session_id, checkpoint)`:

| Derived tag | Rule (abbrev.) |
|-------------|----------------|
| `PROVISIONAL_near_done_fp` | `fire` ∧ `near_done_at_checkpoint[t]=yes` |
| `PROVISIONAL_runaway_hit` | `fire` ∧ `t` ∈ `ideal_steer_window` (non-`none`/`ambiguous`) |
| `PROVISIONAL_runaway_miss_candidate` | ¬`fire` ∧ `runaway_like_at_checkpoint[t]=yes` |
| `PROVISIONAL_productive_interrupt` | `fire` ∧ near-done ≠ yes ∧ runaway ≠ yes |

**Wave-0 Flash join (240 cells, 20 labeled sessions):** see [`analysis/PROVISIONAL-join-summary.json`](analysis/PROVISIONAL-join-summary.json).

| Provisional tag | Count |
|-----------------|------:|
| `PROVISIONAL_productive_interrupt` | 48 |
| `PROVISIONAL_near_done_fp` | 27 |
| `PROVISIONAL_runaway_miss_candidate` | 15 |
| `PROVISIONAL_runaway_hit` | **0** |

**Why zero `runaway_hit`:** labeled useful windows rarely intersect **fixed schedule** checkpoints with `fire=true` (e.g. `a56bad1c7f13` runaway at **t=60** but **no fire** at 60 across combos). Wide windows (e.g. [22,164]) need per-checkpoint `ideal_steer_window_by_cp` or denser schedules — not yet labeled.

Row-level table: [`analysis/PROVISIONAL-join-wave0-flash.jsonl`](analysis/PROVISIONAL-join-wave0-flash.jsonl) (`provisional: true`, `not_scoreboard: true` on every row).

**Next measured join steps** (from summary JSON):

1. Adjudicate `ideal_steer_window_by_cp` where session-level range is too coarse for `FIXED_SCHEDULE`.
2. Regenerate meter markdown with **session-clustered** intervals, not cell-level point rates.
3. Join Flash/Luna/TypeSafe lever streams on `session_id` + `checkpoint` (+ lever keys).
4. Keep scenario sweep on **representative checkpoint** only — do not claim window FP/miss there without per-session window labels at that `t`.

---

## 4. Open gaps

| Gap | Evidence |
|-----|----------|
| Label coverage vs grid | `grid.json` plans **22** sessions; labels + Wave-0 cells cover **20** (2 sessions never got cells in the 240-cap run). |
| Lever grid incomplete | 8/12 combos missing — confounds state/question/class comparisons. |
| Scale streams partial | `flash-scale`, `flash-mid`, `luna-scale`, `luna-mid` incomplete scored rows at land. |
| k1/k2 session N | TypeSafe bulk waves hit **3** sessions in snapshot — not the 41-session scenario sweep pool. |
| No formal FP/miss board | Provisional counts are **not** calibrated precision/recall; n=20 sessions, thin combos. |
| Scenario ↔ outcome join | Scenario sweep uses different checkpoints (`session_representative_mid`) than `FIXED_SCHEDULE` labels. |

---

## 5. Next experiments (bias to measurement)

1. **Label the 2 missing Wave-0 sessions** (or mark `excluded` with rationale) so join denominator matches `grid.json`.
2. **Run the eight skipped lever combos** at the white-paper scale bar (≥1k new trials/driver), same sessions, session-clustered contrasts.
3. **`ideal_steer_window_by_cp`** pilot on the 3 sessions with non-`none` windows + `a56bad1c7f13` runaway@60 — test whether `PROVISIONAL_runaway_hit` / miss become identifiable at schedule points.
4. **Scenario sweep follow-up:** hold state fixed (`tail_focus` vs `window_delta_tools`) and swap only `silent_stall` vs `mid_arc_healthy` on the **same** 41 sessions — quantifies question-wording lever without new sessions.
5. **Blind diagnostic:** correlate `PROVISIONAL_*` tags with Flash vs TypeSafe on matched keys — H6-style dissociation only; still not gold.

---

## 6. Explicit non-authorization

This analysis does **not** unlock Soft Standard, hooks, Pilot, or live Jev. Favorable fire rates or provisional tag counts do **not** authorize behaviour ship. See [`../../PROPOSALS/2026-10-02-interception-steer-to-stop.md`](../../PROPOSALS/2026-10-02-interception-steer-to-stop.md).
