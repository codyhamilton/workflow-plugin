# Design Intent: System Architecture

How the workflow skills, harness hooks, edge capture and the remote quality service fit together,
and the principles that hold across them.

This is a **design-intent doc**, not a plan. It fixes the shape and the seams so each part can take
its own design. Skill behaviour stays in each `SKILL.md`; the skill-level seams stay in
[../ARCHITECTURE.md](../ARCHITECTURE.md). This doc covers everything around the skills.

## Layers

```
 Workflow skills        design · refine · execute · post-build · close-out · comprehensive-review
        │ write files (designs, briefs, execution reports)
 Harness adapters       Claude Code hooks · Codex hooks.json · OpenCode plugin   (cheap, local, no network)
        │ spool envelopes
 Edge capture           spool → drain (scrub, archive, deliver)                  (all transport lives here)
        │ ingest
 Remote service         ingest API · ledger · derived views · scorer client      (replaceable backends)
        │ reads
 Agent advisory tools   read-only MCP: "what should I decide?"
 Maintainer lab         jev-variants · held-out set · white paper                (not part of the pipeline)
```

The scorer is **Jev via TypeSafe System One**, behind a client interface. The model behind it is
TypeSafe's choice and is not part of any contract here.

## Principles

1. **Writes are captured, never requested.** Nothing the system needs depends on an agent calling a
   tool to report state. State is derived from facts: hook events, files, git.
2. **The agent-facing surface is read-only and exists to help the agent decide.** A tool earns a
   place only if the agent would act differently in this run because of its answer. Tools that
   serve only the dataset are removed from the agent's list.
3. **Capture never mutates what the agent wrote.** No hook edits a file, a commit message or any
   other agent output. Correlation lives in the envelope, not in the artifact.
4. **Relationships are edges, not fields.** A conversation, an artifact version, a commit and an
   event are linked by recorded edges. An artifact touched by three conversations has three edges.
5. **Content and its hash are read together, at drain time.** A hash without its content is
   unverifiable. Intermediate drafts overwritten before the drain are lost; this is accepted.
6. **Ingest is dumb and idempotent.** Deduplication, move resolution and joins happen when building
   derived views, so they can be improved and re-run over existing data. All data is kept.
7. **An output exists only if something consumes it as input.** This is why the execution report is
   a handoff for the next phase, not an admin record.
8. **The drain and the remote are separate services.** The drain never starts or manages the
   quality service. The quality service is a remote; the drain is a client of it. The drain and
   ingest are separated by a module boundary, not a process boundary: a local service may host the
   drain in-process ([design 3](03-remote-service.md#local-serve-hosts-the-drain)).
9. **Secret checks are layered.** A light client scrub runs before anything leaves the machine, on
   every path that sends content. The server runs a deterministic precheck on arrival, and Jev is
   the last check before content is persisted.

## Seams

| Seam | Carries | Direction |
|---|---|---|
| Hook payload → spool envelope | raw event + `{ts, harness, event}` | harness → disk |
| Spool → remote ingest | scrubbed events and artifact versions, batched, idempotent by hash | drain → remote |
| Remote → advisory tools | scores, similar plans, cost estimates, queue state | remote → local MCP shim → agent |
| Remote → scorer | scrubbed artifact text | remote → Jev |

## What is retired

`start_execution`, `complete_execution`, `patch_execution`, `post_design`, `post_brief`,
`patch_design`, `patch_brief` and `link_artifacts` stop being agent-facing. Their jobs are done by
write hooks, derived state and the execution report. `define_checks`, `rate_artifact` and `rescore`
are maintainer operations and move to the REST API or CLI.

## Designs this splits into

| # | Design | Covers |
|---|---|---|
| 1 | [Event model and ingest contract](01-event-model-and-ingest.md) | join keys, artifact identity, derived execution view, execution report, envelope types |
| 2 | [Edge capture](02-edge-capture.md) | spool, drain daemon, client config, MCP shim plumbing, per-harness install and trust |
| 3 | [Remote service](03-remote-service.md) | runtime (Go `workflow` binary), API versioning, auth and tenancy, precheck, storage, screening and scoring, local drain hosting |
| 4 | [Agent advisory surface](04-advisory-surface.md) | the read-only MCP, hook feedback, behaviour when the remote is unreachable |
| 5 | [Distribution](05-distribution.md) | plugin layout, per-harness packaging, the pinned Codex copy |
| 6 | Lab and analysis | held-out set, white paper, check-to-cost revisit |
| 7 | [Analytics site](07-analytics-site.md) | person-facing `/v1/analytics` reads, browser CORS, the static Svelte site, local and Pages hosting |

Order: 1 first, since the rest depend on its keys and envelope types. 2 and 3 can then proceed
together.
