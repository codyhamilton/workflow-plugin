# Guidance: measuring with Jev and counters (established findings only)

**Status:** guidance, non-breaking. Source: [`WHITE-PAPER-CLOSE.md`](WHITE-PAPER-CLOSE.md) section 1. Hypotheses are not guidance; they stay in that document until validated.

- **Counters first.** For in-session size/progress, use a plain-code counter (edits to one file, files edited, batches since the last human prompt, browser calls). Jev ties it and adds nothing material (E3). Keep Jev as an optional arm; use it where no simple detector exists (browser/UI loops).
- **The trigger is a soft message** the agent can weigh, not a hard stop. Whether a gated message beats a plain nudge is a behavioural question offline AUC cannot answer.
- **Ask concrete, text-checkable criteria**, not "will this go badly?" Anchor each level to observable content (E7). Do not use Jev's confidence as a trust signal (E6).
- **Compare, don't only grade**: pairwise A-vs-B in both orders is as good as absolute scoring and has no position bias (E8).
- **One call per cell is enough**: scores are near deterministic (E1). Spend calls on more items, not repeats.
- **Do not tune on wording or state size** (E4). Change the signal family or add data.
- **Do not read a single AUC as the level**: labels cap it near 0.74-0.79 (E5), and pooling opposite-direction outcomes hides signal (E2).
- **Scrub before anything goes to Jev/Flash**; keep held-out sealed until the frozen panel is agreed.
