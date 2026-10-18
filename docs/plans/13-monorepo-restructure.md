# Monorepo Restructure: Lab Collapse, Packages and Tools

The repo stopped pretending that maintainer skills were a second plugin and that the binary lived under `tools/`. The plugin now installs from `plugins/yakka`, the shipped units live under `packages/`, and the product calls itself yakka. A layout check keeps that split from drifting. Existing installs are not rewritten; the 3.0.0 changelog is the migration guide. The logged-in Cursor session that should show a hook firing was left for a person to run.

## Intent

User request, verbatim:

> Have an agent work on a background design - collapsing workflow-lab, which should not be its own plugin (just skills at root, they're maintainer-only), as well as cleaning up the repo and distinguishing tools from packages (workflow bin to my mind is a package), organising the repo into a proper monorepo with packages/ containing the various packages it holds as independent deployable units

> Ok we have some other issues to deal with. There should be an open plan for restructuring the plugin? We have to add to that. Cursor is not actually loading the plugin correctly nor triggering hooks. The commands in the hooks file for cursor aren't right, the scripts anyway run from plugin root so only need `./script/...` to execute, plus we should move the workflow plugin into the packages/ dir as a package (it's a plugin referenced from the marketplace entry).

> plus we have a further plan for renaming across the board to yakka - I think it should be integrated into this plan

> maybe instead of packages, we put the plugin in `plugins/yakka`

> Help come up with a better name for this app. We've got `workflow` which is terribly generic. `miniflow` was another thought. It's all about the plan/design/refine/execute SDLC workflow

> It makes more sense to keep yakka for both

> do the /workflow:design

## Why This Existed

`workflow-lab` was a marketplace plugin whose skills run repo commands, so they could not work from their own install root, and the lists of those skills had drifted. `tools/` mixed the shipped Go binary and the hook edge with maintainer scripts, and the binary loaded its check catalogue from a tool directory. Cursor's marketplace entry used the repo root as the plugin, and its hook commands pointed at paths the install does not contain. The product name was the same word as the method.

## What Was Built

**Changed:** `plugins/yakka` (skills, hooks, `script/`, `bin/yakka`), `packages/yakka`, `packages/hooklog`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`, `.claude/skills/`, `install.sh`, `tools/cloud-env/bootstrap-yakka-skills.sh`, `tools/driver`, `tools/release` (layout check and residual-name scan), the root marketplaces, and the stable docs in `docs/design/`, `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `README.md`, and `CHANGELOG.md`.

### Phase 1 — Lab collapses into maintainer skills

The seven lab skills became six Claude Code project skills under `.claude/skills/`. `lab-proposal` was removed. `install.sh` and the cloud bootstrap no longer have a lab opt-in. `workflow-tuning` was later renamed `yakka-tuning`.

### Phase 2 — Runtime units become packages

The Go module and the hook edge left `tools/`. The check catalogue moved in with the binary. Hook configs, Python path lookups, the analytics e2e setup, and the release script follow the new paths.

### Phase 3 — Cursor loads `plugins/yakka`

The plugin tree moved to `plugins/yakka`. Both marketplaces use that directory as `source`. Cursor hook commands are `./script/spool.sh` and `./script/prefetch-version.sh`. A logged-in Cursor session was not opened.

### Phase 4 — Layout contract

`tools/release/test_layout.py` fails when a package runtime path enters `tools/`, when a marketplace is not the single `plugins/yakka` entry, when a Cursor command is not `./script/...`, or when a package README lacks Consumers, Build, Test, and Release. The OpenCode signal log and the driver reader share `${XDG_STATE_HOME:-~/.local/state}/yakka/jev-signal-log.jsonl`.

### Phase 5 — Runtime runs as yakka

The module is `github.com/codyhamilton/yakka/packages/yakka`, the command is `cmd/yakka`, and `yakka --version` prints `yakka <version> <commit>`. Queue, serve, cache, and hooklog state directories use `yakka`. MCP `serverInfo.name` is `yakka`. npm packages are `@codyhamilton/yakka-analytics` and `@codyhamilton/opencode-yakka-hooks`. `WORKFLOW_QUALITY_*` was left on the legacy service.

