# Monorepo Restructure: Lab Collapse, Packages and Tools

## Intent

User request, verbatim:

> Have an agent work on a background design - collapsing workflow-lab, which should not be its own plugin (just skills at root, they're maintainer-only), as well as cleaning up the repo and distinguishing tools from packages (workflow bin to my mind is a package), organising the repo into a proper monorepo with packages/ containing the various packages it holds as independent deployable units

Added intent, verbatim:

> Ok we have some other issues to deal with. There should be an open plan for restructuring the plugin? We have to add to that. Cursor is not actually loading the plugin correctly nor triggering hooks. The commands in the hooks file for cursor aren't right, the scripts anyway run from plugin root so only need `./script/...` to execute, plus we should move the workflow plugin into the packages/ dir as a package (it's a plugin referenced from the marketplace entry).

> plus we have a further plan for renaming across the board to yakka - I think it should be integrated into this plan

> maybe instead of packages, we put the plugin in `plugins/yakka`

The rename was a separate design (`docs/plans/15-rename-to-yakka/`). Its intent is now part of this plan, verbatim:

> Help come up with a better name for this app. We've got `workflow` which is terribly generic. `miniflow` was another thought. It's all about the plan/design/refine/execute SDLC workflow

> It makes more sense to keep yakka for both

> do the /workflow:design

That folder is no longer a design. Its bounded scope lives here.

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
- **Cursor is not loading this plugin, and its hooks are not firing.** That is a defect to close, not a path typo to tidy.
  - `.cursor-plugin/marketplace.json` lists `workflow` with `source: "./"`, so the plugin root Cursor resolves is the repo root. Cursor's marketplace resolution looks for `<source>/.cursor-plugin/plugin.json` and discovers components inside that directory. The repo root is not a plugin directory among others; the lab entry already shows the shape that works (`source: "plugins/workflow-lab"`).
  - `.cursor-plugin/plugin.json` points `hooks` at `./hooks/cursor.json`. Cursor's own default discovery path is `hooks/hooks.json`. The manifest override may be why nothing fires; the phase outcome is that hooks fire, whatever the file has to be named for Cursor to read it.
  - Every command in `hooks/cursor.json` is `bash "${CURSOR_PLUGIN_ROOT}/tools/hooklog/spool.sh" ...` or the same prefix on `bin/workflow`. There is no `script/` directory. The sessionStart entry also prefetches `bin/workflow --version`.
- **The product name is `workflow`.** It is too generic to search for, and in this repo it is also the word for the method. The plugin, the binary, the MCP server, the skill prefix, about 40 environment variables, the commit trailers and several directories all use it. The chosen name is `yakka`. Every later surface (releases, the analytics site, the remote service) costs more the longer the rename waits.

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

After this change the repo has the plugin, the packages and the tools, plus maintainer skills that are not installed:

- **Plugin.** The workflow plugin lives at `plugins/yakka`. That directory is the install root: skills, harness manifests, hooks, and the `script/` directory its Cursor hooks execute. It is not a package.
- **Packages.** `packages/<name>/` holds every independently buildable or deployable unit other than the plugin. Each carries its own manifest or README, which states how it is built, tested and released. The Go binary is one of these (`packages/workflow`, then `packages/yakka`).
- **Tools.** `tools/<name>/` holds maintainer and automation tooling. No runtime code path or config in the plugin or in a package resolves into `tools/`.

The lab plugin is gone. Its skills become Claude Code project skills under `.claude/skills/`, which load only when someone works inside this repo. Each marketplace lists one plugin.

After the rename phases the product is `yakka` everywhere it names itself. Readers still accept the old `Workflow-*` trailers and the old report fence, because git history and old transcripts cannot change. Installed setups get no other backward compatibility. They update by hand, following the CHANGELOG migration guide.

Dependency direction:

- `plugins/yakka` → packages.
- Packages → packages.
- Tools → anything.

A committed check enforces this direction (Phase 4).

### Domain: Plugin (`plugins/yakka`)

- Owns, inside `plugins/yakka`:
  - `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`.
  - `skills/` (the six core skills).
  - `hooks/{hooks,cursor,codex}.json`, `.mcp.json`, `.codex-mcp.json`.
  - `script/` — the scripts Cursor's hooks execute.
  - `bin/{workflow,VERSION,SHA256SUMS,RELEASE_URL}`, until the rename phases replace `workflow` with `yakka`.
