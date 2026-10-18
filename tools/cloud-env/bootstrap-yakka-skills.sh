#!/usr/bin/env bash
# Idempotent Cursor Cloud Agents environment bootstrap.
#
# Tracks codyhamilton/yakka on master, then installs core yakka skills into
# the consuming repo at .cursor/skills/yakka/ (marketplace plugins alone do
# not expose skills to cloud agents).
#
# Wire this script as the Cloud Agent environment install/setup command.
# A daily environment rebuild re-runs setup, which refreshes master and
# re-syncs skills.
#
# Core only — maintainer skills under .claude/skills/ are not installed here.
# WORKFLOW_INSTALL_LAB=1 is accepted for backward compatibility and ignored.
#
# Environment:
#   YAKKA_WORKSPACE        Consuming git repo root (default: git root or /workspace)
#   YAKKA_PLUGIN_CACHE     Git checkout cache (default: ~/.cache/yakka/src)
#   YAKKA_REPO_URL         Override clone URL (default: yakka on GitHub)
#   YAKKA_INSTALL_BRANCH   Branch to track (default: master)
#   YAKKA_INSTALL_SH       Skip fetch; run this installer instead (tests, vendored)
#
# Non-interactive. Safe to re-run. Exits non-zero only on hard failure.
set -euo pipefail

readonly DEFAULT_REPO="https://github.com/codyhamilton/yakka"
readonly DEFAULT_BRANCH="master"
readonly DEFAULT_CACHE="${HOME}/.cache/yakka/src"

REPO_URL="${YAKKA_REPO_URL:-$DEFAULT_REPO}"
BRANCH="${YAKKA_INSTALL_BRANCH:-$DEFAULT_BRANCH}"
CACHE="${YAKKA_PLUGIN_CACHE:-${YAKKA_INSTALL_SRC:-$DEFAULT_CACHE}}"

resolve_workspace() {
  if [[ -n "${YAKKA_WORKSPACE:-}" ]]; then
    echo "$(cd "$YAKKA_WORKSPACE" && pwd)"
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
  echo "Set YAKKA_WORKSPACE to the consuming repository root." >&2
  return 1
}

refresh_plugin_checkout() {
  local cache="$1"
  local branch="$2"
  local url="$3"

  mkdir -p "$(dirname "$cache")"

  if [[ -d "$cache/.git" ]]; then
    echo "Updating yakka checkout at $cache (origin/$branch)" >&2
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
  echo "Cloning yakka to $cache (branch $branch)" >&2
  git clone --depth 1 --branch "$branch" "$url" "$cache"
}

main() {
  local workspace
  workspace="$(resolve_workspace)"
  export YAKKA_WORKSPACE="$workspace"
  export YAKKA_INSTALL_MODE=cloud

  local installer=""

  if [[ -n "${YAKKA_INSTALL_SH:-}" ]]; then
    installer="$YAKKA_INSTALL_SH"
  else
    refresh_plugin_checkout "$CACHE" "$BRANCH" "$REPO_URL"
    installer="$CACHE/install.sh"
    if [[ ! -f "$installer" ]]; then
      echo "Missing installer at $installer after checkout." >&2
      exit 1
    fi
    export YAKKA_INSTALL_SKIP_REFRESH=1
  fi

  echo "Running yakka core skill install (cloud route) for workspace $workspace" >&2
  bash "$installer"
}

main "$@"
