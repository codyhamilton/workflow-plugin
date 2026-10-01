# METERS — batch-002 typesafe multi-driver wave

**Generated:** 2026-10-02 01:38:48 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `typesafe`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **180**
- parse_miss: **0**; errors: **0**; fire_count: **0**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=125854 out=6878

## Framing mix
- `H1`: 180

## Harness mix
- `claude-code`: 138
- `codex`: 6
- `cursor`: 9
- `opencode`: 27

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 60 | 0.0 |
| 60 | 39 | 0.0 |
| 75 | 36 | 0.0 |
| 90 | 17 | 0.0 |
| 105 | 16 | 0.0 |
| 120 | 12 | 0.0 |

## Rating hist
- rating 0: 170
- rating 1: 10

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

