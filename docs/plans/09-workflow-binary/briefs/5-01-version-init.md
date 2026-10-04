---
brief_id: 225
design_id: 209
---

# Brief: 5-01 — `workflow --version` and `workflow init`

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. 5-02's wrapper tests read the
`--version` line this unit prints; 5-05's outcome script runs `init` through the wrapper.
Owned paths: `tools/workflow/cmd/workflow/main.go` (only the `version` case, the usage string and a
new `case "init"`), new `tools/workflow/cmd/workflow/init.go`, new
`tools/workflow/cmd/workflow/init_test.go`,
`docs/plans/09-workflow-binary/reports/5-01-version-init.md` (new). Touch nothing else; in
particular not `internal/`, the other `*_test.go` files, `go.mod` or `go.sum`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing (phases 2 to 4 are committed).
Runs alongside: 5-03, 5-04 (disjoint paths). 5-02 starts after this unit commits.
Budget: 6 files to read, about 250 lines to write including tests, 35 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 5 (grep `### Phase 5`), the outcome sentence
   and the Units decisions under it.
2. `docs/design/05-distribution.md` — Wrapper (the `--version` line, line 38) and Local bootstrap
   (lines 48-60).
3. `tools/workflow/cmd/workflow/main.go` — `run` (lines 29-55).
4. `go doc ./internal/clientconfig` — `Path`, `Load`, the file format.
5. `tools/workflow/cmd/workflow/drain_test.go` — `newEnv` and how the binary is built for tests
   (grep `func newEnv`, `TestMain`).

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, `workflow --version` and `workflow version` print `workflow <version>
<commit>`, and `workflow init` sets up local mode once in the user's config directories without
enabling or starting anything.

## Contract

Cited, binding (design 5, Wrapper): "`workflow --version` prints `workflow <version> <commit>`."
(Local bootstrap): "writes `~/.config/workflow/client.toml` (mode 0600) with `endpoint =
"http://127.0.0.1:8770"` and a random key, unless it exists; writes `~/.config/workflow/serve.env`
(mode 0600) with `WORKFLOW_SERVE_KEYS=local=<that key>`; writes a systemd user unit
`workflow-serve.service` that runs `bin/workflow serve` with that environment file, and prints the
`systemctl --user enable --now` command rather than running it."
DESIGN.md Phase 5 outcome: "`workflow init` in a temp `HOME` writes `client.toml`, `serve.env` and
the user unit, mode 0600, and enables nothing".

Decisions made at refine (settled):

- **Version.** `workflow --version` and `workflow version` both print exactly `workflow <version>
  <commit>\n` to stdout, exit 0 (today: `workflow %s (%s)`). Unset ldflags give `workflow dev
  unknown`. Usage becomes `usage: workflow serve | drain | mcp | status | init | version`.
- **Paths.** client.toml at `clientconfig.Path()` (honours `WORKFLOW_CLIENT_CONFIG`); serve.env at
  `$HOME/.config/workflow/serve.env`; the unit at `$HOME/.config/systemd/user/workflow-serve.service`.
  Directories created 0700, files 0600 (explicit chmod, umask-proof). `HOME` from the environment;
  error if empty.
- **Only if absent.** Each of the three files is written only when it does not exist; an existing
  file is left byte-identical and reported `kept`. If client.toml exists, serve.env takes its key
  (via `clientconfig.Load`); if client.toml is new, its key is 32 random bytes (`crypto/rand`) as
  64 hex characters. The key is never printed.
- **serve.env content:** `WORKFLOW_SERVE_KEYS=local=<key>` and
  `WORKFLOW_CHECKS_DIR=<WORKFLOW_ROOT>/tools/quality`, one per line. `WORKFLOW_ROOT` is set by the
  wrapper (5-02); `init` without it exits 2 with `workflow init: WORKFLOW_ROOT unset; run it through
  bin/workflow`. `WORKFLOW_SERVE_ADDR` is not written (serve defaults to `127.0.0.1:8770`).
- **No `TYPESAFE_API_KEY` in any file init writes**, even when it is in the environment. The unit
  carries `EnvironmentFile=<abs serve.env>` and `EnvironmentFile=-<same dir>/serve.secrets.env`;
  init does not create `serve.secrets.env`. It prints: create `~/.config/workflow/serve.secrets.env`
  (mode 0600) holding `TYPESAFE_API_KEY=...` to enable screening.
- **Unit content:** `[Unit] Description=workflow serve (local)`; `[Service]` the two
  `EnvironmentFile` lines, `ExecStart=<WORKFLOW_ROOT>/bin/workflow serve`, `Restart=on-failure`;
  `[Install] WantedBy=default.target`.
- **Enables nothing.** init never executes `systemctl` or any other process. It prints, last:
  `systemctl --user daemon-reload && systemctl --user enable --now workflow-serve.service`. Output
  lists each path with `wrote` or `kept`. Exit 0; any write error exits 1.

## Changes

`main.go`: `case "--version", "version"`, `case "init": return runInit(args[1:])`, the usage
string. `init.go`: `runInit` (no flags; extra args exit 2). `init_test.go`: the tests below,
driving the built binary as the other tests do.

### Keep untouched

Every other subcommand, `runServe`, `runMCP` and the screen wiring. All earlier tests pass
unchanged.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

Fail first: write `init_test.go` first and quote its failure.

- `go vet ./... && go test -race -count=1 ./...` → passes.
- `go test -v -count=1 -run 'TestVersion|TestInit' ./cmd/workflow` → passes, covering:
  1. a binary built with `-ldflags "-X main.version=9.9.9 -X main.commit=abc123"` prints exactly
     `workflow 9.9.9 abc123` for both `--version` and `version`;
  2. temp `HOME`, `WORKFLOW_CLIENT_CONFIG` unset, `WORKFLOW_ROOT=/x/root`,
     `TYPESAFE_API_KEY=sentinel-not-a-key`: the three files exist, each mode 0600, dirs 0700;
     client.toml endpoint is `http://127.0.0.1:8770`; serve.env's key equals client.toml's;
     `WORKFLOW_CHECKS_DIR=/x/root/tools/quality`; unit `ExecStart=/x/root/bin/workflow serve` and
     both `EnvironmentFile` lines; `sentinel-not-a-key` and `TYPESAFE_API_KEY=` appear in no
     written file; the key appears nowhere in stdout or stderr; stdout ends with the systemctl
     command;
  3. second run: all three `kept`, bytes unchanged;
  4. pre-existing client.toml with key K and no serve.env: serve.env gets `local=K`, client.toml
     unchanged;
  5. no `WORKFLOW_ROOT` → exit 2, nothing written;
  6. `PATH` holding a fake `systemctl` script that touches a marker: marker absent after init.

Safety: temp dirs only (`t.TempDir()` for `HOME` and every config path). Never touch
`~/.config/workflow`, `~/.config/systemd` or `~/.local/share/workflow*`, and never run
`systemctl`. `TYPESAFE_API_KEY` is in your environment: children get only the sentinel above or a
blank value; never print, log, echo or write the real one (no `env`, `printenv`, `set -x`).

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 5: version and init` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/5-01-version-init.md` (design 1, Execution report: what was
done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), with the test lines and one sample `init` stdout (key absent by construction), and
include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
