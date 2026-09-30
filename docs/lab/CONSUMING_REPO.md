# Consuming repo — workflow-plugin declaration

Paste this block into a project that drives builds with the workflow plugin (skills + optional bot loop). It does **not** install anything by itself; it tells humans and Grok Bot where the contract lives.

```markdown
## Workflow plugin

This repo uses [workflow-plugin](https://github.com/codyhamilton/workflow-plugin) for design → per-phase execute → review → close-out.

- **Skills:** run `./install.sh` from a clone of workflow-plugin (core only in CI/cloud; lab optional locally). Claude Code on the web: SessionStart hook — see workflow-plugin `README.md`.
- **Phase loop (bot or human):** read-only status → one phase → assert → repeat until `done` or `unsuccessful`.
  - Status: `python3 <path-to-workflow-plugin>/tools/driver/status.py docs/plans/<NN>-<slug>/`
  - One phase (when landed): `python3 .../tools/driver/run.py <plan-folder> --once`
  - Assert: `python3 .../tools/driver/assert_phase.py --state <compact-state.json>` (see `tools/driver/README.md`)
- **Markers:** `Workflow-Plan:` on the PR; `Workflow-Phase: <slug>:<n>` / `<slug>:done` on closing commits (`skills/execute/SKILL.md`).
- **Status lives in the PR/issue tracker**, not in plan folder names.

Grok Bot (or similar) does **not** auto-discover plugin skills — install hooks or project-local skills first, then call driver CLIs for the loop.
```

Adjust `<path-to-workflow-plugin>` to a submodule path, vendored copy, or documented clone location your automation uses.
