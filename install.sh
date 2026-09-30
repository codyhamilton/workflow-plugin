#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO_HTTPS_URL="https://github.com/codyhamilton/workflow-plugin.git"
INSTALL_BRANCH="${WORKFLOW_INSTALL_BRANCH:-master}"
CURSOR_CORE_PLUGIN="${CURSOR_CORE_PLUGIN:-$HOME/.cursor/plugins/local/workflow}"
CURSOR_LAB_PLUGIN="${CURSOR_LAB_PLUGIN:-$HOME/.cursor/plugins/local/workflow-lab}"
INSTALL_SRC_CACHE="${WORKFLOW_INSTALL_SRC:-$HOME/.cache/workflow-plugin/install-src}"
WORKFLOW_WORKSPACE_SKILLS_NAME="${WORKFLOW_WORKSPACE_SKILLS_NAME:-workflow}"
OPENCODE_SKILLS_ROOT="${WORKFLOW_OPENCODE_SKILLS:-$HOME/.config/opencode/skills}"

# Capture before any function runs — inside functions BASH_SOURCE[0] is the
# function name (e.g. "main" for piped scripts), not the installer path.
_INSTALLER_SOURCE="${BASH_SOURCE[0]:-}"

is_cursor_cloud_agent() {
  [[ "${WORKFLOW_INSTALL_MODE:-}" == "cloud" ]] && return 0
  [[ "${CURSOR_AGENT:-}" == "1" ]] && return 0
  [[ "${HOSTNAME:-}" == "cursor" ]] && return 0
  [[ -f "$HOME/.cursor/plugins/cache/.cloud-plugin-manifest.json" ]] && return 0
  return 1
}

# Claude Code (CLI and web) sets these for every session, local or remote —
# including Bash-tool subprocesses, which have no TTY either way. Check this
# before falling through to the generic non-interactive/Cursor branch so a
# Claude Code session never gets routed into .cursor/skills/.
is_claude_code_agent() {
  [[ "${WORKFLOW_INSTALL_MODE:-}" == "claude-code" ]] && return 0
  [[ "${CLAUDECODE:-}" == "1" ]] && return 0
  [[ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ]] && return 0
  [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] && return 0
  return 1
}

can_prompt_interactively() {
  [[ -t 0 ]] || ( exec 3</dev/tty ) 2>/dev/null
}

is_interactive_install() {
  [[ "${WORKFLOW_INSTALL_MODE:-}" == "interactive" ]] && can_prompt_interactively
}

# curl | bash delivers the script on stdin — BASH_SOURCE is "-" or unset, not a file path.
is_piped_installer() {
  local src="${_INSTALLER_SOURCE:-}"
  [[ -z "$src" || "$src" == "-" || ! -f "$src" ]]
}

should_auto_install_cursor_core() {
  is_interactive_install && return 1
  [[ "${WORKFLOW_INSTALL_MODE:-}" == "interactive" ]] && return 1

  # Runtime cloud agent signals (may be unset during environment setup).
  is_cursor_cloud_agent && return 0

  # curl | bash in environment setup: no TTY, no prompts possible — install core.
  if is_piped_installer || ! can_prompt_interactively; then
    return 0
  fi

  return 1
}

auto_install_reason() {
  if [[ "${WORKFLOW_INSTALL_MODE:-}" == "opencode" ]]; then
    echo "WORKFLOW_INSTALL_MODE=opencode"
  elif [[ "${WORKFLOW_INSTALL_MODE:-}" == "claude-code" ]]; then
    echo "WORKFLOW_INSTALL_MODE=claude-code"
  elif [[ "${CLAUDECODE:-}" == "1" ]]; then
    echo "CLAUDECODE=1"
  elif [[ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ]]; then
    echo "CLAUDE_CODE_ENTRYPOINT=${CLAUDE_CODE_ENTRYPOINT}"
  elif [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]; then
    echo "CLAUDE_CODE_REMOTE=true"
  elif [[ "${WORKFLOW_INSTALL_MODE:-}" == "cloud" ]]; then
    echo "WORKFLOW_INSTALL_MODE=cloud"
  elif [[ "${CURSOR_AGENT:-}" == "1" ]]; then
    echo "CURSOR_AGENT=1"
  elif [[ "${HOSTNAME:-}" == "cursor" ]]; then
    echo "HOSTNAME=cursor"
  elif [[ -f "$HOME/.cursor/plugins/cache/.cloud-plugin-manifest.json" ]]; then
    echo "cloud plugin manifest present"
  elif is_piped_installer; then
    echo "piped installer (curl | bash)"
  else
    echo "non-interactive shell"
  fi
}

