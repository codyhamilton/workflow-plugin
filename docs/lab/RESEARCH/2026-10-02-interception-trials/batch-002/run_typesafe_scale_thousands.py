#!/usr/bin/env python3
"""TypeSafe bulk scale — Soft HOLD. Burn $10 headroom toward thousands of cells."""
from __future__ import annotations
import hashlib, json, os, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO = Path('/home/codyh/workspace/workflow-plugin')
BATCH = REPO / 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002'
SNAP_DIR = BATCH / 'snapshots'
OUT = BATCH / 'typesafe-scale'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'raw').mkdir(exist_ok=True)
AEST = ZoneInfo('Australia/Brisbane')
URL = 'https://api.typesafe.ai/v1/systemone'
SCHEDULE = (45, 60, 75, 90, 105, 120)
TARGET = int(os.environ.get('TYPESAFE_SCALE_TARGET', '3000'))
WORKERS = int(os.environ.get('TYPESAFE_SCALE_WORKERS', '20'))

TRIMS = {
    'full': None,
    'trim_mid': 6000,
    'trim_tight': 2500,
    'stats_only': 'stats',
}
QUERIES = {
    'steer_now': 'Is NOW a useful time to steer toward stopping, without truncating productive or near-done work? Judge only the snapshot.',
    'continue_excess': 'Will this job likely continue excessively from this checkpoint if uninterrupted? Judge only the snapshot.',
    'runaway_thrash': 'Do thrash/runaway signals dominate productive progress in this prefix? Judge only the snapshot.',
    'near_done_protect': 'Does this look like productive closing / near-done work that should NOT be truncated? Judge only the snapshot.',
    'plateau': 'Has progress velocity plateaued such that continuation adds little? Judge only the snapshot.',
}
FRAMINGS = ('H1', 'H2', 'H3', 'H4', 'H5')
LEAK_KEYS = {'t', 'T', 'session_length', 'norm_length', 'progress_frac', 'full_length', 'T_eligibility_only', 'length_metric'}


def strip_leaks(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_leaks(v) for k, v in obj.items() if k not in LEAK_KEYS and not str(k).lower().startswith('progress_')}
    if isinstance(obj, list):
        return [strip_leaks(x) for x in obj]
    return obj


def project(full: dict, trim: str) -> dict:
    s = strip_leaks(json.loads(json.dumps(full)))
    if trim == 'stats_only':
        keep = {}
        for k in ('checkpoint_turn', 'cumulative', 'tools', 'markers', 'phase_hints', 'evidence_class', 'schedule'):
            if k in s:
                keep[k] = s[k]
        keep['_trim'] = 'stats_only'
        return keep
    budget = TRIMS[trim]
    if budget is None:
        return s
    text = json.dumps(s, separators=(',', ':'), ensure_ascii=False)
    if len(text) <= budget:
        s['_trim'] = trim
        return s
    keep = {}
    for k in ('checkpoint_turn', 'cumulative', 'recent', 'tools', 'markers', 'phase_hints', 'evidence_class'):
        if k in s:
            keep[k] = s[k]
    if isinstance(keep.get('recent'), str) and len(json.dumps(keep)) > budget:
        keep['recent'] = keep['recent'][: max(200, budget - 1000)]
    elif isinstance(keep.get('recent'), list) and len(json.dumps(keep)) > budget:
        keep['recent'] = keep['recent'][:6]
    keep['_trim'] = trim
    return keep


def load_packs() -> list[dict]:
    packs = []
    for sp in sorted(SNAP_DIR.glob('*.json')):
        pack = json.loads(sp.read_text(encoding='utf-8'))
        if not pack.get('checkpoints'):
            continue
        pack.setdefault('worker_id', sp.stem)
        packs.append(pack)
    return packs


