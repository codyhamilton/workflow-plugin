#!/usr/bin/env python3
"""TypeSafe SCENARIO corpus sweep — Soft HOLD.

Progress metric: n_distinct_scenarios × n_sessions_swept (outcomes compared).
Scenario = (state_selection × question_format). ONE representative checkpoint
per session — does NOT deepen same-shape × window cartesian.

Outputs: batch-002/typesafe-scenario-sweep/
"""
from __future__ import annotations
import hashlib, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo
import importlib.util

REPO = Path(os.environ.get('WORKFLOW_PLUGIN_REPO', Path(__file__).resolve().parents[5]))
BATCH = REPO / 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002'
SNAP_DIRS = [BATCH/'snapshots-mid', BATCH/'snapshots-dense', BATCH/'snapshots']
OUT = BATCH / 'typesafe-scenario-sweep'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'raw').mkdir(exist_ok=True)
AEST = ZoneInfo('Australia/Brisbane')
URL = 'https://api.typesafe.ai/v1/systemone'
# Cap cells ≈ scenarios × sessions (not windows)
MAX_SCENARIOS = int(os.environ.get('TS_MAX_SCENARIOS', '200'))
WORKERS = int(os.environ.get('TS_SCENARIO_WORKERS', '14'))
FRAMING = 'H1'  # thin single probe — not a scenario multiplier
JEV = 'jev-1.13.0'

_spec = importlib.util.spec_from_file_location('fl_scale', BATCH/'run_batch002_flash_luna_scale.py')
_fl = importlib.util.module_from_spec(_spec)
sys.modules['fl_scale_batch002'] = _fl
_spec.loader.exec_module(_fl)
project_state_fl = _fl.project_state

# Priority NEW states (§D)
STATES_NEW = (
    'delta_only', 'tail_focus', 'tool_hist_focus',
    'brief_cum_no_tail', 'chars_budget_1200', 'window_delta_tools',
)
# Canonical F/L states not yet TypeSafe-swept as scenarios
STATES_FL = (
    'state_length_short', 'state_length_mid',
    'deterministic_trim_v1', 'deterministic_trim_v2',
)
# Thin base for contrast
STATES_BASE = ('stats_only', 'compact_focus')

Q_NEW = {
    'compaction_storm': 'Are compaction events clustering without forward file or output progress? Snapshot only.',
    'reread_loop': 'Are the same paths re-read with little new synthesis (stuck reread loop)? Snapshot only.',
    'silent_stall': 'Are turns elapsing with near-zero tangible output (silent stall)? Snapshot only.',
    'tool_error_cascade': 'Are tool failures/retries cascading enough to warrant steering toward stop? Snapshot only.',
    'context_pressure': 'Do peak-context / pressure signals argue for stop or compress-and-stop? Snapshot only.',
    'validation_loop': 'Is work stuck re-validating/re-testing without new scope completion? Snapshot only.',
    'plan_execute_drift': 'Has execution drifted from brief/plan intent enough to intervene? Snapshot only.',
    'handoff_ready': 'Would handoff or split beat continued solo run from this prefix? Snapshot only.',
    'abort_cheaper': 'Does expected remaining burn exceed recoverable value of continuing? Snapshot only.',
    'duplicate_work': 'Is there evidence of repeating already-completed work? Snapshot only.',
    'over_polish': 'Is this post-success polish / cosmetic churn past good-enough? Snapshot only.',
    'under_verified': 'Are there done-claims without verification evidence in the prefix? Snapshot only.',
    'mid_arc_healthy': 'Is the mid-arc still healthy such that DEFER (not fire) is correct? Snapshot only.',
    'early_false_alarm': 'Would firing NOW likely be an early false alarm? Snapshot only.',
    'late_miss_risk': 'Does waiting further risk a late miss on runaway? Snapshot only.',
    'recovery_possible': 'Is recovery still plausible without external steer? Snapshot only.',
    'stop_preserves_value': 'Would stopping now preserve more value than another ~15 turns? Snapshot only.',
    'continue_learns': 'Would another ~15 turns likely yield learning/progress rather than noise? Snapshot only.',
    'thrash_vs_explore': 'Is activity exploratory learning or unproductive thrash? Snapshot only.',
    'user_wait_signal': 'Does the prefix show blocked-on-user / limit / wait making steer irrelevant? Snapshot only.',
    'resource_asymmetry': 'Does cost/context growth dwarf output growth enough to intervene? Snapshot only.',
    'output_starvation': 'Are tools firing while assistant text/output chars stall? Snapshot only.',
}
Q_FL = {
    'recheck_interval': 'If deferring, is a ~10–15 turn re-check interval still justified, or should fire happen sooner?',
    'closing_protect': 'Would firing now risk interrupting closing-stage validation or delivery value?',
    'scope_drift': 'Do recent turns drift from the brief into unrelated scope expansion?',
    'activity_without_value': 'Is there frequent tool activity without checkable progress (activity ≠ value)?',
    'tail_risk': "Is the trajectory's continuation tail risk high enough to warrant steering toward stop?",
    'recoverable_stall': 'Does a stall look recoverable/valuable, such that deferral is better than fire?',
}
Q_BASE = {
    'steer_now': 'Is NOW a useful time to steer toward stopping, without truncating productive or near-done work? Judge only the snapshot.',
    'thrash_bundle': 'Do compaction, rereads, and weak new output form a thrash bundle? Judge only the snapshot.',
}
QUESTIONS = {**Q_NEW, **Q_FL, **Q_BASE}
LEAK = {'t','T','session_length','norm_length','progress_frac','full_length','T_eligibility_only','length_metric'}

