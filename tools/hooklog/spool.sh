#!/usr/bin/env bash
# Hook-side capture. Drops the raw hook payload into a spool file and returns: no parsing, no network,
# no Python. Never fails the agent (always exit 0). drain.py normalises, scrubs, archives and posts later.
#   spool.sh --harness <auto|claude|cursor|opencode|codex> [--event NAME]
# Spool: $WORKFLOW_HOOKLOG_SPOOL, else <hooklog store>/spool (store = $WORKFLOW_HOOKLOG_DIR or ~/.local/share/workflow-plugin/hooklog).
# One file per event, written under tmp/ then renamed, so a reader never sees a partial file and concurrent hooks never interleave.
# File = one JSON envelope line {"ts","harness","event"} followed by the raw payload.
# WORKFLOW_HOOKLOG=off disables capture. WORKFLOW_HOOKLOG_KICK=0 stops hooks starting the background drain daemon (--daemon: drains, exits after idle).

harness=auto event=
while [ $# -gt 0 ]; do
  case $1 in
    --harness) harness=${2:-auto}; shift 2 ;;
    --event) event=${2:-}; shift 2 ;;
    *) shift ;;
  esac
done
harness=${harness//[^A-Za-z0-9._-]/}
event=${event//[^A-Za-z0-9._-]/}

spool() {
  case "${WORKFLOW_HOOKLOG:-}" in 0 | off | OFF | false | FALSE) return ;; esac
  local dir=${WORKFLOW_HOOKLOG_SPOOL:-${WORKFLOW_HOOKLOG_DIR:-$HOME/.local/share/workflow-plugin/hooklog}/spool}
  umask 077
  mkdir -p "$dir/tmp" 2>/dev/null || return
  local ts=${EPOCHREALTIME:-$(date +%s.%N)}
  ts=${ts/,/.}
  local name="$ts-$$-$RANDOM"
  { printf '{"ts":%s,"harness":"%s","event":"%s"}\n' "$ts" "$harness" "$event"; cat; } >"$dir/tmp/$name" 2>/dev/null &&
    mv "$dir/tmp/$name" "$dir/$name.evt" 2>/dev/null
}

kick() {
  # Ensure one detached drain daemon is running (stateless singleton: it holds a flock on .drain.lock, which dies with it, and
  # exits itself after an idle period). Called after the event is spooled, so the daemon either sees the file or the lock is free.
  [ "${WORKFLOW_HOOKLOG_KICK:-1}" = 0 ] && return
  local dir=${WORKFLOW_HOOKLOG_SPOOL:-${WORKFLOW_HOOKLOG_DIR:-$HOME/.local/share/workflow-plugin/hooklog}/spool}
  local drain
  drain=$(dirname "${BASH_SOURCE[0]}")/drain.py
  [ -f "$drain" ] && command -v python3 >/dev/null 2>&1 || return
  if command -v flock >/dev/null 2>&1 && [ -e "$dir/.drain.lock" ]; then
    flock -n "$dir/.drain.lock" true 2>/dev/null || return  # held: a daemon is running
  fi
  (setsid python3 "$drain" --daemon </dev/null >/dev/null 2>&1 &)
}

spool
case "${WORKFLOW_HOOKLOG:-}" in 0 | off | OFF | false | FALSE) ;; *) kick ;; esac

if [ "$harness" = cursor ]; then
  case $event in
    preToolUse | subagentStart | beforeShellExecution | beforeMCPExecution | beforeReadFile | beforeTabFileRead) echo '{"permission": "allow"}' ;;
    beforeSubmitPrompt) echo '{"continue": true}' ;;
    *) echo '{}' ;;
  esac
fi
exit 0
