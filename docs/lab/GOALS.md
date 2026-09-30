# Goals — workflow-plugin optimisation

_Last updated: 2026-09-30 (Brisbane). Maintained by Workflow Optimiser + Cody._

## North star

Improve **outcome quality per token** for the design → phased refine/execute → review → close-out loop (core `workflow` plugin), measured on real repos and harvested pipeline outcomes — without breaking cloud-safe defaults.

## Current remit (Q4 2026)

1. **Optimise the plugin itself** — skills, brief patterns, evals, and lab tooling — not a new marketplace product.
2. **Measure success** — populate `evals/scenarios/`, run baseline vs candidate comparisons, and use transcript + Jev signals for cost/behaviour regressions.
3. **Cheap typed evaluation** — Jev Choice/Score over compact snapshots (`tools/transcript/classify.py`), not whole-transcript LLM judging.
4. **Operational model policy** — cloud agents on Composer; Grok 4.7 medium for deep research passes; no fast tier; no high-context models by default.
5. **Ship safely** — additive docs and tooling on `master`; behaviour-breaking skill changes only via explicit versioned releases.

## Success metrics

| Metric | Target | How we know |
|--------|--------|-------------|
| Eval corpus | ≥1 scenario with frozen baseline | `evals/scenarios/*/baseline/` non-empty |
| Classify calibration | ≥80% agreement on hand-labeled sample when Jev `confidence ≥ 0.8` | JSONL log + blind `human_label` column |
| Classify coverage | Routine batch over recent sessions (Claude + Cursor) | `tools/transcript/.classify-log.jsonl` |
| Hypothesis tests | At least one README hypothesis moved to “eval” or “observational” verdict | `FINDINGS.md` + eval `quality-comparison.md` |
| Research hygiene | New external refs mapped to skills/evals when they change decisions | `RESEARCH/INDEX.md` updated |

## Non-goals (this quarter)

- Replacing harness orchestration with a mandatory `tools/driver/` deployment (driver remains design-only).
- Storing full message bodies in a conversation indexer (see `docs/design/conversation-indexer.md`).
- Online per-turn gating of live agents via Jev (batch/offline classify first).

## Skill loop under optimisation

The Optimiser explicitly maps research and proposals to these stages:

| Stage | Skill | Optimisation levers |
|-------|--------|---------------------|
| Bound change | `design` | Phase outcomes, assumption ledger, verbatim intent |
| Decompose | `refine` | Brief density, unit budgets, bounce rules |
| Build | `execute` | Worker routing, per-phase verification, trailers |
| Judge | `comprehensive-review` | Outcome-keyed review, remediation split |
| Finish | `close-out` | Record shape, contract promotion |
| Pipeline | `post-build` | Classify/right-size, QA derivation |
| Lab | `iterate`, `workflow-tuning`, `transcript-parser` | Divergence patterns, lessons corpus, cost extraction |