def strip_leaks(obj):
    if isinstance(obj, dict):
        return {k: strip_leaks(v) for k,v in obj.items() if k not in LEAK and not str(k).lower().startswith('progress_')}
    if isinstance(obj, list):
        return [strip_leaks(x) for x in obj]
    return obj

def project(full, mode):
    full = strip_leaks(json.loads(json.dumps(full)))
    cum = full.get('cumulative') or {}
    delta = full.get('delta_since_prior') or {}
    cp = full.get('checkpoint_turn')
    if mode == 'delta_only':
        return {'checkpoint_turn': cp, 'evidence_class': 'delta_only', 'delta_since_prior': delta}
    if mode == 'tail_focus':
        return {'checkpoint_turn': cp, 'evidence_class': 'tail_focus', 'tail': (full.get('tail') or [])[-3:]}
    if mode == 'tool_hist_focus':
        return {'checkpoint_turn': cp, 'evidence_class': 'tool_hist_focus',
                'cumulative': {k: cum.get(k) for k in ('api_turns','compaction_event_count','reread_paths','tool_histogram')}}
    if mode == 'brief_cum_no_tail':
        return {'checkpoint_turn': cp, 'evidence_class': 'brief_cum_no_tail',
                'brief_anchor': (full.get('brief_anchor') or '')[:300], 'cumulative': cum}
    if mode == 'chars_budget_1200':
        keep = {'checkpoint_turn': cp, 'evidence_class': 'chars_budget_1200',
                'cumulative': {k: cum.get(k) for k in ('api_turns','compaction_event_count','reread_paths','assistant_text_chars','peak_ctx_tokens')},
                'delta_since_prior': {k: delta.get(k) for k in ('api_turns','assistant_text_chars')}}
        if len(json.dumps(keep, separators=(',',':'))) > 1200:
            keep['cumulative'] = {k: keep['cumulative'].get(k) for k in ('api_turns','compaction_event_count')}
        return keep
    if mode == 'window_delta_tools':
        return {'checkpoint_turn': cp, 'evidence_class': 'window_delta_tools',
                'delta_since_prior': {k: delta.get(k) for k in ('tool_histogram','assistant_text_chars','api_turns','compaction_event_count')}}
    return strip_leaks(project_state_fl(full, mode))

def load_packs():
    seen, packs = set(), []
    for d in SNAP_DIRS:
        if not d.is_dir(): continue
        for sp in sorted(d.glob('*.json')):
            try: pack = json.loads(sp.read_text())
            except Exception: continue
            if not pack.get('checkpoints'): continue
            wid = pack.get('worker_id') or sp.stem
            if wid in seen: continue
            seen.add(wid); pack['worker_id'] = wid; packs.append(pack)
    return packs

