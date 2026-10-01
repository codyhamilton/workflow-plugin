# Open field — session analysis beyond the harness sketch

**Status:** problem space. **Confidence: not high.** Observations below were read from committed packs and agreement notes. They are not a fitted screen and not a claim that any model will match them.

The cheap-analysis pack specifies one harness: Flash or a local server writes summaries and window labels, TypeSafe tries registered framings, dry-run by default, scored later against a prose gold that is not checkout `A0`. That harness is necessary machinery. It is not yet a choice among ways to spend it. This file lays out the space those choices live in. Named pipelines are in [`CANDIDATE-APPROACHES.md`](CANDIDATE-APPROACHES.md).

## The cost that motivates the field

Maps worker `92a48e004519` is **T = 296**, about **12.7MB** of JSONL, peak context already **129_961** tokens by checkpoint 75. Progressive TERMS keep Jev off the raw file: state over **12_000** characters is rejected. The committed hybrid_v0 row for that worker at checkpoint 75 is **2_660** pack characters. The compression already exists. What does not exist is a measured answer to four questions:

1. Which durable summary of a long transcript is stable enough to compare across workers, and cheap enough that the raw file stays on disk?
2. Which markers inside the first ~120 turns predict session length and shape, when exit turn is explicitly the secondary outcome?
3. Which TypeSafe framing of a small card is worth a live call, given a hard cap of 32 POSTs and a factorial space far larger than that?
4. Which agent is allowed to author, review, label, or close each of those artifacts?

## Constraints (in force for every approach)

Inherited. This pack does not edit them.

| Constraint | Where it lives |
|------------|----------------|
| Soft until Cody. No hook behaviour, no product wiring | Cheap-analysis DESIGN non-goals; TERMS §12–§13 status |
| TypeSafe dry-run unless `live`, `confirm_live`, and `TYPESAFE_API_KEY` | Cheap-analysis R7; [`TOOLS.md`](../2026-10-01-cheap-analysis-typesafe-opencode/TOOLS.md) |
| No `--call-jev` on `replay_progressive_gates.py` from this work | Cheap-analysis NEXT, "explicitly not scheduled" |
| Early signals from `api_turn` ≤ ~120. Later turns are outcome | TERMS §11 and §14. All **102** shape-qual seat verdicts respected the window |
| `early_window_end(T) = min(120, T)` | Cheap-analysis DESIGN |
| Checkout `A0` is not the target to rebuild. P0 α **0.1189**, **A0 null**. Expansion (c) α **0.0000**, **A0 null**. Thrash-screen (d) passed its own H5 (α **0.8276**) with **A0 = 90** on `ca977b9ca0dd` only; thrash-expand (e) added no further A0. That single exit stays in the progressive pack | Progressive NEXT-EXPERIMENTS. This field scores themes and early markers, and does not schedule another checkout panel |
| Exit-turn spread is secondary, not a hard fail | TERMS §11, §14; both agreement summaries |
| `assert_phase --deterministic` stays the kill line. Jev does not hard-pass | Cheap-Jev use cases |
| Classify is not a KPI | Lab policy |
| Flash does not sit a gold seat. Local labels are `seat_class: volume` | Cheap-analysis R2; Flash guidance |
| Prose schemas on `stats_only` or `absent` evidence return `prose_required` and are not stored as qualitative arcs | Cheap-analysis R3 |
| One attempt per rubric version. A failed version is not re-labeled into a pass | Cheap-analysis R4 |
| Shape-gold α floor **0.40**, items = workers, `n_workers` ≥ 3, per field | Cheap-analysis R4. The checkout floor failure is not evidence this floor will clear |
| TERMS vocabulary (`api_turn`, `prefix(c)`, `T`, `hybrid_v0`, `A0`, `R(t)`, `confidence_min`, §11 shape labels) is not amended here | Cheap-analysis R1 |

`trajectory`, foreshadow ids, and `phase_sketch` from the cheap-analysis design are available as **schema vocabulary** for framing trials. They are not promoted into TERMS by being used here.

## What the standing gold already shows

Corpus: **n = 34** open-pajero-maps workers with **T ≥ 75**, hybrid_v0 packs (`N = 8`, excerpt 400), schedule `75:15`. Agreement: [`AGREEMENT-SUMMARY.md`](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/shape-qual-full-maps-v1/AGREEMENT-SUMMARY.md).

