# Rename to yakka

## Intent

User request, verbatim:

> Help come up with a better name for this app. We've got `workflow` which is terribly generic. `miniflow` was another thought. It's all about the plan/design/refine/execute SDLC workflow

> It makes more sense to keep yakka for both

> do the /workflow:design

## Problem

The product is named `workflow`. That name is too generic to search for and too generic to tell apart from the thing it describes. In this repo the word is also overloaded. The plugin, the binary, the MCP server, the skill prefix, about 40 environment variables, the commit trailers and several directories all use the same word the docs use for the method itself.

The user has chosen `yakka` (Australian slang for work, as in "hard yakka") as the single name for product, binary and service. Every later piece of work adds more surfaces that carry the name: releases, the analytics site, the remote service. The longer the rename waits, the more it costs.

## Solution Shape

After this change the product is `yakka` everywhere it names itself:

- The plugin is `yakka@yakka`, and its skills are `yakka:design`, `yakka:refine`, `yakka:execute` and so on.
- The binary is `bin/yakka`, built from `packages/yakka`, and it registers as the MCP server `yakka`.
- Its environment is `YAKKA_*`, and its state lives under `yakka/` XDG directories.
- Closing commits carry `Yakka-Phase:`, and PRs carry `Yakka-Plan:`.

Readers still accept the old `Workflow-*` trailers and the old report fence, because git history and old transcripts cannot change. Beyond that, installed setups get no backward compatibility. They update by hand, following the CHANGELOG migration guide.

This design assumes plans 13 (monorepo restructure) and 14 (analytics UI) have merged. Surfaces are named as plan 13 leaves them. All three phases ship in one PR.

### Domain: Plugin identity (repo root)

- Owns: `.claude-plugin/{plugin,marketplace}.json`; `.cursor-plugin/plugin.json`, plus `.cursor-plugin/marketplace.json` when present; `.codex-plugin/plugin.json`; `.mcp.json`; `.codex-mcp.json`; `hooks/*.json`; `install.sh`; `.gitignore`; `README.md`; `CHANGELOG.md`.
- Contract:
  - **Names.**
    - The plugin name is `yakka` in every plugin manifest.
    - Every marketplace manifest is named `yakka` and lists exactly one plugin, `yakka`, with `source: "./"`.
  - **Version.**
    - Every manifest moves to the next major version once, in Phase 2. They all move together, with one `CHANGELOG.md` entry.
    - Because the change ships as one PR, plan 13's per-phase minor bump does not apply inside it.
  - **MCP server key.**
    - The key is `yakka` in `.mcp.json`, `.codex-mcp.json` and every example MCP config.
    - Claude Code therefore exposes the tools as `mcp__plugin_yakka_yakka__<tool>`. The tool names themselves do not change.
  - **Hook commands.** They keep their shape and arguments. Only the binary path changes, to `<root>/bin/yakka`.
  - **Repo URL.** It is `https://github.com/codyhamilton/yakka` in every place a repo URL appears.
  - **Install locations.**
    - `install.sh` installs Cursor to `~/.cursor/plugins/local/yakka`.
    - The workspace skills folder is `.cursor/skills/yakka/`.
    - The source cache is `${XDG_CACHE_HOME:-~/.cache}/yakka/install-src`.
    - `.gitignore` names `.cursor/skills/yakka/`.
  - **Migration guide.** The CHANGELOG rename entry is the user-facing migration guide. It carries:
    1. the complete `WORKFLOW_*` → `YAKKA_*` map;
    2. the old → new path for every state directory;
    3. for each harness, the command that removes the old `workflow` plugin or local install and the command that installs `yakka`. The old and new installs must not both be enabled, or every hook event is recorded twice.
    4. the `.gitignore` change consuming repos need (`.cursor/skills/workflow/` → `.cursor/skills/yakka/`);
    5. the note that MCP permission entries and skill invocations change prefix;
    6. the maintainer actions listed under Architectural Implications.
- Non-goals: aliasing the old plugin or marketplace name; migrating installed copies automatically.

### Domain: Binary and runtime packages (`packages/`)

- Owns:
  - `packages/yakka`, from `packages/workflow`, including its catalogue at `packages/yakka/catalogue/`.
  - `packages/hooklog`.
  - `packages/yakka-analytics`, from `packages/workflow-analytics`.
  - `packages/opencode-yakka-hooks`, from `packages/opencode-workflow-hooks`.
  - `bin/{yakka,VERSION,SHA256SUMS,RELEASE_URL}`.
  - `tools/release/`.