- Owns, at the repo root:
  - `.cursor-plugin/marketplace.json` and `.claude-plugin/marketplace.json`. Cursor's multi-plugin layout keeps the marketplace manifest at the repo root and the plugin manifest inside the package.
  - `install.sh`.
- Contract:
  - Each marketplace lists exactly one plugin. Its `source` is `plugins/yakka`, not `"./"` and not the repo root. The Claude entry uses a subdir source for that same directory. Until the rename phases, the plugin name stays `workflow` and the marketplace name and repo URL stay as they are. The directory is `plugins/yakka` from Phase 3, before those renames.
  - Cursor loads `plugins/yakka`. Component discovery runs inside it. A Cursor session with the plugin installed from that entry fires hooks.
  - Cursor hook commands are plugin-root-relative `./script/...`. They do not use `${CURSOR_PLUGIN_ROOT}`, an absolute path, or a path that leaves `plugins/yakka`. Arguments stay as they are today (`--harness cursor --event <event>` on the spool; the detached `--version` prefetch stays a second command). The scripts those commands name exist under `plugins/yakka/script/` and are what actually runs. Cursor runs them with `plugins/yakka` as the working directory.
  - Claude and Codex hook commands keep their shape: `bash "<root>/...spool.sh" --harness <h> [--event <E>]`, Codex with no `--event`. `<root>` is `plugins/yakka`. The path they name is inside that directory (the same scripts `script/` provides, or `bin/` for the prefetch), not a sibling the install does not contain.
  - `packages/hooklog` remains the hook-edge package. `plugins/yakka` contains the copies its hooks execute, because a marketplace install of that directory is the whole install root and does not include `packages/`. A repo checkout still source-builds the binary from `packages/workflow`, then `packages/yakka`.
  - `bin/workflow` keeps its four-step resolution and its cache key, `${XDG_CACHE_HOME:-~/.cache}/workflow/<bin/VERSION>/workflow-<os>-<arch>`, until the rename phases. Its step-4 source build reads `packages/workflow` when the checkout contains it. A marketplace install that contains only `plugins/yakka` uses the released binary; it does not contain the Go module.
  - `bin/VERSION` is not bumped before the rename phases. Cached binaries stay valid, and the version field of `workflow --version` is unchanged; only the commit field differs.
  - Plugin version bumps:
    - A phase that changes a shipped plugin file and can merge on its own bumps the plugin manifests one minor version.
    - The rename phases move every manifest to the next major once, together, with one `CHANGELOG.md` entry. They do not also take a minor.
    - The Claude, Cursor and Codex manifests move together.
  - `install.sh` (every mode) and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only. The `WORKFLOW_INSTALL_LAB` opt-in and every lab-install path are removed. Cursor install materializes `plugins/yakka`, not the repo root.
  - Core skills may cite tools and paths in prose, as `execute` cites `tools/driver/`. They never reference `.claude/skills/` or a maintainer skill by path.
- Non-goals:
  - Changing hook events, MCP tool names or binary behaviour, other than the names the rename phases change.
  - Retiring `install.sh`.
  - Aliasing the old plugin name once the rename lands.

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

### Domain: Names

The rename applies on the layout above. Decision 3 records what is kept and what is retargeted. The contracts a phase has to prove:

