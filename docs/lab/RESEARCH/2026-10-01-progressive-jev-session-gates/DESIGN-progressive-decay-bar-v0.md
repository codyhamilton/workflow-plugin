# Design — progressive decay bar + validation handoff (v0)

**Status:** **plan/hold** (2026-10-01). **Confidence: not high.**  
**Owner:** Workflow System Manager (orchestration intent). **Not shipped.** No hooks, no `--call-jev`, no changes to `gate_thresholds.py` or replay harness behaviour in this fold.

**Experiment ids (paired hold):** [`progressive-decay-bar-v1`](NEXT-EXPERIMENTS.md#primary-next--progressive-decay-bar-v1-and-validation-handoff-steer-v1-wsm-design-fold--no-harness-yet), [`validation-handoff-steer-v1`](NEXT-EXPERIMENTS.md#primary-next--progressive-decay-bar-v1-and-validation-handoff-steer-v1-wsm-design-fold--no-harness-yet).  
**Terms anchor:** [`TERMS.md`](TERMS.md) §§11–14 (especially §12 decay, §13 handoff).  
**Prerequisite met:** `shape-signal-panel-v1` Phase 2 + agreement SUMMARY ([`shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md)). Harness still blocked until this schedule is pre-registered and reviewed.

This document is the **written decay schedule + handoff steer** that [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) required before any live `confidence_min` decay or validation-phase wiring. It does **not** unlock Jev behaviour.

---

## 1. Problem

### 1.1 Fixed bar fails late stacking

Offline study cell **`P0`** uses a **fixed** decision rule `R(t)` with `confidence_min = t = 3` at every checkpoint on the `(75, 15)` schedule ([`TERMS.md`](TERMS.md) §§3, 6, 9). That is correct for the pre-registered sweep grid: one threshold, fail-open between firings, no per-round retuning.

For **live** progressive revalidation, a fixed top bar has two failure modes on long Maps-style workers:

1. **Late stacking.** Stop-signals (`runaway_pattern`, `scope_drift`, low `progress_since_prior`, plus shape/early-signal notes when §11 seats exist) can **accumulate across rounds** while `checkout_confidence` stays at 1–2. Under fixed `t = 3`, `R(t)` never fires; the counterfactual worker runs to `T` (e.g. 296 turns) even when later prefixes clearly justify checkout. TERMS §2 already notes that long transcripts get **more** checkpoint draws under a fixed per-checkpoint error rate — that helps “harder to run away” but does **not** substitute for lowering the bar when evidence stacks.

2. **Wrong action at validation inflection.** Many long runs contain a **build → validation** phase change: reactive read/fix/test (CI, lint, failing tests) rather than forward delivery against `brief_anchor`. A checkout-only instrument treats that inflection like runaway thrash. Cody’s intent (§13) is to **steer** the builder before the validation loop (wrap build, defer tests, spawn a **fresh validation agent**) when the worker is **not** yet in validation — not to hard-exit the builder at the first Jev unease. Once the worker **is** already in validation, §12 **leap** / **accumulate** applies; a third hard-exit path is out of scope without replay evidence.

The shape-signal panel shows the asymmetry: **`ca977b9ca0dd`** — unanimous `early_thrash`, exits 75–90; **`92a48e004519`** — shape split but thrash signals around ~90 in ≥1 seat ([`shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md)). Exact **A0** exit-turn unanimity remains null on most of the corpus; tuning decay or handoff against **earliness and shape** (§11) is the agreed weighting, not exact turn match.

---

## 2. Mechanism — `progressive-decay-bar-v1`

### 2.1 Rounds and schedule

- **Round index `k`:** 0 at the first checkpoint that runs `session-checkout` (or equivalent) on the progressive schedule; increments each **~15-turn** revalidation (`interval = 15`, same counter as §2 `api_turn`).
- **Default checkpoint set after handoff phase checks (§3):** continues **`first_at = 75`, `interval = 15`** — turns 75, 90, 105, … while `T` allows.
- **Decision rule unchanged in shape:** at checkpoint turn `c` on round `k`, checkout fires when `checkout_now == checkout` **and** `checkout_confidence >= t_k` ([`TERMS.md`](TERMS.md) §3 `R(t)`), with **`t_k` from the decay schedule** instead of fixed 3.

### 2.2 Pre-registered decay schedule **D0** (harness work — not in replay grid yet)

| Round `k` | First checkpoint turn (if on grid) | `t_k` = `confidence_min` | Notes |
|-----------|--------------------------------------|--------------------------|--------|
| 0 | 75 | **3** | Same as P0 first look |
| 1 | 90 | **3** | Stack signals; bar still strict |
| 2 | 105 | **2** | Accumulate path can fire with moderate confidence |
| 3 | 120 | **2** | Aligns with early-signal window top (~120T) |
| 4+ | 135, 150, … | **1** | Persistent stop-signals can exit without waiting for score 3 |

**Schedule id:** `D0`. Any change to `t_k` or turn anchors requires a new schedule id and a TERMS §12 version note before live use.

### 2.3 Leap vs accumulate

At checkpoint `c`, round `k`, bar `t_k`:

| Path | When | Meaning |
|------|------|---------|
| **Leap** | `checkout_now == checkout` **and** `checkout_confidence >= t_k` **and** the snapshot (plus, when available, multi-model **shape / early-signal / inflection** agreement) supports **near-done or clear mistake** — not a single noisy score | Clears the **current** bar without requiring weaker signals to stack across many rounds. Example: unanimous `early_thrash` with high confidence at 75–90 (`ca977`). |
| **Accumulate** | Stop-signals persist (pattern scores, shape labels, repeated thrash in delta/tail) but `checkout_confidence < t_k` at round `k` | Do **not** fire at `c`. Advance to `c + 15` with **`t_{k+1}` lower** per D0. Guarantees counterfactual exit within a bounded number of rounds if signals persist, without a turn cap that bypasses Jev. |

Leap is **not** “confidence 3 at k=0 only”; it is “meets bar **and** evidence shape agrees.” Accumulate is the **decay** half: the bar drops so stacked evidence can eventually satisfy `R(t_k)`.

### 2.4 Gold and agreement weight (decay tuning)

When interpreting leap vs accumulate or choosing among decay schedules in a **future** harness replay:

| Weight | Use |
|--------|-----|
| **Primary** | Multi-model agreement on **early signals (≤~120T)**, **shape** (`late_pivot` / `early_thrash`), and **inflection** ranges (§11) |
| **Secondary (report only)** | Exact exit turn vs `A0`, exit-turn spread across seats |

Gold for decay experiments should score **earliness vs shape ideal** (§11 `earliness`, `recommended_exit` under shape rules), **not** whether the gate matches unanimous **A0** on workers where **A0** is null. Checkout **A0** remains the P0 sweep rule; it is **not** the sole fit target for §12 live policy ([`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) gold protocol update).

---

## 3. Mechanism — `validation-handoff-steer-v1`

### 3.1 Phase checks

At **`api_turn` ≈ 50, 60, and 75** (phase detection anchors — **not** a replacement for the `(75, 15)` gold grid), run a **validation-phase** judgement (Jev or equivalent soft judge):

> Is this worker **already in validation**?  
> **Validation** = reactive read/fix/test loop (CI, lint, failing tests, fix cycles) rather than forward build or delivery against `brief_anchor`.

After turn 75, continue **session-checkout** revalidation on the §2 schedule (75, 90, 105, …). The 50/60/75 checks are **steer cadence** only ([`TERMS.md`](TERMS.md) §13).

### 3.2 Actions

| Validation answer | Worker state | Action |
|-------------------|--------------|--------|
| **Not** in validation | Builder still delivering / exploring forward work | **Steer only** — do **not** hard-exit. Inject parent steer via hook `additionalContext` (or equivalent): e.g. stop before running full test suites, wrap build artifacts, plan handoff of validation work to a **new agent**. WSM owns orchestration intent; product bytes are a later plan. |
| **Already** in validation | Reactive loop dominant | **No steer-as-exit.** Use §2 **leap** / **accumulate** and decay schedule **D0** only. Do **not** add a third hard-exit without offline replay evidence. |

Rationale: validation handoff is an ideal **inflection** (§11); build context decays once the loop becomes read/fix. Steer preserves builder output; decay-bar handles mistaken continuation **inside** validation or runaway **after** validation has started.

### 3.3 Interaction with decay rounds

- Phase checks at 50/60/75 **do not** decrement `k` or replace `t_k`; they gate **whether steer text is allowed** vs **whether only §12 applies**.
- If steer succeeds (builder stops testing, validation agent spawned), §12 rounds apply to the **validation** worker transcript separately — out of scope for v0 doc (orchestration boundary).

---

## 4. Success metrics (pre-register before harness)

### 4.1 Decay bar (`progressive-decay-bar-v1`)

Evaluated on offline replay with cell **`P_decay_D0`** = `(75, 15, hybrid_v0, Y_full, decay=D0, open, shape-weighted gold)` — **future harness**; not P0.

| Metric | Definition | Direction / gate sketch |
|--------|------------|-------------------------|
| `false_late_rate` | §8 boolean vs shape-weighted gold exit | **Lower** than fixed `P0` on workers with `T ≥ 150`, especially smoking-gun slice |
| `false_early_rate` | §8 vs same gold | **≤** `P0` + 0.05 on pooled `T ≥ 75` corpus |
| `median_overshoot` | Where both exits exist | **Strictly smaller** than fixed-bar progressive cell on shape-labeled workers (`early_thrash`, `late_pivot`) |
| `max_allowed_turns` median | §3 | **Lower** on `92a48e004519`-class runaways without rising false-early above gate |
| `within_one_interval` | §8 | **Report** alongside strict `on_time`; shape gold may not land on 15-grid |
| `leap_share` | Firings classified leap vs accumulate | **Report** — high leap on `ca977`-like; accumulate on stacked low-confidence thrash |
| `missing_rate` | §8 | **≤** P0; decay must not increase schema/shrink failures |
| Shape agreement @ fire | At `gate_exit`, do §11 seats agree on shape/signal? | **Qualitative gate** for recommending live D0 — not exact exit match |

Stratify all rates by **`T` bins** (<100, 100–150, >150) per §8.

### 4.2 Validation handoff (`validation-handoff-steer-v1`)

Offline/counterfactual until hook wiring exists; score steer **drafts** and phase labels, not live parent UI.

| Metric | Definition | Direction / gate sketch |
|--------|------------|-------------------------|
| `phase_label_agreement` | 50/60/75 validation yes/no vs panel `phase_sketch` / narrative phases (§14 when available) | **κ or α ≥ 0.40** on a **validation-boundary** field, or explicit “gold missing” |
| `steer_timeliness` | First steer checkpoint ≤ first panel inflection into verify/fix loop | **Majority** of prose workers with clear validation pivot |
| `builder_false_exit_avoided` | Count of P0-style checkouts on builder phase before validation inflection | **Lower** than P0 on `late_pivot` workers |
| `handoff_followed` | Counterfactual: validation agent would have started with cleaner prefix | **Human or Grok score** on draft usefulness (cf. cheap-analysis steer domain) |
| `decay_after_validation` | Once “in validation,” only §12 firings | **Zero** steer-only exits recorded as `gate_exit` |
| `false_steer_rate` | Steer fired while panel says still in build/delivery | **Report**; block ship if > agreed cap |
| `cost_checks` | Jev calls: 3 phase + session-checkout schedule | **Report** calls/worker vs fixed P0 |

---

## 5. What NOT to ship yet

- **No** `--call-jev`, stats-gate sweep, or live TypeSafe fan-out tied to decay D0.
- **No** Claude hook / OpenCode plugin behaviour: no `additionalContext` bytes, no `PostToolBatch` progressive install, no changes to `packages/opencode-workflow-hooks`.
- **No** edits to [`gate_thresholds.py`](../../2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py), `jev_signal_schemas.py`, `replay_progressive_gates.py` decision logic, or P0 grid constants.
- **No** new `session-checkout` questions in the resolved `session-progress` builder without a versioned experiment id.
- **No** treating shape-signal agreement alone as behaviour unlock ([`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) explicit non-goals).
- **No** revival of `parent-pull-v1` / Sonnet re-label rows as gold.
- **No** padding corpora or adopting **A_maj** / **A_gc** to justify decay tuning.
- **No** merge of decay schedule into P0 TERMS §9 cell without a lock memo and Cody acceptance.

---

## 6. Open questions for Sol (WSM draft — summarize)

Ten items for Workflow Systems / Sol review before harness pre-registration:

1. **Schedule D0 binding:** Is the proposed `k0@75 t=3 … k4+ t=1` table the right default, or should decay start only after `k ≥ 2` (105+) to protect builders longer?
2. **Leap gate:** What minimum **shape-signal** agreement (unanimous vs 2-of-3 seats) is required to classify a firing as **leap** rather than accidental early checkout?
3. **Separate question id:** Should validation-phase detection use a new TypeSafe question set (e.g. `validation-phase-v0`) instead of overloading `session-checkout`?
4. **50/60/75 vs band_exit 76:** How do phase checks interact with the closed **`band_exit`** log at turn 76 without double-steering or contradicting cheap-Jev use case 1?
5. **Steer channel ownership:** Is WSM-only `additionalContext` text sufficient, or must the driver emit structured `trigger_phase` / new-agent spawn records ([`workflow-systems.md`](../2026-09-30-workflow-systems.md) mapping)?
6. **New agent contract:** What brief and transcript slice does the validation agent receive, and who owns session id / fork semantics?
7. **Gold target for replay:** Confirm shape-weighted **earliness** supersedes **A0** for §12 acceptance while P0 sweep stays on **A0** — single repo, two fit rules.
8. **Harness cell naming:** Should `P_decay_D0` live in progressive `proofs/` or only in cheap-analysis matrix ids to avoid colliding with frozen P0 hypotheses?
9. **Inconclusive at phase checks:** If validation-phase Jev returns `inconclusive`, is the policy fail-open steer, fail-open silent, or retry at next anchor (60/75)?
10. **Confidence claim vs bar decay:** Cheap-analysis pack uses per-seat **claim confidence_points** on early signals; §12 uses **`confidence_min` decay** on checkout — Sol to confirm these stay distinct knobs or merge before live orchestration.

---

## 7. Traceability

| Artifact | Link |
|----------|------|
| Decaying bar, leap/accumulate | [`TERMS.md`](TERMS.md) **§12** |
| Validation handoff, 50/60/75 steer | [`TERMS.md`](TERMS.md) **§13** |
| Shape, early signal, inflection, earliness | [`TERMS.md`](TERMS.md) **§11** |
| Early signal ≤~120T, full Maps qual | [`TERMS.md`](TERMS.md) **§14** |
| Hold ids + unlock sketch | [`NEXT-EXPERIMENTS.md`](NEXT-EXPERIMENTS.md) **`progressive-decay-bar-v1`**, **`validation-handoff-steer-v1`** |
| Shape-signal prerequisite | [`shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md) |
| P0 fixed bar (contrast) | [`TERMS.md`](TERMS.md) §§3, 6, 9 **`P0`** |
| Closed gate constants (unchanged) | [`gate_thresholds.py`](../../2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py) (named only) |
| WSM orchestration patterns | [`workflow-systems.md`](../2026-09-30-workflow-systems.md) §§6–7 |

**Version:** v0 — design doc only. Bump version id when D0 or phase anchors change.
