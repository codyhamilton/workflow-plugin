# Session-analysis open field — cycle log

| cycle_id | approach | status | api_calls | kill | artifacts |
|----------|----------|--------|-----------|------|-----------|
| `phase-1a-marker-screen` | `marker-screen-margin` | `gate_cleared` | 0 | thrash_screen_strict vs poll: **PASS** (no poll workers in strict cell) | [`../proofs/phase-1a/`](../proofs/phase-1a/) |
| `phase-1b-framing-dry-run` | `stats-jev-tournament` / `frozen-card-search` (protocol) | `gate_cleared` | 0 | — | [`../proofs/validated/phase-1b-1c/dry_run_batch_log.json`](../proofs/validated/phase-1b-1c/dry_run_batch_log.json), [`../proofs/framing/registry.json`](../proofs/framing/registry.json), [`../proofs/manifests/card_hash_manifest.json`](../proofs/manifests/card_hash_manifest.json) |
| `phase-1c-mount-probe` | `summary-then-judge` (gate) | `refused` (`prose_required` / `absent`) | 0 | — | [`../proofs/validated/phase-1b-1c/mount_probe_results.json`](../proofs/validated/phase-1b-1c/mount_probe_results.json) |
| `pilot-field-proof-wave-001` | `stats-jev-tournament` + `frozen-card-search` + `segment-swarm-arbiter` (Pilot) | `live_complete` (wave-001); **next wave** pruned pool + Luna swarm | 96 (live Jev, wave-001) | Jev: **PASS** `tournament-binary-foreshadow`; **KILL** `tournament-monitor-called-out`. Search: no win. Swarm: **FAIL** local 8/8 (Luna retest pending). **HOLD** scale-up | [`REGISTRATION-pilot-field-proof.md`](REGISTRATION-pilot-field-proof.md), [`../proofs/validated/pilot-field-proof/CYCLE-NOTES.md`](../proofs/validated/pilot-field-proof/CYCLE-NOTES.md), [`../proofs/capture/pilot-field-proof/`](../proofs/capture/pilot-field-proof/) |
| `pilot-wave-002-luna-swarm-dual-label` | `segment-swarm-arbiter` dual-label (Luna+Flash) | `gate_failed_jev_idle` | 0 (no Jev) | Flash conflict **5/8 FAIL**; Luna **0/8 PASS** (volume-label only); Soft Standard **HOLD** | [`CYCLE-wave-002-dual-label-idle.md`](CYCLE-wave-002-dual-label-idle.md), [`../proofs/capture/pilot-field-proof/local-swarm-luna-86bbbe4/`](../proofs/capture/pilot-field-proof/local-swarm-luna-86bbbe4/), [`../proofs/capture/pilot-field-proof/local-swarm/`](../proofs/capture/pilot-field-proof/local-swarm/) |

## phase-1a-marker-screen

- **Registered:** [`REGISTRATION-phase-1a.md`](REGISTRATION-phase-1a.md)
- **Metric:** marker-family ranks, poll-overlap lists, Spearman vs `T` with/without thrash prototypes; round-trip mismatch rate 0 on pack `cumulative`.
- **Kill (approach §4):** extreme thrash cell must not contain poll-label workers — evaluated on `thrash_screen_strict` (no Edit/Write ∧ reread ≥ 8 ∧ compaction ≥ 8 at last cp ≤ 120).
- **Cox sketch:** exploratory concordance **1.0** on thrash-consensus proxy events (complete separation; not identified). Future gate concordance ≤ 0.70 **not** fired on this sketch.

## phase-1b-framing-dry-run

- 24-cell dry-run (8×3 tournament), dedupe + cap check, ≥8 registered blobs, `unregistered_framing` demo. Dummy `TYPESAFE_API_KEY` absent from committed log.

## phase-1c-mount-probe

- No `WORKFLOW_PROGRESSIVE_CORPUS` on cloud VM; default fixtures redacted or missing per pilot — honest refusal for Flash prose.

## pilot-field-proof-wave-001

- **Wave-001 (live):** [`REGISTRATION-pilot-field-proof.md`](REGISTRATION-pilot-field-proof.md) at 96 cells / 12 framings. `run_pilot_live_jev.py --confirm-live` on Ubuntu — 96 POSTs, 0 errors; meters `input_tokens_observed=76468` / 400k; `jev/live/` on harness only (not committed).
- **Kill eval (wave-001):** winner `tournament-binary-foreshadow`; kill `tournament-monitor-called-out`. `frozen-card-search`: no search win.
- **Local swarm (wave-001):** `:8080` 16/18 timeouts → 8/8 conflict/parse kill; committed `conflict_report.json` may be stale.
- **Next wave (this PR):** **88** Jev cells, **11** framings (prune applied); dry-twin `gate_pass`; default swarm **Luna** (`run_local_swarm_pilot.py --live`). Flash optional; Standard/Max **HOLD** until non-local swarm gate passes.
- Details: [`../proofs/validated/pilot-field-proof/CYCLE-NOTES.md`](../proofs/validated/pilot-field-proof/CYCLE-NOTES.md).
