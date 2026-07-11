#!/usr/bin/env bash
# Non-interactive installer for workflow-plugin skills.
#
# Examples (cloud agent / automation):
#   ./install.sh --target cursor
#   ./install.sh --target cursor --target claude --ref master
#   ./install.sh --target all --ref abcdef1
#
# Interactive (no --target): prompts for each detected harness.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_PLUGIN="${CURSOR_PLUGIN:-$HOME/.cursor/plugins/local/workflow}"
CURSOR_SKILLS="${CURSOR_SKILLS:-$HOME/.cursor/skills}"
CLAUDE_SKILLS="${CLAUDE_SKILLS:-$HOME/.claude/skills}"
CODEX_SKILLS="${CODEX_SKILLS:-$HOME/.codex/skills}"

TARGETS=()
REF=""
INTERACTIVE=1
DRY_RUN=0
SOURCE_DIR="$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --target <cursor|claude|codex|all>
                      Install into the given harness. Repeatable.
                      'all' expands to cursor + claude + codex.
                      When omitted, runs interactively for detected harnesses.
  --ref <tag-or-sha>  Checkout this git ref in the install source before copying.
                      Defaults to the current checkout (typically master).
  --source <dir>      Skill pack root to install from (default: this repo).
  --cursor-plugin <path>
                      Cursor plugin checkout path
                      (default: ~/.cursor/plugins/local/workflow).
  --cursor-skills <path>
                      Cursor user skills directory (default: ~/.cursor/skills).
  --claude-skills <path>
                      Claude skills directory (default: ~/.claude/skills).
  --codex-skills <path>
                      Codex skills directory (default: ~/.codex/skills).
  --dry-run           Print actions without writing.
  -h, --help          Show this help.

Cursor installs:
  1) Copy skills into ~/.cursor/skills/ (works for Cursor Cloud agents / automations
     without Team Marketplace access).
  2) Mirror a git checkout into ~/.cursor/plugins/local/workflow for desktop plugin
     discovery when ~/.cursor exists.

Protocol:
  Reads workflow-protocol.json at the skill-pack root. Refuses to install if missing
  or if workflow-protocol is unsupported by this installer.
EOF
}

log() { printf '%s\n' "$*"; }
run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "  [dry-run] $*"
  else
    "$@"
  fi
}

ask() {
  local prompt="$1"
  local reply
  read -r -p "$prompt [y/N] " reply
  [[ "${reply,,}" == "y" ]]
}

require_protocol() {
  local protocol_file="$SOURCE_DIR/workflow-protocol.json"
  if [[ ! -f "$protocol_file" ]]; then
    echo "error: missing workflow-protocol.json in $SOURCE_DIR" >&2
    exit 1
  fi
  local version
  version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("workflow-protocol",""))' "$protocol_file")"
  if [[ "$version" != "1" ]]; then
    echo "error: unsupported workflow-protocol version: ${version:-<missing>} (installer supports 1)" >&2
    exit 1
  fi
  log "workflow-protocol: $version"
}

checkout_ref() {
  local ref="$1"
  if [[ -z "$ref" ]]; then
    return 0
  fi
  if ! git -C "$SOURCE_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "error: --ref requires a git checkout at $SOURCE_DIR" >&2
    exit 1
  fi
  log "Checking out ref: $ref"
  # Best-effort fetch; local refs/SHAs still work without network.
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "  [dry-run] git -C $SOURCE_DIR fetch --tags --force --prune origin $ref"
    log "  [dry-run] git -C $SOURCE_DIR checkout --detach $ref"
  else
    git -C "$SOURCE_DIR" fetch --tags --force --prune origin "$ref" 2>/dev/null || true
    git -C "$SOURCE_DIR" checkout --detach "$ref"
  fi
}

install_protocol_sidecar() {
  local dest_root="$1"
  local label="$2"
  run mkdir -p "$dest_root/_workflow-protocol"
  run cp -rL "$SOURCE_DIR/protocol/." "$dest_root/_workflow-protocol/"
  run cp -f "$SOURCE_DIR/workflow-protocol.json" "$dest_root/_workflow-protocol/workflow-protocol.json"
  log "  [$label] protocol → $dest_root/_workflow-protocol/"
}

install_skills_copy() {
  local dest_root="$1"
  local label="$2"
  run mkdir -p "$dest_root"
  local skill_dir skill_name dest
  for skill_dir in "$SOURCE_DIR/skills"/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    dest="$dest_root/$skill_name"
    if [[ -d "$dest" ]]; then
      log "  [$label] replacing: $skill_name"
      run rm -rf "$dest"
    else
      log "  [$label] installing: $skill_name"
    fi
    run cp -rL "$skill_dir" "$dest"
  done
  install_protocol_sidecar "$dest_root" "$label"
}

