#!/usr/bin/env python3
"""Extract cost metrics from an opencode / Claude Code session transcript.

Reports: parent tool-turn counts by tool, per-subagent tool-turn counts and
model, wall time, and an approximate context estimate (first response only).

opencode and Claude Code share the same JSONL storage location and format;
opencode additionally sets OPENCODE_RUN_ID in the environment.

Usage:
    python3 parse_session.py [session-id]

If session-id is omitted, auto-detects: prefers OPENCODE_RUN_ID from the
environment, otherwise the most recently modified .jsonl for the current
project under ~/.claude/projects/{project-hash}/.
"""
import glob
import json
import os
import sys
from datetime import datetime


def project_dir():
    proj_hash = os.getcwd().replace('/', '-')
    return os.path.expanduser(f'~/.claude/projects/{proj_hash}')


def auto_detect_session_id():
    run_id = os.environ.get('OPENCODE_RUN_ID')
    if run_id:
        return run_id, 'opencode'
    proj_dir = project_dir()
    if not os.path.isdir(proj_dir):
        return None, None
    files = sorted(
        (f for f in os.listdir(proj_dir) if f.endswith('.jsonl')),
        key=lambda f: os.path.getmtime(os.path.join(proj_dir, f)),
        reverse=True,
    )
    if not files:
        return None, None
    with open(os.path.join(proj_dir, files[0])) as f:
        for line in f:
            obj = json.loads(line)
            if 'sessionId' in obj:
                return obj['sessionId'], 'claude-code'
    return None, None


def parse_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def count_tool_loops(messages, is_parent=True):
    """Count tool_use blocks in assistant messages."""
    counts = {}
    for msg in messages:
        if msg.get('type') != 'assistant':
            continue
        if is_parent and msg.get('isSidechain'):
            continue
        for item in msg.get('message', {}).get('content', []):
            if isinstance(item, dict) and item.get('type') == 'tool_use':
                name = item.get('name', 'unknown')
                counts[name] = counts.get(name, 0) + 1
    return counts


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    tool = None
    if not session_id:
        session_id, tool = auto_detect_session_id()
        if not session_id:
            print('No session found. Pass a session-id explicitly.', file=sys.stderr)
            sys.exit(1)
        print(f'Auto-detected session ({tool}): {session_id}')

    proj_dir = project_dir()
    session_file = os.path.join(proj_dir, f'{session_id}.jsonl')
    subagent_dir = os.path.join(proj_dir, session_id, 'subagents')

    if not os.path.exists(session_file):
        print(f'Session file not found: {session_file}', file=sys.stderr)
        sys.exit(1)

    parent_msgs = parse_jsonl(session_file)
    parent_tool_counts = count_tool_loops(parent_msgs)
    parent_total = sum(parent_tool_counts.values())

    timestamps = [
        msg['timestamp'] for msg in parent_msgs
        if 'timestamp' in msg and msg.get('type') in ('user', 'assistant')
    ]
    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None

    context_estimate = None
    for msg in parent_msgs:
        usage = msg.get('message', {}).get('usage')
        if usage:
            context_estimate = (
                usage.get('input_tokens', 0)
                + usage.get('cache_read_input_tokens', 0)
                + usage.get('cache_creation_input_tokens', 0)
            )
            break

    subagents = []
    if os.path.isdir(subagent_dir):
        for meta_file in sorted(glob.glob(os.path.join(subagent_dir, '*.meta.json'))):
            with open(meta_file) as f:
                meta = json.load(f)
            agent_id = os.path.basename(meta_file).replace('.meta.json', '')
            jsonl_path = os.path.join(subagent_dir, f'{agent_id}.jsonl')
            sub_msgs = parse_jsonl(jsonl_path) if os.path.exists(jsonl_path) else []

            sub_model = None
            for m in sub_msgs:
                sub_model = m.get('message', {}).get('model')
                if sub_model:
                    break

            sub_counts = count_tool_loops(sub_msgs, is_parent=False)
            subagents.append({
                'type': meta.get('agentType', 'unknown'),
                'description': meta.get('description', ''),
                'model': sub_model or 'unknown',
                'tool_counts': sub_counts,
                'total': sum(sub_counts.values()),
            })

    print(f'Parent tool turns: {parent_total} {parent_tool_counts}')
    print(f'Subagents: {len(subagents)}')
    for i, sa in enumerate(subagents):
        print(f'  [{i+1}] {sa["type"]} ({sa["model"]}): {sa["total"]} turns {sa["tool_counts"]}')
        print(f'       "{sa["description"]}"')
    if first_ts and last_ts:
        dt0 = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
        dt1 = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
        delta = dt1 - dt0
        mins, secs = divmod(int(delta.total_seconds()), 60)
        print(f'Wall time: {mins}:{secs:02d}')
    if context_estimate is not None:
        print(f'Context estimate (first response, approximate): {context_estimate:,} tokens')


if __name__ == '__main__':
    main()
