# Consuming repo — workflow-plugin declaration

Paste the block below into a project that drives builds with the workflow plugin. The block does not install anything. The files under [`bootstrap/`](bootstrap/) are what the consuming repo copies.

## What a consuming repo copies

Two harnesses, two layers. Do not invent a Cursor session hook.

**Cursor cloud** boots from a prebaked image. Project skills under `.cursor/skills/` are discovered when the agent process starts. There is no `SessionStart` / `reloadSkills`. Put this in the **environment install** script, then snapshot the image so the next boot already has the files:

```bash
export WORKFLOW_WORKSPACE="$(git rev-parse --show-toplevel)"
bash /path/to/workflow-plugin/docs/lab/bootstrap/cursor-cloud-setup.sh
```

That sets `WORKFLOW_INSTALL_MODE=cloud` and runs `install.sh` **core only** into `<repo>/.cursor/skills/workflow/`. Add that path to `.gitignore`. A first-turn install does not put the skills on the first turn's skill list.

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

- **Skills (core only, no lab):** bootstrap before the first phase, then `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py` (exit 0). Cursor cloud: environment install runs `docs/lab/bootstrap/cursor-cloud-setup.sh` and the image is snapshotted (no session hook). Claude Code on the web: copy `docs/lab/bootstrap/session-start.sh` to `.claude/hooks/session-start.sh` and merge `docs/lab/bootstrap/claude-settings-fragment.json` into `.claude/settings.json`. Gitignore `<repo>/.cursor/skills/workflow/` if the Cursor path is used.
- **Phase loop (bot or human):** check skills → read-only status → one phase → assert → repeat until `done` or `unsuccessful`.
  - Skills: `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py`
  - Status: `python3 <path-to-workflow-plugin>/tools/driver/status.py docs/plans/<NN>-<slug>/`
  - One phase: `python3 <path-to-workflow-plugin>/tools/driver/run.py <plan-folder> --once`
  - Assert: `python3 <path-to-workflow-plugin>/tools/driver/assert_phase.py --state <compact-state.json>` (see `tools/driver/README.md`)
- **Markers:** `Workflow-Plan:` on the PR; `Workflow-Phase: <slug>:<n>` / `<slug>:done` on closing commits (`skills/execute/SKILL.md`).
- **Status lives in the PR/issue tracker**, not in plan folder names.

Grok Bot does not auto-discover plugin skills. On Cursor cloud they have to be in the image before the process starts. On Claude Code remote the SessionStart hook installs them and reloads. Then call the driver CLIs.

**OpenCode + DeepSeek Flash:** skills-only install (`./install.sh --opencode-skills`); no driver provider. If Flash agents execute briefs/units, use [`GUIDANCE-flash-review-gate.md`](GUIDANCE-flash-review-gate.md): mandatory phase review gate (Sonnet 5.5 on Flash work, then hold for Claude or Grok sign-off); Flash must not auto close-out or land `Workflow-Phase:`.
```

Adjust `<path-to-workflow-plugin>` to a submodule path, vendored copy, or documented clone location your automation uses.
