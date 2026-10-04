#!/usr/bin/env bash
# Hook-side capture. Drops the raw hook payload into the queue and returns: no parsing, no network,
# no Python. Never fails the agent (always exit 0). `workflow drain` normalises, scrubs, archives and posts later.
#   spool.sh --harness <claude|cursor|opencode|codex> [--event NAME]
# Queue dir ${WORKFLOW_QUEUE:-~/.local/share/workflow/queue}. A missing or `auto` harness, or a payload without a
# conversation ID, is not spooled (and nothing is kicked).
# One file per event, written under tmp/ then renamed, so a reader never sees a partial file and concurrent hooks never interleave.
# Name = <conversation_id>-<ts>-<pid>-<rand>.evt; the ID is a bounded text match (first 64 KiB, bash builtins only) on
# "session_id", "conversation_id", "sessionID" in that order, with characters outside [A-Za-z0-9._-] turned into _.
# File = one JSON envelope line {"ts","harness","event"} followed by the raw payload.
# Kick: `$WORKFLOW_BIN drain` when WORKFLOW_BIN is set, else `bash <repo>/bin/workflow drain`, detached, one at a time
# (flock probe, or a mkdir+pid lock under <queue>/.kick.d without flock(1); WORKFLOW_SPOOL_NOFLOCK=1 forces that).
# WORKFLOW_HOOKLOG=off disables capture. WORKFLOW_HOOKLOG_KICK=0 stops hooks starting a background drain.
# Runs under bash 3.2 (macOS): bash builtins plus head, date, find; no flock(1) needed.

harness= event=
while [ $# -gt 0 ]; do
  case $1 in
    --harness) harness=${2:-}; shift 2 ;;
    --event) event=${2:-}; shift 2 ;;
    *) shift ;;
  esac
done
harness=${harness//[^A-Za-z0-9._-]/}
event=${event//[^A-Za-z0-9._-]/}

dir=${WORKFLOW_QUEUE:-$HOME/.local/share/workflow/queue}
spooled=

conv_id() {  # $1 = file; sets REPLY to the sanitised conversation ID, or empty
  local buf key
  REPLY=
  buf=$(head -c 65536 "$1" 2>/dev/null)
  for key in session_id conversation_id sessionID; do
    if [[ $buf =~ \"$key\"[[:space:]]*:[[:space:]]*\"([^\"\\]{1,128})\" ]]; then
      REPLY=${BASH_REMATCH[1]//[^A-Za-z0-9._-]/_}
      return
    fi
  done
}

spool() {
  case "${WORKFLOW_HOOKLOG:-}" in 0 | off | OFF | false | FALSE) return ;; esac
  case $harness in '' | auto) return ;; esac
  umask 077
  mkdir -p "$dir/tmp" 2>/dev/null || return
  local ts
  ts=$(date +%s.%N 2>/dev/null)
  case $ts in '' | *[!0-9.]*) ts=$(date +%s) ;; esac
  local name="$ts-$$-$RANDOM"
  { printf '{"ts":%s,"harness":"%s","event":"%s"}\n' "$ts" "$harness" "$event"; cat; } >"$dir/tmp/$name" 2>/dev/null || return
  conv_id "$dir/tmp/$name"
  local id=$REPLY
  if [ -z "$id" ]; then rm -f "$dir/tmp/$name"; return; fi
  mv "$dir/tmp/$name" "$dir/$id-$name.evt" 2>/dev/null && spooled=1
}

start_drain() {  # $1 = optional prefix (setsid); detached, so $! is the drain's pid
  local root
  if [ -n "${WORKFLOW_BIN:-}" ]; then
    WORKFLOW_QUEUE="$dir" ${1:+"$1"} nohup "$WORKFLOW_BIN" drain </dev/null >/dev/null 2>&1 &
  else
    root=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd -P) || return 1
    WORKFLOW_QUEUE="$dir" ${1:+"$1"} nohup bash "$root/bin/workflow" drain </dev/null >/dev/null 2>&1 &
  fi
}

kick() {
  # Ensure one detached drain is running. Called after the event is spooled, so the drain either sees the file or the lock is free.
  [ "${WORKFLOW_HOOKLOG_KICK:-1}" = 0 ] && return
  [ -n "$spooled" ] || return
  if [ -n "${WORKFLOW_BIN:-}" ] && [ ! -x "$WORKFLOW_BIN" ]; then return; fi
  if [ -z "${WORKFLOW_SPOOL_NOFLOCK:-}" ] && command -v flock >/dev/null 2>&1; then
    if [ -e "$dir/.drain.lock" ]; then
      flock -n "$dir/.drain.lock" true 2>/dev/null || return  # held: a drain is running
    fi
    if command -v setsid >/dev/null 2>&1; then (start_drain setsid); else (start_drain); fi
    return
  fi
  # No flock(1): mkdir lock with a PID check. The drain's own flock(2) stays the real singleton.
  local lock="$dir/.kick.d" attempt=0 pid
  while [ $attempt -lt 2 ]; do
    attempt=$((attempt + 1))
    if mkdir "$lock" 2>/dev/null; then
      start_drain || { rmdir "$lock" 2>/dev/null; return; }
      echo $! >"$lock/pid" 2>/dev/null
      return
    fi
    if [ -f "$lock/pid" ]; then
      pid=$(cat "$lock/pid" 2>/dev/null)
      case $pid in '' | *[!0-9]*) ;; *) kill -0 "$pid" 2>/dev/null && return ;; esac
    else
      [ -n "$(find "$lock" -maxdepth 0 -mmin +1 2>/dev/null)" ] || return
    fi
    rm -rf "$lock" 2>/dev/null
  done
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