def pick_rep_snap(pack):
    """One representative checkpoint per session — mid of reached list."""
    cps = sorted(pack['checkpoints'], key=lambda s: int(s['checkpoint']))
    if not cps: return None
    return cps[len(cps)//2]

def scenario_list(max_scenarios):
    """Priority: NEW×NEW, NEW×FL-q, FL-state×NEW-q, base contrasts. Deduped."""
    scen = []
    def add(states, qs):
        for st in states:
            for q in qs:
                scen.append((st, q))
    add(STATES_NEW, list(Q_NEW))          # 6×22 = 132
    add(STATES_NEW, list(Q_FL))           # 6×6 = 36
    add(STATES_FL, list(Q_NEW))           # 4×22 = 88
    add(STATES_BASE, list(Q_NEW)[:8])     # thin base contrast
    add(STATES_FL, list(Q_FL))            # FL×FL
    # dedupe preserve order
    out, seen = [], set()
    for s in scen:
        if s in seen: continue
        seen.add(s); out.append(s)
        if len(out) >= max_scenarios: break
    return out

def build_cells():
    packs = load_packs()
    # RR session order
    packs = sorted(packs, key=lambda p: (0 if p.get('harness')=='claude-code' else 1, p['worker_id']))
    scenarios = scenario_list(MAX_SCENARIOS)
    cells = []
    for state_v, qk in scenarios:
        qtext = QUESTIONS[qk]
        for pack in packs:
            snap = pick_rep_snap(pack)
            if not snap: continue
            full = snap.get('full_state') or {}
            if not isinstance(full, dict) or not full: continue
            cp = int(snap['checkpoint'])
            if 'checkpoint_turn' not in full:
                full = {**full, 'checkpoint_turn': cp}
            try:
                state = project(full, state_v)
            except Exception:
                continue
            sid = pack['worker_id']
            scenario_id = f'state.{state_v}|q.{qk}'
            raw = f'scenario|{scenario_id}|{sid}|rep{cp}|{FRAMING}|binary_fire'
            cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
            cells.append({
                'cell_id': cid,
                'scenario_id': scenario_id,
                'state_selection': state_v,
                'question_format': qk,
                'session_id': sid,
                'checkpoint': cp,
                'checkpoint_role': 'session_representative_mid',
                'framing': FRAMING,
                'question': qtext,
                'response_class': 'binary_fire',
                'state': state,
                'harness': pack.get('harness'),
                'project': pack.get('project'),
            })
    return cells, packs, scenarios

def post(cell):
    key = os.environ['TYPESAFE_API_KEY'].strip()
    body = {
        'model': JEV,
        'state': {
            'checkpoint_turn': cell['checkpoint'],
            'evidence_class': cell['state'].get('evidence_class') or cell['state_selection'],
            'scenario_id': cell['scenario_id'],
            'framing': cell['framing'],
            'snapshot': cell['state'],
        },
        'questions': {
            'fire_now': {
                'type': 'choice',
                'instructions': cell['question'] + ' Answer fire or defer from the snapshot only.',
                'criteria': {
                    'fire': 'Fire now: thrash/runaway / steer-to-stop indicated',
                    'defer': 'Defer: productive, near-done, healthy mid-arc, or insufficient evidence',
                },
            },
            'steer_urgency': {
                'type': 'score',
                'instructions': 'Steer-urgency 0..3 from snapshot only.',
                'criteria': ['0 defer/productive','1 mild concern','2 steer soon','3 fire/runaway'],
            },
        },
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(URL, data=data, method='POST',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            ans = json.loads(resp.read().decode()); err, code = None, resp.status
    except urllib.error.HTTPError as e:
        ans, err, code = None, f'HTTP {e.code}: {e.read().decode("utf-8", errors="replace")[:400]}', e.code
    except Exception as e:
        ans, err, code = None, f'{type(e).__name__}: {e}', None
    fire = None
    if ans and isinstance((ans.get('answers') or {}).get('fire_now'), dict):
        fire = ans['answers']['fire_now'].get('choice')
    return {
        'cell_id': cell['cell_id'],
        'scenario_id': cell['scenario_id'],
        'state_selection': cell['state_selection'],
        'question_format': cell['question_format'],
        'session_id': cell['session_id'],
        'checkpoint': cell['checkpoint'],
        'checkpoint_role': cell['checkpoint_role'],
        'framing': cell['framing'],
        'response_class': cell['response_class'],
        'harness': cell.get('harness'), 'project': cell.get('project'),
        'wall_s': round(time.time()-t0, 3), 'http': code, 'error': err,
        'answers': (ans or {}).get('answers') if ans else None,
        'usage': (ans or {}).get('usage') if ans else None,
        'fire': fire,
        'soft_standard_hold': True, 'product_wiring': False,
        'capture_tag': 'typesafe-scenario-sweep',
        'ts': datetime.now(AEST).isoformat(timespec='seconds'),
    }

def write_scenario_meters(rows, packs, scenarios, wall_s, tok_in, tok_out, err):
    scen_ids = sorted({r['scenario_id'] for r in rows})
    sessions = sorted({r['session_id'] for r in rows})
    by_scen = defaultdict(list)
    for r in rows:
        if r.get('fire') is not None:
            by_scen[r['scenario_id']].append(r['fire'] == 'fire')
    outcomes = {}
    for sid, flags in by_scen.items():
        outcomes[sid] = {
            'n_sessions': len(flags),
            'fire_count': sum(flags),
            'fire_rate': round(sum(flags)/len(flags), 4) if flags else None,
        }
    meters = {
        'metric': 'scenario_progress',
        'n_distinct_scenarios': len(scen_ids),
        'n_sessions_swept': len(sessions),
        'n_cells_incidental': len(rows),
        'n_packs_available': len(packs),
        'n_scenarios_planned': len(scenarios),
        'errors': err,
        'tok_in': tok_in, 'tok_out': tok_out, 'wall_s': wall_s,
        'checkpoint_policy': 'one_representative_mid_per_session',
        'window_cartesian': False,
        'soft_standard_hold': True,
        'product_wiring': False,
        'outcomes_by_scenario': outcomes,
        'scenario_ids': scen_ids,
        'generated_at': datetime.now(AEST).isoformat(timespec='seconds'),
    }
    (OUT/'meters.json').write_text(json.dumps(meters, indent=2)+'\n')
    # human note
    md = [
        '# SCENARIO-PROGRESS — TypeSafe corpus sweep',
        '',
        f"**Generated:** {meters['generated_at']}",
        '',
        '**Soft Standard HOLD** — measured corpus only; no product wiring.',
        '',
        '## Metric (not n_cells)',
        f"- **n_distinct_scenarios:** {meters['n_distinct_scenarios']}",
        f"- **n_sessions_swept:** {meters['n_sessions_swept']}",
        f"- n_cells (incidental = scenarios × sessions): {meters['n_cells_incidental']}",
        f"- window cartesian: **false** (1 representative checkpoint / session)",
        '',
        '## Scenario list (state × question)',
    ]
    for s in scen_ids:
        o = outcomes.get(s, {})
        md.append(f"- `{s}` — sessions={o.get('n_sessions')} fire_rate={o.get('fire_rate')}")
    md.append('')
    (OUT/'SCENARIO-PROGRESS.md').write_text('\n'.join(md)+'\n')
    # also drop a copy at batch root for WSM ping
    (BATCH/'SCENARIO-PROGRESS.md').write_text('\n'.join(md)+'\n')
    return meters

def main():
    assert os.environ.get('TYPESAFE_API_KEY', '').strip()
    cells, packs, scenarios = build_cells()
    plan = {
        'n_distinct_scenarios': len(scenarios),
        'n_sessions': len(packs),
        'n_cells_incidental': len(cells),
        'scenarios': [f'state.{a}|q.{b}' for a,b in scenarios],
        'checkpoint_policy': 'one_representative_mid_per_session',
        'window_cartesian': False,
        'soft_standard_hold': True,
        'product_wiring': False,
        'catalog': 'CASE-CATALOG.md',
    }
    (OUT/'cells_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({
        'n_distinct_scenarios': plan['n_distinct_scenarios'],
        'n_sessions': plan['n_sessions'],
        'n_cells_incidental': plan['n_cells_incidental'],
        'workers': WORKERS,
    }), flush=True)
    results = OUT/'results.jsonl'
    done=set()
    if results.exists():
        for line in results.read_text().splitlines():
            try: done.add(json.loads(line)['cell_id'])
            except Exception: pass
    todo=[c for c in cells if c['cell_id'] not in done]
    print(json.dumps({'todo': len(todo), 'already': len(done)}), flush=True)
    err=tok_in=tok_out=0
    t0=time.time()
    with results.open('a') as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs=[ex.submit(post, c) for c in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            row=fut.result(); f.write(json.dumps(row)+'\n'); f.flush()
            if row.get('error'): err+=1
            u=row.get('usage') or {}
            tok_in+=int(u.get('input_tokens') or 0); tok_out+=int(u.get('output_tokens') or 0)
            if i%50==0 or i==len(todo):
                # live scenario progress
                partial=[json.loads(l) for l in results.open()]
                n_sc=len({r['scenario_id'] for r in partial})
                n_sess=len({r['session_id'] for r in partial})
                print(json.dumps({
                    'done': i, 'todo': len(todo),
                    'n_distinct_scenarios': n_sc, 'n_sessions_swept': n_sess,
                    'err': err, 'tok_in': tok_in, 'wall_s': round(time.time()-t0,1),
                }), flush=True)
    rows=[json.loads(l) for l in results.open()]
    meters=write_scenario_meters(rows, packs, scenarios, round(time.time()-t0,1), tok_in, tok_out, err)
    print(json.dumps({
        'n_distinct_scenarios': meters['n_distinct_scenarios'],
        'n_sessions_swept': meters['n_sessions_swept'],
        'n_cells_incidental': meters['n_cells_incidental'],
        'errors': err, 'soft_hold': True,
    }), flush=True)
    return 0 if err < max(1, len(todo)//5) else 1

if __name__ == '__main__':
    raise SystemExit(main())
