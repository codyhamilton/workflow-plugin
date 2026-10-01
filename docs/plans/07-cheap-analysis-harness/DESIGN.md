# Cheap analysis harness

## Intent

User request, verbatim:

> ## Goal
> Design (lab research pack + system design doc — **no behaviour-shipping code** unless a tiny non-wiring sketch is needed for clarity) an efficient test harness and analysis pipeline that uses **DeepSeek Flash (via OpenCode)** and/or **local llama.cpp/Qwen :8080** to:
> 1. Produce refined session summaries and long-form qualitative analysis of agent transcripts (Maps-style long runs).
> 2. Segment-by-segment strip/classify early turns for shape/phase/early-signal work.
> 3. Trial large numbers of differently framed TypeSafe/Jev calls to discover which prompts/schemas work better.
> 4. Extend the **OpenCode plugin** with **custom tools** that wrap TypeSafe API calls so Flash/local can cheaply fan out many framed requests.
>
> Open a PR under `docs/lab/` (research pack + design). Do **not** change live hooks, Jev gates, or product behaviour.
>
> ## First shell (required)
> Before other work:
> ```bash
> export WORKFLOW_WORKSPACE="${WORKFLOW_WORKSPACE:-$(pwd)}" && curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/tools/cloud-env/bootstrap-workflow-skills.sh | bash && python3 "$HOME/.cache/workflow-plugin/tools/driver/check_skills.py"
> ```
>
> ## Constraints / standing guidance
> - Repo: `codyhamilton/workflow-plugin` (this checkout).
> - Soft-until-Cody: draft measured recommendations; wait before shipping behaviour.
> - Flash may draft freely; Sonnet 5.5 reviews Flash work; phase sign-off is Claude/Grok only — this pack is **your** (Grok) design, so resolve recommendations yourself.
> - Local llama.cpp/Qwen :8080 is for **high-volume** eval (hooks, integrations, Jev conditions). Other agents default DeepSeek via OpenCode; llama is not the global OpenCode default.
> - Progressive Jev gold: early signals must be in first **~120 turns** (later = outcome). Shape analysis: late_pivot vs early_thrash; phases; early foreshadowing. Progressive 15-turn revalidation + decaying confidence bar; validation-phase handoff via additionalContext steer ~50/60/75.
> - Existing offline replay harness + progressive TERMS live under `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/`.
> - OpenCode hooks plugin already shipped; look at OpenCode plugin layout for where custom tools would plug in.
> - TypeSafe/Jev: cheap classify/eval; assert_phase without TYPESAFE_API_KEY dry-runs; no LLM fallback for hard assert.
> - Prefer measurement plans with success metrics; no classify-as-KPI path.
>
> ## What to research (in-repo + design)
> Inventory existing pieces first:
> - OpenCode plugin / TypeSafe / Jev client / offline replay fixtures
> - Any prior lab papers on Jev cheap judgement, progressive gates, analytics sink
> - How session packs/gold seats are structured today
>
> Then design a **system** covering:
>
> ### A. Role split
> - Flash: refined summaries, long qualitative arcs, draft analysis briefs
> - Local Qwen/llama :8080: segment strip → classify (high volume, short windows ≤120T focus)
> - Sonnet/Grok: review Flash drafts; gold/panel seats stay expensive models
> - Jev/TypeSafe: structured schema calls for A0/shape/phase/signal trials
>
> ### B. OpenCode custom tools
> Propose concrete tool surfaces Flash/local can call, e.g.:
> - `typesafe.classify` / `jev.classify` with pluggable prompt+schema+fixture id
> - batch trial runner (N framings × M segments)
> - pack/segment loader (turn windows, ≤120 early window helper)
> How tools map into the existing OpenCode plugin; auth via TYPESAFE_API_KEY; rate/cost guards.
>
> ### C. Efficient test harness
> - Offline-first: historical transcript packs (Maps T≥75 shape-qual inventory)
> - Matrix: (model tier × framing × segment policy × schema) → agreement vs gold shape/early_signals
> - Caching, dedupe, parallel batching, cost/latency budgets
> - How this feeds progressive decay-bar / validation-handoff experiment design without live Claude
> - Success metrics: early-signal precision vs gold panels; cost per trial; throughput on local vs Flash
>
> ### D. Deliverables in PR
> 1. `docs/lab/RESEARCH/<date>-cheap-analysis-typesafe-opencode/` RESEARCH.md (or equivalent) + DESIGN.md system design with **Resolved recommendations**
> 2. Short NEXT-EXPERIMENTS.md with ordered spikes (still no behaviour ship)
> 3. Optional: stub tool interface sketch / OpenAPI-ish tool defs as markdown only (or non-wired examples under docs/lab) — **no** production wiring
> 4. Update lab index / GUIDANCE pointers if the repo already does that for packs
> 5. Link to progressive TERMS / shape-qual work where relevant
>
> ## Out of scope
> - Launching live `--call-jev`
> - Changing progressive gate behaviour in hooks
> - Replacing expensive gold seats with Flash alone
>
> ## Done when
> PR open with coherent design + resolved recommendations + measurable next experiments; summary lists PR URL and key recommendations.

