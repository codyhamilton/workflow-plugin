# Backlog — observability, tooling, spikes

Prioritised gaps for the Workflow Optimiser. Not a commitment order — reorder when goals shift.

## P0 — measurement foundation

- [ ] **First eval scenario** — pick a repo/task with known reference; populate `evals/scenarios/<name>/` and freeze baseline (see `PROPOSALS/2026-09-30-first-eval-scenario.md`).
- [ ] **Classify review gate** — script or doc workflow to set `human_label` on low-confidence rows; report accuracy/confusion (`jq` summary from JSONL).
- [ ] **Fix Claude snapshot text join** — newline-per-char distortion in user message fields (see FINDINGS 2026-09-30).

## P1 — typed eval hooks

- [ ] **Jev assertion spike** — one Choice question wired to a skill outcome (e.g. “does IMPLEMENTATION.md list verified outcomes per phase?”) on fixture JSON, not live API (see proposal).
- [ ] **Compare classify vs `iterate_analysis.py`** — same sessions, document disagreement (session *kind* vs spawn phase regex).
- [ ] **Snapshot hash regression test** — golden files for Cursor + Claude extract JSON.

## P2 — observability & harvest

- [ ] **Pipeline outcome harvest** — formalise workflow-tuning’s merged-PR scrape into a repeatable checklist + storage location.
- [ ] **Cost window ↔ session join** — `cost_window.py` notes no join key; document limitation or add bridge metadata when available.
- [ ] **Phase driver MVP** — implement minimal `tools/driver/` per `docs/plans/06-phase-driver/DESIGN.md` (large; blocked on harness nesting economics).

## P3 — research follow-ups

- [ ] LangGraph-style **evaluator–optimizer** loop for brief quality (offline, not live harness).
- [ ] **Human-in-the-loop** checkpoint patterns for `design` assumption ledger (map from OpenHands security/HITL docs).
- [ ] Document **Composer vs Grok 4.7 medium** split for Optimiser runs (model policy in lab README).

## Done / landed

- [x] Jev classify spike code on master (`tools/transcript/classify.py`, 2026-09-30).
- [x] `docs/lab/` workspace scaffold (2026-09-30).