- The plugin name is `yakka` in every plugin manifest. Every marketplace manifest is named `yakka` and lists exactly one plugin, `yakka`, whose `source` is `plugins/yakka`. The directory does not move again during the rename.
- The Go module is `github.com/codyhamilton/yakka/packages/yakka`, command `cmd/yakka`. `bin/yakka` keeps the four-step resolution. Cache, release assets and state directories use `yakka` as in the path table below. `bin/VERSION` is bumped, so no tag serves both asset names. `yakka --version` prints `yakka <version> <commit>`. MCP `serverInfo.name` is `yakka`.
- Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`. No code reads the old env vars or the old state paths.

  | Was | Becomes |
  |---|---|
  | `~/.local/share/workflow/{queue,serve}` | `~/.local/share/yakka/{queue,serve}` |
  | `~/.config/workflow/client.toml` | `~/.config/yakka/client.toml` |
  | `~/.cache/workflow/` | `~/.cache/yakka/` |
  | `~/.local/state/workflow/` | `~/.local/state/yakka/` |
  | `~/.local/share/workflow-plugin/hooklog` | `~/.local/share/yakka/hooklog` |
  | `~/.cache/workflow-plugin` (cloud-env checkout) | `~/.cache/yakka/src` |

- npm: `@codyhamilton/yakka-analytics` (private; Pages project `yakka-analytics`) and `@codyhamilton/opencode-yakka-hooks` (export `yakka-signals.json`, plugin export `YakkaSignalsPlugin`). Analytics `localStorage` keys become `yakka-analytics-base`, `yakka-analytics-key` and `yakka-analytics-views:*`.
- Writers emit `Yakka-Phase: <slug>:<n>`, `Yakka-Phase: <slug>:done`, a PR body starting `Yakka-Plan: docs/plans/<NN>-<slug>/`, and a `yakka-report` fence. Readers accept `Workflow-Phase` / `Yakka-Phase`, `Workflow-Plan:` / `Yakka-Plan:`, and both fences, permanently, through one shared key list in `tools/driver/`.
- Repo URL `https://github.com/codyhamilton/yakka` everywhere a repo URL appears. `install.sh` installs Cursor to `~/.cursor/plugins/local/yakka` from `plugins/yakka`. The bootstrap script is `tools/cloud-env/bootstrap-yakka-skills.sh`. There is no forwarding stub at the old URL.
- The CHANGELOG rename entry is the migration guide: the full `WORKFLOW_*` → `YAKKA_*` map, every state path above, per-harness remove-then-install commands, the `.gitignore` change (`.cursor/skills/workflow/` → `.cursor/skills/yakka/`), the MCP-prefix and skill-prefix note, and the maintainer actions (repo rename, release publish, serve data-dir move, `client.toml`, harness reinstall, cloud `environment.json`, optional Pages project, optional checkout rename).
- The residual-name scan from the folded design is the done check. Its exclusions, forbidden patterns and allowed exceptions are unchanged. Refine decides whether it is a committed script or a one-off command; the patterns stay these.

Maintainer actions outside the repo are listed in that guide and are not phases. This plan's own trailers may be `Workflow-Phase:` because it runs under the installed `workflow` plugin; the dual-read rule makes that harmless.

- Non-goals: publishing the release or the npm packages; migrating data; rewriting commits, PR bodies or recorded events; renaming the legacy quality service beyond its catalogue path; renaming the common noun.

## Architectural Implications

These stable docs become stale. Each phase updates the ones it invalidates.

- `docs/ARCHITECTURE.md`: the component map, the lab skill rows, invariant 7, and the Stable References into `plugins/workflow-lab/`.
- `docs/OVERVIEW.md`: "ten skills across two plugins", the Lab plugin section, and the `docs/lab/` note on where lab skills live.
- `docs/design/05-distribution.md`: the Layout table, the per-harness config paths, and the Release paragraph. Its "Not in this round: monorepo reorganisation" line is replaced by a Layout section stating packages, tools, and the plugin at `plugins/yakka`.
- `docs/design/system-architecture.md`: the "Maintainer lab" row points at `.claude/skills/`.
- `docs/design/{01,03,07}-*.md`: these mention `tools/workflow` and `tools/hooklog` in path text.
- The rename phases then rewrite the contract sections of those docs, plus `docs/design/04-advisory-surface.md` and `docs/design/system-architecture.md`, to the yakka names, and add the trailer dual-read rule to the PR Artifact Seam and the phase-boundary contract.

History is not rewritten. `docs/plans/*` records, `docs/lab/` dated findings and proposals, and earlier `CHANGELOG.md` entries keep the old paths. They describe what was true then.

Compatibility:

- An already-installed plugin is a copy of whatever that version's marketplace source was. Old installs keep running that copy until someone installs the package. They are not rewritten.
- A user-pasted Cursor config that hard-codes an absolute `.../tools/hooklog/spool.sh`, as `cursor-hooks.example.json` showed, will break silently, because `spool.sh` exits 0. The Phase 2 CHANGELOG entry calls this out.
- After the rename, an existing install keeps running `workflow` until it is removed and `yakka` is installed. Both enabled at once records every hook event twice. Anything that sets `WORKFLOW_*`, or relies on data under the old paths, is ignored by the new binary. Cloud environments that fetch the old bootstrap URL stop working. The CHANGELOG guide is the only migration. No code reads the old paths, and recorded events are not rewritten.

Sequencing: plan 12 (`plan/12-analytics-dashboard-overhaul`) is mid-flight, with two of five phases closed. It touches:

