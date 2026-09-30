# Cloud Agent environment bootstrap

Cursor Cloud Agents discover **project** skills under `.cursor/skills/` when the agent process starts. Marketplace plugin installs under `~/.cursor/plugins/` are not enough on cloud VMs — core workflow skills must be copied into the consuming repo workspace.

## Script

[`bootstrap-workflow-skills.sh`](bootstrap-workflow-skills.sh):

1. Clones or updates `https://github.com/codyhamilton/workflow-plugin` on **`master`** in a cache directory (default `~/.cache/workflow-plugin`) via `git fetch` and `git reset --hard origin/master`.
2. Runs `install.sh` with `WORKFLOW_INSTALL_MODE=cloud`, syncing the six core skills into `<workspace>/.cursor/skills/workflow/`.
3. Is idempotent and non-interactive — safe on every environment setup run.

Legacy alias: [`docs/lab/bootstrap/cursor-cloud-setup.sh`](../../docs/lab/bootstrap/cursor-cloud-setup.sh) execs this script.

## Cursor Cloud Agents setup command

In the consuming repo’s Cursor **environment** configuration, set the install/setup command to run before agents start (exact UI field name may vary):

```bash
export WORKFLOW_WORKSPACE="${WORKFLOW_WORKSPACE:-/workspace}"
bash -lc 'curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/tools/cloud-env/bootstrap-workflow-skills.sh | bash'
```

If workflow-plugin is already vendored or cloned in the image:

```bash
export WORKFLOW_WORKSPACE="$(git rev-parse --show-toplevel)"
bash /path/to/workflow-plugin/tools/cloud-env/bootstrap-workflow-skills.sh
```

Add `<repo>/.cursor/skills/workflow/` to `.gitignore`.

**Daily rebuild:** when the environment is rebuilt on a schedule, this command runs again and pulls the latest `master`, so skills stay current without pinning SHAs.

After setup (no network required):

```bash
python3 /path/to/workflow-plugin/tools/driver/check_skills.py
```

Exit `0` when all six core skills are present.

## Optional lab skills

Unattended cloud bootstrap installs **core only**. To also copy workflow-lab skills into `.cursor/skills/workflow-lab/`, set `WORKFLOW_INSTALL_LAB=1`. Lab skills are not required for `check_skills.py` or the phase driver loop.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `WORKFLOW_WORKSPACE` | git root or `/workspace` | Consuming repository |
| `WORKFLOW_PLUGIN_CACHE` | `~/.cache/workflow-plugin` | Git checkout cache |
| `WORKFLOW_REPO_URL` | workflow-plugin GitHub URL | Fork or mirror |
| `WORKFLOW_INSTALL_BRANCH` | `master` | Tracked branch |
| `WORKFLOW_INSTALL_SH` | — | Skip fetch; run alternate installer (tests) |
| `WORKFLOW_INSTALL_LAB` | unset | Set to `1` to copy lab skills |

More context: [`docs/lab/CONSUMING_REPO.md`](../../docs/lab/CONSUMING_REPO.md).