- Contract:
  - **Go module.** The module is `github.com/codyhamilton/yakka/packages/yakka`, with the command at `cmd/yakka`.
  - **Binary.**
    - `bin/yakka` keeps the four-step resolution of `docs/design/05-distribution.md`.
    - Its cache is `${XDG_CACHE_HOME:-~/.cache}/yakka/<bin/VERSION>/yakka-<os>-<arch>`.
    - Release assets are named `yakka-<os>-<arch>` and live under `<RELEASE_URL>/v<version>/`.
    - `bin/VERSION` is bumped, so no tag ever serves both old and new asset names.
    - `yakka --version` prints `yakka <version> <commit>`.
  - **MCP.** `initialize` returns `serverInfo.name = "yakka"`.
  - **Identifiers.**
    - Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix. This covers environment variables and named constants alike, in shipped code (packages, `bin/`, hooks, `install.sh`, `tools/cloud-env`) and in maintainer tools.
    - The one exception is the `WORKFLOW_QUALITY_` prefix, which belongs to the legacy quality service.
  - **State paths.** The XDG base resolution is unchanged. Only the product segment changes:

    | Was | Becomes |
    |---|---|
    | `~/.local/share/workflow/{queue,serve}` | `~/.local/share/yakka/{queue,serve}` |
    | `~/.config/workflow/client.toml` | `~/.config/yakka/client.toml` |
    | `~/.cache/workflow/` | `~/.cache/yakka/` |
    | `~/.local/state/workflow/` | `~/.local/state/yakka/` |
    | `~/.local/share/workflow-plugin/hooklog` | `~/.local/share/yakka/hooklog` |
    | `~/.cache/workflow-plugin` (cloud-env checkout) | `~/.cache/yakka/src` |

    No code reads the old paths.
  - **npm packages.**
    - `@codyhamilton/yakka-analytics` (private). Its Pages project name is `yakka-analytics`, and its site placeholder marker is `yakka-analytics-placeholder`.
    - `@codyhamilton/opencode-yakka-hooks`. It exports `yakka-signals.json`, and its plugin export is `YakkaSignalsPlugin`.
  - **Browser storage.** The analytics site's `localStorage` keys become `yakka-analytics-base`, `yakka-analytics-key` and `yakka-analytics-views:*`. Nothing reads the old keys, because no users have saved settings, views or dashboards yet.
  - **Catalogue consumers.** `tools/quality` and every test setup that names the catalogue directory are repointed to `packages/yakka/catalogue` in the same phase that moves it. This is the only change to `tools/quality`.
- Non-goals:
  - Publishing the release or the npm packages, or creating the Pages project. These are maintainer publish actions.
  - Migrating data.
  - Rewriting recorded events. Recorded tool names such as `mcp__plugin_workflow_workflow__*` stay as recorded.

### Domain: Plan protocol (skills, driver, evals)

- Owns:
  - `skills/*/SKILL.md` and their templates and briefs.
  - `docs/automation/post-build.md`.
  - `tools/driver/`.
  - `evals/scenarios/trailer-completeness/`.
  - The maintainer skill `.claude/skills/workflow-tuning`, renamed `.claude/skills/yakka-tuning`.
- Contract:
  - **What writers emit.**
    - A phase-closing commit carries `Yakka-Phase: <slug>:<n>`.
    - The wrap-up commit carries `Yakka-Phase: <slug>:done`.
    - The first line of the PR body is `Yakka-Plan: docs/plans/<NN>-<slug>/`.
    - `execute`'s final report is fenced ```` ```yakka-report ````.
  - **What readers accept.**
    - `Workflow-Phase` and `Yakka-Phase` are equivalent trailer keys. Phase resolution takes the union of both from `<default>..HEAD`.
    - `Workflow-Plan:` and `Yakka-Plan:` are equivalent PR markers.
    - ```` ```workflow-report ```` and ```` ```yakka-report ```` are equivalent fences.
    - This equivalence is permanent.
    - Every reader in `tools/driver/` goes through one shared definition of the accepted keys. Today these are `resolve`, `status`, `trigger`, `run`, `run_record`, `assert_phase`, `phase_assert` and `report`.
    - Each reading skill states the legacy forms it accepts in one sentence.
  - **Skill cross-references.** Cross-references in skill prose use the `yakka:` prefix.
