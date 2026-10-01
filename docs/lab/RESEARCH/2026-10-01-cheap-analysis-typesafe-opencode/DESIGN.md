# System design — cheap analysis harness

**Status:** resolved recommendations for a harness that is not built. **Confidence: not high.** Soft until Cody accepts a behaviour change. The bounding plan is [`docs/plans/07-cheap-analysis-harness/DESIGN.md`](../../../plans/07-cheap-analysis-harness/DESIGN.md). Contracts a brief would cite live there; this file is the recommendation text and the measurement plan.

## What the system is

An offline harness and a small set of OpenCode tools, specified here and not registered, that let a Flash session or a local llama.cpp server:

1. Write a refined summary or a long qualitative arc when the window actually contains prose.
2. Classify short windows, focused on the first 120 `api_turn`s, for shape, phase sketch, and early signals.
3. Try many TypeSafe framings over many segments, with a cache, a cap, and a dry-run default.
4. Emit counterfactual steer drafts at turns 50, 60, and 75 without a live Claude hook.

Progressive checkout replay stays the owner of `gate_exit`. This harness does not write that field.

## Terms this study adds

Progressive [`TERMS.md`](../2026-10-01-progressive-jev-session-gates/TERMS.md) is unchanged. Where this file uses `api_turn`, `prefix(c)`, `T`, `hybrid_v0`, `runaway`, `low_progress`, `context_thrash`, or `scope_drift`, those words mean what TERMS and the gold rubric say.

| Term | Meaning here |
|------|----------------|
| `early_window_end(T)` | `min(120, T)` |
| `early_prefix` | `prefix(early_window_end)` |
| Outcome suffix | Turns after 120. Hindsight only |
| `evidence_class` | `prose` or `stats_only`, from the artifact in hand |
| `trajectory` | First match: `early_thrash`, `early_other`, `late_pivot`, `steady`, `unlabeled` (hindsight seat, prose only) |
| Early signal | A foreshadow id justified only by turns `≤ early_window_end` |
| Foreshadow ids (v0) | `reread_cluster`, `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `none` |
| `phase_sketch` | Ordered tags from `orient`, `search`, `edit`, `verify`, `replan`, `stall` |
| `confidence_points` | Starts at 3 on a claimed signal. Minus 1 per failed revalidation. Expired at 0 |
| Steer draft | ≤500 characters from `prefix(c)` at `c ∈ {50, 60, 75}` |

`trajectory` is a total order, first match wins. `early_thrash`: the early prefix supports rubric `runaway` or `context_thrash`, and either `T ≤ 120` or the outcome suffix supports one of those two. `early_other`: the early prefix supports `scope_drift` or `low_progress` and the row is not `early_thrash`. `late_pivot`: the early prefix supports none of the four rubric patterns, and the outcome suffix supports `runaway`, `context_thrash`, or `scope_drift`. `steady`: the early prefix supports none of the four and the row is not `late_pivot`. `low_progress` in the suffix alone stays `steady`. `unlabeled`: no hindsight seat. A stats-only pack can compute `reread_cluster` (a path count ≥ 3, the rubric's "at least three") without a seat. It can report `compaction_event_count`. It cannot declare `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `phase_sketch`, or `trajectory`. Those need `prose`. The first spike publishes the compaction distribution and does not lock a threshold. An early-signal row carries `justifying_turns`, all `≤` the prefix end.

`phase_sketch` tags are not workflow phases and not `Workflow-Phase` trailers.

The foreshadow crosswalk, diagnostic only:

| Foreshadow | Rubric pattern |
|------------|----------------|
| `reread_cluster` | `runaway` |
| `compaction_cycle` | `context_thrash` |
| `no_checkable_step` | `low_progress` |
| `anchor_divergence` | `scope_drift` |

## Resolved recommendations

### R1 — Sibling study, read-only TERMS

Shape, the 120-turn window, claim decay, and steer drafts are this pack's vocabulary. They are not amendments to P0 `(75, 15)`, `A0`, `Y_full`, or `confidence_min`. A cell that needs a different meaning says so in its `schema_id` and does not overwrite the checkout builders.

### R2 — Role split

