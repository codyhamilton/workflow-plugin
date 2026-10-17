# Brief: 1-01 — Lab collapse

Consumer: the Composer worker dispatched by the phase 1 orchestrator. Its commit is the unit. The orchestrator verifies the phase outcome and writes the closing record.
Owned paths:
`plugins/workflow-lab/**` (remove after the move),
`.claude/skills/**` (the six moved skills),
`.claude-plugin/marketplace.json`,
`.cursor-plugin/marketplace.json`,
`.claude-plugin/plugin.json`,
`.cursor-plugin/plugin.json`,
`.codex-plugin/plugin.json`,
`install.sh`,
`tools/cloud-env/bootstrap-workflow-skills.sh`,
`tools/cloud-env/README.md`,
`tools/driver/check_skills.py`,
`tools/driver/README.md`,
`tools/driver/tests/test_check_skills.py`,
`tools/driver/tests/test_install_route.py`,
`tools/jev-variants/README.md`,
`docs/lab/README.md`,
`docs/lab/JEV-METHODOLOGY.md`,
`docs/lab/FINDINGS.md`,
`docs/lab/RESEARCH/INDEX.md`,
`docs/lab/PROVENANCE-jev-hypotheses-2026-10-02.md`,
`docs/lab/CONSUMING_REPO.md`,
`docs/ARCHITECTURE.md`,
`docs/OVERVIEW.md`,
`docs/design/system-architecture.md`,
`README.md`,
`CHANGELOG.md`,
`docs/plans/13-monorepo-restructure/reports/1-01-lab-collapse.md` (new).
Touch nothing else. In particular do not edit `DESIGN.md`, `skills/` (the six core skills), `hooks/`, `bin/`, `tools/workflow/`, `packages/`, or any `docs/plans/` file other than the report.
Commits: Commit to the current branch (`cursor/restructure-plan-scope-93a1`) when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/1-01-lab-collapse.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: nothing.
Budget: 35 files to read, about 400 lines to change, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/13-monorepo-restructure/IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — `### Phase 1: Lab collapses into maintainer skills` (outcome, surfaces), `### Domain: Maintainer skills`, the install bullet and the plugin-version-bump bullets under `### Domain: Plugin`, Assumption 7, Assumption 9. Binding.
2. `plugins/workflow-lab/skills/*/SKILL.md` frontmatter only, plus the directory listing of each skill. Confirm the six to move and that `lab-proposal` is the one to delete.
3. `install.sh` — the lab functions and the four mode branches (`claude-code`, `cursor-cloud`, `opencode`, and the interactive Cursor/Claude/OpenCode tail).
4. `tools/driver/check_skills.py` — `LAB_SKILLS`. `tools/driver/tests/test_install_route.py` and `tools/driver/tests/test_check_skills.py` — every use of `LAB_SKILLS`.
5. `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, and the `version` field of the three root plugin manifests (all `2.9.2`).
6. `CHANGELOG.md` — the `## 2.9.2` heading, as the pattern for the new entry.
7. The doc sections that name the lab plugin: `docs/ARCHITECTURE.md` component map, invariant 7, Stable References; `docs/OVERVIEW.md` opening and Lab plugin section; `docs/design/system-architecture.md` Maintainer lab row; `README.md` lab rows and install instructions.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The lab plugin is gone. Its six maintainer skills run as Claude Code project skills at the repo root, and no install path copies them out.

## Contract

Cited, binding (DESIGN.md Phase 1 outcome):

