# Next experiments — progressive Jev gold labeling

**Confidence: not high.** H5 failed on P0 (α = 0.1189, **A0 null**) and on experiment **(c)** expansion (α = **0.0000** on 3×20, **A0 null**). Experiment **(d)** thrash-screen **passes** H5 on its own 3×12 table (α = **0.8276**) with **A0 = 90** on `ca977b9ca0dd` only. **Jev stays blocked:** one non-null A0 is not a tuning corpus. No hook change.

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

## Primary next — experiment **(e)** `ubuntu-thrash-high-score-expand-v1`

**Status:** plan. **Goal:** pack and label **more** workers that match the shape that actually produced **A0** in (d) — rank-1 `ca977b9ca0dd` (no Edit/Write, high max-reread, high compaction) — and **hold Jev** until at least a second worker has non-null **A0**.

### Why (e) now

**(d)** cleared thrash-only H5 (α = **0.8276** ≥ 0.40) and produced the first new unanimous exit (**A0 = 90** on `ca977b9ca0dd`). The confidence caveat is on the record: `daf933273c8f` and `7b00225cb824` are **A0 null**, and nine of twelve prefixes are unanimous `not_yet`. A sweep on that table would tune to a single exit turn, so Jev and any stats sweep stay blocked.

Ranks 2–3 (sleep/poll and Contract-W Bash) stayed `not_yet` on every seat. The next packs should follow the `ca977b9ca0dd` / `92a48e004519` shape: no Edit/Write, high max-reread, high compaction (smoking-gun thrash score ≈ 151). Leave the poll class off the shortlist.

### Protocol sketch

1. **Screen:** From the remaining Ubuntu maps workers with `T ≥ 75`, exclude already labeled ids (`92a48e004519`, `bb6165018de0`, `0aab88c525de`, `036ff3ed4a89`, `0853bc21d3aa`, `ca977b9ca0dd`, `daf933273c8f`, `7b00225cb824`). Rank with the same dry-run thrash tables. **Prefer** no Edit/Write in the tool histogram, high max-reread, and high compaction. **Deprioritize** sleep/poll and brief-mandated Bash monitors — (d) labeled that class `not_yet`.
2. **Pre-register N** before labeling. Pack hybrid_v0 (`75:15`) for the next workers that meet the stricter shape. Target **≥ 3** additional workers when the screen has them. If fewer than two meet the shape, record **blocked** for the rest; do not pad with poll-class workers to hit a count.
3. **Panel:** Same three seats and original rubric as (d). Keep P0, expansion, and (d) JSONLs read-only.
4. **Metrics:** **A0** per new worker and nominal α on the enlarged thrash table (d’s 12 prefixes plus the new ones). H5 floor unchanged (**≥ 0.40**).
5. **Jev gate (explicit):** no Jev sweep and no stats-gate sweep in (e). A later sweep is in scope only after **both** (i) thrash-table α ≥ 0.40 **and** (ii) **≥ 2** workers with non-null **A0**. One worker (`ca977b9ca0dd`) already counts toward (ii); (e) has to add another. Document confidence caveats either way. Do not ship hooks, plugins, or behaviour.

### Success sketch

| Gate | Criterion |
|------|-----------|
| Corpus | ≥ **2** new workers packed under the stricter shape, or an explicit **blocked** note if the screen cannot supply them |
| Panel | Three seats on every new prefix; original rubric only |
| Gold rule | ≥ **2** workers with non-null **A0** across (d)+(e), or a written miss |
| H5 | Enlarged thrash-table α **≥ 0.40** |
| Non-goal | No `--call-jev`, no stats sweep, no hook or plugin edit, no adoption of **A_maj** / **A_gc** |

### Alternate (not primary)

**Hold.** Leave (d) as the last measurement and do not pack further until a human spot-check of `ca977b9ca0dd@75` (Sonnet-only) versus `@90` (unanimous) is on file. That check does not by itself authorize a Jev sweep.
