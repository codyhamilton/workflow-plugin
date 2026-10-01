# Next experiments

**Status:** ordered spikes. None of them ship behaviour. None of them call `--call-jev`, edit hooks, or change progressive TERMS.

A failed gate stops the spikes that depend on it. It does not stop an independent measurement. After a prose-α failure the spikes that may still run are 0, 1, 2, 3a, 5, and 8 (table only, marked `agreement_withheld`). Spikes 3b's precision, 4's precision, 6's claim to have read prose it did not have, and 7's usefulness score do not run. Do not re-collect a failed rubric version under the same id.

## 0 — Segment inventory, no network

**Does:** Walk the four `T ≥ 75` fixtures plus `6c87c96bd9bb`, and the committed judge packs, and write a JSONL of segment rows. This is the segment strip: one row per window, not a new turn counter.

**Columns:** `worker_id`, `T`, `early_window_end`, `window_id`, `grid`, `start`, `end`, `evidence_class`, `excerpt_nonempty`, `reread_present`, `max_reread_count`, `compaction_event_count`, `source_path`.

**Done when:** `92a48e004519` shows `early_window_end = 120`; the control shows `70`; the turn-75 judge pack shows `evidence_class = stats_only`, `excerpt_nonempty = false`, `reread_present = true`, and `max_reread_count ≥ 3`; a row built only from the redacted JSONL shows `evidence_class = absent` and `reread_present = false`. `grid = label_60` inside the early window lists 60, 75, 90, 105, 120 where `T` allows. `grid = p0_75` starts at 75 and does not include 60. Both grids are present and named. No judge-pack row claims a turn-60 checkpoint, because those packs start at 75.

**Gate:** If `early_window_end` is computed from anything other than progressive `api_turn`, stop.

## 1 — Schema dry-run under the state guard

**Does:** Emit request JSON for `shape-v0`, `phase-sketch-v0`, and `early-signal-v0` on one `stats_only` segment and, if raw JSONL is mounted, one `prose` segment. The `stats_only` requests may ask only the mechanical `reread_cluster` question plus the reported compaction count. They must not include `no_checkable_step`, `anchor_divergence`, or `compaction_cycle` as questions a model is graded on. Emit one `session-checkout` / `Y_full` request from the existing builder and diff the question text against `session_checkout.py`. Emit one deliberately edited instruction and show that its stored `framing_id` hash differs and that an unregistered question blob returns `unregistered_framing`.

**Done when:** Every state JSON is ≤ 12_000 characters or the row says `unlabelable` with the length. The `Y_full` question text matches the builder byte for byte. The edited instruction does not use framing id `Y_full`. A prose-only schema pointed at the `stats_only` segment returns `reason: prose_required` and does not build a request that pretends the excerpts exist.

**Gate:** A schema that only fits by dropping the cumulative re-read block is ineligible for the stats corpus. Do not shrink that block away to make a prose tail fit.

## 2 — Batch dry-run, dedupe, caps

**Does:** Cross two framings, the `early_120` window, and the grid points from spike 0, for `early-signal-v0`, dry-run. Repeat one cell on purpose. Request `max_calls` 1 on a second invocation that would have POSTed more than one cell if `live` were set; in dry-run, confirm the cap counter ignores dry-run rows (the invocation is not rejected for size) and that a live-shaped request with `max_calls` 1 marks the extra would-POST cells `decision: missing`, `reason: cap`, without opening a socket.

**Done when:** The deduped cartesian size is the row count, the duplicate appears once, `duplicate_post_rate` is 0, dry-run rows are `decision: dry_run`, capped would-POST cells are `missing` / `cap`, and a `max_calls` of 257 is rejected before any row is sent. No `TYPESAFE_API_KEY` value appears in the file. Confirm by running with the variable set to a dummy and grepping the output.

**Gate:** Any live POST in this spike is a failed spike.

## 3a — Mechanical reread label, no panel

**Does:** On committed judge packs for the four `T ≥ 75` workers, at the checkpoints those packs actually contain (75 and later, not 60), set `reread_cluster` true when any path count is ≥ 3.

**Done when:** A JSONL matches a hand read of `92a48e004519` at turn 75 (true, a count of 10). No seat name appears. No α is computed. `compaction_event_count` is a column, not a label.

**Gate:** A row that asks Sonnet, Grok, Composer, or Flash whether the count is "at least three" fails the spike.

## 3b — Prose panel, pre-registered, one attempt

**Does not start** unless a raw mount gives `evidence_class: prose` for at least three of the four `T ≥ 75` workers. Otherwise the result is `insufficient_n` and later precision stays withheld. This is a successful stop.

