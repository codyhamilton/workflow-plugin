# Event recording gaps: Codex apply_patch writes and Codex plugin upgrades

## Intent

User request, verbatim:

> Check daily and make sure each harness is properly reporting events and designs and briefs and executions. If not backfill the artifacts where possible and investigate the root cause, create a design to fix and escalate for approval to fix.

The daily check already exists. This design covers only the fix for the two recording defects it found. Backfill is out of scope (Non-goals).

## Problem

Workflow Event Watch found two defects that stop Codex work reaching the ledger. Claude, Cursor and OpenCode are not affected.

1. **Codex `apply_patch` writes never become artifact versions.** The `writePaths` patch branch in `tools/workflow/internal/facts/facts.go` reads patch text only from `tool_input.patch`, then `tool_input.input` (or from a raw `tool_input` string that is not JSON). Codex sends `apply_patch` as `tool_input: {"command": "*** Begin Patch…"}`. All 1308 Codex `apply_patch` PostToolUse facts in the ledger carry only `command`. So the drain records the `hook_event` but no `artifact_version`. Codex worktree artifact versions total 0. Downstream, `artifact_feedback` gets a 404 from serve and reports `not delivered` (`tools/workflow/internal/mcp/feedback.go`). That message is correct for a missing version, so it is a symptom and not a defect. `tools/quality/artifact_submit.py` `write_paths` has the same gap; `facts.go` says it is a port of that function. The shared fixture `tools/hooklog/tests/fixtures/artifact_writes.json` covers Codex `apply_patch` as a raw string and as `{"input": …}`. It has no `{"command": …}` case, so the tests pass against a shape Codex does not send.
2. **A Codex plugin upgrade cuts off hooks in live sessions.** Codex installs plugins at `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` and deletes the old version directory when it upgrades. The 2.9.1 → 2.9.2 upgrade (`ebe8a10`) removed 2.9.1 at about 13:01 AEST on 2026-10-05. Only `2.9.2` is left in `~/.codex/plugins/cache/workflow-plugin/workflow/`. Sessions that were already running keep the old `${PLUGIN_ROOT}` in the `hooks/codex.json` commands they loaded, so every later hook call runs `bash <deleted path>/tools/hooklog/spool.sh` and nothing is spooled. Claude Code keeps old versions (`2.5.0` through `2.9.2` are still in `~/.claude/plugins/cache/workflow-plugin/workflow/`), so Claude sessions are unaffected. Codex also auto-upgrades configured git marketplaces when a session starts (openai/codex#17425). That means no upgrade step exists that this repo runs and could hook into. The same failure is reported upstream as openai/codex#31383. openai/codex#38703 (merged 2026-08-15) rebuilds hook runtimes for loaded sessions after an upgrade. The installed CLI is `codex-cli 0.160.0`. Whether it includes #38703, and whether #38703 covers this case, is not verified (Open Questions).

Both defects leave the daily check reporting gaps it cannot close. The first drops every Codex design, brief and report write. The second drops all Codex events for sessions that span an upgrade.

## Solution Shape

After this change, a Codex `apply_patch` whose patch text is in `tool_input.command` produces the same `artifact_version` facts as Claude `Write` or Cursor `afterFileEdit`. The shared fixture set contains the shape Codex actually sends. A binary with the fix is built, and the outcome record says how to deploy it to the local serve on 8770. A Codex session keeps spooling events after its plugin version directory is removed by an upgrade, with the hook still exiting 0. Hook and queue formats do not change, Claude's hooks do not change, and nothing is restarted by the build.

### Domain: Write-path extraction (`tools/workflow/internal/facts`, `tools/quality/artifact_submit.py`)

- Owns: the derivation of write paths from one hook payload. Its consumers are `facts.Build` (the standalone drain, and the drain hosted inside `workflow serve`, `tools/workflow/internal/serve/host.go`), `facts.WritePaths` (the MCP shim's queue-file match in `feedback.go`), and the legacy Python `write_paths`.
- Contract:
  - Applies only when the normalised tool name is `apply_patch` or `applypatch` and the event is the harness's post-tool event. The current gates in `writePaths` (event map, `source != "bus"`, `writeTools`) stay as they are.
  - Patch text is the first non-empty **string** among `tool_input.patch`, `tool_input.input` and `tool_input.command`. When `tool_input` is a non-JSON string, that string is the patch text, as today. A non-string `command` (array or object) is ignored.
  - Paths come from every `*** Add File: `, `*** Update File: ` and `*** Move to: ` line in that text (`patchRE`, unchanged). Relative paths join to `cwd`, or else `workspace_roots[0]`, as today.
  - Tools other than the patch tools never read `command`, so a shell tool's `command` text is never treated as a patch.
  - For the same payload, `facts.WritePaths` and Python `write_paths` return the same paths that `facts.Build` uses. Python returns them relative, Go returns them cleaned and absolute, as today.
  - The emitted `artifact_version` fact is unchanged: `source: "worktree"`, the current file content, and `keys.Kind` gating.
- Fixture contract: `artifact_writes.json` gains one entry with `"harness": "codex"` and payload `{"hook_event_name":"PostToolUse","tool_name":"apply_patch","session_id":<fixture id>,"tool_input":{"command":"*** Begin Patch\n*** Update File: docs/plans/example/DESIGN.md\n@@\n-before\n+after\n*** End Patch"}}`. That is the observed Codex shape. Every consumer that asserts the fixture count (11 today: `facts_test.go`, `capture_test.go`, `drain_test.go`, `test_spool_queue.py`, `test_write_surfaces.py`) moves to the new count.
- Non-goals: changing `feedback.go`'s `not delivered` wording or its 404 handling; new tool names; `*** Delete File:` tracking; patch-body content checks.

### Domain: Codex hook liveness across plugin upgrade (`hooks/codex.json` and what it calls)

- Owns: the Codex hook command strings, any copy of the hook entry point the plugin keeps outside the versioned cache, and the Codex sections of `tools/hooklog/README.md` and `docs/design/05-distribution.md`. It does not own Codex's cache manager (`~/.codex/plugins/cache`), which is upstream code.
- Contract (holds whichever approach is chosen):
  - A Codex hook command loaded from plugin version N is invoked after `…/workflow/N/` has been removed (and N+1 installed). It still writes exactly one queue file for the event under `${WORKFLOW_QUEUE:-~/.local/share/workflow/queue}`, with envelope `harness: "codex"` (design 2 queue format, unchanged), and exits 0 within the 3 s hook timeout.
  - If every location the command can resolve is missing, the command writes nothing and still exits 0. A hook never fails the agent; `spool.sh` already guarantees this, and any wrapper must keep it.
  - The fix applies to sessions started on a plugin version that ships it. Sessions already running on 2.9.2 keep the command strings they loaded and do not benefit.
  - `hooks/hooks.json` (Claude), `hooks/cursor.json` and the OpenCode plugin are untouched.
- Non-goals: patching Codex itself; disabling Codex marketplace auto-upgrade for the user; making live MCP shim processes survive an upgrade (they run the cached binary from `~/.cache/workflow/<VERSION>/`, not the plugin directory).

## Architectural Implications

- `docs/design/02-edge-capture.md` Write surfaces lists Codex as "`PostToolUse` on apply_patch and write tools" without the field. Close-out adds a note that the Codex patch text is in `tool_input.command`.
- `docs/design/05-distribution.md` assumes a plugin directory lives as long as the sessions that loaded it. That is true for Claude and Cursor and false for Codex. Phase 2 corrects that doc.
- `facts.Build` runs in two places: the drain hosted inside `workflow serve`, and standalone drains that hooks start through `bin/workflow`. Standalone drains exec the cached binary fresh each time, so they pick up a replaced binary immediately. The hosted drain needs a serve restart. MCP shim processes in live Claude, Cursor and Codex sessions keep the old `WritePaths` until their own sessions restart. This design does not restart them, so `artifact_feedback`'s queue-file match in those sessions stays on the old logic for a while. Serve-side versions are recorded correctly anyway.
- `bin/workflow` resolves `~/.cache/workflow/<bin/VERSION>/workflow-linux-amd64`, and `bin/VERSION` is `0.1.0`. A rebuilt binary with an unchanged `VERSION` takes effect only if it replaces that cache file. `tools/release/build.sh` also rewrites the tracked `bin/SHA256SUMS`. Publishing a release is maintainer-gated (design 5 Release).
- Concurrency: a headless Claude session is building plan 10 phase 1 (`tools/workflow/internal/serve`, `store`) on master right now and will push. A binary built from master after that lands includes plan 10's serve changes, so restarting serve deploys both. The surfaces do not overlap (`facts` versus `serve`/`store`).
- Recorded history is not repaired by the fix. The 1308 existing Codex `apply_patch` `hook_event` facts stay without versions. Re-draining archived queue files would record **current** worktree content, not the content at the time (Non-goals).

## Decisions

None taken with Cody yet. The checkpoint is held: see PROVENANCE.md and Open Questions. The ledger below lists the positions the design proceeds on unless Cody overturns them at the checkpoint.

## Assumption Ledger

Interactive posture with the checkpoint held. These entries are written down so Cody can confirm or overturn each one at sign-off. They do not wave the design through.

### Assumption 1

- Question: the quality service on 8765 is down. Does that affect this design?
- Answer chosen: it does not block either phase. Neither fix depends on 8765. The invoker reports it down. A probe at 01:31 AEST on 2026-10-06 found `workflow-quality.service` listed active, but `GET /health` returned 405 and `GET /v1/health` 404, so it is not usable as a quality API. As a result, `artifact_feedback` was not called on this design. Backfilling silver-chronicle plans after 21 (deliberate `post_design` / `post_brief` / executions) needs quality up and is left out.
- Rationale: the defects live in drain-side extraction and in hook resolution. Both are proven against serve on 8770 and the queue.
- If wrong: if backfill has to ride with this fix, a third phase is added for a lab backfill tool, and it depends on quality being restored. The phase count changes before sign-off.

### Assumption 2

- Question: should `tools/quality/artifact_submit.py` be fixed, given design 5 dropped its hook registration?
- Answer chosen: yes, for parity, in Phase 1.
- Rationale: `facts.go` is documented as a port of it. `tools/quality/quality.py` and `tools/release/phase5_outcome.py` still reference it. The change is one more key in the same lookup.
- If wrong: drop that surface from Phase 1. Nothing else changes.

### Assumption 3

- Question: does Phase 1 bump `bin/VERSION` or publish a release?
- Answer chosen: no. The phase proves the fix in tests and produces a linux-amd64 binary. The deploy procedure is to put that binary at the cache path `bin/workflow` resolves for `0.1.0` and restart `workflow-serve.service`. That is an operator step taken after Cody approves. `bin/SHA256SUMS` and `bin/VERSION` are not changed by this phase.
- Rationale: the posture rules out building or restarting from this design. Releases are maintainer-gated.
- If wrong: Phase 1 adds a version bump, and the release follows the design 5 path.

### Assumption 4

- Question: is Phase 2 Known or Open?
- Answer chosen: Open. The outcome is provable. The approach is not settled, because there is no "upgrade time" this repo controls (startup auto-upgrade, openai/codex#17425), and whether the upstream refresh (#38703) is present in 0.160.0 and covers this case is unverified.
- Rationale: the candidates differ in where state lives and in how much they touch Codex's own cache. See Phase 2.
- If wrong: Cody picks one candidate and the flag becomes Known.

### Assumption 5

- Question: does Phase 2 cover Claude, Cursor or OpenCode?
- Answer chosen: Codex only.
- Rationale: Claude keeps old version directories (observed). Cursor's plugin is a local checkout (`~/.cursor/plugins/local/workflow-plugin`). OpenCode's hook package is not a versioned cache.
- If wrong: the same contract is applied per harness in a follow-on design.

## Open Questions

For Cody at the checkpoint:

1. Sign-off on the two phases and their order. Phase 1 is independent and can ship alone.
2. Phase 2 flag: Open (built as divergent candidates against the fixed outcome) or Known with a named candidate? The design's lean is candidate (a) below if Known is preferred.
3. Phase 1 deploy: is replacing `~/.cache/workflow/0.1.0/workflow-linux-amd64` and restarting `workflow-serve.service` the deploy you want (Assumption 3)? Should the restart wait until plan 10 phase 1 has landed, since the binary will carry both?
4. Phase 2's live check needs a plugin version bump published to the marketplace, which is a push. Approve that as part of Phase 2, or keep Phase 2 closing on the simulated test and do the live check at the next release?
5. Backfill (out of scope here): once quality is up, do you want a separate lab design for re-recording silver-chronicle plans after 21 and the dropped Codex writes, accepting that re-drained Codex writes carry current content rather than historical content?

## Phases

Two phases, fixed at sign-off. Each has more than one unit, so `refine` runs before each is built. Phase 1 does not depend on Phase 2 and can close on its own.

### Phase 1 — Codex apply_patch writes become artifact versions

- Outcome:
  - From `tools/workflow`, `go test ./internal/facts ./cmd/workflow` passes with the new Codex `{"command": …}` fixture included. `Build` on that fixture emits a `hook_event` and one `artifact_version` (`harness: "codex"`, `source: "worktree"`, `path: "docs/plans/example/DESIGN.md"`). `WritePaths` returns that file's absolute path. A non-patch tool payload (for example a Codex shell tool) whose `tool_input.command` contains `*** Update File:` lines emits no `artifact_version`.
  - `python3 -m unittest tools/hooklog/tests/test_write_surfaces.py` replays the new fixture through `hooks/codex.json` into a temp serve and observes the `artifact_version` for it. All fixture-count assertions match the new count.
  - `tools/quality/tests/test_artifact_submit.py` includes a case where `write_paths` on the same payload returns `docs/plans/example/DESIGN.md`.
  - A `workflow-linux-amd64` built from the phase's closing commit exists outside the tracked tree, and its `--version` names that commit. `bin/VERSION` and `bin/SHA256SUMS` are unchanged.
  - The phase's record in `IMPLEMENTATION.md` contains the operator deploy procedure: place the binary at `~/.cache/workflow/0.1.0/workflow-linux-amd64` (moving the old one aside), run `systemctl --user restart workflow-serve.service`, confirm `GET http://127.0.0.1:8770/v1/health` returns `ok: true`, then confirm that the next Codex `apply_patch` to a plan file produces an `artifact_version` with `harness: "codex"` and that `artifact_feedback` on that path no longer returns 404 `not delivered`. The procedure states that no Claude, Cursor, Codex or seat process is restarted, and that live MCP shims keep the old match until their sessions restart.
  - The build does not run that procedure.
- Surfaces: `tools/workflow/internal/facts/facts.go` (`writePaths`), `tools/workflow/internal/facts/facts_test.go`, `tools/workflow/cmd/workflow/capture_test.go`, `tools/workflow/cmd/workflow/drain_test.go`, `tools/hooklog/tests/fixtures/artifact_writes.json`, `tools/hooklog/tests/test_write_surfaces.py` (including `fixture_path`), `tools/hooklog/tests/test_spool_queue.py`, `tools/quality/artifact_submit.py` (`write_paths`), `tools/quality/tests/test_artifact_submit.py`.
- Approach: known
- Depends on: nothing

### Phase 2 — Codex hooks survive a plugin upgrade

- Outcome:
  - A test under `tools/hooklog/tests/` runs every `hooks/codex.json` command with the env Codex provides (`PLUGIN_ROOT`, `PLUGIN_DATA`). It first runs `SessionStart` from a plugin copy, then deletes that copy, then sends a `PostToolUse` payload through the same command string. Exactly one queue file appears with envelope `harness: "codex"`, and the command exits 0 in under 3 s.
  - The same test, with every resolvable location removed, shows the command exits 0 and writes nothing.
  - `hooks/hooks.json` and `hooks/cursor.json` are byte-identical to before.
  - `tools/hooklog/README.md` (Codex section) and `docs/design/05-distribution.md` state what happens to live Codex sessions across a plugin upgrade, and which plugin version first carries the fix.
  - Live check, run when the fixed plugin version is published (Open Question 4): a Codex session started on that version, followed by `codex plugin marketplace upgrade` (or the startup auto-upgrade) to a later version, keeps producing `hook_event` facts with `harness: "codex"` on 8770 for its next tool calls.
- Candidates (Open; the outcome above is the yardstick):
  - (a) Fallback outside the versioned cache: `SessionStart` copies the hook entry point (`spool.sh`) into `${PLUGIN_DATA}`. Each `hooks/codex.json` command tries `${PLUGIN_ROOT}` first, then that copy, then exits 0. This is the lean. It must first be verified that `PLUGIN_DATA` is not versioned. Kicking the drain from the copy needs a resolvable binary, but serve's hosted drain picks up the queue regardless.
  - (b) Recreate the old directory: `SessionStart` in N+1 recreates missing previously seen version directories as symlinks to a retained copy. Weaker: it writes into Codex's cache, leaves a gap until the next session starts, and Codex may remove those links on its next upgrade.
  - (c) Upstream: confirm or obtain a Codex CLI that carries openai/codex#38703, and document it as the requirement. No plugin change if it proves the outcome.
  - (d) Operator upgrade script that snapshots N before `codex plugin marketplace upgrade`. Rejected as the sole fix because startup auto-upgrade bypasses it.
- Surfaces: `hooks/codex.json`, `tools/hooklog/spool.sh` (only if the copy needs to know its origin), `.codex-plugin/plugin.json` (version bump at publish), `tools/hooklog/README.md`, `docs/design/05-distribution.md`, a new test in `tools/hooklog/tests/`.
- Approach: open
- Depends on: nothing. It is ordered after Phase 1 because Phase 1 restores the larger loss.

## Non-goals

- Backfilling artifacts. This covers the 1308 Codex `apply_patch` events already recorded without versions, and the silver-chronicle plans after 21 (`post_design` / `post_brief` / executions). Both need quality up and a deliberate re-record. Re-draining archived Codex queue files would record current content, not historical content. A later lab design can take this on once serve and quality work is done.
- Building, deploying, pushing or restarting anything from this design. The serve restart is an operator step after Cody approves.
- Restarting Claude, Cursor, Codex sessions or seats.
- Changing `feedback.go`, the queue format, the fact schema, or the daily check routine.
- Patching Codex or turning off its marketplace auto-upgrade.

## Provenance Notes

- Ground on 2026-10-06 re-read `writePaths` at `95f41f7` (`facts.go` lines 247–335; patch branch at 308–316), Python `write_paths` (`artifact_submit.py` 136–164), `feedback.go` 253–257, `artifact_writes.json` (11 entries; the Codex ones are a raw string and `{"input"}`), `hooks/codex.json`, `.codex-plugin/plugin.json` (2.9.2), `bin/workflow`, `tools/release/build.sh`, `serve/host.go` (the hosted drain), and the `workflow-serve.service` unit (ExecStart `~/.cursor/plugins/local/workflow-plugin/bin/workflow serve`, running `~/.cache/workflow/0.1.0/workflow-linux-amd64`). The 1308/1308 count and Codex version total of 0 come from Workflow Event Watch's ledger query and were not re-run here.
- Reading `command` only as a string, and only for patch tools, keeps the existing commit detector (`commandText`) and shell tools from being misread as patches. Arrays were not observed for Codex `apply_patch`.
- Rejected for Phase 1: normalising Codex payloads in `spool.sh`. The spool is deliberately parse-free (design 2), and the fix belongs where every other write shape is decoded.
- Rejected for Phase 2: pinning the Codex plugin to a fixed version. It stops upgrades without fixing liveness, and the plugin still ships through the marketplace.
- No clean-context adversarial pass was available in this run (no subagent dispatch). Its absence is reported, and the pass should run before or at sign-off.
