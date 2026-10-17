# Brief: 4-01 — Layout contract

Consumer: the phase 4 worker.
Owned paths:
`tools/release/test_layout.py` (new),
`tools/release/test_release.py`,
`tools/README.md` (new),
`packages/README.md` (new),
`packages/workflow/README.md` (new),
`packages/hooklog/README.md`,
`packages/workflow-analytics/README.md` (new),
`packages/opencode-workflow-hooks/README.md`,
`packages/opencode-workflow-hooks/python/batch_flush_cli.py`,
`packages/opencode-workflow-hooks/python/batch_aggregator.py`,
`packages/opencode-workflow-hooks/tests/test_batch.py`,
`tools/driver/jev_signal_log.py` (new),
`tools/driver/tests/test_jev_signal_log.py` (new),
`docs/design/05-distribution.md`,
`docs/ARCHITECTURE.md`,
`docs/plans/13-monorepo-restructure/reports/4-01-layout-contract.md` (new).
Touch nothing else. Do not edit `IMPLEMENTATION.md` unless you stop over budget. Do not edit `DESIGN.md`.
Commits: one commit on the current branch when done evidence passes, plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before that commit, write `docs/plans/13-monorepo-restructure/reports/4-01-layout-contract.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 3.
Runs alongside: nothing.
Budget: 40 files to read, about 700 lines to change, 70 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Packages, Domain: Tools, Domain: Plugin (the `./script/...` and marketplace sentences), Assumption 11, Assumption 12, Phase 4 outcome and surfaces. Do not read Phases 5–7 except to avoid doing their work.
2. `packages/opencode-workflow-hooks/python/batch_flush_cli.py` and `batch_aggregator.py` — where the signal-log path is chosen.
3. `tools/release/test_release.py` — how the release suite is invoked, and the `bin/workflow` path it still joins.
4. `docs/ARCHITECTURE.md` section "Component Map". `docs/design/05-distribution.md` section "Layout" and the "Not in this round" heading.
5. `plugins/yakka/hooks/cursor.json`, `plugins/yakka/.cursor-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `.claude-plugin/marketplace.json`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The packages, tools, and `plugins/yakka` rule fails loudly when it is broken, each package README says how that package is built and shipped, and the OpenCode signal log no longer defaults into `tools/`.

## Contract

Cited, binding. Settled. Do not reopen them.

- "A committed check enforces this direction (Phase 4)." Direction: "`plugins/yakka` → packages. Packages → packages. Tools → anything." "No runtime code path or config in the plugin or in a package resolves into `tools/`."
- "**README fields.** Each package README carries four labelled fields: **Consumers**, **Build**, **Test**, **Release**. Release states the mechanism, or "embedded in `<package>`", or "ships as plugin files"."
- "**No runtime path into `tools/`.** Package runtime code and config never resolve a path into `tools/`. The following are exempt: comments; Markdown; test code and test config: files under `tests/`, `*_test.go`, `test_*.py`, `*.test.*`, `playwright*.config.ts`."
- "**OpenCode signal log.**" "Its new default is `${XDG_STATE_HOME:-~/.local/state}/workflow/jev-signal-log.jsonl`, overridable by `WORKFLOW_JEV_SIGNAL_LOG`. `tools/driver` readers use the same resolution (Assumption 11)."
- Assumption 12: the package's runtime read of `docs/lab/RESEARCH/.../proofs` in `batch_aggregator.py` is not fixed here. Do not edit files under `docs/lab/`.
- "Core skills may cite tools and paths in prose, as `execute` cites `tools/driver/`. They never reference `.claude/skills/` or a maintainer skill by path."
- "Each marketplace lists exactly one plugin. Its `source` is `plugins/yakka`."
- "Cursor hook commands are plugin-root-relative `./script/...`."
- Phase 4 outcome, the clauses this unit can check: the layout check passes and is one stdlib Python test under `tools/release/` that runs with that suite; the check fails, naming the file and the offending path, for each of the six cases, each covered by a fixture; the OpenCode package and `tools/driver` resolve the signal-log default as Assumption 11 states; `tools/README.md` and `packages/README.md` index every directory under them; `docs/design/05-distribution.md` has a Layout section stating packages, tools, and `plugins/yakka`; `docs/ARCHITECTURE.md`'s component map shows `plugins/yakka`, the packages, and the tools.
- "`plugins/yakka` is not a package and does not carry those fields."
- "`bin/VERSION` is not bumped before the rename phases." This unit does not change a shipped plugin file. Do not bump plugin manifests. Do not add a CHANGELOG entry.
- Phase 3 Carried item 1 (logged-in Cursor session) is not this unit. Do not run `agent login`. Do not start Cursor.

