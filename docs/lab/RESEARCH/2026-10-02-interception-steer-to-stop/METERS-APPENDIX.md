# METERS-APPENDIX — batch-002 TypeSafe + stream diagnostics (Soft HOLD)

> **Soft Standard HOLD** — mechanical meter packing only. No hooks, no `:8080`, no behaviour unlock, no FP/miss scoreboard. Narrative interpretation stays in [`ANALYSIS.md`](ANALYSIS.md) ([#111](https://github.com/codyhamilton/workflow-plugin/pull/111)); pair ranking in [#109](https://github.com/codyhamilton/workflow-plugin/pull/109); refill corpus in [#110](https://github.com/codyhamilton/workflow-plugin/pull/110).

**Canonical machine meters:** [`../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/meters.json`](../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/meters.json) (`generated_at` on disk). Human-readable per-scenario list: [`../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/SCENARIO-PROGRESS.md`](../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/SCENARIO-PROGRESS.md).

---

## 1. TypeSafe scenario sweep (post–#110 meters)

| Field | Value | Notes |
|-------|------:|-------|
| `n_distinct_scenarios` | **392** | 290 non-GROWTH (×41 sessions) + 102 GROWTH (×16 eligible) |
| `n_sessions_swept` | **41** | Representative mid checkpoint / session; `window_cartesian=false` |
| `n_cells_incidental` (scored in meters) | **13,522** | Excludes stale pre-fill GROWTH rows |
| `stale_growth_rows_excluded` | **2,312** | Empty-field GROWTH rows retained in `results.jsonl` only |
| `growth_fill_version` | `growth-fill-v1` | See [`GROWTH-DESIGN-NOTES.md`](../2026-10-02-interception-trials/batch-002/GROWTH-DESIGN-NOTES.md) |
| Raw `results.jsonl` rows | **15,834** | 13,522 scored + 2,312 stale GROWTH (provenance) |
| Overall fire (scored cells) | **256 / 13,522** (**1.89%**) | Mixed 41- and 16-session denominators per scenario |

**#110 refill (growth-fill-v1):** 2,042 new cells, 0 errors; 1,632 GROWTH cells (102 scenarios × 16 sessions) → **103 fire / 1,529 defer**; 2,550 cells gated (102 × 25 tail-less sessions).

---

## 2. Scenario-level fire-rate bands (from `outcomes_by_scenario`)

Mutually exclusive bands per measured scenario (not accuracy bands):

| Band | All scenarios (392) | Filled GROWTH only (102) |
|------|--------------------:|-------------------------:|
| 0 | **334** | **77** |
| (0, 0.10] | 31 | 8 |
| (0.10, 0.25] | 16 | 8 |
| (0.25, 0.50] | 4 | 4 |
| (0.50, 0.75] | 5 | 4 |
| >0.75 | 2 | 1 |

Maximum observed scenario fire rate: **0.875**. Same table in [`ANALYSIS.md`](ANALYSIS.md) §2b.

---

## 3. Preferred GROWTH reporting cut (12 × 9) — [#109](https://github.com/codyhamilton/workflow-plugin/pull/109) / [#112](https://github.com/codyhamilton/workflow-plugin/pull/112) scope

Pair list: [`GROWTH-RANKING.json`](../2026-10-02-interception-trials/batch-002/GROWTH-RANKING.json) (`priority_pairs`, 12 scenarios).

| Join bucket | Claude-code pairs (of 16 GROWTH-eligible) | Cells per preferred scenario (driver) |
|-------------|----------------------------------------:|--------------------------------------:|
| `label_join_exact` | **9** | **12 × 9 = 108** exact-labeled-ready |
| `checkpoint_unlabeled` + `session_unlabeled` | **7** | **12 × 7 = 84** diagnostic only |
| Tail-less (gated) | 25 sessions | 0 (do not substitute empty state) |

**Post–#110 response on the 12 ranked pairs** (`growth-fill-v1` rows only, 16 sessions each → 192 cells/driver):

| Scenario | Fire / 16 |
|----------|----------:|
| `state.markers_focus` × `q.idle_tool_spin` | **9 / 16** |
| `state.markers_focus` × `q.context_thrash_compact` | 1 / 16 |
| All other 10 ranked pairs | 0 / 16 |
| **Total (16 state-valid snapshots)** | **10 / 192** |
| **Exact-labeled subset (9 snapshots)** | **6 / 108** (5 + 1 on the two firing pairs above) |
| Seven diagnostic snapshots | 4 / 84 |

Analytic selection only — [#110](https://github.com/codyhamilton/workflow-plugin/pull/110) merged before [#109](https://github.com/codyhamilton/workflow-plugin/pull/109); not a preregistered evaluation.

---

## 4. Per-stream meter sheets (Flash / Luna / Wave-0)

| Stream | `METERS.md` | Rows (landed) | Scored @ land | Soft HOLD note |
|--------|-------------|-------------:|--------------:|----------------|
| Wave-0 Flash | [`batch-002/METERS.md`](../2026-10-02-interception-trials/batch-002/METERS.md) | 240 | 240 | `window_status=unidentified`; provisional join in [`analysis/PROVISIONAL-join-summary.json`](analysis/PROVISIONAL-join-summary.json) |
| `flash-scale` | [`flash-scale/METERS.md`](../2026-10-02-interception-trials/batch-002/flash-scale/METERS.md) | 2,400 | 250 | Streaming partial |
| `flash-mid` | [`flash-mid/METERS.md`](../2026-10-02-interception-trials/batch-002/flash-mid/METERS.md) | 1,600 | 50 | Streaming partial |
| `luna-scale` | [`luna-scale/METERS.md`](../2026-10-02-interception-trials/batch-002/luna-scale/METERS.md) | 960 | 90 | Streaming partial |
| `luna-mid` | [`luna-mid/METERS.md`](../2026-10-02-interception-trials/batch-002/luna-mid/METERS.md) | 640 | 30 | Streaming partial |
| TypeSafe scenario | [`typesafe-scenario-sweep/SCENARIO-PROGRESS.md`](../2026-10-02-interception-trials/batch-002/typesafe-scenario-sweep/SCENARIO-PROGRESS.md) | — | 13,522 | Stale GROWTH excluded in `meters.json` |
| Cumulative roll-up | [`CUMULATIVE-STREAM.md`](../2026-10-02-interception-trials/batch-002/CUMULATIVE-STREAM.md) | 6,764 | 1,512 | Flash/Luna streaming status |

---

## 5. Superseded pre-fill snapshots (do not cite for GROWTH fire)

These predate `growth-fill-v1` and still use ×41 denominators or empty-field GROWTH rows:

- [`GROWTH-WAVE.md`](../2026-10-02-interception-trials/batch-002/GROWTH-WAVE.md) — replaced by §1–3 above.
- [`GROWTH-WAVE-SUMMARY.json`](../2026-10-02-interception-trials/batch-002/GROWTH-WAVE-SUMMARY.json) — includes the stale `markers_focus|silent_stall` 41/41 artifact; historical only.
