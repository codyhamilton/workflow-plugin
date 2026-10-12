# Monorepo Restructure: Lab Collapse, Packages and Tools

## Intent

User request, verbatim:

> Have an agent work on a background design - collapsing workflow-lab, which should not be its own plugin (just skills at root, they're maintainer-only), as well as cleaning up the repo and distinguishing tools from packages (workflow bin to my mind is a package), organising the repo into a proper monorepo with packages/ containing the various packages it holds as independent deployable units

## Problem

The repo's directory names no longer say what anything is.

- **The lab plugin.** `workflow-lab` is a second marketplace plugin (`plugins/workflow-lab`, v1.2.0).
  - Its seven skills are maintainer-only.
  - Its skills run repo-checkout commands such as `python3 tools/transcript/find.py` or `tools/jev-variants/...`. Those commands cannot work from the plugin's own install root, `./plugins/workflow-lab`, which contains no `tools/`.
  - Lab-install paths are spread across its manifests, the marketplace entry, `install.sh`, `tools/cloud-env` and `tools/driver/check_skills.py` (`LAB_SKILLS`). They have drifted: they name four skills where there are seven, and `docs/lab/FINDINGS.md` gives the wrong version.
- **`tools/` mixes two kinds of directory**, with nothing marking which is which.
  - Shipped runtime units:
    - `tools/workflow` is the Go binary, and the only released artifact.
    - `tools/hooklog/spool.sh` is the hook edge that every harness config executes.
  - Maintainer tooling: `transcript`, `driver`, `quality`, `jev-variants`, `interception`, `release`, `cloud-env`.
- **`packages/`** already holds two deployable units:
  - `workflow-analytics`, embedded into the binary.
  - `opencode-workflow-hooks`, an npm-shaped OpenCode plugin.
- **The binary depends on a tool.** The binary's scorer loads its catalogue (`criteria.json` plus `checks/*.json`) from `tools/quality`, through `WORKFLOW_CHECKS_DIR` and through its tests. So a shipped unit depends on a maintainer tool.
- **This round was deferred.** `docs/design/05-distribution.md` says "Not in this round: the monorepo reorganisation". This design is that round.

Why this matters now:

- Each new unit has to guess its directory. Plan 12 is adding packages to the binary, and recent work added a shipped OpenCode package and an embedded site.
- Each guess hard-codes another cross-tree path. Recon counted about 60 Go imports, more than 15 `parents[N]` and `sys.path` assumptions, and more than 60 hook commands that encode the current layout.

What "cleaning up" covers here:

- Removing the second plugin, along with its drifted lists and opt-ins.
- Moving the two shipped runtime units out of `tools/`.
- Cutting the package → tool dependencies: the catalogue, and one runtime default path.
- Retiring the superseded `lab-proposal` skill.
- Indexing both trees.
- Enforcing the dependency direction with a check, so the layout stays clean.

Cleanup of tool internals, legacy services and research notes is out of scope.

## Solution Shape

After this change the repo has three kinds of directory, each with one rule:

- **Plugin surface.** The repo root remains the `workflow` plugin.
- **Packages.** `packages/<name>/` holds every independently buildable or deployable unit. Each carries its own manifest or README, which states how it is built, tested and released.
- **Tools.** `tools/<name>/` holds maintainer and automation tooling. No runtime code path or config in the plugin surface or in a package resolves into `tools/`.

The lab plugin is gone. Its skills become Claude Code project skills under `.claude/skills/`, which load only when someone works inside this repo. The marketplace lists one plugin.

Dependency direction:

- Plugin surface → packages.
- Packages → packages.
- Tools → anything.

A committed check enforces this direction (Phase 3).

### Domain: Plugin surface (repo root)

- Owns:
  - `.claude-plugin/{marketplace,plugin}.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`.
  - `skills/` (the six core skills).
  - `hooks/{hooks,cursor,codex}.json`, `.mcp.json`, `.codex-mcp.json`.
  - `bin/{workflow,VERSION,SHA256SUMS,RELEASE_URL}`.
  - `install.sh`.
- Contract:
  - Marketplace `workflow-plugin` lists exactly one plugin, `workflow`, with `source: "./"`. The marketplace name, plugin name and repo URL are unchanged.
  - Runtime configs never resolve into `tools/` or `.claude/`. Every executed path in `hooks/*.json`, `.mcp.json`, `.codex-mcp.json` and `bin/workflow` resolves under `${CLAUDE_PLUGIN_ROOT}` (or the harness equivalent) to `bin/` or `packages/<name>/`.
  - Hook commands keep their shape. Each is `bash "<root>/packages/hooklog/spool.sh" --harness <h> [--event <E>]`, with arguments unchanged per harness; Codex passes no `--event`. Only the directory changes.
  - `bin/workflow` keeps its four-step resolution and its cache key, `${XDG_CACHE_HOME:-~/.cache}/workflow/<bin/VERSION>/workflow-<os>-<arch>`. Its step-4 source build reads `packages/workflow`.
  - `bin/VERSION` is not bumped. Cached binaries stay valid, and the version field of `workflow --version` is unchanged; only the commit field differs.
  - Plugin version bumps:
    - Any phase that changes a shipped plugin file bumps the plugin manifests one minor version.
    - The Claude, Cursor and Codex manifests move together, with a `CHANGELOG.md` entry.
  - `install.sh` (every mode) and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only. The `WORKFLOW_INSTALL_LAB` opt-in and every lab-install path are removed.
  - Core skills may cite tools and paths in prose, as `execute` cites `tools/driver/`. They never reference `.claude/skills/` or a maintainer skill by path.
- Non-goals:
  - Moving the plugin itself into `packages/` (Assumption 2).
  - Changing hook events, MCP tools or binary behaviour.
  - Retiring `install.sh`.

### Domain: Packages (`packages/<name>/`)

- Owns:

  | Package | From | Unit | Manifest |
  |---|---|---|---|
  | `packages/workflow` | `tools/workflow`, plus the catalogue from `tools/quality/{criteria.json,checks/}` | Go binary; four-platform release assets; embeds the analytics site; ships the catalogue | `go.mod`, module `github.com/codyhamilton/workflow-plugin/packages/workflow` |
  | `packages/hooklog` | `tools/hooklog` | Hook capture edge: `spool.sh`, `hooklog.py`, scrub, example harness configs | README (bash and Python stdlib) |
  | `packages/workflow-analytics` | unchanged | SvelteKit static site; embedded into `packages/workflow`; optionally a Cloudflare Pages deploy | `package.json` (`private: true`) |
  | `packages/opencode-workflow-hooks` | unchanged | OpenCode plugin | `package.json` (public-shaped) |

- Contract:
  - **README fields.** Each package README carries four labelled fields: **Consumers**, **Build**, **Test**, **Release**. Release states the mechanism, or "embedded in `<package>`", or "ships as plugin files".
  - **No runtime path into `tools/`.** Package runtime code and config never resolve a path into `tools/`. The following are exempt:
    - comments;
    - Markdown;
    - test code and test config: files under `tests/`, `*_test.go`, `test_*.py`, `*.test.*`, `playwright*.config.ts`.
  - **References between packages.** A package references other packages only by sibling-relative paths, and only those its README names.
  - **Catalogue.** It lives at `packages/workflow/catalogue/`, which holds `criteria.json` and `checks/*.json`.
    - It keeps the shape `scorer.LoadChecks(dir)` expects today. `WORKFLOW_CHECKS_DIR` names this directory, as it names `tools/quality` today.
    - Go tests and the analytics e2e and hosted setups load it from there.
    - `tools/quality` reads `criteria.json` and `checks/` from there.
    - The rubric citation in `skills/execute/SKILL.md` and `skills/refine/templates/brief.md` becomes `packages/workflow/catalogue/checks/execution-report.json`.
  - **Sibling depth.** `packages/workflow` and `packages/hooklog` are siblings at the same depth as today. The Go tests' `../../../hooklog/...` and `../../../../docs/...` paths therefore resolve unchanged.
  - **Release.**
    - `tools/release/build.sh` builds `packages/workflow-analytics` and copies its output into `packages/workflow/internal/serve/site/`.
    - It then cross-compiles from `packages/workflow` and writes `bin/SHA256SUMS`.
    - Artifact names (`workflow-<os>-<arch>`) and the release URL are unchanged.
  - **OpenCode signal log.** `packages/opencode-workflow-hooks`' signal-log default stops pointing into `tools/driver/`.
    - Its new default is `${XDG_STATE_HOME:-~/.local/state}/workflow/jev-signal-log.jsonl`, overridable by `WORKFLOW_JEV_SIGNAL_LOG`.
    - `tools/driver` readers use the same resolution (Assumption 11).
- Non-goals:
  - Publishing either npm package.
  - CI, `go.work`, or root npm workspaces (Assumption 8).
  - Changing package runtime behaviour beyond the signal-log default.
  - The package's runtime read of `docs/lab/RESEARCH/.../proofs` in `batch_aggregator.py`. It is not a `tools/` reference, so the rule allows it. Assumption 12 records it as a known wart.

### Domain: Tools (`tools/<name>/`)

- Owns: maintainer and automation tooling.
  - `transcript`, `driver`, `quality` (without its catalogue), `jev-variants`, `interception`, `release`, `cloud-env`.
- Contract:
  - Tools may reference packages and each other.
  - `tools/README.md` states the rule and indexes each tool with a one-line purpose.
  - Paths that already-deployed environments fetch do not move:
    - the raw URL `.../master/tools/cloud-env/bootstrap-workflow-skills.sh`;
    - `~/.cache/workflow-plugin/tools/driver/check_skills.py`;
    - the systemd unit's `%REPO%/tools/quality/server.py`.
- Non-goals:
  - Retiring `tools/quality` or its legacy service.
  - Restructuring tool internals.

### Domain: Maintainer skills (`.claude/skills/`)

- Owns: the former lab skills, as Claude Code project skills.
  - `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`.
- Contract:
  - **Moved intact.** Each skill directory moves with its `SKILL.md`, `briefs/`, `principles.md` and `reference.md`. The existing `name:` frontmatter works unchanged.
  - **Commands resolve from the repo root.** Repo-relative commands (`tools/...`) work as written, because the repo root is the working context.
  - **Invariant 7 is restated.** In ARCHITECTURE it becomes "core never depends on maintainer skills". The existing non-invoking prose mentions in core skills stay: `iterate` in `execute`, `workflow-tuning` in `comprehensive-review`.
  - **`lab-proposal` is retired** (Assumption 7). Live links to lab skill paths are repointed.
- Non-goals:
  - Distributing these skills to plugin users, cloud installs or OpenCode installs.
  - Changing skill behaviour.

## Architectural Implications

These stable docs become stale. Each phase updates the ones it invalidates.

- `docs/ARCHITECTURE.md`: the component map, the lab skill rows, invariant 7, and the Stable References into `plugins/workflow-lab/`.
- `docs/OVERVIEW.md`: "ten skills across two plugins", the Lab plugin section, and the `docs/lab/` note on where lab skills live.
- `docs/design/05-distribution.md`: the Layout table, the per-harness config paths, and the Release paragraph. Its "Not in this round: monorepo reorganisation" line is replaced by a Layout section stating the three-kind rule.
- `docs/design/system-architecture.md`: the "Maintainer lab" row points at `.claude/skills/`.
- `docs/design/{01,03,07}-*.md`: these mention `tools/workflow` and `tools/hooklog` in path text.

History is not rewritten. `docs/plans/*` records, `docs/lab/` dated findings and proposals, and earlier `CHANGELOG.md` entries keep the old paths. They describe what was true then.

Compatibility:

- The installed plugin cache is a per-version copy of the whole repo. An old version's hooks call that version's own `tools/hooklog/spool.sh`, so installed plugins keep working.
- A user-pasted Cursor config that hard-codes an absolute `.../tools/hooklog/spool.sh`, as `cursor-hooks.example.json` showed, will break silently, because `spool.sh` exits 0. The Phase 2 CHANGELOG entry calls this out.

Sequencing: plan 12 (`plan/12-analytics-dashboard-overhaul`) is mid-flight, with two of five phases closed. It touches:

- `tools/workflow/**`;
- `tools/hooklog/tests/fixtures/`;
- `packages/opencode-workflow-hooks/{src,tests,README.md}`;
- in its Phases 4 and 5, `packages/workflow-analytics`.

Its Phase 3 adds a Go test that reads `tools/transcript/pricing.json`. That is test-only and exempt from the package rule, but Phase 2 here must repoint it at the moved depth if needed. See Decision 1.

## Decisions

### Decision 1: Sequencing against plan 12 and other in-flight branches

- Chosen:
  - **Phase 1 (lab collapse) may land on master at any time.** It touches no path in plan 12's diff. One trivial textual conflict is expected: Phase 1 adds a `CHANGELOG.md` entry and bumps the manifests, and plan 12's close-out probably does too. Whichever lands second resolves it by keeping both entries.
  - **Phases 2 and 3 start only after plan 12 has merged to master.** Phase 2 moves the module and hooklog. Phase 3 edits `packages/opencode-workflow-hooks` and the READMEs and tests of `packages/workflow-analytics`, which plan 12's later phases edit too.
  - **The gate is mechanical.** Refine for Phase 2, and again for Phase 3, checks that master contains plan 12's close-out record, `docs/plans/12-analytics-dashboard-overhaul.md`. Briefs are written only after that check passes.
- Move shape: each move lands as two commits.
  1. A rename-only `git mv` commit, with no content edits.
  2. A path-rewrite commit.

  Phase 2 records the exact rewrite command in `IMPLEMENTATION.md`.
- Rebase protocol for any other branch touching a moved path:
  1. Rebase onto master. Rename detection replays the branch's edits into the new location.
  2. Rerun the recorded rewrite over the branch's own new files. It covers the Go module path, `tools/hooklog` → `packages/hooklog`, and the catalogue path.
- Alternative not chosen: land the moves now, and have plan 12 rebase across them using the same protocol.
  - Rejected because another orchestrator is building plan 12 right now.
  - A module-path rewrite touches every `.go` file plan 12 edits, so it would turn plan 12's remaining three phases into conflict work.
  - The restructure has no deadline that justifies that cost.

## Assumption Ledger

### Assumption 1

- Question: Where do the "skills at root" go: the root `skills/` directory, or the project-level `.claude/skills/`?
- Answer chosen: `.claude/skills/`.
- Rationale:
  - The root `skills/` directory is what the `workflow` plugin ships to every user, cloud VM and OpenCode install. Putting maintainer-only skills there would distribute them.
  - `.claude/skills/` loads only inside this repo.
  - `.gitignore` does not ignore it.
- If wrong:
  - Phase 1 changes destination.
  - The install routes gain an exclusion list to keep these skills out of cloud and OpenCode installs.
  - `tools/driver` tests assert that exclusion.

### Assumption 2

- Question: Does the `workflow` plugin itself become `packages/workflow-plugin`, or stay at the repo root?
- Answer chosen: it stays at the repo root (`source: "./"`).
- Rationale:
  - Several things assume the root:
    - the marketplace contract;
    - installed caches;
    - the `curl .../master/install.sh` URL;
    - the pinned Codex copy;
    - the source-build fallback in `bin/workflow`.
  - A subdirectory source would shrink the install root to exclude `packages/hooklog` and `packages/workflow`. That would force `spool.sh` to be vendored into the plugin and would drop the source-build fallback.
  - The plugin is the shell that composes the packages.
- If wrong:
  - A further phase moves the plugin surface to `packages/workflow-plugin` and changes the marketplace `source`.
  - It vendors `spool.sh`.
  - It makes the release download the only binary path.
  - It requires a coordinated update of the Codex pin and `install.sh`.

  That is a separate design. **This assumption is the largest gap against the user's literal words.** The most visibly deployable unit stays out of `packages/`.

### Assumption 3

- Question: What are the binary's package directory and Go module path called?
- Answer chosen: `packages/workflow`, with module path `github.com/codyhamilton/workflow-plugin/packages/workflow`.
- Rationale:
  - The name matches `cmd/workflow` and the release asset names.
  - No `go install` URL and no ldflags reference the module path. Only `go.mod` and about 60 internal imports change.
- If wrong: rename it, for example to `packages/workflow-cli`. The cost is the same, and it is cheapest before Phase 2.

### Assumption 4

- Question: Is `tools/hooklog` a package?
- Answer chosen: yes. It becomes `packages/hooklog`.
- Rationale: every harness's hook config executes it at runtime from the installed plugin. It is the capture edge of design 02.
- If wrong: it stays in `tools/`, and the layout rule needs a named exception for it.

### Assumption 5

- Question: Do `tools/cloud-env` and `tools/driver/check_skills.py` move? Already-deployed Cursor cloud `environment.json` configs fetch them by raw URL and from the install cache.
- Answer chosen: neither moves.
- Rationale:
  - Both are maintainer-operated automation for the maintainer's own cloud environments.
  - Moving them breaks deployed commands.
  - There is no evidence of third-party users.
  - The only content change is dropping the lab opt-in.
- If wrong: cloud-env becomes `packages/cloud-env`, with a forwarding stub at the old raw URL kept for one release cycle.

### Assumption 6

- Question: Where does the scorer's catalogue live?
- Answer chosen: `packages/workflow/catalogue/{criteria.json,checks/}`.
- Rationale:
  - The catalogue's runtime consumer is the binary.
  - Leaving it in `tools/quality` keeps a package depending on a tool.
  - Moving `criteria.json` together with `checks/` preserves the directory shape that `LoadChecks` and `WORKFLOW_CHECKS_DIR` expect.
- If wrong: it becomes its own `packages/catalogue/`, and the same consumers repoint there.

### Assumption 7

- Question: Is `lab-proposal` collapsed with the rest of the lab, or retired?
- Answer chosen: retired.
- Rationale: its own `SKILL.md` says `white-paper` supersedes it, and the user asked for cleanup.
- If wrong: move it into `.claude/skills/` like the others. It is one directory.

### Assumption 8

- Question: Does a "proper monorepo" require CI, a `go.work`, root npm workspaces, or npm publishing?
- Answer chosen: no.
- Rationale:
  - "Independent deployable units" is satisfied by each package having its own manifest, a documented build, test and release, and an enforced dependency direction.
  - There is no CI today, and releases are a manual maintainer action (design 05).
  - There is one Go module and two npm packages with no shared dependencies.
- If wrong: a follow-up design adds CI that runs each package's Test field.

### Assumption 9

- Question: Do Cursor sessions in this repo also need the maintainer skills?
- Answer chosen: Claude Code project skills are the target.
- Rationale:
  - If the Cursor version in use does not read `.claude/skills/`, the fallback is a per-skill symlink, `.cursor/skills/<name>` → `../../.claude/skills/<name>`.
  - It is never a whole-directory symlink. This repo's own cloud bootstrap writes the gitignored `.cursor/skills/workflow/`, and a directory symlink would land that inside the tracked tree.
  - Phase 1's refine checks which case applies.
- If wrong: maintainers lack these skills in Cursor until the symlinks are added. Nothing user-facing changes.

### Assumption 10

- Question: Is `tools/quality` a tool, given that it is a deployed systemd service (`server.py` on 127.0.0.1:8765)?
- Answer chosen: it stays a tool.
- Rationale:
  - It is a superseded legacy service that the maintainer alone runs (designs 03 and 05).
  - Its unit path `%REPO%/tools/quality/server.py` stays valid.
  - Only its `sys.path` imports of `../hooklog` and its catalogue reads change.
- If wrong: it becomes `packages/quality-service`, with a unit path migration.

### Assumption 11

- Question: Where does the OpenCode package's Jev signal log default to? Today it is `tools/driver/.jev-signal-log.jsonl`, which is a runtime path into `tools/`.
- Answer chosen: `${XDG_STATE_HOME:-~/.local/state}/workflow/jev-signal-log.jsonl`, overridable by `WORKFLOW_JEV_SIGNAL_LOG`. `tools/driver` resolves it the same way.
- Rationale:
  - A package must not write into a tool's directory.
  - The installed plugin cache is no place for a growing log.
  - The XDG state directory sits beside the existing queue convention.
- If wrong: keep the old default and add a named exception to the layout check. Existing logs at the old path are not migrated in either case.

### Assumption 12

- Question: Does the package's runtime read of `docs/lab/RESEARCH/.../proofs` (in `batch_aggregator.py`) need fixing here?
- Answer chosen: no. The rule governs `tools/`, not `docs/`.
- Rationale: fixing it means relocating research proofs into the package. That is research-tree cleanup, which is out of scope.
- If wrong: a follow-up moves the proofs the package depends on into `packages/opencode-workflow-hooks/`.

## Open Questions

None. The ledger holds every scope-shaping choice, and Decision 1 fixes when Phases 2 and 3 start.

## Phases

There are three phases. Phase 1 is independent of plan 12. Phases 2 and 3 are gated by Decision 1.

Each outcome clause is tagged with how it is proven. All tagged clauses are required.

- **[test]**: a committed automated test or check in the existing suites.
- **[cmd]**: a command whose output `IMPLEMENTATION.md` records at phase close.
- **[judgement]**: a reviewer reads and confirms it. This tag is limited to prose docs describing the layout.

### Phase 1: Lab collapses into maintainer skills

- Why: lab skills run repo-checkout commands that cannot work from their plugin install root, and their install lists have drifted. As project skills they run where their commands resolve, and the drifted lists disappear.
- Outcome:
  - [cmd] `claude -p "/skills"`, run at the repo root on master, lists exactly these six project skills: `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`.
  - [cmd] `python3 tools/transcript/find.py --help`, the first command of the `transcript-parser` skill, exits 0 from the repo root.
  - [cmd] `.claude-plugin/marketplace.json` lists only `workflow`, and `test -e plugins` fails.
  - [test] The `tools/driver` tests pass with `LAB_SKILLS` replaced by a maintainer-skill list. They assert that `install.sh` in each mode (Claude local, Cursor local and cloud, OpenCode) and `tools/cloud-env/bootstrap-workflow-skills.sh`, run with `WORKFLOW_INSTALL_LAB=1` set, install none of those six skills.
  - [cmd] Searching live files for `plugins/workflow-lab` or `lab-proposal` returns no hits. Live files exclude `docs/plans/`, dated `docs/lab/{PROPOSALS,RESEARCH}/` files and earlier `CHANGELOG.md` entries.
  - [judgement] `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `docs/design/system-architecture.md` and `README.md` describe one plugin plus maintainer skills.
- Surfaces:
  - Skills: `plugins/workflow-lab/**` (removed); `.claude/skills/**` (new).
  - Manifests: `.claude-plugin/marketplace.json`; the version fields in `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` and `.codex-plugin/plugin.json`.
  - Install: `install.sh`; `tools/cloud-env/{bootstrap-workflow-skills.sh,README.md}`.
  - Driver: `tools/driver/{check_skills.py,README.md}`; `tools/driver/tests/{test_check_skills.py,test_install_route.py}`.
  - Other tools: `tools/jev-variants/README.md`.
  - Lab docs: `docs/lab/{README.md,JEV-METHODOLOGY.md,FINDINGS.md,RESEARCH/INDEX.md}`.
  - Stable docs: `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `docs/design/system-architecture.md`, `README.md`, `CHANGELOG.md`.
- Approach: known.
- Depends on: nothing. It may land before plan 12 merges.

### Phase 2: Runtime units become packages

- Why: the binary and the hook edge are what every user runs. While they sit in `tools/`, the directory name lies about them, and the binary's catalogue makes a shipped unit depend on a maintainer tool. Each outcome below proves the move broke none of the user-visible paths: source build, hook capture, release build.
- Outcome:
  - [cmd] `bin/workflow --version` builds from source and keeps its version.
    - Preconditions: master, an empty `~/.cache/workflow/<VERSION>/`, and `WORKFLOW_RELEASE_URL` pointed at an unreachable host.
    - Result: it builds from `packages/workflow` and prints the same version field as before the move.
  - [cmd] Hook events flow through the moved spool. A Claude Code session with the plugin installed from this commit writes `SessionStart` and `PreToolUse` events through `packages/hooklog/spool.sh` into the queue. `bin/workflow drain` then ships them to a local `workflow serve`, and `workflow status` reports no failure.
  - [cmd] `tools/release/build.sh` writes four binaries and `bin/SHA256SUMS`, with the analytics site embedded.
  - [test] These suites pass:
    - `go test ./...` in `packages/workflow`;
    - the Python suites of `packages/hooklog`, `tools/quality`, `tools/jev-variants`, `tools/release` and `tools/driver`;
    - `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs`;
    - the `packages/workflow-analytics` e2e suite.
  - [cmd] Old-path references are gone. Searching live files for `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks` and the path-segment forms (`'tools', 'hooklog'`, `"..", "..", "..", "quality"`, `../../../quality`) returns no hits.
    - Live files exclude `docs/plans/`, `docs/lab/` and earlier `CHANGELOG.md` entries.
    - The new CHANGELOG entry may name the old spool path.
- Surfaces:
  - Moves:
    - `tools/workflow/**` → `packages/workflow/**`, with `go.mod` and every internal import rewritten.
    - `tools/quality/{criteria.json,checks/**}` → `packages/workflow/catalogue/`.
    - `tools/hooklog/**` → `packages/hooklog/**`.
  - Hook configs: `hooks/{hooks,cursor,codex}.json`; `packages/hooklog/{cursor-hooks.example.json,cursor-mcp.example.json,codex-mcp.example.toml,README.md}`.
  - Build: `bin/workflow`, which is the step-4 source-build path; `tools/release/{build.sh,phase5_outcome.py,test_release.py}`; `.gitignore`.
  - Go tests: the `LoadChecks` and catalogue paths in `packages/workflow/**/*_test.go`, including `screen_wiring_test.go`; plan 12's `pricing.json` test, if depth-dependent.
  - Python path fixes, the `sys.path` and `parents[N]` lookups:
    - `tools/quality/{quality.py,server.py,hookevents.py,interventions.py,thresholds.py,executor_reports.py}`;
    - `tools/jev-variants/{jev_variants.py,build_corpus.py,runner.py,events.py}`;
    - `packages/hooklog/tests/*`.
  - TypeScript and Node tests: `packages/workflow-analytics/tests/{e2e,hosted}/global-setup.ts`; `packages/opencode-workflow-hooks/{tests/test_hooks.mjs,src/index.ts,README.md}`.
  - Skill prose:
    - the catalogue citation in `skills/execute/SKILL.md` and `skills/refine/templates/brief.md`;
    - `.claude/skills/jev-variants/SKILL.md`;
    - `.claude/skills/workflow-tuning/reference.md`.
  - Docs: `docs/design/{01,03,05,07}-*.md`, `README.md`, `CHANGELOG.md`, and the plugin manifest version bump.
- Approach: known. The moves follow Decision 1's two-commit shape.
- Depends on: Phase 1, and plan 12 merged to master.

### Phase 3: The layout contract is stated and enforced

- Why: without a check, the next unit guesses its directory again and adds another cross-tree path. The check makes the three-kind rule fail loudly instead of drifting, and the README fields make each package independently buildable by anyone reading it.
- Outcome:
  - [test] The layout check passes on master. It is one stdlib Python test under `tools/release/` and runs with that suite.
  - [test] The check fails, naming the file and the offending path, in each of these cases. The test suite covers each case with a fixture.
    1. An executed path in `hooks/*.json`, `.mcp.json`, `.codex-mcp.json` or `bin/workflow` resolves into `tools/` or `.claude/`.
    2. A non-exempt file under `packages/` contains a `tools/` path. "Non-exempt" means not a comment, Markdown, or test code or test config, as defined in the package contract.
    3. A file under `skills/` references `.claude/skills/`.
    4. A `packages/<name>/` lacks a README with the Consumers, Build, Test and Release fields.
    5. `.claude-plugin/marketplace.json` lists more than one plugin.
  - [test] `packages/opencode-workflow-hooks` resolves its signal-log default as Assumption 11 states, and `tools/driver` reads the same path.
  - [judgement] Both trees and the stable docs describe the new layout:
    - `tools/README.md` and `packages/README.md` index every directory under them, each with a one-line purpose.
    - `docs/design/05-distribution.md` has a Layout section stating the three-kind rule, in place of its "Not in this round" line.
    - `docs/ARCHITECTURE.md`'s component map shows the three kinds.
- Surfaces:
  - Check: the new layout test under `tools/release/`.
  - Indexes: `tools/README.md` and `packages/README.md` (new).
  - Package READMEs: the field blocks in `packages/{workflow,hooklog,workflow-analytics,opencode-workflow-hooks}/README.md`. `packages/workflow/README.md` is new.
  - Signal log: `packages/opencode-workflow-hooks/python/{batch_flush_cli.py,batch_aggregator.py}`; `packages/opencode-workflow-hooks/tests/test_batch.py`; the readers of `.jev-signal-log.jsonl` in `tools/driver`.
  - Go comments: `packages/workflow/internal/{facts/facts.go,scorer/jev.go}`, reworded only if the check's comment exemption needs them to be.
  - Docs: `docs/design/05-distribution.md`, `docs/ARCHITECTURE.md`.
- Approach: known.
- Depends on: Phase 2. That carries plan 12's merge gate, which Phase 3's own refine also checks per Decision 1.

Refine:

- Phases 1 and 3 are each small enough for one worker and may skip `refine`.
- Phase 2 needs `refine`. It spans the Go module, Python tooling, TypeScript and Node tests, and docs. Refine cuts the rename commit first, then parallel path-rewrite units by area.

## Provenance Notes

- **Posture.** This was a headless design, so there is no `PROVENANCE.md`. The Assumption Ledger carries every choice that would otherwise have been asked.
- **Grounding facts:**
  - Marketplace `source: "./"` makes the installed cache the whole repo, so packages are reachable from `${CLAUDE_PLUGIN_ROOT}`.
  - The binary cache is keyed on `bin/VERSION`.
  - No ldflags, install URL or release script carries the module path.
  - There is no `.github/`, CI, `go.work`, root `package.json` or Makefile.
  - `LoadChecks(dir)` reads `dir/criteria.json` and `dir/checks/*.json`.
- **Rejected alternatives:**
  - A `packages/` directory for every tool. That erases the distinction the user drew.
  - `packages/workflow-bin` as the binary's directory. The directory follows the binary's name.
  - A whole-directory `.cursor/skills` symlink (see Assumption 9).
- **Why the workflow and hooklog moves share a phase.** Moving `packages/workflow` and `packages/hooklog` together keeps the Go tests' sibling-relative paths valid.
- **Drift that Phase 1 removes rather than fixes:** the lab manifest descriptions, the four-entry `LAB_SKILLS` list, and `docs/lab/FINDINGS.md`'s version number.
- **`docs/lab/` stays.** It is the Workflow Optimiser's notebook, not a lab-plugin asset.
- **Adversarial pass** (clean context). Applied:
  - Corrected the catalogue contract: `criteria.json` moves with `checks/`.
  - Completed the Phase 2 surfaces: `tools/quality` imports, `test_hooks.mjs`, and the jev-variants skill.
  - Made the Phase 3 check consistent with master. Runtime-only scope, explicit exemptions, and the signal-log default fixed.
  - Corrected the Codex hook shape.
  - Made the Cursor symlink per-skill.
  - Added `docs/lab/JEV-METHODOLOGY.md`.
  - Made the Phase 1 outcomes command-checkable.
  - Excluded `CHANGELOG.md` history from the searches.
  - Ledgered `tools/quality`.
  - Corrected the claim that the OpenCode package's docs read is test-only.
  - Dropped `evals/` and docs that carry no moved paths from the Phase 2 surfaces.
- **Artifact feedback.** The first feedback flagged problem coverage, surface specificity, outcome checkability and proof labelling below the tenant's p25. The Problem's why-now and cleanup scope, the explicit surface lists, and the proof tags answer those.
