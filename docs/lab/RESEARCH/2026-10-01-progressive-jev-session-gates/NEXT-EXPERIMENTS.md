# Next experiments — progressive Jev gold labeling

**Confidence: not high.** H5 failed on the P0 panel (α = 0.1189, **A0 null**). No Jev sweep, no hook change.

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

## Primary next — experiment **(c)** `corpus-expand-hybrid-panel-original`

**Status:** plan. **Goal:** enlarge the labeled corpus under the **original** rubric (body of [`GOLD-LABEL-RUBRIC.md`](GOLD-LABEL-RUBRIC.md) **without** the draft parent-pull delta), then re-run the **three-seat** panel (Sonnet signed final + Composer + Grok) on **hybrid_v0** judge packs. This addresses H5 underpowering and the n = 2 smoking-gun island; it is **not** a Jev tuning sweep.

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

Failure to clear α after expansion does **not** authorize a return to `parent-pull-v1` without a new explicit experiment. Confidence stays **not high** until (c) completes and is read against [`HYPOTHESIS.md`](HYPOTHESIS.md).

### Stop rules (c)

1. **Under-corpus.** Fewer than two new workers labeled → status **blocked**, not a rubric pass/fail.
2. **Rubric leak.** Any seat prompt includes the parent-pull draft, other seats’ labels, or target turns → discard that worker’s panel and re-run.
3. **No Jev.** Do not interpret H1–H4 / H6–H7 from Jev dry-run or live cache until H5 clears on the enlarged gold table.
4. **(b) rows.** Never promote `p0-checkout-verdicts-sonnet-relabel-*.jsonl` to gold.
