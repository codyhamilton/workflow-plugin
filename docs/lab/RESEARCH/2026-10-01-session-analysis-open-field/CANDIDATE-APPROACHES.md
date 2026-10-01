# Candidate approaches

**Status:** five competing end-to-end pipelines. **Confidence: not high.** None is selected. Each can be killed without the others dying. Resource figures are counts of agents and API calls for a first slice, not a schedule commitment.

Shared substrate, already specified and not rebuilt here: segment vocabulary and the 32-call dry-run cap from the [cheap-analysis design](../2026-10-01-cheap-analysis-typesafe-opencode/DESIGN.md); theme strata and marker families from [`OPEN-FIELD.md`](OPEN-FIELD.md); gold that is **not** `A0`.

A first slice that finishes as `prose_required`, `missing` (server down), `gold_missing`, or `agreement_withheld` is a successful stop. A slice that prints a precision number anyway has left its gate.

## Comparison

| | Stats→Jev tournament | Summary-then-judge | Local segment swarm + Flash arbiter | Marker screen, prose on the margin | Frozen-card framing search |
|--|----------------------|--------------------|--------------------------------------|-------------------------------------|----------------------------|
| Id | `stats-jev-tournament` | `summary-then-judge` | `segment-swarm-arbiter` | `marker-screen-margin` | `frozen-card-search` |
| Thesis in one line | The early card is already numeric; spend Jev on framings of that card | A reviewed summary is the only object expensive seats should share | Local models read windows; Flash writes one card where they conflict; Jev sees the card | Most of n = 34 never needs a model; prove the screen before any framing | Once a card is frozen, search framings under the cap instead of factorial expansion |
| Needs raw prose to start | No | Yes, or an honest refusal | Only for the Flash arbiter | No | No, if the frozen card is the stats card |
| Live Jev in the first slice | 0, then one wave of 32 | 0 until fidelity passes, then ≤ 32 | 0 until an arbiter card exists, then ≤ 32 | 0 | 0 in the protocol slice; 32 only in a later pre-registered wave |
| Can finish on committed packs alone | Dry-run yes. Theme score yes, as a rank against agreement themes, with Jev still dry | No. Thrash prototypes have empty excerpts | Local half can be attempted on pack windows; Flash half refuses on empty excerpts | Yes | Protocol and dry-run yes |
| First-slice agents | 1 collector for the card builder and the dry-run | 8 Flash cards, 8 Sonnet reviews, 1 sign-off, only if a mount exists | 1 local server, Flash on the conflict subset, Sonnet on those arcs | 1 collector, no model | 1 collector for the search log; WSM registers the wave |
| Main confound | Jev repeats a counter the card already contains | Summary invents a narrative for a 36-character prefix | Local disagreement is noise, so Flash re-reads everything and the savings vanish | A rule fit on the two prototypes | The search picks a winner on the same 8 workers used to score it |
| Kill (short) | Both prototypes leave the extreme cell, or poll workers enter it | Fidelity contradictions on non-empty workers, or thrash cards that state counts the pack does not | Parse-failure or conflict rate sends more than half the workers to Flash | Thrash/poll overlap in the published extreme cell | Winner's question JSON was not registered before the run, or it loses to the random baseline on the hold-out |

## 1. Stats→Jev tournament

**Thesis.** Shape themes that seats agreed on are visible in hybrid_v0 cumulative fields by checkpoint 75–105. A TypeSafe framing tournament over a programmatic stats card will separate thrash consensus from poll labels at a recorded token cost, or it will show that the model adds nothing a rank on the card does not already show.

**Pipeline.**

1. Build one `stats_card` per worker from checkpoints ≤ 120 (marker families in [`OPEN-FIELD.md`](OPEN-FIELD.md)). No tail prose, even when excerpts are non-empty. That omission is the point of this approach.
2. Publish the rank table with zero model calls. This is the baseline the tournament has to beat.
3. Register four framings before any POST. All four use `schema_id: early-signal-v0` and `model: jev-1.13.0`. Suggested contrast, replaceable only before registration: binary foreshadow ids; Likert collapsed by a rule written in the same registration; binary ids with `monitor_present` called out as its own choice; the same binary ids with the instruction "do not infer a story beyond the counts."
4. Dry-run the 8 × 4 wave (stratified eight in the open-field note). Confirm `duplicate_post_rate = 0`, state ≤ 12_000 characters, no key in the file.
5. One live wave, 32 calls, cache on. Second invocation of the same command must POST 0.
6. Score: for each framing, whether the two thrash-consensus workers are flagged and whether any poll-label worker is flagged. Compare that pair of lists to the zero-call rank table. A framing that matches the rank table and costs tokens has not won. It has tied a counter.