- `tools/workflow/**`;
- `tools/hooklog/tests/fixtures/`;
- `packages/opencode-workflow-hooks/{src,tests,README.md}`;
- in its Phases 4 and 5, `packages/workflow-analytics`.

Its Phase 3 adds a Go test that reads `tools/transcript/pricing.json`. That is test-only and exempt from the package rule, but Phase 2 here must repoint it at the moved depth if needed. See Decision 1.

Plan 14 has merged. Plan 12's close-out record is on master (`docs/plans/12-analytics-dashboard-overhaul.md`), so Decision 1's gate is already met.

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
  - Rejected because another orchestrator was building plan 12 when this decision was made.
  - A module-path rewrite would have touched every `.go` file plan 12 edited.
- The gate is met. Master contains `docs/plans/12-analytics-dashboard-overhaul.md`. Phases 2 and later are not waiting on plan 12.

### Decision 2: The plugin is `plugins/yakka`, and Cursor hooks are `./script/...`

- Chosen:
  - The plugin leaves the repo root and lives at `plugins/yakka`. It is not under `packages/`. Marketplace entries use that path as `source`.
  - Cursor hook commands are plugin-root-relative `./script/...`, run with `plugins/yakka` as the working directory.
  - `packages/hooklog` stays a separate package. `plugins/yakka` contains the scripts its own hooks run, because the install root is that directory.
  - The Go binary stays on its own move: `packages/workflow`, then `packages/yakka`.
- Supersedes Assumption 2, which had kept the plugin at the repo root with `source: "./"`.
- Supersedes the earlier reading of the added intent that put the plugin under `packages/`. The user closed that: `plugins/yakka`.
- Also supersedes the rename design's marketplace contract `source: "./"`. The source is `plugins/yakka`. The rename changes the plugin's name, not that path.

### Decision 3: The yakka rename is phases of this plan

- Chosen: the scope bounded by `docs/plans/15-rename-to-yakka/` is Phases 5–7 here. That folder is not a second design and is not built on its own.
- Kept from that design, unchanged:
  - One name, `yakka`, for the product, the binary and the service. Not a split name.
  - The GitHub repo, the marketplaces, the Go module and every repo URL become `yakka`. The repo rename itself stays a maintainer action outside this repo.
  - `WORKFLOW_*` becomes `YAKKA_*` with the same suffix, except `WORKFLOW_QUALITY_`. No fallback, no data migration. State paths move as that design's table says. The CHANGELOG entry is the migration guide.
  - Writers emit `Yakka-Phase:`, `Yakka-Plan:` and a `yakka-report` fence. Readers accept the old and new forms permanently.
  - The legacy quality service keeps its names, apart from the catalogue path. History is not rewritten. The common noun "workflow" stays.
  - npm packages stay scoped `@codyhamilton/`. `localStorage` keys rename. Analytics series may split at the rename.
  - The residual-name scan, its exclusions and its allowed exceptions are that design's scan, unchanged. It is the definition of done for the rename phases.
- Retargeted because the plugin is now a package:
  - Names apply inside `plugins/yakka`. Marketplace `source` stays `plugins/yakka`.
  - Cursor hook commands stay `./script/...` through the rename. Claude and Codex commands change only the binary path, to `plugins/yakka/bin/yakka`.
  - The binary package is `packages/yakka`, from `packages/workflow`. That directory is the Go module, not the plugin.
- Sequencing: Phases 5–7 run after Phase 4, on the layout this plan has just stated. They ship as one cut: one major version, one migration guide. Directory moves in Phases 2–4 use today's `workflow` names so those phases' outcomes stay checkable before the rename.
- The rename design's "rejected: folding into plan 13" is reversed by the added intent.

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

**Superseded by Decision 2.** The plugin moves to `plugins/yakka`, and the marketplace source is that path. The original answer is kept so the reversal stays visible.

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

None. The plugin directory was the open question. It is `plugins/yakka` (Decision 2). The Go binary remains `packages/workflow` through Phase 4 and `packages/yakka` from Phase 5.

## Phases

There are seven phases. Phase 1 can land on its own. Phases 2–4 are the layout, and Decision 1's gate on them is already met. Phases 5–7 are the rename and ship as one cut after Phase 4.

Where a later phase renames or moves something an earlier phase proved, the later outcome is the one that holds at the end. The earlier outcome is what is true when that phase closes.

Each outcome clause is tagged with how it is proven. All tagged clauses are required.