| Fact | Why it binds the field |
|------|------------------------|
| §11 `shape_label` unanimity is **17/34 `unclear`**, plus **1** unanimous `early_thrash` (`ca977b9ca0dd`). **1** three-way diverge (`bb6165018de0`) | A method scored only on §11 unanimity will look strong by predicting `unclear` |
| Sonnet `shape_detail` and Grok `poll_monitor` carry the distinctions the coarse trio misses. Sonnet assigned **0** `late_pivot` | Forcing §11 pivot agreement is the wrong objective. Shared themes are the objective |
| Thrash **signals** agree on `ca977b9ca0dd` (unanimous) and `92a48e004519` (2-of-3 `early_thrash`; Composer `late_pivot` on the long middle) | The early bundle is the prototype. The §11 label on `92a48e` is the disagreement to preserve, not to vote away |
| `poll_monitor` / `poll_monitor_wait` is a sibling family (Grok: `87a380bc64ff`, `bb6165018de0`, `15f24c7ba18c`, `8e36f8e80baa`). Agreement asked that it not be folded into thrash | A screen that ranks poll workers with thrash workers has failed, even if thrash recall is perfect |
| Composer-only `early_thrash` on `07357f196666`, `daf933273c8f`, `de5b76cc68a6`, `e28a2428b192` is weak consensus (Sonnet `bash_only_silent` or similar; Grok `unclear`) | Bash-only silence is a hard negative for a thrash rule |
| `ca977b9ca0dd` has **T = 109**. Several non-thrash workers are longer (`0aab88c525de` 192, `036ff3ed4a89` 161, `0853bc21d3aa` 155, `bb6165018de0` 154) | Predicting **T** and predicting **thrash** are different tasks. A marker that tracks the longest file is aimed at `92a48e` alone |
| Many workers have one checkpoint inside the early window (T just above 75) | A multi-checkpoint loop cannot be declared from a single row. `checkpoints_seen` is part of the feature, not a footnote |

### Pack arithmetic already visible at checkpoint ≤ 120

Read from `shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl` while writing this pack. Recompute rather than cite these as gold labels.

**82** of **104** rows have `checkpoint_turn` ≤ 120. **30** workers have at least one non-empty tail excerpt in that window. **4** workers have empty excerpts on every such row: `92a48e004519`, `ca977b9ca0dd`, `daf933273c8f`, `07357f196666`.

The two strongest thrash prototypes are in that empty set. Their early window is a stat card:

| Worker | cp | `compaction_event_count` | `assistant_text_chars` | max reread count | Edit / Write in histogram |
|--------|---:|-------------------------:|-----------------------:|-----------------:|---------------------------|
| `ca977b9ca0dd` | 75 → 90 → 105 | 10 → 12 → 16 | 167, flat | 10 → 12 → 14 | absent |
| `92a48e004519` | 75 → 90 → 105 → 120 | 12 → 14 → 18 → 20 | 36, flat | 10 → 10 → 13 → 13 | absent |

Poll and steady rows do not look like that card:

| Worker | At cp 75 | Contrast |
|--------|----------|----------|
| `87a380bc64ff` | compaction **0**, text **2_284**, `Monitor` **6**, excerpts non-empty | Poll spotlight. No frozen-narration bundle |
| `bb6165018de0` | compaction **0**, text **2_174** growing through cp 120, `Monitor` present, `Write` present | Shared monitor-wait theme. Shape labels diverge |
| `0aab88c525de` | compaction **4**, text growing, max reread **7** (12 by cp 105), `Edit` present | Mechanical `reread_cluster` (count ≥ 3) is true on a productive edit arc |
| `a318f4b89a6a` | compaction **8**, text **2_460**, `Edit` **8** | Compaction count alone is not the thrash bundle |

So a Flash "summary" of the thrash prototypes, built from the committed packs, has no prose to compress. Cheap-analysis R3 would refuse a qualitative arc on that evidence. A raw mount may add the missing tool-result text; it will not invent assistant prose that `assistant_text_chars` already counts in the tens or low hundreds. The durable artifact for those two is the stat card. Summaries earn their cost on workers whose tails actually contain sentences.

## 1. Abstract session summaries

Goal: a durable, comparable object per worker (or per prefix ≤ `early_window_end`) that later framings can share, small enough for the 12_000-character guard, stable enough that two runs on the same prefix diff cleanly.

Three authors are viable. They are not substitutes.

