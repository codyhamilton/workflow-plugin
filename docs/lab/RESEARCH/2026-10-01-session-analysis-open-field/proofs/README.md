# Open-field proofs

Lab scripts for the session-analysis open field. **No live TypeSafe POSTs** in the committed phase-1b/1c slice; phase 1a is **0 network** as well.

## Phase 1a — marker screen

```bash
pip install -r requirements-lab.txt  # once per environment
python3 docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs/run_phase_1a.py
```

Outputs under [`phase-1a/`](phase-1a/): `marker_features.jsonl`, `marker_analysis.json`, `cox_sketch.json`, `SPIKE-RESULT.md`, `CYCLEResult.md`.

Cox sketch: [`run_cox_sketch.py`](run_cox_sketch.py) (also invoked by the phase runner). Future gate from [`ALTERNATES.md`](../2026-10-01-session-analysis-alternate-angles/ALTERNATES.md): concordance ≤ **0.70** on a proper gold → kill Alternate E.

## Phase 1b + 1c — framing dry-run and mount probe

[`TOOLING-MVP.md`](../TOOLING-MVP.md) items 3–4. Reuses [`cheap-analysis` spike lib](../../2026-10-01-cheap-analysis-typesafe-opencode/proofs/lib/) (`batch_trial`, `classify`). No OpenCode registration. No `replay_progressive_gates.py --call-jev`.

| Script | Phase | Output |
|--------|-------|--------|
| `run_framing_dry_run.py` | 1b | `validated/phase-1b-1c/dry_run_batch_log.json`, `framing/registry.json` |
| `run_card_hash_manifest.py` | 1b | `manifests/card_hash_manifest.json` |
| `probe_progressive_corpus_mount.py` | 1c | `validated/phase-1b-1c/mount_probe_results.json` |

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
python3 run_card_hash_manifest.py
python3 run_framing_dry_run.py
python3 probe_progressive_corpus_mount.py
```

Raw Ubuntu JSONL: set `WORKFLOW_PROGRESSIVE_CORPUS` to a directory of `{worker_id}.jsonl` files. The repo does not vendor them.

## Pilot field-proof (registration + dry-twin)

[`cycles/REGISTRATION-pilot-field-proof.md`](../cycles/REGISTRATION-pilot-field-proof.md). Capture layout: [`capture/README.md`](capture/README.md).

| Script | Output |
|--------|--------|
| `run_pilot_dry_twin.py` | `capture/pilot-field-proof/jev/dry-twin/`, `validated/pilot-field-proof/dry_twin_batch_log.json` |
| `run_local_swarm_pilot.py` | `capture/pilot-field-proof/local-swarm/` (add `--live-local` on Ubuntu) |

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
python3 run_pilot_dry_twin.py
python3 run_local_swarm_pilot.py
```

Local swarm runbook: [`pilot/RUNBOOK-local-swarm.md`](pilot/RUNBOOK-local-swarm.md).