- **[test]**: a committed automated test or check in the existing suites.
- **[cmd]**: a command whose output `IMPLEMENTATION.md` records at phase close.
- **[judgement]**: a reviewer reads and confirms it. This tag is limited to prose docs describing the layout.

### Phase 1: Lab collapses into maintainer skills

- Why: lab skills run repo-checkout commands that cannot work from their plugin install root, and their install lists have drifted. As project skills they run where their commands resolve, and the drifted lists disappear.
- Outcome:
  - [cmd] `claude -p "/skills"`, run at the repo root on master, lists exactly these six project skills: `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`.
  - [cmd] `python3 tools/transcript/find.py --help`, the first command of the `transcript-parser` skill, exits 0 from the repo root.
  - [cmd] `.claude-plugin/marketplace.json` lists only `workflow`, and `test -e plugins` fails. Phase 3 is what creates `plugins/yakka`; this clause is the Phase 1 close, not the final layout.
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
- Depends on: nothing.

Units:

- 1-01 Lab collapse. Brief: `briefs/1-01-lab-collapse.md`. Depends on: nothing. Runs alongside: nothing.

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
  - Hook configs: `hooks/{hooks,codex}.json` repoint at `packages/hooklog`. `hooks/cursor.json` is repointed only far enough that it no longer names `tools/hooklog`; Phase 3 replaces its commands. `packages/hooklog/{cursor-hooks.example.json,cursor-mcp.example.json,codex-mcp.example.toml,README.md}`.
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
- Depends on: Phase 1. Plan 12 is already on master.

Units:

- 2-01 Package renames (git mv only). Brief: `docs/plans/13-monorepo-restructure/briefs/2-01-package-renames.md`. Depends on: Phase 1. Runs alongside: nothing.
- 2-02 Go workflow package and bin resolver. Brief: `docs/plans/13-monorepo-restructure/briefs/2-02-go-workflow-package.md`. Depends on: 2-01. Runs alongside: 2-03, 2-04, 2-05.
- 2-03 Hook configs and hooklog package. Brief: `docs/plans/13-monorepo-restructure/briefs/2-03-hooks-and-hooklog.md`. Depends on: 2-01. Runs alongside: 2-02, 2-04, 2-05.
- 2-04 Python maintainer tooling paths. Brief: `docs/plans/13-monorepo-restructure/briefs/2-04-python-tooling-paths.md`. Depends on: 2-01. Runs alongside: 2-02, 2-03, 2-05.
- 2-05 JavaScript and Node test consumers. Brief: `docs/plans/13-monorepo-restructure/briefs/2-05-js-and-node-consumers.md`. Depends on: 2-01. Runs alongside: 2-02, 2-03, 2-04.
- 2-06 Prose, stable docs, and changelog. Brief: `docs/plans/13-monorepo-restructure/briefs/2-06-prose-docs-and-closeout-prep.md`. Depends on: 2-02, 2-03, 2-04, 2-05. Runs alongside: nothing.
- 2-07 Residual path comments. Brief: `docs/plans/13-monorepo-restructure/briefs/2-07-residual-path-comments.md`. Depends on: 2-06. Runs alongside: nothing.

### Phase 3: Cursor loads `plugins/yakka` and its hooks fire

- Why: Cursor is not loading this plugin, and the hooks file's commands never run. The plugin is a marketplace entry at `plugins/yakka`, and those commands are `./script/...` because Cursor runs them from that directory.
- Outcome:
  - [cmd] Both marketplace entries' `source` for the core plugin is `plugins/yakka`: `.cursor-plugin/marketplace.json` and `.claude-plugin/marketplace.json`. That directory contains `.cursor-plugin/plugin.json`, `skills/` and the hooks file the manifest names. Neither `source` is `"./"` or the repo root. The plugin is not under `packages/`.
  - [cmd] Every command in the Cursor hooks file is plugin-root-relative `./script/...`. None contains `${CURSOR_PLUGIN_ROOT}`, `tools/hooklog` or an absolute path. The named scripts exist under `plugins/yakka/script/`.
  - [cmd] With the working directory set to `plugins/yakka`, the spool command from that file, given a `sessionStart` payload, exits 0 and writes an event into the queue. The detached `--version` command from that file is the other `./script/...` entry.
  - [cmd] Installing that marketplace entry and opening a Cursor session loads the plugin's skills and fires a hook. The fired command is one of those `./script/...` entries, and the event lands in the queue. `workflow drain` to a local `workflow serve` then ships it, and `workflow status` reports no failure.
  - [test] The install-route tests show Cursor install copies `plugins/yakka`, and the installed tree contains `script/` and the hooks file. Claude and Codex hook commands in that tree resolve inside `plugins/yakka`.
