# Seat prompt scaffolding — `shape-qual-full-maps-v1`

**Status:** scaffolding only. Do **not** launch Composer / Sonnet / Grok seats from the packs PR. No `--call-jev`.

**Packs:** [`shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl`](shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl) (104 rows; 34 workers). Inventory: [`INVENTORY-shape-qual-full-maps-v1-20261001-214046.json`](INVENTORY-shape-qual-full-maps-v1-20261001-214046.json).

**Terms:** [`TERMS.md`](../../../../TERMS.md) §11 + §14.

## Hard rules for every seat

1. Read **only** the hybrid_v0 pack row(s) for the worker (all `75:15` checkpoints for that `worker_id`).
2. Answer the three qualitative questions below.
3. **`early_signals` ≤ ~120T only.** Anything later is outcome / mid-late symptom — do **not** list it under early signals.
4. Exit turn + earliness are **secondary**. Do not optimize for A0 or exit agreement.
5. Do not use maps nicknames, prior seat labels, or turn count alone as the answer.

## Questions (per worker)

1. **Narrative shape** — How did this run look? (Free prose; optional labels `late_pivot` / `early_thrash` / `unclear` from §11.)
2. **Phases contained** — Ordered phases with turn anchors (e.g. productive build → validation pivot; early thrash; wait/implement; census; sleep/poll).
3. **Early signals (≤ ~120T)** — Concrete, turn-anchored foreshadowing of how it played out. Cite only turns ≤ ~120 that appear in the packs. Mid/late symptoms after ~120 are **not** early signals.

**Secondary (optional report):** recommended exit turn + earliness vs ideal. Spread across seats is expected and not a hard fail.

## Suggested verdict row shape

```json
{
  "experiment": "shape-qual-full-maps-v1",
  "worker_id": "<id>",
  "model": "<Composer|Sonnet|Grok>",
  "narrative_shape": "<prose>",
  "shape_label": "late_pivot|early_thrash|unclear",
  "phases": [{"range": "75-120", "name": "…", "note": "…"}],
  "early_signals": [{"turn": 90, "signal": "…"}],
  "early_signal_window_respected": true,
  "recommended_exit": null,
  "earliness": null,
  "rationale": "≤120 words"
}
```

Every `early_signals[].turn` MUST be ≤ 120. Set `early_signal_window_respected` false only if the seat could not find any ≤120 foreshadowing (empty list is OK; post-120 citations are not).
