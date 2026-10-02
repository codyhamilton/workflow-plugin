# Contrast — H1 rating → fire vs signal closeness

**Date:** 2026-10-02  
**Status:** pointer only. Measurement design. **Not** behaviour ship. Does not reopen this pack’s bake-off and does not change the white paper’s `resolved-soft` status.  
**Primary grammar for the next theory → signal → subset loop:** [`../2026-10-01-progressive-jev-session-gates/DESIGN-signal-closeness-v0.md`](../2026-10-01-progressive-jev-session-gates/DESIGN-signal-closeness-v0.md) ([`TERMS.md`](../2026-10-01-progressive-jev-session-gates/TERMS.md) §15).

## What is demoted, and only for that loop

[`H1-DETAIL.md`](H1-DETAIL.md) defines success along this chain:

```text
(Jev state, question, response-class)
    → predictive rating
    → fire / defer
    → fire-time vs ideal steer
```

That chain stays in this pack as the recorded contrast. It is **not** the primary instrument of the next signal loop. A single rating that is then thresholded into fire is the kind of hard decision the 2026-10-02 guidance steps back from: muddy workers do not become crisp by forcing one score into a yes. The white paper’s framing table still lists H1 as the provisional primary of the **interception bake-off**. This file does not re-rank H1–H6 and does not authorise another wave of that chain.

## What the next loop measures instead

Independent **float closeness** to qualitative signals, several asks in one call, each float judged alone, each signal proved or killed before any union. State is specialised per signal (last-N, prompt plus last-N, all user prompts plus last-N, or a programmatic turn-type profile with minimal prose). The weighted union and the per-round discount of the fire bar are Workflow System Manager’s, offline, aligned with decay schedule **D0**. Draft family names `PR-SIGNAL-CLOSENESS`, `PR-SIGNAL-STATE-ABLATION`, and `PR-DECAY-ACCUM` are unsigned. They are not a GO and not a seat protocol.

Wave-2 lessons that motivate the demotion — validation labels collapsing to one class, survival times coming back null, a zero-call profile already separating extremes, tool-grounding recovering productive-edit mass — are written in the design note’s section 4. They are not re-derived here, and they do not unlock hooks or live in-loop calls.

## What not to do from this pointer

- Do not reseat the killed validation yes/no or the killed survival-time questions as if they were H1 variants.
- Do not treat a rating→fire cell as the first measurement of a new qualitative signal.
- Do not load a local `:8080` server, leave maps, or edit harness code from this contrast.