- Surfaces:
  - `plugins/yakka`: skills, harness manifests, `hooks/`, `.mcp.json`, `.codex-mcp.json`, `bin/`, `script/`.
  - Repo-root marketplaces: `.cursor-plugin/marketplace.json`, `.claude-plugin/marketplace.json`.
  - Install: `install.sh` and the Cursor branch of `tools/driver` install tests.
  - Hook edge: the scripts under `plugins/yakka/script/`, taken from `packages/hooklog` and `bin/workflow` so an install of `plugins/yakka` does not need `packages/`.
  - Docs: the per-harness path row in `docs/design/02-edge-capture.md` and `docs/design/05-distribution.md`, and `CHANGELOG.md`.
- Approach: known. The path, the command shape and the move are decided. The hooks filename is whatever Cursor must read for the session outcome to hold.
- Depends on: Phase 2, so `script/` wraps the moved hook edge. It can be briefed against `plugins/yakka`.

Units:

- 3-01 Cursor plugin and hook scripts. Brief: `docs/plans/13-monorepo-restructure/briefs/3-01-cursor-plugin.md`. Depends on: Phase 2. Runs alongside: nothing.

### Phase 4: The layout contract is stated and enforced

- Why: without a check, the next unit guesses its directory again and adds another cross-tree path. The check makes the packages, tools and `plugins/yakka` rule fail loudly instead of drifting, and the README fields make each package independently buildable by anyone reading it.
- Outcome:
  - [test] The layout check passes on master. It is one stdlib Python test under `tools/release/` and runs with that suite.
  - [test] The check fails, naming the file and the offending path, in each of these cases. The test suite covers each case with a fixture.
    1. An executed path in the plugin's hook configs, its MCP configs or `bin/workflow` resolves into `tools/` or `.claude/`.
    2. A non-exempt file under `packages/` contains a `tools/` path. "Non-exempt" means not a comment, Markdown, or test code or test config, as defined in the package contract.
    3. A file under `skills/` references `.claude/skills/`.
    4. A `packages/<name>/` lacks a README with the Consumers, Build, Test and Release fields.
    5. Either marketplace lists more than one plugin, or its core-plugin `source` is not `plugins/yakka`.
    6. A command in the Cursor hooks file is not plugin-root-relative `./script/...`.
  - [test] `packages/opencode-workflow-hooks` resolves its signal-log default as Assumption 11 states, and `tools/driver` reads the same path.
  - [judgement] Both trees and the stable docs describe the new layout:
    - `tools/README.md` and `packages/README.md` index every directory under them, each with a one-line purpose.
    - `docs/design/05-distribution.md` has a Layout section stating packages, tools and `plugins/yakka`, in place of its "Not in this round" line.
    - `docs/ARCHITECTURE.md`'s component map shows `plugins/yakka`, the packages and the tools.
- Surfaces:
  - Check: the new layout test under `tools/release/`.
  - Indexes: `tools/README.md` and `packages/README.md` (new).
  - Package READMEs: the field blocks in `packages/{workflow,hooklog,workflow-analytics,opencode-workflow-hooks}/README.md`. `packages/workflow/README.md` is new. `plugins/yakka` is not a package and does not carry those fields.
  - Signal log: `packages/opencode-workflow-hooks/python/{batch_flush_cli.py,batch_aggregator.py}`; `packages/opencode-workflow-hooks/tests/test_batch.py`; the readers of `.jev-signal-log.jsonl` in `tools/driver`.
  - Go comments: `packages/workflow/internal/{facts/facts.go,scorer/jev.go}`, reworded only if the check's comment exemption needs them to be.
  - Docs: `docs/design/05-distribution.md`, `docs/ARCHITECTURE.md`.
- Approach: known.
- Depends on: Phase 3.

Units:

- 4-01 Layout contract. Brief: `docs/plans/13-monorepo-restructure/briefs/4-01-layout-contract.md`. Depends on: Phase 3. Runs alongside: nothing.

### Phase 5: Runtime runs as yakka

