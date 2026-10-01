# PROTOCOL — interception trials batch-002 (Wave-0 score-ready path)

**Date:** 2026-10-02 (AEST)  
**Wave:** Wave-0  
**Status:** offline / Soft Standard **HOLD** — protocol decontaminated vs Opus R1–R3  
**TypeSafe:** **not used** (ask CHM before any live Jev spend)  
**Hooks / Soft Standard unlock:** none  
**Scorecard header:** assessment/decision layer only; steer adherence unmeasured.

## Relation to batch-001

`batch-001/` is **plumbing-only; contaminated (T leak)**. Its meters are **not** evidence. This batch restarts Wave-0 under a fixed protocol. See `../batch-001/LEAKAGE-NOTE.md` and `../EVIDENCE-LOG.md`.

## Goal

Grow a trial-results corpus for:

`(state, question, response-class) → predictive rating → fire decision`

at **T-independent** checkpoints, on prefix-only state. Multi-approach lever grid stays open (Pilot seeds + exploratory). Flash is **policy-under-test** for volume (labelled as such), not gold. Luna optional dual later for H6 dissociation only — not agreement-as-gold.

## Corpus

`#96` provisional shortlist (det 30 + Flash ~18 qualitative capacity). Disclose Maps / CC concentration. Length-first shortlist selection bias remains (Opus R4 ESCALATE) — reported, not cured in Wave-0.

## Decontamination (R1–R3)

### R1 — no outcome leak into inputs

**Forbidden in prompt and state:**

- `T`, `T_observed`, `T_observed_session`, full-session length metrics
- `approx_progress_frac` or any `cp/T`
- `userish_count_full_session` / full-session role totals that reveal final length
- shape hints (`short_natural` / `long_runawayish`) or ideal-window fields
- any field that requires events **after** the checkpoint

**Allowed:** cumulative / delta / brief / tail built from `prefix(checkpoint)` only (progressive `hybrid_v0` / stats projections). Lite non-CC states may include prefix-local counts only.

Leakage audit: `LEAKAGE-AUDIT.md` in this directory — required before meters may be called score-ready.

### R2 — non-length outcome sheet

**Length-derived windows are not reference evidence.**  
Batch-002 does **not** emit `runaway_hit` / `near_done_fp` / `runaway_miss` from `f(T)`.

Frozen Wave-0 outcome sheet (provisional, non-length):

| Field | Values | Rule |
|-------|--------|------|
| `window_status` | `unidentified` | Default until transcript-evidence steer window exists |
| `reference_fire` | `null` | No length oracle |
| `termination_cause` | `unknown` \| later fill | Censoring note (R5); not used as score in Wave-0 |
| `diagnostic_only` | fire rate, rating hist, abstention | Among sessions **at risk** at checkpoint t |

Formal FP/miss scoreboard waits on an evidence-based window sheet (closing-stage / thrash / requirement evidence; windows may be `none` / `ambiguous`). Optional H7 (human steers) / H11 (hazard past 360) only after Wave-0 is score-ready on clean inputs.

### R3 — T-independent schedule + hazard framing

**Same schedule for every session:** checkpoints  
`FIXED_SCHEDULE = (45, 60, 75, 90, 105, 120)`  

(Candidate scaffold only — not a locked shipping cadence.)

- Emit a cell at turn t **only if** the session **survived to t** (`T >= t` for indexing purposes used solely for eligibility, never sent to the judge).
- Report `n_at_risk(t)`, `n_never_reached(t)`, and fire rate **conditional on survival to t**.
- Do not invent T-proportional schedules for short sessions.

## Lever grid

| Lever | Variants |
|-------|----------|
| **state** | `stats_only`, `hybrid_v0`, `stats_plus_delta`, `compact_focus` |
| **question** | `continue_excessively`, `steer_now`, `productive_arc`, `near_done`, `thrash_bundle`, `defer_recheck` |
| **response-class** | `binary_fire`, `likert_0_3`, `four_class`, `rating_plus_offset` (offset = diagnostic column only; scored at next real checkpoint if used) |

Stratified subsample of combos (multi-approach); full cartesian documented as remaining.

## Capture

```
docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/
  PROTOCOL.md
  LEAKAGE-AUDIT.md
  results.jsonl
  METERS.md          # plumbing vs score-ready clearly labelled
  grid.json
  snapshots/
  raw/
```

Mirror: `/tmp/2026-10-02-interception-trials-batch-002/`

## Harness

- Primary: `opencode run --model deepseek/deepseek-flash --format default '…' </dev/null`
- Do **not** kill long-lived OpenCode TUI (e.g. silver-chronicle on pts/5)
