#!/usr/bin/env bash
# Hook-side capture. Drops the raw hook payload into a spool file and returns: no parsing, no network,
# no Python. Never fails the agent (always exit 0). A drain normalises, scrubs, archives and posts later.
#   spool.sh --harness <auto|claude|cursor|opencode|codex> [--event NAME]
# Two paths:
#   legacy (default): spool dir $WORKFLOW_HOOKLOG_SPOOL, else <hooklog store>/spool (store = $WORKFLOW_HOOKLOG_DIR or
#     ~/.local/share/workflow-plugin/hooklog); kicks `drain.py --daemon`. A payload without a conversation ID is spooled as `unknown-...`.
#   Go (WORKFLOW_BIN set and non-empty): queue dir ${WORKFLOW_QUEUE:-~/.local/share/workflow/queue}; kicks `$WORKFLOW_BIN drain`
#     if executable. A payload without a conversation ID is not spooled and nothing is kicked.
# One file per event, written under tmp/ then renamed, so a reader never sees a partial file and concurrent hooks never interleave.
# Name = <conversation_id>-<ts>-<pid>-<rand>.evt; the ID is a bounded text match (first 64 KiB, bash builtins only) on
# "session_id", "conversation_id", "sessionID" in that order, with characters outside [A-Za-z0-9._-] turned into _.
# File = one JSON envelope line {"ts","harness","event"} followed by the raw payload.
# WORKFLOW_HOOKLOG=off disables capture. WORKFLOW_HOOKLOG_KICK=0 stops hooks starting a background drain.

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

go=
[ -n "${WORKFLOW_BIN:-}" ] && go=1
if [ -n "$go" ]; then
  dir=${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}
else
  dir=${WORKFLOW_HOOKLOG_SPOOL:-${WORKFLOW_HOOKLOG_DIR:-$HOME/.local/share/workflow-plugin/hooklog}/spool}
fi
spooled=

conv_id() {  # $1 = file; sets REPLY to the sanitised conversation ID, or empty
  local buf key
  REPLY=
  IFS= read -r -N 65536 buf <"$1" 2>/dev/null
  for key in session_id conversation_id sessionID; do
    if [[ $buf =~ \"$key\"[[:space:]]*:[[:space:]]*\"([^\"\\]{1,128})\" ]]; then
      REPLY=${BASH_REMATCH[1]//[^A-Za-z0-9._-]/_}
      return
    fi
  done
}

spool() {
  case "${WORKFLOW_HOOKLOG:-}" in 0 | off | OFF | false | FALSE) return ;; esac
  umask 077
  mkdir -p "$dir/tmp" 2>/dev/null || return
  local ts=${EPOCHREALTIME:-$(date +%s.%N)}
  ts=${ts/,/.}
  local name="$ts-$$-$RANDOM"
  { printf '{"ts":%s,"harness":"%s","event":"%s"}\n' "$ts" "$harness" "$event"; cat; } >"$dir/tmp/$name" 2>/dev/null || return
  conv_id "$dir/tmp/$name"
  local id=$REPLY
  if [ -z "$id" ]; then
    if [ -n "$go" ]; then rm -f "$dir/tmp/$name"; return; fi
    id=unknown
  fi
  mv "$dir/tmp/$name" "$dir/$id-$name.evt" 2>/dev/null && spooled=1
}

kick() {
  # Ensure one detached drain is running (stateless singleton: it holds a flock on .drain.lock, which dies with it).
  # Called after the event is spooled, so the drain either sees the file or the lock is free.
  [ "${WORKFLOW_HOOKLOG_KICK:-1}" = 0 ] && return
  if [ -n "$go" ]; then
    [ -n "$spooled" ] && [ -x "$WORKFLOW_BIN" ] || return
    if command -v flock >/dev/null 2>&1 && [ -e "$dir/.drain.lock" ]; then
      flock -n "$dir/.drain.lock" true 2>/dev/null || return  # held: a drain is running
    fi
    # No flock(1) (macOS): start unconditionally; the drain's own flock(2) is the singleton and extra starts exit.
    if command -v setsid >/dev/null 2>&1; then
      (WORKFLOW_QUEUE="$dir" setsid "$WORKFLOW_BIN" drain </dev/null >/dev/null 2>&1 &)
    else
      (WORKFLOW_QUEUE="$dir" nohup "$WORKFLOW_BIN" drain </dev/null >/dev/null 2>&1 &)
    fi
    return
  fi
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
