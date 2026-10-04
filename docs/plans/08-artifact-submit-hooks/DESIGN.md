---
design_id: 172
---

# Artifact submit hooks

> **Superseded** by [docs/design/system-architecture.md](../../design/system-architecture.md) and
> [docs/design/01-event-model-and-ingest.md](../../design/01-event-model-and-ingest.md). Hooks no
> longer post; the drain captures artifact versions. Kept for history.

## Intent

User request, verbatim:

> Cody wants a design, not a build yet. Design hook checks on design-file and brief-file writes. On write, check that the design or brief was submitted to the event sink. If it was not submitted, call the APIs automatically.

## Problem

The workflow-quality service (`tools/quality`, MCP at `127.0.0.1:8765`, REST under `/v1`) is the durable event sink for designs and briefs. The `design` and `refine` skills require agents to call `post_design` / `post_brief` and write returned ids into frontmatter. In practice, agents skip the MCP step, post only after the file exists, or type ids locally without a ledger row. Hooklog already ingests the conversation stream and can bind a successful `post_*` tool call to an artifact id (`conversation_binds` in `tools/quality/hookevents.py`), but nothing today closes the loop when a plan file lands on disk without a matching post.

A partial implementation already exists: `quality.py hook` runs on Claude `PostToolUse`, classifies `docs/plans/*/DESIGN.md` and `docs/plans/*/briefs/*.md`, and scores into the **local** SQLite store via `log_row` — not into the central service lifecycle (`lifecycle.put_artifact`). It emits `additionalContext` with an informational rating summary. That path does not satisfy “submitted to the event sink” and can diverge from the ledger the skills and `QUALITY-SERVICE.md` describe.

Writes to plan artifacts are observable on every harness that already records agent file edits, but only through different hook names. Missing posts are invisible in `GET /v1/sessions/{id}` and plan/session joins until someone notices manually.

## Solution Shape

After this change is built, every supported harness runs an **artifact-submit** hook immediately after hooklog on the same file-write surfaces. The hook reads the written file, decides whether the current content is already **submitted** on the workflow-quality service for this conversation, and if not, calls the existing `POST /v1/designs` or `POST /v1/briefs` (same contract as MCP `post_design` / `post_brief`) with correlation context (`conversation_id`, `harness`, `repo_path`, `path`, `text`). The editor write always succeeds; the hook never blocks, denies, or rewrites tool results. Failures are advisory: Claude `PostToolUse` may receive `additionalContext`; all harnesses record a structured outcome row that hooklog posts to `/v1/hook-events` so misses remain visible in session and plan views. The hook does not mutate plan files (no frontmatter injection); ids returned from a successful auto-post are surfaced for the agent to adopt. Execution lifecycle (`start_execution`, `complete_execution`) stays out of scope.

### Domain: Plan artifact paths

- Owns: which filesystem paths count as a design file or brief file. Owned by the shared submit helper (`tools/quality/`, new module beside `lifecycle.py`).
- Contract:
  - **Design file:** repo-relative path matching `docs/plans/<plan>/DESIGN.md` (same rule as `quality.kind_of` today).
  - **Brief file:** repo-relative path matching `docs/plans/<plan>/briefs/*.md`.
  - **Content hash:** SHA-256 of the file body **after** stripping identity-only frontmatter (`design_id`, `brief_id`), truncated to 16 hex chars — same rule as `lifecycle.put_artifact` / `quality.score_content`.
  - **Repo root:** `git rev-parse --show-toplevel` from the file’s directory, with the same non-git fallback as `quality.repo_root`.
  - **Project / plan:** `quality.project_name(repo)` and the `<plan>` segment from the path.
  - Paths outside these patterns are ignored; the hook exits 0 with no side effects.
- Non-goals: `PLAN.md` legacy names (skills already read either); artifacts outside `docs/plans/`; inferring submission from git commit messages or `Workflow-Plan:` markers.

### Domain: Submitted predicate