### Phase 6 — Plugin and plan protocol are yakka

Plugin and marketplace manifests are `yakka` 3.0.0. Writers emit `Yakka-Phase`, `Yakka-Plan`, and a `yakka-report` fence. `tools/driver/trailer_keys.py` is the list readers use for the old and new trailer keys and both fences. Install routes and the cloud bootstrap use the yakka paths. There is no stub at the old bootstrap script name.

### Phase 7 — Docs and migration guide

`README.md` installs from `codyhamilton/yakka` and `yakka@yakka`. The 3.0.0 changelog entry maps the renamed environment variables and state paths and gives remove-then-install steps for Claude Code, Cursor, Codex, and OpenCode. `docs/ARCHITECTURE.md` and `docs/design/system-architecture.md` state the dual-read rule. `tools/release/scan_residual_names.py --scope all` exits 0.

## Deviations

- The plugin wrapper's source build looked one directory too high (`$ROOT/../packages/...`) until Phase 5 pointed it at `packages/yakka`.
- After Phase 5 the OpenCode package logged under `yakka` while `tools/driver` still logged under `workflow`. Phase 6 made them the same path.
- The first changelog table missed six removed `WORKFLOW_*` identifiers. A follow-up unit added the rows.
- Stable docs that would have quoted `Workflow-Phase` point at the dual-read section instead, because the residual scan treats that string as a hit outside its exceptions.
- The phase 4, 5, and 6 closing commits put a blank line between `Workflow-Phase` and `Co-authored-by`, so `git interpret-trailers` did not see the phase trailer. Empty commits restored the three trailers. Published commits were not amended.

## Review

Terminal review at `2f4e3bcb096a63c3f81bb09cf396845afc74e166`. Verdict PASS_WITH_FOLLOWUPS. No blocker or high finding, so no fixer ran. Phase 3 is partial only on the logged-in Cursor session, which the user said not to block on. The other phase outcomes hold, with later renames standing in for the names those phases proved.

Automation review at `fa198181cf6327fecd04ed77e734f63876994168` plus follow-up commit. Verdict PASS_WITH_FOLLOWUPS. Fixed: residual-name scan literals in `docs/design/05-distribution.md`; production OAuth sign-in URL and Pages callback API base; `session-start.sh` URL aligned with README. No blocker or high finding outstanding.

## Residual Risks

- Nobody has installed this marketplace entry in a logged-in Cursor session and watched a `./script/...` hook reach the queue, then `yakka drain` into a local `yakka serve`.
- `artifact_feedback` never scored a brief or a report. The workflow MCP server failed tool discovery on every phase.
- `install.sh` and the release URL name `github.com/codyhamilton/yakka` before that repository and the 3.0.0 assets exist. Renaming the repo and publishing the release are maintainer actions in the changelog.
- `spool.sh` still exits 0 when it cannot record an event.

## Follow-ups

Recorded in [design 5](../design/05-distribution.md) under Layout rules: `docs/lab/CONSUMING_REPO.md` still fetches `codyhamilton/workflow-plugin`, the unused `YAKKA_QUALITY_URL` in the hooklog tests, and `tools/driver/README.md` still showing only the legacy trailer and fence.

## Decisions Worth Keeping

- The plugin is `plugins/yakka`, not a package. Marketplace `source` is that directory. Cursor runs `./script/...` from that directory.
- One name, yakka, for the product, the binary, and the service. No fallback reads of the old environment variables or state paths, except `WORKFLOW_QUALITY_*`.
- Readers accept `Workflow-Phase` and `Yakka-Phase`, and both report fences, permanently. Git history is not rewritten.
- Maintainer skills stay in `.claude/skills/` and are not installed for plugin users.
- The rename shipped as one major, 3.0.0, with the changelog as the only migration.
