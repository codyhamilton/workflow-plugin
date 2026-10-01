# Aggressive Phase-1.5 / Phase-2 resource budget

## Field capture

Live waves must persist **raw request/response JSONL**, **framing hashes**, **worker ids**, **dry-run twins**, **timestamps**, **model pin**, and **cost meters**. Learning from Pilot / Standard / Max requires full capture; do not score or compare tiers from partial logs.

**Date:** 2026-10-01 (AEST / Brisbane)  
**Status:** costed plan for Cody sign-off. **Estimate only — no live `--call-jev` in this write-up.** Soft until Cody. No behaviour ship.  
**Parent:** [`CANDIDATE-APPROACHES.md`](CANDIDATE-APPROACHES.md), [`TOOLING-MVP.md`](TOOLING-MVP.md), cheap-analysis [`TOOLS.md`](../2026-10-01-cheap-analysis-typesafe-opencode/TOOLS.md), [`ALTERNATES.md`](../2026-10-01-session-analysis-alternate-angles/ALTERNATES.md).  
**Posture:** earlier open-field slices capped live TypeSafe at **32** POSTs per wave. That is operationally tidy and, at published Jev prices, **too timid**. This note prices three aggressiveness tiers that try **local swarm segment cutting** and hit Jev with **many framing variants**, with Flash optional when a corpus mount exists.

**Phase 1 collectors stay as-is** (marker / survival distribution + framing dry-run registry, **0** live Jev). This wave is **additive**: after the dry-run registry exists, or in parallel with dry cycles that do not share a live TypeSafe budget ([`RESEARCH-OPS.md`](RESEARCH-OPS.md)).

---

## 1. Price card (documented; confirm before spend)

