# Economics — Jev as cheap pre-filter

## Position

Frontier review (comprehensive-review, adversarial subagents, human Cody) is **high marginal cost** per invocation. Full-session transcript review is incompatible with Grok Bot’s thin context loop.

**Typed Jev questions** over compact JSON state are the cheap layer:

- Small input (headings, counts, brief excerpt, report fence fields).
- Pin `jev-1.13.0`; log scores to JSONL for weekly skim.
- **Never hard-gate** by default — steer attention so expensive follow-ups run on the right ~30% of events, not on every unit or tool batch.

## Break-even intuition

If conditional Jev avoids even **~30%** of expensive follow-ups (extra review agent, re-run phase, human deep-dive) while missing few true failures (because deterministic asserts still catch structural closure bugs), the hook tax pays for itself.

Opposite failure mode to avoid: Jev-triggered **always-on** review → higher cost than today with no verifier gain. Measurement must track **count of review spawns** and **cost per phase**, not session-kind accuracy.

## Relation to 5h window burn

Maps Claude evidence ([`evidence-maps-claude-5h.md`](evidence-maps-claude-5h.md)) shows a **small fraction** of subagents over the ideal band, but those few **dominate** rolling 5h token windows (parallel fat workers). Cheap in-session signals (use case 1) target **early** detection before a worker reaches 150+ API calls or 12MB JSONL — cheaper than post-hoc transcript archaeology.

## Policy alignment

- [`../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md) — Jev for asserts/steer; classify not KPI.
- [`../../GOALS.md`](../../GOALS.md) — turns and cost per phase as observational targets.

## Non-goals (economics)

- Using Jev disagreement to **recalibrate classify**.
- Making Jev scores a **merge gate** without Cody sign-off.