- Owns: the boolean “this write is already on the ledger for this conversation.” Owned by the shared submit helper; the service DB is authoritative.
- Contract:
  - **Submitted** = true iff the quality ledger has an artifact for `(kind, project, path)` whose **latest stored body hash** equals the file’s content hash **and** at least one of:
    1. A `scores` row for that artifact with `session_id` equal to the hook’s `conversation_id`, or
    2. A `conversation_binds` row linking that `conversation_id` to the artifact id, or
    3. An `events` row with `event` ∈ `{posted_design, patched_design, posted_brief, patched_brief}` for that artifact id and the same `conversation_id`.
  - A frontmatter `design_id` / `brief_id` alone does **not** imply submitted; the predicate ignores frontmatter ids unless backed by the rows above.
  - A prior post in **another** conversation for the same path and hash counts as submitted for ledger completeness but does **not** bind this conversation; the hook still calls `post_*` with this `conversation_id` so session/plan joins stay correct (service upsert: identical content is not re-scored; context and binds still update).
  - **Check order:** resolve path → read file → hash → query the same service at `WORKFLOW_QUALITY_URL` used by the auto-post client (`GET /v1/sessions/{conversation_id}` plus artifact body/hash comparison, using the same default URL, authentication, and timeout as the post; the predicate above is normative). Co-location does not change the store selection; do not use `WORKFLOW_QUALITY_DIR` as a separate check store or fallback.
- Non-goals: treating `rate_artifact` MCP calls as submission; treating local-only `quality.py score --no-log` or the current `cmd_hook` local `log_row` as submission.

### Domain: Auto-post client

- Owns: calling the existing lifecycle API when the predicate is false. Owned by the shared submit helper.
- Contract:
  - **Design:** `POST /v1/designs` with `{ text, project, plan, path, repo_path, conversation_id, harness, workflow_version, … }` — full file text including frontmatter as on disk.
  - **Brief:** `POST /v1/briefs` with the same fields plus `design_id` when present in frontmatter or resolvable from the plan’s `DESIGN.md` frontmatter.
  - **Transport:** HTTP to `WORKFLOW_QUALITY_URL` (default `http://127.0.0.1:8765`), `Authorization: Bearer` when `WORKFLOW_QUALITY_TOKEN` is set, timeout `WORKFLOW_QUALITY_TIMEOUT` (default 2s). No second sink, no parallel MCP client required in the hook process.
  - **Success:** response `id` and `frontmatter` block treated as advisory output only; the hook does not write them into the file.
  - **Failure** (timeout, connection refused, 4xx/5xx): no exception propagated to the harness; return a structured `{ ok: false, reason, path, kind }` to the hook driver.
  - **Idempotence:** repeated hook invocations for the same hash rely on service upsert (`scored: false`, identical content) and remain exit 0.
- Non-goals: `patch_*` from the hook (agent-driven patches stay MCP); `define_checks`, `rescore`, or execution endpoints.

### Domain: Harness file-write surfaces

- Owns: which hook registrations invoke the submit helper after hooklog. Owned by plugin manifests (`hooks/hooks.json`, `hooks/cursor.json`, `packages/opencode-workflow-hooks`, `tools/hooklog/codex-hooks.example.json`).
- Contract:
  - **Claude Code:** `PostToolUse` when normalized `tool_name` is a file-writing tool (`Write`, `Edit`, `MultiEdit`, or the host’s equivalent) and `tool_input` resolves to a plan artifact path. **`FileChanged` is out of scope** — it is a filesystem watcher, not an agent-attributed write surface, and would double-fire with `PostToolUse`.
  - **Cursor:** `postToolUse` under the same tool-name rule (advisory `additionalContext` supported). **`afterFileEdit`** runs the same ensure logic for paths present in the payload (`file_path`) so edits that bypass tool metadata still submit; response body remains `{}` on that event (hooklog policy: no injection on that channel today). **`afterTabFileEdit` is out of scope** — Tab composer, not workflow plan authoring.
  - **OpenCode:** `tool.execute.after` when the tool is a file write/edit and args resolve to a plan artifact path. The `file.edited` bus alone is **not** a separate registration (no dedicated file-write hook in the catalog); optional dedupe if both fire is implementation detail.
  - **Codex:** `PostToolUse` with the same tool-name rule as Claude. No additional file-write hook exists in the Codex catalog; none is invented.
  - **Registration shape:** append a second command after the existing `hooklog.py record` line, same timeout budget (5s), e.g. `python3 …/tools/quality/artifact_submit.py hook --harness <harness>`. stdin is the raw hook JSON; harness-specific response printing stays in `artifact_submit.py` (mirror `hooklog.py` Cursor permissive responses when the submit hook shares the `before*` events — submit hook should only be registered on **post-write** events listed above).
  - **OpenCode** invokes the same Python entrypoint from `tool.execute.after` (spawn, stdin payload) without changing tool outputs; errors swallowed like hooklog.
