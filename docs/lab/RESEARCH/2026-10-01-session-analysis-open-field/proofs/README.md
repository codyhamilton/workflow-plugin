# Session-analysis open field — proofs

Offline tooling for [`TOOLING-MVP.md`](../TOOLING-MVP.md) items 3–4. **0 live TypeSafe POSTs** in the committed slice.

| Script | Phase | Output |
|--------|-------|--------|
| `run_framing_dry_run.py` | 1b | `validated/phase-1b-1c/dry_run_batch_log.json`, `framing/registry.json` |
| `run_card_hash_manifest.py` | 1b | `manifests/card_hash_manifest.json` |
| `probe_progressive_corpus_mount.py` | 1c | `validated/phase-1b-1c/mount_probe_results.json` |

Reuses [`cheap-analysis` spike lib](../../2026-10-01-cheap-analysis-typesafe-opencode/proofs/lib/) (`batch_trial`, `classify`, cap/dedupe). No OpenCode registration. No `replay_progressive_gates.py --call-jev`.

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
python3 run_card_hash_manifest.py
python3 run_framing_dry_run.py
python3 probe_progressive_corpus_mount.py
```

Raw Ubuntu JSONL: set `WORKFLOW_PROGRESSIVE_CORPUS` to a directory of `{worker_id}.jsonl` files. The repo does not vendor them.
