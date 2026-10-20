#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO_HTTPS_URL="https://github.com/codyhamilton/yakka"
INSTALL_BRANCH="${YAKKA_INSTALL_BRANCH:-master}"
CURSOR_CORE_PLUGIN="${CURSOR_CORE_PLUGIN:-$HOME/.cursor/plugins/local/yakka}"
INSTALL_SRC_CACHE="${YAKKA_INSTALL_SRC:-$HOME/.cache/yakka/src}"
YAKKA_WORKSPACE_SKILLS_NAME="${YAKKA_WORKSPACE_SKILLS_NAME:-yakka}"
OPENCODE_SKILLS_ROOT="${YAKKA_OPENCODE_SKILLS:-$HOME/.config/opencode/skills}"

# Capture before any function runs — inside functions BASH_SOURCE[0] is the
# function name (e.g. "main" for piped scripts), not the installer path.
_INSTALLER_SOURCE="${BASH_SOURCE[0]:-}"

is_cursor_cloud_agent() {
  [[ "${YAKKA_INSTALL_MODE:-}" == "cloud" ]] && return 0
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
  [[ "${YAKKA_INSTALL_MODE:-}" == "claude-code" ]] && return 0
  [[ "${CLAUDECODE:-}" == "1" ]] && return 0
  [[ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ]] && return 0
  [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] && return 0
  return 1
}

can_prompt_interactively() {
  [[ -t 0 ]] || ( exec 3</dev/tty ) 2>/dev/null
}

is_interactive_install() {
  [[ "${YAKKA_INSTALL_MODE:-}" == "interactive" ]] && can_prompt_interactively
}

# curl | bash delivers the script on stdin — BASH_SOURCE is "-" or unset, not a file path.
is_piped_installer() {
  local src="${_INSTALLER_SOURCE:-}"
  [[ -z "$src" || "$src" == "-" || ! -f "$src" ]]
}

should_auto_install_cursor_core() {
  is_interactive_install && return 1
  [[ "${YAKKA_INSTALL_MODE:-}" == "interactive" ]] && return 1

  # Runtime cloud agent signals (may be unset during environment setup).
  is_cursor_cloud_agent && return 0

  # curl | bash in environment setup: no TTY, no prompts possible — install core.
  if is_piped_installer || ! can_prompt_interactively; then
    return 0
  fi

  return 1
}

auto_install_reason() {
  if [[ "${YAKKA_INSTALL_MODE:-}" == "opencode" ]]; then
    echo "YAKKA_INSTALL_MODE=opencode"
  elif [[ "${YAKKA_INSTALL_MODE:-}" == "claude-code" ]]; then
    echo "YAKKA_INSTALL_MODE=claude-code"
  elif [[ "${CLAUDECODE:-}" == "1" ]]; then
    echo "CLAUDECODE=1"
  elif [[ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ]]; then
    echo "CLAUDE_CODE_ENTRYPOINT=${CLAUDE_CODE_ENTRYPOINT}"
  elif [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]; then
    echo "CLAUDE_CODE_REMOTE=true"
  elif [[ "${YAKKA_INSTALL_MODE:-}" == "cloud" ]]; then
    echo "YAKKA_INSTALL_MODE=cloud"
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
  if [[ -n "${YAKKA_WORKSPACE:-}" ]]; then
    echo "$(cd "$YAKKA_WORKSPACE" && pwd)"
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
  echo "$workspace/.cursor/skills/$YAKKA_WORKSPACE_SKILLS_NAME"
}

