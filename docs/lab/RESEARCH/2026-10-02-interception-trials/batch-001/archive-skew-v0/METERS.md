# METERS — interception trials batch-001

**Generated:** 2026-10-02 00:36:59 AEST

**Soft Standard HOLD** — TypeSafe: **no**. Hooks unlock: **no**. Luna: **no**.

## Counts

- Sessions: **22**
- Cells: **180**
- Flash batches: **18** (parallel≤3, 10/call)
- Flash wall-sum: **269.4s**
- Parse-miss cells: **0**
- Fire count: **16**

## Harness mix (cells)

- `claude-code`: 36
- `codex`: 144

## Maps concentration

- Sessions maps-family: 14/22; cells: 36/180

## Outcome tags (cell-level)

- `defer_ok`: 114
- `runaway_miss_candidate`: 50
- `runaway_hit`: 10
- `premature`: 6

## Session rollup (long_runawayish)

- Hits (fire in ideal window): **1**
- Miss / outside-window longs: **2**
- Sessions with any near_done_fp cell: **0**

## Paths

- `/home/codyh/workspace/workflow-plugin/docs/lab/RESEARCH/2026-10-02-interception-trials/batch-001`
- mirror `/tmp/2026-10-02-interception-trials-batch-001`

## Remaining grid

Full cartesian would be 4×6×4=96 per checkpoint; batch-001 used 12 stratified combos × selected cps.

## Ready for WSM

yes — offline Flash lever grid burned on #96 shortlist; 180 cells / 22 sessions; outcomes near_done_fp=0, premature=6, runaway_hit=10, runaway_miss_candidate=50; TypeSafe unused; Soft Standard HOLD.