find_workspace_root() {
  if [[ -n "${WORKFLOW_WORKSPACE:-}" ]]; then
    echo "$(cd "$WORKFLOW_WORKSPACE" && pwd)"
    return 0
  fi
  if git rev-parse --show-toplevel &>/dev/null; then
    git rev-parse --show-toplevel
    return 0
  fi
  if [[ -d /workspace/.git ]]; then
    echo /workspace
    return 0
  fi
  return 1
}

workspace_skills_dest() {
  local workspace="$1"
  echo "$workspace/.cursor/skills/$WORKFLOW_WORKSPACE_SKILLS_NAME"
}

# Explicit WORKFLOW_INSTALL_MODE wins over ambient harness variables so an
# image bake (mode=cloud) is not captured by a stray CLAUDECODE, and a
# Claude hook (mode=claude-code) is not captured by HOSTNAME=cursor.
# Unset mode keeps the historical order: Claude signals, then Cursor cloud
# signals, then piped or non-interactive (workspace skills, core only).
resolve_install_route() {
  local mode="${WORKFLOW_INSTALL_MODE:-}"
  case "$mode" in
    claude-code) echo claude-code; return ;;
    cloud) echo cursor-cloud; return ;;
    opencode) echo opencode; return ;;
    interactive) echo interactive; return ;;
  esac
  if is_claude_code_agent; then
    echo claude-code
    return
  fi
  if should_auto_install_cursor_core; then
    echo cursor-cloud
    return
  fi
  echo interactive
}

print_install_route() {
  local route dest reason core workspace
  route="$(resolve_install_route)"
  core="true"
  dest=""
  reason="$(auto_install_reason)"
  case "$route" in
    claude-code)
      dest="${HOME}/.claude/skills"
      ;;
    opencode)
      dest="$OPENCODE_SKILLS_ROOT"
      ;;
    cursor-cloud)
      if workspace="$(find_workspace_root)"; then
        dest="$(workspace_skills_dest "$workspace")"
      else
        reason="${reason}; workspace root not found"
      fi
      ;;
    interactive)
      core="false"
      reason="interactive prompts"
      ;;
  esac
  python3 -c 'import json,sys; print(json.dumps({"route":sys.argv[1],"core_only":sys.argv[2]=="true","dest":sys.argv[3] or None,"reason":sys.argv[4]}, indent=2))' \
    "$route" "$core" "$dest" "$reason"
}

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

refresh_git_checkout() {
  # Tests and offline copies set this. Production installs still update.
  [[ "${WORKFLOW_INSTALL_SKIP_REFRESH:-}" == "1" ]] && return 0
  local dir="$1"
  [[ -d "$dir/.git" ]] || return 0
  git -C "$dir" remote get-url origin &>/dev/null || return 0

  echo "  Updating checkout at $dir (origin/$INSTALL_BRANCH)" >&2
  if ! git -C "$dir" fetch --depth 1 origin "$INSTALL_BRANCH" &>/dev/null; then
    git -C "$dir" fetch origin "$INSTALL_BRANCH" >&2
  fi

  if git -C "$dir" show-ref --verify --quiet "refs/heads/$INSTALL_BRANCH"; then
    git -C "$dir" checkout "$INSTALL_BRANCH" >&2
    git -C "$dir" merge --ff-only "origin/$INSTALL_BRANCH" >&2
  else
    git -C "$dir" checkout -B "$INSTALL_BRANCH" "origin/$INSTALL_BRANCH" >&2
  fi
}

