#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/plugins/workflow"

ask() {
  local prompt="$1"
  local reply
  read -r -p "$prompt [y/N] " reply
  [[ "${reply,,}" == "y" ]]
}

echo "workflow-plugin installer"
echo "========================="

# Claude Code — copy skills to ~/.claude/skills/
if [[ -d "$HOME/.claude" ]]; then
  if ask "Install workflow skills into Claude Code (~/.claude/skills/)?"; then
    CLAUDE_SKILLS="$HOME/.claude/skills"
    mkdir -p "$CLAUDE_SKILLS"
    for skill_dir in "$PLUGIN_DIR/skills"/*/; do
      skill_name="$(basename "$skill_dir")"
      dest="$CLAUDE_SKILLS/$skill_name"
      if [[ -d "$dest" ]]; then
        echo "  Replacing existing skill: $skill_name"
        rm -rf "$dest"
      else
        echo "  Installing skill: $skill_name"
      fi
      cp -r "$skill_dir" "$dest"
    done
    echo "  Done. Skills available immediately in Claude Code."
  fi
else
  echo "Claude Code (~/.claude) not found — skipping."
fi

echo ""

# Cursor — install plugin to ~/.cursor/plugins/local/
if [[ -d "$HOME/.cursor" ]]; then
  if ask "Install workflow plugin into Cursor (~/.cursor/plugins/local/)?"; then
    CURSOR_LOCAL="$HOME/.cursor/plugins/local/workflow"
    if [[ -d "$CURSOR_LOCAL" ]]; then
      echo "  Replacing existing Cursor plugin."
      rm -rf "$CURSOR_LOCAL"
    fi
    mkdir -p "$(dirname "$CURSOR_LOCAL")"
    cp -r "$PLUGIN_DIR" "$CURSOR_LOCAL"
    echo "  Done. Restart Cursor to pick up the plugin."
  fi
else
  echo "Cursor (~/.cursor) not found — skipping."
fi

echo ""
echo "Installation complete."
