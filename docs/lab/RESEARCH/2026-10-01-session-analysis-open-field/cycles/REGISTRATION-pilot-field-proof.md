# Registration — Pilot field-proof wave

**Cycle id:** `pilot-field-proof-wave-001`  
**Tier:** Pilot ([`RESOURCE-BUDGET-AGGRESSIVE.md`](../RESOURCE-BUDGET-AGGRESSIVE.md) §4)  
**Status:** `registered_awaiting_live` (dry-twin committed; no `TYPESAFE_API_KEY` on cloud VM)  
**Live TypeSafe:** yes, **after** this file + dry-twin pass are committed and CHM confirms key on Ubuntu harness  
**Model pin:** `jev-1.13.0` only  

## Approach ids (one cycle, three workstreams)

| Stream | Id | Role in Pilot |
|--------|-----|----------------|
| **A** | `segment-swarm-arbiter` | Local `:8080` segment labels (~24 cells); Flash arbiter ≤ **4** on conflict only |
| **B** | `stats-jev-tournament` | **96** Jev POSTs on frozen **stats_card**, `early-signal-v0` |
| **D** | `frozen-card-search` | Same wave: **8** baseline + **24** search + **64** matrix fill (see cell plan) |

Workstream **C** (`summary-then-judge`): optional **8** Flash cards only if mount probe passes on Ubuntu; **0** Jev on summary cards in Pilot. Not blocking A/B.

## Workers (stratified 8)

Hold-out **26** untouched. Same draw as [`paths.py`](../proofs/lib/paths.py) `STRATIFIED_EIGHT`:

| worker_id | stratum (standing) |
|-----------|-------------------|
| `ca977b9ca0dd` | thrash_consensus |
| `92a48e004519` | thrash_consensus |
| `87a380bc64ff` | poll_label |
| `bb6165018de0` | poll_label |
| `15f24c7ba18c` | poll_label |
| `0677f597286e` | residual (steady build) |
| `074c8cf22927` | residual (steady build) |
| `07357f196666` | weak_thrash |

## Card

- **Kind:** stats_card (frozen per worker at last checkpoint ≤ `early_window_end`)  
- **Manifest:** [`proofs/manifests/card_hash_manifest.json`](../proofs/manifests/card_hash_manifest.json)  
- **Schema:** `early-signal-v0`, `hide_outcome_suffix: true`  

## Framing pool (12 registered hashes)

All slugs in [`proofs/framing/registry.json`](../proofs/framing/registry.json) after dry-twin regen (12 rows). Tournament quartet plus eight pool / spike slugs including `pool-thrash-card-anchor` and `pool-residual-baseline`.

Question blobs whose hash is **not** in that registry must return `unregistered_framing` and must not POST.

## Budget

| Field | Value |
|-------|------:|
| `max_calls` | **96** (single wave; ≤ **256** cap per `analysis.batch_trial`) |
| `budget_tokens` | **400_000** input tokens (covers mid **2k** × 96 ≈ 192k; high **4k** × 96 ≈ 384k) |
| Jev USD mid (direct $0.042/M) | ~$0.008 |
| Local completions (A) | **~24** planned ([`local_swarm_plan.json`](../proofs/capture/pilot-field-proof/local_swarm_plan.json)) |
| Flash (C, optional) | 0–8 summaries + ≤ **4** arbiter |

## Jev cell plan (96)

Committed machine-readable plan: [`proofs/capture/pilot-field-proof/jev_cell_plan.json`](../proofs/capture/pilot-field-proof/jev_cell_plan.json).

| Arm | POSTs | Rule |
|-----|------:|------|
| **Baseline** | **8** | Reproducible random slug draw per baseline cell (seed `pilot-field-proof-wave-001-baseline-v1`) |
| **Search** | **24** | First **6** stratified workers × **4** tournament framings |
| **Matrix fill** | **64** | Remaining worker × framing pairs to complete **8 × 12** |

## Kill criteria (copied — do not paraphrase)

### `segment-swarm-arbiter` ([`CANDIDATE-APPROACHES.md`](../CANDIDATE-APPROACHES.md) §3)

- Conflict or parse failure on more than **4 of the 8** stratified workers. The arbiter is then the whole panel, and this approach has collapsed into summary-then-judge at higher operational cost.
- A local response is repaired by a TypeSafe retry.
- A stable label of `thrash_bundle` on any poll-label worker in the 8. That kill fires even if Flash would have caught it, because the savings depend on trusting stable labels enough to skip Flash.
- Windows whose end is past `early_window_end` were sent.

### `stats-jev-tournament` (§1)

- The zero-call extreme cell already separates the two prototypes from all four poll-label workers. Further Jev framings of the same card are not scheduled (the tournament's premise, that the model must interpret the card, is idle).
- Or a live framing flags a poll-label worker together with both prototypes.
- Or any POST uses a model other than `jev-1.13.0`, or a second rubric pass rewrites a framing after seeing answers.

### `frozen-card-search` (§5)

- The winning framing's hash is absent from the pre-run registry.
- Search-arm mechanical reward ≤ baseline arm.
- The allocator's reward function reads `shape_label`, `shape_detail`, or stratum.
- A second wave under the same registration id.

### Pilot aggregate ([`RESOURCE-BUDGET-AGGRESSIVE.md`](../RESOURCE-BUDGET-AGGRESSIVE.md))

- Local conflict **> 4 / 8**; poll flags co-occur with thrash prototypes; unregistered framing.

## Capture (required before compare tiers)

Layout: [`proofs/capture/README.md`](../proofs/capture/README.md). Dry-twin paths populated by [`run_pilot_dry_twin.py`](../proofs/run_pilot_dry_twin.py). Live paths are empty until CHM run.

## Guards

- Default `dry_run`. Live needs `live`, `confirm_live`, non-empty `TYPESAFE_API_KEY`.
- One live TypeSafe cycle at a time ([`RESEARCH-OPS.md`](../RESEARCH-OPS.md)).
- No hooks, no behaviour ship, no `replay_progressive_gates.py --call-jev`.

## NEXT (CHM / Ubuntu live)

1. `export TYPESAFE_API_KEY=…` on harness (confirm direct vs gateway pricing on console).
2. `pip install -r proofs/requirements-lab.txt`  
3. `python3 proofs/run_pilot_dry_twin.py` — must show `gate_pass: true` (already committed from cloud).  
4. `python3 proofs/run_local_swarm_pilot.py --live-local` with `WORKFLOW_LOCAL_LLM_URL` → `capture/.../local-swarm/completions.jsonl`.  
5. `python3 proofs/run_pilot_live_jev.py --confirm-live` (optional `--limit N` smoke) → `capture/pilot-field-proof/jev/live/`.  
6. Close cycle in [`CYCLE-LOG.md`](CYCLE-LOG.md) with call counts and kill evaluation.
