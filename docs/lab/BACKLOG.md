# Backlog — bot control, observability, workflow

Prioritised for the Grok Bot remit in `GOALS.md`. Reorder when a kill line in the [strategy pass](ANALYSIS/2026-09-30-grokbot-driver-reorient.md) fires.

## P0 — automated driver

- [ ] **One-phase trigger** — CLI `--once` and/or MCP `status` / `trigger_phase` / `poll` that Grok Bot can call; provider by key; driver never commits (spike B). Design: `docs/plans/06-phase-driver/DESIGN.md`.
- [ ] **Unattended core skills** — SessionStart installer hook, Cursor cloud `install.sh`, or image bake, so the bot's first turn sees core skills.

## P1 — asserts and outcomes

- [ ] **Jev assert hook** — one question over compact phase state, dry-run JSON, live log separate from classify, fail branch for the bot (spike C; see `PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`).
- [ ] **Run record** — stdout or external JSON: last report, per-phase cost, assert results. No plan-folder status file.
- [ ] **First outcome row** — one dogfood or `evals/scenarios/` run scored by verifier, trailers, and cost (`PROPOSALS/2026-09-30-first-eval-scenario.md`).

## P2 — workflow follow-through

- [ ] **Driver loop to completion** — `run.py` without `--once`, after the bot has driven two phases via the one-phase primitive. Claude provider first, Cursor provider second (design phases 2–3).
- [ ] **Pipeline outcome harvest** — workflow-tuning's merged-PR scrape as a repeatable checklist the collector can run.
- [ ] **Headless posture check** — confirm a bot invoking `design` gets the assumption ledger and never waits on an interactive checkpoint.

## P3 — parked research

- [ ] LangGraph-style evaluator–optimizer for **brief quality**, offline, using an assert rather than session kind.
- [ ] Document the Composer (collect) vs Grok (strategy) split with a pointer to a real run's inputs and the analysis file it produced.

## Deferred / POC (do not block P0–P1)

Classify remains available as a visualisation. These items are not on the measurement path.

- [ ] **Classify human-label and calibration** — `PROPOSALS/2026-09-30-classify-human-label-workflow.md` (**deferred**).
- [ ] **Claude snapshot text join** — `PROPOSALS/2026-09-30-snapshot-claude-text-join.md` (**deferred**; snapshot parity is not a blocker).
- [ ] **Archive classify spike narrative** — `PROPOSALS/2026-09-30-spike-design-archive.md` (**deferred**).
- [ ] **Classify vs `iterate_analysis.py`** — session kind vs spawn-phase regex. Orthogonal charts; no merge work.
- [ ] **Snapshot hash golden files** — only if a future viz regression needs them.

## Done / landed

- [x] Jev classify spike code on master (`tools/transcript/classify.py`, 2026-09-30) — visualisation POC.
- [x] `docs/lab/` workspace scaffold (2026-09-30).
- [x] Composer vs Grok 4.7 medium split recorded in `docs/lab/README.md` (2026-09-30).
- [x] Classify measurement strategy pass (`ANALYSIS/2026-09-30-strategy-pass.md`, 2026-09-30).
- [x] Strategy reorientation for Grok Bot control (`ANALYSIS/2026-09-30-grokbot-driver-reorient.md`, 2026-09-30).
- [x] **Phase status CLI** — `tools/driver/status.py` (read-only JSON from trailers + `DESIGN.md`; spike A step 1).