- Non-goals: rewriting existing commits or PR bodies; any other change to the plan protocol.

### Residual-name scan

The phase outcomes rely on this scan, so it is part of the contract. The scan is case-sensitive and is run over `git ls-files`.

**Excluded paths:**
- `docs/plans/` (all of it);
- `docs/lab/`, `docs/analysis/`, `evals/results/`;
- `tools/quality/`;
- in `CHANGELOG.md`, every entry up to and including the rename entry;
- in `docs/design/*.md`, sections whose heading contains a date (`YYYY-MM-DD`). These are dated records, not contracts.

**Forbidden patterns (extended regex):**
- `WORKFLOW_` not followed by `QUALITY_`
- `\bbin/workflow\b`, `\bcmd/workflow\b`, `\bpackages/workflow\b`
- `\bworkflow-(plugin|analytics|tuning|lab|signals|quality-placeholder)\b`
- `\bopencode-workflow-hooks\b`, `WorkflowSignalsPlugin`
- `\bworkflow-(darwin|linux)-`
- `workflow (version|<version>)` at the start of a `--version` string
- `\bworkflow:(design|refine|execute|close-out|comprehensive-review|post-build|plan|setup)\b`
- `(\.local/(share|state)|\.config|\.cache)/workflow\b`
- `\.cursor/(plugins/local|skills)/workflow\b`
- `"workflow"\s*:` in JSON, `\[mcp_servers\.workflow\]`
- `mcp__plugin_workflow_`
- `Workflow-(Phase|Plan)\b`, `workflow-report\b`

**Allowed exceptions for the last line (`Workflow-Phase`, `Workflow-Plan`, `workflow-report`) only:**
- `tools/driver/`;
- `evals/scenarios/trailer-completeness/`;
- the one legacy-forms sentence in each reading skill;
- Go test fixtures under `packages/yakka/` that contain recorded commit text.

Refine decides whether the scan is committed as a script or run as a one-off command. Either way, its patterns and exclusions are exactly these.

## Architectural Implications

- **Stable docs.** `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` and the contract sections of `docs/design/*` (in particular `05-distribution.md`, `04-advisory-surface.md`, `07-analytics-site.md` and `system-architecture.md`) are updated to the new names. The PR Artifact Seam and phase-boundary contracts gain the dual-read rule.
- **Plan 13 superseded in part.** Plan 13 said the raw bootstrap URL and `~/.cache/workflow-plugin/tools/driver/check_skills.py` do not move. This design supersedes that contract: the bootstrap script becomes `tools/cloud-env/bootstrap-yakka-skills.sh` and the cache moves, with no forwarding stub (hard break). `tools/README.md` is updated to match.
- **Plan 13's layout is the starting point.** If plan 13's final layout differs from its design, the first `refine` maps these contracts onto what landed, without reopening this design.
- **Hard-break consequences.** After merge:
  - An existing install keeps running `workflow` until it is removed and `yakka` is installed.
  - Anything that sets `WORKFLOW_*`, or relies on data under the old paths, is ignored by the new binary.
  - Cloud environments that fetch the old bootstrap URL stop working.
- **Maintainer actions outside the repo** (listed in the CHANGELOG guide):
  1. Rename the GitHub repo to `codyhamilton/yakka` when the PR merges.
  2. Publish the `v<bin/VERSION>` release with `yakka-*` assets. Until then the wrapper builds from source.
  3. Move the live serve deployment:
     - stop `workflow-serve.service`;
     - move `~/.local/share/workflow/serve` to `~/.local/share/yakka/serve` and the queue alongside it;
     - install `yakka-serve.service` with `YAKKA_SERVE_*` and an ExecStart under `~/.local/lib/yakka/`;
     - remove the old unit.

     Upgrading the binary without these steps starts serve on an empty ledger.
  4. Move `~/.config/workflow/client.toml` if it exists.
  5. Remove the old plugin from, and install `yakka` into, each harness.
  6. Update each deployed cloud-env `environment.json`.
  7. Optionally create the `yakka-analytics` Pages project.
  8. Optionally rename the local checkout. Claude Code keys project memory on the checkout path, so memory would need copying.
