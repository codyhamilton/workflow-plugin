# Session-analysis open field — cycle log

| cycle_id | approach | status | api_calls | kill | artifacts |
|----------|----------|--------|-----------|------|-----------|
| `phase-1a-marker-screen` | `marker-screen-margin` | `gate_cleared` | 0 | thrash_screen_strict vs poll: **PASS** (no poll workers in strict cell) | [`../proofs/phase-1a/`](../proofs/phase-1a/) |
| `phase-1b-framing-dry-run` | `stats-jev-tournament` / `frozen-card-search` (protocol) | `gate_cleared` | 0 | — | [`../proofs/validated/phase-1b-1c/dry_run_batch_log.json`](../proofs/validated/phase-1b-1c/dry_run_batch_log.json), [`../proofs/framing/registry.json`](../proofs/framing/registry.json), [`../proofs/manifests/card_hash_manifest.json`](../proofs/manifests/card_hash_manifest.json) |
| `phase-1c-mount-probe` | `summary-then-judge` (gate) | `refused` (`prose_required` / `absent`) | 0 | — | [`../proofs/validated/phase-1b-1c/mount_probe_results.json`](../proofs/validated/phase-1b-1c/mount_probe_results.json) |
| `pilot-field-proof-wave-001` | `stats-jev-tournament` + `frozen-card-search` + `segment-swarm-arbiter` (Pilot) | `registered_awaiting_live` | 0 (dry-twin) | not evaluated | [`REGISTRATION-pilot-field-proof.md`](REGISTRATION-pilot-field-proof.md), [`../proofs/capture/pilot-field-proof/`](../proofs/capture/pilot-field-proof/), [`../proofs/validated/pilot-field-proof/`](../proofs/validated/pilot-field-proof/) |

## phase-1a-marker-screen

- **Registered:** [`REGISTRATION-phase-1a.md`](REGISTRATION-phase-1a.md)
- **Metric:** marker-family ranks, poll-overlap lists, Spearman vs `T` with/without thrash prototypes; round-trip mismatch rate 0 on pack `cumulative`.
- **Kill (approach §4):** extreme thrash cell must not contain poll-label workers — evaluated on `thrash_screen_strict` (no Edit/Write ∧ reread ≥ 8 ∧ compaction ≥ 8 at last cp ≤ 120).
- **Cox sketch:** exploratory concordance **1.0** on thrash-consensus proxy events (complete separation; not identified). Future gate concordance ≤ 0.70 **not** fired on this sketch.

## phase-1b-framing-dry-run

- 32-cell dry-run (8×4), dedupe + cap check, ≥8 registered blobs, `unregistered_framing` demo. Dummy `TYPESAFE_API_KEY` absent from committed log.

## phase-1c-mount-probe

- No `WORKFLOW_PROGRESSIVE_CORPUS` on cloud VM; default fixtures redacted or missing per pilot — honest refusal for Flash prose.

## pilot-field-proof-wave-001

- **Registered:** [`REGISTRATION-pilot-field-proof.md`](REGISTRATION-pilot-field-proof.md) (96 Jev cells, `budget_tokens` 400k, 12 framings, stratified 8).
- **Dry-twin:** `run_pilot_dry_twin.py` → `capture/pilot-field-proof/jev/dry-twin/` (0 live POSTs). `TYPESAFE_API_KEY` unset on cloud VM.
- **Local swarm stub:** `run_local_swarm_pilot.py` (dry-stub; `--live-local` for Ubuntu `:8080`).
- **NEXT:** CHM live Jev → `jev/live/` JSONL; evaluate kills; optional Flash if mount passes.