| Author | Keeps | Drops | Comparability | Cost shape | Where it fails |
|--------|-------|-------|---------------|------------|----------------|
| **Programmatic cleanup** | Tool histogram, reread paths, compaction count and its slope across checkpoints ≤ 120, `assistant_text_chars` and its delta, `Monitor` / `Edit` / `Write` presence, run-length sketch of `tool_names`, `checkpoints_seen`, brief anchor (already capped at 500) | Intent, "waiting on" language unless an excerpt is copied through, anything TERMS calls `anchor_divergence` | Exact. Same prefix, same JSON | Zero model calls. Reads packs that are already in git | Silent on the poll sentence when excerpts are empty and `Monitor` is absent. Cannot author `phase_sketch` as a prose claim; it can emit a **tool-run sketch** that a later seat may accept or ignore |
| **Local LLM** (llama.cpp at `WORKFLOW_LOCAL_LLM_URL`, default `http://127.0.0.1:8080/v1`) | A schema-locked JSON card: restated counts, a phase tag sequence from the cheap-analysis set (`orient`, `search`, `edit`, `verify`, `replan`, `stall`), a noise note | Free prose unless the schema allows one short field | High if the schema is closed and parse failures are `missing` | GPU time. Cache bypass when the measurement is the server, not the matrix (cheap-analysis spike 5) | Parse failures. Drift from the counts if the prompt asks it to "explain" rather than copy fields. Banned from prose claims on `stats_only` / empty-excerpt windows |
| **DeepSeek Flash** via OpenCode | A short qualitative arc or a filled card, when `evidence_class` is `prose` | Raw tool args, post-120 outcome, gold status | Low if the artifact is free prose; high if Flash must fill the same card schema the local model fills | One Flash call per card, then a Sonnet 5.5 review, then Claude or Grok sign-off of that review. The arc does not enter the gold file | Refused when excerpts are empty (`prose_required`). A fluent restatement of a frozen 36-character prefix is a failed artifact even if it reads well |

**Noise to strip, for every author:** tool-call arguments, secrets (snapshot redaction patterns), pack metadata (`pack_meta`, `shrink_steps`), prior seat labels, maps nicknames, and any turn after `early_window_end` when the card is an early card. Compaction events stay as counts. They are signal, not noise.

**What would prove a summary method:**

- **Fidelity, programmatic:** round-trip. The card's histogram, compaction count, and text-char field match the pack row. Mismatch rate above 0 kills that extractor version.
- **Fidelity, model:** a blinded check on a worker with non-empty excerpts. The card may not state a count that contradicts the pack. Sonnet marks contradictions. Flash does not grade itself.
- **Comparability:** two builds of the same prefix produce equal programmatic cards. Two model cards parse to the same keys. Free-prose arcs fail this test by construction and stay beside the matrix, as cheap-analysis R9 already says.
- **Usefulness:** a downstream judge, shown only the card, recovers the **theme** (thrash bundle, poll/monitor, productive edits) that ≥2 shape-qual seats already recorded from the packs. Usefulness stays null when the theme was not shared. Exit turn is not the score.

A summary method that needs the raw 12.7MB file inside the judge has left this problem. The raw mount is for building cards and for prose seats. It is not the judge input.

## 2. Early markers for length and shape

Markers are features of `prefix(c)` with `c ≤ early_window_end`. They are visible in the first ~120 turns by construction. Outcomes, attached only at scoring time, are:

- **Shape theme**, from the agreement note, not a new labeling pass. Suggested strata, written so a scorer cannot quietly expand them: **thrash consensus** = `{ca977b9ca0dd, 92a48e004519}`; **poll labels** = Grok `poll_monitor` `{87a380bc64ff, bb6165018de0, 15f24c7ba18c, 8e36f8e80baa}`; **shared monitor-wait** (agreement §4, ≥2 seats) = `{87a380bc64ff, bb6165018de0, 6e06ab86aa72}`; **weak thrash** = Composer-only `{07357f196666, daf933273c8f, de5b76cc68a6, e28a2428b192}`. Everyone else stays `residual` until a later rubric. Sonnet `shape_detail` is a stratum description, not a third vote.
- **Length**, `T` as recorded in the inventory, plus buckets `T ≤ 90`, `91–120`, `> 120`. Length is hindsight. A marker may correlate with it. Correlation is not a checkout recommendation.

### Marker families to publish before any threshold

No family below has a locked cut. The first measurement is the distribution on all 34 workers, features collapsed from checkpoints ≤ 120 only. Cheap-analysis already forbids a compaction-count threshold presented as a rubric. The same ban applies to every row here.

