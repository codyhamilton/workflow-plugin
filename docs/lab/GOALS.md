# Goals — workflow-plugin optimisation

_Last updated: 2026-09-30 strategy pass (UTC). Maintained by Workflow Optimiser + Cody._

## North star

Improve **outcome quality per token** for the design → phased refine/execute → review → close-out loop (core `workflow` plugin), measured on real repos and harvested pipeline outcomes — without breaking cloud-safe defaults.

## Current remit (Q4 2026)

1. **Optimise the plugin itself** — skills, brief patterns, evals, and lab tooling — not a new marketplace product.
2. **Measure success** — honest classify and snapshot metrics first; an external eval scenario only when it has a verifier; transcript + Jev signals for cost/behaviour regressions. A frozen baseline is a milestone, not a verdict.
3. **Cheap typed evaluation** — Jev Choice/Score over compact snapshots (`tools/transcript/classify.py`), not whole-transcript LLM judging.
4. **Operational model policy** — cloud agents on Composer; Grok 4.7 medium for deep research passes; no fast tier; no high-context models by default.
5. **Ship safely** — additive docs and tooling on `master`; behaviour-breaking skill changes only via explicit versioned releases.

## Success metrics

Strategy pass (2026-09-30) tightened these so a single unlabelled batch or a single self-scenario cannot close them. Detail: [`ANALYSIS/2026-09-30-strategy-pass.md`](ANALYSIS/2026-09-30-strategy-pass.md).

| Metric | Target | How we know |
|--------|--------|-------------|
| Snapshot parity | Confirm or kill the Claude state token-density gap (~1.9× chars/4 estimate on the 2026-09-30 batch; Cursor matches) | FINDINGS paragraph: newline ratio, readability, mechanism verdict |
| Classify pilot | All 8 current rows blind-labeled; agreement reported **split** at confidence ≥ 0.8 vs below | FINDINGS table. Publishing the table is success. Hitting 80% is not required |
| Classify calibration (claim) | ≥80% agreement when `confidence ≥ 0.8`, only once **n ≥ 10** such labeled rows exist on one snapshot generation | JSONL `human_label` + FINDINGS. Not claimable on the current 3/8 |
| Hypothesis status | Ledger line for all 8 README hypotheses; #8 recorded as observational-partial from the 2026-09-08 analysis, with the unmeasured remainder named | `FINDINGS.md` |
| Eval corpus | External scenario spec (repo, pinned commit, verifier) **or** an explicit kill of the in-repo self-scenario. A frozen `baseline/` is a later milestone, not a verdict | `evals/scenarios/*/source.md` or a FINDINGS kill line |
| Research hygiene | New external refs mapped to skills/evals when they change decisions | `RESEARCH/INDEX.md` updated |

`workflow_alignment` is not a KPI until a human 0–3 exists. Cross-source score comparisons wait on snapshot parity. Do not grow the classify corpus for pooled metrics before that parity note.

## Focus order

Attention order from the 2026-09-30 strategy pass, not an effort estimate.

1. **First window — honest ruler.** Snapshot parity dump; blind kind labels on the existing eight rows.
2. **Second window — status, not a run.** Hypothesis ledger; external `source.md` only if a verifier can be named, otherwise kill the in-repo first scenario. Parser fix only if move 1 confirms the mechanism.
3. **Third window — one baseline or stop.** One frozen baseline on an external spec, or leave `evals/scenarios/` empty and keep measurement observational. No Jev artifact hook and no driver in this window.

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
