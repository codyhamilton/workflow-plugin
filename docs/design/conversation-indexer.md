# Design Intent: Conversation Indexer

A programmatic interface to agent conversation logs — discover sessions, parse them into a
normalized shape, store the analytics in SQLite, and query them from a library or CLI.

This is a **design-intent doc**, not a plan: it describes a target shape and the contracts any
implementation must obey. Nothing here is scheduled. Each slice that gets built takes its own plan
folder and references this file rather than restating it.

## Why it should exist

The `transcript-parser` skill is instruction-based: an agent is told how to read JSONL files and
produce a markdown section. That is fragile in two ways.

**Reproducibility.** Different agents, or the same agent under different context pressure, produce
different output from the same session. There is no canonical record.

**Queryability.** Ad-hoc markdown is not queryable. Cost comparisons across sessions, time series of
tool usage, and cross-project analytics are all out of reach — and the workflow's own tuning depends
on exactly those questions.

The end state: `transcript-parser` becomes a thin renderer over indexed data, and the hard work —
discovering sessions, parsing formats, normalizing tool names, tracking compaction — lives in tested
code instead of a prompt.

## What already exists

`tools/cursor/` ships the Cursor-only fast track: `find.py`, `extract.py`, `stats.py`, `search.py`,
`iterate_analysis.py`, and `cost_window.py`, standalone with no dependencies and no indexing step.
They were built because a 67-subagent session had to be analysed by hand and that cost must not
repeat. See `docs/plans/05-cursor-toolkit/PLAN.md` for what shipped and what it cost.

Two things that work should survive into any indexer: the **pipe shape** (`extract.py` emits a JSON
document that every other tool consumes, so extraction is cached once and analysed many times) and
**explicit attribution confidence** (`cost_window.py` reports what fraction of in-window tokens
belong to models the session actually used, rather than implying precision it does not have).

## Binding contracts

Any implementation must obey these. They were settled during design and are the reason a later plan
can be short.

**Identity is `(tool, session_id)`.** `tool` ∈ `opencode | claude-code | cursor | copilot | codex`.
`session_id` is the tool-native identifier, opaque — never derived or transformed. `project_hash`
(from `cwd` with `/` → `-`) is metadata that aids discovery, **not** an identity key: two sessions may
share one, and a session may move between paths and keep its identity. A separate mapping carries
human-meaningful project labels, so renaming a project does not orphan historical data.

**Timestamps are ISO 8601 UTC, trailing `Z`, exactly three digits of millisecond precision,
zero-padded.** Tool-native timestamps are normalized on parse. Fixed subsecond width is load-bearing:
comparison is lexicographic, which is only correct when every timestamp has the same width.

**Tool names are stored raw and canonical.** `tool_name_raw` is exactly what the source emitted;
`tool_name_canonical` is a small closed enum. One shared normalization function owns the mapping with
per-tool overrides — parsers call it rather than each keeping their own table. Unknown tools map to
`Other` with the raw name preserved. Adding a canonical name is a schema migration, not an edit.

**Parsers implement one interface and are otherwise independent.** A parser discovers its sessions,
reads a session, and returns the normalized types; adding a harness must not require touching the
schema, the indexer, or another parser. Cursor is the deliberate second parser precisely because it
proves the abstraction generalizes beyond the opencode format — its sessions store a parent JSONL
plus a `subagents/` directory, so any interface that assumes one transcript per session is wrong.

**Partial parses are recorded, not fatal.** A malformed record marks the session partial and records
the error; indexing continues. Every indexing run records what it saw, indexed, and errored, so
"indexing is working" is an observable claim rather than an assumption.

**Storage shape.** Sessions, the agents within them, tool turns, per-message token usage, compaction
events, project mapping, and index-run history — with the parent→subagent delegation edge stored on
the parent's turn, so the delegation boundary is queryable. Per-message token capture (input, output,
cache read, cache creation) is required: lesson 21 in the tuning corpus turns on cache-read share, and
a session-level total cannot answer it.

**No credentials, no message bodies.** Fixtures and indexed data carry analytics, never API keys,
tokens, or full message text.

**Cost is a pure function of the data, not a stored field.** Token capture supports a pricing model;
the calculator reads published rates from a separate file that can be edited as they change. Do not
denormalize dollar figures into the database — see lesson 22: the vendor export has no dollars and no
join key, so any stored cost is a reconstruction that will silently rot.

## Boundaries

Out of scope for a first implementation: copilot and codex parsers; a packaged release; a web UI,
server, or MCP interface; live indexing of in-progress sessions; and rewriting `transcript-parser`
itself to consume the index — that is a follow-on once the index exists and is trusted.

Open, and worth deciding before the first slice: whether the code lives in this repo long-term. In-repo
keeps the change reviewable in one diff and lets the plugin use the indexer immediately; a separate
repo becomes right once it has consumers beyond this one. Defer the split until it does.

## Provenance

Distilled from `docs/plans/[NEW]-conversation-indexer/` (parent plan, `DESIGN.md`, and child plans
01–03), which was written under the removed parent-program convention and never built. The full
draft — including the complete v1 SQL schema, the Python interface stubs, the CLI surface, and the
test strategy — remains in git history at commit `ade4380` and can be recovered if a plan for this
work is picked up.
