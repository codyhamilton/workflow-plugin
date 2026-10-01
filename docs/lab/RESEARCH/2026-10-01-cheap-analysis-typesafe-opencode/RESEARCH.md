# Inventory — what already exists

**Status:** source note for the harness design. Numbers below are from the tree this pack was written against. Confidence in the *mapping* is high where a file is cited. Confidence that a cheap model will match a future shape gold is not high, because that gold does not exist.

## OpenCode plugin

The product package is `packages/opencode-workflow-hooks` (`@codyhamilton/opencode-workflow-hooks`). `WorkflowSignalsPlugin` returns two hooks: `tool.execute.after` (buffer a call) and `event` (flush on `message.updated` or `session.idle`). The flush spawns `python/batch_flush_cli.py`, which calls `process_hook_input` from the cheap-Jev proofs. That helper logs a deterministic gate and does not POST to TypeSafe. Failures in the TypeScript side are swallowed. The plugin does not block the agent and does not call `assert_phase`.

The research note [`OPENCODE-PLUGIN-API.md`](../2026-09-30-opencode-hooks-plugin/OPENCODE-PLUGIN-API.md) lists a `tool` hook at plugin init whose job is to register custom tools. Nothing in `src/index.ts` implements it. `config` can also mutate an `mcp` entry; the package does not. Skills install (`install.sh --opencode-skills`) is a separate path and does not write `opencode.json`.

Registration today is manual, via the example `plugin` array. The proposal [`2026-09-30-opencode-hooks-plugin.md`](../../PROPOSALS/2026-09-30-opencode-hooks-plugin.md) is `status: resolved` with disposition "recommendations accepted pending product wiring." The in-tree package name (`opencode-workflow-hooks`) and the proposal's working name (`opencode-workflow-signals`) differ. This pack does not resolve that naming.

DeepSeek is not configured in any committed `opencode.json`. Host notes in [`FINDINGS.md`](../../FINDINGS.md) record OpenCode with `deepseek/deepseek-flash` on `codyh-ubuntu`. [`GUIDANCE-flash-review-gate.md`](../../GUIDANCE-flash-review-gate.md) encourages Flash for briefs and units, requires a Sonnet 5.5 review of that work, and reserves phase sign-off for Claude Code or Grok. The guidance does not set a model.

No lab doc pins llama.cpp, Qwen, or port 8080. The progressive P0 summary mentions a local llama.cpp provider on the OpenCode box as a reason cloud seats were skipped at first; those seats were later labeled from judge packs. Qwen appears only as a citation in the progressive literature note.

## TypeSafe / Jev client

`tools/transcript/lib/jev_client.py` posts to `https://api.typesafe.ai/v1/systemone` with bearer `TYPESAFE_API_KEY` and `model` `jev-1.13.0`. `require_api_key` exits if the variable is empty. There is no fallback model.

| Caller | Live POST | Missing key |
|--------|-----------|-------------|
| `tools/transcript/classify.py` | Only with `--live` | Prints the request. Session-kind chart, not a KPI |
| `tools/driver/assert_phase.py` | `--live`, or implicit when the key is set and `--deterministic` / `--dry-run` were not passed | Prints the request, exit 0, no pass/fail |
| `assert_phase.py --deterministic` | Never | Deterministic outcome evidence, exit 0 or 2. Jev cannot flip it |
| `replay_progressive_gates.py` | `--call-jev` only, and it refuses without the key | Default dry-run, `decision: missing`, `reason: dry_run` |

`assert_phase` reuses `post_systemone`. The progressive replay script has its own POST helper and the same model pin. Question sets for checkout live in `session_checkout.py`: `Y_full` (`runaway_pattern`, `progress_since_prior`, `scope_drift`, `checkout_now`, `checkout_confidence`), `Y_choice_only`, and `Y_legacy` (the resolved `session-progress` pair). State over 12_000 characters is rejected before a request exists.

The four cheap-judgement schemas in `jev_signal_schemas.py` (`session-progress`, `refine-brief-complexity`, `unit-needs-review`, `phase-alignment-sanity`) are proofs. The PostToolBatch probe does not call them. Use cases are locked in [`use-cases-cody-locked.md`](../2026-09-30-jev-cheap-judgement-signals/use-cases-cody-locked.md): signals steer, the deterministic assert is the kill line, classify is not on the path.

There is no function named `call_jev`. The live flag on the progressive CLI is `--call-jev`. This pack does not add a caller.

## Offline replay and fixtures

Default corpus, commit-safe, from [`corpus_manifest.json`](../2026-10-01-progressive-jev-session-gates/proofs/validated/corpus_manifest.json):

