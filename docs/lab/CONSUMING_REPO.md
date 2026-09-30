# Consuming repo — workflow-plugin declaration

Paste the block below into a project that drives builds with the workflow plugin. The block does not install anything. The files under [`bootstrap/`](bootstrap/) are what the consuming repo copies.

## What a consuming repo copies

Two harnesses, two layers. Do not invent a Cursor session hook.

**Cursor cloud** boots from a prebaked image. Project skills under `.cursor/skills/` are discovered when the agent process starts. There is no `SessionStart` / `reloadSkills`. Put this in the **environment install / setup** command (runs on each environment build — a **daily rebuild** keeps skills synced to workflow-plugin **master** without pinning SHAs):

```bash
export WORKFLOW_WORKSPACE="$(git rev-parse --show-toplevel)"
bash /path/to/workflow-plugin/tools/cloud-env/bootstrap-workflow-skills.sh
```

Same behavior via legacy path: `docs/lab/bootstrap/cursor-cloud-setup.sh` (execs the script above).

From GitHub without a local clone:

```bash
export WORKFLOW_WORKSPACE="${WORKFLOW_WORKSPACE:-/workspace}"
curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/tools/cloud-env/bootstrap-workflow-skills.sh | bash
```

That tracks `master` in `~/.cache/workflow-plugin`, runs `install.sh` **core only** into `<repo>/.cursor/skills/workflow/`. Optional lab skills: `WORKFLOW_INSTALL_LAB=1` (see [`tools/cloud-env/README.md`](../../tools/cloud-env/README.md)). Add the core path to `.gitignore`. A first-turn install does not put the skills on the first turn's skill list.

**Claude Code on the web** starts a fresh container per session and does support a hook. Copy:

- [`bootstrap/session-start.sh`](bootstrap/session-start.sh) → `.claude/hooks/session-start.sh` and `chmod +x`
- merge [`bootstrap/claude-settings-fragment.json`](bootstrap/claude-settings-fragment.json) into `.claude/settings.json`

The hook no-ops unless `CLAUDE_CODE_REMOTE=true`, curls `install.sh` (core only, `~/.claude/skills/`), and prints `reloadSkills` so the same session rescans. The same script is in the root `README.md` heredoc.

After either install, with no network:

```bash
python3 <path-to-workflow-plugin>/tools/driver/check_skills.py
```

Exit 0 means `design`, `refine`, `execute`, `comprehensive-review`, `close-out`, and `post-build` each contain `SKILL.md` at that harness's install root. Lab skills are not required. Stdout JSON: `{ok, harness, skills_found, missing, skills_root}`.

## Paste block

```markdown
## Workflow plugin

This repo uses [workflow-plugin](https://github.com/codyhamilton/workflow-plugin) for design → per-phase execute → review → close-out.

- **Skills (core only, no lab):** bootstrap before the first phase, then `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py` (exit 0). Cursor cloud: environment setup runs `tools/cloud-env/bootstrap-workflow-skills.sh` (or `docs/lab/bootstrap/cursor-cloud-setup.sh`); daily rebuild refreshes master (no session hook). Claude Code on the web: copy `docs/lab/bootstrap/session-start.sh` to `.claude/hooks/session-start.sh` and merge `docs/lab/bootstrap/claude-settings-fragment.json` into `.claude/settings.json`. Gitignore `<repo>/.cursor/skills/workflow/` if the Cursor path is used.
- **Phase loop (bot or human):** check skills → read-only status → one phase → assert → repeat until `done` or `unsuccessful`.
  - Skills: `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py`
  - Status: `python3 <path-to-workflow-plugin>/tools/driver/status.py docs/plans/<NN>-<slug>/`
  - One phase: `python3 <path-to-workflow-plugin>/tools/driver/run.py <plan-folder> --once`
  - Assert: `python3 <path-to-workflow-plugin>/tools/driver/assert_phase.py --state <compact-state.json>` (see `tools/driver/README.md`)
- **Markers:** `Workflow-Plan:` on the PR; `Workflow-Phase: <slug>:<n>` / `<slug>:done` on closing commits (`skills/execute/SKILL.md`).
- **Status lives in the PR/issue tracker**, not in plan folder names.

Grok Bot does not auto-discover plugin skills. On Cursor cloud they have to be in the image before the process starts. On Claude Code remote the SessionStart hook installs them and reloads. Then call the driver CLIs.
```

Adjust `<path-to-workflow-plugin>` to a submodule path, vendored copy, or documented clone location your automation uses.