- Non-goals: **OpenCode** `file.edited`-only wiring; **Cursor Cloud** events the host omits (documented gaps stay gaps); new hook names on any harness.

### Domain: Advisory visibility (hook-failure surface)

- Owns: how a miss or auto-post error is visible without blocking the write. Owned by the submit helper plus hooklog ingest.
- Contract:
  - Hook process **always exits 0** for the harness (same invariant as `hooklog`).
  - **Claude `PostToolUse`:** optional `hookSpecificOutput.additionalContext` summarizing success (`posted design_id=…`) or failure (`workflow-quality unreachable; posting still owed for <path>`). Replaces the current local-score `additionalContext` from `quality.py hook` for plan paths.
  - **Cursor `postToolUse`:** same `additionalContext` when the platform accepts it on that event.
  - **All harnesses:** emit one normalised hooklog row `{ kind: tool_call, tool_name: artifact_submit, ok: <bool>, input: {path, kind}, output: <service response or error>, session_id, harness }` posted to `/v1/hook-events` so `GET /v1/sessions/{id}` and plan session joins show the attempt even when the parent UI shows nothing.
  - **`postToolUseFailure` / `PostToolUseFailure`:** not used for submit misses (the write already succeeded); those events remain hooklog-only.
- Non-goals: steering, hard asserts, or progressive Jev gates; rewriting `postToolUse` tool results.

## Architectural Implications

- **`docs/ARCHITECTURE.md` and `docs/OVERVIEW.md`** do not yet describe the quality service or hook backstop posting. A later doc pass (build phase or close-out) should add one paragraph under the artifact seam: skills own deliberate `post_*`; hooks backstop ledger submission on plan file writes.
- **`docs/lab/QUALITY-SERVICE.md`** remains the API authority; add a short “Hook backstop” subsection when built, pointing at this plan.
- **`quality.py cmd_hook`:** superseded for plan paths by `artifact_submit.py`; local-only scoring on write should be removed or delegated to avoid two divergent ledgers. Pivot named here; stable docs do not yet reflect it.
- **Land path for the eventual build:** local merge to `master` and push on Cody’s machine — **no pull request** for this repo. This design does not perform that merge.
- **Cloud agents** cannot reach `127.0.0.1:8765`; auto-post fails open with visible “posting owed” in the agent report. Spool/backfill does not substitute for submission (no `design_id` invented offline).

## Decisions

- **Service ledger is the sink.** Submission means `lifecycle.put_artifact` via REST/MCP, not `quality.py` local `log_row`.
- **Non-blocking everywhere.** Matches hooklog invariants and the invoker’s constraints.
- **No file mutation in the hook.** Frontmatter remains the skill/agent responsibility; the hook only fills ledger gaps.
- **Harness coverage follows existing file-write hooks only.** Claude/Codex `PostToolUse`, Cursor `postToolUse` + `afterFileEdit`, OpenCode `tool.execute.after`. Tab, filesystem watcher, and bus-only paths excluded per ledger above.
- **Conversation binding matters.** Re-post on same hash in a new session is intentional so analytics joins work.
- **Execution lifecycle excluded** per invoker scope.

## Assumption Ledger

### Assumption 1

- Question: Should `FileChanged` on Claude register the submit hook?
- Answer chosen: No — use `PostToolUse` only for Claude file writes.
- Rationale: `FileChanged` is not agent-attributed and duplicates `PostToolUse` for agent writes.
- If wrong: Add `FileChanged` with dedupe by path+hash within a short window.

### Assumption 2

- Question: Should the hook write returned `design_id` / `brief_id` into the file?
- Answer chosen: No — advisory `additionalContext` and hook-events only.
- Rationale: Avoid racing the agent’s editor and keep a single writer for frontmatter (skills).
- If wrong: Add an opt-in env `WORKFLOW_ARTIFACT_SUBMIT_WRITE_FM=1` for local-only harnesses.

### Assumption 3

- Question: How does the hook check “submitted” when the service is remote from the hook process?
- Answer chosen: Use `GET /v1/sessions/{conversation_id}` at the same `WORKFLOW_QUALITY_URL` used for posting and compare artifact paths and body hashes from the response, whether the service is co-located or remote. Use the post client's default URL, authentication, and timeout; do not check a separate database via `WORKFLOW_QUALITY_DIR`.
- Rationale: The check and post must use the same authoritative store; a co-located database can differ from the service selected by `WORKFLOW_QUALITY_URL`.
- If wrong: Add `GET /v1/artifacts?project=&path=` in a small follow-up.

