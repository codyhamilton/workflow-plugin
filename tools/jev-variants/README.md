# jev-variants

Registry, validator and matrix expander for the Jev Stage A variant search (see `plugins/workflow-lab/skills/jev-variants/SKILL.md` for the agent protocol).

- Axes: `signals/`, `states/`, `markers/` JSON files under a registry root; filename and `id` are a content hash of `spec`, so results stay tied to what ran.
- `brief <role>` prints a self-contained prompt for a variant-authoring agent (the primary way to drive opencode/Flash runs); `template <kind>` prints an example spec.
- `new` registers a variant (rejects invalid specs, exact duplicates and near-duplicate wording); `validate` checks the whole registry; `expand` produces budget-checked, resumable cells for a round; `digest` rolls a ledger up per axis.
- Not included yet: the runner that builds a state from a transcript and calls Jev for each cell, and the label join. Cells are the contract for that runner.

Tests: `python3 -m unittest discover -s tests` from this directory.

## Panels, corpus and runner (added)

- **Panel** (`pn-…`): the set of markers sent in one Jev call (one marker per signal, 1–16; a live probe answered 1/8/16/32
  questions per call). A cell is (panel, state, session, checkpoint); markers whose signal needs features the state or the
  session's harness lacks are dropped from that cell.
- **corpus.json** (under the registry root): session → `{harness, path, split, …}`. Build with
  `build_corpus.py --root R [--hooklog-dir D]`; split is a stable hash of the session id (60/20/20 discovery/dev/heldout).
  Held-out sessions are sealed unless a round sets `allow_heldout`.
- **events.py / state_builder.py**: normalise Claude, Cursor and hooklog sources into `user_prompt`/`tool_batch` events with a
  `turn` field; the state is prefix-only (events with turn ≤ checkpoint).
- **runner.py** `--root R --round-file F --ledger L [--limit N] [--concurrency 4] [--dry-run]`: one Jev call per cell, question
  ids namespaced `<marker id>__<question id>`, one ledger row per (cell, marker) with the answer, Jev's confidence and
  probabilities, and usage. Secrets are scrubbed from the state before sending. Resumable (rows are keyed by cell id).
- **Cost:** `usage` returns tokens only (no dollars), so ledger costs are the round's `est_cost_per_call_usd` and are flagged
  `cost_estimated`. Score answers are continuous (expected value over the levels, e.g. 0.03 on a 0–3 scale).
- **Turns from hook logs:** see `tools/hooklog/README.md` (verified live for Claude and Cursor).
