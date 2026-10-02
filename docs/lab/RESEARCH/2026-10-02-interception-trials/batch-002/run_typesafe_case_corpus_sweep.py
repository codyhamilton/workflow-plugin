#!/usr/bin/env python3
"""TypeSafe case×corpus sweep — Soft HOLD. CASE-CATALOG new+canonical × all packs RR."""
from __future__ import annotations
import hashlib, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import importlib.util

REPO = Path('/home/codyh/workspace/workflow-plugin')
BATCH = REPO / 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002'
SNAP_DIRS = [BATCH/'snapshots-mid', BATCH/'snapshots-dense', BATCH/'snapshots']
OUT = BATCH / 'typesafe-case-sweep'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'raw').mkdir(exist_ok=True)
AEST = ZoneInfo('Australia/Brisbane')
URL = 'https://api.typesafe.ai/v1/systemone'
TARGET = int(os.environ.get('TS_CASE_SWEEP_TARGET', '2500'))
WORKERS = int(os.environ.get('TS_CASE_SWEEP_WORKERS', '14'))
JEV = 'jev-1.13.0'

_spec = importlib.util.spec_from_file_location('fl_scale', BATCH/'run_batch002_flash_luna_scale.py')
_fl = importlib.util.module_from_spec(_spec)
sys.modules['fl_scale_batch002'] = _fl
_spec.loader.exec_module(_fl)
project_state_fl = _fl.project_state

FRAMINGS_THIN = {
    'H1': 'Framing H1 progressive re-check: fire-now vs defer-and-recheck ~15 turns.',
    'H3': 'Framing H3 progress velocity: sustained plateau/thrash vs substantive progress?',
    'H5': 'Framing H5 counterfactual waste: would steering now reduce avoidable continuation?',
}
Q_FL = {
    'recheck_interval': 'If deferring, is a ~10–15 turn re-check interval still justified, or should fire happen sooner?',
    'closing_protect': 'Would firing now risk interrupting closing-stage validation or delivery value?',
    'scope_drift': 'Do recent turns drift from the brief into unrelated scope expansion?',
    'activity_without_value': 'Is there frequent tool activity without checkable progress (activity ≠ value)?',
    'tail_risk': "Is the trajectory's continuation tail risk high enough to warrant steering toward stop?",
    'recoverable_stall': 'Does a stall look recoverable/valuable, such that deferral is better than fire?',
}
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
Q_BASE = {
    'steer_now': 'Is NOW a useful time to steer toward stopping, without truncating productive or near-done work? Judge only the snapshot.',
    'thrash_bundle': 'Do compaction, rereads, and weak new output form a thrash bundle? Judge only the snapshot.',
    'defer_recheck': 'Should interception DEFER and re-check ~15 turns later instead of firing now? Judge only the snapshot.',
}
QUESTIONS = {**Q_BASE, **Q_FL, **Q_NEW}
PROJ_FL = ('state_length_short', 'state_length_mid', 'deterministic_trim_v1', 'deterministic_trim_v2', 'stats_only', 'compact_focus')
PROJ_NEW = ('delta_only', 'tail_focus', 'tool_hist_focus', 'brief_cum_no_tail', 'chars_budget_1200', 'window_delta_tools')
PROJECTIONS = tuple(dict.fromkeys([*PROJ_NEW, *PROJ_FL]))
LEAK = {'t','T','session_length','norm_length','progress_frac','full_length','T_eligibility_only','length_metric'}

def strip_leaks(obj):
    if isinstance(obj, dict):
        return {k: strip_leaks(v) for k,v in obj.items() if k not in LEAK and not str(k).lower().startswith('progress_')}
    if isinstance(obj, list):
        return [strip_leaks(x) for x in obj]
    return obj

def project_new(full: dict, mode: str) -> dict:
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
    return project_state_fl(full, mode)

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

def rr_pairs(packs):
    lists = [[(p,s) for s in sorted(p['checkpoints'], key=lambda x: int(x['checkpoint']))] for p in packs]
    out=[]; i=0
    while True:
        added=False
        for lst in lists:
            if i < len(lst): out.append(lst[i]); added=True
        if not added: break
        i += 1
    return out

def build_cells(target):
    packs = load_packs(); pairs = rr_pairs(packs); cells=[]
    q_order = list(Q_NEW) + list(Q_FL) + list(Q_BASE)
    for qk in q_order:
        qtext = QUESTIONS[qk]
        for proj in PROJECTIONS:
            for fr in FRAMINGS_THIN:
                for pack, snap in pairs:
                    full = snap.get('full_state') or {}
                    if not isinstance(full, dict) or not full: continue
                    cp = int(snap['checkpoint'])
                    if 'checkpoint_turn' not in full:
                        full = {**full, 'checkpoint_turn': cp}
                    try:
                        state = project_new(full, proj) if proj in PROJ_NEW else strip_leaks(project_state_fl(full, proj))
                    except Exception:
                        continue
                    raw = f'casesweep|{fr}|{pack["worker_id"]}|{cp}|{proj}|{qk}|binary_fire'
                    cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
                    cells.append({
                        'cell_id': cid, 'session_id': pack['worker_id'], 'checkpoint': cp,
                        'framing': fr, 'state_variant': proj, 'question_variant': qk,
                        'question': qtext, 'framing_text': FRAMINGS_THIN[fr],
                        'response_class': 'binary_fire', 'state': state,
                        'harness': pack.get('harness'), 'project': pack.get('project'),
                        'case_ids': [f'state.{proj}', f'q.{qk}', f'framing.{fr}', 'rc.binary_fire'],
                    })
                    if len(cells) >= target:
                        return cells, packs
    return cells, packs

