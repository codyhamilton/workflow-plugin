> **SUPERSEDED for scoring.** This PROTOCOL allowed T leak / length windows / T-dependent schedules (Opus R1–R3). Contaminated. See `LEAKAGE-NOTE.md`. Live protocol: `../batch-002/PROTOCOL.md`.

# PROTOCOL — interception trials batch-001

**Date:** 2026-10-02 (AEST)  
**Status:** offline / Soft Standard **HOLD**  
**WSM:** GO confirmed for this scope  
**TypeSafe:** **not used** (ask CHM before any live Jev spend)  
**Hooks / Soft Standard unlock:** none

## Goal

Grow a **trial-results corpus** for holistic interception scoring:

`(state, question, response-class) → predictive rating → fire-time`

vs session length/shape (**near-done FP** vs **runaway-intercept miss**).

LLM agreement is **not** gold. Flash drives volume; Luna optional dual-label if free.

## Corpus

Source: `#96` provisional shortlist pack on master (`4ac78e6`):

- Deterministic pool **n=30** (`stats.json` → `deterministic_shortlist`)
- Flash qualitative **~18** (`SHORTLIST.md`) for diversity expansion when capacity allows

**Disclosed bias:** length-first; heavy **open-pajero-maps / claude-code** concentration in the length ranks. Batch-001 samples longer sessions first and adds non-Maps / non-CC rows from the Flash qualitative list when present.

## Lever grid (starting + exploratory)

Reuse Pilot / open-field framings as seeds; do **not** freeze one approach.

| Lever | Variants in batch-001 |
|-------|------------------------|
| **state** | `stats_only`, `hybrid_v0`, `stats_plus_delta`, `compact_focus` |
| **question** | `continue_excessively`, `steer_now`, `productive_arc`, `near_done`, `thrash_bundle`, `defer_recheck` (+ pilot tournament/pool seeds where packed) |
| **response-class** | `binary_fire`, `likert_0_3`, `four_class`, `rating_plus_offset` |

Batch-001 does **not** run the full cartesian on every checkpoint. It uses a **stratified subsample** (multi-approach) sized for tens–low hundreds of cells tonight, maximizing Flash cells first. Remaining grid documented in `METERS.md`.

## Checkpoints

Claude-code JSONL: `api_turn` index via progressive proofs `turn_index` / `snapshot_state`. Schedule preference `75:15` when `T >= 75`; else proportional early/mid/late slices. Non-CC: length-proportional slices on inventory metrics / light parses (`evidence_class: lite`).

## Scoring (offline)

For each cell: Flash returns `rating` (0–3), `fire` (bool), optional `fire_offset_turns`, `response_class_label`, brief rationale.

**Shape prior from observed T only** (not multi-model gold):

| Shape bucket | Heuristic | Ideal steer window (eval only) |
|--------------|-----------|--------------------------------|
| `short_natural` | `T < 90` | Prefer **defer** at early cps; fire = near-done/premature risk |
| `mid` | `90 <= T < 160` | Soft window ~ `[max(75, T-50), T-15]` |
| `long_runawayish` | `T >= 160` | Window ~ `[max(75, T-90), T-30]` |

Outcome tags per cell (checkpoint-level):

- `near_done_fp` — fire on `short_natural`, or fire after `T-20` on mid/long (closing risk)
- `premature` — fire before window start on mid/long
- `runaway_hit` — fire inside ideal window on `long_runawayish` (or mid)
- `runaway_miss_candidate` — defer on long at/after window start (session-level rollup uses last cps)
- `defer_ok` — defer outside miss zone / on short

Session-level rollup: first fire time vs ideal window; never-fire on long → runaway miss.

**Weights (explicit eval choice, not fact):** premature=1.0, near_done_fp=1.2, runaway_miss=1.5; hits earn credit not cost.

## Soft Standard HOLD

- No hooks unlock  
- No shipping-behaviour change  
- Offline/replay only  
- **No TypeSafe** in batch-001 unless CHM explicitly approves a tiny microbatch

## Capture layout

```
docs/lab/RESEARCH/2026-10-02-interception-trials/batch-001/
  PROTOCOL.md
  results.jsonl
  METERS.md
  grid.json
  snapshots/   # compact state packs (no full chat bodies)
  raw/         # Flash stdout batches
```

Mirror: `/tmp/2026-10-02-interception-trials-batch-001/`

## Harness

- Primary: `opencode run --model deepseek/deepseek-flash --format default '…' </dev/null`
- Optional: `codex exec -m gpt-6-luna -c model_reasoning_effort=high … </dev/null` for dual subset
- Do **not** kill long-lived OpenCode TUI (e.g. silver-chronicle on pts/5)
