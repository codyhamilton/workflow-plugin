---
name: setup
description: Bootstrap stable docs (docs/OVERVIEW.md and docs/ARCHITECTURE.md) for a repo that does not have them yet. Use when starting plan on a new repo or when plan reports that stable docs are absent or thin.
disable-model-invocation: true
---

This skill exists because the plan skill reads `docs/ARCHITECTURE.md` and `docs/OVERVIEW.md` at the start of every plan session. When these docs are absent or contain only stubs, plan must guess context repeatedly. Running setup once eliminates this degradation for all future plan sessions.

## When to Use

- Before the first plan session on a new repo
- When the plan skill reports that stable docs are missing or thin
- When existing docs are partial, scattered, or inconsistent and need consolidation

## Six Phases

### Phase 1: Reconnaissance

Read everything available before saying a word:

- `docs/ARCHITECTURE.md` if it exists
- `docs/OVERVIEW.md` if it exists
- `docs/ROADMAP.md` if it exists (legacy — setup no longer creates or maintains this file; if found, its content is salvage material for phase 3, not something to recreate)
- Any files in `docs/design/`
- `README.md` and top-level config files (package.json, Cargo.toml, go.mod, pyproject.toml, etc.)
- Source tree structure (`ls` the top level, `ls src/` or equivalent)

Goal: arrive at the permission gate with a concrete summary of what exists and what is missing.

### Phase 2: Assessment and Permission Gate

Present findings to the user:

- What docs exist and what they contain (one sentence each)
- What is missing or thin
- What setup will create or consolidate

Then ask: **"Shall I proceed?"**

Do not begin writing docs or asking architecture questions until the user confirms. Do not proceed to Phase 3 (consolidation analysis) until the user confirms. If the user says no or asks to narrow scope, respect that.

### Phase 3: Consolidation (if partial docs exist)

If any partial docs exist, read them fully and extract any useful content before the guided conversation. Identify:

- Sections that are accurate and can be kept
- Sections that contradict observed code or are stale
- Gaps to fill through the guided conversation

If any sections contradict what was observed in reconnaissance, flag those contradictions in the Phase 2 findings summary before the permission gate fires (or note them before starting Phase 4 if discovered during Phase 3).

Do not create new docs alongside existing ones. Merge content into the final docs written in phase 5.

### Phase 4: Guided Conversation

Ask one question per round. Wait for the user's response before asking the next question. Do not front-load all questions.

**Round 1 — Purpose and intent:**
> "What problem does this project solve, and who uses it? What does success look like?"

Wait for response.

**Round 2 — Components and structure:**
> "Walk me through the main components or subsystems — what are they, and how do they connect?"

Wait for response.

**Round 3 — Constraints and non-goals:**
> "Are there significant constraints or known technical debt? Is there anything intentionally out of scope for this system's architecture — things plan should not treat as fair game?"

Wait for response.

Record user responses. You do not need to ask follow-up questions unless a response is ambiguous enough to produce incorrect docs.

### Phase 5: Write Docs

Write `docs/OVERVIEW.md` and `docs/ARCHITECTURE.md` using the content from reconnaissance and the guided conversation. Setup does not create a canonical schedule doc — the backlog is dead; PRs and the issue tracker carry status, not a repo file.

**`docs/OVERVIEW.md`** must be a single paragraph (3–5 sentences) covering: what the project does, who uses it, and what success looks like. This is the first file the plan skill reads — keep it concise and concrete.

**`docs/ARCHITECTURE.md`** must have these sections:

- **Purpose/Intent**: What the system does and why it exists. Who uses it and what success looks like.
- **Stack**: Languages, frameworks, runtime, key dependencies.
- **Component Map**: Main subsystems, what each does, how they connect. Can be prose or a simple table.
- **Invariants**: Constraints that must hold across changes — things that should never break.
- **Key Data Flows**: The two or three most important end-to-end flows through the system.
- **Non-Goals** (optional): What is explicitly out of scope for the system's architecture, drawn from Round 3. Prevents scope creep in plan. Include only when the conversation actually surfaced real constraints — omit rather than pad with generic filler.
- **Stable References**: Links or paths to other docs that planners should consult.

If partial content from existing docs was found in phase 3, merge it into the appropriate sections rather than duplicating it. If an existing `docs/ROADMAP.md` is found during reconnaissance, do not recreate or update it as a schedule — its "Not In Scope" content, if any, is exactly the material Round 3 gathers; fold it into `docs/ARCHITECTURE.md`'s Non-Goals section instead.

### Phase 6: Plan Hook

After writing the docs, tell the user:

> "Stable docs are in place (`docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`). You can now run `/workflow:plan` to start a plan session — it will read these docs automatically."

## Rules

- Do not write docs before the permission gate. Phase 2 must complete before phase 4 starts.
- Ask one question per round. Do not bundle all three rounds into one message.
- If partial docs exist, consolidate — do not create alongside. One authoritative source per doc.
- Prefer the user's words when writing stable docs. Accurate paraphrase is fine; do not invent technical detail that was not provided.
- If the user's answers are thin, write what you know and leave clear placeholders (`<!-- TODO: add X -->`) rather than padding with generic filler.
- Do not ask more than three rounds of questions unless a response is genuinely ambiguous. Three rounds is enough to produce usable stable docs.
- If a PROVENANCE.md already exists in a plan directory for the current session, append the guided conversation turns to it. If running standalone (no existing PROVENANCE.md), no provenance record is required.
