# Session-analysis open field — cycle log

| cycle_id | approach | status | api_calls | kill | artifacts |
|----------|----------|--------|-----------|------|-----------|
| `phase-1a-marker-screen` | `marker-screen-margin` | `gate_cleared` | 0 | thrash_screen_strict vs poll: **PASS** (no poll workers in strict cell) | [`../proofs/phase-1a/`](../proofs/phase-1a/) |
| `phase-1b-framing-dry-run` | `stats-jev-tournament` / `frozen-card-search` (protocol) | `gate_cleared` | 0 | — | [`../proofs/validated/phase-1b-1c/dry_run_batch_log.json`](../proofs/validated/phase-1b-1c/dry_run_batch_log.json), [`../proofs/framing/registry.json`](../proofs/framing/registry.json), [`../proofs/manifests/card_hash_manifest.json`](../proofs/manifests/card_hash_manifest.json) |
| `phase-1c-mount-probe` | `summary-then-judge` (gate) | `refused` (`prose_required` / `absent`) | 0 | — | [`../proofs/validated/phase-1b-1c/mount_probe_results.json`](../proofs/validated/phase-1b-1c/mount_probe_results.json) |

## phase-1a-marker-screen

- **Registered:** [`REGISTRATION-phase-1a.md`](REGISTRATION-phase-1a.md)
- **Metric:** marker-family ranks, poll-overlap lists, Spearman vs `T` with/without thrash prototypes; round-trip mismatch rate 0 on pack `cumulative`.
- **Kill (approach §4):** extreme thrash cell must not contain poll-label workers — evaluated on `thrash_screen_strict` (no Edit/Write ∧ reread ≥ 8 ∧ compaction ≥ 8 at last cp ≤ 120).
- **Cox sketch:** exploratory concordance **1.0** on thrash-consensus proxy events (complete separation; not identified). Future gate concordance ≤ 0.70 **not** fired on this sketch.

## phase-1b-framing-dry-run

- 32-cell dry-run (8×4), dedupe + cap check, ≥8 registered blobs, `unregistered_framing` demo. Dummy `TYPESAFE_API_KEY` absent from committed log.

## phase-1c-mount-probe

- No `WORKFLOW_PROGRESSIVE_CORPUS` on cloud VM; default fixtures redacted or missing per pilot — honest refusal for Flash prose.