| Provider | Rate used here | As-of / source | Unknowns |
|----------|----------------|----------------|----------|
| **TypeSafe Jev** `jev-1.13.0` | **$0.042 / M input tokens; output free** | Third-party citations of TypeSafe model page, checked ~2026-09-18…22 ([typesafeai.org guide](https://www.typesafeai.org/guides/jev-pricing), Failproof, Refix). Equal to **$42 / B** input. | Confirm live on `console.typesafe.ai` / official models page before budgeting. Metered waitlist-skip gateways cite **~$0.42 / M** (10×) — if the Ubuntu key is gateway-metered, multiply all Jev USD by ~10. Credits / prepaid packs / expiry not modelled. |
| **Jev rate limits** | 250k tokens/s, **1,200 RPM** (stated as dynamic) | Same third-party snapshots | Treat as dated; plan for 429/529 + SDK backoff. |
| **DeepSeek Flash** `deepseek-flash` (V4.1-Flash) | **Off-peak:** cache-miss in **$0.15 / M**, cache-hit in **$0.003 / M**, out **$0.60 / M**. **Peak = 2×** (Mon–Fri 01:00–04:00 and 06:00–10:00 UTC). | [Official DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing) (fetched 2026-10-01). | OpenCode markup / routing unknown. Thinking-mode can inflate output. Peak in Brisbane ≈ **11:00–14:00** and **16:00–20:00 AEST** weekdays. |
| **Local llama.cpp / Qwen** `:8080` | **$0 API** | Cheap-analysis R2 / spike 5 | Wall-clock + electricity only. Throughput unmeasured until spike 5. |
| **Sonnet 5.5 reviews** | **Not priced** (OpenCode / Anthropic path) | — | Material open unknown if Flash volume rises. Budget a separate Sonnet envelope or cap reviews. |

**Arithmetic check (why 32 is timid):** at mid **2,000 input tokens / Jev POST** and **$0.042 / M**, **1,000** POSTs ≈ **$0.084**; **10,000** POSTs ≈ **$0.84**. Output is free. The binding constraints are **registration discipline**, **rate limits**, **local throughput**, and **what we learn** — not the Jev line item.

---

## 2. Shared assumptions (all tiers)

### Token assumptions (sensitivity)

| Call type | Low (tok) | Mid (tok) | High (tok) | Notes |
|-----------|----------:|----------:|-----------:|-------|
| Jev POST input (stats / early-signal card) | 1,000 | 2,000 | 4,000 | Packs ~2–3k chars state + question JSON. High if `summary_card` / hybrid excerpt grows. |
| Flash summary (in / out) | 3,000 / 400 | 6,000 / 800 | 12,000 / 1,500 | Only when `evidence_class: prose`. Cache-hit blend not assumed (mostly miss). |
| Local segment label (in / out) | 800 / 200 | 1,500 / 400 | 3,000 / 800 | Closed phase tags + theme guess; `cache: bypass`. |

**USD formulas (estimate only):**

- `jev_usd ≈ N_jev × tok_in / 1e6 × 0.042` (×10 if gateway-metered).
- `flash_usd_offpeak ≈ N_flash × (tok_in/1e6×0.15 + tok_out/1e6×0.60)`.
- `flash_usd_peak ≈ 2 × flash_usd_offpeak`.
- Local API USD = **0**.

### Caps & protocol (inherited, not waived)

| Rule | Implication for aggressive tiers |
|------|----------------------------------|
| Default `max_calls` **32**; above 32 needs `budget_tokens`; reject above **256** per `analysis.batch_trial` invocation | Aggressive spend = **multiple registered waves**, each ≤256, each with `budget_tokens` and hashed framings **before** POSTs. |
| Dry-run default; live needs `live` + `confirm_live` + `TYPESAFE_API_KEY` | Sign-off on a tier is not the same as flipping `live`. |
| Model pin `jev-1.13.0` | No fallback to local or Flash on Jev miss. |
| One live TypeSafe cycle at a time (ops) | Waves are sequential registrations, not an unregistered firehose. |
| Phase 1 collectors unchanged | Marker / survival + dry-run registry keep running; this wave does not replace them. |

### Concurrency / wall-clock assumptions

| Surface | Assumption | Wall-clock sketch |
|---------|------------|-------------------|
| Jev cloud | Effective **4–8** concurrent POSTs (tool max concurrency 8); RPM headroom large vs our N | Pilot/Standard: **minutes**. Max 2k–4k POSTs: **tens of minutes** including backoff, not hours. |
| Local `:8080` | Mid **5 s / cell** serial; optimistic **2 s**; pessimistic **15 s**. Concurrency **1–4** depending on GPU | Standard ~220 cells @ 5 s serial ≈ **18 min**; @ conc 4 ≈ **~5 min**. Max ~800 @ 5 s serial ≈ **~67 min**. |
| Flash | Cloud; batch of tens | Minutes; review seat is the slower human/agent step. |

### Dependencies (gate before live)

| Dependency | Needed for |
|------------|------------|
| Framing dry-run registry (Phase 1) with hashes | Any live Jev wave |
| `TYPESAFE_API_KEY` on Ubuntu harness (Coding Harness Manager) | Live Jev |
| Local server up at `WORKFLOW_LOCAL_LLM_URL` (default `http://127.0.0.1:8080/v1`) | Workstream **A** |
| `WORKFLOW_PROGRESSIVE_CORPUS` (or explicit mount) with assistant prose | Workstream **C** (else `prose_required` / skip) |
| WSM registration per wave (approach id, workers, framing hashes, kill, `budget_tokens`) | Cadence / audit |
| Spike 0–2 machinery (segment inventory, dry-run, dedupe) | Shared substrate — extend, do not fork |

---

## 3. Workstreams (shared definitions)

| Id | Name | What it does |
|----|------|--------------|
| **A** | Local swarm segment cutting | Cut early prefixes at `label_60` grid points (and optionally sub-windows) ≤ `early_window_end`; local model labels phase tags + theme guess; conflict → Flash arbiter card only. Maps to `segment-swarm-arbiter`. |
| **B** | Jev framing / variant tournament | Many registered framings × stratified workers on a **frozen card**; multi-wave under caps. Maps to `stats-jev-tournament` + aggressive expansion. |
| **C** | Flash summary-then-judge (optional) | Schema-locked Flash cards on prose workers → Sonnet review → later Jev on signed cards. Maps to `summary-then-judge`. **Skipped cleanly** if mount missing. |
| **D** | Frozen-card framing search size | Size of pre-registered framing pool + 8/24 (or larger) baseline-vs-search split. Maps to `frozen-card-search`. |

Marker-screen / survival collectors (**Phase 1**) remain **0-call** and are **not** re-budgeted here.

---

## 4. Tier table

### Summary (sign-off view)

| | **Pilot** | **Standard** ★ recommended | **Max** |
|--|-----------|----------------------------|---------|
| Intent | Prove A+B machinery; still ≫ timid 32 | Hit Jev hard on hold-out discipline; full n=34 local swarm | Thousands of Jev cells + dense local cuts; optional full Flash |
| **A** local reqs | ~24 (8 workers × ~3 cps) | ~120–220 (34 × grid ± subwindows) | ~500–1,000 |
| **B+D** Jev POSTs | **96** (8×12) | **288** (128+128+32) | **~2,000** mid / **~4,000** high |
| Framing pool \|D\| | 12 registered | 16 registered | 32 registered (+ hashed mutants in later waves) |
| **C** Flash calls | 0–8 (+≤4 arbiter) | ~8–25 (arbiter + optional 8 summaries) | ~45–80 (summaries + arbiters) |
| Jev USD mid / high (direct $0.042) | **~$0.01 / $0.02** | **~$0.02 / $0.05** | **~$0.17 / $0.67** |
| Jev USD if gateway ×10 | **~$0.08 / $0.16** | **~$0.24 / $0.48** | **~$1.70 / $6.70** |
| Flash USD mid off-peak / high peak | **~$0.01 / $0.04** | **~$0.03 / $0.14** | **~$0.07 / $0.43** |
| **Total cloud mid / high (direct Jev)** | **~$0.02 / $0.06** | **~$0.05 / $0.20** | **~$0.25 / $1.10** |
| **+ gateway Jev mid / high** | **~$0.09 / $0.20** | **~$0.27 / $0.62** | **~$1.80 / $7.20** |
| Sonnet review envelope | Cap ≤8 cards | Cap ≤25 cards | Cap ≤80 cards — **price unknown** |
| Wall-clock (order) | &lt;30 min compute | ~30–90 min compute | ~2–6 h compute + review seats |
| What we learn | Whether local conflict rate is &lt;50% on 8; whether 12 framings separate thrash vs poll on strat set | Hold-out confirmation; swarm economics on full 34; framing winner vs random baseline | Brittleness (adversarial), evolutionary search value, summary-card vs stats-card delta |
| Primary kill | Conflict &gt;4/8 local; poll flags with thrash; unregistered framing | Search ≤ baseline mechanical; hold-out fails theme separation; swarm collapses to all-Flash | Same + concordance / usefulness null on summary path; spend without new gated metric |

★ **Default ask: Standard.**

---

### Pilot — detail

| Workstream | Spec |
|------------|------|
| **A** | Stratified **8** workers (both thrash, 3 poll, 2 steady residual, 1 weak-thrash — same draw spirit as open-field). Segments = pack checkpoints ≤120 (~**24** local completions). Conflict → Flash arbiter ≤**4**. Kill if conflict/parse on **&gt;4/8**. |
| **B** | **8 × 12 = 96** Jev POSTs on frozen **stats_card**. One registration with `budget_tokens` covering ~200k–400k input tokens. Schema `early-signal-v0` (or pre-registered mix). Dry-run identical shape first. |
| **C** | Optional: **8** Flash schema cards if mount probe passes; else `prose_required` and stop C. **0** Jev on summary cards in Pilot (keep B on stats_card). |
| **D** | Pool of **12** hashed framings. First **32** of the 96 may use 8 baseline / 24 search split; remainder matrix fill. |

| Budget line | Low | Mid | High |
|-------------|----:|----:|-----:|
| Jev POSTs | 96 | 96 | 96 |
| Jev input tokens | 96k | 192k | 384k |
| Jev USD (direct) | $0.004 | $0.008 | $0.016 |
| Flash calls | 0 | 8+4 | 12 |
| Flash USD (off-peak→peak) | $0 | ~$0.01 | ~$0.06 |
| Local reqs / tokens out | 24 / ~5k | 24 / ~10k | 40 / ~30k |
| Local USD | $0 | $0 | $0 |

**Kill / learn:** local thesis survives or collapses into summary-then-judge; 12-framing matrix either separates thrash vs poll or ties the zero-call rank table (`echo` / idle premise).

---

### Standard — detail (recommended ask)

| Workstream | Spec |
|------------|------|
| **A** | All **34** workers. Primary: every `label_60` / pack checkpoint ≤120 (~**120** local). Optional dense: +3 subwindows (1–40, 41–80, 81–120) where T allows (~**+100** → **~220** mid). Publish parse-failure % and conflict %. Flash arbiter **only** on conflict ids (expect **8–17** if thesis holds; kill-adjacent if **&gt;17**). |
| **B** | **Three registered waves** (sequential): (1) strat 8 × **16** framings = **128**; (2) hold-out **16** workers × top **8** framings from wave 1 = **128**; (3) frozen-card search **32** (8 baseline + 24 search). Total **288** POSTs. Theme scoring on hold-out only for wave-2 claims. |
| **C** | Mount probe first. If prose: optional **8** Flash summaries (same pilot set) + Sonnet review; usefulness null until α gate. Do **not** block A/B on mount. |
| **D** | Pool **16** framings registered before wave 1. Wave 3 is the formal baseline-vs-search cell. |

| Budget line | Low | Mid | High |
|-------------|----:|----:|-----:|
| Jev POSTs | 288 | 288 | 288 |
| Jev input tokens | 288k | 576k | 1.15M |
| Jev USD (direct) | $0.012 | $0.024 | $0.048 |
| Jev USD (gateway ×10) | $0.12 | $0.24 | $0.48 |
| Flash calls | 0 | ~20 | ~30 |
| Flash USD | $0 | ~$0.03 | ~$0.16 |
| Local reqs | 120 | 220 | 280 |
| Wall-clock compute | ~20 min | ~45–90 min | ~2 h |

**Kill / learn:** whether search beats random baseline mechanically; whether hold-out theme flags match standing strata without poll contamination; whether local swarm keeps Flash under half the panel.

---

### Max — detail

| Workstream | Spec |
|------------|------|
| **A** | Dense cutting: grid + subwindows + optional 15-turn slices inside ≤120 → **~500–1,000** local reqs. Still `cache: bypass` for throughput measurement. Conflict rule unchanged; if &gt;50% conflict, **kill A** and stop densifying. |
| **B** | Framing pool **32**. Example mid stack (~**2,000** POSTs): 8×32=256; hold-out 26×16=416; adversarial perturbations (Alternate C) ~140; mechanical bandit/evo wave 256; summary-card re-judge 8×16=128 if C cleared; second tournament / sensitivity ~500; contingency ~300. High stack **~4,000** POSTs = more sensitivity × schema (`phase-sketch-v0`, Likert collapse) and a second hold-out pass. **Many sequential registrations**, each ≤256 with `budget_tokens`. |
| **C** | If mount: Flash summaries for all workers with non-empty early excerpts (~**30**) + arbiters (~**15**) → **~45–80** Flash; Sonnet reviews capped (sample if cost bites). |
| **D** | Pool 32 + hashed evolutionary offspring only after mechanical parent wins; never score theme inside the allocator reward. |

| Budget line | Low | Mid | High |
|-------------|----:|----:|-----:|
| Jev POSTs | 1,200 | 2,000 | 4,000 |
| Jev input tokens | 1.2M | 4M | 16M |
| Jev USD (direct) | $0.05 | $0.17 | $0.67 |
| Jev USD (gateway ×10) | $0.50 | $1.70 | $6.70 |
| Flash USD | ~$0.02 | ~$0.07 | ~$0.43 |
| Local reqs | 500 | 800 | 1,000 |
| Wall-clock compute | ~1–2 h | ~2–4 h | ~4–8 h + reviews |

**Kill / learn:** adversarial brittleness of verdicts; whether evo/bandit beats pre-registered matrix on mechanical reward; whether summary cards change Jev theme flags vs stats cards; at what N returns diminish.

---

## 5. Recommendation

**Ask Cody to sign Standard** as the default Phase-1.5 / Phase-2 additive wave.

| Why Standard | Why not Pilot alone | Why not Max first |
|--------------|---------------------|-------------------|
| Full-corpus local swarm (the ask) + enough Jev variants (16) + hold-out discipline | Pilot under-samples n=34 swarm economics and cannot confirm hold-out | Max’s extra $ are tiny, but registration / review / kill surfaces explode; run after Standard clears gates |
| Cloud mid cost still **≪ $1** on direct Jev (or **≪ $1** even gateway mid) | 96 POSTs still fine, but leaves framing search thin | Adversarial + evo are hedges (`ALTERNATES` C); schedule as Standard follow-ons |

**Sign-off sentence (proposed):**  
*Approve Standard: ≤288 live `jev-1.13.0` POSTs across three registered waves, ≤~220 local `:8080` segment labels on n=34, optional ≤~25 Flash if corpus mounted; Phase 1 collectors unchanged; no hook/behaviour ship; abort on listed kills; escalate before any wave &gt;256 or any non-`jev-1.13.0` model.*

Pilot remains available as a **one-evening preflight** if `:8080` or the key path is unproven. Max remains a **pre-approved envelope** Cody can release after Standard’s wave-2 hold-out table exists.

---

## 6. Open unknowns (explicit)

1. **Direct vs gateway Jev price** on the Ubuntu `TYPESAFE_API_KEY` (1× vs ~10×).  
2. **Live confirmation** of $0.042 / M on the official TypeSafe models page / console (third-party as-of late Sep 2026).  
3. **Actual tokens/cell** from first dry-run → live microbatch (replace mid 2k assumption).  
4. **Local `:8080` seconds/cell** and safe concurrency (spike 5).  
5. **Corpus mount** availability for workstream C (`prose_required` is a valid refusal).  
6. **Sonnet 5.5 review** $/card via OpenCode (largest soft cost if Max Flash volume runs).  
7. **OpenCode Flash** billing identity (pass-through DeepSeek vs markup).  
8. **Dynamic Jev RPM** under sustained 8-way concurrency (429 rate).  
9. Whether **288** or **2,000** POSTs need an explicit Cody prepaid credit top-up (account balance unknown).  
10. Interaction with **in-flight Phase 1 collectors** — confirm they stay dry-run only while Standard wave 1 is live (ops: one live TypeSafe cycle at a time).

---

## 7. What this agent did / did not do

- **Did:** Read open-field candidates + tooling MVP, cheap-analysis TOOLS, alternates; fetched / searched Flash + Jev list prices; designed Pilot / Standard / Max with call budgets and USD bands.  
- **Did not:** Live `--call-jev`, hook edits, plugin registration, behaviour ship, or spend against `TYPESAFE_API_KEY`.  
- **PR:** local markdown path prepared; push/PR may need a GitHub-authenticated follow-up (no `gh` token in this executor).

---

## 8. Index touch (when landing)

Add a row to [`INDEX.md`](INDEX.md) / parent [`../INDEX.md`](../INDEX.md) pointing at this file as the costed aggressive wave beside the open-field pack. Landing is mechanical docs-only.
