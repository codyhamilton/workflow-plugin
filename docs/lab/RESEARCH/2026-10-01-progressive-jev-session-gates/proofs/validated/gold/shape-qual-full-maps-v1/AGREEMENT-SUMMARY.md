# Shape-qual full Maps agreement — `shape-qual-full-maps-v1`

**Date:** 2026-10-01 (Brisbane) · **Protocol:** [`TERMS.md`](../../../../TERMS.md) §11 + §14

**Weight order (Cody / WSM):** (1) shared **early signals (≤ ~120T)** + **phases / narrative shape** — **primary**; (2) recommended exit turn / earliness — **secondary**, not a hard fail.

**Corpus:** **n = 34** open-pajero-maps Claude workers with **T ≥ 75** ([`INVENTORY-shape-qual-full-maps-v1-20261001-214046.json`](../packs/INVENTORY-shape-qual-full-maps-v1-20261001-214046.json)). Packs: `shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl` (hybrid_v0, schedule `75:15`). Seats read pack rows only; no maps nicknames, no prior seat labels, no `--call-jev`.

**Seat PRs (verdicts not merged):**

| Seat | PR | Branch |
|------|-----|--------|
| Composer | [#72](https://github.com/codyhamilton/workflow-plugin/pull/72) | `lab/shape-qual-composer-20261001` |
| Sonnet | [#74](https://github.com/codyhamilton/workflow-plugin/pull/74) | `lab/shape-qual-sonnet-20261001-clean` |
| Grok | [#75](https://github.com/codyhamilton/workflow-plugin/pull/75) | `lab/shape-qual-grok-20261001` |

**Prior panel style:** [`shape-signal-agreement-SUMMARY-20261001.md`](../shape-signal-agreement-SUMMARY-20261001.md) (7-worker `shape-signal-panel-v1`, PR [#70](https://github.com/codyhamilton/workflow-plugin/pull/70)).

**Jev:** No `--call-jev`. **Hold Jev behaviour ship** until WSM green-lights after these notes (TERMS §12–§14).

---

## 1. Method

- **Population:** all 34 Maps workers in the combined inventory (no excludes for workers already in the 7-worker shortlist).
- **Seats:** three independent qualitative labels per worker (`shape_label` + `phases` + `early_signals`), one JSON verdict each under `composer/`, `sonnet/`, `grok/` on the seat branches above.
- **Early-signal window:** every cited `early_signals[].turn` ≤ **120** on all **102** seat verdicts (34 × 3); `early_signal_window_respected: true` everywhere. Post-~120 observations belong in phases/narrative, not early signals (§14).
- **Agreement scoring:** per worker, compare the three `shape_label` values. Tiers: **unanimous** (3/3), **2-of-3** (majority label), **diverge** (three distinct labels). Grok’s extra **`poll_monitor`** label is treated as a first-class shape for agreement (not folded into §11 `unclear`). Sonnet’s optional **`shape_detail`** is **not** a vote — it refines the coarse §11 enum when Sonnet kept `unclear`.
- **Signal agreement (primary):** for each worker, note early-signal **themes** that appear in ≥2 seats (compaction surge, zero Edit/Write, re-read loop, frozen narration, monitor/census wait, productive Edits early, etc.), with turn bands **75–120** where the packs support them.
- **Exit / earliness:** collected as secondary on some Composer rows; **not** used as agreement pass/fail.

---

## 2. Per-seat `shape_label` histograms

| shape_label | Composer | Sonnet | Grok |
|-------------|----------|--------|------|
| `unclear` | 23 | 32 | 24 |
| `early_thrash` | 5 | 2 | 2 |
| `late_pivot` | 6 | 0 | 4 |
| `poll_monitor` | — | — | 4 |

**Seat behaviour (interpretation):**

- **Composer** is the most willing to assign **`late_pivot`** (6) or **`early_thrash`** (5) under §11; only 23/`unclear`.
- **Sonnet** almost never uses §11 pivots/thrash on this corpus (**0** `late_pivot`, **2** `early_thrash`). It adds **`shape_detail`** on all 34 workers (finer taxonomy: `steady_build_to_commit` ×11, `bash_only_silent` ×4, `build_then_long_wait` ×4, `poll_monitor_wait` ×3, `churn_compaction_loop` ×2 for the thrash golds, etc.). Sonnet explicitly reserved **`late_pivot`** for “change of fortune after productive progress” and found **no** worker meeting that bar in-pack.
- **Grok** introduces **`poll_monitor`** (4) for monitor/census/orchestrator-standby shapes, including **`87a380bc64ff`** as requested. Grok’s **`late_pivot`** (4) aligns with Composer on some implement-then-wait tails but uses a stricter thrash bar (only **2** `early_thrash`, same pair as Sonnet).

---

## 3. Worker-level shape agreement

**Counts:** **18** unanimous · **15** two-of-three · **1** three-way diverge.

| Tier | n | Majority / pattern |
|------|---|---------------------|
| Unanimous `unclear` | 17 | Ordinary build/wait/orchestrator completions — Sonnet `shape_detail` carries the real distinction. |
| Unanimous `early_thrash` | 1 | **`ca977b9ca0dd`** only. |
| 2-of-3 `unclear` | 12 | Composer (or Grok) names pivot/thrash/poll; Sonnet stays `unclear`. |
| 2-of-3 `early_thrash` | 1 | **`92a48e004519`** (Sonnet + Grok thrash; Composer `late_pivot`). |
| 2-of-3 `late_pivot` | 1 | **`5163c22a6a3e`** (Composer + Grok). |
| Diverge | 1 | **`bb6165018de0`** — Composer `late_pivot` / Sonnet `unclear` / Grok `poll_monitor`. |

### Master table (shape votes)

Abbreviations: **thrash** = `early_thrash`, **pivot** = `late_pivot`, **poll** = `poll_monitor`.

| Worker | T | Composer | Sonnet | Grok | Tier | Majority | Sonnet `shape_detail` | Notes |
|--------|---|----------|--------|------|------|----------|----------------------|-------|
| `bb6165018de0` | 154 | pivot | unclear | poll | diverge | split | poll_monitor_wait | prior gold / spotlight |
| `036ff3ed4a89` | 161 | pivot | unclear | unclear | 2-of-3 | unclear | wait_verify_then_record |  |
| `07357f196666` | 83 | thrash | unclear | unclear | 2-of-3 | unclear | bash_only_silent |  |
| `0aab88c525de` | 192 | unclear | unclear | pivot | 2-of-3 | unclear | steady_build_then_wait |  |
| `15f24c7ba18c` | 93 | unclear | unclear | poll | 2-of-3 | unclear | orchestrator_monitor_burst | Grok-only poll |
| `5163c22a6a3e` | 90 | pivot | unclear | pivot | 2-of-3 | late_pivot | build_then_long_wait | pivot 2/3 |
| `52ea24516a6e` | 107 | pivot | unclear | unclear | 2-of-3 | unclear | build_then_long_wait |  |
| `582c23b3c6e4` | 77 | unclear | unclear | pivot | 2-of-3 | unclear | bash_only_silent |  |
| `7c99c180742e` | 100 | unclear | unclear | pivot | 2-of-3 | unclear | build_then_long_wait |  |
| `87a380bc64ff` | 89 | unclear | unclear | poll | 2-of-3 | unclear | poll_monitor_wait | prior gold / spotlight |
| `8e36f8e80baa` | 97 | unclear | unclear | poll | 2-of-3 | unclear | orchestrator_dispatch_wait | Grok-only poll |
| `92a48e004519` | 296 | pivot | thrash | thrash | 2-of-3 | early_thrash | churn_compaction_loop | prior gold / spotlight |
| `a3cc4da7e21c` | 91 | pivot | unclear | unclear | 2-of-3 | unclear | build_then_long_wait |  |
| `daf933273c8f` | 122 | thrash | unclear | unclear | 2-of-3 | unclear | silent_bash_loop_then_monitor |  |
| `de5b76cc68a6` | 94 | thrash | unclear | unclear | 2-of-3 | unclear | bash_only_silent |  |
| `e28a2428b192` | 102 | thrash | unclear | unclear | 2-of-3 | unclear | bash_only_silent |  |
| `0677f597286e` | 93 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `074c8cf22927` | 76 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `0853bc21d3aa` | 155 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `16a958631580` | 94 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `5a152464f6e5` | 119 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `6e06ab86aa72` | 123 | unclear | unclear | unclear | unanimous | unclear | poll_monitor_wait |  |
| `79a557b56a6e` | 95 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `7af2854bba92` | 99 | unclear | unclear | unclear | unanimous | unclear | orchestrator_dispatch_wait |  |
| `7b00225cb824` | 137 | unclear | unclear | unclear | unanimous | unclear | steady_build_with_perf_debug |  |
| `89608cc68603` | 125 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `91a9aa8050fb` | 86 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `9b156dbab5d9` | 93 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `9da2f589b11b` | 76 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |
| `a318f4b89a6a` | 95 | unclear | unclear | unclear | unanimous | unclear | debug_iterate_runaway_job |  |
| `ca977b9ca0dd` | 109 | thrash | thrash | thrash | unanimous | early_thrash | churn_compaction_loop | prior gold / spotlight |
| `d34bb8ba01ba` | 116 | unclear | unclear | unclear | unanimous | unclear | steady_build_with_audit_of_existing |  |
| `d84416c7c9d4` | 81 | unclear | unclear | unclear | unanimous | unclear | research_measurement |  |
| `e8aa4f271927` | 76 | unclear | unclear | unclear | unanimous | unclear | steady_build_to_commit |  |

Machine-readable twin: [`agreement-matrix.json`](agreement-matrix.json).

---

## 4. Early-signal agreement (≤ ~120T)

**Global:** no seat listed a post-120 turn under `early_signals`. Most workers cite **75–105** (first checkpoints) plus tails visible in hybrid_v0 excerpts.

**Recurring theme families (same worker, ≥2 seats):**

| Theme | Where it clusters | Agreement note |
|-------|-------------------|----------------|
| **Churn / thrash foreshadowing** | `ca977b9ca0dd`, `92a48e004519` | **Strongest signal agreement in the corpus.** ≥2 seats cite zero Edit/Write (or frozen text), `_cenc`/divide re-read loops, compaction already **10–12+** by cp75–90, Bash/Read-only histogram. Unanimous on `ca977b`; 2/3 on `92a48e` with Composer naming a later recovery arc (`late_pivot`). |
| **Composer-only thrash labels** | `07357f196666`, `daf933273c8f`, `de5b76cc68a6`, `e28a2428b192` | Composer `early_thrash`; Sonnet **`bash_only_silent`** / silent bash + monitor; Grok **`unclear`** (insufficient multi-checkpoint loop in pack). Shared **monitor_wait** or **reread** themes appear in 1–2 seats — **weak thrash consensus**, not ca977-class. |
| **Implement then external wait** | `5163c22a6a3e`, `52ea24516a6e`, `7c99c180742e`, `0aab88c525de`, `036ff3ed4a89` | ≥2 seats: **productive_edits** and/or explicit **monitor_wait** in 75–120 band. Shape split: Composer/Grok **`late_pivot`** vs Sonnet **`build_then_long_wait`** / **`wait_verify_then_record`** with §11 `unclear`. Signals agree on arc; §11 label does not. |
| **Poll / monitor standby** | `87a380bc64ff`, `bb6165018de0`, `6e06ab86aa72`, `15f24c7ba18c`, `8e36f8e80baa` | **monitor_wait** theme in ≥2 seats for `87a380`, `bb6165`, `6e06ab`. Grok **`poll_monitor`** on four workers; Sonnet **`poll_monitor_wait`** / orchestrator details; Composer often **`unclear`** or **`late_pivot`** (census completion narrative). |
| **Steady build** | 11 unanimous “boring” workers | All §11 `unclear`; Sonnet **`steady_build_to_commit`**; early signals cite Edits/Writes/tests by cp75–120 — **productive_edits** theme in ≥2 seats, no thrash family. |

**Turn-band examples (illustrative, not exhaustive):**

- **`ca977b9ca0dd`:** cp75–90 — compactions 10→16, text frozen ~167 chars, `_cenc`/divide/`_e2` re-reads, no Edit/Write (all three seats).
- **`92a48e004519`:** cp75–90 — same thrash bundle; Sonnet/Grok label thrash from cp75; Composer agrees on signals but labels **`late_pivot`** citing eventual recovery/gate closeout beyond the early window (phases, not credited as early signals).
- **`87a380bc64ff`:** sole cp75 in pack — consecutive turns waiting on compare_disc + quantisation_roundtrip monitors; Sonnet **`poll_monitor_wait`**, Grok **`poll_monitor`**, Composer **`unclear`** (dual-monitor wait, not bash-only thrash).

---

## 5. Prior golds & spotlight workers

### `ca977b9ca0dd` (T=109)

- **Shape:** unanimous **`early_thrash`** (only unanimous non-`unclear` label in n=34).
- **Signals:** textbook 3C-09 compressed runaway — zero Edit/Write, re-read loop, compaction surge, frozen narration by first checkpoints.
- **Panel echo:** same unanimous thrash story as `shape-signal-panel-v1`; full Maps corpus confirms this as the **clearest progressive-Jev stop-signal prototype**.

### `92a48e004519` (T=296)

- **Shape:** **2-of-3 `early_thrash`** (Sonnet + Grok) vs Composer **`late_pivot`** — same split family as the 7-worker panel (Composer late_pivot / Grok early_thrash / Sonnet unclear there).
- **Signals:** thrash foreshadowing by **~75–90** is shared (compaction, reread loop, frozen text); disagreement is **labeling the long middle** (recovery vs runaway), not absence of early thrash cues.
- **Exit:** secondary; do not require exit-turn match for agreement.

### `bb6165018de0` (T=154)

- **Shape:** **only three-way diverge** — `late_pivot` / `unclear` / `poll_monitor`.
- **Signals:** census **monitor_wait** from ~68–120 is shared; seats differ on whether completion at ~149 is “pivot” (Composer), benign poll shape (Grok), or on-brief wait (Sonnet `poll_monitor_wait` + `unclear`).
- **Panel echo:** majority **`unclear`** in `shape-signal-panel-v1`; full Maps adds Grok **`poll_monitor`** split.

### `87a380bc64ff` (T=89, single cp75 pack)

- **Shape:** 2-of-3 **`unclear`** vs Grok **`poll_monitor`**; Sonnet **`shape_detail` = `poll_monitor_wait`** (kept distinct per WSM).
- **Signals:** all seats anchor “waiting on both monitors” at cp75; **no** ca977-style zero-edit thrash loop in the visible prefix.
- **Recommendation:** treat **`poll_monitor`** / **`poll_monitor_wait`** as a **sibling shape family** to monitor-gated evidence runs when tuning progressive-Jev — not fold into `early_thrash`.

---

## 6. Implications for progressive-Jev (recommendations only)

1. **Hold behaviour ship; no `--call-jev`.** Qual labels are for WSM / decay-bar design (TERMS §12), not production hooks yet.
2. **High-confidence stop families:** pair **`zero Edit/Write` + compaction + fixed re-read loop + frozen narration** in the **75–105** band (`ca977b`, `92a48e`). This is the same family the 7-worker panel identified; n=34 shows it is **rare** (2 strong thrash workers, 1 unanimous).
3. **Do not over-trigger on Composer-only `early_thrash`** on **`bash_only_silent`** workers (`07357f`, `de5b76`, `e28a2428`, `daf933273c8f`) — Sonnet/Grok withhold thrash without multi-checkpoint loops; packs often end shortly after cp75.
4. **Separate poll/monitor gates from thrash:** Grok **`poll_monitor`** + Sonnet **`poll_monitor_wait`** align on **`87a380bc64ff`**, **`bb6165018de0`**, **`6e06ab86aa72`**, orchestrator bursts — use **monitor_wait early themes**, not thrash scores, for steer/handoff (TERMS §13 validation handoff).
5. **`late_pivot` is seat-sensitive:** Composer assigns it to implement-then-wait tails; Sonnet assigns **zero** `late_pivot` on this corpus. Progressive policy should prefer **shared early signals + phases** over forcing §11 pivot unanimity.
6. **Pack coverage:** many workers have **unseen tail turns** after the last checkpoint (listed in Sonnet seat SUMMARY). Agreement on **`unclear`** partly reflects **hybrid_v0 visibility limits**, not necessarily benign runs.
7. **Next tuning inputs:** weight **early_thrash signal bundles** heavily in decay; treat **`poll_monitor`** as its own cluster; keep exit-turn spread **non-blocking** (§14).

---

## 7. Explicit hold

- **No `--call-jev`** in this experiment or in downstream progressive revalidation until WSM green-lights after absorbing this agreement note.
- This PR **does not** merge seat verdict branches ([#72](https://github.com/codyhamilton/workflow-plugin/pull/72), [#74](https://github.com/codyhamilton/workflow-plugin/pull/74), [#75](https://github.com/codyhamilton/workflow-plugin/pull/75)), **does not** change TERMS, packs, or Jev code, and **does not** rewrite seat prompts.

---

## Headline findings (Phase 2 close-out)

1. **§11 `shape_label` unanimity is mostly `unclear` (17/34)** — the coarse trio is insufficient for Maps; Sonnet’s **`shape_detail`** and Grok’s **`poll_monitor`** carry the actionable taxonomy.
2. **One unanimous thrash gold: `ca977b9ca0dd`**; **`92a48e004519`** is **2/3 early_thrash** with shared cp75–90 thrash signals despite Composer **`late_pivot`**.
3. **Composer-only `early_thrash` on four short bash-silent workers** does not replicate to other seats — weak thrash consensus.
4. **`poll_monitor` / `poll_monitor_wait`** cluster on **`87a380bc64ff`** and census/orchestrator waits; keep **`87a380bc64ff`** as a **distinct poll/monitor shape**, not thrash.
5. **Early-signal window discipline held (0 violations)**; agreement should weight **shared themes in 75–120**, not exit turns — **hold Jev ship**.