- Why: the binary and hooks are what every harness executes, so they have to work under the new names before anything else points at them.
- Outcome:
  - [cmd] From a `HOME` with no `yakka` state: `bin/yakka --version` prints `yakka <version> <commit>` through a source build; an event passed to the spool lands in `~/.local/share/yakka/queue`; `bin/yakka drain` delivers it to a keyless `bin/yakka serve` under `~/.local/share/yakka/serve/local/`; `bin/yakka mcp` answers `initialize` with `serverInfo.name = "yakka"`.
  - [test] Every suite passes, including `tools/quality` and the analytics e2e setup loading `packages/yakka/catalogue`.
  - [cmd] The residual-name scan reports nothing under the runtime packages (`packages/yakka`, `packages/hooklog`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`), `plugins/yakka`'s `bin/`, `hooks/`, `script/` and MCP configs, and `tools/release/`. Plugin manifests and `skills/` are Phase 6. Catalogue citations in the skills are repointed here too.
  - [cmd] Every Cursor hook command is still plugin-root-relative `./script/...`.
- Surfaces: `packages/workflow` → `packages/yakka`; `packages/hooklog`; `packages/workflow-analytics` → `packages/yakka-analytics`; `packages/opencode-workflow-hooks` → `packages/opencode-yakka-hooks`; `tools/release/`; `plugins/yakka`'s hooks, `script/` and `bin/`; the catalogue path in `tools/quality` and in `skills/execute` and `skills/refine`.
- Approach: known.
- Depends on: Phase 4.

Units:

- 5-01 Package renames (git mv only). Brief: `docs/plans/13-monorepo-restructure/briefs/5-01-package-renames.md`. Depends on: Phase 4. Runs alongside: nothing.
- 5-02 Go yakka runtime package. Brief: `docs/plans/13-monorepo-restructure/briefs/5-02-go-yakka-runtime.md`. Depends on: 5-01. Runs alongside: 5-04, 5-06.
- 5-03 Plugin `bin/yakka` and hook edge. Brief: `docs/plans/13-monorepo-restructure/briefs/5-03-plugin-bin-and-hook-edge.md`. Depends on: 5-02. Runs alongside: nothing.
- 5-04 npm runtime packages. Brief: `docs/plans/13-monorepo-restructure/briefs/5-04-npm-runtime-packages.md`. Depends on: 5-01. Runs alongside: 5-02, 5-06.
- 5-05 Release tooling, residual scan, package index. Brief: `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md`. Depends on: 5-02, 5-03, 5-04, 5-07. Runs alongside: nothing.
- 5-07 Residual runtime names outside release. Brief: `docs/plans/13-monorepo-restructure/briefs/5-07-residual-runtime-names.md`. Depends on: 5-02, 5-03, 5-04. Runs alongside: nothing.
- 5-06 Quality catalogue path and skill citations. Brief: `docs/plans/13-monorepo-restructure/briefs/5-06-quality-catalogue-and-skill-citations.md`. Depends on: 5-01. Runs alongside: 5-02, 5-04.

### Phase 6: Plugin and plan protocol are yakka

- Why: this is the name users see and type, and the protocol every later plan writes.
- Outcome:
  - [cmd] Every plugin and marketplace manifest names `yakka` at the next major version, and each marketplace `source` is still `plugins/yakka`.
  - [test] `tools/driver` resolves a branch whose closing commits carry `Workflow-Phase: <slug>:1` and `Yakka-Phase: <slug>:2` to phase 3 through `resolve`, `status` and `trigger`, and `report.py` parses both fences.
  - [cmd] The trailer-completeness eval passes for each key.
  - [test] `install.sh` in each mode, and `tools/cloud-env/bootstrap-yakka-skills.sh`, install into the `yakka`-named locations, with Cursor installing `plugins/yakka`.
  - [cmd] The residual-name scan reports nothing under `skills/`, `.claude/skills/`, the plugin manifests, `install.sh`, `.gitignore` or `tools/`.
  - [judgement] Each reading skill writes the `Yakka-*` forms and names the legacy forms it accepts in one sentence.
- Surfaces: `plugins/yakka` manifests and `skills/`; `.claude/skills/workflow-tuning` → `yakka-tuning`; `tools/driver/`; `tools/cloud-env/`; `tools/transcript/` and `tools/jev-variants/` identifiers; `install.sh`; `.gitignore`; `evals/scenarios/trailer-completeness/`.
- Approach: known.
- Depends on: Phase 5.

Units:

- 6-01 Plugin and marketplace manifests. Brief: `docs/plans/13-monorepo-restructure/briefs/6-01-plugin-manifests.md`. Depends on: Phase 5. Runs alongside: `6-02`, `6-04`, `6-05`.
- 6-02 Core skills protocol and `yakka-tuning`. Brief: `docs/plans/13-monorepo-restructure/briefs/6-02-skills-and-tuning-rename.md`. Depends on: Phase 5. Runs alongside: `6-01`, `6-04`, `6-05`.
- 6-04 Install routes and cloud bootstrap. Brief: `docs/plans/13-monorepo-restructure/briefs/6-04-install-and-cloud-env.md`. Depends on: Phase 5. Runs alongside: `6-01`, `6-02`, `6-05`.
- 6-05 Transcript and jev-variants identifiers. Brief: `docs/plans/13-monorepo-restructure/briefs/6-05-transcript-and-jev-variants.md`. Depends on: Phase 5. Runs alongside: `6-01`, `6-02`, `6-04`.
- 6-03 Driver dual-read and trailer-completeness eval. Brief: `docs/plans/13-monorepo-restructure/briefs/6-03-driver-and-trailer-eval.md`. Depends on: `6-02`, `6-04`. Runs alongside: nothing.
- 6-06 Phase 6 residual-name scan. Brief: `docs/plans/13-monorepo-restructure/briefs/6-06-residual-scan-phase6.md`. Depends on: `6-01`, `6-02`, `6-03`, `6-04`, `6-05`. Runs alongside: nothing.

### Phase 7: Docs and migration guide

- Why: a hard break is only safe if the guide is complete. It is the only thing that tells existing installs what to do.
- Outcome:
  - [cmd] The residual-name scan over its whole scope reports nothing outside its exceptions.
  - [cmd] The CHANGELOG rename entry carries one `YAKKA_*` row for every `WORKFLOW_*` identifier removed by Phases 5–6, every path in the state-path table, remove-and-install commands for Claude Code, Cursor, Codex and OpenCode, and the numbered maintainer actions.
  - [cmd] `README.md` install instructions use `codyhamilton/yakka` and `yakka@yakka`.
  - [judgement] `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` and the contract sections of `docs/design/*` describe the yakka names and state the trailer dual-read rule.
- Surfaces: `README.md`, `CHANGELOG.md`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, the contract sections of `docs/design/*`, `docs/automation/post-build.md`, and the package and tool READMEs Phase 4 added.
- Approach: known.
- Depends on: Phases 5 and 6.

Refine:

- Phases 1 and 4 are each small enough for one worker and may skip `refine`.
- Phase 2 needs `refine`. It spans the Go module, Python tooling, TypeScript and Node tests, and docs. Refine cuts the git-mv commit first, then parallel path-rewrite units by area.
- Phase 3 is one unit and may skip `refine`. Its path is `plugins/yakka`.
- Phases 5–7 need `refine`. They are one cut, briefed against the layout Phases 2–4 actually left.

## Provenance Notes

- **Posture.** This was a headless design, so there is no `PROVENANCE.md`. The Assumption Ledger carries every choice that would otherwise have been asked.
- **Added scope.** Cursor load and hooks, `plugins/yakka`, and the yakka rename are Decisions 2 and 3. The plugin is not a package under `packages/`. The rename design's own adversarial pass stands for Phases 5–7; this plan does not relitigate the name, the hard break or the dual-read rule. A second pass on the addition tagged the Phase 5 hook-shape clause, narrowed that phase's scan so manifests stay in Phase 6, and required both marketplace sources in the Phase 3 outcome. The layout check this note used to call Phase 3 is Phase 4.
- **Grounding facts:**
  - `.cursor-plugin/marketplace.json` gives `workflow` `source: "./"`. `.claude-plugin/marketplace.json` points the core plugin at the GitHub repo, and the lab plugin at `plugins/workflow-lab`.
  - `hooks/cursor.json` commands use `${CURSOR_PLUGIN_ROOT}/tools/hooklog/spool.sh` and `${CURSOR_PLUGIN_ROOT}/bin/workflow`. Cursor's plugin docs discover hooks at `hooks/hooks.json` and show hook commands as `./scripts/...`. The decided command shape is the user's: `./script/...`.
  - Plan 12's close-out record is on master. Plan 14 has merged.
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
- **Artifact feedback.** The first feedback flagged problem coverage, surface specificity, outcome checkability and proof labelling below the tenant's p25. The Problem's why-now and cleanup scope, the explicit surface lists, and the proof tags answer those. Feedback on this addition was unreachable: the workflow MCP server failed tool discovery.