ensure_cursor_plugin() {
  # Prefer syncing the already-resolved SOURCE_DIR (honors --ref) over a fresh
  # remote clone, so cloud-agent installs get exactly the checkout they prepared.
  run mkdir -p "$(dirname "$CURSOR_PLUGIN")"
  if [[ "$SOURCE_DIR" -ef "$CURSOR_PLUGIN" ]]; then
    log "  [cursor-plugin] source is already $CURSOR_PLUGIN — nothing to mirror"
    return 0
  fi
  if [[ -e "$CURSOR_PLUGIN" ]]; then
    log "  [cursor-plugin] replacing existing install at $CURSOR_PLUGIN"
    run rm -rf "$CURSOR_PLUGIN"
  fi
  log "  [cursor-plugin] mirroring $SOURCE_DIR → $CURSOR_PLUGIN"
  run mkdir -p "$CURSOR_PLUGIN"
  # Copy contents; keep a .git when present so desktop users can git pull later.
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "  [dry-run] cp -a $SOURCE_DIR/. $CURSOR_PLUGIN/"
  else
    cp -a "$SOURCE_DIR"/. "$CURSOR_PLUGIN/"
  fi
}

install_cursor() {
  log "Installing for Cursor..."
  # Skills dir is the primary path for cloud agents / automations without marketplace.
  install_skills_copy "$CURSOR_SKILLS" "cursor-skills"
  log "  Skills path: $CURSOR_SKILLS"
  # Plugin checkout helps Cursor desktop local-plugin discovery and keeps protocol paths stable.
  if [[ -d "$HOME/.cursor" ]] || [[ "${CURSOR_FORCE_PLUGIN:-0}" == "1" ]]; then
    ensure_cursor_plugin
    log "  Plugin path: $CURSOR_PLUGIN"
    log "  Restart Cursor desktop to pick up the local plugin if needed."
  else
    log "  ~/.cursor not found — skipped plugins/local checkout (skills install still applied)."
  fi
}

install_claude() {
  log "Installing for Claude Code..."
  install_skills_copy "$CLAUDE_SKILLS" "claude"
  log "  Skills path: $CLAUDE_SKILLS"
}

install_codex() {
  log "Installing for Codex..."
  install_skills_copy "$CODEX_SKILLS" "codex"
  log "  Skills path: $CODEX_SKILLS"
}

expand_targets() {
  local -a expanded=()
  local t
  for t in "${TARGETS[@]}"; do
    case "$t" in
      all) expanded+=(cursor claude codex) ;;
      cursor|claude|codex) expanded+=("$t") ;;
      *)
        echo "error: unknown --target $t (expected cursor|claude|codex|all)" >&2
        exit 1
        ;;
    esac
  done
  TARGETS=()
  local seen="|"
  for t in "${expanded[@]}"; do
    if [[ "$seen" != *"|$t|"* ]]; then
      TARGETS+=("$t")
      seen+="$t|"
    fi
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { echo "error: --target requires a value" >&2; exit 1; }
      TARGETS+=("$2")
      INTERACTIVE=0
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || { echo "error: --ref requires a value" >&2; exit 1; }
      REF="$2"
      shift 2
      ;;
    --source)
      [[ $# -ge 2 ]] || { echo "error: --source requires a value" >&2; exit 1; }
      SOURCE_DIR="$(cd "$2" && pwd)"
      shift 2
      ;;
    --cursor-plugin)
      [[ $# -ge 2 ]] || { echo "error: --cursor-plugin requires a value" >&2; exit 1; }
      CURSOR_PLUGIN="$2"
      shift 2
      ;;
    --cursor-skills)
      [[ $# -ge 2 ]] || { echo "error: --cursor-skills requires a value" >&2; exit 1; }
      CURSOR_SKILLS="$2"
      shift 2
      ;;
    --claude-skills)
      [[ $# -ge 2 ]] || { echo "error: --claude-skills requires a value" >&2; exit 1; }
      CLAUDE_SKILLS="$2"
      shift 2
      ;;
    --codex-skills)
      [[ $# -ge 2 ]] || { echo "error: --codex-skills requires a value" >&2; exit 1; }
      CODEX_SKILLS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

echo "workflow-plugin installer"
echo "========================="

if [[ ${#TARGETS[@]} -gt 0 ]]; then
  expand_targets
fi

checkout_ref "$REF"
require_protocol

if [[ "$INTERACTIVE" -eq 1 ]]; then
  log "Interactive mode (pass --target for non-interactive installs)."
  log ""

  if [[ -d "$HOME/.claude" ]]; then
    if ask "Install workflow skills into Claude Code ($CLAUDE_SKILLS)?"; then
      install_claude
    fi
  else
    log "Claude Code (~/.claude) not found — skipping."
  fi

  log ""

  if [[ -d "$HOME/.cursor" ]]; then
    if ask "Install workflow skills into Cursor ($CURSOR_SKILLS + local plugin)?"; then
      install_cursor
    fi
  else
    log "Cursor (~/.cursor) not found — skipping."
  fi

  log ""

  if [[ -d "$HOME/.codex" ]]; then
    if ask "Install workflow skills into Codex ($CODEX_SKILLS)?"; then
      install_codex
    fi
  else
    log "Codex (~/.codex) not found — skipping."
  fi
else
  for t in "${TARGETS[@]}"; do
    case "$t" in
      cursor) install_cursor ;;
      claude) install_claude ;;
      codex) install_codex ;;
    esac
    log ""
  done
fi

log "Installation complete."
log "Skill names: workflow-plan, workflow-execute, workflow-setup, comprehensive-review, iterate, workflow-tuning, transcript-parser"