https_repo_url() {
  local url=""
  if [[ -n "${WORKFLOW_REPO_URL:-}" ]]; then
    url="$WORKFLOW_REPO_URL"
  elif [[ -n "${SCRIPT_DIR:-}" ]] && git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    url="$(git -C "$SCRIPT_DIR" config --get remote.origin.url || echo "$DEFAULT_REPO_HTTPS_URL")"
  else
    url="$DEFAULT_REPO_HTTPS_URL"
  fi

  case "$url" in
    git@github.com:*)
      echo "https://github.com/${url#git@github.com:}"
      ;;
    git@github.com:/*)
      echo "https://github.com/${url#git@github.com:/}"
      ;;
    *)
      echo "$url"
      ;;
  esac
}

# When run as `curl … | bash`, the script is not on disk next to skills/. Clone
# (or refresh) a shallow checkout so the rest of the installer can copy files.
ensure_script_dir() {
  local candidate=""
  local src="${_INSTALLER_SOURCE:-}"
  if [[ -n "$src" && "$src" != "-" && -f "$src" ]]; then
    candidate="$(cd "$(dirname "$src")" && pwd)"
    if [[ -d "$candidate/skills" ]]; then
      refresh_git_checkout "$candidate"
      echo "$candidate"
      return
    fi
  fi

  local url="$DEFAULT_REPO_HTTPS_URL"
  if [[ -n "${WORKFLOW_REPO_URL:-}" ]]; then
    url="$WORKFLOW_REPO_URL"
  fi
  case "$url" in
    git@github.com:*) url="https://github.com/${url#git@github.com:}" ;;
    git@github.com:/*) url="https://github.com/${url#git@github.com:/}" ;;
  esac

  mkdir -p "$(dirname "$INSTALL_SRC_CACHE")"
  if [[ -d "$INSTALL_SRC_CACHE/.git" ]]; then
    refresh_git_checkout "$INSTALL_SRC_CACHE"
  else
    if [[ -e "$INSTALL_SRC_CACHE" ]]; then
      rm -rf "$INSTALL_SRC_CACHE"
    fi
    echo "  Cloning installer checkout to $INSTALL_SRC_CACHE" >&2
    git clone --depth 1 --branch "$INSTALL_BRANCH" "$url" "$INSTALL_SRC_CACHE"
  fi
  echo "$INSTALL_SRC_CACHE"
}

# Route only — do not clone or copy. Used by tests and by the bot before install.
INSTALL_ARG="${1:-}"
if [[ "$INSTALL_ARG" == "--print-route" ]]; then
  print_install_route
  exit 0
fi
if [[ "$INSTALL_ARG" == "--opencode-skills" ]]; then
  WORKFLOW_INSTALL_MODE="${WORKFLOW_INSTALL_MODE:-opencode}"
  INSTALL_ARG=""
fi

SCRIPT_DIR="$(ensure_script_dir)"

is_valid_plugin_source() {
  local src="$1"
  [[ -d "$src/skills" && -f "$src/.cursor-plugin/plugin.json" ]]
}

# Cursor rejects symlinks that point outside ~/.cursor/plugins/local/. Always
# materialize a real directory tree under the local plugins folder.
copy_plugin_tree() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" ]]; then
    echo "  Replacing existing install at $dest"
    rm -rf "$dest"
  fi
  mkdir -p "$dest"
  echo "  Copying plugin files to $dest"
  cp -a "$src"/. "$dest"/
}

# Cursor does not follow symlinks — materialize a real checkout into
# ~/.cursor/plugins/local/. Prefer copying from an already-fetched source tree
# (SCRIPT_DIR or INSTALL_SRC_CACHE) so we never symlink out of the plugin folder.
ensure_cursor_core_plugin() {
  mkdir -p "$(dirname "$CURSOR_CORE_PLUGIN")"

  local src=""
  if is_valid_plugin_source "$SCRIPT_DIR"; then
    src="$SCRIPT_DIR"
  elif is_valid_plugin_source "$INSTALL_SRC_CACHE"; then
    src="$INSTALL_SRC_CACHE"
  fi

  if [[ -n "$src" ]]; then
    refresh_git_checkout "$src"
    local src_real dest_real
    src_real="$(readlink -f "$src")"
    dest_real="$(readlink -f "$CURSOR_CORE_PLUGIN" 2>/dev/null || echo "$CURSOR_CORE_PLUGIN")"
    if [[ "$src_real" != "$dest_real" ]]; then
      copy_plugin_tree "$src" "$CURSOR_CORE_PLUGIN"
      verify_cursor_core_plugin "$CURSOR_CORE_PLUGIN"
      return
    fi
  fi

  local url
  url="$(https_repo_url)"
  if [[ -d "$CURSOR_CORE_PLUGIN/.git" ]]; then
    refresh_git_checkout "$CURSOR_CORE_PLUGIN"
  else
    if [[ -e "$CURSOR_CORE_PLUGIN" ]]; then
      echo "  Replacing existing install at $CURSOR_CORE_PLUGIN"
      rm -rf "$CURSOR_CORE_PLUGIN"
    fi
    echo "  Cloning plugin to $CURSOR_CORE_PLUGIN"
    git clone --depth 1 --branch "$INSTALL_BRANCH" "$url" "$CURSOR_CORE_PLUGIN"
  fi
  verify_cursor_core_plugin "$CURSOR_CORE_PLUGIN"
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
  cp -a "$src"/. "$CURSOR_LAB_PLUGIN"/
}

verify_cursor_core_plugin() {
  local plugin="$1"
  local errors=0

  if [[ -L "$plugin" ]]; then
    echo "  ERROR: $plugin is a symlink; Cursor requires a real directory." >&2
    errors=$((errors + 1))
  fi
  if [[ ! -f "$plugin/.cursor-plugin/plugin.json" ]]; then
    echo "  ERROR: missing $plugin/.cursor-plugin/plugin.json" >&2
    errors=$((errors + 1))
  fi
  if [[ ! -d "$plugin/skills" ]]; then
    echo "  ERROR: missing $plugin/skills/" >&2
    errors=$((errors + 1))
  fi

  local skill_count=0
  local skill_dir
  for skill_dir in "$plugin"/skills/*/; do
    [[ -f "${skill_dir}SKILL.md" ]] && skill_count=$((skill_count + 1))
  done
  if [[ "$skill_count" -eq 0 ]]; then
    echo "  ERROR: no skills with SKILL.md found under $plugin/skills/" >&2
    errors=$((errors + 1))
  fi

  if [[ "$errors" -gt 0 ]]; then
    echo "  Plugin verification failed for $plugin" >&2
    return 1
  fi

  echo "  Verified plugin at $plugin ($skill_count skills)"
}

