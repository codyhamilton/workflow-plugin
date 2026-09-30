#!/bin/bash
set -euo pipefail
[[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] || exit 0
# Redirect the installer's own progress output to stderr — stdout is
# reserved for the control JSON below, which Claude Code parses.
curl -fsSL https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/install.sh | bash >&2
# Skill discovery runs before SessionStart hooks finish by default, so
# skills installed above wouldn't be visible until the *next* session —
# which never comes in a one-shot cloud container. reloadSkills forces a
# rescan after this (synchronous, non-async) hook completes.
echo '{"hookSpecificOutput": {"hookEventName": "SessionStart", "reloadSkills": true}}'