**Rubric version** `shape-rubric-v0` is the terms in [`DESIGN.md`](DESIGN.md) as of this pack. Seats label only prose fields: `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `phase_sketch`, `trajectory`. They do not label `reread_cluster`. Early pass before hindsight. Outcome suffix withheld from the early pass. Checkpoints are workers at 75 and, where `T` allows, 90, 105, 120. Turn 60 only if `prefix(60)` is on the mount. α is reported per field, with items = workers at that checkpoint.

**Done when:** The file records `n_workers`, per-field α, and one sentence: the floor cleared, or it did not, or `insufficient_n`. A second labeling under `shape-rubric-v0` is not a spike. It is a protocol break.

**Gate:** If a field's α < 0.40 or `n_workers < 3`, that field's precision is withheld forever for v0. Do not drop a worker or a prefix after seeing α in order to cross 0.40. Do not point the target at `A0`.

## 4 — Capped TypeSafe live

**Does:** At most 32 live `jev-1.13.0` calls, one pre-registered framing from spike 1. Segments for a precision claim are the prose prefixes from spike 3b. Segments for a `reread_cluster_accuracy` claim may be the spike 3a packs and do not wait on 3b. Key required. Cache on. Second run of the same command must POST 0. Cache key includes the instruction string.

**Done when:** A table with `tokens_per_cell` (and `usd_per_cell` if the body carries it), `duplicate_post_rate = 0` on the second run, `reread_cluster_accuracy` if 3a ran, and prose precision either as a number under the spike 3b gate or `agreement_withheld` / `gold_missing`. `decision: missing` counted in its own rate.

**Gate:** A call that uses any model other than `jev-1.13.0`, a retry of a failed cell against `:8080`, or a precision number on a field whose v0 α failed, fails the spike. Abort above 32 POSTs.

## 5 — Local throughput

**Does:** Same segments as the stats half of spike 4, `backend: local`, `cache: bypass` on both passes so "warm" means the server, not the matrix cache. Server `WORKFLOW_LOCAL_LLM_URL`, default `http://127.0.0.1:8080/v1`. Record the model id the server reports and any sampling parameter it echoes. Do not write that id into OpenCode config. Windows end at or before `early_window_end`.

**Done when:** `segments_per_hour` for the first pass and the second pass, `seconds_per_cell`, parse-failure rate as `missing`. If the server is down, the spike's result is `missing` and the other spikes stay valid.

**Gate:** A fallback POST to TypeSafe, or a matrix-cache hit reported as a warm server, fails the spike.

## 6 — Flash arc, reviewed

**Does:** One qualitative arc of `92a48e004519` and one of `bb6165018de0`, only if spike 0 marked a mounted corpus `prose`. Sonnet 5.5 reviews both. Grok or Claude signs that review as the study convention in the Flash guidance, not as a workflow phase close. The arc does not enter the gold file.

**Done when:** Two artifacts with `review_status: sonnet_reviewed` and a sign-off line, or a recorded `reason: prose_required` if no raw mount exists. The refusal is a successful spike.

**Gate:** An arc written from empty excerpts fails the spike even if it reads well.

## 7 — Steer drafts at 50, 60, 75

**Does:** Three drafts for `92a48e004519` from `prefix(c)` only, each with `max_turn_seen` ≤ `c`. Flash authors when prose exists; otherwise a stats-only draft that cites counts. Sonnet reviews. No hook file is added. Usefulness is left null unless spike 3b cleared the foreshadow field's α. It is then one boolean per draft: named a panel foreshadow on `early_prefix`, or not.

**Done when:** Three JSON objects, `cited_turns` all `≤ c`, `max_turn_seen` ≤ `c`, length ≤ 500, no `additionalContext` key. Usefulness null is the correct output when 3b did not clear.

**Gate:** A draft that quotes a turn after `c`, or a usefulness score against a failed v0 panel, fails the spike.

## 8 — Decay table, arithmetic only

**Does:** If spike 3b produced per-seat prose labels, compute `confidence_points` for each seat and each foreshadow id across the grid points inside the early window. `missing` does not decrement. Stratify by the checkpoint where the seat first claimed the id. No model call. If 3b did not clear, still emit the table when labels exist, with `agreement_withheld` on every rank, and do not order signals by the points.

**Done when:** A table of claim checkpoint, points after each later step, `missing` counts, and `expired` if points hit 0. The table does not contain `gate_exit`, `confidence_min`, `A_maj`, or `A_gc`.

**Gate:** A pooled expiry that treats an API miss as a denial, or that averages seats, fails the spike.

## Explicitly not scheduled

- Wiring `TOOLS.md` into `packages/opencode-workflow-hooks` or a published npm package.
- `replay_progressive_gates.py --call-jev`.
- Retuning `gate_thresholds.py`, P0, or `A0`.
- A Qwen GGUF pin.
- Opus as a required fourth seat.
- Treating spike 5's local labels as gold.
- A second `shape-rubric-v0` panel.
