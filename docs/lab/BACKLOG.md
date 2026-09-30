# Backlog — observability, tooling, spikes

Reordered 2026-09-30 strategy pass. Rationale and kill lines: [`ANALYSIS/2026-09-30-strategy-pass.md`](ANALYSIS/2026-09-30-strategy-pass.md). Items stay proposed until the move’s how-we’ll-know line is met. Not an effort estimate.

## Now — next three moves

- [ ] **1. Snapshot parity diagnostic** — dump one Claude and one Cursor `first_user_message` from the 2026-09-30 batch (length, newline ratio, readability) and record `(input_tokens − 728) / snapshot_token_estimate`. **Done when:** FINDINGS states confirm or kill for the newline-per-character mechanism. **Kill:** readable prose with a normal newline ratio → do not patch `parsers/claude.py` on this hypothesis; leave the 1.9× density gap as an open question. See `PROPOSALS/2026-09-30-snapshot-claude-text-join.md` (still proposed).
- [ ] **2. Blind kind labels on the existing 8 rows** — label from `SESSION_KIND_CRITERIA` without reading `answers`. Kind in `human_label`; optional `align=<0-3>` in `human_notes` only. **Done when:** FINDINGS table splits agreement at confidence ≥ 0.8 (3 rows) versus below (5 rows). **Revise taxonomy if:** no single dominant kind on ≥ 3 rows, or high-confidence agreement worse than 2/3. Do not claim the 80% GOALS line. See `PROPOSALS/2026-09-30-classify-human-label-workflow.md` (still proposed).
- [ ] **3. Hypothesis ledger + first-scenario decision** — eight README hypotheses with status and pointer; mark #8 observational-partial via `docs/analysis/2026-09-08-workflow-vs-field.md`; name the unmeasured remainder (cloud per-phase turn/context counts). Same entry: external `evals/scenarios/<slug>/source.md` (repo, SHA, verifier) **or** kill the in-repo self-scenario. **Kill:** do not start a full workflow run to manufacture a number, and do not use a `docs/plans/` self-solve as the fixture. See `PROPOSALS/2026-09-30-first-eval-scenario.md` (still proposed; do not execute as written).

## After those three

- [ ] **Parser fix + reclassify**, only if move 1 confirms the mechanism. Same four Claude session ids; compare `snapshot_hash` and token estimate. Do not reuse labels collected on the old hash. Golden snapshot fixture rides along with the fix (`PROPOSALS/2026-09-30-snapshot-claude-text-join.md`).
- [ ] **Classify vs `iterate_analysis.py` note** — side-by-side on sessions that actually have spawns. Expect disagreement: phase regex ≠ session kind. Document that and stop. Do not merge taxonomies. `agree_with_iterate_phase_mode` is not a target.
- [ ] **One frozen baseline** — only after an external spec with a verifier exists. First run establishes `baseline/`; it is not a hypothesis verdict (`evals/README.md` variance rule).

## Later

- [ ] **Pipeline harvest checklist** beyond the single hypothesis ledger line (workflow-tuning merged-PR scrape, storage location).
- [ ] **Cost-window join limitation** — document that `cost_window.py` has no session join key, or add bridge metadata when a real key exists. Not on the critical path.
- [ ] **Spike design archive** — optional onboarding doc. Code constants remain source of truth. Not a blocker (`PROPOSALS/2026-09-30-spike-design-archive.md`).

## Parked (do not start this quarter)

- [ ] **Jev artifact assertion spike** — deferred until kind calibration exists **and** someone names a check a schema cannot do. “Does IMPLEMENTATION.md list verification per phase?” is deterministic. Do not ship a Score ≥ 2.5 threshold (`PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`).
- [ ] **Phase driver MVP** (`tools/driver/`) — contradicts the Q4 non-goal. Revisit only with a measured nesting-economics reason.
- [ ] **LangGraph-style brief-quality optimizer** — same dead end as the assertion spike, less specified.
- [ ] **HITL changes** to `design` or `execute` — behaviour change; execute HITL stays forbidden for cloud.
- [ ] **Online per-turn Jev gating** — non-goal. Batch classify is not calibrated yet.
- [ ] **In-repo plan as first eval scenario** — no independent verifier.
- [ ] **Retuning the 0.8 gate on n=8** — provisional review exemption only.

## Done / landed

- [x] Jev classify spike code on master (`tools/transcript/classify.py`, 2026-09-30).
- [x] `docs/lab/` workspace scaffold (2026-09-30).
- [x] Composer vs Grok 4.7 medium split recorded in `docs/lab/README.md` (2026-09-30). Closed by the strategy pass; no further doc needed.
- [x] Strategy pass written (2026-09-30): `ANALYSIS/2026-09-30-strategy-pass.md`.
