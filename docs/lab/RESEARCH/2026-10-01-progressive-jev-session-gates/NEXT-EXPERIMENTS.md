# Next experiments — progressive Jev gold labeling

**Confidence: not high.** H5 failed on P0 (α = 0.1189, **A0 null**) and on experiment **(c)** expansion (α = **0.0000** on 3×20, **A0 null**). Experiment **(d)** thrash-screen **passes** H5 on its own 3×12 table (α = **0.8276**) with **A0 = 90** on `ca977b9ca0dd` only. Experiment **(e)** thrash-expand is a **miss**: strict ca977 shape empty on the remaining maps pool; best-available panel **A0 null** on all three workers; **0/5** checkout on every seat. Expand-only α is **undefined** (all `not_yet`; a De=0 convention of 1.0 is not a pass). Combined (d)+(e) is 17 prefixes, α = **0.8377**, and still **one** non-null A0. Experiment **(f)** cross-project ca977 screen is **blocked** (empty). **No hook change.**

**Gold protocol update (Cody 2026-10-01):** experiment **`shape-signal-panel-v1`** **supersedes** the unanimous A0 / ≥2 A0 gate as the primary next measurement. Do **not** require three-model exact exit agreement. Multi-model agreement on early signals / shape / inflections is primary; exit-turn spread is secondary. **Panel + agreement done** — see [`shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md). **Hold Jev behaviour ship** and do **not** `--call-jev` until WSM progressive revalidation + validation handoff ([`TERMS.md`](TERMS.md) §§12–13) have a pre-registered decay schedule / harness design. Definitions: [`TERMS.md`](TERMS.md) §§11–13.

## Completed — experiment **(b)** `sonnet-relabel-parent-pull-v1` (**FAIL**)

**Status:** done. **Outcome:** scorecard **fail** — stop rule **1 (over-fire)**.  
**Artifacts (research only, not gold):** [`proofs/validated/gold/p0-checkout-verdicts-sonnet-relabel-20261001.jsonl`](proofs/validated/gold/p0-checkout-verdicts-sonnet-relabel-20261001.jsonl), [`p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json`](proofs/validated/gold/p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json). Merged via PR #46.

| Scorecard row | Result |
|---------------|--------|
| Rule 1 — checkout at `92a48e004519` **180, 195, 210** | **Pass** (all three true) |
| Rule 2 — **0** Sonnet checkouts on **13** hold-out prefixes | **Fail** — **1** hold-out checkout at **`92a48e004519@255`** |
| Rule 3 — α ≥ 0.40 | Not evaluated as pass (rules 1–2 did not both pass) |

**Reported (non-failing):** Sonnet checkout on all five Grok-only cps **105–165** on `92a48e004519` (5/5). Total Sonnet checkouts on that worker: **9** (105–210 plus **255**).

**Consequences (stop rule 1):**

1. Discard the `parent-pull-v1` / `sonnet-relabel` rows as gold. They do **not** replace signed `p0-checkout-verdicts-20261001.jsonl` (`reviewer_final`).
2. Do **not** start a Jev or stats-gate sweep.
3. Do **not** adopt **A_maj** or **A_gc** as the fit target ([`p0-alt-gold-targets-20261001.json`](proofs/validated/gold/p0-alt-gold-targets-20261001.json)).
4. Leave the draft rubric delta at the bottom of [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) **not in force**. Do not schedule a second Sonnet run with the same paragraph (stop rule 2 in the archived protocol below).

**CHM hint (not a pass):** If this seat were substituted into the 3×21 panel, nominal Krippendorff α would rise to about **0.5674** ([`panel_recompute_hint_for_WSM`](proofs/validated/gold/p0-checkout-verdicts-sonnet-relabel-SUMMARY-20261001.json)). That α hint does **not** override stop rule 1: one hold-out checkout still discards the run as gold regardless of α.

Signed P0 panel numbers in [`PANEL-FINDINGS-20261001.md`](proofs/validated/gold/PANEL-FINDINGS-20261001.md) are unchanged (**A0 null**, α **0.1189**).

### Archived protocol — (b) Sonnet re-label under `parent-pull-v1` (for audit)

Primary measurement after H5: re-label the Sonnet seat on the same 21 P0 prefixes with the draft parent-pull delta. Inputs were hybrid_v0 packs (`p0-judge-packs-20261001-194107.jsonl`), not the gitignored gold-bundle JSONL.

<details>
<summary>Scorecard and stop rules (as run 2026-10-01)</summary>

| Set | Checkpoints | Rule |
|-----|-------------|------|
| Required Sonnet checkout | `92a48e004519` at **180, 195, 210** | All three true |
| Hold-out, Sonnet stays `not_yet` | `92a48e004519` at **75, 90, 225, 240, 255, 270, 285** (7) and `bb6165018de0` at **75…150** (6) | **13** prefixes, zero Sonnet checkouts |
| Reported either way | `92a48e004519` at **105, 120, 135, 150, 165** | Grok-only cps; publish count only |

Stop rules included: over-fire on hold-out → discard as gold; no second identical Sonnet run; island miss at 180/195/210; α &lt; 0.40; blocked bundle; no behaviour ship.

</details>

---

## Completed — experiment **(c)** `corpus-expand-hybrid-panel-original` (**H5 not passed; gold unusable for A0**)

**Status:** done (2026-10-01). **Artifacts:** three-seat expansion JSONLs under [`proofs/validated/gold/`](proofs/validated/gold/) (`expansion-checkout-verdicts-{sonnet,composer,grok}-20261001.jsonl`, 20 rows each, same pack ids); agreement [`expansion-panel-agreement-20261001.json`](proofs/validated/gold/expansion-panel-agreement-20261001.json); human summary in [`PANEL-FINDINGS-20261001.md`](proofs/validated/gold/PANEL-FINDINGS-20261001.md) §(c).

| Gate | Result |
|------|--------|
| Corpus | **3** workers labeled (`0aab88c525de`, `036ff3ed4a89`, `0853bc21d3aa`), **20** pooled `75:15` prefixes |
| Panel | Sonnet **0**/20 checkout; Grok **0**/20; Composer **1**/20 (`036ff3ed4a89@135` only) |
| **A0** | **null** on all three expansion workers (no unanimous checkout prefix) |
| H5 (expansion-only 3×20) | Krippendorff α_nominal = **0.0000** (< 0.40) — **fail** |
| Positive-class mass | **1** total `checkout_recommended=true` across 60 seat-labels |

**Interpretation:** Raw pairwise agreement on expansion is **95–100%** (almost all `not_yet`), but that is agreement-on-false, not usable unanimous gold. A single Composer-only checkout at `036ff3ed4a89@135` prevents any **A0** exit. **Do not** run a Jev sweep. P0 numbers (α **0.1189**, **A0 null** on smoking guns) are unchanged.

**Consequences:** Treat expansion labels as research corpus only until a follow-on design yields non-null **A0** or an explicitly pre-registered alternate gold rule. Do **not** return to `parent-pull-v1` without a new experiment.

### Archived protocol — (c) corpus + original-rubric panel (for audit)

**Goal:** enlarge the labeled corpus under the **original** rubric (body of [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) **without** the draft parent-pull delta), then re-run the **three-seat** panel on **hybrid_v0** judge packs. Not a Jev tuning sweep.

### Why (c) now

Experiment **(b)** showed that tightening Sonnet with `parent-pull-v1` on packs **over-fires** (hold-out @255 plus checkout on all Grok-only 105–165). Rubric revision on the same two workers is blocked until the panel has more sessions. [`TUNING-PLAN.md`](TUNING-PLAN.md) already requires **≥ 2** additional `T >= 75` gold workers before interpreting H1; only `92a48e004519` and `bb6165018de0` are labeled today.

**(a)** (adopt `A_maj` / `A_gc`) stays **not chosen** — same as before (b): fit on n = 1 positive worker, and stop rule 1 forbids adoption after (b)’s fail.

### Corpus expansion (step 1)

Build commit-safe **hybrid_v0** packs (`N=8`, excerpt 400) for **at least two** additional open-pajero-maps workers with **T ≥ 75**, same schedule **`75:15`**, using [`proofs/build_gold_judge_packs.py`](proofs/build_gold_judge_packs.py) against gitignored ubuntu-raw gold-bundles (or mounted transcripts). Redacted fixtures already in repo:

| short_id | T | Fixture (redacted) | Priority |
|----------|--:|--------------------|----------|
| `0aab88c525de` | 192 | [`maps-5h-workers/0aab88c525de.jsonl`](../../2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/0aab88c525de.jsonl) | **P1** |
| `036ff3ed4a89` | 161 | [`maps-5h-workers/036ff3ed4a89.jsonl`](../../2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/036ff3ed4a89.jsonl) | **P1** |
| `0853bc21d3aa` | 155 | redact from Ubuntu when present (not in fixtures manifest yet) | optional third |

Keep existing P0 packs under [`proofs/validated/gold/packs/`](proofs/validated/gold/packs/). Emit per-worker `*-judge-packs-*.jsonl` plus an updated combined manifest in `packs/` (new date stamp). Document checkpoint counts per worker in a short `packs/README` addendum.

**Blocked:** if ubuntu-raw gold-bundles are absent for a chosen worker, record **blocked** for that worker; do not substitute unredacted paths in cloud seats.

### Panel (step 2)

1. **Rubric:** [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) **original** text only — **omit** the “Draft delta — not in force” section and any `parent-pull-v1` wording.
2. **Seats:** same three as P0 — Sonnet 5.5 (`reviewer_final` chain or independent seat), Composer 2.5, Grok 4.7 high — each row from hybrid_v0 packs only ([`packs/README.md`](proofs/validated/gold/packs/README.md)).
3. **Schedule:** `first_at=75`, `interval=15` on every expanded worker; retain the 21 P0 rows in the pooled agreement file (do not overwrite signed P0 Sonnet JSONL with (b) relabel rows).
4. **Metrics:** recompute **A0**, pairwise κ, and pooled nominal α on the **enlarged** 3×N table. H5 floor remains **α ≥ 0.40** on the pooled panel.
5. **Explicit non-goals:** no `--call-jev`; no stats-gate sweep; no hook or plugin edits; do not adopt **A_maj** / **A_gc** unless pre-registered in a separate decision.

### Success sketch (pre-registration light)

| Gate | Criterion |
|------|-----------|
| Corpus | ≥ **2** new workers with full `75:15` pack rows committed under `packs/` |
| Panel | Three independent seats on all new checkpoints |
| H5 | Pooled α **≥ 0.40** on the combined P0 + new workers |
| Gold rule | Report **A0** per worker; unanimous exit may still be null on some workers |

Failure to clear α after expansion does **not** authorize a return to `parent-pull-v1` without a new explicit experiment. Confidence stays **not high** ([`HYPOTHESIS.md`](HYPOTHESIS.md)).

<details>
<summary>Stop rules (c) — as run</summary>

1. **Under-corpus.** Fewer than two new workers labeled → status **blocked**, not a rubric pass/fail.
2. **Rubric leak.** Any seat prompt includes the parent-pull draft, other seats’ labels, or target turns → discard that worker’s panel and re-run.
3. **No Jev.** Do not interpret H1–H4 / H6–H7 from Jev dry-run or live cache until H5 clears on the enlarged gold table.
4. **(b) rows.** Never promote `p0-checkout-verdicts-sonnet-relabel-*.jsonl` to gold.

</details>

---

## Completed — experiment **(d)** `ubuntu-thrash-screen-before-pack-v1` (**H5 pass on 3×12; A0 on one worker; Jev still blocked**)

**Status:** packs + panel done (2026-10-01). **Artifacts:** hybrid_v0 packs [`proofs/validated/gold/packs/thrash-screen-judge-packs-20261001-204508.jsonl`](proofs/validated/gold/packs/thrash-screen-judge-packs-20261001-204508.jsonl) (12 rows); seat JSONLs `thrash-screen-checkout-verdicts-{sonnet,composer,grok}-20261001.jsonl`; agreement [`thrash-screen-panel-agreement-20261001.json`](proofs/validated/gold/thrash-screen-panel-agreement-20261001.json); human summary in [`PANEL-FINDINGS-20261001.md`](proofs/validated/gold/PANEL-FINDINGS-20261001.md) §(d); scorecard [`thrash-screen-panel-SCORECARD-20261001.md`](proofs/validated/gold/thrash-screen-panel-SCORECARD-20261001.md).

| Gate | Result |
|------|--------|
| Corpus | **3** screened workers, **12** pooled `75:15` prefixes (`ca977b9ca0dd` 3, `daf933273c8f` 4, `7b00225cb824` 5) |
| Panel | Sonnet **3/12** checkout; Composer **2/12**; Grok **2/12**. All positive labels are on `ca977b9ca0dd` |
| **A0** | **90** on `ca977b9ca0dd` (Sonnet alone at 75; unanimous at 90 and 105). **null** on `daf933273c8f` and `7b00225cb824` |
| H5 (thrash-only 3×12) | Krippendorff α_nominal = **0.8276** (≥ 0.40) — **pass** |
| Pairwise κ | sonnet↔composer **0.75**; sonnet↔grok **0.75**; composer↔grok **1.0** |
| Jev | **Blocked.** α clears the floor and only one worker has non-null **A0** |

**Interpretation:** The screen’s rank-1 worker (no Edit/Write, high reread) is the first new unanimous gold exit in this study. Ranks 2–3 stayed `not_yet` on every seat. High α here is real agreement on that one worker’s checkout bit, not the expansion prevalence paradox (α **0.0000**). It is still one exit turn. **Do not** run a Jev or stats sweep. P0 (α **0.1189**, **A0 null**) and expansion (**A0 null**) are unchanged.

**Consequences:** Keep these labels as research gold for `ca977b9ca0dd@90` only. Do not treat thrash-only α as a pass of the original P0 H5 table. Do not ship behaviour.

### Archived protocol — (d) thrash screen before pack (for audit)

**Status at planning:** plan. **Goal:** before building more hybrid_v0 judge packs, **screen** the Ubuntu maps worker enum (`ubuntu-raw` dry-run thrash tables + `replay_progressive_gates` metrics) for sessions that already look **runaway / low_progress / context_thrash**-like at `75:15`, instead of sampling additional **T ≥ 75** workers at random. Label only workers that pass the screen (expect checkout disagreement mass similar to `92a48e004519`, not census-wait tails like `0aab88c525de` / `bb6165018de0`).

### Why (d) now

Experiment **(c)** met the corpus-size gate but added **no** unanimous gold: **A0** stayed null everywhere and only **one** checkout bit fired across 60 seat-labels. High agreement on `not_yet` does not repair H5 or unlock **A0**. Re-pooling P0 smoking guns with expansion under one combined α still leaves **A0 null** on all five workers — that path is **not** chosen as primary.

### Protocol sketch

1. **Screen:** Rank workers with `T ≥ 75` using committed [`proofs/validated/ubuntu-raw/*-dry-run-thrash-table-*.json`](proofs/validated/ubuntu-raw/) signals (re-read loops, peak ctx, tool histogram skew) plus maps fixtures manifest. Publish a ranked shortlist (top **N**, pre-register **N** before labeling).
2. **Pack:** Build hybrid_v0 packs only for shortlisted workers ([`build_gold_judge_packs.py`](proofs/build_gold_judge_packs.py)); keep P0 + expansion packs read-only.
3. **Panel:** Same three seats and original rubric as (c); target at least **2** new workers with **≥1** non-null per-seat earliest checkout among Sonnet/Grok/Composer before expecting **A0**.
4. **Metrics:** Report **A0** per worker and pooled nominal α on new prefixes; H5 floor unchanged (**≥ 0.40**). **No Jev sweep.**

### Alternate (not primary) — not chosen

**`combined-panel-p0-expansion-smoking-gun-v1`:** recompute agreement on **P0 + expansion (41 cps)** with `92a48e004519` in the same table — diagnostic only; does not fix **A0 null**. Still not primary after (d): thrash-only H5 passed, but the blocker is a single **A0**, which pooling with null-A0 tables does not repair.

---

## Completed — experiment **(e)** `ubuntu-thrash-high-score-expand-v1` (**miss: zero checkouts, no second A0**)

**Status:** packs + panel done (2026-10-01). **Outcome:** **miss.** Strict ca977 shape was empty on the remaining maps pool. The best-available research panel added **no** checkout and **no** second non-null **A0**.

**Artifacts:** hybrid_v0 packs [`proofs/validated/gold/packs/thrash-expand-e-judge-packs-20261001-210125.jsonl`](proofs/validated/gold/packs/thrash-expand-e-judge-packs-20261001-210125.jsonl) (5 rows); seat JSONLs `thrash-expand-e-checkout-verdicts-{sonnet,composer,grok}-20261001.jsonl`; agreement [`thrash-expand-e-panel-agreement-20261001.json`](proofs/validated/gold/thrash-expand-e-panel-agreement-20261001.json); combined (d)+(e) [`thrash-de-panel-agreement-20261001.json`](proofs/validated/gold/thrash-de-panel-agreement-20261001.json); human summary in [`PANEL-FINDINGS-20261001.md`](proofs/validated/gold/PANEL-FINDINGS-20261001.md) §(e); scorecard [`thrash-expand-e-panel-SCORECARD-20261001.md`](proofs/validated/gold/thrash-expand-e-panel-SCORECARD-20261001.md).

| Gate | Result |
|------|--------|
| Shape | **Miss.** Remaining maps `T≥75` after excludes: n=26. Strict ca977 (no Edit/Write ∧ max reread ≥ 8 ∧ compact ≥ 8): **n_ca977_shape = 0** |
| Corpus | Best-available N=3 packed anyway: `e8aa4f271927` (1 cp), `5163c22a6a3e` (2), `a318f4b89a6a` (2) → **5** prefixes. Not a shape-gate pass |
| Panel | Sonnet **0/5** checkout; Composer **0/5**; Grok **0/5**. Earliest checkout **null** on every worker and every seat |
| **A0** | **null** on `e8aa4f271927`, `5163c22a6a3e`, and `a318f4b89a6a` |
| H5 (expand-only 3×5) | Nominal α **undefined** (all `not_yet`; Do = De = 0). `h5_pass` **false**. A De=0 convention of **1.0** is recorded and is **not** a pass |
| (d)+(e) | **17** prefixes. α = **0.8377** (numeric floor only). Non-null **A0** count = **1** (`ca977b9ca0dd` @ **90**) |
| Jev | **Blocked.** Need ≥ 2 non-null A0. Combined `h5_pass` does not unlock a sweep |

**Interpretation:** The open-pajero-maps remainder does not contain another ca977 twin, and labeling the nearest substitutes produced unanimous `not_yet`. High raw agreement (100%, κ 0) is the constant-table prevalence case, the same family as expansion’s agreement-on-false, with even less positive-class mass (zero true labels). The combined α lift **0.8276 → 0.8377** is those five `not_yet` prefixes. **Do not** run a Jev or stats sweep. P0 and expansion numbers are unchanged. Do not ship behaviour.

**Consequences:** Keep (d)’s `ca977b9ca0dd@90` as the only new unanimous gold exit. Do not pack further maps near-misses. Do not treat expand-only α, or the combined numeric H5 pass, as a gold unlock.

### Archived protocol — (e) high-score expand (for audit)

**Goal at planning:** pack and label more workers that match the shape that produced **A0** in (d) — rank-1 `ca977b9ca0dd` (no Edit/Write, high max-reread, high compaction) — and hold Jev until a second worker has non-null **A0**.

The screen was empty, so the run packed a pre-registered best-available panel instead of recording blocked. That panel is the miss above. The Jev gate in the sketch was not waived: (e) did not add a second A0, so no sweep was run.

<details>
<summary>Protocol sketch (as planned 2026-10-01)</summary>

1. Screen remaining Ubuntu maps workers with `T ≥ 75`, excluding already labeled ids. Prefer no Edit/Write, high max-reread, and high compaction. Deprioritize sleep/poll and brief-mandated Bash monitors.
2. Pre-register N before labeling. Pack hybrid_v0 (`75:15`) for workers that meet the stricter shape. If fewer than two meet the shape, record **blocked**; do not pad with poll-class workers.
3. Same three seats and original rubric as (d). Prior JSONLs read-only.
4. **A0** per new worker and nominal α on the enlarged thrash table. H5 floor ≥ 0.40.
5. No Jev or stats sweep inside (e). A later sweep only after thrash-table α ≥ 0.40 **and** ≥ 2 workers with non-null **A0**.

</details>

---

## Completed — experiment **(f)** `cross-project-ca977-shape-screen-v1` (**blocked: empty cross-project screen**)

**Status:** **blocked** (2026-10-01). **Goal (as run):** find a second worker with the ca977 shape (no Edit/Write ∧ high max-reread ∧ high compaction ∧ `T ≥ 75`) in **other** Ubuntu Claude project directories, then pack and label only shape hits. The ≥2 A0 Jev gate here is **superseded** by `shape-signal-panel-v1` (signal/shape agreement primary).

**Screen result:** nine non-maps `~/.claude/projects/` dirs on Ubuntu → **0** subagent/worker JSONLs → **0** T≥75 candidates → **n_ca977_shape = 0**. No packs. No panel. Artifacts: [`proofs/validated/ubuntu-raw/SUMMARY-ubuntu-raw-cross-project-ca977-f-20261001-211725.json`](proofs/validated/ubuntu-raw/SUMMARY-ubuntu-raw-cross-project-ca977-f-20261001-211725.json), [`proofs/validated/gold/packs/SUMMARY-cross-project-ca977-f-20261001-211725.md`](proofs/validated/gold/packs/SUMMARY-cross-project-ca977-f-20261001-211725.md). Fall through to **`hold-until-new-maps-sessions`**. Holding does not unlock Jev.

### Why this was primary (superseded by `shape-signal-panel-v1`)

The maps remainder is exhausted for ca977 twins. (e) screened the remaining open-pajero-maps `T≥75` pool (n=26) and the strict shape returned **zero** workers. The best-available substitutes were then labeled and added **zero** checkouts. Packing more of that remainder repeats a miss. A second **A0** has to come from sessions that were not in that maps enum: other project directories on the same Ubuntu Claude tree, or new maps sessions that do not exist yet. Looking at the other directories is the measurement that can still add a shape-matched worker. Waiting is the fallback when that screen is also empty.

### Protocol sketch

1. **Screen:** Enumerate Ubuntu `~/.claude/projects/` directories other than `-home-codyh-workspace-open-pajero-maps`. Same dry-run thrash metrics as (d)/(e). Gate: `T ≥ 75` ∧ no Edit/Write ∧ max reread ≥ 8 ∧ compaction ≥ 8 (the empty (e) shape). Exclude every worker already labeled in P0, (c), (d), and (e). Publish the ranked shape hits before packing.
2. **Do not pad.** If fewer than two workers pass the shape gate, record **blocked** and stop. Do not pack best-available near-misses. (e) already showed that padding adds prefixes and no **A0**. Fall through to the hold alternate below.
3. **Pack:** hybrid_v0 (`75:15`) only for shape hits. Keep P0, expansion, (d), and (e) JSONLs read-only.
4. **Panel:** same three seats and original rubric (no `parent-pull-v1`).
5. **Metrics:** **A0** per new worker and nominal α on the enlarged thrash table. H5 floor unchanged (≥ 0.40). An all-`not_yet` table has **undefined** α; a De=0 convention of 1.0 is not a pass and not a gold unlock.
6. **Jev gate (explicit):** no Jev sweep and no stats-gate sweep in (f), and none after it, until **both** (i) thrash-table α ≥ 0.40 on a table that is not constant-`not_yet` **and** (ii) **≥ 2** workers with non-null **A0**. Today only `ca977b9ca0dd` counts toward (ii). Do not ship hooks, plugins, or behaviour.

### Success sketch

| Gate | Criterion |
|------|-----------|
| Corpus | ≥ **2** new shape-matched workers packed, or an explicit **blocked** note if the cross-project screen cannot supply them |
| Panel | Three seats on every new prefix; original rubric only |
| Gold rule | ≥ **2** workers with non-null **A0** across (d)+(e)+(f), or a written miss |
| H5 | Enlarged thrash-table α **≥ 0.40**, and the table is not all `not_yet` |
| Non-goal | No `--call-jev`, no stats sweep, no hook or plugin edit, no adoption of **A_maj** / **A_gc** |

### Alternates (not primary)

**`hold-until-new-maps-sessions`:** stop packing the maps remainder. Wait for new long runaway sessions that meet the ca977 shape, then pack those. Use this when the cross-project screen is empty or the other project directories are not on the Ubuntu box. Holding does not unlock Jev.

**`spot-check-ca977-75-vs-90`:** human or agent spot-check of `ca977b9ca0dd@75` (Sonnet-only checkout) versus `@90` (unanimous **A0**). Annotation only. It does not add a second **A0** and does not unlock Jev by itself.

---

## Completed — experiment **`shape-signal-panel-v1`** (NEW gold protocol — packs + three seats + agreement)

**Status:** Phase 1 packs **done**; Phase 2 seats **done** (Composer PR #66, Grok #67, Sonnet #68); agreement SUMMARY **done** (2026-10-01). **Supersedes** unanimous A0 / ≥2 A0 as the hard gate.

**Artifacts:** seat JSONLs `shape-signal-verdicts-{composer,grok,sonnet}-20261001.jsonl` (+ seat SUMMARYs); agreement [`shape-signal-agreement-SUMMARY-20261001.json`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.json) / [`.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md); packs [`shape-signal-judge-packs-20261001-212524.jsonl`](proofs/validated/gold/packs/shape-signal-judge-packs-20261001-212524.jsonl).

**Agreement highlights:** **`ca977b9ca0dd`** unanimous `early_thrash` (exits 75–90); **`92a48e004519`** shape **split** but thrash signals around ~90 in ≥1 seat; five other workers majority `unclear` (wait/implement arcs). Exit-turn spread reported, not a hard fail.

**Why it ran.** (e) and (f) exhausted ca977-twin hunting. Exact exit-turn unanimity kept Jev blocked on a single A0 and discarded useful disagreement. This experiment asked seats for **shape** and **early signals** first, then a recommended exit. Agreement on signals/shape/inflections is the unlock path; exit-turn spread is secondary.

### Per-seat questions

1. **Shape:** `late_pivot` vs `early_thrash` (see [`TERMS.md`](TERMS.md) §11).
2. **Why T is large:** turn-anchored account of what kept the session long.
3. **Inflection points:** turn ranges + what changed.
4. **Early signals:** concrete foreshadowing of the outcome, turn-anchored in the pack.
5. **Recommended exit + earliness:** pivot for `late_pivot`; first clear thrash for `early_thrash`; earliness vs that ideal.

### Agreement worth

| Primary (score) | Secondary (report, not hard fail) |
|-----------------|-----------------------------------|
| Multi-model agreement on **early signals**, **shape**, and **inflections** | Exact exit-turn match / exit-turn spread |

Do **not** fail the panel solely because seats disagree on the exit turn.

### Pool / shortlist (Phase 1)

Reopen Maps `T≥75` including prior A0-null and shape-miss workers. Prefer **diverse** shapes. Include the ~300T runaway. **No padding.** Prefer workers that already have hybrid_v0 packs under [`proofs/validated/gold/packs/`](proofs/validated/gold/packs/) — **reuse**; build new packs only for gaps.

| Rank | Worker | T | Pack | Diversity role |
|-----:|--------|--:|------|----------------|
| 1 | `92a48e004519` | 296 | reuse `…-194107` | ~300T runaway / P0 A0-null |
| 2 | `ca977b9ca0dd` | 109 | reuse `…-204508` | prior A0 hit; early_thrash candidate |
| 3 | `bb6165018de0` | 154 | reuse `…-194107` | P0 null contrast |
| 4 | `0aab88c525de` | 192 | reuse `…-202909` | expansion A0-null long |
| 5 | `036ff3ed4a89` | 161 | reuse `…-202909` | expansion partial disagreement |
| 6 | `7b00225cb824` | 137 | reuse `…-204508` | thrash null sleep/poll |
| 7 | `5163c22a6a3e` | 90 | reuse `…-210125` | shape-miss expand null |

**Artifacts (Phase 1):** [`proofs/validated/gold/packs/shape-signal-judge-packs-20261001-212524.jsonl`](proofs/validated/gold/packs/shape-signal-judge-packs-20261001-212524.jsonl) (45 rows); ranking [`SUMMARY-shape-signal-20261001-212524.md`](proofs/validated/gold/packs/SUMMARY-shape-signal-20261001-212524.md). Leak-scan PASS. No new per-worker packs (all reuse).

### Protocol sketch (as run)

1. **Phase 1:** TERMS §11 + NEXT-EXPERIMENTS + combined packs + SUMMARY. **Hold panel** in that task.
2. **Phase 2:** three seats on the shortlist packs (PRs #66/#67/#68); collect shape/signal/inflection/exit answers.
3. **Agreement:** publish agreement SUMMARY (this close-out). Original rubric patterns still available; do not revive `parent-pull-v1` without a new experiment.
4. **Jev:** no `--call-jev` and no behaviour ship until §§12–13 decay/handoff have a written harness design (WSM fold). Signal-agreement notes now exist on several workers; that alone does **not** ship behaviour.

### Success sketch

| Gate | Criterion |
|------|-----------|
| Corpus | ≥ **5** diverse Maps `T≥75` workers with hybrid_v0 packs (Phase 1: **7**, all reuse) |
| Panel | Seats answer the five questions; primary score = signal/shape/inflection agreement |
| Exit | Exit-turn spread reported; not a hard fail if spread is large |
| Non-goal | No `--call-jev`, no stats sweep, no hook/plugin edit, no `parent-pull-v1`, no padding |

<details>
<summary>Stop rules (shape-signal-panel-v1)</summary>

1. **No exact-exit hard fail.** Do not discard the panel solely for exit-turn disagreement.
2. **No Jev early.** Do not `--call-jev` or ship behaviour before signal-agreement notes on several workers.
3. **No padding.** Do not add near-duplicate poll-class workers to inflate N.
4. **No parent-pull.** Do not include the draft parent-pull delta in seat prompts.
5. **Phase hold (Phase 1 only).** Phase 1 must not run seats. Phase 2 seats and agreement are complete.

</details>

---

## Primary next — **`progressive-decay-bar-v1`** and **`validation-handoff-steer-v1`** (WSM design fold — no harness yet)

**Status:** **plan/hold** (2026-10-01). **Owner:** Workflow System Manager (orchestration docs). **Shape-signal unlock prerequisite met** — Phase 2 seats (PRs #66/#67/#68) + agreement SUMMARY ([`shape-signal-agreement-SUMMARY-20261001.md`](proofs/validated/gold/shape-signal-agreement-SUMMARY-20261001.md)). Still **no harness work** and **no `--call-jev`** until a decay schedule is pre-registered and reviewed. Definitions: [`TERMS.md`](TERMS.md) §12–§13.

These two ids split Cody’s same design fold for traceability; they ship together when unlocked, not as competing primaries.

| Id | Design slice | TERMS |
|----|--------------|-------|
| **`progressive-decay-bar-v1`** | ~15-turn revalidation; **decaying `confidence_min`**; **leap** (high-confidence near-done) vs **accumulate** (stacked stop-signals) exit paths | §12 |
| **`validation-handoff-steer-v1`** | Progressive checks ~**50 / 60 / 75** (then §2 schedule): ask if agent is **already in validation**; if **not**, **steer** via `additionalContext` and **new agent** for validation rather than hard-exiting the builder; if **yes**, use §12 paths only | §13 |

**Agreement weight (both):** Multi-model agreement on **early signals**, **shape**, and **inflections** (§11) **>>** exact exit turn when tuning decay or interpreting handoff inflections. Cross-link §11; do **not** rewrite shape-signal seat prompts or packs.

**Explicit non-goals (hold):**

- No `--call-jev`, no stats-gate sweep, no hook or plugin behaviour.
- Do not pad the shape-signal shortlist or revive `parent-pull-v1`.
- Do not implement decay schedule or validation questions in the replay harness until a decay schedule is written and reviewed (shape-signal unlock is met; harness still blocked).

**Unlock sketch (pre-register before harness):**

| Gate | Criterion |
|------|-----------|
| Prerequisite | `shape-signal-panel-v1` Phase 2+ **done** (agreement SUMMARY 2026-10-01); several workers have shared early-signal notes (`ca977` unanimous; `92a48e` thrash@~90) |
| Docs | §12–§13 unchanged or versioned in TERMS; decay schedule written before any live `confidence_min` decay |
| Harness | Separate PR / seats — **not** this lab-docs fold |

**Confidence:** stays **not high** until offline replay shows decay + handoff beats fixed `P0` on gold-relevant metrics; WSM steer remains convention until product wiring accepts it.
