#!/usr/bin/env bash
# Cursor cloud environment install (image bake). Not a session hook.
#
# Cursor cloud agents boot from a prebaked image and discover project skills
# when the agent process starts. There is no SessionStart/reloadSkills hook.
# Run this once from the environment setup script, then snapshot the image.
# The next agent boot must already have the six core skill directories on disk.
#
# Core only — never installs workflow-lab.
#
#   export WORKFLOW_WORKSPACE=/path/to/consuming/repo   # optional; git root or /workspace
#   docs/lab/bootstrap/cursor-cloud-setup.sh
#
# WORKFLOW_INSTALL_SH, when set, is the installer to run (tests, vendored copy).
# Otherwise a checkout that contains skills/design/install.sh is used, else curl.
set -euo pipefail

if [[ -z "${WORKFLOW_WORKSPACE:-}" ]]; then
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    WORKFLOW_WORKSPACE="$(git rev-parse --show-toplevel)"
  elif [[ -d /workspace/.git ]]; then
    WORKFLOW_WORKSPACE=/workspace
  else
    echo "Set WORKFLOW_WORKSPACE to the consuming repository root." >&2
    exit 1
  fi
fi
export WORKFLOW_WORKSPACE

# Explicit mode wins over ambient Claude/Cursor variables in the image build.
export WORKFLOW_INSTALL_MODE=cloud

if [[ -n "${WORKFLOW_INSTALL_SH:-}" ]]; then
  bash "$WORKFLOW_INSTALL_SH"
elif [[ -f "$WORKFLOW_WORKSPACE/install.sh" && -d "$WORKFLOW_WORKSPACE/skills/design" ]]; then
  bash "$WORKFLOW_WORKSPACE/install.sh"
else
  curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/install.sh | bash
fi
