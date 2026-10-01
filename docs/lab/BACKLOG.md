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

- [ ] **Progressive Jev session gates (researching)** — pack [`RESEARCH/2026-10-01-progressive-jev-session-gates/`](RESEARCH/2026-10-01-progressive-jev-session-gates/INDEX.md), stub [`PROPOSALS/2026-10-01-progressive-jev-session-gates.md`](PROPOSALS/2026-10-01-progressive-jev-session-gates.md). Offline replay only: stored JSONL, Jev on snapshots, multi-model gold exits. **Not high-confidence** until agreement and overshoot numbers exist. No live Claude hook, no `additionalContext` / parent-surface design, no change to the resolved cheap-Jev thresholds.

- [x] **Durable analytics sink (research)** — pack [`RESEARCH/2026-09-30-durable-analytics-sink/`](RESEARCH/2026-09-30-durable-analytics-sink/INDEX.md) and proposal [`PROPOSALS/2026-09-30-durable-analytics-sink.md`](PROPOSALS/2026-09-30-durable-analytics-sink.md) (`status: resolved`). Inventory, HTTP dual-write lab recipe, cloud HTTPS egress proof; local JSONL plus optional HTTP envelope; no default driver/hook wiring (2026-09-30).
- [x] **OpenCode hooks plugin (research)** — pack [`RESEARCH/2026-09-30-opencode-hooks-plugin/`](RESEARCH/2026-09-30-opencode-hooks-plugin/INDEX.md): API map, hook site gaps, `proofs/run_proofs.sh` batch aggregator; separate npm plugin recommended (2026-09-30). White paper resolved: [`PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](PROPOSALS/2026-09-30-opencode-hooks-plugin.md).
- [ ] **Wire accepted durable analytics sink** — implementation, not research. Recommendations are `status: resolved` in [`PROPOSALS/2026-09-30-durable-analytics-sink.md`](PROPOSALS/2026-09-30-durable-analytics-sink.md). One opt-in helper shared by the assert log, Jev probes, and the driver run record; `WORKFLOW_ANALYTICS_URL` unset by default; remote failure leaves exit codes unchanged; `assert_phase --deterministic` stays the kill line; classify stays a POC. Collector deployment (token, dedupe, object storage) is out-of-repo ops.
- [ ] **Wire accepted cheap-Jev signals** — implementation, not research. Recommendations are `status: resolved` in [`PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md). Opt-in Claude hook and Cursor driver JSONL; Jev only at the four accepted points; `assert_phase --deterministic` stays the kill line; classify stays a POC. OpenCode package (unpublished): [`PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](PROPOSALS/2026-09-30-opencode-hooks-plugin.md). OpenCode/LCD keeps `run_proofs.sh` as the stand-in until that package aggregates `tool.execute.after`.
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
- [x] **White paper: Jev cheap judgement signals** — [`PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: resolved`, recommendations accepted pending product wiring, 2026-09-30). Proofs on `112ccfe` (PR #24). Research pack [`RESEARCH/2026-09-30-jev-cheap-judgement-signals/`](RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md).
- [x] **White paper: durable analytics sink** — [`PROPOSALS/2026-09-30-durable-analytics-sink.md`](PROPOSALS/2026-09-30-durable-analytics-sink.md) (`status: resolved`, recommendations accepted pending product wiring, 2026-09-30). Proofs on `1bff769` (PR #27). Research pack [`RESEARCH/2026-09-30-durable-analytics-sink/`](RESEARCH/2026-09-30-durable-analytics-sink/INDEX.md).
- [x] **White paper: OpenCode hooks plugin** — [`PROPOSALS/2026-09-30-opencode-hooks-plugin.md`](PROPOSALS/2026-09-30-opencode-hooks-plugin.md) (`status: resolved`, recommendations accepted pending product wiring, 2026-09-30). Proofs on `d4c4da1` (PR #28). LCD `codyh-ubuntu`: `run_proofs.sh` exit 0, 4/4, one turn-76 `band_exit` row; live sketch not installed.