## Problem

Maps-length worker transcripts are expensive to read and the cheap instruments we already have do not answer the questions this study needs.

The progressive session-gate pack can replay stored JSONL, build `hybrid_v0` snapshots, and hold a multi-model checkout panel. That panel missed its reliability floor (Krippendorff α = 0.1189, primary gold rule `A0` null on both P0 workers). Checkout gold is therefore not a target this study can score against. The same pack's committed judge packs do carry prefix stats (re-read counts, compaction counts, tool histograms) while the committed redacted JSONL has empty assistant prose and empty re-read paths if replayed directly. Qualitative reading and stats-based foreshadowing are different evidence classes, and nothing in the repo routes them to different models on purpose.

TypeSafe calls are already cheap relative to a Sonnet or Grok seat, but every live call is a hand-run of `classify.py --live`, `assert_phase.py`, or `replay_progressive_gates.py --call-jev`. There is no way for a Flash session or a local llama.cpp server to fan out many framings over many segments, cache the request, and refuse a second POST. The OpenCode plugin that exists (`packages/opencode-workflow-hooks`) buffers `tool.execute.after` and flushes a deterministic gate. It does not register custom tools. The documented extension point for tools is the OpenCode `tool` init hook, unused in that package.

`assert_phase --deterministic` remains the phase kill line, with Jev as an audit log that cannot overturn it. `tools/transcript/classify.py` remains a session-kind chart. Neither is a shape metric. Building another chart and calling it agreement would repeat the classify-as-KPI mistake.

## Solution Shape

After this change the repo holds a signed design for an offline analysis harness and the lab record of that design. The harness is not installed. Live hooks, the progressive replay CLI, the OpenCode signals plugin, and `assert_phase` behave as they do today.

The designed system is five domains. A role registry says which model tier may write which artifact. A segment index cuts stored transcripts into windows using the progressive turn counter, and labels each window `stats_only` or `prose` from the evidence actually present. A trial matrix runs one schema and one framing over those windows on TypeSafe, on a local OpenAI-compatible server, or on answers the caller already computed, and stores one cache row per canonical request. An OpenCode tool surface, specified and not wired, lets a Flash or local session invoke that matrix without a second HTTP client. A steer-draft writer produces counterfactual handoff text at three prefix lengths for a later human score. Product wiring of any of these is a later plan, after Cody accepts a spike.

The lab record that this plan delivers is [`docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/`](../../lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/INDEX.md). Contracts below are what a later brief cites. Schemas, spike order, and the recommendation ledger in full live in that pack's [`DESIGN.md`](../../lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/DESIGN.md) and [`TOOLS.md`](../../lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/TOOLS.md).

### Domain: Role registry