# Cloud agents discover project skills from .cursor/skills/, not plugins/local/.
ensure_cursor_workspace_skills() {
  local workspace=""
  local dest=""
  local src=""

  if ! workspace="$(find_workspace_root)"; then
    echo "  ERROR: cannot find workspace root for skill install." >&2
    echo "  Set WORKFLOW_WORKSPACE to your repository root and re-run." >&2
    return 1
  fi

  dest="$(workspace_skills_dest "$workspace")"
  if is_valid_plugin_source "$SCRIPT_DIR"; then
    src="$SCRIPT_DIR/skills"
  elif [[ -d "$INSTALL_SRC_CACHE/skills" ]]; then
    src="$INSTALL_SRC_CACHE/skills"
  else
    echo "  ERROR: no workflow skills source found." >&2
    return 1
  fi

  echo "  Workspace: $workspace"
  install_skills "$src" "$dest"
  verify_workspace_skills "$dest"
}

# Claude Code (local and web/remote) discovers personal skills from
# ~/.claude/skills/ in every project — no workspace files, no trust gate,
# no interactive /plugin install step required.
ensure_claude_user_skills() {
  local dest="$HOME/.claude/skills"
  local src=""

  if is_valid_plugin_source "$SCRIPT_DIR"; then
    src="$SCRIPT_DIR/skills"
  elif [[ -d "$INSTALL_SRC_CACHE/skills" ]]; then
    src="$INSTALL_SRC_CACHE/skills"
  else
    echo "  ERROR: no workflow skills source found." >&2
    return 1
  fi

  install_skills "$src" "$dest"
  verify_workspace_skills "$dest"
}

