# Execution report: 5-04 OpenCode plugin on the queue (brief 228, exec 29)

## Done
- `packages/opencode-workflow-hooks/src/index.ts`: `recordHooklog` writes `${WORKFLOW_QUEUE:-~/.local/share/workflow/queue}/<sanitised session>-<ts>-<pid>-<rand>.evt` (tmp/ then rename, 0700 dir) with envelope `{ts, harness:"opencode", event}` plus the payload snapshot; records with no `session_id` are dropped. Kick: `WORKFLOW_BIN drain`, else `bash <root>/bin/workflow drain`, detached, at most once per 10 s, `WORKFLOW_HOOKLOG_KICK=0` disables. Prefetch `--version` once at plugin load. `spoolDir`, `submitArtifact`, `runPythonHook` removed; soft-signal flush untouched.
- Tests rewritten (6 pass): queue name/envelope, spool.sh parity, no-session drop, kick throttle and prefetch, KICK=0, no submit helper.
- README: queue, kick, `WORKFLOW_QUEUE`/`WORKFLOW_BIN`/`WORKFLOW_HOOKLOG_KICK`; retired names and quality-service rows removed.
- Fail first: 4 of 6 failed before the code change; 6 of 6 pass after. Grep for retired names: no output.

## Departures
- The event name in the envelope is the payload's `hook_event_name` (the old plugin wrote `""`).
- Conversation id is the payload's `session_id`, which the plugin sets from the event's `sessionID`.
- Removed `WORKFLOW_QUALITY_*` README rows; only the retired submit path used them.
- `opencode.json.example` had no retired path; untouched.

## Known problems
- Kick when `WORKFLOW_BIN` is unset needs `bin/workflow` (5-02); tests stub it.
- Random suffix is `Math.random()*32768`, matching bash `$RANDOM` range; the pid/ts pair is the real uniqueness.
