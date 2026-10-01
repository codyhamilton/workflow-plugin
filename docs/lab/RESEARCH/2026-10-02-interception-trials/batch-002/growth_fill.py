#!/usr/bin/env python3
"""GROWTH pack field fill — Soft HOLD.

Snapshot builders for batch-002 never emitted `markers`, `phase_hints` or
`recent`, so the GROWTH state-selections (markers_focus, phase_hints_focus,
recent_delta_brief) sent empty fields to the judge. This module derives them
deterministically from fields every claude-code snapshot already carries
(`tail`, `cumulative`, `delta_since_prior`) and gates sessions that cannot
supply them (lite-prefix packs have no `tail`).

Pure stdlib, no network. Uses only prefix-observable data: no schedule, no
session-length or progress fields (see LEAK in the sweep runner).

CLI:  python3 growth_fill.py            # writes GROWTH-FILL-COVERAGE.json
"""
from __future__ import annotations
import json, re, sys
from collections import Counter
from pathlib import Path

FILL_VERSION = 'growth-fill-v1'
GROWTH_FIELD = {
    'markers_focus': 'markers',
    'phase_hints_focus': 'phase_hints',
    'recent_delta_brief': 'recent',
}
RECENT_N = 4
RECENT_TEXT_CHARS = 160

TOOL_CLASS = {
    'explore': {'Read', 'Grep', 'Glob', 'ListAgents', 'ToolSearch', 'WebSearch', 'WebFetch'},
    'edit': {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'},
    'exec': {'Bash'},
    'orchestrate': {'Agent', 'SendMessage', 'Monitor', 'TaskStop', 'Skill',
                    'ScheduleWakeup', 'EnterWorktree'},
    'user': {'AskUserQuestion'},
}
CLASSES = tuple(TOOL_CLASS) + ('other',)

_TERMS = {
    'error_terms': r'\b(error|errors|fail|failed|failing|failure|exception|traceback|timeout|timed out)\b',
    'verify_terms': r'\b(test|tests|pytest|passed|verify|verified|lint|build)\b',
    'delivery_terms': r'\b(commit|committed|push|pushed|merged|merge|pr|done|complete|completed)\b',
    'wait_terms': r'\b(wait|waiting|poll|monitor|blocked|background)\b',
}
_TERM_RE = {k: re.compile(v, re.I) for k, v in _TERMS.items()}


def tool_class(name: str) -> str:
    for cls, names in TOOL_CLASS.items():
        if name in names:
            return cls
    return 'other'


def _class_counts(tool_names) -> dict:
    c = Counter(tool_class(n) for n in tool_names)
    return {k: c.get(k, 0) for k in CLASSES}


def _dominant(counts: dict):
    total = sum(counts.values())
    if not total:
        return None
    best = max(CLASSES, key=lambda k: (counts[k], -CLASSES.index(k)))
    return best


def _max_same_tool_run(tail) -> int:
    best = run = 0
    prev = None
    for e in tail:
        sig = tuple(sorted(e.get('tool_names') or ()))
        if sig and sig == prev:
            run += 1
        elif sig:
            run = 1
        else:
            run = 0
        prev = sig if sig else None
        best = max(best, run)
    return best


def _tail_entries(full: dict):
    tail = full.get('tail')
    if not isinstance(tail, list):
        return None
    out = [e for e in tail if isinstance(e, dict)]
    return out or None


def derive_growth_fields(full: dict):
    """Return {'markers', 'phase_hints', 'recent'} or None when ineligible.

    Ineligible = no usable `tail` (lite-prefix packs). Callers must gate on
    None rather than send an empty field to the judge.
    """
    tail = _tail_entries(full)
    if not tail:
        return None
    cum = full.get('cumulative') or {}
    delta = full.get('delta_since_prior') or {}
    texts = [e.get('excerpt') or '' for e in tail]
    blob = '\n'.join(texts)

    tool_turns = [e for e in tail if e.get('tool_names')]
    markers = {
        'tail_turns': len(tail),
        'tool_turns': len(tool_turns),
        'silent_tool_turns': sum(1 for e in tool_turns if not (e.get('excerpt') or '').strip()),
        'text_only_turns': sum(1 for e in tail if not e.get('tool_names') and (e.get('excerpt') or '').strip()),
        'max_same_tool_run': _max_same_tool_run(tail),
        **{k: len(rx.findall(blob)) for k, rx in _TERM_RE.items()},
        'compaction_event_count': cum.get('compaction_event_count'),
        'reread_path_count': len(cum.get('reread_paths') or []),
        'delta_new_read_paths': len(delta.get('new_read_paths') or []),
    }

    tail_tools = [n for e in tail for n in (e.get('tool_names') or ())]
    tail_counts = _class_counts(tail_tools)
    cum_counts = _class_counts(
        n for n, k in (cum.get('tool_histogram') or {}).items() for _ in range(int(k or 0)))
    cum_total = sum(cum_counts.values())
    phase_hints = {
        'tail_class_counts': tail_counts,
        'tail_dominant_class': _dominant(tail_counts),
        'cumulative_class_share': (
            {k: round(v / cum_total, 2) for k, v in cum_counts.items()} if cum_total else {}),
        'cumulative_dominant_class': _dominant(cum_counts),
        'tail_has_edit': tail_counts['edit'] > 0,
        'closing_language': markers['delivery_terms'] > 0 or markers['verify_terms'] > 0,
        'basis': 'lexical+tool-class over tail[-8:]; heuristic, not a label',
    }

    recent = [{
        'turn': e.get('turn'),
        'tools': list(e.get('tool_names') or ()),
        'text': (e.get('excerpt') or '')[:RECENT_TEXT_CHARS],
    } for e in tail[-RECENT_N:]]

    return {'markers': markers, 'phase_hints': phase_hints, 'recent': recent}


def fill_growth_fields(full: dict, mode: str):
    """Return `full` with the growth field for `mode` populated, or None if gated.

    Fields already present and non-empty on the snapshot (a future builder
    that emits them natively) win over derived values.
    """
    field = GROWTH_FIELD[mode]
    if full.get(field):
        return full
    derived = derive_growth_fields(full)
    if derived is None:
        return None
    return {**full, field: derived[field]}


def _rep_snap(pack: dict):
    cps = sorted(pack.get('checkpoints') or [], key=lambda s: int(s['checkpoint']))
    return cps[len(cps) // 2] if cps else None


def coverage_report(batch: Path) -> dict:
    """Per-pack eligibility at the sweep's representative (mid) checkpoint."""
    seen, rows = set(), []
    for d in ('snapshots-mid', 'snapshots-dense', 'snapshots'):
        for sp in sorted((batch / d).glob('*.json')):
            try:
                pack = json.loads(sp.read_text())
            except Exception:
                continue
            if not pack.get('checkpoints'):
                continue
            wid = pack.get('worker_id') or sp.stem
            if wid in seen:
                continue
            seen.add(wid)
            snap = _rep_snap(pack)
            full = (snap or {}).get('full_state') or {}
            rows.append((pack.get('harness'), full, derive_growth_fields(full)))
    by_harness = {}
    for h, _full, d in rows:
        b = by_harness.setdefault(h, {'sessions': 0, 'eligible': 0})
        b['sessions'] += 1
        b['eligible'] += d is not None
    elig = [d for _, _, d in rows if d]
    return {
        'fill_version': FILL_VERSION,
        'checkpoint_policy': 'one_representative_mid_per_session',
        'n_sessions': len(rows),
        'n_eligible': len(elig),
        'n_gated_no_tail': len(rows) - len(elig),
        'by_harness': by_harness,
        'nonempty_after_fill': {
            f: sum(1 for d in elig if d[f]) for f in ('markers', 'phase_hints', 'recent')},
        'soft_standard_hold': True,
        'product_wiring': False,
    }


def main() -> int:
    batch = Path(__file__).resolve().parent
    rep = coverage_report(batch)
    (batch / 'GROWTH-FILL-COVERAGE.json').write_text(json.dumps(rep, indent=2) + '\n')
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