| worker_id | `T` | Role |
|-----------|----:|------|
| `92a48e004519` | 296 | P0 smoking gun |
| `bb6165018de0` | 154 | P0 smoking gun |
| `0aab88c525de` | 192 | Expansion fixture |
| `036ff3ed4a89` | 161 | Expansion fixture |
| `6c87c96bd9bb` | 70 | Negative control, outside `T ≥ 75` |

`n_workers_ge_75` is 4. `0853bc21d3aa` has expansion judge packs and is not in this manifest. Redaction keeps `message.id`, usage, and tool names, and strips prose, `Read` paths, and compaction subtypes. A dry-run on the redacted JSONL reports empty `reread_paths` and `compaction_event_count` ([corpus manifest](../2026-10-01-progressive-jev-session-gates/proofs/corpus/MANIFEST.md)). Raw Ubuntu JSONL is not in git.

Committed judge packs are a second evidence class. The pack row for `92a48e004519` at checkpoint 75 (`hybrid_v0`, `N=8`, excerpt 400) includes `reread_paths` with a count of 10 on one path, `compaction_event_count` 12, a Bash/Read histogram, and **empty** `tail[].excerpt`. Those stats were computed from raw bundles before redaction. The excerpts were not kept. A stats-only foreshadow is in the repo. A prose summary of that prefix is not.

P0 schedule on a `T=296` file is checkpoints 75, 90, …, 285. The label grid is 60, 75, 90, …. Turn 120 is one of those checkpoints. It is not, in TERMS, an "early window."

## Gold seats today

Protocol: [`GOLD-LABEL-RUBRIC.md`](../2026-10-01-progressive-jev-session-gates/GOLD-LABEL-RUBRIC.md) and [`TUNING-PLAN.md`](../2026-10-01-progressive-jev-session-gates/TUNING-PLAN.md).

| Seat | Model | Counts toward α |
|------|--------|-----------------|
| Draft | `deepseek/deepseek-flash` via OpenCode | No |
| Signed final | Claude Sonnet | Yes, `signed: true` |
| Cloud | Grok 4.7, Composer 2.5 | Yes |
| Optional | Claude Opus | Required by the TERMS panel table; P0 ran three seats |

The judge answers `not_yet` or `checkout` and zero or more of `runaway`, `low_progress`, `context_thrash`, `scope_drift`. There is no field named `shape`, `early_signals`, `trajectory`, or `phase`.

P0 result ([`PANEL-FINDINGS-20261001.md`](../2026-10-01-progressive-jev-session-gates/proofs/validated/gold/PANEL-FINDINGS-20261001.md)): α = 0.1189 on 3×21 binary checkout labels. H5 floor is 0.40. H5 failed. `A0` (unanimous earliest checkout) is null on both workers. `A_maj` and `A_gc` are 180 on `92a48e004519` and null on `bb6165018de0`, and are not the fit target. H1–H4 and H6–H7 were not run. Experiment (b), a parent-pull re-label, failed and was discarded. Experiment (c) is corpus expansion on the original rubric.

Jev checkout cache and the parameter sweep are still absent. `run_proofs.sh` is dry-run only.

## What the standing notes are not

Searched the lab tree while writing this pack. These phrases are not defined in progressive TERMS:

- an early window of about 120 turns
- `late_pivot` and `early_thrash` as label values
- early foreshadowing as a gold field
- a decaying confidence bar (TERMS §2: the v0 bar does not rise with `k`; a rising `confidence_min` is an open axis outside the default grid)
- a validation handoff via hook `additionalContext` at turns 50, 60, or 75 (TERMS §3 and §10 put that channel out of scope)

The in-house 50–75 turn band is a cost-crossover note, not a gate. `first_at = 75` was carried forward from it and is unvalidated. Turn 50 is inside a 120-turn prefix and before the gold grid.

## Analytics and classify

The durable-sink proposal is resolved and unwired by default. Envelopes must not contain `TYPESAFE_API_KEY`. Classify logs to `tools/transcript/.classify-log.jsonl` with `human_label: null`. Eval scenario `trailer-completeness` expects classify unused. [`GOALS.md`](../../GOALS.md) lists per-turn Jev inside worker loops as a non-goal.

## Implication for the harness

Any matrix that wants prose has to mount raw JSONL or accept that it is not looking at prose. Any matrix that wants re-read and compaction counts can start from the committed judge packs and must not recompute those counts from the redacted fixtures. Any agreement number that uses checkout gold will inherit a failed reliability floor and the wrong question. The design in [`DESIGN.md`](DESIGN.md) is built on those three constraints.
