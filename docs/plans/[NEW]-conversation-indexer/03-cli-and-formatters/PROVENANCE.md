# Provenance: 03 — CLI Queries and Cost-Comparison Formatter

## Session

- Session: Initial child-plan write (Jun 14, 2026)
- Timestamp: 2026-06-14T00:00:00Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> We'd want to index conversation logs, store them efficiently, then provide a queryable interface.

## Planning Conversation

### Turn 1

**Agent asked:** Should `cost-comparison` support multiple sessions side-by-side (Baseline vs Candidate)?

**Agent decisions:**

- Yes, with a `--baseline` flag. The default single-session render is the primary case; side-by-side is the eval case.
- The full multi-session design (multiple candidates, statistical comparison) is deferred until an actual eval run needs it. v1 supports one-or-two.

### Turn 2

**Agent asked:** Markdown output only, or also JSON?

**Agent decisions:**

- Both, behind `--format md|json`. Markdown is the paste-ready path; JSON is the programmatic path. The cost is low; the value of "no format lock-in" is high.

## Agent Decisions

- **The cost-comparison formatter is its own module.** `conv_index/formatters/cost_comparison.py` is a peer of the library, not buried in the CLI. The CLI is a thin wrapper. This lets future consumers (e.g., a future workflow-tuning eval) import the formatter directly.
- **Snapshot tests, not just smoke tests.** The formatter output is a contract. A regression in formatting breaks the eval system downstream. Snapshots are the right defense.
- **Documentation ships with the code.** `conv_index/README.md` is a deliverable, not a follow-up. Without it, the CLI is undiscoverable.
- **End-to-end test runs every command.** The acceptance criterion is not "each command tested in isolation" but "the whole tool works end-to-end against the test fixtures."