- Owns: which tier may author summaries, volume labels, panel gold, and TypeSafe requests. The registry is the lab design, not a config file in the product.
- Contract:
  - `deepseek/deepseek-flash` via OpenCode may author session summaries, long qualitative arcs, and draft analysis briefs. Each artifact carries `author_tier: flash` and `review_status: unreviewed` until a Sonnet 5.5 pass sets `review_status: sonnet_reviewed`. Phase sign-off stays with Claude Code or Grok, as in [`GUIDANCE-flash-review-gate.md`](../../lab/GUIDANCE-flash-review-gate.md). Flash artifacts are excluded from panel α and from any gold aggregate, matching the progressive gold chain.
  - Local llama.cpp, OpenAI-compatible, base URL `WORKFLOW_LOCAL_LLM_URL` defaulting to `http://127.0.0.1:8080/v1`, may author volume labels on windows whose end is at most `early_window_end`. The model id is recorded per run and is not pinned in this design. This base URL is not written into OpenCode's provider map. Other agents stay on DeepSeek via OpenCode.
  - Panel gold for this study is an expensive-seat label. Seats that count are Claude Sonnet (`signed: true`), Grok, and Composer. Opus is optional and not required. Flash and the local server do not occupy a seat.
  - TypeSafe System One (`https://api.typesafe.ai/v1/systemone`, model pin `jev-1.13.0`) authors structured answers only. A missing `TYPESAFE_API_KEY`, an HTTP error, or invalid JSON yields `decision: missing`. No other model is called in its place. `assert_phase --deterministic` stays the only hard pass/fail, and a Jev score cannot change it.
- Non-goals: choosing OpenCode's global default model; replacing a gold seat with Flash; a new kill line.

### Domain: Segment index