- **This plan's own trailers.** This plan runs under the installed `workflow` plugin, so its phase trailers may be `Workflow-Phase:`. The dual-read rule makes that harmless.
- **Analytics continuity.** Series grouped by MCP tool name or skill name will split at the rename. That is accepted, not reconciled.

## Decisions

These are recorded turn by turn in PROVENANCE.md.

1. Sequenced after plans 13 and 14, on the post-13 layout, as one PR.
2. The GitHub repo, the marketplaces, the Go module and every repo URL become `yakka`.
3. Env vars, constants and state paths are a hard break: no fallback, no migration, and a CHANGELOG migration guide.
4. Trailers and the report fence are renamed, and readers accept both forms permanently.
5. Out of scope: the legacy quality service (except its catalogue path), historical docs, and "workflow" used as a common noun.

## Assumption Ledger

None. See PROVENANCE.md.

## Risks

- **Duplicate hooks during cutover** — mitigated. An install with both plugins enabled records every event twice. The guide's per-harness remove-then-install step is the mitigation; nothing in code detects it.
- **Serve started on an empty ledger** — mitigated. Upgrading the live serve deployment without moving its data dir starts it empty. Maintainer action 3 covers it; the binary does not warn.
- **Cloud environments break at merge** — accepted. Any environment fetching the old bootstrap URL fails until its `environment.json` is updated (maintainer action 6). This is the user's hard-break choice.
- **Plan 13 lands differently from its design** — open. Surface names here assume plan 13's design. The first `refine` maps them onto what landed; if the difference changes a phase outcome, the design returns to the user.
- **Analytics series split at the rename** — accepted. Not reconciled.

## Open Questions

None.

## Phases

Each phase ends with every test suite in the repo passing (Go, Python under `packages/` and `tools/`, JS/TS). That way no phase leaves a consumer of a renamed path broken.

### Phase 1 — Runtime runs as yakka

- Outcome. Why it matters: the binary and hooks are what every harness executes, so they must work under the new names before anything points at them.
  - **[proven by script]** From a `HOME` with no `yakka` state:
    - `bin/yakka --version` prints `yakka <version> <commit>`, through a source build.
    - An event passed to `packages/hooklog/spool.sh --harness claude` lands in `~/.local/share/yakka/queue`.
    - `bin/yakka drain` delivers it to a keyless `bin/yakka serve`, which stores it under `~/.local/share/yakka/serve/local/`.
    - `bin/yakka mcp` answers `initialize` with `serverInfo.name = "yakka"`.
  - **[proven by tests]** Every suite passes, including `tools/quality` and the analytics e2e setup loading `packages/yakka/catalogue`.
  - **[proven by scan]** The residual-name scan reports nothing under `packages/`, `bin/`, `hooks/`, `.mcp.json`, `.codex-mcp.json` or `tools/release/`. Skill and brief citations of the catalogue path are repointed in this phase too.
- Surfaces:
  - `packages/workflow` → `packages/yakka` (module, `cmd/`, env reads, path defaults, MCP serverInfo, catalogue);
  - `packages/hooklog` (`spool.sh`, `hooklog.py`, example configs);
  - `packages/workflow-analytics` → `packages/yakka-analytics` (`package.json`, `wrangler.toml`, placeholder marker, e2e/hosted setups);
  - `packages/opencode-workflow-hooks` → `packages/opencode-yakka-hooks` (`package.json`, `src/index.ts`, Python helpers, tests);
  - `bin/*`; `tools/release/`; `hooks/*.json`; `.mcp.json`; `.codex-mcp.json`;
  - the catalogue path in `tools/quality`, `skills/execute/SKILL.md` and `skills/refine/templates/brief.md`.
- Approach: known
- Depends on: plans 13 and 14 merged

### Phase 2 — Plugin and plan protocol are yakka

