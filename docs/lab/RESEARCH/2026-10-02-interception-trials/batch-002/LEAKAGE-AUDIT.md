# Leakage audit — batch-002 Wave-0

**Audit time:** 2026-10-02 AEST  
**Gate:** required before score-ready claim (Opus R1 mitigation)

## Prompt fields (Flash policy-under-test)

| Field | Post-checkpoint? | Status |
|-------|------------------|--------|
| `cell_id` | no | OK |
| `checkpoint` | no (current t) | OK |
| `state_variant` / `question` / `response_class` | no | OK |
| `state` (projected prefix snapshot) | no if built from prefix only | OK — verify builders |
| `T_observed_session` | **yes** | **REMOVED** (was R1 BLOCK in batch-001) |
| `shape_hint` / ideal window | **yes** | **REMOVED** |

## State fields

| Field | Source | Post-checkpoint? | Status |
|-------|--------|------------------|--------|
| `cumulative.*` from `prefix(cp)` | progressive snapshot | no | OK |
| `delta_since_prior` within schedule | prefix | no | OK |
| `brief_anchor` / `tail` excerpts | prefix | no | OK |
| `approx_progress_frac` | cp/T | **yes** | **REMOVED** |
| `T_observed` / `userish_count_full_session` | full file | **yes** | **REMOVED** |
| lite `file_lines` full-file | full file | **yes** | **REMOVED** — use prefix-only line/role counts through cp when lite |
| inventory `messages_full` as T | full session | **yes** | **REMOVED** from judge-facing state |

## Eligibility-only (never in judge payload)

| Field | Use |
|-------|-----|
| Session `T` | Survive-to-t filter (`T >= checkpoint`); meters `n_at_risk` |
| `shape_bucket(T)` | **Not used** for scoring in batch-002 |

## Outcome sheet

Length-derived `ideal_window(T)` **not** applied. `window_status=unidentified`. Diagnostic meters only until evidence-based windows exist.

## Result

Audit **PASS for R1 input leak** if runner matches this table.  
R2 scoreboard still limited (unidentified windows).  
R3 schedule fixed + at-risk reporting required in `METERS.md`.