| Tier | May author | Excluded from |
|------|------------|----------------|
| DeepSeek Flash via OpenCode (`deepseek/deepseek-flash`) | Summaries, long arcs, draft briefs, steer drafts, `inline` matrix answers | Panel α, shape-gold aggregate, phase sign-off |
| Local llama.cpp at `WORKFLOW_LOCAL_LLM_URL` (default `http://127.0.0.1:8080/v1`) | Volume labels on windows ending at or before `early_window_end` | Panel α, OpenCode's default provider map, prose claims on `stats_only` windows |
| Sonnet 5.5 | Review of Flash summaries, briefs, and steer drafts | Being skipped when Flash wrote the draft |
| Claude Code or Grok | Sign-off on a reviewed Flash artifact; Grok may sit a gold seat | — |
| Sonnet (signed), Grok, Composer | Shape-gold seats. Opus optional, not required | — |
| TypeSafe `jev-1.13.0` | Structured answers for a named `schema_id` | Hard pass/fail. `assert_phase --deterministic` stays the kill line. No fallback model |

Flash output is stored with `author_tier: flash` and `review_status: unreviewed`. Sonnet sets `sonnet_reviewed`. Sign-off is a separate act and follows the existing guidance. Local rows carry `seat_class: volume`.

The local server is for high-volume eval of windows, schemas, and Jev-shaped questions. It is not the default model for other agents. This pack does not edit `opencode.json`.

### R3 — Evidence class before any summary

`analysis.load_segment` sets `evidence_class`.

- Committed redacted JSONL under `maps-5h-workers/`: `evidence_class: absent` for re-read and prose. Turn counts and tool-name histograms are still there. Re-read paths and compaction counts from a replay of those files are empty (`reread_present: false`). `stats_only` is reserved for a judge pack (or a raw mount) that actually carries the aggregates.
- Committed judge packs: `stats_only`. The `92a48e004519` row at turn 75 already has a path count of 10 and `compaction_event_count` 12, with empty excerpts. That is inside the early window. It is an observation about the pack, not a trajectory label.
- Mounted raw JSONL (`WORKFLOW_PROGRESSIVE_CORPUS` or an explicit path): `prose` when assistant text is non-empty.

A Flash qualitative job on `evidence_class` other than `prose` is not stored. The tool returns `refused: prose_required`. This avoids a polished summary of an empty tail.

### R4 — Two references, and checkout gold is neither

`reread_cluster` on a judge pack is the predicate "some path count ≥ 3". The matrix scores models against that predicate (`reread_cluster_accuracy`). No seat labels it. Asking a panel to read a count that is already in the bundle would repeat the checkout failure on a question a counter answers, and the committed packs have no turn-60 row and empty excerpts.