- Outcome. Why it matters: this is the name users see and type, and the protocol every later plan writes.
  - **[proven by check]** Every plugin and marketplace manifest names `yakka` at the next major version.
  - **[proven by tests]** The `tools/driver` tests show two things:
    - A branch whose closing commits carry `Workflow-Phase: <slug>:1` and `Yakka-Phase: <slug>:2` resolves to phase 3 through `resolve`, `status` and `trigger`.
    - `report.py` parses both fences.
  - **[proven by eval]** The trailer-completeness eval passes for each key.
  - **[proven by tests]** The install-route tests show that `install.sh` in each mode, and `tools/cloud-env/bootstrap-yakka-skills.sh`, install into the `yakka`-named locations.
  - **[proven by scan]** The residual-name scan reports nothing under `skills/`, `.claude/skills/`, the plugin manifest directories, `install.sh`, `.gitignore` or `tools/`.
  - **[judgement, reviewed]** Each skill's prose writes the `Yakka-*` forms and names the legacy forms it accepts in exactly one sentence.
- Surfaces:
  - `.claude-plugin/`, `.cursor-plugin/`, `.codex-plugin/`;
  - `skills/**`;
  - `.claude/skills/workflow-tuning` → `yakka-tuning`, and its inbound references;
  - `tools/driver/` (shared trailer-key definition, every reader, `check_skills.py`, fixtures, tests);
  - `tools/cloud-env/` (script rename, README, `environment.json.example`);
  - `tools/transcript/` and `tools/jev-variants/` `WORKFLOW_*` identifiers;
  - `tools/README.md`; `install.sh`; `.gitignore`;
  - `evals/scenarios/trailer-completeness/`.
- Approach: known
- Depends on: Phase 1, because skills and install paths cite the binary and package names

### Phase 3 — Docs and migration guide

- Outcome. Why it matters: a hard break is only safe if the guide is complete. It is the only thing that tells existing installs what to do.
  - **[proven by scan]** The residual-name scan over its whole scope reports nothing outside its exceptions.
  - **[proven by check]** The CHANGELOG rename entry carries:
    - one `YAKKA_*` row for every `WORKFLOW_*` identifier removed by Phases 1–2 (checked against `git diff` of the PR);
    - every path in the state-path table;
    - remove-and-install commands for Claude Code, Cursor, Codex and OpenCode;
    - the numbered maintainer actions.
  - **[proven by check]** `README.md` install instructions use `codyhamilton/yakka` and `yakka@yakka`.
  - **[judgement, reviewed]** `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md` and the contract sections of `docs/design/*` describe the yakka names and state the trailer dual-read rule.
- Surfaces:
  - `README.md`, `CHANGELOG.md`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`;
  - `docs/design/{01-event-model-and-ingest,02-edge-capture,03-remote-service,04-advisory-surface,05-distribution,07-analytics-site,conversation-indexer,system-architecture}.md` (contract sections only);
  - `docs/automation/post-build.md`;
  - READMEs: `evals/README.md`, `packages/opencode-yakka-hooks/README.md`, `packages/hooklog/README.md`, `tools/{cloud-env,driver,jev-variants,transcript}/README.md`, plus any README plan 13 adds under `packages/`.
- Approach: known
- Depends on: Phases 1 and 2

## Provenance Notes

- **Name chosen: `yakka` over `gaffer`.** `gaffer` is crowded on GitHub (gchq/Gaffer, GafferHQ/gaffer and others). `yakka` is nearly empty there and free on crates.io. The bare npm and PyPI names belong to a 2024 placeholder, so npm packages stay scoped under `@codyhamilton/`.
- **Rejected: a split name** (yakka for the product, gaffer for the service). Two names is too many for one product.
- **Rejected: folding the rename into plan 13.** That would save one `git mv` per directory, but it would reopen a signed-off design.
- **Rejected: env-var fallback and data migration.** The user chose a hard break. The installs are few and maintainer-controlled, so a complete guide is enough. That is why Phase 3's outcome is about the guide's completeness.
- **`localStorage` keys renamed too.** The review proposed keeping them so saved dashboards would survive. The user said no analytics users have saved state yet, so the keys follow the hard break.
- **Trailers dual-read permanently.** Close-out records and post-merge tooling read old history. The reader cost is one shared key list.
- **The residual-name scan is a contract.** "workflow" is an ordinary English word, so done has to be defined by explicit patterns and exclusions, not by a plain grep.
- **Adversarial pass (clean context) applied:**
  - the scan was made passable and exact;
  - the catalogue consumers and every driver reader were given owners;
  - the old-install removal, `.gitignore` and serve-unit steps were added to the guide;
  - the plan 13 supersession was stated;
  - all suites must pass at every phase;
  - the Cursor marketplace manifest was added;
  - one major bump per PR was settled.
