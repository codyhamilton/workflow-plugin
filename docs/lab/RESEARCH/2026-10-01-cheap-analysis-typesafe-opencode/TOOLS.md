# Tool surfaces (unwired)

**Status:** sketch. These definitions are the contract in [`DESIGN.md`](DESIGN.md) R7 and R8, written so a later plugin can implement them. Nothing here is registered with OpenCode. The signals plugin does not gain a `tool` hook in this pack.

A later wiring plan adds a **sibling** plugin factory. OpenCode calls its `tool` init hook ([API note](../2026-09-30-opencode-hooks-plugin/OPENCODE-PLUGIN-API.md)). Suggested package name, not created: `@codyhamilton/opencode-analysis-tools`. It does not import `process_hook_input` and it does not buffer `tool.execute.after`.

Auth and guards common to every POST-capable tool:

| Rule | Behaviour |
|------|-----------|
| Default | `live` false → `decision: dry_run`, no socket |
| TypeSafe live | `live` and `confirm_live` both true, and `TYPESAFE_API_KEY` non-empty |
| Missing key | `decision: missing`, `reason: missing_api_key`. No other backend |
| Model pin | `jev-1.13.0` only. Any other `model` in a built request is a bug |
| HTTP | `tools/transcript/lib/jev_client.post_systemone`. The wrapper catches that client's process-exit on a missing key and returns `missing`. It does not change the client |
| Local live | POST `{WORKFLOW_LOCAL_LLM_URL}/chat/completions`. Default base `http://127.0.0.1:8080/v1`. Connection failure is `missing`, not a TypeSafe call |
| Cache | sha256 of the full outbound body: endpoint, model, questions, state, instruction string, sampling parameters. Hit does not POST. Tool name is not part of the key. `inline` keys are framing hash + `segment_id` + answer hash, and are not HTTP entries. `cache: bypass` skips the HTTP cache in both directions |
| Secrets | Results and logs omit the API key. Analytics envelopes follow the sink rule and also omit it |
| Caps | Enforced only inside `analysis.batch_trial`. The count is cells that would POST. Dry-run rows and cache hits do not count. `max_calls` above 256 is rejected before any send. Above 32 requires `budget_tokens`. `max_concurrency` maximum 8 |

`jev.classify` and `typesafe.classify` share one handler. Calling both on the same payload in one batch yields one POST.

## `analysis.load_segment`

No network. Implements `early_window_end`.

```yaml
name: analysis.load_segment
input:
  type: object
  required: [source]
  properties:
    source:
      type: object
      description: Exactly one of fixture, worker_id, pack_path.
      properties:
        fixture: {type: string, description: Repo-relative JSONL}
        worker_id: {type: string, description: Short id resolved via the progressive corpus manifest}
        pack_path: {type: string, description: Judge-pack JSONL row source}
    window_id:
      type: string
      enum: [early_120, grid_15, range]
      default: early_120
    range:
      type: object
      properties:
        start: {type: integer, minimum: 1}
        end: {type: integer, minimum: 1}
    snapshot_mode:
      type: string
      enum: [hybrid_v0]
      default: hybrid_v0
      description: Snapshot mode only. stats_only is an evidence_class, not a mode.
    grid:
      type: string
      enum: [label_60, p0_75]
      default: label_60
      description: >
        label_60 is the progressive gold grid (60+15k). p0_75 is checkpoints(75, 15, T).
        Ignored unless window_id is grid_15.
output:
  type: object
  required: [segments]
  properties:
    segments:
      type: array
      items:
        type: object
        required: [segment_id, worker_id, T, start, end, evidence_class, state]
        properties:
          segment_id: {type: string}
          worker_id: {type: string}
          T: {type: integer}
          early_window_end: {type: integer}
          start: {type: integer}
          end: {type: integer}
          evidence_class:
            type: string
            enum: [prose, stats_only, absent]
          excerpt_nonempty: {type: boolean}
          reread_present: {type: boolean}
          snapshot_mode: {type: string}
          state: {type: object, description: Jev state object, or null when absent}
          state_chars: {type: integer}
```

`early_120` sets `end = min(120, T)` and `start = 1`. `grid_15` emits one segment per grid point `≤ end`, and for schemas that are not `session-checkout` the caller asks the batch runner to drop points `> early_window_end`. The loader itself does not hide the outcome suffix; the batch runner does, so a hindsight job can still request it on purpose by passing `range`.

`evidence_class: absent` means the redacted JSONL has no prose and the caller did not supply a judge pack. `state` is still returned for turn counts and tool-name histograms, with `reread_present: false`.

## `jev.classify`

```yaml
name: jev.classify
input:
  type: object
  required: [schema_id, framing_id]
  properties:
    schema_id:
      type: string
      enum: [session-checkout, shape-v0, phase-sketch-v0, early-signal-v0, trajectory-v0]
    framing_id:
      type: string
      description: >
        Caller passes a slug. The stored id is slug plus the sha256 of the
        canonical question JSON. The slug must name a row in the registered
        framing table. Unregistered question JSON is missing / unregistered_framing.
    question_set:
      type: string
      enum: [Y_full, Y_choice_only, Y_legacy]
      description: Legal only when schema_id is session-checkout. Default Y_full.
    segment_id: {type: string}
    state:
      type: object
      description: Inline state. Ignored when segment_id is set; the loader's state wins.
    live: {type: boolean, default: false}
    confirm_live: {type: boolean, default: false}
output:
  type: object
  required: [decision, cache_key, schema_id, framing_id]
  properties:
    decision:
      type: string
      enum: [dry_run, ok, missing]
    reason: {type: string}
    cache: {type: string, enum: [hit, miss, skipped]}
    request: {type: object}
    answers: {type: object}
    usage: {type: object}
    model: {type: string, const: jev-1.13.0}
```