| Id | Definition (computable from hybrid_v0 cumulative + histogram) | Why it is in the set | Confusion it must survive |
|----|---------------------------------------------------------------|----------------------|---------------------------|
| `frozen_text` | `assistant_text_chars` unchanged across every pair of checkpoints ≤ 120. Undefined when `checkpoints_seen` < 2 | Both thrash prototypes are flat (167 and 36) | A short worker with one checkpoint must not match via a missing delta |
| `compaction_level` | Count at the last checkpoint ≤ 120, and the delta from the first | Prototypes rise 10→16 and 12→20 inside the window | `a318f4b89a6a` is already 8 at cp 75 with edits and growing text |
| `no_mutation` | `Edit` and `Write` both absent at every checkpoint ≤ 120 | Shared thrash citation | Bash-only weak-thrash workers also lack edits; poll workers generally have `Write` or `Monitor` |
| `reread_max` | Max path count. The mechanical predicate "≥ 3" already exists and is not a panel question | Prototypes are ≥ 10 | `0aab88c525de` exceeds 3 while editing |
| `bash_read_monopoly` | Histogram keys ⊆ `{Bash, Read, ToolSearch}` | Describes the prototype histogram | `de5b76cc68a6` and `582c23b3c6e4` are bash-heavy without thrash consensus |
| `monitor_present` | `Monitor` count ≥ 1 at the first checkpoint ≤ 120 | Separates the poll family in the packs (`87a380bc64ff` has 6; prototypes have 0) | Orchestrator bursts (`15f24c7ba18c` has `Monitor` 28 and also `Edit`) are not thrash and not pure poll |
| `text_growth` | Delta of `assistant_text_chars` when two checkpoints exist | Poll and steady rows grow; prototypes do not | Single-checkpoint workers are excluded from this feature, not imputed |
| `mutation_present` | `Edit` + `Write` ≥ 1 by the first checkpoint | Anti-feature for the thrash bundle | Does not mean "short" or "healthy" |
| `checkpoints_seen` | How many `75:15` rows fall at ≤ 120 | Support for any slope feature | Workers with T ∈ [75, 89] have one row. Agreement already warned that packs ending just after cp 75 under-determine a loop |
| `peak_ctx` | `peak_ctx_tokens` at the first checkpoint | `92a48e004519` is ~130k by cp 75 | Likely collinear with compaction. Report it. Do not let it stand in for the bundle |

`anchor_divergence` and `no_checkable_step` stay prose fields, as in cheap-analysis DESIGN. A stats card may carry them only as `not_in_evidence`.

### How to measure predictive power

Units are **workers** (34), not checkpoint rows. Nested prefixes of one worker are not the N. Features from turns > 120 are excluded even when the pack has them (`92a48e004519` has checkpoints through 285; those rows are outcome).

Because the thrash consensus has **n = 2**, a threshold fit on those two is not a measurement. Publish ranks:

1. For each family, the percentile of each thrash-consensus worker among the 34.
2. The list of **other** workers that land in the same extreme cell. Name them. A cell that also contains a poll-label worker fails that family as a thrash separator, on this corpus, for this pre-registered cell.
3. Spearman correlation of each numeric family with `T`, and the same correlation **with the two thrash-consensus workers removed**, so `92a48e004519` cannot be the entire length result. `ca977b9ca0dd` is not a long session.
4. A separate length table: median `T` in the top quartile of `text_growth` versus the bottom quartile, among workers with `checkpoints_seen` ≥ 2. This asks whether early text growth tracks length. It does not ask for a stop turn.

A boolean rule is a **later** cell, one id, one attempt, scored once against the strata above. Precision on thrash consensus and the poll-overlap list are the headline. Recall on n = 2 is almost free and is not the headline. Agreement with `A0`, `recommended_exit`, or checkout α is not computed.

## 3. TypeSafe / Jev framing variations

The judge sees a **card**, never the raw JSONL. The card is one of:

| Slice | Contents | When it is legal |
|-------|----------|------------------|
| `stats_card` | Programmatic cleanup only. No model prose | Always, from committed packs |
| `hybrid_excerpt` | Current hybrid_v0 row, tail included, still ≤ ~3k characters on these packs | Always. On the four empty-excerpt workers the tail adds tool names and nothing else |
| `summary_card` | Schema-locked Flash or local card that has passed the fidelity check | Only after that check. Flash version only when evidence is prose |
| `segment_window` | A sub-range inside ≤ 120 (for example turns 1–40, 41–80, 81–120, or one `grid_15` point) | When the approach's pipeline says the judge sees windows rather than one prefix card |

