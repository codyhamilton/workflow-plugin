---
name: transcript-parser
description: Parse an AI tool session transcript to extract cost metrics (agents spawned, tool turns per agent, tool type breakdown, context estimate, wall time) in eval cost-comparison format. Use after a plan-execute run to populate a cost-comparison.md, or during workflow-tuning to compare execution approaches.
---

# Transcript Parser

Extract objective cost metrics from a session transcript and produce a section for `cost-comparison.md`.

## Quickstart

```bash
# Find recent sessions (both Claude Code and Cursor)
python3 tools/transcript/find.py ~/workspace/my-project

# Extract and summarise
python3 tools/transcript/extract.py latest --project ~/workspace/my-project > /tmp/s.json
cat /tmp/s.json | python3 tools/transcript/stats.py

# Emit cost-comparison.md section
python3 tools/transcript/cost.py --session latest --project ~/workspace/my-project --label Candidate
```

Paste the `cost.py` output into `cost-comparison.md` under the appropriate `## Baseline` or `## Candidate` heading. Schema: `evals/README.md`.

## Session resolution

`extract.py` accepts:
- UUID or prefix (`f06c7365`)
- Claude URL slug (`session_01GUoz3qj2N9czSfWTifD6rM`)
- Full Claude URL
- `latest` (most recent session for the project)

Filter to one harness with `--tool claude-code` or `--tool cursor`. Default queries both.

## Workflow

1. **Identify the session** — user input, IMPLEMENTATION.md Session section, or `find.py` / `latest`.
2. **Extract** — `python3 tools/transcript/extract.py <ref> [--project PATH]`.
3. **Format** — `cost.py --label Candidate` (or pipe extract output to `stats.py` for a quick overview).

## Rules

- Report what is in the transcript. Do not estimate counts you cannot read.
- Mark unavailable fields explicitly in output (`cost.py` handles this for context estimate).
- `token_usage` and `api_calls` in extract output include **parent + all subagents** (deduped per `message.id`). Use `parent_token_usage` / `subagent_token_usage` for the split.
- Context estimate is the first parent response only — not total session context. For billed tokens, use `token_usage` from `stats.py`.
- **Cursor** JSONL has no usage blocks. Use `cost_estimate.py` for ballpark tokens/cost (fixed context + per-tool deltas + cache simulation). Reconcile with `usage-events-*.csv` via `--reconcile-csv` or `cost_window.py` for the CSV side.

## Reference

Full command reference, normalized schema, and extension guide: `tools/transcript/README.md`.