def post(cell):
    key = os.environ['TYPESAFE_API_KEY'].strip()
    body = {
        'model': JEV,
        'state': {
            'checkpoint_turn': cell['checkpoint'],
            'evidence_class': cell['state'].get('evidence_class') or cell['state_variant'],
            'framing': cell['framing'], 'framing_text': cell['framing_text'],
            'question_variant': cell['question_variant'], 'snapshot': cell['state'],
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
        'cell_id': cell['cell_id'], 'session_id': cell['session_id'], 'checkpoint': cell['checkpoint'],
        'framing': cell['framing'], 'state_variant': cell['state_variant'],
        'question_variant': cell['question_variant'], 'response_class': cell['response_class'],
        'case_ids': cell['case_ids'], 'harness': cell.get('harness'), 'project': cell.get('project'),
        'wall_s': round(time.time()-t0, 3), 'http': code, 'error': err,
        'answers': (ans or {}).get('answers') if ans else None,
        'usage': (ans or {}).get('usage') if ans else None,
        'fire': fire, 'soft_standard_hold': True, 'product_wiring': False,
        'capture_tag': 'typesafe-case-sweep',
        'ts': datetime.now(AEST).isoformat(timespec='seconds'),
    }

def main():
    assert os.environ.get('TYPESAFE_API_KEY', '').strip()
    cells, packs = build_cells(TARGET)
    plan = {
        'n': len(cells), 'target': TARGET, 'n_packs': len(packs),
        'n_sessions': len({c['session_id'] for c in cells}),
        'n_questions': len({c['question_variant'] for c in cells}),
        'n_projections': len({c['state_variant'] for c in cells}),
        'questions': sorted({c['question_variant'] for c in cells}),
        'projections': sorted({c['state_variant'] for c in cells}),
        'round_robin': True, 'soft_standard_hold': True, 'product_wiring': False,
        'catalog': 'CASE-CATALOG.md',
    }
    (OUT/'cells_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({k: plan[k] for k in ('n','n_packs','n_sessions','n_questions','n_projections')}), flush=True)
    results = OUT/'results.jsonl'
    done=set()
    if results.exists():
        for line in results.read_text().splitlines():
            try: done.add(json.loads(line)['cell_id'])
            except Exception: pass
    todo=[c for c in cells if c['cell_id'] not in done]
    print(json.dumps({'todo': len(todo), 'already': len(done), 'workers': WORKERS}), flush=True)
    fire=err=tok_in=tok_out=0
    t0=time.time()
    with results.open('a') as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs=[ex.submit(post, c) for c in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            row=fut.result(); f.write(json.dumps(row)+'\n'); f.flush()
            if row.get('fire')=='fire': fire+=1
            if row.get('error'): err+=1
            u=row.get('usage') or {}
            tok_in+=int(u.get('input_tokens') or 0); tok_out+=int(u.get('output_tokens') or 0)
            if i%50==0 or i==len(todo):
                print(json.dumps({'done':i,'todo':len(todo),'fire':fire,'err':err,'tok_in':tok_in,'wall_s':round(time.time()-t0,1)}), flush=True)
    meters={'n_cells': len(done)+len(todo), 'new': len(todo), 'fire': fire, 'errors': err,
            'tok_in': tok_in, 'tok_out': tok_out, 'wall_s': round(time.time()-t0,1),
            'n_sessions': plan['n_sessions'], 'n_questions': plan['n_questions'],
            'n_projections': plan['n_projections'], 'round_robin': True,
            'soft_hold': True, 'product_wiring': False,
            'generated_at': datetime.now(AEST).isoformat(timespec='seconds')}
    (OUT/'meters.json').write_text(json.dumps(meters, indent=2)+'\n')
    from collections import Counter, defaultdict
    rows=[json.loads(l) for l in results.open()] if results.exists() else []
    fire_qp=defaultdict(lambda: [0,0])
    for r in rows:
        if r.get('fire') is None: continue
        k=(r.get('question_variant'), r.get('state_variant'), r.get('framing'))
        fire_qp[k][1]+=1
        if r.get('fire')=='fire': fire_qp[k][0]+=1
    desc={
        'n': len(rows),
        'by_question': dict(Counter(r.get('question_variant') for r in rows)),
        'by_projection': dict(Counter(r.get('state_variant') for r in rows)),
        'by_framing': dict(Counter(r.get('framing') for r in rows)),
        'n_sessions': len({r.get('session_id') for r in rows}),
        'fire_rate_sample': {
            f'{q}|{p}|{fr}': {'fire':a,'n':b,'rate': round(a/b,4) if b else None}
            for (q,p,fr),(a,b) in sorted(fire_qp.items(), key=lambda kv: -kv[1][1])[:40]
        },
        'soft_hold': True,
    }
    (OUT/'DESCRIPTIVE-STATS.json').write_text(json.dumps(desc, indent=2)+'\n')
    print(json.dumps(meters), flush=True)
    return 0 if err < max(1, len(todo)//5) else 1

if __name__ == '__main__':
    raise SystemExit(main())