- Owns: windows over a stored transcript, and the evidence class of each window.
- Contract:
  - Turns are progressive `api_turn`. `prefix(c)` is the progressive prefix. `T` is the progressive `T`. This domain does not define a second counter.
  - `early_window_end(T) = min(120, T)`. `early_prefix` is `prefix(early_window_end)`. Turns after 120 are the outcome suffix. The outcome suffix is visible only to a hindsight trajectory label. It is withheld from early-signal judges, from Jev state, and from local volume calls.
  - A segment record names `worker_id`, `window_id`, inclusive `api_turn` start and end, `snapshot_mode`, and `evidence_class`.
  - `evidence_class` is `prose` when the window contains non-empty assistant text. It is `stats_only` when the only usable evidence is aggregate fields (tool histogram, `reread_paths`, `compaction_event_count`) such as a progressive judge pack whose `tail[].excerpt` is empty. It is `absent` when neither prose nor those aggregates are present, which is what a replay of the committed redacted JSONL yields for re-read paths. A qualitative summary requires `prose`. A `stats_only` window may still feed a schema whose questions are answerable from those aggregates. An `absent` window may feed turn-count checks only.
  - Window ids used by the matrix: `early_120` (the single prefix `1..early_window_end`), `grid_15` (progressive label grid `60 + 15k` intersected with the call's allowed range), and an explicit `{start, end}` range. Default `snapshot_mode` for cells that must stay comparable to the progressive harness is `hybrid_v0` with `N = 8` and `excerpt = 400`. State JSON stays under the existing 12_000 character guard.
- Non-goals: editing [`TERMS.md`](../../lab/RESEARCH/2026-10-01-progressive-jev-session-gates/TERMS.md); moving P0 off `(75, 15)`; treating 120 as a checkout checkpoint.

### Domain: Trial matrix

- Owns: the cartesian measurement of cheap answers against a reference, and the cache that makes a repeat free.
- Contract:
  - A cell is `(model_tier, framing_id, segment_id, schema_id)`. `model_tier` is `typesafe` | `local` | `inline`. `inline` stores answers the caller computed (a Flash session, or a human) and performs no outbound call. `typesafe` posts only through `tools/transcript/lib/jev_client.post_systemone` with `model` fixed to `jev-1.13.0`. `local` posts chat completions to `WORKFLOW_LOCAL_LLM_URL`.
  - `schema_id` is one of `session-checkout`, `shape-v0`, `phase-sketch-v0`, `early-signal-v0`, `trajectory-v0`. `session-checkout` uses the existing question sets `Y_full`, `Y_choice_only`, and `Y_legacy` unchanged, including their instruction text. The caller passes a framing slug. The stored `framing_id` is that slug plus the sha256 of the canonical question JSON. An edited instruction is a new slug and is not reported as `Y_full`. Question JSON that is not in the registered framing table for that slug is `decision: missing`, `reason: unregistered_framing`.
  - The cache key is the sha256 of the full outbound body: endpoint, model, questions, state, the instruction string, and any sampling parameters that were sent. A cache hit does not POST. Duplicate cells in one batch collapse before any call. `inline` rows are keyed by framing hash, `segment_id`, and a hash of the answer object. They are not HTTP cache entries. A run that sets `cache: bypass` still dedupes inside the batch and does not read or write the HTTP cache, so a warm-server measurement is not a matrix-cache hit.
  - Default execution is dry-run: emit the request and the cache key, `decision: dry_run`. A live call requires `live: true` and `confirm_live: true`. TypeSafe live also requires `TYPESAFE_API_KEY`. The tool wrapper catches the client's process-exit on a missing key and returns `decision: missing`, `reason: missing_api_key`. It does not change `jev_client.py`. Local live requires the server to answer; a dead server is `missing`, not a TypeSafe retry.
  - Caps apply to cells that would POST. Dry-run cells and cache hits do not count. `max_calls` default 32. A value above 32 without `budget_tokens` is rejected before any POST. A value above 256 is rejected outright. `max_concurrency` default 4, maximum 8. Cells past the cap are `decision: missing`, `reason: cap`. HTTP failures are `missing` and are not retried onto another tier.
  - `hide_outcome_suffix` defaults true. A segment with `end > early_window_end` is then `missing`, `reason: outcome_suffix`, and its state is not truncated and not sent. The flag may be false only for `schema_id` `session-checkout` or `trajectory-v0`. It may not be false for `shape-v0`, `phase-sketch-v0`, or `early-signal-v0`, on any backend, including `inline` and `local`. An `inline` early-signal or steer row carries `max_turn_seen`, and the row is `missing` with `reason: suffix_seen` when that value exceeds the prefix end.
  - A schema that needs prose (`compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `phase_sketch`, `trajectory`) on an `evidence_class` other than `prose` is `missing`, `reason: prose_required`.
  - `reread_cluster` on `stats_only` evidence is the mechanical predicate "some path count ≥ 3". Models are scored against that predicate as `reread_cluster_accuracy`. Seats are not asked to label it. It does not use α and it does not use checkout gold.
  - Panel agreement is per field. Precision and recall for a field are withheld unless that field's gold file exists, the rubric version was registered before any seat ran, `n_workers` with `prose` is at least 3, and Krippendorff α on that field for that rubric version is at least 0.40. Nested prefixes of one worker are not the item count. One attempt per rubric version. A later version does not revive a failed version's precision. Checkout α is not evidence about these fields. Until the gold file exists, agreement is null and `reason: gold_missing`. Below the floor or below `n_workers`, `reason: agreement_withheld`. Cost and throughput are still reported. `session_kind` from `classify.py` is never an agreement target. "Beats the other framing" requires at least two framings on the same segments and is withheld under the same gate.
  - The matrix does not write `gate_exit`, does not change `confidence_min`, and does not invoke `replay_progressive_gates.py --call-jev`.
- Non-goals: a leaderboard of session kinds; tuning H1–H4 of the progressive pack; storing API keys or raw provider payloads that contain them.

### Domain: OpenCode analysis tools

- Owns: the model-invoked surface for the matrix. Specified in the lab pack. Not registered in `opencode.json` and not exported by `@codyhamilton/opencode-workflow-hooks` in this plan.
- Contract:
  - Four tool names: `jev.classify`, `typesafe.classify`, `analysis.load_segment`, `analysis.batch_trial`. The first two are one handler. A batch that names both dedupes by cache key so the alias cannot double-spend.
  - Registration, when a later plan wires it, is a sibling plugin factory that returns a `tool` init hook. It is a separate `plugin` array entry from `WorkflowSignalsPlugin`. It does not subscribe to `tool.execute.after` and it does not call `process_hook_input`.
  - `analysis.load_segment` performs no network I/O. It is the only tool that implements `early_window_end`.
  - `analysis.batch_trial` is the only tool that loops. It enforces the caps in the trial-matrix contract.
  - Tool results omit `TYPESAFE_API_KEY` and do not echo it into the analytics sink. The sink's existing rule (no API key in the POST body) is unchanged.
  - Dry-run is the default on every tool that can POST.
- Non-goals: editing `packages/opencode-workflow-hooks/src/index.ts`; `install.sh` registration; an MCP wrapper around TypeSafe in this plan; blocking the agent loop.

### Domain: Steer drafts

- Owns: counterfactual handoff text at `api_turn` 50, 60, and 75.
- Contract:
  - A draft is one JSON object: `worker_id`, `api_turn` ∈ {50, 60, 75}, `author_tier`, `review_status`, `text` of at most 500 characters, `cited_turns` drawn from `prefix(api_turn)` only, `max_turn_seen` ≤ `api_turn`, `evidence_class`.
  - Author tier for a generated draft is `flash`, and the draft stays `unreviewed` until Sonnet 5.5 reviews it. Usefulness is scored later by a human or by Grok, and only after the prose early-signal field has cleared its α gate: did the draft name a foreshadow the panel marked on `early_prefix`. A failed or missing panel leaves usefulness null. Checkout labels are not the score. The Sonnet-then-sign-off step on these artifacts is a study convention recorded in the Flash guidance. It does not add a phase-close rule.
  - Turn 50 is inside the early window and before the progressive gold grid, which starts at 60. A draft at 50 has no checkout gold. That is expected.
  - The artifact is a JSONL in the lab pack. It is not a Claude hook response and it has no `additionalContext` field.
- Non-goals: installing a hook; parent-UI surfacing; designing the progressive feedback channel that TERMS §3 and §10 leave deferred.

### Domain: Shape gold

- Owns: the reference labels the matrix agrees with. Absent until a spike writes them. The domain's rules are in force before any row exists.
- Contract:
  - Which ids a seat may be asked depends on `evidence_class`, registered before any seat runs. On `stats_only`, the only foreshadow a machine emits is mechanical `reread_cluster` (path count ≥ 3). Seats are not convened for it. `compaction_event_count` is reported beside the row and is not a label. On `prose`, seats may label `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `phase_sketch`, and `trajectory`. `reread_cluster` stays mechanical even when prose is present, so the bundle's path counts are not a second opinion. On `absent`, no foreshadow is labeled. Turn 60 is not in the committed P0 judge packs (those start at 75). A prose label at 60 exists only when raw `prefix(60)` is mounted.
  - Two passes, stored as separate rows, prose only. The early-signal pass sees only `early_prefix` (or a grid prefix at `c ≤ 120`) and records `justifying_turns`, each `≤` the prefix end. The hindsight pass sees the whole file and may set `trajectory`. It is saved after the early-signal pass. When two seats are available, they are different seats. Rubric version `shape-rubric-v0` is the text in the lab design. One labeling attempt per version. A retry is a new version declared before the new seats run. Items for α are workers, at a stated checkpoint, not five nested prefixes of one worker. `n_workers` with prose must be at least 3 or the result is `insufficient_n`.
  - `trajectory` is assigned by first match: `early_thrash` if the early prefix supports rubric `runaway` or `context_thrash`, and either `T ≤ 120` or the outcome suffix supports one of those two; `early_other` if the early prefix supports `scope_drift` or `low_progress` and the row is not `early_thrash`; `late_pivot` if the early prefix supports none of the four rubric patterns and the outcome suffix supports `runaway`, `context_thrash`, or `scope_drift`; `steady` if the early prefix supports none of the four and the row is not `late_pivot`; `unlabeled` if no hindsight seat has answered. `low_progress` in the suffix alone does not make `late_pivot`.
  - An early signal is a foreshadow id with `justifying_turns` all `≤ early_window_end`. Ids: `reread_cluster` (mechanical), `compaction_cycle`, `no_checkable_step`, `anchor_divergence`, `none`. They crosswalk to `runaway`, `context_thrash`, `low_progress`, `scope_drift` for diagnosis. The crosswalk is not the precision denominator. Each of `trajectory`, `phase_sketch`, and the prose foreshadow set has its own α gate.
  - `phase_sketch` is an ordered list from {`orient`, `search`, `edit`, `verify`, `replan`, `stall`}. These tags are not `Workflow-Phase` indexes and not `execute` phases. The segment strip the study asked for is `grid_15`: one segment per checkpoint, not a new counter.
  - Revalidation is per seat, on that seat's own claims, inside the early window, on the progressive 15-turn grid. `confidence_points` starts at 3. A denial by that same seat subtracts 1. A `missing` answer leaves the points unchanged and is counted in a separate `missing` column. Points do not increase. At 0 the signal is `expired` for that seat. A pooled expiry requires every counting seat that claimed the id to have reached 0. Tables are stratified by the checkpoint of the claim. This counter is not `confidence_min` and it does not fire `R(t)`. There is no majority rule and no use of `A_maj` or `A_gc`.
- Non-goals: rewriting `A0`; adopting `A_maj` or `A_gc`; a rising or falling `confidence_min` inside P0.

## Architectural Implications

- [`docs/OVERVIEW.md`](../../OVERVIEW.md) and [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md) stay as they are. This plan adds no skill, no driver provider, and no hook. OpenCode remains skills-plus-an-unwired-signals-plugin in the overview, which is still accurate.
- [`docs/design/conversation-indexer.md`](../../design/conversation-indexer.md) is a design-intent doc for a future index. The segment loader reads fixture JSONL and committed judge packs. It does not wait on that index.
- The progressive pack's TERMS, hypotheses, replay CLI, and gold files are read-only inputs. A one-line sibling link in that pack's `INDEX.md` is the only edit there.
- A later plan that wires the sibling plugin will have to touch the OpenCode package and, at that point, say so in `docs/ARCHITECTURE.md`. This plan does not.
- Stable docs were readable and current enough for this boundary. Nothing in them contradicts the role split. The overview already points operators at the Flash sign-off guidance.

## Decisions

- **Docs only.** The user asked for a research pack and a system design, and forbade live `--call-jev`, hook changes, and replacing gold seats. This plan's only phase is the publication of that record.
- **Sibling study.** Shape, early signals, the 120-turn window, claim-confidence decay, and steer drafts are terms of this study. They cite progressive `api_turn`, `prefix`, `hybrid_v0`, rubric patterns, and the 12_000 character guard. They do not edit them.
- **One phase, refine skipped.** A single worker can carry the phase, and the phase is the pack itself. `refine` is skipped.
- **Tools stay unwired.** The `tool` init hook is the extension point. The signals plugin stays a hooks plugin. The sketch is markdown under the lab pack.
- **Agreement waits for new gold.** Checkout α failed. Scoring shape against `A0` would launder that failure. Cost and throughput do not wait.
- **Stats and prose stay split.** Committed judge packs can support a stats foreshadow. Empty excerpts cannot support a qualitative arc. The loader reports which one it has.
- **Decay is a claim counter.** It is not a new `confidence_min` schedule. P0 stays `t = 3`, fixed, fail-open.
- **Headless.** This session is a cloud agent. Scope questions are ledgered below. The checkpoint is waved through.

## Assumption Ledger

### Assumption 1

- Question: Should the system design live only in `docs/plans/`, or also as a lab research pack?
- Answer chosen: Both. This file is the bounding design. The pack under `docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/` holds the inventory, the full recommendation text, the spike order, and the tool sketch.
- Rationale: The design skill keeps a plan at contract altitude and requires the `Workflow-Plan:` marker. The user named the lab path and the lab index already catalogs packs there.
- If wrong: A later close-out can point the plan record at the pack and drop the duplicate narration. The contracts stay in whichever file Cody treats as the citation source.

### Assumption 2

- Question: Should the new vocabulary be written into progressive `TERMS.md`?
- Answer chosen: No. Different meanings are a different study, which is that file's own rule.
- Rationale: P0 is `first_at = 75`, interval 15, fixed `confidence_min`, and `A0`. H5 failed. Folding 120, decay, and steer drafts into that file would retune a study this plan is forbidden to retune.
- If wrong: Cody can ask for a TERMS amendment as its own change. The crosswalk in the lab design is the migration note.

### Assumption 3

- Question: Where do custom tools plug in?
- Answer chosen: A sibling plugin that uses the documented `tool` init hook, left unwired here. Not a new branch inside `WorkflowSignalsPlugin`.
- Rationale: The signals plugin is advisory and runs on every tool result. A TypeSafe fan-out on that hook would spend money on the agent loop. The user forbade live hook changes.
- If wrong: The tool names and the dry-run contract can move onto the existing factory later. Callers do not change.

### Assumption 4

- Question: Two tools, `typesafe.classify` and `jev.classify`, or one?
- Answer chosen: One handler, two names, deduped by cache key. One endpoint, pin `jev-1.13.0`.
- Rationale: The user named both. The repo has one System One client.
- If wrong: Dropping the alias is a docs edit. The batch runner's cache key does not include the tool name.

### Assumption 5

- Question: What is the decaying confidence bar?
- Answer chosen: per-seat `confidence_points` on an early-signal claim, start 3, minus 1 on a denial by that seat, unchanged on `missing`, expired at 0, stratified by claim checkpoint. Not a change to `confidence_min` or `R(t)`.
- Rationale: The standing note asks for 15-turn revalidation and a decaying bar, and for early signals to live in the first ~120 turns. TERMS already says a moving `confidence_min` is an open axis outside the P0 grid. Reusing that knob would collide with the frozen checkout study.
- If wrong: A cell that moves `confidence_min` with checkpoint index can be added beside this one. P0 stays fixed either way.

### Assumption 6

- Question: How is a steer at turns 50, 60, and 75 scored without a live Claude hook?
- Answer chosen: Offline drafts from `prefix(c)` only. The score, once early-signal gold exists, is whether the draft names a panel foreshadow on `early_prefix`. No `additionalContext` bytes.
- Rationale: Progressive TERMS leaves the hook channel out of scope. Turn 50 has no checkout label. The user asked for the experiment design without live Claude.
- If wrong: A product plan can reuse the draft text as the body of whatever channel Cody picks. The score definition would need to be re-registered if the target becomes checkout instead of foreshadow.

### Assumption 7

- Question: Should this plan include a `PROPOSALS/` white paper that accepts the recommendations?
- Answer chosen: No. Recommendations are resolved inside the lab design for the harness shape. The backlog row stays researching. Behaviour waits on Cody.
- Rationale: The user asked for resolved recommendations in the pack, and also for soft-until-Cody. A proposal marked accepted would overclaim a behaviour change.
- If wrong: A later pass can lift the recommendation section into `docs/lab/PROPOSALS/` without moving the contracts.

### Assumption 8

- Question: Should path-count ≥ 3 be a panel label, given the checkout panel already failed?
- Answer chosen: No. On `stats_only` packs it is a mechanical predicate. Seats are reserved for prose judgments. Panel α is per field, needs at least three workers with prose, and one attempt per rubric version.
- Rationale: The committed packs show the count and hide the prose. Asking Sonnet whether a printed 10 is "at least three" spends a gold seat on arithmetic and would launder a pass on nested prefixes of one worker.
- If wrong: If Cody wants a panel on `reread_cluster` anyway, it is a new rubric version and still cannot be scored from empty excerpts.

### Assumption 9

- Question: Which corpus rows enter the first spikes?
- Answer chosen: The four committed `T ≥ 75` fixtures. `0853bc21d3aa` stays out until its JSONL is in the manifest. `6c87c96bd9bb` is a windowing control only. Opus is not a required seat. Prose work refuses without a raw mount.
- Rationale: The manifest's `n_workers_ge_75` is 4. P0 judge packs start at turn 75, so turn 60 is not a stats row. TERMS lists Opus; P0 did not use it, and requiring it would block the prose spike on a seat this repo has not been collecting.
- If wrong: Adding the fifth worker is a manifest change in the progressive pack, not a silent expansion here.

### Assumption 10

- Question: Do dry-runs and cache hits consume `max_calls`?
- Answer chosen: No. The cap counts cells that would POST. Above 256 is rejected. Above 32 requires `budget_tokens`.
- Rationale: A dry-run matrix is the cheap experiment. Counting it against the live cap would make the dry-run unable to enumerate the grid it exists to check.
- If wrong: A stricter cap that counts dry-run rows is a one-line change to the batch contract. The rejection above 256 can stay.

### Assumption 11

- Question: May a live call see turns after 120?
- Answer chosen: Only `session-checkout` and `trajectory-v0`, and only when `hide_outcome_suffix` is explicitly false. Shape, phase, and early-signal schemas cannot disable the hide, on any backend.
- Rationale: The standing note says later turns are outcome. A boolean that any schema can flip would put the suffix into the early-signal state.
- If wrong: A hindsight schema can be added. The three early schemas stay prefix-bounded.

## Open Questions

None that block publication of the record. The Qwen GGUF id on `:8080` is deliberately unpinned until a spike records the id the server returns. Shape-gold logistics (which day, which checkout of the packs) are spike work in [`NEXT-EXPERIMENTS.md`](../../lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/NEXT-EXPERIMENTS.md), and the matrix contract already says what to emit when the gold file is absent.

## Phases

This design has one phase. One worker can carry it. `refine` is skipped.

### Phase 1 — The harness design is a lab record

- Outcome: A checkout of this branch contains `docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/` with `INDEX.md`, `RESEARCH.md`, `DESIGN.md`, `NEXT-EXPERIMENTS.md`, and `TOOLS.md`; `docs/lab/RESEARCH/INDEX.md` lists the pack; `docs/lab/BACKLOG.md` points at it; `docs/lab/GUIDANCE-flash-review-gate.md` points at it; and the diff does not modify `packages/`, `tools/`, `skills/`, `plugins/`, `install.sh`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/lab/PROPOSALS/`, `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/TERMS.md`, or that pack's `proofs/`.
- Surfaces: `docs/plans/07-cheap-analysis-harness/DESIGN.md`, `docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/*`, `docs/lab/RESEARCH/INDEX.md`, `docs/lab/BACKLOG.md`, `docs/lab/GUIDANCE-flash-review-gate.md`, `docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/INDEX.md` (sibling link only).
- Approach: known
- Depends on: nothing

## Provenance Notes

Ground was three recon passes: the OpenCode package and its API note, the Jev client and both replay harnesses, and the progressive gold pack. The facts that moved the shape are these.

The OpenCode package returns `tool.execute.after` and `event` only. Custom tools are a documented init hook, not an implemented one. Putting fan-out there, inside the flush path, would bill TypeSafe on the agent loop. A sibling plugin keeps the advisory gate boring.

`jev_client.py` exits when the key is missing and pins `jev-1.13.0`. `assert_phase` dry-runs the request when the key is absent and, when Jev does run, keeps `decision_source` on the deterministic checks. `replay_progressive_gates.py` duplicates the POST and refuses `--call-jev` without a key. The matrix contract picks the shared client for a later spike so a third copy does not appear, and it does not add that flag to the progressive CLI now.

Progressive gold is checkout-shaped: `not_yet` | `checkout`, patterns `runaway` | `low_progress` | `context_thrash` | `scope_drift`, seats Sonnet (signed), Grok, Composer, Flash as an unsigned draft excluded from α. There is no `shape` or `early_signals` field. `A0` is null and α is 0.1189. The committed judge pack for `92a48e004519` at turn 75 already shows a path read 10 times and `compaction_event_count` 12, with empty tail excerpts. So a stats foreshadow is in-repo inside the early window, and a prose summary is not, until raw JSONL is mounted.

Rejected: scoring the new matrix against `A0`; lowering `confidence_min` over checkpoint index as the meaning of "decaying bar"; registering tools on the signals plugin; pinning a GGUF this repo has never recorded; writing a proposal that marks the recommendations accepted; convening gold seats to label a path count that is already in the judge pack.

An adversarial pass on the first draft blocked two things: seating a panel on empty excerpts and on a turn-60 pack row that does not exist, and allowing a failed α to be re-collected until it passed. Both are now in the shape-gold contract (mechanical `reread_cluster`, prose-only panel, one attempt per rubric version, `n_workers` ≥ 3, per-field α). The same pass moved the outcome-suffix flag, the cache key, the cap counter, and the decay miss-rule into the contracts above.
