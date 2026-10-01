# LEAKAGE-NOTE — batch-001 (Opus R1–R3)

**Status:** **plumbing-only; contaminated (T leak)** — **not** score-ready evidence.  
**Date:** 2026-10-02 AEST  
**Soft Standard HOLD** unchanged.

## Verdict

Do **not** treat `METERS.md` / `results.jsonl` / `meters.json` from this directory (including `archive-skew-v0/`) as interception score evidence. They measure how well a judge predicts length when length (or length-derived fields) is visible.

## Adversarial BLOCKs

| ID | Issue in batch-001 | Evidence |
|----|--------------------|----------|
| **R1** | Outcome leaked into inputs | Flash prompts included `T_observed_session`. Lite states included `approx_progress_frac=cp/T`, `T_observed`, `userish_count_full_session`. |
| **R2** | Length-as-runaway reference window | `ideal_window(T)` and tags `near_done_fp` / `runaway_hit` / `runaway_miss_candidate` derived from observed T alone. |
| **R3** | T-dependent checkpoint schedules | Long sessions: `75:15`; shorter: T-proportional slices — survivorship + schedule leak. |

Also: early cell allocation skew (codex T inflation) archived under `archive-skew-v0/` — separate plumbing defect.

## Disposition

- Keep artifacts for audit / leak-ablation contrast only.
- **Wave-0 score-ready path continues as `batch-002/`** after PROTOCOL decontamination (T-independent schedule, no T fields in state/prompt, non-length outcome sheet).
- No TypeSafe; no hooks unlock; no Soft Standard unlock.