### Assumption 4

- Question: Replace or supplement `quality.py hook`?
- Answer chosen: Replace for plan artifact paths; retain `score` CLI for manual use.
- Rationale: One behaviour per write; local ledger duplication confuses “submitted.”
- If wrong: Gate local score behind `WORKFLOW_QUALITY_LOCAL_SCORE=1`.

### Assumption 5

- Question: OpenCode — register on `file.edited` bus?
- Answer chosen: No — only `tool.execute.after` for write tools.
- Rationale: User directive: do not invent a hook the harness does not already treat as file-write; bus `file.edited` is not in the Hooks callback list as a file-write hook.
- If wrong: Add bus handler with tool-level dedupe.

## Open Questions

- Whether Cursor will eventually allow `additionalContext` on `afterFileEdit`; until then, `postToolUse` carries parent-visible misses for Cursor agent writes.
- Remote quality service (non-loopback): predicate over HTTP may need a dedicated lightweight GET; deferred until a host actually runs harness and service on different machines.

## Phases

### Phase 1 — Shared submit helper and predicate

- Outcome: `python3 -m unittest discover -s tools/quality/tests -p 'test_artifact_submit*.py'` exits 0; tests start an in-process `server.py` handler and prove that `is_submitted` and `ensure_posted` match the contracts above for design and brief fixtures (including frontmatter strip, conversation bind, and idempotent re-post).
- Surfaces: `tools/quality/artifact_submit.py` (new), `tools/quality/tests/test_artifact_submit.py`, shared helpers reused from `quality.py` / `lifecycle.py` (`kind_of`, `split_frontmatter`, `project_name`, `repo_root`).
- Approach: known
- Depends on: nothing

### Phase 2 — Harness wiring

- Outcome: For each harness in Domain: Harness file-write surfaces, a recorded hook payload fixture in tests produces exactly one `POST /v1/designs` or `POST /v1/briefs` when the predicate is false and zero posts when true; `hooks/hooks.json`, `hooks/cursor.json`, `tools/hooklog/codex-hooks.example.json`, and `packages/opencode-workflow-hooks/src/index.ts` register the submit command on the listed events only; `quality.py cmd_hook` no longer runs for plan paths.
- Surfaces: `hooks/hooks.json`, `hooks/cursor.json`, `tools/hooklog/codex-hooks.example.json`, `packages/opencode-workflow-hooks/src/index.ts`, `tools/quality/quality.py` (remove or redirect plan-path `hook` behaviour), `tools/hooklog/tests/` (fixture replay).
- Approach: known
- Depends on: Phase 1

### Phase 3 — Operator docs and skill seam

- Outcome: `docs/lab/QUALITY-SERVICE.md` documents hook backstop behaviour; `skills/design/SKILL.md` and `skills/refine/SKILL.md` each state that hooks auto-post to the service but agents must still post (or patch) deliberately and write frontmatter ids; a human with `workflow-quality` running locally can write a plan `DESIGN.md`, see `posted_design` in `GET /v1/sessions/{conversation_id}` without manually calling MCP, and see `additionalContext` on Claude when the service is stopped.
- Surfaces: `docs/lab/QUALITY-SERVICE.md`, `skills/design/SKILL.md`, `skills/refine/SKILL.md`, optional one-line pointer in `tools/hooklog/README.md`.
- Approach: known
- Depends on: Phase 2

## Provenance Notes

Grounding: `quality.kind_of` and `lifecycle.put_artifact` define paths and hashing; `hookevents.bind_target` defines how MCP posts bind conversations; shipped manifests show hooklog-only registrations on write surfaces today; `quality.py cmd_hook` implements local score + `additionalContext` but not service post — the main pivot from changelog narrative (2.8.0 service) to write-path behaviour.

Rejected: blocking writes pending post; a second analytics sink; hook-managed `start_execution`; inventing Codex `FileChanged` or OpenCode-only `file.edited` wiring; PR-based land (repo uses local merge).

Adversarial pass (applied): (1) Narrowed Claude to `PostToolUse` to avoid watcher double-fire. (2) Split Cursor advisory (`postToolUse`) from detection (`afterFileEdit`) so visibility matches platform limits. (3) Made “submitted” depend on ledger rows, not frontmatter. (4) Required conversation re-post on same hash so joins work. (5) Named supersession of local `cmd_hook` to prevent dual ledgers. (6) Kept execution endpoints explicitly out of scope to match invoker.
