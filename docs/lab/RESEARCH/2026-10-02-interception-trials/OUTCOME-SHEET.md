# Outcome sheet — Wave-0 interception trials (non-length reference)

**Soft Standard HOLD** (product and hooks only). This sheet does not ship behaviour, hooks, Pilot, Standard, Max, or live in-loop Jev. It does not gate trial volume: Flash, TypeSafe, and Luna measurement waves are GO under [`../../PROPOSALS/2026-10-02-interception-steer-to-stop.md`](../../PROPOSALS/2026-10-02-interception-steer-to-stop.md). Labels in this sheet stay human-written; TypeSafe is not a labeler.

This document **freezes the labeling protocol** for Opus adversarial **R2** (closing R3’s remaining gate piece alongside batch-002’s R1-clean inputs and T-independent schedule). It does **not** populate labels for any batch. Until labeled rows exist in a sidecar file (see below), batch-002 meters stay **diagnostics only** — not a formal **near-done false-positive** or **runaway-await** scoreboard (`window_status=unidentified` in `results.jsonl`).

**Related:** [`batch-002/PROTOCOL.md`](batch-002/PROTOCOL.md) §R2, [`batch-002/LEAKAGE-AUDIT.md`](batch-002/LEAKAGE-AUDIT.md), [`../2026-10-02-interception-steer-to-stop/ADVERSARIAL-GATE-opus.md`](../2026-10-02-interception-steer-to-stop/ADVERSARIAL-GATE-opus.md) (R1–R3, R11), [`../2026-10-02-interception-steer-to-stop/RESEARCH-PACK.md`](../2026-10-02-interception-steer-to-stop/RESEARCH-PACK.md) §G.3 step 1, [`EVIDENCE-LOG.md`](EVIDENCE-LOG.md).

---

## Purpose

Wave-0 lever trials score `(state, question, response-class) → rating → fire` at **T-independent** checkpoints on **prefix-only** state. To turn fire/defer into **near-done FP** and **runaway-await** meters, we need a **reference that does not use session length as evidence**.

Forbidden as reference evidence (R2):

- `ideal_window(T)`, `shape_hint`, or any window derived from **final** turn count `T`
- Rules of the form “fire between T−90 and T−30”, “near-done after T−20”, or `approx_progress_frac = cp/T`
- Using **whether a checkpoint exists** as a proxy for length band (R3 already fixes schedule; labels must not reintroduce survivorship as truth)

Allowed: transcript and deliverable observables through a stated review horizon (full session transcript for **labeling only**, never copied into judge state or prompts).

---

## Core concepts (observable, not length)

### Near-done (closing-stage protection)

A session (or checkpoint **t**) is **near-done** when the transcript and artifacts show **closing work with demonstrated value remaining**, such that steering toward stop at **t** would likely displace completion, validation, or delivery — **independent of how many turns the session eventually runs**.

**Positive observables (non-exhaustive; cite turns in rationale):**

- Explicit user or brief acceptance criteria nearly satisfied; final verification, test fix, or packaging in flight
- Edits that land checkable artifacts (tests passing, build green, PR/diff ready) with **narrow** remaining scope named in recent assistant turns
- Monotonic progress toward a stated deliverable in the **last N prefix turns** (edits, decisions that narrow scope — not mere reads)

**Not sufficient alone:**

- High turn count or “long session”
- High context / compaction without a thrash pattern (see runaway-like)
- Flash/Luna **rating** or **fire** on the same cell

### Runaway-like continuation (“would excessive continuation continue?”)

**Runaway-await** labeling asks: at checkpoint **t**, is there evidence that **continuing the same worker on the same arc** is likely to accumulate **avoidable** turns — repetition, thrash, post-boundary polish, or scope expansion **without** new checkable progress — such that a **well-timed steer toward stop** would have been useful?

Aligns with adversarial **R11** sketch: a long productive session is **not** runaway by definition. Require **transcript evidence** of waste or unjustified continuation for at least a **minimum span** (Wave-0 default: **≥ 8 assistant turns** in the labeling rationale showing the pattern, or an equivalent deliverable stall — tunable in sidecar `protocol_rev` without changing judge inputs).

**Positive observables (non-exhaustive):**

- **Thrash / repetition:** same paths re-read without new facts; retry loops; poll/sleep cycles that do not change plan
- **Low checkable progress:** intervals with no edit, no changed test outcome, no decision narrowing the brief (compare to [`../2026-10-01-progressive-jev-session-gates/GOLD-LABEL-RUBRIC.md`](../2026-10-01-progressive-jev-session-gates/GOLD-LABEL-RUBRIC.md) patterns — **different instrument**; do not reuse Jev question text as the label prompt)
- **Post-boundary overrun:** work continues after an explicit “done / ship / stop” boundary in transcript or deliverable state
- **Scope drift:** latest turns pursue a different task from the brief anchor

**Natural completion:** session ends with deliverable met and no runaway-like tail → ideal steer window may be **`none`** (deferral was correct; fire would be harmful).

### Ideal steer window (reference for timing meters)

For each labeled **session** (and optionally per checkpoint **t**), reviewers may record an **earliest useful steer window** expressed only as **turn indices** justified by **transcript citations**, not by `f(T)`:

| `ideal_steer_window` | Meaning |
|----------------------|---------|
| `none` | No steer toward stop was appropriate (natural completion or productive arc throughout) |
| `[t_start, t_end]` | Inclusive turn range where steering would have been **useful** without sacrificing closing value already underway at `t_start` |
| `ambiguous` | Competing interpretations; retain uncertainty (counts toward coverage, not toward a single FP/miss verdict without adjudication) |