# Explicit YAKKA_INSTALL_MODE wins over ambient harness variables so an
# image bake (mode=cloud) is not captured by a stray CLAUDECODE, and a
# Claude hook (mode=claude-code) is not captured by HOSTNAME=cursor.
# Unset mode keeps the historical order: Claude signals, then Cursor cloud
# signals, then piped or non-interactive (workspace skills, core only).
resolve_install_route() {
  local mode="${YAKKA_INSTALL_MODE:-}"
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
  [[ "${YAKKA_INSTALL_SKIP_REFRESH:-}" == "1" ]] && return 0
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
  if [[ -n "${YAKKA_REPO_URL:-}" ]]; then
    url="$YAKKA_REPO_URL"
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

is_valid_plugin_source() {
  local src="$1"
  [[ -d "$src/skills" && -f "$src/.cursor-plugin/plugin.json" ]]
}

plugin_source_for_checkout() {
  local base="$1"
  local src="$base/plugins/yakka"
  if is_valid_plugin_source "$src"; then
    echo "$src"
    return 0
  fi
  return 1
}

resolve_plugin_source() {
  local src=""
  if src="$(plugin_source_for_checkout "$SCRIPT_DIR")"; then
    echo "$src"
    return 0
  fi
  if src="$(plugin_source_for_checkout "$INSTALL_SRC_CACHE")"; then
    echo "$src"
    return 0
  fi
  return 1
}

# When run as `curl … | bash`, the script is not on disk next to skills/. Clone
# (or refresh) a shallow checkout so the rest of the installer can copy files.
ensure_script_dir() {
  local candidate=""
  local src="${_INSTALLER_SOURCE:-}"
  if [[ -n "$src" && "$src" != "-" && -f "$src" ]]; then
    candidate="$(cd "$(dirname "$src")" && pwd)"
    if plugin_source_for_checkout "$candidate" >/dev/null; then
      refresh_git_checkout "$candidate"
      echo "$candidate"
      return
    fi
  fi

  local url="$DEFAULT_REPO_HTTPS_URL"
  if [[ -n "${YAKKA_REPO_URL:-}" ]]; then
    url="$YAKKA_REPO_URL"
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
  YAKKA_INSTALL_MODE="${YAKKA_INSTALL_MODE:-opencode}"
  INSTALL_ARG=""
fi

SCRIPT_DIR="$(ensure_script_dir)"

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
  if src="$(resolve_plugin_source)"; then
    local checkout src_real dest_real
    checkout="$(cd "$src/../.." && pwd -P)"
    refresh_git_checkout "$checkout"
    src_real="$(readlink -f "$src")"
    dest_real="$(readlink -f "$CURSOR_CORE_PLUGIN" 2>/dev/null || echo "$CURSOR_CORE_PLUGIN")"
    if [[ "$src_real" != "$dest_real" ]]; then
      copy_plugin_tree "$src" "$CURSOR_CORE_PLUGIN"
      verify_cursor_core_plugin "$CURSOR_CORE_PLUGIN"
      return
    fi
  fi

  local url checkout
  url="$(https_repo_url)"
  checkout="$INSTALL_SRC_CACHE"
  mkdir -p "$(dirname "$checkout")"
  if [[ -d "$checkout/.git" ]]; then
    refresh_git_checkout "$checkout"
  else
    if [[ -e "$checkout" ]]; then
      echo "  Replacing existing installer checkout at $checkout"
      rm -rf "$checkout"
    fi
    echo "  Cloning installer checkout to $checkout"
    git clone --depth 1 --branch "$INSTALL_BRANCH" "$url" "$checkout"
  fi
  if ! src="$(plugin_source_for_checkout "$checkout")"; then
    echo "  ERROR: checkout at $checkout is missing plugins/yakka" >&2
    return 1
  fi
  copy_plugin_tree "$src" "$CURSOR_CORE_PLUGIN"
  verify_cursor_core_plugin "$CURSOR_CORE_PLUGIN"
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
  if [[ ! -x "$plugin/script/spool.sh" ]]; then
    echo "  ERROR: missing or non-executable $plugin/script/spool.sh" >&2
    errors=$((errors + 1))
  fi
  local hooks_rel="hooks/cursor.json"
  if [[ -f "$plugin/.cursor-plugin/plugin.json" ]]; then
    hooks_rel=$(python3 -c "import json; print(json.load(open('$plugin/.cursor-plugin/plugin.json'))['hooks'].lstrip('./'))")
  fi
  if [[ ! -f "$plugin/$hooks_rel" ]]; then
    echo "  ERROR: missing hooks file $plugin/$hooks_rel" >&2
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
    echo "  Set YAKKA_WORKSPACE to your repository root and re-run." >&2
    return 1
  fi

  dest="$(workspace_skills_dest "$workspace")"
  if src="$(resolve_plugin_source)"; then
    src="$src/skills"
  else
    echo "  ERROR: no yakka skills source found." >&2
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

  if src="$(resolve_plugin_source)"; then
    src="$src/skills"
  else
    echo "  ERROR: no yakka skills source found." >&2
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
  local src=""

  if src="$(resolve_plugin_source)"; then
    src="$src/skills"
  else
    echo "  ERROR: no yakka skills source found." >&2
    return 1
  fi

  echo "  Checkout skills: $src"
  echo "  OpenCode skills dir: $OPENCODE_SKILLS_ROOT"
  symlink_skills "$src" "$OPENCODE_SKILLS_ROOT"
  verify_symlinked_skills "$OPENCODE_SKILLS_ROOT" "OpenCode core skills"
}

echo "yakka installer"
echo "========================="

route="$(resolve_install_route)"
case "$route" in
  opencode)
    echo "OpenCode skills install ($(auto_install_reason)) — symlinking core yakka skills."
    echo "  Preferred layout: $OPENCODE_SKILLS_ROOT/<skill> → <checkout>/skills/<skill>"
    echo "  (Symlinks only — no copy into ~/.claude/skills.)"
    echo ""
    ensure_opencode_skills
    echo "  Done. Core skills linked under: $OPENCODE_SKILLS_ROOT"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build, login"
    echo ""
    echo "Installation complete."
    exit 0
    ;;
  claude-code)
    echo "Claude Code detected ($(auto_install_reason)) — installing core yakka skills to ~/.claude/skills/."
    echo "  (Personal-scope skills — nothing written to the repo workspace.)"
    echo ""
    ensure_claude_user_skills
    echo "  Done. Core skills available at: $HOME/.claude/skills/"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build, login"
    echo ""
    echo "Installation complete."
    exit 0
    ;;
  cursor-cloud)
    echo "Non-interactive install ($(auto_install_reason)) — installing core yakka skills to workspace .cursor/skills/."
    echo "  (Cloud agents load project skills from .cursor/skills/, not plugins/local/.)"
    echo "  Cursor discovers those skills when the agent process starts. Bake this install"
    echo "  into the image; there is no session hook that reloads skills mid-turn."
    echo ""
    ensure_cursor_workspace_skills
    workspace="$(find_workspace_root)"
    dest="$(workspace_skills_dest "$workspace")"
    echo "  Done. Core skills available at: $dest"
    echo "  Skills: design, refine, execute, comprehensive-review, close-out, post-build, login"
    echo "  Add .cursor/skills/$YAKKA_WORKSPACE_SKILLS_NAME/ to .gitignore in your repo."
    echo ""
    echo "Installation complete."
    exit 0
    ;;
