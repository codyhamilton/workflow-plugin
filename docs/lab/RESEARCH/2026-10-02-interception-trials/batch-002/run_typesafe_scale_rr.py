#!/usr/bin/env python3
"""TypeSafe scale round-robin across ALL snapshot packs (Soft HOLD).

Fixes session skew from run_typesafe_scale_thousands (first-N fill).
Does not touch typesafe-scale/; writes typesafe-scale-rr/.
"""
from __future__ import annotations
import hashlib, json, os, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path('/home/codyh/workspace/workflow-plugin')
BATCH = REPO / 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002'
SNAP_DIRS = [BATCH / 'snapshots-dense', BATCH / 'snapshots']
OUT = BATCH / 'typesafe-scale-rr'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'raw').mkdir(exist_ok=True)
AEST = ZoneInfo('Australia/Brisbane')
URL = 'https://api.typesafe.ai/v1/systemone'
SCHEDULE = (45, 52, 60, 67, 75, 82, 90, 97, 105, 112, 120)
TARGET = int(os.environ.get('TYPESAFE_RR_TARGET', '2000'))
WORKERS = int(os.environ.get('TYPESAFE_RR_WORKERS', '16'))
TRIMS = {'full': None, 'trim_mid': 6000, 'trim_tight': 2500, 'stats_only': 'stats'}
QUERIES = {
    'steer_now': 'Is NOW a useful time to steer toward stopping, without truncating productive or near-done work? Judge only the snapshot.',
    'continue_excess': 'Will this job likely continue excessively from this checkpoint if uninterrupted? Judge only the snapshot.',
    'runaway_thrash': 'Do thrash/runaway signals dominate productive progress in this prefix? Judge only the snapshot.',
    'near_done_protect': 'Does this look like productive closing / near-done work that should NOT be truncated? Judge only the snapshot.',
    'plateau': 'Has progress velocity plateaued such that continuation adds little? Judge only the snapshot.',
}
FRAMINGS = ('H1', 'H2', 'H3', 'H4', 'H5')
LEAK_KEYS = {'t', 'T', 'session_length', 'norm_length', 'progress_frac', 'full_length', 'T_eligibility_only', 'length_metric'}

def strip_leaks(obj):
    if isinstance(obj, dict):
        return {k: strip_leaks(v) for k, v in obj.items() if k not in LEAK_KEYS and not str(k).lower().startswith('progress_')}
    if isinstance(obj, list):
        return [strip_leaks(x) for x in obj]
    return obj

def project(full, trim):
    s = strip_leaks(json.loads(json.dumps(full)))
    if trim == 'stats_only':
        keep = {k: s[k] for k in ('checkpoint_turn', 'cumulative', 'tools', 'markers', 'phase_hints', 'evidence_class', 'schedule') if k in s}
        keep['_trim'] = 'stats_only'
        return keep
    budget = TRIMS[trim]
    if budget is None:
        return s
    keep = {k: s[k] for k in ('checkpoint_turn', 'cumulative', 'recent', 'tail', 'tools', 'markers', 'phase_hints', 'evidence_class', 'brief_anchor') if k in s}
    text = json.dumps(keep, separators=(',', ':'), ensure_ascii=False)
    if len(text) > budget and isinstance(keep.get('tail'), list):
        keep['tail'] = keep['tail'][-2:]
    if len(json.dumps(keep)) > budget and isinstance(keep.get('brief_anchor'), str):
        keep['brief_anchor'] = keep['brief_anchor'][:200]
    keep['_trim'] = trim
    return keep

def load_packs():
    seen, packs = set(), []
    for d in SNAP_DIRS:
        if not d.is_dir():
            continue
        for sp in sorted(d.glob('*.json')):
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
            pack['worker_id'] = wid
            packs.append(pack)
    return packs

def build_cells(target):
    packs = load_packs()
    # round-robin (pack, snap) pairs
    lists = []
    for pack in packs:
        cps = [s for s in sorted(pack['checkpoints'], key=lambda x: int(x['checkpoint'])) if int(s['checkpoint']) in SCHEDULE]
        lists.append([(pack, s) for s in cps])
    pairs = []
    i = 0
    while True:
        added = False
        for lst in lists:
            if i < len(lst):
                pairs.append(lst[i]); added = True
        if not added:
            break
        i += 1
    cells = []
    for trim in TRIMS:
        for qk, qtext in QUERIES.items():
            for fr in FRAMINGS:
                for pack, snap in pairs:
                    sid = pack['worker_id']
                    cp = int(snap['checkpoint'])
                    full = snap.get('full_state') or {}
                    if not isinstance(full, dict) or not full:
                        continue
                    if 'checkpoint_turn' not in full:
                        full = {**full, 'checkpoint_turn': cp}
                    projected = project(full, trim)
                    raw = f'tsrr|{fr}|{sid}|{cp}|{trim}|{qk}'
                    cid = hashlib.sha1(raw.encode()).hexdigest()[:16]
                    cells.append({
                        'cell_id': cid, 'session_id': sid, 'checkpoint': cp,
                        'trim': trim, 'query': qk, 'question': qtext, 'framing': fr,
                        'state': projected, 'harness': pack.get('harness'),
                        'project': pack.get('project'),
                    })
                    if len(cells) >= target:
                        return cells, packs
    return cells, packs