Windows may be **`none`** or **`ambiguous`**. Length alone **never** implies `[T−90, T−30]`.

---

## Session-level label schema (sidecar)

Labels live in **`batch-002/outcome-labels.jsonl`** (one JSON object per `session_id` when labeling begins). **Do not** backfill invented values into `results.jsonl`. Cells keep `window_status: "unidentified"` and `outcome_tag: null` until a batch-wide label pass completes and meters are regenerated from the join.

| Field | Type | Allowed values / notes |
|-------|------|-------------------------|
| `session_id` | string | Must match `grid.json` / `results.jsonl` |
| `label_status` | enum | `not_labeled` \| `labeled` \| `excluded` (corrupt transcript, policy) |
| `labeler` | string | Human id or role (not `deepseek-flash`, not Luna gold) |
| `labeled_at` | ISO date | Audit trail |
| `protocol_rev` | string | e.g. `outcome-sheet-v1` (this doc) |
| `termination_cause` | enum | `unknown` \| `natural_completion` \| `user_stop` \| `human_steer` \| `cap_or_compaction` \| `crash_or_abort` \| `other` (R5 censoring note; not a Wave-0 score by itself) |
| `human_steer_count` | int \| null | Count of mid-session human redirects in transcript |
| `near_done_at_checkpoint` | map | Keys: checkpoint turns from `FIXED_SCHEDULE`; values: `yes` \| `no` \| `ambiguous` — **prefix through t only** when deciding each key |
| `runaway_like_at_checkpoint` | map | Same keys; `yes` \| `no` \| `ambiguous` |
| `ideal_steer_window` | `none` \| `[int,int]` \| `ambiguous` | Session-level default; optional override per checkpoint in `ideal_steer_window_by_cp` |
| `ideal_steer_window_by_cp` | map | Optional; keys = checkpoint **t**; values as above |
| `pattern_tags` | string[] | Subset of: `closing_stage`, `productive_mid`, `thrash`, `low_progress`, `scope_drift`, `post_boundary`, `natural_completion` |
| `rationale` | string | ≤ 200 words; must cite turn indices or artifact facts — **not** final T |
| `independence` | object | `{ "used_flash_rating": false, "used_flash_fire": false, "used_leaked_fields": false }` — attestation |

**Who labels:** a **human reviewer** (or adjudication panel) using full transcript + deliverables. **Forbidden:** Flash/Luna as reference gold; any field from the trial **judge payload** or `rating`/`fire`/`rationale` from the same cell as input to the label decision.

**Independence from judge rating:** labelers must not open `results.jsonl` for the session until their draft label is written from transcript evidence, or must use a blind bundle (transcript + prefix snapshots only). Agreement between label and Flash is **diagnostic only** (H6 path), not success.

---

## Checkpoint join (cells → meters without leakage)

1. **Eligibility (already in batch-002):** emit/score cells at turn **t** only if session survived to **t** (`T ≥ t` in runner — **eligibility only**, never in judge payload).
2. **Label join (after sidecar exists):** for each cell at `(session_id, checkpoint t)`, read `near_done_at_checkpoint[t]` and `runaway_like_at_checkpoint[t]` and `ideal_steer_window(_by_cp)`.
3. **Set `window_status` on derived meter rows only** (in `METERS.md` / a post-label report — not by silently rewriting historical `results.jsonl` without a documented migration):

| Meter | Definition (when labels exist) |
|-------|--------------------------------|
| **near_done_fp** | `fire=true` at **t** while `near_done_at_checkpoint[t]=yes` |
| **runaway_hit** | `fire=true` at **t** while **t** lies inside labeled `ideal_steer_window` (or per-cp window) and window ≠ `none`/`ambiguous` |
| **runaway_miss** | `fire=false` at **t** while `runaway_like_at_checkpoint[t]=yes` and labeled window exists and **t** is inside window |
| **productive_interrupt** | `fire=true` while near-done **no** and runaway-like **no** at **t** (report separately) |

When `ideal_steer_window` is `none` or `ambiguous`, or `label_status≠labeled`, meters remain **`diagnostic_only`**; do not emit FP/miss leaderboard rows.

4. **No leakage:** sidecar fields and full-session transcript used for labeling **must not** be merged into `state` builders, prompts, or `snapshots/` used for new judge calls. Updating labels never changes prefix snapshots retroactively for re-judging unless a **new** batch id is forked.

---

## batch-002 status (this land)

| Item | Status |
|------|--------|
| R1 leakage audit | PASS (`LEAKAGE-AUDIT.md`) |
| R3 T-independent schedule | Fixed `(45, 60, 75, 90, 105, 120)` + at-risk reporting (`METERS.md`) |
| R2 outcome sheet **protocol** | **Landed** (this file) |
| `outcome-labels.jsonl` | **Not created** — **no session labels** |
| `results.jsonl` | All cells: `window_status=unidentified`, `outcome_tag=null` |
| FP/miss scoreboard | **Not claimed** — meters diagnostic until labels exist |

---

## Explicit non-authorization

This sheet does not unlock hooks, Pilot, Standard, Max, or live in-loop Jev. TypeSafe trial waves are specified in the white paper and may run before labels exist. Favorable future FP/miss numbers do not release the product hold. batch-002 stays off the FP/miss board until human labels are published and joined under this schema.
