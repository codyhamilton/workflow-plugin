# Backlog — bot control, observability, workflow

Prioritised for the Grok Bot remit in `GOALS.md`. Reorder when a kill line in the [strategy pass](ANALYSIS/2026-09-30-grokbot-driver-reorient.md) fires.

## P0 — automated driver

- [x] **One-phase trigger** — `tools/driver/run.py --once`, `mcp_server.py` (`status` / `trigger_phase` / `poll`); provider interface + dry-run; driver never commits (spike B, 2026-09-30).
- [x] **Unattended core skills** — Cursor cloud kill line: bake core-only `install.sh` into the image (`docs/lab/bootstrap/cursor-cloud-setup.sh`); hooks do not reload skills. Claude Code remote: copy `docs/lab/bootstrap/session-start.sh`. Gate: `python3 tools/driver/check_skills.py` (step 5, 2026-09-30). This environment's snapshot was not rebuilt.

## P1 — asserts and outcomes

- [x] **Run record** — `run_record.py`, JSONL outside plan folder; wired from `run.py`, `assert_phase.py`, `status.py --run-record` (step 4, 2026-09-30).
- [x] **First outcome row** — `evals/scenarios/trailer-completeness/` (`verify.py`: status → `--once` → `--deterministic` assert). Cost unavailable (no provider key). Classify not used (`PROPOSALS/2026-09-30-first-eval-scenario.md`, 2026-09-30).

## P2 — workflow follow-through

- [ ] **Driver loop to completion** — `run.py` without `--once`, after the bot has driven two phases via the one-phase primitive. Claude provider first, Cursor provider second (design phases 2–3).
- [ ] **Pipeline outcome harvest** — workflow-tuning's merged-PR scrape as a repeatable checklist the collector can run.
- [ ] **Headless posture check** — confirm a bot invoking `design` gets the assumption ledger and never waits on an interactive checkpoint.

## P3 — parked research

- [ ] **White paper: Jev cheap judgement signals** — research pack [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md) landed; Grok pass to write [`PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`lab-proposal` step 4).
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
- [x] **One-phase trigger** — `tools/driver/run.py --once`, provider layer + dry-run, `mcp_server.py` (spike B step 2, 2026-09-30).
- [x] **Jev assert hook** — `tools/driver/assert_phase.py` + `phase_assert.py`; fixtures/tests; deterministic kill line (spike C step 3).
- [x] **Run record** — external JSONL per invocation; git + record for phase/cost/report (spike step 4).
- [x] **Unattended core skills** — install route + disk check; Cursor image-bake recommendation; Claude SessionStart template (step 5, 2026-09-30).
- [x] **First outcome row** — trailer-completeness verifier + FINDINGS row; fixture stand-in, cost unavailable (step 6, 2026-09-30).