verify_workspace_skills() {
  local dest="$1"
  local errors=0
  local skill_count=0
  local skill_dir

  if [[ -L "$dest" ]]; then
    echo "  ERROR: $dest is a symlink; use a real directory." >&2
    errors=$((errors + 1))
  fi
  if [[ ! -d "$dest" ]]; then
    echo "  ERROR: missing $dest" >&2
    errors=$((errors + 1))
  fi

  for skill_dir in "$dest"/*/; do
    [[ -f "${skill_dir}SKILL.md" ]] && skill_count=$((skill_count + 1))
  done
  if [[ "$skill_count" -eq 0 ]]; then
    echo "  ERROR: no skills with SKILL.md found under $dest" >&2
    errors=$((errors + 1))
  fi

  if [[ "$errors" -gt 0 ]]; then
    echo "  Workspace skill verification failed for $dest" >&2
    return 1
  fi

  echo "  Verified workspace skills at $dest ($skill_count skills)"
}

install_skills() {
  local src="$1"
  local dest_root="$2"
  local skill_dir skill_name dest
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
    cp -a "$skill_dir" "$dest"
  done
}

# OpenCode: symlink each skill directory into ~/.config/opencode/skills/<name>
# so edits in the checkout are picked up without copying.
symlink_skills() {
  local src="$1"
  local dest_root="$2"
  local skill_dir skill_name dest src_abs target
  mkdir -p "$dest_root"
  for skill_dir in "$src"/*/; do
    skill_name="$(basename "$skill_dir")"
    dest="$dest_root/$skill_name"
    src_abs="$(readlink -f "$skill_dir")"
    if [[ -L "$dest" ]]; then
      target="$(readlink -f "$dest" 2>/dev/null || true)"
      if [[ "$target" == "$src_abs" ]]; then
        echo "  Symlink up to date: $skill_name"
        continue
      fi
      echo "  Replacing symlink: $skill_name"
      rm -f "$dest"
    elif [[ -e "$dest" ]]; then
      echo "  Replacing existing path (not a matching symlink): $skill_name"
      rm -rf "$dest"
    else
      echo "  Linking skill: $skill_name"
    fi
    ln -s "$src_abs" "$dest"
  done
}