Prose fields (`compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `phase_sketch`, `trajectory`) use a new gold file. They do not use `A0`, `A_maj`, `A_gc`, or `session_kind`.

Until that file exists, panel agreement is null and `reason: gold_missing`. Cost, throughput, and `reread_cluster_accuracy` are still reported.

Panel protocol, registered here as `shape-rubric-v0` before any seat runs:

- Prose only. A spike with fewer than three workers of `evidence_class: prose` ends `insufficient_n` and does not compute α.
- Early-signal pass sees only the prefix at `c ≤ 120`, records `justifying_turns`, and does not see the outcome suffix, Jev answers, Flash drafts, or local labels. Turn 60 is in the pass only when raw `prefix(60)` is mounted. Committed P0 packs start at 75.
- Hindsight pass may set `trajectory`, and is saved after the early pass. Prefer a different seat.
- Counting seats: Sonnet signed, Grok, Composer. Opus is optional.
- α is Krippendorff's alpha **per field**, items = workers at a stated checkpoint (nested prefixes of one worker are not the N). Floor 0.40 is necessary and is not sufficient below `n_workers` 3. The checkout result 0.1189 is not evidence these fields will clear. This design does not predict that they will.
- One attempt per rubric version. A failed version's precision stays withheld. A retry is a new version written down before the new labels exist.
- Below the floor, that field's precision and recall are `agreement_withheld`. Other fields are not rescued by a neighbour clearing the floor.

`session-checkout` remains a legal `schema_id` so a regression cell can show that a new framing did not silently edit `Y_full`. Those cells report checkout agreement only as `checkout_diagnostic`, unfit while H5 is failed. A full-schedule checkout cell is the one case that may set `hide_outcome_suffix` false, together with `trajectory-v0`. `shape-v0`, `phase-sketch-v0`, and `early-signal-v0` may not.

### R5 — Decay is a claim counter inside the early window

On the progressive label grid (`60 + 15k`) while the checkpoint is `≤ early_window_end`:

- The table is per seat. A signal that seat claims at `c` gets `confidence_points = 3`.
- The same seat is asked the same id at each later grid point still inside the window.
- A confirmation leaves the points unchanged.
- A denial by that seat subtracts 1. A `missing` answer does not. It is a separate column.
- At 0 the signal is `expired` for that seat. Pooled expiry requires every counting seat that claimed it to have reached 0. There is no majority shortcut.
- Rows are stratified by the checkpoint of the claim, so a claim at 105 is not ranked against a claim at 75.

Expired is not `checkout` and not `gate_exit`. Points are not `checkout_confidence`. P0's `confidence_min = 3` stays fixed. A schedule that lowers `confidence_min` as `k` grows is a different cell (`threshold_decay_v0`). It is not the recommendation, because it would move the checkout study's open axis under a new name.

Revalidation stops at `early_window_end`. Later turns describe the outcome. They do not create early signals.

### R6 — Steer drafts are counterfactual text

For each chosen worker, three drafts, at `api_turn` 50, 60, and 75, each from `prefix(c)` only, at most 500 characters, with `cited_turns`.

Author: Flash, when `evidence_class` is `prose`. On `stats_only`, the draft may cite only aggregate fields and must set `evidence_class: stats_only` so a reader does not treat a path count as a narrative. The row includes `max_turn_seen` ≤ `c`. Reviewer: Sonnet 5.5, then a Claude or Grok sign-off as the study convention in the Flash guidance, not as a phase close. Usefulness stays null until the prose foreshadow field has cleared its own α gate. The score is whether the draft named a foreshadow the panel marked on `early_prefix`. A human or Grok records it. Flash does not.

Turn 50 has no progressive checkout label. The experiment does not pretend it does.

The JSONL has no `additionalContext` key. Progressive TERMS still owns the decision to leave that channel deferred. This recommendation is the measurement Cody can read before that decision.

### R7 — One TypeSafe handler, dry-run default, shared client

`jev.classify` and `typesafe.classify` are one handler. The batch dedupes by cache key, which does not include the tool name.

Live TypeSafe requires `live`, `confirm_live`, and `TYPESAFE_API_KEY`. Otherwise the result is `decision: dry_run` or `decision: missing` with `reason: missing_api_key`. No other model is substituted. A later implementation posts with `jev_client.post_systemone` and does not add a third HTTP copy next to the progressive replay helper. This plan does not change that helper.

Cache key: sha256 of the full outbound body (endpoint, model, questions, state, instruction string, sampling parameters). Namespaces `typesafe` and `local` do not share rows. A hit returns the stored body and does not POST. `cache: bypass` is how a warm-server measurement avoids counting a matrix hit as a warm server.

Caps, per invocation of `analysis.batch_trial`: the count is cells that would POST. `max_calls` 32 by default, rejected above 256, and rejected above 32 unless `budget_tokens` is present. `max_concurrency` 4, maximum 8. One HTTP failure is `missing` for that cell. It is not retried on the other backend. The wrapper catches `jev_client`'s process-exit on a missing key and returns `missing`. The client file is unchanged.

`classify.py` is not called.

### R8 — Tools are a sibling plugin, unwired

When a later plan wires tools, it adds a new plugin factory whose init hook is `tool`, as a second `plugin` entry. It does not add a `tool` key to `WorkflowSignalsPlugin`, does not flush batches, and does not import `process_hook_input`. `install.sh` stays skills-only.

This PR's sketch is [`TOOLS.md`](TOOLS.md). No `packages/` diff.

### R9 — Matrix axes and what a success looks like

Axes:

| Axis | Values |
|------|--------|
| `model_tier` | `typesafe`, `local`, `inline` |
| `framing_id` | slug + hash of question JSON |
| `segment` | `window_id` (`early_120`, `grid_15`, or an explicit range) × `snapshot_mode` (default `hybrid_v0` / `N=8` / excerpt 400) × `evidence_class` |
| `schema_id` | `session-checkout`, `shape-v0`, `phase-sketch-v0`, `early-signal-v0`, `trajectory-v0` |

`grid_15` for `early-signal-v0`, `shape-v0`, and `phase-sketch-v0` includes only checkpoints `≤ early_window_end`. A checkout regression cell may use the full P0 schedule and must set `schema_id: session-checkout`. A hindsight trajectory cell may see the suffix only as `trajectory-v0` with `hide_outcome_suffix` false.

Headline metrics, in the order they become available:

| Metric | When it is reportable | Target shape |
|--------|----------------------|--------------|
| `duplicate_post_rate` | Any live or dry-run batch | 0 after dedupe |
| `tokens_per_cell` | Provider `usage` present | Recorded, no invented rate card |
| `usd_per_cell` | Provider returns money | Otherwise null |
| `seconds_per_cell` | Local tier | Recorded |
| `segments_per_hour` | Cold cache and warm cache, same segment policy | Local and Flash/`inline` each reported |
| `reread_cluster_accuracy` | Judge pack has `reread_paths` | Agreement with path count ≥ 3. No α. Not a panel |
| `early_signal_precision` | That field's prose gold exists, `n_workers ≥ 3`, that field's α ≥ 0.40 on the pre-registered rubric version, at least two framings when a winner is claimed | Fraction of predicted foreshadow ids the panel marked |
| `early_signal_recall` | Same gate | Secondary. Precision is the headline because a false foreshadow becomes a bad steer |
| `trajectory` / `phase_sketch` agreement | That field's own α gate | Withheld independently of the foreshadow gate |

`agreement_withheld` is a successful honest output when α is below 0.40. A run that prints a precision anyway has left the metric.

Non-metrics: `session_kind`, classify log rows, checkout α, `A0`, `gate_exit`, `max_allowed_turns`.

### R10 — Corpus for the first spikes

Start with the four committed `T ≥ 75` fixtures and the judge packs that already exist for them (P0 packs for the two smoking guns, expansion packs for `0aab88c525de` and `036ff3ed4a89`). Leave `0853bc21d3aa` out until its JSONL is in the manifest. Leave `6c87c96bd9bb` in as the negative control for windowing (`T = 70`, so `early_window_end = 70`, and P0 checkpoints are empty) and out of `T ≥ 75` precision.

Do not vendor `/home/codyh`. Prose spikes set `WORKFLOW_PROGRESSIVE_CORPUS` or refuse.

### R11 — What this does to the progressive experiments

The decay counter and the steer drafts are experiment designs the progressive study can read. They do not change its harness.

- A survival table of `confidence_points` is arithmetic on early-signal labels. It does not call Jev and does not move `confidence_min`.
- Steer drafts are a file a person can compare to later gold. They are not hook responses, so they can be reviewed with no Claude session in the loop.
- A `session-checkout` regression cell, dry-run, shows whether a framing trial accidentally forked `Y_full`. Live checkout calls stay behind the progressive CLI's `--call-jev`, which this pack does not launch.

H1–H4 stay untested. This design does not claim to unblock them. Clearing shape-gold α is a different floor on a different label.

## Non-goals

- Live `--call-jev`, live `assert_phase`, or any POST from this change.
- Edits to `packages/opencode-workflow-hooks`, `tools/driver`, `tools/transcript`, skills, or progressive proofs.
- Replacing Sonnet, Grok, or Composer seats with Flash or Qwen.
- Classify calibration, `human_label` gates, or a session-kind KPI.
- Per-turn Jev inside a worker loop (`GOALS.md` non-goal).
- A compaction-count threshold presented as a rubric.
- Pinning a GGUF filename the repo has not recorded.
- An accepted white paper. Recommendations here are the harness shape. Product behaviour waits on Cody.

## Ownership

| Domain | Citation source | Later implementation, not this PR |
|--------|-----------------|-----------------------------------|
| Role registry | Plan + R2 | Operator config only |
| Segment index | Plan segment contract, R3, R10 | Lab proof script under this pack |
| Trial matrix | Plan matrix contract, R4, R7, R9 | Same proof tree, importing `jev_client` |
| OpenCode tools | [`TOOLS.md`](TOOLS.md), R8 | Sibling plugin, separate plan |
| Steer drafts | R6 | JSONL artifact, separate plan |
| Shape gold | R4, R5 | Panel on existing packs, separate plan |