Go comments in `packages/workflow/internal/facts/facts.go` and `packages/workflow/internal/scorer/jev.go` name `tools/`. Reword them only if the check's comment exemption cannot leave them in place. The exemption is the contract; prefer leaving them.

## Changes

### Layout check

New `tools/release/test_layout.py`, stdlib `unittest` only. A function scans a root directory and returns violations. Each violation names the file and the offending path. The pass test scans this repo. The six fail tests each build a temp fixture and assert the violation names that file and that path. Do not mutate the repo to prove failure.

The six cases, from the Phase 4 outcome:

1. An executed path in the plugin's hook configs (`plugins/yakka/hooks/`), its MCP configs (`plugins/yakka/.mcp.json`, `plugins/yakka/.codex-mcp.json`), or `plugins/yakka/bin/workflow` resolves into `tools/` or `.claude/`.
2. A non-exempt file under `packages/` contains a `tools/` path. Exempt comments, Markdown, and the test files and test config named in the package contract. `tools/list` and `tools/call` are MCP method names, not a path into `tools/`. Do not flag them.
3. A file under `plugins/yakka/skills/` references `.claude/skills/`. That is the `skills/` tree after Phase 3. Do not flag `.claude/skills/` itself.
4. A `packages/<name>/` lacks a README with the four labels **Consumers**, **Build**, **Test**, **Release**.
5. Either `.cursor-plugin/marketplace.json` or `.claude-plugin/marketplace.json` lists more than one plugin, or its core plugin `source` is not `plugins/yakka`.
6. A command in `plugins/yakka/hooks/cursor.json` is not plugin-root-relative `./script/...` (it must start with `./script/` and must not contain `..`, `${CURSOR_PLUGIN_ROOT}`, or an absolute path).

`tools/release/test_release.py` still joins `bin/workflow` at the repo root. Phase 3 moved that wrapper to `plugins/yakka/bin/workflow`, and `WORKFLOW_ROOT` is that plugin directory. Repoint the suite's wrapper and `bin/` copy at `plugins/yakka/bin`, and the `test_10` expected `WORKFLOW_ROOT`, so `python3 -m unittest discover -s tools/release -p 'test_*.py'` can load. Do not change wrapper behaviour.

### Package READMEs

Add the four labelled fields. Keep existing prose.

- `packages/workflow`: consumers are the harnesses through `plugins/yakka/bin/workflow`, `tools/release`, and `tools/quality` (catalogue). Build is `go build` in that module, or the wrapper's step-4 source build. Test is `go test ./...` in `packages/workflow`. Release is `tools/release/build.sh` (four `workflow-<os>-<arch>` binaries and `SHA256SUMS`).
- `packages/hooklog`: consumers are the copies under `plugins/yakka/script/` and the OpenCode plugin's queue files. Build is none (bash and Python stdlib). Test is `python3 -m unittest discover -s packages/hooklog/tests`. Release is "ships as plugin files".
- `packages/workflow-analytics`: consumer is the binary that embeds the built site. Build is `npm run build`. Test is `npm test` and `npm run test:e2e`. Release is "embedded in `packages/workflow`".
- `packages/opencode-workflow-hooks`: consumer is an OpenCode `file://` plugin registration. Build is none (OpenCode loads the TypeScript). Test is `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` and `python3 -m unittest discover -s packages/opencode-workflow-hooks/tests`. Release is "ships as plugin files". Name sibling packages the README already points at (`packages/hooklog`).