esac

# Claude Code — copy skills to ~/.claude/skills/
if [[ -d "$HOME/.claude" ]]; then
  if ask "Install yakka core skills (design, refine, execute, comprehensive-review, close-out, post-build, login) into Claude Code (~/.claude/skills/)?"; then
    if src="$(resolve_plugin_source)"; then
      install_skills "$src/skills" "$HOME/.claude/skills"
    else
      echo "  ERROR: no yakka skills source found." >&2
      exit 1
    fi
    echo "  Done. Core skills available immediately in Claude Code."
  fi
else
  echo "Claude Code (~/.claude) not found — skipping."
fi

echo ""

# OpenCode — symlink skills into ~/.config/opencode/skills/ (preferred over ~/.claude/skills).
if [[ -d "$HOME/.config/opencode" || -d "$OPENCODE_SKILLS_ROOT" ]]; then
  if ask "Install yakka core skills into OpenCode ($OPENCODE_SKILLS_ROOT/) as symlinks to this checkout?"; then
    ensure_opencode_skills
    echo "  Done. Core skills symlinked for OpenCode."
  fi
else
  echo "OpenCode (~/.config/opencode) not found — skipping."
  echo "  To install anyway: YAKKA_INSTALL_MODE=opencode ./install.sh"
  echo "  or: ./install.sh --opencode-skills"
fi

echo ""

# Cursor — materialize repo into ~/.cursor/plugins/local/yakka (core).
if [[ -d "$HOME/.cursor" ]]; then
  if ask "Install yakka core plugin into Cursor (~/.cursor/plugins/local/)?"; then
    ensure_cursor_core_plugin
    echo "  Done. Restart Cursor to pick up the plugin."
    echo "  Plugin path: $CURSOR_CORE_PLUGIN (re-run install.sh to update)"
  fi
else
  echo "Cursor (~/.cursor) not found — skipping."
fi

echo ""
echo "Installation complete."
