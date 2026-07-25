# Cursor Analysis Toolkit

Standalone scripts for pulling workflow and cost data out of Cursor session transcripts, built after
a four-cycle `iterate` run in `~/workspace/garcia-music` produced 67 subagents whose data had been
extracted by hand. Shipped and used: every finding in the two analysis documents it produced is
reproducible from the scripts.

## Intent

User request, verbatim:

> We have just used the iterate skill for a multi-cycle iteration for some significant changes to an existing repo. The repo is ~/workspace/garcia-music. The costing data is in @usage-events-2026-06-26.csv. The harness was cursor and its transcripts are available in ~/.cursor/projects (find the one relating to this work).
>
> What we should start with is analysing the transcript, thinking about what kind of data we'd want to pull out. I certainly want to consolidate the usage data into costings alongside the workflow, visualise how the workflow is working, assess the quality of the directions given to subagents and its alignment with the workflow. Initial steps should be to pull out data - the transcripts are too large for manual work - we need to pull out stats and important aspects that relate to workflow alignment

> Ok output analysis into a doc, but most importantly ensure the analysis tools are scriptable and easy for agents to run, and documented, so we can reduce manual discovery work. I'd like the tools to make it easy to just search/query/analyse conversation transcripts. ensure it works with cursor for now. First plan the changes and then delegate implementation

## Why This Existed

The hand extraction behind that session's analysis was expensive and must not repeat. The
long-horizon answer — a SQLite-backed conversation indexer, specified in
`docs/design/conversation-indexer.md` — starts with the opencode schema and parser, not Cursor, and
did not exist. This was the fast track: standalone Cursor scripts with no indexing step and no
database, delivering the capability immediately and grounding the indexer's later Cursor support.

## What Was Built

`tools/cursor/` as a clean pipe — `find.py` → `extract.py` → everything else — with `extract.py`'s
JSON as the cacheable primitive that every downstream tool reads. `stats.py` reports per-model
breakdowns, `search.py` locates content by pattern, and `iterate_analysis.py` labels each task call
with an `iterate` phase, detects the cycle structure, and reports workflow-alignment issues with
evidence. Python 3.10+, no external dependencies, each script individually callable with `--help`. A
fresh agent reading only `tools/cursor/README.md` can discover and analyse a session with no further
instruction. All acceptance criteria were checked against the real 67-subagent session.

**Changed:** `tools/cursor/` (five scripts plus `README.md`), `docs/analysis/` (new directory for
toolkit outputs, which are not plan artifacts).

## Deviations

- **`cost_window.py` and `pricing.json` were added beyond scope**, driven by using the toolkit
  rather than by the plan: nothing bridged a session to the usage CSV, so the entire cost half of the
  analysis was hand-written awk. It derives its window from a piped session, attributes tokens per
  model, reconstructs dollar cost from published rates, and — the part that matters — flags foreign
  models and prints an attribution-confidence figure instead of implying precision the data cannot
  support.
- **A second analysis document was written**, `docs/analysis/2026-06-26-iterate-case-study.md`,
  answering whether `iterate` earned its cost. It is the source of tuning lessons 20–25.
- **The planned correction to the indexer's Cursor assumptions was folded into
  `docs/design/conversation-indexer.md`** instead of a child plan: Cursor *does* store subagent
  transcripts (a parent JSONL plus a `subagents/` directory), contradicting the earlier
  single-parent-agent assumption.
- **Originally planned as a child of a parent-program folder** under the folder-status taxonomy that
  had since been removed. Renumbered and flattened during that migration; the original tree is in
  git history at `ade4380`.

## Review

None. This plan predates the close-out contract and ran without an independent review. The toolkit
was validated empirically instead: every finding in both analysis documents was reproduced from the
scripts, and the case study reproduces end-to-end from three commands.

## QA

Not applicable — developer tooling with no user-facing surface.

## Residual Risks

- Phase classification is heuristic (description plus prompt keyword matching) and tuned to one
  orchestrator's style. The README documents the known misclassification cases.
- Cost attribution is timestamp correlation only — around 97% reliable here because the session
  dominated the day, and unreliable for any session overlapping other work (tuning lesson 22).

## Follow-ups

`iterate_analysis.py` could emit the gate prompt-length curve per cycle as a first-class signal. It
was the cleanest leading indicator of the cycle-01 degradation and currently needs a manual table.
Not filed as an issue — pick it up if the toolkit gets used again.
