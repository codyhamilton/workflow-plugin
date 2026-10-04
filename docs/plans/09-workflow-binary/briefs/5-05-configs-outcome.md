---
brief_id: 229
design_id: 209
---

# Brief: 5-05 — Harness configs, MCP registration and the phase 5 outcome

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. The orchestrator runs this unit's
`tools/release/phase5_outcome.py` to close phase 5; phase 6 rewrites the skills against the
registrations this unit ships.
Owned paths: `hooks/hooks.json`, `hooks/cursor.json`, `tools/hooklog/cursor-hooks.example.json`,
`tools/hooklog/codex-hooks.example.json`, `.mcp.json`, new `tools/hooklog/cursor-mcp.example.json`,
new `tools/hooklog/codex-mcp.example.toml`, `tools/hooklog/README.md`,
`tools/hooklog/tests/test_surfaces.py`, `tools/hooklog/tests/test_artifact_submit_surfaces.py`
(deleted) → new `tools/hooklog/tests/test_write_surfaces.py`, new `tools/release/phase5_outcome.py`,
`docs/plans/09-workflow-binary/reports/5-05-configs-outcome.md` (new). Touch nothing else; not
`.cursor-plugin/plugin.json`, `skills/` (phase 6), `tools/quality/` (the legacy lab keeps
`artifact_submit.py`), or any unit 5-01 to 5-04 path (a defect there is reported, not fixed).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 5-01, 5-02, 5-03, 5-04, all committed. Read their reports first.
Runs alongside: nothing (it tests every earlier unit together).
Budget: 10 files to read, about 400 lines changed including tests, 55 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 5 (grep `### Phase 5`), the outcome sentence
   verbatim and the Units decisions.
2. `docs/plans/09-workflow-binary/reports/5-01-version-init.md`, `5-02-wrapper-release.md`,
   `5-03-spool-flip-retire.md`, `5-04-opencode-plugin.md`.
3. `docs/design/05-distribution.md` — Wrapper (lines 43-46, the prefetch), Per-harness configs
   (lines 68-77), Retired (lines 79-85).
