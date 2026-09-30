# Goals — workflow-plugin optimisation

_Last updated: 2026-09-30 (Brisbane), Grok Bot reorientation. Maintained by Workflow Optimiser + Cody._

Strategy pass: [`ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](ANALYSIS/2026-09-30-grokbot-driver-reorient.md).

## North star

Improve **outcome quality per token** for the design → phased refine/execute → review → close-out loop, measured on real runs the automated driver can observe — trailer-complete phases, verifier results, and provider cost — while core skills stay cloud-safe.

## Current remit

1. **The workflow** — cloud-safe core skills, verbatim briefs, `Workflow-Phase:` trailers, cold reads between phases.
2. **Observability** — a fresh process (the bot, a later session, this notebook) can read phase state, the last report, per-phase cost, and assert results without opening a transcript.
3. **Control** — **Grok Bot** or a similar unattended driver runs the loop end to end. Humans escalate on `unsuccessful`. They are not the default phase dispatcher.
4. **Jev asserts** — TypeSafe Jev (`jev-1.13.0`) at phase boundaries for alignment, logging, and steering. Session classify (`tools/transcript/classify.py`) is visualisation only.
5. **Measurable outcomes** — evals and dogfood runs scored by verifiers, trailers, and cost. Classify labels do not gate those scores.
6. **Model split** — Composer (or an equivalent collector) gathers raw observations. Grok does strategy passes over that material.
7. **Ship safely** — additive docs and tooling on `master`. Behaviour-breaking skill changes only via explicit versioned releases.

## Success metrics

| Metric | Target | How we know |
|--------|--------|-------------|
| Bot phase advance | A ≥2 phase design reaches `done`, or stops at the first `unsuccessful`, with zero human `execute` dispatches | Driver/bot log in `FINDINGS.md` |
| Phase status | Resolver JSON matches hand resolution on a fixture set (open phase, wrap-up, done) | Fixture run; bot consumes JSON only |
| Assert steer | One Jev assert, pass fixture and fail fixture, logged; fail fixture takes the fail branch | Assert JSONL + fixture note |
| Outcome row | ≥1 run with verifier pass/fail, trailer list, and cost; classify not in the gate | `FINDINGS.md` or `evals/` |
| Cloud skills | Fresh unattended session lists core skills with no human install step | Hook, image bake, or Cursor `install.sh` note |
| Research hygiene | External refs mapped to bot, hooks, trailers, or asserts when they change decisions | `RESEARCH/INDEX.md` |

## Non-goals (this quarter)

- Classify calibration, `human_label` gates, and Claude/Cursor snapshot parity as blockers or KPIs.
- Per-turn Jev gating inside worker loops.
- Requiring the lab plugin (`iterate`, `workflow-tuning`) on the bot path.
- A status file inside the plan folder (invariant: nothing in the repo carries status).
- Storing full message bodies in a conversation indexer.
- Deleting the naive coordinator path on harnesses that already nest two levels. That path stays; the bot path is what we measure next.

## Skill loop under optimisation

| Stage | Skill or tool | Optimisation levers |
|-------|----------------|---------------------|
| Bound change | `design` | Headless assumption ledger for the bot; verbatim intent |
| Decompose | `refine` | Brief density, unit budgets, bounce rules |
| Build | `execute` | One phase, trailer, report, then stop |
| Drive | Grok Bot + `tools/driver/` | Status, one-phase trigger, loop ownership |
| Align | Jev assert hook | Compact phase state, log, steer or escalate |
| Judge | `comprehensive-review` | Outcome-keyed review, remediation split |
| Finish | `close-out` | Record shape, contract promotion |
| Pipeline | `post-build` | Right-size, QA derivation, required checks |
| See | transcript tools, classify | Cost extraction and session-kind **charts**, not gates |
