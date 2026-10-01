# Corpus manifest — progressive Jev session gates

**Status:** paths and expected turn counts. This file is not a measurement.

The harness does not vendor raw Ubuntu JSONLs. Redacted copies that preserve `message.id`, usage, and tool names are the default corpus when they are on the checkout.

## Default corpus (in repo)

`docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/`

See that directory's [`MANIFEST.md`](../../../2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/MANIFEST.md) and `manifest.json` for sha256-ready counts. Turn definition there matches this harness: unique `message.id` on `type=assistant`. Those files are subagent transcripts, so every assistant row is `isSidechain: true` and still counts.

| short_id | role | expected `T` | fixture |
|----------|------|-------------:|---------|
| `92a48e004519` | smoking gun | 296 | `92a48e004519.jsonl` |
| `bb6165018de0` | smoking gun | 154 | `bb6165018de0.jsonl` |
| `6c87c96bd9bb` | negative control (not in the `T >= 75` corpus) | 70 | `6c87c96bd9bb.jsonl` |
| `0aab88c525de` | additional `T >= 75` | 192 | `0aab88c525de.jsonl` |
| `036ff3ed4a89` | additional `T >= 75` | 161 | `036ff3ed4a89.jsonl` |
| `3ff8479be14a` | in-band, below `first_at` 75 | 68 | `3ff8479be14a.jsonl` |
| `6135cffdf32a` | in-band, below `first_at` 75 | 68 | `6135cffdf32a.jsonl` |

`run_proofs.sh` dry-replays the two smoking guns and the control when this directory exists, and writes `validated/corpus_manifest.json`.

Redaction keeps `message.id`, usage, and tool names. It replaces prose, `Read` paths, and compaction subtypes, so a dry-run on these fixtures reports turn counts and tool histograms, and reports empty `reread_paths` and `compaction_event_count`. Mount a raw JSONL before treating snapshot prose as evidence.

## Override

`WORKFLOW_PROGRESSIVE_CORPUS` replaces the default directory. Point it at a folder of Claude JSONLs (redacted fixtures or a mounted Ubuntu tree). The harness does not fetch `/home/codyh`.

```bash
export WORKFLOW_PROGRESSIVE_CORPUS=/path/to/jsonls
python3 replay_progressive_gates.py --schedule 75:15 --dry-run \
  --workers 92a48e004519,bb6165018de0,6c87c96bd9bb
```

## Ubuntu sources (not in git)

Root: `/home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/`

| short_id | path |
|----------|------|
| `92a48e004519` | `d006f5a0-267f-402e-bed7-b13d1a65a961/subagents/agent-a23c692a48e004519.jsonl` |
| `bb6165018de0` | `bd4f6c0d-5061-4e77-9a4c-2e083814b952/subagents/agent-ad325bb6165018de0.jsonl` |
| `6c87c96bd9bb` | `af9b5cb1-edc5-4155-b521-a56bad1c7f13/subagents/agent-a95386c87c96bd9bb.jsonl` |

Dry-replay one smoking gun once that tree is mounted:

```bash
python3 docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/replay_progressive_gates.py \
  --transcript /home/codyh/.claude/projects/-home-codyh-workspace-open-pajero-maps/d006f5a0-267f-402e-bed7-b13d1a65a961/subagents/agent-a23c692a48e004519.jsonl \
  --schedule 75:15 \
  --dry-run
```

The same command against the redacted fixture (no Ubuntu mount):

```bash
python3 docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/replay_progressive_gates.py \
  --transcript docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers/92a48e004519.jsonl \
  --schedule 75:15 \
  --dry-run
```

## Synthetic fixture

`fixtures/synthetic_worker_90.jsonl` has 90 assistant turns (one duplicate `message.id` that must not increase `T`). Schedule `75:15` yields checkpoints 75 and 90. `run_proofs.sh` uses it even when the maps directory is absent. It is not a maps worker and is not in the metric corpus.