`typesafe.classify` has the same input and output schema. Implementations compare handlers by identity.

`session-checkout` questions are the objects in `session_checkout.session_checkout_questions`. A framing that is not those objects is rejected when `question_set` is set. Other schemas take their question JSON from the registered framing table keyed by the caller's slug. Unregistered question JSON is `decision: missing`, `reason: unregistered_framing`. That keeps a typo from becoming a silent new instrument. The stored `framing_id` is the slug plus the question-JSON hash. Callers do not pass the hash.

State over 12_000 characters is `missing`, `reason: state_guard`, and is not POSTed.

## `analysis.batch_trial`

The only looping tool.

```yaml
name: analysis.batch_trial
input:
  type: object
  required: [schema_id, framing_ids, backend]
  properties:
    schema_id:
      type: string
      enum: [session-checkout, shape-v0, phase-sketch-v0, early-signal-v0, trajectory-v0]
    framing_ids:
      type: array
      items: {type: string}
      minItems: 1
    backend:
      type: string
      enum: [typesafe, local, inline]
    segments:
      type: array
      description: Segment records from analysis.load_segment, or ids resolved the same way.
      items: {type: object}
    hide_outcome_suffix:
      type: boolean
      default: true
      description: >
        When true, any segment with end greater than early_window_end is
        decision missing, reason outcome_suffix, and is not sent. The handler
        does not silently truncate state. False is legal only for
        session-checkout and trajectory-v0. shape-v0, phase-sketch-v0, and
        early-signal-v0 reject false with reason suffix_forbidden.
    cache:
      type: string
      enum: [read, bypass]
      default: read
    live: {type: boolean, default: false}
    confirm_live: {type: boolean, default: false}
    max_calls: {type: integer, minimum: 1, maximum: 256, default: 32}
    budget_tokens: {type: integer, minimum: 1}
    max_concurrency: {type: integer, minimum: 1, maximum: 8, default: 4}
    inline_answers:
      type: array
      description: Required when backend is inline. One object per cell, with segment_id, framing_id, answers.
output:
  type: object
  required: [cells, duplicate_post_rate, posts]
  properties:
    posts: {type: integer}
    duplicate_post_rate: {type: number}
    capped: {type: integer, description: Cells not sent because of max_calls}
    cells:
      type: array
      items:
        type: object
        required: [model_tier, framing_id, segment_id, schema_id, decision, cache_key]
        properties:
          model_tier: {type: string, enum: [typesafe, local, inline]}
          framing_id: {type: string}
          segment_id: {type: string}
          schema_id: {type: string}
          decision: {type: string, enum: [dry_run, ok, missing]}
          reason: {type: string}
          cache: {type: string, enum: [hit, miss, skipped]}
          answers: {type: object}
          usage: {type: object}
          seconds: {type: number}
          agreement: {type: [number, "null"]}
          agreement_reason: {type: string}
```

Rules the handler enforces:

- `max_calls` above 32 without `budget_tokens` is rejected before any call (`reason: budget_required` on the whole invocation, zero posts).
- Cells past the cap are `decision: missing`, `reason: cap`, and are not POSTed.
- `backend: inline` never opens a socket. Missing `inline_answers` for a cell is `missing`, not a model call.
- `backend: local` never calls TypeSafe, including when the local response is not valid JSON (`reason: parse`).
- `hide_outcome_suffix: false` is legal only for `session-checkout` and `trajectory-v0`. The other schemas return `reason: suffix_forbidden` if the caller sets it false, on every backend including `inline` and `local`.
- A prose-field schema on `evidence_class` other than `prose` returns `reason: prose_required` and does not POST.
- An `inline` early-signal or steer answer without `max_turn_seen` ≤ the prefix end is `reason: suffix_seen`.
- `max_calls` counts would-POST cells only. Dry-run and cache hits do not count. Above 256 rejects the invocation with zero posts. Capped cells are `decision: missing`, `reason: cap`.
- Agreement is filled only from `shape_gold.jsonl` by the rules in DESIGN R4. Otherwise `agreement` is null and `agreement_reason` is `gold_missing` or `agreement_withheld`.

## Local request shape

`backend: local` sends one chat completion whose user message contains the same question JSON and state JSON the TypeSafe request would carry, plus an instruction to return a JSON object of answers and nothing else. That instruction is part of the cache key. The recorded `model` is the server's id, not a pin from this repo. Temperature is left at the server default; if the server echoes a sampling parameter, that value is stored on the row and included in the cache key of any later call that sends it. This pack does not set a sampling parameter of its own.

## What Flash calls, and what it does not

A Flash session in OpenCode is the caller. It uses `analysis.load_segment`, writes prose itself when `evidence_class` is `prose`, and uses `analysis.batch_trial` with `backend: typesafe` or `backend: local` to fan out. Its own written arc is stored with `analysis.batch_trial` `backend: inline` only when the arc has been reduced to schema answers. The long-form text is an artifact beside the matrix, not a TypeSafe question.

The local server is reached by the batch tool, not by changing OpenCode's default provider. A Qwen process on `:8080` can also be the OpenCode model for a dedicated volume session; that session still must not be the global default, and its labels stay `seat_class: volume`.