### Indexes

`tools/README.md` states the direction rule and indexes every directory now under `tools/`, one line each: `cloud-env` (cloud bootstrap of core skills), `driver` (phase closure primitives), `interception` (TypeSafe lever and window-status joins), `jev-variants` (variant-search registry), `quality` (legacy quality service; catalogue lives in `packages/workflow`), `release` (four-platform binary build), `transcript` (session cost metrics).

`packages/README.md` indexes every directory now under `packages/`, one line each: `hooklog` (hook capture edge), `opencode-workflow-hooks` (OpenCode plugin), `workflow` (Go binary and catalogue), `workflow-analytics` (static site embedded in the binary). State that `plugins/yakka` is the plugin, not a package.

### Signal log

Replace the `tools/driver/.jev-signal-log.jsonl` default in `batch_flush_cli.py` with Assumption 11's path. `WORKFLOW_JEV_SIGNAL_LOG` still overrides. `batch_aggregator.py` takes `log_path` from its caller; do not give it a `tools/` default, and do not move the `docs/lab` import.

`tools/driver` has no reader of `.jev-signal-log.jsonl` today. Do not add a feature that tails or appends the log. Add `tools/driver/jev_signal_log.py` with the same resolution, and a test that the package default and that function are the same path: unset env and unset `XDG_STATE_HOME` → `~/.local/state/workflow/jev-signal-log.jsonl`; `XDG_STATE_HOME` set → that directory; `WORKFLOW_JEV_SIGNAL_LOG` set → that path. The default must not contain `tools/driver`. Do not import `batch_aggregator` from the driver (importing it inserts `docs/lab` proofs onto `sys.path`).

Update the OpenCode package README's signal-log default to the same path. Root `README.md` still names the old path and is not an owned path; leave it and name that in the report.

### Docs

`docs/ARCHITECTURE.md` component map: the plugin install root is `plugins/yakka` (skills, hooks, `script/`, `bin/`), not the repo root. Show `packages/` and `tools/` as the other two trees. Keep maintainer skills at `.claude/skills/`. Do not rename the product to yakka.

`docs/design/05-distribution.md` Layout section: state packages, tools, and `plugins/yakka`. The monorepo "Not in this round" line is already gone. Leave the remaining "Not in this round" bullets (pinned copies, registration).

### Keep untouched

Product name `workflow`, marketplace name, repo URL, `plugins/yakka/bin/VERSION`, plugin manifest versions, hook event lists, `packages/workflow` module path, `docs/lab/**`, root `README.md`, `CHANGELOG.md`, and anything Phases 5–7 own (the yakka rename).

## Done evidence

Write `tools/release/test_layout.py` so the pass test fails on the current signal-log default before you change `batch_flush_cli.py`. Record that failure, then the pass.

- `python3 -m unittest tools/release/test_layout.py` → pass, including one fixture test per case that fails the check and names the file and the path.
- `python3 -m unittest discover -s tools/release -p 'test_*.py' -v` lists `test_layout` cases. You do not have to wait out `test_release.py`'s binary builds if they exceed the budget; say so. The path repoint must be in the diff.
- `python3 -m unittest packages/opencode-workflow-hooks/tests/test_batch.py tools/driver/tests/test_jev_signal_log.py` → pass. The default path is Assumption 11's, and both resolvers agree.
- `packages/workflow/README.md`, `packages/hooklog/README.md`, `packages/workflow-analytics/README.md`, and `packages/opencode-workflow-hooks/README.md` each contain the four labels.
- `tools/README.md` names every child of `tools/`. `packages/README.md` names every child of `packages/`.
- The component map in `docs/ARCHITECTURE.md` shows `plugins/yakka`, `packages/`, and `tools/`. The Layout section in `docs/design/05-distribution.md` states those three.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
