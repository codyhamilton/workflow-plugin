#!/usr/bin/env bash
# Cursor cloud environment install (image bake). Not a session hook.
#
# Thin entry point — canonical logic lives in tools/cloud-env/bootstrap-workflow-skills.sh
# so consuming repos can point Cloud Agent setup at either path inside workflow-plugin.
#
#   export WORKFLOW_WORKSPACE=/path/to/consuming/repo   # optional; git root or /workspace
#   docs/lab/bootstrap/cursor-cloud-setup.sh
#
# See tools/cloud-env/bootstrap-workflow-skills.sh for environment variables.
set -euo pipefail

_BOOTSTRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_PLUGIN_ROOT="$(cd "$_BOOTSTRAP_DIR/../../.." && pwd)"
exec bash "$_PLUGIN_ROOT/tools/cloud-env/bootstrap-workflow-skills.sh" "$@"