**Proof gates.**

- Card round-trips to pack counts (mismatch rate 0) on all 34.
- Dry-run wave matches cheap-analysis spike 2's cap and dedupe rules.
- After the live wave: a table of `tokens_per_cell`, poll-overlap list, and thrash flags, per framing. If prose gold for non-mechanical foreshadow ids is absent, those ids are `gold_missing` and only `reread_cluster` plus the pre-registered theme flags from **counts the model was given** are scored. Asking the model to rediscover a number printed in the card is reported as `echo`, not as accuracy.

**Resources.**

| | First slice |
|--|-------------|
| Agents | 1 collector (card + dry-run). No gold seats. No Flash |
| API calls | 0 live. Optional confirmation wave: **32** `jev-1.13.0` POSTs, then 0 on replay |
| Week-1 build list | Stats-card JSONL for 34 workers; framing registry with hashes; dry-run batch log. No plugin, no `opencode.json` edit |

**Kill criteria.**

- The zero-call extreme cell already separates the two prototypes from all four poll-label workers. Further Jev framings of the same card are not scheduled (the tournament's premise, that the model must interpret the card, is idle).
- Or a live framing flags a poll-label worker together with both prototypes.
- Or any POST uses a model other than `jev-1.13.0`, or a second rubric pass rewrites a framing after seeing answers.

## 2. Summary-then-judge

**Thesis.** Comparable judgements need a comparable narrative object. A schema-locked summary of the early prefix, authored by Flash, reviewed by Sonnet, signed as a study artifact, is what TypeSafe should see. Stats cards miss the poll sentence ("waiting on both monitors") that seats actually cited.

**Pipeline.**

1. Mount raw JSONL or stop with `prose_required`. Committed packs are not enough: the thrash prototypes' early tails are empty, and several poll rows are where the prose is.
2. Flash fills one summary schema per worker for a pilot of **8**: both thrash-consensus workers, `87a380bc64ff`, `bb6165018de0`, `6e06ab86aa72`, two `steady_build_to_commit` workers, one weak-thrash worker. Schema sections, fixed: copied counts (must match the pack), compaction events as a list of checkpoint counts, a phase sketch using the cheap-analysis tags, a noise line, and at most one short excerpt quote with `turn` ≤ `early_window_end`. Free prose outside those sections is discarded, not stored.
3. Sonnet 5.5 reviews each card for contradictions against the pack and for quotes past the window. Grok or Claude signs the review set. The cards do not become gold.
4. TypeSafe framings run on the **signed card**, not on the transcript. Same 32-call discipline as the tournament, and only after fidelity passes.
5. Usefulness: the judge's theme matches a theme ≥2 seats recorded. Usefulness is null on `residual`.

**Proof gates.**

- Pilot either records `prose_required` or produces 8 cards with `review_status: sonnet_reviewed` and a sign-off line.
- Zero count-contradictions on the reviewed cards. A contradiction fails the card, not the worker's gold.
- `max_turn_seen` ≤ `early_window_end` on every quote.
- Judge wave, if run, reports tokens and theme flags separately from the stats-tournament wave so the two approaches can be compared on the same 8 workers.

**Resources.**

| | First slice |
|--|-------------|
| Agents | 8 Flash drafts, 8 Sonnet reviews, 1 sign-off pass over the set. Collector writes the schema and the fidelity diff |
| API calls | 8 Flash completions plus review-agent usage, then **0** Jev until fidelity passes. A later judge wave is ≤ **32** POSTs |
| Week-1 build list | Summary schema; fidelity diff script against pack counts; mount probe. Flash sessions only if the probe finds prose |

**Kill criteria.**

- Mount missing: the approach stops. It does not summarise empty excerpts.
- Sonnet finds a count contradiction on more than one of the eight cards.
- The thrash-consensus cards contain a narrative claim that is not a count, a flat text-char field, or a quote of assistant text that exists. Those prefixes are tens or low hundreds of assistant characters; a paragraph of motive is fabrication.
- Usefulness scored against `A0` or against a failed `shape-rubric-v0` field.

## 3. Local segment swarm + Flash arbiter

**Thesis.** A single prefix card hides where in the first 120 turns a pattern starts. Local models can label every segment cheaply. Flash should see only the segments the local labels disagree on, and TypeSafe should see only the arbiter card. Volume stays off the expensive seats.

**Pipeline.**

1. Cut each early prefix into segments whose ends are ≤ `early_window_end`. Default cut, pre-register before any local call: the `label_60` grid points that exist (60 only when a mount has `prefix(60)`; committed packs start at 75), each segment being the hybrid row at that checkpoint, which already represents `prefix(c)`.
2. Local server labels each segment with the closed phase-tag set and a theme guess from `{thrash_bundle, poll_monitor, productive, unknown}`. `cache: bypass`. Record the server's model id. Do not write it into OpenCode config.
3. A worker is **stable** when every segment that exists agrees on the theme guess and all responses parse. Stable workers produce a programmatic card plus the local tags. No Flash.
4. A worker is **in conflict** when tags differ or any segment is `missing` / `unknown`. Flash writes one arbiter card from those segment cards (not from the raw file), under the summary schema. Sonnet reviews the arbiter cards only.
5. Jev, later, runs on arbiter cards plus a sample of stable cards, so a "stable" local consensus can still be wrong. The sample is inside the 32-call cap.

**Proof gates.**

- If the server is down, the result is `missing` and the other approaches stay valid (same rule as cheap-analysis spike 5).
- Parse-failure rate and conflict rate are published on the stratified 8 and, if cheap, on all 34.
- Flash is invoked only for conflict workers. The log lists worker ids.
- No TypeSafe call appears in a local failure path.

**Resources.**

| | First slice |
|--|-------------|
| Agents | 1 local server process. Segment count on the stratified 8 is the number of checkpoints ≤ 120 those workers have (on the order of **1–4** each, so about **20** local completions, not 34 × many). Flash only for the conflict subset. Sonnet reviews that subset |
| API calls | 0 TypeSafe in the first slice. Local calls as above. Flash calls equal to the conflict count, expected to be a handful if the thesis holds, and equal to 8 if it does not |
| Week-1 build list | Segment cutter over existing pack rows; local request log with `cache: bypass`; conflict rule written down before the server is queried |

**Kill criteria.**

- Conflict or parse failure on more than **4 of the 8** stratified workers. The arbiter is then the whole panel, and this approach has collapsed into summary-then-judge at higher operational cost.
- A local response is repaired by a TypeSafe retry.
- A stable label of `thrash_bundle` on any poll-label worker in the 8. That kill fires even if Flash would have caught it, because the savings depend on trusting stable labels enough to skip Flash.
- Windows whose end is past `early_window_end` were sent.

## 4. Marker screen, prose on the margin

**Thesis.** n = 34 is mostly residual and `unclear`. The thrash bundle and the poll family are rare and already separated in the cumulative fields. A programmatic screen should decide who deserves prose or Jev. Models run only on the margin the screen calls ambiguous. Predictive power against **T** and against **theme** is measured before any of those models are hired.

**Pipeline.**

1. Compute every marker family on all 34 workers from checkpoints ≤ 120. Emit one JSONL row per worker: features, `checkpoints_seen`, stratum (thrash consensus, poll label, shared monitor-wait, weak thrash, residual), `T`.
2. Publish ranks, poll-overlap lists, and both Spearman figures from [`OPEN-FIELD.md`](OPEN-FIELD.md) §2. No threshold object is created in this step.
3. Define **ambiguous** only after that table exists, in a separate pre-registration that a reader can diff: for example "not in the frozen-text and rising-compaction extreme, and not `mutation_present` with `text_growth` above the residual median." The example is not in force until it is registered as its own id.
4. Prose or Jev is legal only for workers the registered rule marks ambiguous, plus a fixed audit sample of one thrash prototype and one poll worker (so a clear cell is still spot-checked). Everyone else is a screen decision with a feature row and no model.
5. Length result is the Spearman pair and the quartile table. It is not fed back into the theme rule.

**Proof gates.**

- Feature JSONL covers 34 workers, 0 network calls, every cited turn in the feature derivation ≤ 120.
- Both thrash prototypes' percentiles and the full poll-overlap list are in the summary.
- Spearman with and without the two prototypes, for each numeric family.
- A follow-on boolean rule, if anyone writes one, is one id and one score. It does not edit this distribution paper.

**Resources.**

| | First slice |
|--|-------------|
| Agents | 1 collector. No Flash, no local, no Jev, no new gold seats |
| API calls | **0** |
| Week-1 build list | The feature JSONL, a one-page rank table, the poll-overlap list. This slice is the whole proof gate for the distribution claim |

**Kill criteria.**

- Any feature uses a checkpoint > 120 or a seat's `recommended_exit`.
- The extreme cell that contains both thrash prototypes also contains any worker in the poll-label set. The screen does not proceed to a prose margin; the family definitions come back to the open field.
- A boolean cut is chosen by inspecting the two prototypes and then reported as predictive. That cell is void.
- The write-up recommends a checkout turn or a `confidence_min` change.

## 5. Frozen-card framing search

**Thesis.** The expensive axis is framing, not summarisation. Freeze one card (the stats card unless a later cycle has a fidelity-passed summary card), then spend a 32-call budget on a search that can lose to a random baseline. Evolutionary and bandit ideas are legal only where the reward does not look at the theme labels used for the final claim.

**Pipeline.**

1. Freeze the card hash per worker. A card change voids the search.
2. Split the budget in the registration, before any POST: **8** calls are a random framing drawn from the registered pool (the baseline arm); **24** calls are the search arm. Four framings × six search workers, or another split with the same 8/24 cut. The stratified hold-out of 26 from the open-field note stays untouched by both arms.
3. **Matrix arm** (default if this approach is the one started): the 24 calls are a pre-registered 6 × 4 matrix. No adaptation.
4. **Bandit arm** (alternative, not simultaneous): reward is mechanical only — JSON parse success and `reread_cluster` echo/error against the printed count. Theme labels are withheld from the allocator. After 24, the framing with the best mechanical reward is applied once to the hold-out only if a **new** budget is registered. This arm does not claim a theme winner.
5. **Evolutionary arm** (later, not in the first slice): mutate instruction text of the matrix winner. Offspring are registered (hashed) before they are sent. Fitness is the mechanical reward. Any offspring whose hash was not on the pre-run list is `unregistered_framing` and is not sent.
6. Report search-arm mechanical reward minus baseline-arm mechanical reward. A negative or zero difference kills the claim that search beat registering four prompts.

**Proof gates.**

- Registration file lists framing hashes, the baseline draw, and the worker ids before the batch log's timestamps.
- `duplicate_post_rate = 0`. Replay POSTs 0.
- Baseline arm and search arm both have counts. A wave that spends all 32 on the search arm is void.
- Theme scoring, if added later, uses the hold-out and a new registration. It is not computed on the search workers and then called a confirmation.

**Resources.**

| | First slice |
|--|-------------|
| Agents | 1 collector to emit the dry-run and the registration template. WSM (Grok, fresh context) writes the registration. No gold seats |
| API calls | **0** until a registration is signed off as a cycle. The wave itself is **32** POSTs, of which 8 are baseline |
| Week-1 build list | Card-hash manifest; framing pool of at least 8 registered question blobs (so a random arm has somewhere to draw); dry-run that shows the 8/24 split without opening a socket |

**Kill criteria.**

- The winning framing's hash is absent from the pre-run registry.
- Search-arm mechanical reward ≤ baseline arm.
- The allocator's reward function reads `shape_label`, `shape_detail`, or stratum.
- A second wave under the same registration id.

## What a head-to-head would need

These pipelines share workers and must not share a live budget in the same cycle. A comparison cell, registered only after at least two first slices have closed:

- Same 8 workers.
- Same theme strata.
- Costs in calls and, when the provider returns them, tokens.
- Each approach's kill either fired or its proof gate cleared.
- The write-up still names both. Clearing a gate is not a mandate to delete the others.

No approach in this file is allowed to declare itself the harness. The cheap-analysis spikes remain the path that builds shared machinery (segment inventory, dry-run, dedupe). These five say what to point that machinery at.
