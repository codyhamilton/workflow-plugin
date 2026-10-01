# METERS — interception trials batch-002 (Wave-0)

**Generated:** 2026-10-02 00:42:31 AEST

**Meters class:** score-ready-path **diagnostics** (clean inputs + fixed schedule). **NOT** a length-window FP/miss scoreboard — `window_status=unidentified` (R2).

**Soft Standard HOLD** — TypeSafe: **no**. Hooks: **no**. Luna: **no**.

## Protocol fixes vs batch-001

- R1: no `T_observed_session` / progress-frac / full-session length in prompt or state
- R2: no `runaway_hit` / `near_done_fp` from `f(T)`; outcome sheet unidentified
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`; at-risk / never-reached reported

## Counts

- n_sessions_independent: **22**
- n_variants (cells): **240**
- Flash batches: **24**; wall-sum **408.7s**
- Parse-miss: **0**; fire_count: **54**
- Prompt leak spotcheck hits: **0**

## Harness mix (cells)

- `claude-code`: 152
- `codex`: 33
- `cursor`: 22
- `opencode`: 33

## Maps concentration
- sessions 14/22; cells 152/240

## Survival (R3)

| t | n_at_risk | n_never_reached | fire_rate among cells at t |
|---|-----------|-----------------|------------------------------|
| 45 | 21 | 1 | 0.225 (n=240) |
| 60 | 13 | 9 | None (n=0) |
| 75 | 12 | 10 | None (n=0) |
| 90 | 8 | 14 | None (n=0) |
| 105 | 8 | 14 | None (n=0) |
| 120 | 6 | 16 | None (n=0) |

## Rating hist

- rating 0: 84
- rating 1: 102
- rating 2: 30
- rating 3: 24

## Paths

- `/home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002`
- mirror `/tmp/2026-10-02-interception-trials-batch-002`

## Ready for WSM

yes — Wave-0 batch-002 decontaminated path live; 240 cells / 22 sessions; leak_spotcheck_hits=0; FP/miss board **not** claimed (windows unidentified); TypeSafe unused; Soft Standard HOLD.

