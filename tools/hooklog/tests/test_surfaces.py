"""Registration smoke: run every shipped command against an isolated spool, drain it, check the archive."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
CLAUDE = set('SessionStart Setup InstructionsLoaded UserPromptSubmit UserPromptExpansion MessageDisplay PreToolUse PermissionRequest PermissionDenied PostToolUse PostToolUseFailure PostToolBatch Notification SubagentStart SubagentStop TaskCreated TaskCompleted Stop StopFailure TeammateIdle ConfigChange CwdChanged DirectoryAdded FileChanged WorktreeCreate WorktreeRemove PreCompact PostCompact PreModelSwitch PostModelSwitch Elicitation ElicitationResult SessionEnd'.split())
# The supplied catalog's 22 subtotal enumerates only these 21 names; see README caveat.
CURSOR = set('sessionStart sessionEnd preToolUse postToolUse postToolUseFailure subagentStart subagentStop beforeShellExecution afterShellExecution beforeMCPExecution afterMCPExecution beforeReadFile afterFileEdit beforeSubmitPrompt preCompact stop afterAgentResponse afterAgentThought beforeTabFileRead afterTabFileEdit workspaceOpen'.split())
CODEX = set('SessionStart SessionEnd SubagentStart SubagentStop PreToolUse PermissionRequest PostToolUse PreCompact PostCompact UserPromptSubmit Stop Interrupt'.split())

class SurfaceTests(unittest.TestCase):
    def test_shipped_registrations_capture_all_events(self):
        registrations = [('claude', 'hooks/hooks.json', CLAUDE), ('cursor', 'hooks/cursor.json', CURSOR),
                         ('cursor', 'tools/hooklog/cursor-hooks.example.json', CURSOR),
                         ('codex', 'tools/hooklog/codex-hooks.example.json', CODEX)]
        for harness, file, expected in registrations:
            with self.subTest(file=file), tempfile.TemporaryDirectory() as tmp:
                config = json.loads((ROOT / file).read_text())
                self.assertEqual(set(config['hooks']), expected)
                env = dict(os.environ, WORKFLOW_HOOKLOG_DIR=tmp, WORKFLOW_HOOKLOG='on', WORKFLOW_HOOKLOG_KICK='0', WORKFLOW_QUALITY_URL='',
                           CLAUDE_PLUGIN_ROOT=str(ROOT), CURSOR_PLUGIN_ROOT=str(ROOT))
                for event, groups in config['hooks'].items():
                    if harness == 'claude' and event in ('WorktreeCreate', 'WorktreeRemove'):
                        self.assertEqual(groups, [])  # logger must not replace host operations
                        command = f'bash "{ROOT}/tools/hooklog/spool.sh" --harness claude --event {event}'
                        # Existing worktree handlers can call this command with their payload.
                    else:
                        hook = groups[0] if harness == 'cursor' else groups[0]['hooks'][0]
                        command = hook['command'].replace('/ABS/PATH/workflow-plugin', str(ROOT))
                    payload = {'hook_event_name': event, 'session_id': 'surface-test', 'prompt': 'smoke'}
                    if harness == 'claude':
                        payload['transcript_path'] = '/tmp/transcript.jsonl'
                    result = subprocess.run(command, shell=True, input=json.dumps(payload), text=True,
                                            capture_output=True, env=env, cwd='/tmp')
                    self.assertEqual(result.returncode, 0, (event, result.stderr))
                    if harness != 'cursor':
                        self.assertEqual(result.stdout, '')
                subprocess.run(['python3', str(ROOT / 'tools/hooklog/drain.py'), '--once'], env=env, check=True, capture_output=True)
                rows = [json.loads(line) for line in (Path(tmp) / harness / 'surface-test.jsonl').read_text().splitlines()]
                self.assertEqual({row['hook_event'] for row in rows}, expected)
                self.assertEqual(len(rows), len(expected))

    def test_cursor_manifest_selects_native_registration(self):
        manifest = json.loads((ROOT / '.cursor-plugin/plugin.json').read_text())
        self.assertEqual(manifest['hooks'], './hooks/cursor.json')
        self.assertTrue((ROOT / manifest['hooks']).is_file())

if __name__ == '__main__':
    unittest.main()
