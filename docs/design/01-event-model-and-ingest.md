# Design Intent 1: Event Model and Ingest Contract

What the system records, how records are joined, and what the remote accepts. Part of
[system-architecture.md](system-architecture.md); read its principles first.

## Problem

Executions were reported by agents after the fact. The records lack the conversation ID, model and
cost; the harness label was a default (12 of 13 said "cursor"); hook events never joined the same
conversation; one execution is stuck "running". The cause is that state was requested from the
agent instead of derived from facts the harness already produces.

## Model

Everything is a recorded fact with a join key. State is a view over facts.

### Facts

| Fact | Source | Carries |
|---|---|---|
| Hook event | harness hook → spool | conversation ID, harness, event, tool, timing, model and cost where the payload has them |
| Artifact version | write hook → drain reads file | `repo_id`, `path`, content hash, content, conversation ID, source (`worktree` or `commit`) |
| Commit | hook on `git commit` | SHA, touched paths, rename pairs, conversation ID |
| Capture gap | repair submit | reason, harness, conversation ID |

### Keys

- **Conversation ID** comes from the hook payload. It is stamped on every fact in the envelope. It
  is never written into an artifact.
- **`repo_id`** is the normalised remote URL if one exists, otherwise the root commit SHA. A
  checkout path is never an identity.
- **Artifact key** is `(repo_id, path)`. A version is keyed by content hash; re-posting identical
  content is a no-op. No frontmatter and no IDs inside files.
- **Server IDs** are an index only. Clients never depend on them.

### Edges

`conversation —produced→ artifact version`, `commit —touched→ artifact path`,
`commit —in→ conversation`, `artifact path —alias of→ artifact path`.

An artifact has many conversations and a conversation has many artifacts. Edges are append-only.

### Moves

Best effort. Two signals, applied when building views:

1. A rename pair reported with a commit (authoritative).
2. A new path whose content hash equals the latest version of an artifact whose path no longer
   exists.

Merges are conservative: hash match or git rename only, never fuzzy similarity alone. A detected
move adds an alias edge and rewrites nothing, so a wrong link can be removed. An undetected move
yields a duplicate artifact, which is acceptable.

### Derived execution view

An execution is a view: `conversation + brief + commits + report`. No start or stop events exist.

| Shape | Meaning |
|---|---|
| conversation + brief + commits + report | complete |
| conversation + brief + commits, no report | unreported (a finding in itself) |
| conversation + brief, no commits | started, nothing landed |

The report's presence is the completion signal the phase runner reads. The view is rebuilt from
facts, so it cannot go stale.

## Execution report

A handoff, not telemetry. It exists because the next phase consumes it.

**Consumers**

- The phase runner, which orchestrates a phase and its subagents, reads the reports directly.
- The review agent, to call out known issues.
- Design and refine agents, to pick up leftovers that need re-refining or redesign.

**Why an artifact.** The executing agent writes it at the time, so the runner reads the original,
not its own paraphrase of a subagent reply. It survives the runner's context compaction and is
readable from a later conversation.

**Authorship.** One report per executing subagent, beside its brief. The runner reads reports and
does not rewrite them. A runner-level phase note, if wanted, is a separate artifact with its own
author.

**Content.** What the next phase cannot get another way: what was done against the brief, departures
from the brief and why, unfinished or deferred work, problems hit, surprises. Nothing derivable:
commits, model, cost, duration, files touched, conversation ID.

**No required structure.** The skill defines what good looks like; the report is scored against it.

**Rubric (candidate checks)**

- Says what was done against the brief, verifiably (commits, test results).
- Names every departure from the brief with its reason.
- Leaves unfinished work specific enough to act on without reopening the whole execution.
- States known problems plainly.
- Contains nothing the consumer cannot use.

The wording is defined once and referenced by both the skill and the service's checks, so they
cannot drift.

**Usage measure.** A report whose leftover issues are later addressed by a brief or design is
being used; one that nothing follows up, or later work contradicts, is weak. This is an edge query,
needs no scorer, and waits for the linked dataset.

## Ingest contract

Envelope types accepted by the remote: `hook_event`, `artifact_version`, `commit`, `capture_gap`.

- Idempotent by row hash; at-least-once delivery.
- No session or lifecycle state on the server.
- An execution report is an `artifact_version` whose kind is inferred from its path.
- Artifact kind (design, brief, report) is inferred from path convention, not declared by the agent.

## Who does what

- **Hooks** do cheap local work only: write the spool envelope; on `git commit`, run
  `git rev-parse HEAD` and `git diff-tree -M --name-status`. No network, no file edits.
- **Drain** reads artifact files and hashes them together, scrubs, archives, delivers.
- **Repair submit** is a separate, synchronous, explicit path for "the remote does not know this
  artifact". It shares the envelope builder, the scrub and the delivery client with the drain as a
  library, and shares no queue. Every use is logged as a `capture_gap`.

## Decisions

1. **One report per brief, beside it.** A brief is one piece of work and has one outcome; a
   re-run produces a new version of the same report, not a second report. Proposed path:
   `docs/plans/<plan>/reports/<brief-name>.md`, so the kind patterns cannot collide with
   `briefs/*.md`.
2. **`spool.sh` never snapshots.** It records the event only. If the file is gone at drain time,
   no `artifact_version` is produced; a failure log can be added later.
3. **Harness label comes from the adapter.** Each harness has its own hook config, which passes a
   literal `--harness` name. No `auto` and no default.
4. **Every submitted fact has a conversation ID.** All harness hook schemas carry one. Hook types
   without a correlation ID are not submitted. Commits are captured from the agent's `git commit`
   tool call, so they carry it too; commits made outside an agent are out of scope for now.
5. **Plan 08 is superseded** by this design and the ones that follow from it. See below.
6. **Secret checks are layered.** A light client scrub for obvious formats (known key prefixes,
   private key blocks, `*_KEY=` assignments) runs before anything leaves the machine. The server
   runs a deterministic precheck on arrival, and Jev is the last check before content is persisted.
   This does not stop a secret crossing the wire, but it reduces the chance it is stored. How
   content is held while awaiting the Jev check (pending store or quarantine) belongs to design 3.

## Plan 08 under this model

[plans/08-artifact-submit-hooks](../plans/08-artifact-submit-hooks/DESIGN.md) posts from inside the
write hook: it queries the service for a "submitted" predicate, then calls `POST /v1/designs` or
`/v1/briefs` synchronously (2 s timeout) and returns `posted design_id=…` as `additionalContext`.
That breaks three principles here: hooks do network work, server IDs are handed to the agent to
adopt, and the hash strips frontmatter IDs that no longer exist.

What carries over:

- The path rules for design and brief files, extended with the report pattern.
- The per-harness write-surface table: Claude and Codex `PostToolUse` on write tools, Cursor
  `postToolUse` plus `afterFileEdit`, OpenCode `tool.execute.after`; `FileChanged` and
  `afterTabFileEdit` excluded. The drain uses it to decide which spooled events produce an
  `artifact_version`.
- No file mutation, and a re-write in a new conversation still records an edge.

What goes:

- The `artifact_submit.py hook` registration on every harness. Its CLI form becomes the basis of
  repair submit.
- The submitted predicate. Idempotent ingest makes it unnecessary.
- Synchronous `posted …` / `posting still owed` feedback.
- `tools/hooklog/tests/test_artifact_submit_surfaces.py`, which asserts the old shape and is
  rewritten for the drain.