def post(cell):
    key = os.environ['TYPESAFE_API_KEY'].strip()
    body = {
        'model': 'jev-1.13.0',
        'state': {
            'checkpoint_turn': cell['checkpoint'],
            'evidence_class': 'stats_hybrid',
            'framing': cell['framing'],
            'trim': cell['trim'],
            'snapshot': cell['state'],
        },
        'questions': {
            'fire_now': {
                'type': 'choice',
                'instructions': cell['question'] + ' Answer fire or defer only from the snapshot.',
                'criteria': {
                    'fire': 'Fire now: thrash/runaway / steer-to-stop indicated',
                    'defer': 'Defer: productive, near-done, or insufficient evidence',
                },
            },
            'steer_urgency': {
                'type': 'score',
                'instructions': 'Urgency of steering toward stop now (0 defer … 3 fire). Snapshot only.',
                'criteria': [
                    '0: clearly productive / defer',
                    '1: mild concern',
                    '2: useful to steer soon',
                    '3: fire / likely runaway',
                ],
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
    if ans and isinstance(ans.get('answers', {}).get('fire_now'), dict):
        fire = ans['answers']['fire_now'].get('choice')
    return {
        'cell_id': cell['cell_id'], 'session_id': cell['session_id'], 'checkpoint': cell['checkpoint'],
        'trim': cell['trim'], 'query': cell['query'], 'framing': cell['framing'],
        'harness': cell.get('harness'), 'project': cell.get('project'),
        'wall_s': round(time.time() - t0, 3), 'http': code, 'error': err,
        'answers': (ans or {}).get('answers') if ans else None,
        'usage': (ans or {}).get('usage') if ans else None,
        'fire': fire, 'soft_standard_hold': True,
        'ts': datetime.now(AEST).isoformat(timespec='seconds'),
        'capture_tag': 'typesafe-scale-rr',
    }

def main():
    assert os.environ.get('TYPESAFE_API_KEY', '').strip()
    cells, packs = build_cells(TARGET)
    (OUT / 'cells_plan.json').write_text(json.dumps({
        'n': len(cells), 'target': TARGET,
        'n_sessions': len({c['session_id'] for c in cells}),
        'n_packs': len(packs),
        'round_robin': True,
        'schedule': list(SCHEDULE),
        'soft_standard_hold': True,
    }, indent=2) + '\n')
    print(json.dumps({'planned': len(cells), 'sessions': len({c['session_id'] for c in cells}), 'packs': len(packs)}), flush=True)
    results_path = OUT / 'results.jsonl'
    done = set()
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try: done.add(json.loads(line)['cell_id'])
            except Exception: pass
    todo = [c for c in cells if c['cell_id'] not in done]
    print(json.dumps({'todo': len(todo), 'already': len(done), 'workers': WORKERS}), flush=True)
    fire = err = tok_in = tok_out = 0
    t0 = time.time()
    with results_path.open('a') as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(post, c) for c in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            f.write(json.dumps(row) + '\n'); f.flush()
            if row.get('fire') == 'fire': fire += 1
            if row.get('error'): err += 1
            u = row.get('usage') or {}
            tok_in += int(u.get('input_tokens') or 0)
            tok_out += int(u.get('output_tokens') or 0)
            if i % 50 == 0 or i == len(todo):
                print(json.dumps({'done': i, 'todo': len(todo), 'fire': fire, 'err': err, 'tok_in': tok_in, 'wall_s': round(time.time()-t0,1)}), flush=True)
    meters = {'n_cells': len(done)+len(todo), 'new': len(todo), 'fire': fire, 'errors': err,
              'tok_in': tok_in, 'tok_out': tok_out, 'wall_s': round(time.time()-t0,1),
              'n_sessions': len({c['session_id'] for c in cells}), 'round_robin': True,
              'soft_hold': True, 'generated_at': datetime.now(AEST).isoformat(timespec='seconds')}
    (OUT / 'meters.json').write_text(json.dumps(meters, indent=2) + '\n')
    print(json.dumps(meters), flush=True)
    return 0 if err < max(1, len(todo)//5) else 1

if __name__ == '__main__':
    raise SystemExit(main())
