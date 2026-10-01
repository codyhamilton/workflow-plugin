# Consuming repo — workflow-plugin declaration

Paste the block below into a project that drives builds with the workflow plugin. The block does not install anything. The files under [`bootstrap/`](bootstrap/) are what the consuming repo copies.

## What a consuming repo copies

Claude Code and Cursor cloud are the two bootstrap layers below. **Codex** is a separate CLI harness (not OpenCode, not Composer) — advertise it with soft routing guidance (CHM when unsure); see [`GUIDANCE-codex-harness.md`](GUIDANCE-codex-harness.md). Do not invent a Cursor session hook.

**Cursor cloud** boots from a prebaked image. Project skills under `.cursor/skills/` are discovered when the agent process starts. There is no `SessionStart` / `reloadSkills`. **Preferred:** commit [`.cursor/environment.json`](https://cursor.com/docs/cloud-agent/environments) using [`tools/cloud-env/environment.json.example`](../../tools/cloud-env/environment.json.example) (or append its `install` to an existing one). The repo file beats dashboard config. Environment **builds** run `install` before agents start; **daily rebuild** tracks workflow-plugin **master** without pinning SHAs.

If the repo has no committed env file, use the dashboard **install** command or the curl one-liner below (fallback only — skills are not on the first turn if install runs only after the agent boots):

```bash
export WORKFLOW_WORKSPACE="${WORKFLOW_WORKSPACE:-/workspace}"
curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/tools/cloud-env/bootstrap-workflow-skills.sh | bash
```

With a local clone or vendored copy:

```bash
export WORKFLOW_WORKSPACE="$(git rev-parse --show-toplevel)"
bash /path/to/workflow-plugin/tools/cloud-env/bootstrap-workflow-skills.sh
```

Same behavior via legacy path: `docs/lab/bootstrap/cursor-cloud-setup.sh` (execs the bootstrap script).

That tracks `master` in `~/.cache/workflow-plugin`, runs `install.sh` **core only** into `<repo>/.cursor/skills/workflow/`. Optional lab skills: `WORKFLOW_INSTALL_LAB=1` (see [`tools/cloud-env/README.md`](../../tools/cloud-env/README.md)). Add the core path to `.gitignore`.

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

- **Skills (core only, no lab):** bootstrap before the first phase, then `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py` (exit 0). Cursor cloud: commit `.cursor/environment.json` from `tools/cloud-env/environment.json.example` (or dashboard/curl fallback — see above); daily rebuild refreshes master (no session hook). Claude Code on the web: copy `docs/lab/bootstrap/session-start.sh` to `.claude/hooks/session-start.sh` and merge `docs/lab/bootstrap/claude-settings-fragment.json` into `.claude/settings.json`. Gitignore `<repo>/.cursor/skills/workflow/` if the Cursor path is used.
- **Phase loop (bot or human):** check skills → read-only status → one phase → assert → repeat until `done` or `unsuccessful`.
  - Skills: `python3 <path-to-workflow-plugin>/tools/driver/check_skills.py`
  - Status: `python3 <path-to-workflow-plugin>/tools/driver/status.py docs/plans/<NN>-<slug>/`
  - One phase: `python3 <path-to-workflow-plugin>/tools/driver/run.py <plan-folder> --once`
  - Assert: `python3 <path-to-workflow-plugin>/tools/driver/assert_phase.py --state <compact-state.json>` (see `tools/driver/README.md`)
- **Markers:** `Workflow-Plan:` on the PR; `Workflow-Phase: <slug>:<n>` / `<slug>:done` on closing commits (`skills/execute/SKILL.md`).
- **Status lives in the PR/issue tracker**, not in plan folder names.

Grok Bot does not auto-discover plugin skills. On Cursor cloud they have to be in the image before the process starts. On Claude Code remote the SessionStart hook installs them and reloads. Then call the driver CLIs.

**OpenCode + DeepSeek Flash:** skills-only install (`./install.sh --opencode-skills`); no driver provider. Flash is encouraged for brief/unit work when rationing capacity; [`GUIDANCE-flash-review-gate.md`](GUIDANCE-flash-review-gate.md) bounds sign-off only (Sonnet 5.5 on Flash work, hold for Claude or Grok — no Flash auto close-out or `Workflow-Phase:`).

**Codex (separate harness):** not an OpenCode provider. Pin **sol** → `gpt-6.1-sol` and **luna** → `gpt-6-luna` for Plus/Codex work (`codex exec -m … -c model_reasoning_effort=…`; pass prompt on argv, override `-m` if config still says `gpt-5.4`). Often fits high-thinking / mechanically rich units alongside Claude — soft routing, not mandatory. Discovery for bots is still status → trigger → asserts (skills alone are not enough for Grok Bot). Details: [`GUIDANCE-codex-harness.md`](GUIDANCE-codex-harness.md).
```

Adjust `<path-to-workflow-plugin>` to a submodule path, vendored copy, or documented clone location your automation uses.