Question styles, all under existing `schema_id`s (`shape-v0`, `phase-sketch-v0`, `early-signal-v0`, `trajectory-v0`). A new style is a new `framing_id` (slug + hash of the question JSON), not a new term in TERMS. `session-checkout` remains a regression schema only; its agreement is `checkout_diagnostic` and unfit while H5 is failed.

| Style | Ask | Scoring | Call cost |
|-------|-----|---------|-----------|
| Binary foreshadow ids | The v0 set: `reread_cluster`, `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `none` | `reread_cluster` against the path-count predicate, no panel. Other ids only against prose gold that has cleared its own α | One call |
| Likert | 0–3 strength per id, plus `none` | Needs a pre-registered collapse back to a theme before any winner is claimed. An uncollapsed Likert is not comparable to a binary | One call |
| Free tags | Short tags in the Sonnet `shape_detail` spirit | Discovery only. Not a precision claim. A tag set that is scored after looking at it is a new rubric version and must be written down first | One call |
| Multi-hop | First a phase tag, then a theme question conditioned on that tag | Two calls, or one call that returns both with the second marked as conditioned. Spending two calls per worker halves the number of framings inside the cap of 32 | Two, unless packed |

Few-shot: a shot that includes `ca977b9ca0dd` or `92a48e004519` is illegal on any framing scored on those workers. Shots, if any, are synthetic or taken from workers outside the scored set, and their text is inside the question JSON so the `framing_id` hash changes when the shot changes.

Chain versus single-shot: a chain is a multi-hop framing. It is worth running only after a single-shot wave parses and still misses a theme the card actually contains. It is not the default.

### How to search the framing space

A full matrix does not fit the cap. Illustrative size, not a plan to run: 4 slices × 4 styles × 4 schemas × 34 workers is thousands of cells. Cheap-analysis R7 caps a live batch at **32** POSTs unless a higher budget is explicitly present, and rejects above **256**.

Search methods that respect the cap:

| Method | What it spends the 32 on | When it is the right search | When it lies |
|--------|--------------------------|-----------------------------|--------------|
| **Pre-registered matrix wave** | One frozen slice, one stratified worker set, framings named before any answer | The first live wave. The contrast is knowable in advance (binary vs Likert, stats card vs excerpt card) | If a framing is added after seeing answers, the wave is void |
| **Tournament** | Winners of wave 1 play wave 2 | Only with a **new** pre-registered budget and a hold-out set that wave 1 did not fit | On 8 workers, the winner is a story about those 8 |
| **Batch bandit** | Adaptive allocation across framings | When the reward is immediate and mechanical (`reread_cluster_accuracy`, parse success). A second pass can shift calls toward framings that parse | When the reward is prose-theme agreement. That reward is not available until seats exist, and adapting on it overfits the same labels used to judge |
| **Evolutionary edit of the instruction** | Mutations of a parent prompt, fitness from the mechanical reward | A later cell, after a matrix wave has a parent worth mutating | If the fitness function can see thrash-consensus labels, or if the winning instruction was not hashed before the run. Unregistered question JSON is already `unregistered_framing` |

Stratification that fits **one** 32-call wave on a frozen slice: **8** workers × **4** framings. A concrete draw, replaceable only before the wave runs: both thrash-consensus workers, three poll-label workers, two residual workers Sonnet called `steady_build_to_commit`, one weak-thrash worker. The other 26 workers are the hold-out and are not used to pick the winner.

`reread_cluster` on a stats card does not need this wave. A counter already answers it (cheap-analysis spike 3a). Spending Jev calls on "is the count at least three?" fails that spike.

## 4. What this field refuses to collapse

These are open at once. An approach may specialise. The pack does not close the others by omission.

- Summary author: programmatic, local, Flash, or a refusal (`prose_required`).
- Marker use: a screen that skips the model, a feature vector inside the card, or unused.
- Framing search: matrix wave, tournament, bandit on mechanical reward, evolutionary later.
- Who labels: nobody (mechanical), volume local, or a prose panel under `shape-rubric-v0` rules when a raw mount exists.

Picking one cell to run first is an operating decision in [`RESEARCH-OPS.md`](RESEARCH-OPS.md). It is not a finding that the other cells are inferior.