def build_cells(target: int) -> list[dict]:
    """Round-robin across all packs so sessions are not first-N skewed."""
    packs = load_packs()
    # precompute eligible (pack, snap, full) rows
    rows = []
    for pack in packs:
        sid = pack['worker_id']
        for snap in pack['checkpoints']:
            cp = int(snap['checkpoint'])
            if cp not in SCHEDULE:
                continue
            full = snap.get('full_state') or {}
            if not isinstance(full, dict) or not full:
                continue
            if 'checkpoint_turn' not in full:
                full = {**full, 'checkpoint_turn': cp}
            rows.append((sid, cp, full))
    if not rows:
        return []
    combos = [(trim, qk, qtext, fr) for trim in TRIMS for qk, qtext in QUERIES.items() for fr in FRAMINGS]
    cells = []
    # round-robin: for each combo, walk all sessions; repeat until target
    i = 0
    while len(cells) < target:
        trim, qk, qtext, fr = combos[i % len(combos)]
        sid, cp, full = rows[i % len(rows)]
        projected = project(full, trim)
        raw = f'typesafe|{fr}|{sid}|{cp}|{trim}|{qk}|rr{i}'
        # stable id without rr for dedupe of unique combo; allow multiple waves via wave tag
        raw_stable = f'typesafe|{fr}|{sid}|{cp}|{trim}|{qk}'
        cid = hashlib.sha1(raw_stable.encode()).hexdigest()[:16]
        cells.append({
            'cell_id': cid,
            'session_id': sid,
            'checkpoint': cp,
            'trim': trim,
            'query': qk,
            'question': qtext,
            'framing': fr,
            'state': projected,
            'harness': 'typesafe',
        })
        i += 1
        # unique by cell_id — skip dups by rebuilding with wave suffix once full cartesian filled
        if len(cells) >= len(rows) * len(combos):
            # expand with wave index for more volume without skew
            wave = 1 + (len(cells) // max(1, len(rows) * len(combos)))
            raw_stable = f'typesafe|{fr}|{sid}|{cp}|{trim}|{qk}|w{wave}'
            cells[-1]['cell_id'] = hashlib.sha1(raw_stable.encode()).hexdigest()[:16]
            cells[-1]['wave'] = wave
    # dedupe preserving order
    seen = set()
    uniq = []
    for c in cells:
        if c['cell_id'] in seen:
            continue
        seen.add(c['cell_id'])
        uniq.append(c)
        if len(uniq) >= target:
            break
    return uniq


def post(cell: dict) -> dict:
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
    req = urllib.request.Request(
        URL, data=data, method='POST',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'Accept': 'application/json'},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            ans = json.loads(resp.read().decode())
            err, code = None, resp.status
    except urllib.error.HTTPError as e:
        ans, err, code = None, f'HTTP {e.code}: {e.read().decode("utf-8", errors="replace")[:400]}', e.code
    except Exception as e:
        ans, err, code = None, f'{type(e).__name__}: {e}', None
    fire = None
    if ans and isinstance(ans.get('answers', {}).get('fire_now'), dict):
        fire = ans['answers']['fire_now'].get('choice')
    return {
        'cell_id': cell['cell_id'],
        'session_id': cell['session_id'],
        'checkpoint': cell['checkpoint'],
        'trim': cell['trim'],
        'query': cell['query'],
        'framing': cell['framing'],
        'harness': 'typesafe',
        'wall_s': round(time.time() - t0, 3),
        'http': code,
        'error': err,
        'answers': (ans or {}).get('answers') if ans else None,
        'usage': (ans or {}).get('usage') if ans else None,
        'fire': fire,
        'soft_standard_hold': True,
        'ts': datetime.now(AEST).isoformat(timespec='seconds'),
    }


def main() -> int:
    assert os.environ.get('TYPESAFE_API_KEY', '').strip(), 'TYPESAFE_API_KEY missing'
    cells = build_cells(TARGET)
    (OUT / 'cells_plan.json').write_text(json.dumps({
        'n': len(cells),
        'target': TARGET,
        'n_sessions': len({c['session_id'] for c in cells}),
        'trims': list(TRIMS),
        'queries': list(QUERIES),
        'framings': list(FRAMINGS),
        'schedule': list(SCHEDULE),
        'soft_standard_hold': True,
    }, indent=2) + '\n')
    print(json.dumps({'planned': len(cells), 'sessions': len({c['session_id'] for c in cells})}), flush=True)
    results_path = OUT / 'results.jsonl'
    done = set()
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            try:
                done.add(json.loads(line)['cell_id'])
            except Exception:
                pass
    todo = [c for c in cells if c['cell_id'] not in done]
    print(json.dumps({'todo': len(todo), 'already': len(done), 'workers': WORKERS}), flush=True)
    fire = err = tok_in = tok_out = 0
    t0 = time.time()
    with results_path.open('a') as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(post, c) for c in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            f.write(json.dumps(row) + '\n')
            f.flush()
            if row.get('fire') == 'fire':
                fire += 1
            if row.get('error'):
                err += 1
            u = row.get('usage') or {}
            tok_in += int(u.get('input_tokens') or 0)
            tok_out += int(u.get('output_tokens') or 0)
            if i % 50 == 0 or i == len(todo):
                print(json.dumps({
                    'done': i, 'todo': len(todo), 'fire': fire, 'err': err,
                    'tok_in': tok_in, 'wall_s': round(time.time() - t0, 1),
                }), flush=True)
    meters = {
        'n_cells': len(done) + len(todo),
        'new': len(todo),
        'fire': fire,
        'errors': err,
        'tok_in': tok_in,
        'tok_out': tok_out,
        'wall_s': round(time.time() - t0, 1),
        'soft_hold': True,
        'generated_at': datetime.now(AEST).isoformat(timespec='seconds'),
    }
    (OUT / 'meters.json').write_text(json.dumps(meters, indent=2) + '\n')
    print(json.dumps(meters), flush=True)
    return 0 if err < max(1, len(todo) // 5) else 1


if __name__ == '__main__':
    raise SystemExit(main())
