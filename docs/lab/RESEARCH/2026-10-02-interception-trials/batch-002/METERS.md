# METERS — interception trials batch-002 (Wave-0)

**Generated:** 2026-10-02 00:45:40 AEST

**Meters class:** score-ready-path **diagnostics** (clean inputs + fixed schedule). **NOT** a length-window FP/miss scoreboard — `window_status=unidentified` (R2).

**Soft Standard HOLD** — TypeSafe: **no**. Hooks: **no**. Luna: **no**.

## Protocol fixes vs batch-001

- R1: no `T_observed_session` / progress-frac / full-session length in prompt or state
- R2: no `runaway_hit` / `near_done_fp` from `f(T)`; outcome sheet unidentified
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`; at-risk / never-reached reported

## Counts

- n_sessions_independent: **22**
- n_variants (cells): **240**
- Flash batches: **24**; wall-sum **464.5s**
- Parse-miss: **0**; fire_count: **75**
- Prompt leak spotcheck hits: **0**

## Harness mix (cells)

- `claude-code`: 181
- `codex`: 12
- `cursor`: 12
- `opencode`: 35

## Maps concentration
- sessions 14/22; cells 181/240

## Survival (R3)

| t | n_at_risk | n_never_reached | fire_rate among cells at t |
|---|-----------|-----------------|------------------------------|
| 45 | 21 | 1 | 0.25 (n=84) |
| 60 | 13 | 9 | 0.2692 (n=52) |
| 75 | 12 | 10 | 0.3947 (n=38) |
| 90 | 8 | 14 | 0.375 (n=24) |
| 105 | 8 | 14 | 0.3333 (n=24) |
| 120 | 6 | 16 | 0.4444 (n=18) |

## Rating hist

- rating 0: 92
- rating 1: 73
- rating 2: 33
- rating 3: 42

## Paths

- `/home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002`
- mirror `/tmp/2026-10-02-interception-trials-batch-002`

## Ready for WSM

yes — Wave-0 batch-002 decontaminated path live; 240 cells / 22 sessions; leak_spotcheck_hits=0; FP/miss board **not** claimed (windows unidentified); TypeSafe unused; Soft Standard HOLD.

## Outcome labels (2026-10-02)

Sidecar `outcome-labels.jsonl` exists (20 labeled sessions, `chm-sol-adjudication`, `outcome-sheet-v1`). Soft HOLD: meters remain **diagnostics**; **PROVISIONAL** join only — [`../../2026-10-02-interception-steer-to-stop/ANALYSIS.md`](../../2026-10-02-interception-steer-to-stop/ANALYSIS.md) + [`../../2026-10-02-interception-steer-to-stop/analysis/PROVISIONAL-join-summary.json`](../../2026-10-02-interception-steer-to-stop/analysis/PROVISIONAL-join-summary.json). TypeSafe scenario + GROWTH cut tables: [`../../2026-10-02-interception-steer-to-stop/METERS-APPENDIX.md`](../../2026-10-02-interception-steer-to-stop/METERS-APPENDIX.md). Do not rewrite `window_status` in `results.jsonl` or claim FP/miss scoreboard.