4. `docs/design/04-advisory-surface.md` — registration (lines 93-96).
5. `docs/design/02-edge-capture.md` — Write surfaces (line 176), Per-harness install (line 191,
   Codex's 3 s ceiling), Tests (line 220).
6. The four hook configs and `.mcp.json` (short).
7. `tools/hooklog/tests/test_surfaces.py` and `test_artifact_submit_surfaces.py` (53 and 139 lines),
   `tools/hooklog/tests/fixtures/artifact_writes.json`.
8. `tools/workflow/cmd/workflow/capture_test.go` — `startHosted`, `writeConfig` and the ledger
   query for `artifact_version` (grep `artifact_version`): the hosted-serve setup to copy into
   Python.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, every shipped harness registration captures through `spool.sh` (or the
OpenCode plugin) into the queue, registers the advisory shim as stdio `bin/workflow mcp`, warms the
binary at session start, and one script proves every clause of the phase 5 outcome.

## Contract

Cited, binding (DESIGN.md, Phase 5 outcome): "`bin/workflow --version` prints `workflow <version>
<commit>` from a clean temp cache by building from source, and two concurrent first runs both
succeed; `tools/release/build.sh` produces four binaries and `bin/SHA256SUMS`; `workflow init` in a
temp `HOME` writes `client.toml`, `serve.env` and the user unit, mode 0600, and enables nothing;
replaying the write fixtures through each shipped hook config into a temp `serve` produces an
`artifact_version`; no shipped config references `artifact_submit.py`, `--harness auto` or the HTTP
MCP; `drain.py`, the systemd timer and service are gone."
Design 4 (registration): the shim is the stdio `bin/workflow mcp`; the HTTP `127.0.0.1:8765/mcp`
registration is removed.

Decisions made at refine (settled):

- **Hook configs.** `hooks/hooks.json`: `--harness auto` → `--harness claude` everywhere. All four
  configs: remove every `artifact_submit.py` hook. Codex example: every timeout ≤ 3. Worktree
  events in `hooks.json` stay `[]`.
- **Prefetch.** A second `SessionStart`/`sessionStart` hook in the Claude, Cursor and Codex configs:
  `nohup bash "<root>/bin/workflow" --version </dev/null >/dev/null 2>&1 & exit 0`, with `<root>`
  written as each config already writes it (`${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}`,
  `${CURSOR_PLUGIN_ROOT}`, `/ABS/PATH/workflow-plugin`); timeout 5 (3 for Codex); prints nothing.
- **MCP.** `.mcp.json` → `{"mcpServers": {"workflow": {"command":
  "${CLAUDE_PLUGIN_ROOT}/bin/workflow", "args": ["mcp"]}}}`. New
  `tools/hooklog/cursor-mcp.example.json` (Cursor `mcp.json` shape, absolute
  `/ABS/PATH/workflow-plugin/bin/workflow`, `args: ["mcp"]`) and
  `tools/hooklog/codex-mcp.example.toml` (`[mcp_servers.workflow]`, `command =
  "/ABS/PATH/workflow-plugin/bin/workflow"`, `args = ["mcp"]`). The Cursor manifest is unchanged.
- **README.** `tools/hooklog/README.md` describes the queue, `bin/workflow drain`, `workflow init`,
  the MCP examples and `serve.secrets.env` for `TYPESAFE_API_KEY`; no retired name.
- **test_surfaces.py.** Same coverage, against a temp `WORKFLOW_QUEUE` with
  `WORKFLOW_HOOKLOG_KICK=0`: every event in each config yields exactly one queue file whose
  envelope event is that event (no `drain.py`); the prefetch hooks are run with `WORKFLOW_BIN` a
  stub and print nothing; the Cursor manifest test stays.
- **test_write_surfaces.py** (replaces `test_artifact_submit_surfaces.py`). Builds the binary once
  into a temp dir (`go build` from `tools/workflow` with `$HOME/.local/go/bin` on `PATH`) and sets
  `WORKFLOW_BIN` to it. Starts a hosted `serve` on a free `127.0.0.1` port (never 8765 or 8770),
  with temp `WORKFLOW_SERVE_DATA`, `WORKFLOW_SERVE_KEYS=t=<random>`, a temp client.toml naming it,
  temp `WORKFLOW_QUEUE`, `TYPESAFE_API_KEY=` blank. A temp git repo with one commit (no `repo_id`
  before a first commit) holds the fixtures' paths. Each fixture in `artifact_writes.json`
  (Claude, Cursor ×2 surfaces, Codex, OpenCode) is replayed through every command its shipped
  config registers for that event (`/ABS/PATH/workflow-plugin` and the plugin-root variables
  pointed at the checkout); OpenCode fixtures go through the plugin the way 5-04's test loads it,
  or, if that is not workable from Python, through `spool.sh --harness opencode` (5-04 proved them
  equivalent) and say which. Then wait (≤ 30 s) until the tenant's `ledger.db` has an
  `artifact_version` fact for each fixture's path. Kill serve and every child whose command line
  holds the temp dir.
- **phase5_outcome.py.** A thin aggregator printing one `outcome <clause> PASS|FAIL` line per
  clause and exiting non-zero on any FAIL, by running the units' own checks: `version-clean-build`
  and `concurrent-first-runs` and `release-build` (5-02's tests by name), `init` (5-01's `go test
  -run TestInit`), `write-replay` (`test_write_surfaces.py`), `no-retired-refs` (the grep below),
  `retired-files-gone` (`drain.py`, the `.service`, the `.timer`, `install-drain.sh` absent).
- **Retired-reference grep.** Pattern `drain\.py|install-drain|workflow-hooklog-drain|artifact_submit|--harness auto|127\.0\.0\.1:8765/mcp|WORKFLOW_ARTIFACT_SUBMIT_CLI`
  over `hooks/`, `.mcp.json`, `tools/hooklog/*.json`, `tools/hooklog/*.sh`,
  `tools/hooklog/*.example.*`, `tools/hooklog/README.md`, `packages/opencode-workflow-hooks/src`,
  its `README.md` and `opencode.json.example`, `bin/` and `tools/release/` (excluding
  `phase5_outcome.py`) → nothing. `skills/` is excluded (phase 6); `tools/quality/`,
  `docs/`, `CHANGELOG.md` and `tools/hooklog/hooklog.py` are history or the legacy lab and stay.

## Changes

The configs, the two MCP examples, the README and the three test files per the decisions.
`git rm` `test_artifact_submit_surfaces.py`.

### Keep untouched

The event lists of each config (the surface tests assert them), the Cursor permissive responses
and `.cursor-plugin/plugin.json`.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

Fail first: write `phase5_outcome.py` and `test_write_surfaces.py` first and quote the failing
lines.

- `python3 -m unittest discover -s tools/hooklog/tests -v` → passes.
- `python3 tools/release/phase5_outcome.py` → the orchestrator's phase gate; every line `PASS`, one
  per clause: `version-clean-build`, `concurrent-first-runs`, `release-build`, `init`,
  `write-replay`, `no-retired-refs`, `retired-files-gone`.
- `go test -count=1 ./...` (from `tools/workflow`) → passes.
- `node --experimental-strip-types --test tests/test_hooks.mjs` (from the OpenCode package) → passes.
- `python3 -c 'import json,tomllib;[json.load(open(p)) for p in (".mcp.json","tools/hooklog/cursor-mcp.example.json")];tomllib.load(open("tools/hooklog/codex-mcp.example.toml","rb"))'` → exits 0.
- `pgrep -f '<the test temp dirs>'` after the run → prints nothing.

Live effects, record in the report and do not trigger them yourself: on commit Cursor's
`sessionStart` runs the prefetch, which (no release exists) tries GitHub once and then builds into
the real `~/.cache/workflow/0.1.0/` with `~/.local/go/bin/go`; the repo-root `.mcp.json` change
means new Claude Code sessions opened in this repo get the stdio `workflow` server instead of the
legacy `workflow-quality` HTTP tools.

Safety: temp dirs only (`HOME`, `WORKFLOW_QUEUE`, `WORKFLOW_CLIENT_CONFIG`, `WORKFLOW_SERVE_DATA`,
`XDG_CACHE_HOME` temp in every child; set `WORKFLOW_BIN` so no hook builds into the real cache).
Never touch `~/.local/share/workflow*`, `~/.config/workflow`, `~/.cache/workflow`,
`~/.config/systemd`, the live queue or the legacy service; never run `systemctl` except `--user
cat`/`status` reads. Every `serve` off ports 8765 and 8770 and killed after. `TYPESAFE_API_KEY=`
blank in every child; never print it or the test key.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 5: harness configs, MCP
registration and outcome` (the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/5-05-configs-outcome.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), including the full `phase5_outcome.py` output, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
