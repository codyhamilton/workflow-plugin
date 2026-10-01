# METERS — batch-002 flash multi-driver wave

**Generated:** 2026-10-02 01:41:10 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `flash`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **240**
- parse_miss: **0**; errors: **0**; fire_count: **46**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=0 out=0

## Framing mix
- `H1`: 240

## Harness mix
- `claude-code`: 185
- `codex`: 8
- `cursor`: 12
- `opencode`: 35

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 80 | 0.1875 |
| 60 | 52 | 0.1923 |
| 75 | 42 | 0.119 |
| 90 | 24 | 0.1667 |
| 105 | 24 | 0.2083 |
| 120 | 18 | 0.3889 |

## Rating hist
- rating 0: 124
- rating 1: 61
- rating 2: 14
- rating 3: 32

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

