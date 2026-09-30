#!/usr/bin/env bash
# Idempotent Cursor Cloud Agents environment bootstrap.
#
# Tracks codyhamilton/workflow-plugin on master, then installs core workflow
# skills into the consuming repo at .cursor/skills/workflow/ (marketplace
# plugins alone do not expose skills to cloud agents).
#
# Wire this script as the Cloud Agent environment install/setup command.
# A daily environment rebuild re-runs setup, which refreshes master and
# re-syncs skills.
#
# Core only — workflow-lab is not installed unless WORKFLOW_INSTALL_LAB=1
# (opt-in; not required for the driver loop).
#
# Environment:
#   WORKFLOW_WORKSPACE     Consuming git repo root (default: git root or /workspace)
#   WORKFLOW_PLUGIN_CACHE  Git checkout cache (default: ~/.cache/workflow-plugin)
#   WORKFLOW_REPO_URL      Override clone URL (default: workflow-plugin on GitHub)
#   WORKFLOW_INSTALL_BRANCH  Branch to track (default: master)
#   WORKFLOW_INSTALL_SH    Skip fetch; run this installer instead (tests, vendored)
#   WORKFLOW_INSTALL_LAB=1 Also copy lab skills into .cursor/skills/workflow-lab/
#
# Non-interactive. Safe to re-run. Exits non-zero only on hard failure.
set -euo pipefail

readonly DEFAULT_REPO="https://github.com/codyhamilton/workflow-plugin.git"
readonly DEFAULT_BRANCH="master"
readonly DEFAULT_CACHE="${HOME}/.cache/workflow-plugin"

REPO_URL="${WORKFLOW_REPO_URL:-$DEFAULT_REPO}"
BRANCH="${WORKFLOW_INSTALL_BRANCH:-$DEFAULT_BRANCH}"
CACHE="${WORKFLOW_PLUGIN_CACHE:-${WORKFLOW_INSTALL_SRC:-$DEFAULT_CACHE}}"

resolve_workspace() {
  if [[ -n "${WORKFLOW_WORKSPACE:-}" ]]; then
    echo "$(cd "$WORKFLOW_WORKSPACE" && pwd)"
    return 0
  fi
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    git rev-parse --show-toplevel
    return 0
  fi
  if [[ -d /workspace/.git ]]; then
    echo /workspace
    return 0
  fi
  echo "Set WORKFLOW_WORKSPACE to the consuming repository root." >&2
  return 1
}

refresh_plugin_checkout() {
  local cache="$1"
  local branch="$2"
  local url="$3"

  mkdir -p "$(dirname "$cache")"

  if [[ -d "$cache/.git" ]]; then
    echo "Updating workflow-plugin checkout at $cache (origin/$branch)" >&2
    git -C "$cache" remote get-url origin >/dev/null 2>&1 || \
      git -C "$cache" remote add origin "$url"
    if ! git -C "$cache" fetch --depth 1 origin "$branch" 2>/dev/null; then
      git -C "$cache" fetch origin "$branch"
    fi
    git -C "$cache" checkout -B "$branch" "origin/$branch" 2>/dev/null || true
    git -C "$cache" reset --hard "origin/$branch"
    return 0
  fi

  if [[ -e "$cache" ]]; then
    rm -rf "$cache"
  fi
  echo "Cloning workflow-plugin to $cache (branch $branch)" >&2
  git clone --depth 1 --branch "$branch" "$url" "$cache"
}

install_lab_skills_optional() {
  [[ "${WORKFLOW_INSTALL_LAB:-}" == "1" ]] || return 0

  local workspace="$1"
  local plugin_root="$2"
  local lab_src="$plugin_root/plugins/workflow-lab/skills"
  local dest="$workspace/.cursor/skills/workflow-lab"

  if [[ ! -d "$lab_src" ]]; then
    echo "WORKFLOW_INSTALL_LAB=1 but lab skills missing at $lab_src" >&2
    return 1
  fi

  echo "Installing optional workflow-lab skills to $dest" >&2
  mkdir -p "$dest"
  local skill_dir skill_name
  for skill_dir in "$lab_src"/*/; do
    skill_name="$(basename "$skill_dir")"
    rm -rf "$dest/$skill_name"
    cp -a "$skill_dir" "$dest/$skill_name"
  done
}

main() {
  local workspace
  workspace="$(resolve_workspace)"
  export WORKFLOW_WORKSPACE="$workspace"
  export WORKFLOW_INSTALL_MODE=cloud

  local installer=""
  local plugin_root=""

  if [[ -n "${WORKFLOW_INSTALL_SH:-}" ]]; then
    installer="$WORKFLOW_INSTALL_SH"
    plugin_root="$(dirname "$installer")"
  else
    refresh_plugin_checkout "$CACHE" "$BRANCH" "$REPO_URL"
    plugin_root="$CACHE"
    installer="$CACHE/install.sh"
    if [[ ! -f "$installer" ]]; then
      echo "Missing installer at $installer after checkout." >&2
      exit 1
    fi
    export WORKFLOW_INSTALL_SKIP_REFRESH=1
  fi

  echo "Running workflow core skill install (cloud route) for workspace $workspace" >&2
  bash "$installer"

  install_lab_skills_optional "$workspace" "$plugin_root"
}

main "$@"
