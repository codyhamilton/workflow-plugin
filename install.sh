#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_PLUGIN="${CURSOR_PLUGIN:-$HOME/.cursor/plugins/local/workflow}"
DEFAULT_REPO_URL="git@github.com:codyhamilton/workflow-plugin.git"

ask() {
  local prompt="$1"
  local reply
  read -r -p "$prompt [y/N] " reply
  [[ "${reply,,}" == "y" ]]
}

repo_url() {
  if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    git -C "$SCRIPT_DIR" config --get remote.origin.url || echo "$DEFAULT_REPO_URL"
  else
    echo "$DEFAULT_REPO_URL"
  fi
}

# Cursor does not follow symlinks — clone a real checkout into ~/.cursor/plugins/local/.
ensure_cursor_plugin() {
  mkdir -p "$(dirname "$CURSOR_PLUGIN")"
  local url
  url="$(repo_url)"
  if [[ -d "$CURSOR_PLUGIN/.git" ]]; then
    echo "  Updating plugin at $CURSOR_PLUGIN"
    git -C "$CURSOR_PLUGIN" pull --ff-only
  else
    if [[ -e "$CURSOR_PLUGIN" ]]; then
      echo "  Replacing existing install at $CURSOR_PLUGIN"
      rm -rf "$CURSOR_PLUGIN"
    fi
    echo "  Cloning plugin to $CURSOR_PLUGIN"
    git clone --depth 1 "$url" "$CURSOR_PLUGIN"
  fi
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
  if ask "Install workflow skills into Claude Code (~/.claude/skills/)?"; then
    install_skills "$SCRIPT_DIR/skills" "$HOME/.claude/skills"
    echo "  Done. Skills available immediately in Claude Code."
  fi
else
  echo "Claude Code (~/.claude) not found — skipping."
fi

echo ""

# Cursor — clone repo into ~/.cursor/plugins/local/workflow
if [[ -d "$HOME/.cursor" ]]; then
  if ask "Install workflow plugin into Cursor (~/.cursor/plugins/local/)?"; then
    ensure_cursor_plugin
    echo "  Done. Restart Cursor to pick up the plugin."
    echo "  Plugin path: $CURSOR_PLUGIN (git pull + re-run install.sh to update)"
  fi
else
  echo "Cursor (~/.cursor) not found — skipping."
fi

echo ""
echo "Installation complete."