- "`claude -p "/skills"`, run at the repo root on master, lists exactly these six project skills: `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`."
- "`python3 tools/transcript/find.py --help`, the first command of the `transcript-parser` skill, exits 0 from the repo root."
- "`.claude-plugin/marketplace.json` lists only `workflow`, and `test -e plugins` fails. Phase 3 is what creates `plugins/yakka`; this clause is the Phase 1 close, not the final layout."
- "The `tools/driver` tests pass with `LAB_SKILLS` replaced by a maintainer-skill list. They assert that `install.sh` in each mode (Claude local, Cursor local and cloud, OpenCode) and `tools/cloud-env/bootstrap-workflow-skills.sh`, run with `WORKFLOW_INSTALL_LAB=1` set, install none of those six skills."
- "Searching live files for `plugins/workflow-lab` or `lab-proposal` returns no hits. Live files exclude `docs/plans/`, dated `docs/lab/{PROPOSALS,RESEARCH}/` files and earlier `CHANGELOG.md` entries."
- "`docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `docs/design/system-architecture.md` and `README.md` describe one plugin plus maintainer skills."

Cited, binding (Maintainer skills contract): "Each skill directory moves with its `SKILL.md`, `briefs/`, `principles.md` and `reference.md`. The existing `name:` frontmatter works unchanged." "Repo-relative commands (`tools/...`) work as written." "In ARCHITECTURE it becomes `core never depends on maintainer skills`. The existing non-invoking prose mentions in core skills stay: `iterate` in `execute`, `workflow-tuning` in `comprehensive-review`." "`lab-proposal` is retired. Live links to lab skill paths are repointed."

Cited, binding (Plugin contract, this phase only): "`install.sh` (every mode) and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only. The `WORKFLOW_INSTALL_LAB` opt-in and every lab-install path are removed." "A phase that changes a shipped plugin file and can merge on its own bumps the plugin manifests one minor version." "The Claude, Cursor and Codex manifests move together." "`bin/VERSION` is not bumped before the rename phases."

Settled here, do not re-decide:

- **Move with `git mv`.** `plugins/workflow-lab/skills/{iterate,jev-variants,setup,transcript-parser,white-paper,workflow-tuning}` → `.claude/skills/<same name>`. Do not edit skill bodies. Delete `plugins/workflow-lab/skills/lab-proposal/` and the lab plugin manifests. After that, `plugins/` must not remain.
- **Marketplace.** Remove the `workflow-lab` entry from both marketplace files. Leave the `workflow` entry's `source` as it is (`github` / `repo` on Claude, `"./"` on Cursor). Phase 3 sets `source` to `plugins/yakka`. Do not create `plugins/`.
- **Versions.** `2.9.2` → `2.10.0` in `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, and `.codex-plugin/plugin.json` only. Do not change `bin/VERSION`.
- **CHANGELOG.** Add `## 2.10.0 — 2026-10-17` above `## 2.9.2`, stating that the lab plugin is removed and the six skills are maintainer project skills under `.claude/skills/`. The new entry must not contain the strings `plugins/workflow-lab` or `lab-proposal`.
- **Install.** Delete `CURSOR_LAB_PLUGIN`, `ensure_cursor_lab_plugin`, `WORKFLOW_OPENCODE_INCLUDE_LAB`, and every prompt or branch that copies or symlinks lab skills. `WORKFLOW_INSTALL_LAB=1` must be a no-op: the variable may still be set by an old caller, and it must not install anything. Do not change `ensure_cursor_core_plugin`. Cursor local still materializes the repo checkout; Phase 3 is what switches that copy to `plugins/yakka`.
- **Driver.** Replace `LAB_SKILLS` with one maintainer-skill tuple of the six names, in `check_skills.py`. Unattended `scan_core_skills` still requires only `CORE_SKILLS`. Point tests at the new tuple. Each of these runs sets `WORKFLOW_INSTALL_LAB=1` and asserts none of the six names appear at that mode's skill destination: Claude local (`WORKFLOW_INSTALL_MODE=claude-code`, `$HOME/.claude/skills/`), Cursor cloud (`WORKFLOW_INSTALL_MODE=cloud`, workspace `.cursor/skills/workflow/`), OpenCode (`WORKFLOW_INSTALL_MODE=opencode`), Cursor local (interactive plugin install must not create `~/.cursor/plugins/local/workflow-lab`), and `tools/cloud-env/bootstrap-workflow-skills.sh` (same workspace destination as cloud). A full checkout copy that happens to contain `.claude/skills/` is not an install of those skills.
- **Cursor symlinks.** Do not add `.cursor/skills/<name>` symlinks. Cursor's skills documentation loads `.claude/skills/` for compatibility (Assumption 9, checked while this brief was written). A directory symlink is forbidden by that assumption.
- **Docs.** One plugin, `workflow`, plus maintainer skills at `.claude/skills/`. Invariant 7's sentence becomes "core never depends on maintainer skills". Repoint Stable References and other live links at the moved skill paths. `docs/lab/FINDINGS.md`'s lab version line is drift: remove it rather than correcting `1.1.0`. `docs/lab/` stays the notebook. History is not rewritten: leave `docs/plans/` and dated files under `docs/lab/PROPOSALS/` and `docs/lab/RESEARCH/` (a dated file has `YYYY-MM-DD` in its path). `docs/lab/RESEARCH/INDEX.md` is not dated; it is live. `docs/lab/PROVENANCE-jev-hypotheses-2026-10-02.md` is outside those two directories; repoint its white-paper link. `docs/lab/CONSUMING_REPO.md` must stop telling anyone to set `WORKFLOW_INSTALL_LAB=1`.
- **Core skill prose.** Do not edit `skills/`. Mentions of `iterate` and `workflow-tuning` there stay.

