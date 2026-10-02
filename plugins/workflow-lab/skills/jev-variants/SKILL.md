---
name: jev-variants
description: Generate and register Jev Stage A test variants (signals, state specs, marker wording) as validated, lineage-tracked registry files, and assemble budget-bounded rounds from them. Use when running a variant-authoring agent for the H2 fire-timing search, or when planning the next tuning round.
---

# Jev variants

The Stage A search is a matrix: **signal × state variant × marker wording × session × checkpoint**. Agents author the first three axes; code (`tools/jev-variants/jev_variants.py`) validates them and expands rounds. Evidence rules live in `docs/lab/JEV-METHODOLOGY.md` (H2, Stage A). Sessions, not cells, are the evidence denominator.

## Running authoring agents (opencode / Flash)

The orchestrator generates a self-contained brief per agent run and passes it as the agent's whole prompt. The agent needs no skill loading:

```bash
python3 tools/jev-variants/jev_variants.py brief signal-proposer --root <registry> --round R002 --n 5 --sessions <discovery ids>
python3 tools/jev-variants/jev_variants.py brief state-designer  --root <registry> --round R002 --n 5
python3 tools/jev-variants/jev_variants.py brief marker-writer   --root <registry> --round R002 --n 5 --signal <sig id>
```

The brief embeds the role rules, a valid example, the allowed enums, the existing variants to avoid, and the exact `new` command with a three-try retry limit. Run many briefs in parallel; the content-hash ids and near-duplicate check keep concurrent agents from colliding or piling up paraphrases. `template <kind>` prints just the example spec.

## Roles

Pick one role per agent run. Do not combine roles; independent authoring is what makes the matrix worth running.

| Role | Reads | Writes | Must not |
|---|---|---|---|
| **signal-proposer** | `discovery`-split sessions only, the signal registry (avoid duplicates), the latest digest | `signals/*.json` | read `dev` or `heldout` sessions; propose a signal with no counterexample |
| **state-designer** | the signal registry (`requires_features`), the state registry, the digest | `states/*.json` | invent builder behaviour: a state is only the parameters the spec schema lists; if you need a new capability, write a `needs-builder` note instead |
| **marker-writer** | one signal, the state specs it will run against, existing markers for it, the digest | `markers/*.json` | change the signal's meaning; reword the signal claim inside the question |
| **round-planner** | the registry, the last digests, the budget | one round file | include `heldout` sessions (sealed until the one confirmatory replay) |

## Register a variant

1. Write only the `spec` JSON to a scratch file. Schema by kind is in `jev_variants.py` (`validate_spec`); fields and enums are the source of truth.
2. Register it (computes the content-hash id, refuses duplicates and invalid specs):

```bash
python3 tools/jev-variants/jev_variants.py new <signal|state|marker> --root <registry> \
  --spec spec.json --author <agent-label> --round R002 \
  --rationale "<why this variant, one or two sentences>" \
  --informed-by <discovery session ids or prior result ids> [--parent <variant id>]
python3 tools/jev-variants/jev_variants.py validate --root <registry>
```

Editing a spec means a **new variant** with `--parent`, so old results stay attached to the exact thing that ran. New variants start `proposed`; the round-planner or human promotes to `active`.

## What makes a good variant

- **Signals:** one observable anchor, a stated direction (`near_completion`, `productive_continuation`, `low_value_continuation`), at least one counterexample from real sessions, and the `zero_call_detector` that would catch it without Jev (or `null` if none can). Declare `requires_features` honestly; the expander skips states that cannot provide them.
- **States:** vary one dimension from an existing state where possible (window size, output truncation, prompt mode, counters), so results are attributable. Always set the `max_tokens` cap. Hook-event states cannot carry assistant text.
- **Markers:** one signal each. Ask for the presence of the signal, not for a stop decision. Cover distinct wording families (direct yes/no criteria, evidence-quote-first, contrast with the nearest confusable signal, negated phrasing), not paraphrases. Polarity must say whether a high score means present or absent. Missing evidence is not a yes.
- **Diversity before volume:** list near-duplicates you rejected in the rationale. A hundred paraphrases of one marker is one variant.

## Plan a round

A round file (`rounds/R00N.json`) names variant ids, `sessions` as `{session_id: split}`, `checkpoints`, `max_calls`, `max_cost_usd`, `est_cost_per_call_usd`, a `test_card` path (hypothesis, baseline, kill rule, written **before** running), and `learned_from` (prior digests or `[]`). Then:

```bash
python3 tools/jev-variants/jev_variants.py expand --root <registry> --round-file rounds/R002.json \
  --ledger results/ledger.jsonl --out rounds/R002.cells.jsonl
```

It refuses invalid or retired variants, sealed held-out sessions, and over-budget rounds (exit 2, no cells written); skips signal/state pairs where the state lacks required features and lists them; and skips cells already in the ledger so interrupted runs resume. The output reports `independent_sessions`; quote that, not the call count.

## After a round

```bash
python3 tools/jev-variants/jev_variants.py digest --ledger results/ledger.jsonl
```

Ledger rows: `cell_id, signal, state, marker, session, split, checkpoint, parse_ok, cost_usd, state_tokens, response`, plus `label` and `score` once independent labels exist. Authoring agents in the next round get the **digest**, never raw held-out rows. Retire variants that fail the parse or cost gates in the test card; record why in the results register (`docs/lab/JEV-RESULTS.md`), including nulls.
