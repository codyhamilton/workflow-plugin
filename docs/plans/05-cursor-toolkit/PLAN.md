# Cursor Analysis Toolkit

## Intent

User request, verbatim:

> We have just used the iterate skill for a multi-cycle iteration for some significant changes to an existing repo. The repo is ~/workspace/garcia-music. The costing data is in @usage-events-2026-06-26.csv. The harness was cursor and its transcripts are available in ~/.cursor/projects (find the one relating to this work).
>
> What we should start with is analysing the transcript, thinking about what kind of data we'd want to pull out. I certainly want to consolidate the usage data into costings alongside the workflow, visualise how the workflow is working, assess the quality of the directions given to subagents and its alignment with the workflow. Initial steps should be to pull out data - the transcripts are too large for manual work - we need to pull out stats and important aspects that relate to workflow alignment

> Ok output analysis into a doc, but most importantly ensure the analysis tools are scriptable and easy for agents to run, and documented, so we can reduce manual discovery work. I'd like the tools to make it easy to just search/query/analyse conversation transcripts. ensure it works with cursor for now. First plan the changes and then delegate implementation

## Why This Plan Exists

A just-completed four-cycle `iterate` session in `~/workspace/garcia-music` produced 67 subagents
whose data had been extracted by hand at significant effort. That effort must not repeat, and the
long-horizon answer — a SQLite-backed indexer, see `docs/design/conversation-indexer.md` — starts
with the opencode schema and parser, not Cursor, and does not exist.

This is the fast track: standalone Cursor scripts an agent can invoke with no indexing step and no
database, delivering the analysis capability now and grounding the indexer's Cursor support later.

## Scope

Standalone Python 3.10+ scripts under `tools/cursor/`, no external dependencies, each individually
callable with `--help`, plus agent-oriented documentation and a worked analysis of the garcia-music
session as both provenance and a living example of the toolkit in use.

Out of scope: SQLite indexing or persistence, opencode/Claude Code parsers, full `conv-index` CLI
integration, a web UI or server, and cross-session queries (which require the database).

## Architectural Implications

- New top-level `tools/` directory alongside `skills/`, `docs/`, and `evals/`. Additional harnesses
  become peer subdirectories.
- New `docs/analysis/` directory: outputs of running the toolkit on real sessions. Not plan
  artifacts — those stay in `docs/plans/`.
- No changes to stable docs or to any skill. The toolkit is a peer tool, not a workflow change.
- The scripts do not import from any indexer package, so they can later be adapted into a thin shell
  over one, or retired, without rework elsewhere.

## Acceptance Criteria

Non-user-facing (observable statements):

- `find.py` discovers the garcia-music session and reports its subagent count.
- `extract.py` emits a JSON document with one entry per task call and per subagent; that JSON is the
  input to every other tool.
- `iterate_analysis.py` labels every task call with an iterate phase, detects the cycle structure,
  and reports alignment issues with evidence.
- `search.py` locates a known user correction by pattern.
- `stats.py` reports the per-model breakdown.
- A fresh agent reading only `tools/cursor/README.md` can discover and analyse the session without
  further instruction.
- The analysis document stands alone — a reader understands the session and the findings without
  running the tools.

## Outcome

Shipped. `tools/cursor/` carries `find.py`, `extract.py`, `stats.py`, `search.py`, and
`iterate_analysis.py` as a clean pipe — `find` → `extract` → everything else — with `extract.py`'s
JSON as the cacheable primitive. All acceptance criteria met against the real 67-subagent session.

**Changed:** `tools/cursor/` (five scripts plus `README.md`); `docs/analysis/2026-06-25-garcia-music-iterate.md`.

**Deviations:** two additions beyond the original scope, both driven by using the toolkit rather than
by the plan. `cost_window.py` and `pricing.json` were added when the follow-up case study hit the one
gap the original scope missed — nothing bridged a session to the usage CSV, so the entire cost half of
the analysis was hand-written awk. It now derives its window from a piped session, attributes tokens
per model, reconstructs dollar cost from published rates, and — the part that matters — flags foreign
models and prints an attribution-confidence figure rather than implying precision the data cannot
support. A second analysis document, `docs/analysis/2026-06-26-iterate-case-study.md`, was written to
answer whether `iterate` earned its cost; it is the source of tuning lessons 20–25.

The planned correction to the conversation-indexer child plan was folded into
`docs/design/conversation-indexer.md` instead: Cursor *does* store subagent transcripts (parent JSONL
plus a `subagents/` directory), contradicting the earlier assumption of a single parent agent.

**Review:** none at the time — this plan predates the close-out contract and ran without an
independent review. The toolkit was validated empirically instead: every finding in both analysis
documents was reproduced from the scripts, and the case study reproduces end-to-end from three
commands.

**QA:** not applicable — developer tooling with no user-facing surface.

**Residual risks:** phase classification is heuristic (description plus prompt keyword matching) and
tuned to one orchestrator's style; the README documents the known misclassification cases. Cost
attribution is timestamp-correlation only — reliable here at ~97% because the session dominated the
day, and unreliable for any session overlapping other work (tuning lesson 22).

**Follow-ups:** `iterate_analysis.py` could emit the gate prompt-length curve per cycle as a
first-class signal — it was the cleanest leading indicator of the cycle-01 degradation and currently
requires a manual table. Recorded here rather than as an issue; pick it up if the toolkit gets used
again.

**Provenance note:** originally planned as `04-cursor-toolkit`, a child of the
`[NEW]-conversation-indexer` parent program, under the folder-status taxonomy that has since been
removed. Renumbered and flattened during that migration; the original tree is in git history at
commit `ade4380`.
