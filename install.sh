#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO_HTTPS_URL="https://github.com/codyhamilton/workflow-plugin.git"
CURSOR_CORE_PLUGIN="${CURSOR_CORE_PLUGIN:-$HOME/.cursor/plugins/local/workflow}"
CURSOR_LAB_PLUGIN="${CURSOR_LAB_PLUGIN:-$HOME/.cursor/plugins/local/workflow-lab}"
INSTALL_SRC_CACHE="${WORKFLOW_INSTALL_SRC:-$HOME/.cache/workflow-plugin/install-src}"

ask() {
  local prompt="$1"
  local reply=""
  if [[ -t 0 ]]; then
    read -r -p "$prompt [y/N] " reply || true
  elif ( exec 3</dev/tty ) 2>/dev/null; then
    read -r -p "$prompt [y/N] " reply </dev/tty || return 1
  else
    return 1
  fi
  [[ "${reply,,}" == "y" ]]
}

repo_url() {
  if [[ -n "${WORKFLOW_REPO_URL:-}" ]]; then
    echo "$WORKFLOW_REPO_URL"
    return
  fi
  if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    git -C "$SCRIPT_DIR" config --get remote.origin.url || echo "$DEFAULT_REPO_HTTPS_URL"
  else
    echo "$DEFAULT_REPO_HTTPS_URL"
  fi
}

# When run as `curl … | bash`, the script is not on disk next to skills/. Clone
# (or refresh) a shallow checkout so the rest of the installer can copy files.
ensure_script_dir() {
  local candidate=""
  if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" != "-" ]]; then
    candidate="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -d "$candidate/skills" ]]; then
      echo "$candidate"
      return
    fi
  fi

  local url="$DEFAULT_REPO_HTTPS_URL"
  if [[ -n "${WORKFLOW_REPO_URL:-}" ]]; then
    url="$WORKFLOW_REPO_URL"
  fi

  mkdir -p "$(dirname "$INSTALL_SRC_CACHE")"
  if [[ -d "$INSTALL_SRC_CACHE/.git" ]]; then
    echo "  Refreshing installer checkout at $INSTALL_SRC_CACHE"
    git -C "$INSTALL_SRC_CACHE" pull --ff-only
  else
    if [[ -e "$INSTALL_SRC_CACHE" ]]; then
      rm -rf "$INSTALL_SRC_CACHE"
    fi
    echo "  Cloning installer checkout to $INSTALL_SRC_CACHE"
    git clone --depth 1 "$url" "$INSTALL_SRC_CACHE"
  fi
  echo "$INSTALL_SRC_CACHE"
}

SCRIPT_DIR="$(ensure_script_dir)"

# Cursor does not follow symlinks — clone a real checkout into ~/.cursor/plugins/local/.
# This checkout carries the whole repo, including plugins/workflow-lab/ — the
# core plugin's own manifest and skills/ live at the checkout root, unaffected.
ensure_cursor_core_plugin() {
  mkdir -p "$(dirname "$CURSOR_CORE_PLUGIN")"
  local url
  url="$(repo_url)"
  if [[ -d "$CURSOR_CORE_PLUGIN/.git" ]]; then
    echo "  Updating plugin at $CURSOR_CORE_PLUGIN"
    git -C "$CURSOR_CORE_PLUGIN" pull --ff-only
  else
    if [[ -e "$CURSOR_CORE_PLUGIN" ]]; then
      echo "  Replacing existing install at $CURSOR_CORE_PLUGIN"
      rm -rf "$CURSOR_CORE_PLUGIN"
    fi
    echo "  Cloning plugin to $CURSOR_CORE_PLUGIN"
    git clone --depth 1 "$url" "$CURSOR_CORE_PLUGIN"
  fi
}

# The lab plugin is a subtree of the same repo (plugins/workflow-lab/), not a
# separate remote — copy it out of the already-current core checkout rather
# than cloning again. Requires the core plugin to have been installed first.
ensure_cursor_lab_plugin() {
  local src="$CURSOR_CORE_PLUGIN/plugins/workflow-lab"
  if [[ ! -d "$src" ]]; then
    echo "  workflow-lab not found in core checkout at $src — skipping."
    return
  fi
  if [[ -e "$CURSOR_LAB_PLUGIN" ]]; then
    echo "  Replacing existing install at $CURSOR_LAB_PLUGIN"
    rm -rf "$CURSOR_LAB_PLUGIN"
  fi
  mkdir -p "$(dirname "$CURSOR_LAB_PLUGIN")"
  echo "  Copying lab plugin to $CURSOR_LAB_PLUGIN"
  cp -rL "$src" "$CURSOR_LAB_PLUGIN"
}

install_skills() {
  local src="$1"
  local dest_root="$2"
  mkdir -p "$dest_root"
  for skill_dir in "$src"/*/; do
    skill_name="$(basename "$skill_dir")"
    dest="$dest_root/$skill_name"
    if [[ -d "$dest" ]]; then
      echo "  Replacing existing skill: $skill_name"
      rm -rf "$dest"
    else
      echo "  Installing skill: $skill_name"
    fi
    cp -rL "$skill_dir" "$dest"
  done
}

echo "workflow-plugin installer"
echo "========================="

# Claude Code — copy skills to ~/.claude/skills/
if [[ -d "$HOME/.claude" ]]; then
  if ask "Install workflow core skills (plan, execute, comprehensive-review, post-build) into Claude Code (~/.claude/skills/)?"; then
    install_skills "$SCRIPT_DIR/skills" "$HOME/.claude/skills"
    echo "  Done. Core skills available immediately in Claude Code."
  fi
  echo ""
  if ask "Also install workflow-lab skills (setup, iterate, transcript-parser, workflow-tuning)? Local/interactive only — skip this in cloud build environments."; then
    install_skills "$SCRIPT_DIR/plugins/workflow-lab/skills" "$HOME/.claude/skills"
    echo "  Done. Lab skills available immediately in Claude Code."
  fi
else
  echo "Claude Code (~/.claude) not found — skipping."
fi

echo ""

# Cursor — clone repo into ~/.cursor/plugins/local/workflow (core), then
# optionally copy the lab subtree into ~/.cursor/plugins/local/workflow-lab
if [[ -d "$HOME/.cursor" ]]; then
  if ask "Install workflow core plugin into Cursor (~/.cursor/plugins/local/)?"; then
    ensure_cursor_core_plugin
    echo "  Done. Restart Cursor to pick up the plugin."
    echo "  Plugin path: $CURSOR_CORE_PLUGIN (git pull + re-run install.sh to update)"
    echo ""
    if ask "Also install workflow-lab plugin into Cursor?"; then
      ensure_cursor_lab_plugin
      echo "  Done. Restart Cursor to pick up the lab plugin."
      echo "  Plugin path: $CURSOR_LAB_PLUGIN (re-run install.sh to update; tracks the core checkout)"
    fi
  fi
else
  echo "Cursor (~/.cursor) not found — skipping."
fi

echo ""
echo "Installation complete."