## Changes

The decisions above are the change. The worker locates each lab branch in the owned files and applies them. Not a diff.

### Keep untouched

Skill text inside the six moved directories, including commands such as `python3 tools/transcript/find.py`. Core skills. Hook configs. The `workflow` marketplace `source` values. `bin/VERSION`. `ensure_cursor_core_plugin`. Dated research and proposal files, and every `docs/plans/` record except this unit's report.

## Done evidence

Identify the failing state before changing code. Report its output before and after.

Before:

- `python3 -c "import json; print([p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']])"` → includes `workflow-lab`.
- `test -d plugins/workflow-lab` → exit 0.
- `python3 -c "import ast,pathlib; t=ast.parse(pathlib.Path('tools/driver/check_skills.py').read_text()); print('LAB_SKILLS' in pathlib.Path('tools/driver/check_skills.py').read_text())"` → `True`.

After:

- `test ! -e plugins` → exit 0.
- `.claude/skills/` contains exactly `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`, each with its previous `name:` frontmatter.
- `python3 -c "import json; print([p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']])"` → `['workflow']`. The Cursor marketplace's plugin names are the same.
- `python3 tools/transcript/find.py --help` from the repo root → exit 0.
- `python3 -m unittest tools/driver/tests/test_check_skills.py tools/driver/tests/test_install_route.py` → pass. The runs that install set `WORKFLOW_INSTALL_LAB=1`.
- Live-file search, below, prints nothing.
- The three plugin manifests are `2.10.0`. `bin/VERSION` is unchanged.
- `git diff --stat -- plugins/workflow-lab .claude/skills` shows the six directories as renames, not as delete-plus-add of their contents. `lab-proposal` is a deletion.

Live-file search. Dated means the path contains `YYYY-MM-DD`. `docs/lab/RESEARCH/INDEX.md` is live. Earlier `CHANGELOG.md` entries are not. The new `2.10.0` entry is. All three commands expect no output:

```bash
git grep -n -e 'plugins/workflow-lab' -e 'lab-proposal' -- . \
  ':(exclude)docs/plans' ':(exclude)docs/lab/PROPOSALS' ':(exclude)docs/lab/RESEARCH' ':(exclude)CHANGELOG.md'
git grep -n -e 'plugins/workflow-lab' -e 'lab-proposal' -- docs/lab/PROPOSALS docs/lab/RESEARCH \
  | grep -v -E '[0-9]{4}-[0-9]{2}-[0-9]{2}'
awk 'BEGIN{p=0} /^## 2\.10\.0/{p=1; next} /^## /{p=0} p' CHANGELOG.md \
  | grep -e 'plugins/workflow-lab' -e 'lab-proposal' || true
```

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
