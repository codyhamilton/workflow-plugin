---
brief_id: 217
design_id: 209
---

# Brief: 2-02 — Fact building and the client config

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Unit 2-03's drain calls the
`facts` and `clientconfig` APIs built here for every batch; 2-04's hosted drain reuses them; phase 4's
shim reads the same config.
Owned paths: `tools/workflow/internal/facts/`, `tools/workflow/internal/clientconfig/`,
`tools/hooklog/tests/fixtures/commit_calls.json` (new),
`docs/plans/09-workflow-binary/reports/2-02-facts-clientconfig.md`. Touch nothing else; in
particular not `go.mod` (standard library only, plus this module's own packages).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing beyond phase 1 (committed).
Runs alongside: 2-01 (disjoint paths).
Budget: 9 files to read, about 1,100 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 2 (lines 163-178).
2. `docs/design/02-edge-capture.md` — Drain: **Building facts**, **Commit facts**, **Scrub
   outcome**, **Delivery** (fact IDs, worst-fact outcome), **Scrub** (lines 66-111); Config (lines
   121-139); Write surfaces (lines 176-190). Binding.
3. `docs/design/01-event-model-and-ingest.md` — Facts and Keys (lines 17-48), Decision 4 (line
   149). Binding.
4. `docs/plans/09-workflow-binary/briefs/1-03-ingest-serve.md` — Contract, "Fact wire shape" and
   "Per-fact validation". The wire shape is fixed; build exactly that.
5. `go doc` of `./internal/keys`, `./internal/secrets`, `./internal/ingest` (run from
   `tools/workflow`).
6. `tools/quality/artifact_submit.py` — `WRITE_TOOLS` and `write_paths` (lines 130-165), and the
   `cwd` rule in `run_hook` (line 190): the write-surface logic to port.
7. `tools/hooklog/tests/fixtures/artifact_writes.json` — the committed write fixtures.
8. `tools/hooklog/tests/test_hooklog.py` lines 44-75 — the shapes of a Claude `Bash` call and a
   Cursor `afterShellExecution` / `Shell` call.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Turn a batch of queue files into the facts design 2 says they yield, with the outcome each file
gets, as pure library code the drain can call; and load the one client config file both the drain
and the shim read.

## Contract

Cited, binding: design 2 Building facts ("`hook_event` from each envelope, normalised and
scrubbed", "`artifact_version` for write events on the write-surface table below whose path matches
a kind pattern. Content is read and hashed at drain time. A missing file produces nothing", commit
catch-up "read from the committed blob"); Commit facts (the whole paragraph, including "No SHA in
the output, or a failed tool call, means no commit fact; the drain never guesses from `HEAD`" and
`git diff-tree -M --name-status -r --root <sha>`); Scrub outcome ("Artifact content is never
redacted: a hit means the artifact is not sent, and its file moves to `rejected/` with the pattern
name and line"; "Content hashes are always of the raw file"); Delivery ("Each fact's ID is `<file
name>#<n>`. A file's outcome is its worst fact's"); Batch window ("coalesces repeated writes to one
`(repo_id, path)` into one file read. Cursor's `postToolUse` and `afterFileEdit` for the same write
coalesce here"); Config (file, mode 0600, `endpoint` and `key`, "Not env vars … An env override
exists for tests only", "No config: the drain makes no attempt"). Design 1 Keys for `repo_id`,
path and hashes — use `internal/keys`, never reimplement.

Decisions made at refine (settled; 2-03 builds against them):

- **Package `facts` API** (names may differ; the report gives the final ones):
  `Build(ctx, files []File) []Output`, `File{Name string; Data []byte}`,
  `Output{Name string; Facts []json.RawMessage; Reasons []string}`. An `Output` with any `Reasons`
  means the drain moves that file to `rejected/` after its facts are delivered. Facts are numbered
  `<Name>#0`, `#1`, … in the `id` key.
- **Queue file format** (unit 2-01): first line is the envelope `{"ts","harness","event"}`, the rest
  is the raw payload JSON. Unparseable envelope or payload, or a payload that is not an object:
  no facts, reason `unparseable: <short cause>`. No conversation ID: no facts, reason
  `invalid: no conversation id`.
- **Common keys.** `conversation_id` from the payload: first non-empty string of `session_id`,
  `conversation_id`, `sessionID` (same order as 2-01). `harness` from the envelope, literally
  (`auto` is passed through and matches no write surface). `event` from the envelope, else the
  payload's `hook_event_name`. `ts` from the envelope (number).
- **`hook_event`.** One per file: the payload object with every string leaf passed through
  `secrets.Redact`, recursively; a string `tool_input` that is JSON stays a string (redacted). No
  clipping. "Normalised" in design 2 is read as lifting the common keys out; the payload keeps its
  native shape.
- **Write surfaces.** Port `write_paths` exactly (event per harness, `afterFileEdit` for Cursor,
  `source == "bus"` excluded, the `WRITE_TOOLS` set, `tool_input` as object or JSON string, `edits`,
  the apply_patch `Add File` / `Update File` / `Move to` lines). Relative paths resolve against the
  payload's `cwd`, else `workspace_roots[0]`; no base and a relative path means no artifact. Then
  `keys.RepoPath`; `keys.Kind(rel)` must be non-empty; `repo_id` from `keys.RepoID(top)`.
- **`artifact_version` (worktree).** Read the file; missing, unreadable or not valid UTF-8 means no
  artifact fact and no reason. `content_hash` = `keys.ContentHash(raw bytes)`; `source` =
  `"worktree"`. `secrets.Scan(content)` with any hit: no artifact fact, and the file gets reason
  `secret: <pattern> at line <n> in <rel path>` (first hit; never the matched text). The file's
  `hook_event` is still built.
- **Coalescing.** Within one `Build` call, read each absolute path once. Emit one worktree
  `artifact_version` per `(conversation_id, repo_id, path)`, attached to the last file (by order
  given) that referred to it; earlier files that referred to it emit only their `hook_event`.
- **Commit detection.** Any post-tool event on any harness (Claude/Codex `PostToolUse`, Cursor
  `postToolUse` and `afterShellExecution`, OpenCode `tool.execute.after`) whose command text is a
  commit by design 2's rule. Command text: `tool_input.command` (string, or array of strings joined
  by spaces; `tool_input` may be a JSON string), else the payload's `command`. Output text: the
  string or the `stdout`/`output`/`stderr` fields of `tool_response`, `tool_output` or `output`. A
  failed call is one with a non-zero `exit_code`/`exitCode` (top-level or in the response), or a
  `PostToolUseFailure`/`postToolUseFailure` event: no commit fact. SHA from the output line
  `[<branch> (root-commit)? <hex7-40>]`, resolved with `git rev-parse --verify <hex>^{commit}` in
  the `-C` directory (relative to the cwd base) or the cwd base.
- **`commit` fact.** `repo_id`, full `sha`, `paths` (every path in `diff-tree` output, destination
  side for renames), `renames` (`{"from","to"}` for `R` lines). Within one `Build`, emit one commit
  fact per `(conversation_id, repo_id, sha)`.
- **Commit catch-up.** For each added, modified or renamed-to path whose `keys.Kind` is non-empty,
  `git show <sha>:<path>`, then an `artifact_version` with `source: "commit"` and an extra key
  `"sha": "<full sha>"` (kept in `raw` by ingest; 2-04's join query uses it). Same scan rule: a hit
  sends no version for that path and adds a reason.
- **git** runs via `exec.CommandContext` with a 10 s timeout per call, `GIT_TERMINAL_PROMPT=0`, never
  a shell. A git failure means that fact is skipped, not a reason.
- **Package `clientconfig`.** `Load() (Config, error)` with `Config{Endpoint, Key string}` and a
  `Path()` helper. Path: `$WORKFLOW_CLIENT_CONFIG` if set (tests only), else
  `$HOME/.config/workflow/client.toml`. Missing file returns a sentinel `ErrNoConfig`. Parse only the
  subset design 2 shows: `name = "string"` lines, `#` comments, blank lines; unknown names ignored;
  anything else is an error naming the line number, never its text. Missing `endpoint` or `key` is
  an error. No new dependency. Never log the key.
- **Fixtures.** Add `tools/hooklog/tests/fixtures/commit_calls.json` in the shape of
  `artifact_writes.json` (`[{"harness","payload"}]`), with a top-level note that these payloads are
  synthesized and unverified against real harness output (use an object
  `{"note": "...", "fixtures": [...]}` if a list cannot carry it). Cover: a Claude `Bash` commit with
  `git -C <dir> commit` after `&&`; a Codex shell commit with an array command; a Cursor
  `afterShellExecution` commit; an OpenCode `bash` commit; a failed commit; a commit with no SHA in
  the output; a `git log` call (not a commit). Use a placeholder SHA and directory that tests
  substitute.

## Changes

New packages `internal/facts` and `internal/clientconfig` with package doc comments stating the
contracts above, and their tests. Tests create a temp git repo (`git init`, a commit touching
`docs/plans/x/DESIGN.md`, `docs/plans/x/briefs/a.md`, a rename, and a non-kind file), substitute it
into the fixtures, and call `Build`.

### Keep untouched

`internal/keys`, `internal/secrets`, `internal/ingest`, `internal/store`, `internal/serve`,
`cmd/workflow`, `go.mod`. If an API you need is missing or wrong, report it; a one-line bug fix is
allowed and named in the report. `artifact_writes.json` is read only.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test ./...` → passes; `TestRepoDocsClean` still passes.
- `go test -v -run 'Writes' ./internal/facts` → each of the 11 `artifact_writes.json` payloads (with
  `cwd` set to the temp repo, the files present) yields one `hook_event` and one `artifact_version`
  with the right `repo_id`, `path`, `content_hash` and `source: "worktree"`; a Cursor `postToolUse`
  plus `afterFileEdit` for one file in one `Build` reads the file once and emits one version; with
  the file deleted the payload yields only its `hook_event`.
- `go test -v -run 'Commit' ./internal/facts` → each commit fixture yields a `commit` fact with the
  full SHA, the `diff-tree` paths and the rename pair, plus `source: "commit"` versions (with `sha`)
  for the design and brief paths only; the failed, no-SHA and `git log` fixtures yield no commit
  fact.
- `go test -v -run 'Secret|Scrub' ./internal/facts` → an artifact holding a credential-shaped
  string (built by concatenation at runtime) yields no `artifact_version`, a reason naming the
  pattern, line and path, and no output contains the secret text; a payload string holding one is
  redacted in the `hook_event`.
- Every fact `Build` emits passes `ingest.Ingest` validation: a test feeds them to `Ingest` on a
  `store.Open(t.TempDir())` tenant and gets no `invalid:` result.
- `go test -v ./internal/clientconfig` → reads a temp file via `WORKFLOW_CLIENT_CONFIG`; missing file
  is `ErrNoConfig`; a malformed line errors with its number and without its text.

Safety: test only in `t.TempDir()` / `mktemp -d` repos. Never read `~/.config/workflow`, the live
queue, `~/.local/share/workflow*` or the legacy spool. Never print `TYPESAFE_API_KEY` or any key.

Commit: title `[exec <execution_id>] Phase 2: fact building and client config` (the orchestrator
supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/2-02-facts-clientconfig.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems;
nothing derivable; include the final exported API names) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