verify_symlinked_skills() {
  local dest_root="$1"
  local label="${2:-OpenCode skills}"
  local errors=0
  local skill_count=0
  local skill_dir

  if [[ ! -d "$dest_root" ]]; then
    echo "  ERROR: missing $dest_root" >&2
    return 1
  fi

  for skill_dir in "$dest_root"/*; do
    [[ -d "$skill_dir" ]] || continue
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_count=$((skill_count + 1))
    # Do not use a trailing slash on skill_dir — bash follows symlinks and -L would fail.
    if [[ ! -L "$skill_dir" ]]; then
      echo "  ERROR: $skill_dir is not a symlink (OpenCode install expects symlinks only)." >&2
      errors=$((errors + 1))
    fi
  done
  if [[ "$skill_count" -eq 0 ]]; then
    echo "  ERROR: no skills with SKILL.md found under $dest_root" >&2
    errors=$((errors + 1))
  fi
  if [[ "$errors" -gt 0 ]]; then
    echo "  $label verification failed for $dest_root" >&2
    return 1
  fi
  echo "  Verified $label at $dest_root ($skill_count skills, symlinks)"
}

ensure_opencode_skills() {
  local include_lab="${WORKFLOW_OPENCODE_INCLUDE_LAB:-0}"
  local src=""

  if is_valid_plugin_source "$SCRIPT_DIR"; then
    src="$SCRIPT_DIR/skills"
  elif [[ -d "$INSTALL_SRC_CACHE/skills" ]]; then
    src="$INSTALL_SRC_CACHE/skills"
  else
    echo "  ERROR: no workflow skills source found." >&2
    return 1
  fi

  echo "  Checkout skills: $src"
  echo "  OpenCode skills dir: $OPENCODE_SKILLS_ROOT"
  symlink_skills "$src" "$OPENCODE_SKILLS_ROOT"
  verify_symlinked_skills "$OPENCODE_SKILLS_ROOT" "OpenCode core skills"

  if [[ "$include_lab" == "1" ]]; then
    local lab_src="$SCRIPT_DIR/plugins/workflow-lab/skills"
    if [[ ! -d "$lab_src" && -d "$INSTALL_SRC_CACHE/plugins/workflow-lab/skills" ]]; then
      lab_src="$INSTALL_SRC_CACHE/plugins/workflow-lab/skills"
    fi
    if [[ -d "$lab_src" ]]; then
      echo "  Including workflow-lab skills"
      symlink_skills "$lab_src" "$OPENCODE_SKILLS_ROOT"
      verify_symlinked_skills "$OPENCODE_SKILLS_ROOT" "OpenCode skills (core + lab)"
    else
      echo "  workflow-lab skills not found — skipping lab symlink pass."
    fi
  fi
}

echo "workflow-plugin installer"
echo "========================="

route="$(resolve_install_route)"
case "$route" in
  opencode)
    echo "OpenCode skills install ($(auto_install_reason)) — symlinking core workflow skills."
    echo "  Preferred layout: $OPENCODE_SKILLS_ROOT/<skill> → <checkout>/skills/<skill>"
    echo "  (Symlinks only — no copy into ~/.claude/skills.)"
    echo ""
    ensure_opencode_skills
    echo "  Done. Core skills linked under: $OPENCODE_SKILLS_ROOT"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build"
    if [[ "${WORKFLOW_OPENCODE_INCLUDE_LAB:-0}" == "1" ]]; then
      echo "  Lab skills were included (WORKFLOW_OPENCODE_INCLUDE_LAB=1)."
    else
      echo "  (workflow-lab not linked; set WORKFLOW_OPENCODE_INCLUDE_LAB=1 or re-run interactively.)"
    fi
    echo ""
    echo "Installation complete."
    exit 0
    ;;
  claude-code)
    echo "Claude Code detected ($(auto_install_reason)) — installing core workflow skills to ~/.claude/skills/."
    echo "  (Personal-scope skills — nothing written to the repo workspace.)"
    echo ""
    ensure_claude_user_skills
    echo "  Done. Core skills available at: $HOME/.claude/skills/"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build"
    echo "  (workflow-lab is not installed automatically; install it interactively if needed.)"
    echo ""
    echo "Installation complete."
    exit 0
    ;;
  cursor-cloud)
    echo "Non-interactive install ($(auto_install_reason)) — installing core workflow skills to workspace .cursor/skills/."
    echo "  (Cloud agents load project skills from .cursor/skills/, not plugins/local/.)"
    echo "  Cursor discovers those skills when the agent process starts. Bake this install"
    echo "  into the image; there is no session hook that reloads skills mid-turn."
    echo ""
    ensure_cursor_workspace_skills
    workspace="$(find_workspace_root)"
    dest="$(workspace_skills_dest "$workspace")"
    echo "  Done. Core skills available at: $dest"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build"
    echo "  Add .cursor/skills/$WORKFLOW_WORKSPACE_SKILLS_NAME/ to .gitignore in your repo."
    echo "  (workflow-lab is not installed in cloud agent environments.)"
    echo ""
    echo "Installation complete."
    exit 0
    ;;
esac

# Claude Code — copy skills to ~/.claude/skills/
if [[ -d "$HOME/.claude" ]]; then
  if ask "Install workflow core skills (design, refine, execute, comprehensive-review, close-out, post-build) into Claude Code (~/.claude/skills/)?"; then
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

# OpenCode — symlink skills into ~/.config/opencode/skills/ (preferred over ~/.claude/skills).
if [[ -d "$HOME/.config/opencode" || -d "$OPENCODE_SKILLS_ROOT" ]]; then
  if ask "Install workflow core skills into OpenCode ($OPENCODE_SKILLS_ROOT/) as symlinks to this checkout?"; then
    WORKFLOW_OPENCODE_INCLUDE_LAB=0
    ensure_opencode_skills
    echo "  Done. Core skills symlinked for OpenCode."
    echo ""
    if ask "Also symlink workflow-lab skills into OpenCode? Local/interactive only."; then
      WORKFLOW_OPENCODE_INCLUDE_LAB=1
      ensure_opencode_skills
      echo "  Done. Lab skills symlinked for OpenCode."
    fi
  fi
else
  echo "OpenCode (~/.config/opencode) not found — skipping."
  echo "  To install anyway: WORKFLOW_INSTALL_MODE=opencode ./install.sh"
  echo "  or: ./install.sh --opencode-skills"
fi

echo ""

# Cursor — materialize repo into ~/.cursor/plugins/local/workflow (core), then
# optionally copy the lab subtree into ~/.cursor/plugins/local/workflow-lab
if [[ -d "$HOME/.cursor" ]]; then
  if ask "Install workflow core plugin into Cursor (~/.cursor/plugins/local/)?"; then
    ensure_cursor_core_plugin
    echo "  Done. Restart Cursor to pick up the plugin."
    echo "  Plugin path: $CURSOR_CORE_PLUGIN (re-run install.sh to update)"
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
