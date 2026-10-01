#!/usr/bin/env python3
"""TypeSafe review_check top-up — Soft HOLD, distinct cases, append-only."""
from __future__ import annotations
import hashlib, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from collections import Counter
from zoneinfo import ZoneInfo

REPO = Path(os.environ.get('WORKFLOW_PLUGIN_REPO', Path(__file__).resolve().parents[5]))
BATCH = REPO / 'docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002'
SNAP_DIRS = [BATCH/'snapshots-mid', BATCH/'snapshots-dense', BATCH/'snapshots']
OUT = BATCH / 'typesafe-review-check'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'raw').mkdir(exist_ok=True)
PROOFS = REPO / 'docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs'
AEST = ZoneInfo('Australia/Brisbane')
URL = 'https://api.typesafe.ai/v1/systemone'
TARGET = int(os.environ.get('TS_REVIEW_TOPUP', '1500'))
WORKERS = int(os.environ.get('TS_REVIEW_WORKERS', '10'))

sys.path.insert(0, str(PROOFS))
from jev_signal_schemas import (
    build_unit_needs_review_request,
    build_refine_brief_request,
    build_session_progress_request,
    example_states,
)

BODIES = {
    'strong_verify': '### Verification\n\nRan tests; evidence ties to design outcome. Exit 0.\n',
    'partial_verify': '### Verification\n\nRan some checks; not clearly tied to outcome.\n',
    'no_verify': '## Close\n\nShipped. Looks done.\n',
    'contradict': '### Verification\n\nSkipped verification; claimed success.\n',
    'placeholder': '### Verification\n\nTODO verify\n',
    'error_cascade': '### Verification\n\nRepeated tool errors; retries exhausted; no green run.\n',
    'polish_only': '### Verification\n\nTests green earlier; only docstring/format churn since.\n',
    'handoff_note': '### Carried\n\nNeeds parent handoff; unit incomplete by design.\n',
}

def load_packs():
    seen, packs = set(), []
    for d in SNAP_DIRS:
        if not d.is_dir(): continue
        for sp in sorted(d.glob('*.json')):
            try: pack=json.loads(sp.read_text())
            except Exception: continue
            if not pack.get('checkpoints'): continue
            wid=pack.get('worker_id') or sp.stem
            if wid in seen: continue
            seen.add(wid); pack['worker_id']=wid; packs.append(pack)
    return packs

def rr_pairs(packs):
    lists=[[(p,s) for s in sorted(p['checkpoints'], key=lambda x:int(x['checkpoint']))] for p in packs]
    out=[]; i=0
    while True:
        added=False
        for lst in lists:
            if i < len(lst): out.append(lst[i]); added=True
        if not added: break
        i+=1
    return out

def build_cells(target):
    packs=load_packs(); pairs=rr_pairs(packs); cells=[]
    ex=example_states()
    for key, builder in (('unit_needs_review','unit_needs_review'),('refine_brief','refine_brief'),('session_progress','session_progress')):
        st=ex[key]
        cid=hashlib.sha1(f'rvtop|example|{builder}'.encode()).hexdigest()[:16]
        cells.append({'cell_id':cid,'axis':'review_check','builder':builder,'variant':f'example|{builder}','state':st,'source':'example_states'})
    for pack, snap in pairs:
        sid=pack['worker_id']; cp=int(snap['checkpoint'])
        cum=(snap.get('full_state') or {}).get('cumulative') or {}
        slug=((pack.get('project') or pack.get('harness') or 'unit')[:28]).replace(' ','-').lower()
        slug=''.join(c if c.isalnum() or c in '-_' else '-' for c in slug) or 'unit'
        for body_k, body in BODIES.items():
            for phase in (1, 2, 3):
                for vex in (0, 1):
                    for trailer in (f'{slug}:{phase}', f'{slug}:done', ''):
                        st={
                            'question_id':'unit-needs-review','slug':slug,'phase':phase,
                            'unit_id':f'{sid[:8]}-cp{cp}-{body_k[:6]}',
                            'closing_headings':['## Phase','### Verification'] if 'verify' in body_k or body_k=='strong_verify' else ['## Phase'],
                            'closing_body_excerpt': f'Session {sid[:12]} @{cp}. api_turns={cum.get("api_turns")}.\n{body}'[:500],
                            'trailer': trailer, 'verifier_exit_code': vex,
                            'prefix_signals': {
                                'compaction_event_count': cum.get('compaction_event_count'),
                                'reread_paths': cum.get('reread_paths'),
                                'peak_ctx_tokens': cum.get('peak_ctx_tokens'),
                            },
                        }
                        variant=f'unit|{body_k}|p{phase}|vex{vex}|{trailer or "blank"}|{sid[:8]}|{cp}'
                        cid=hashlib.sha1(f'rvtop|unit_needs_review|{variant}'.encode()).hexdigest()[:16]
                        cells.append({'cell_id':cid,'axis':'review_check','builder':'unit_needs_review','variant':variant,
                                      'state':st,'session_id':sid,'checkpoint':cp,'harness':pack.get('harness'),
                                      'project':pack.get('project'),'source':'corpus_synth'})
                        if len(cells)>=target: return cells
                for lines in (40, 120, 240, 600):
                    st={
                        'question_id':'refine-brief-complexity','slug':slug,'phase':phase,
                        'brief_id':f'{sid[:8]}-{cp}','brief_title':f'Refine @{cp} {body_k}',
                        'brief_line_count': lines,
                        'brief_excerpt': (body + f'\napi_turns={cum.get("api_turns")}\n')[:400],
                        'design_outcome': f'Phase {phase} outcome for {slug}',
                    }
                    variant=f'refine|L{lines}|{body_k}|p{phase}|{sid[:8]}|{cp}'
                    cid=hashlib.sha1(f'rvtop|refine_brief|{variant}'.encode()).hexdigest()[:16]
                    cells.append({'cell_id':cid,'axis':'review_check','builder':'refine_brief','variant':variant,
                                  'state':st,'session_id':sid,'checkpoint':cp,'harness':pack.get('harness'),
                                  'project':pack.get('project'),'source':'corpus_synth'})
                    if len(cells)>=target: return cells
                for batch_n in (1, 2, 8):
                    st={
                        'question_id':'session-progress','slug':slug,'phase':phase,
                        'brief_id':f'{sid[:8]}-{cp}',
                        'api_turns': int(cum.get('api_turns') or cp),
                        'peak_ctx_tokens': int(cum.get('peak_ctx_tokens') or 0) or 90000,
                        'last_tool_batch': [f'tool-{i}' for i in range(batch_n)],
                        'design_outcome_line': f'Phase {phase} progress for {slug}',
                        'compaction_event_count': cum.get('compaction_event_count'),
                        'reread_paths': cum.get('reread_paths'),
                    }
                    variant=f'prog|t{cp}|b{batch_n}|{body_k}|p{phase}|{sid[:8]}'
                    cid=hashlib.sha1(f'rvtop|session_progress|{variant}'.encode()).hexdigest()[:16]
                    cells.append({'cell_id':cid,'axis':'review_check','builder':'session_progress','variant':variant,
                                  'state':st,'session_id':sid,'checkpoint':cp,'harness':pack.get('harness'),
                                  'project':pack.get('project'),'source':'corpus_synth'})
                    if len(cells)>=target: return cells
    return cells

BUILDERS = {
    'unit_needs_review': build_unit_needs_review_request,
    'refine_brief': build_refine_brief_request,
    'session_progress': build_session_progress_request,
}

def post(cell):
    key=os.environ['TYPESAFE_API_KEY'].strip()
    st=deepcopy(cell['state'])
    req=BUILDERS[cell['builder']](st)
    cid=cell['cell_id']
    (OUT/'raw'/f'{cid}-request.json').write_text(json.dumps(req, indent=2)+'\n')
    data=json.dumps(req).encode()
    http=urllib.request.Request(URL, data=data, method='POST',
        headers={'Authorization':f'Bearer {key}','Content-Type':'application/json','Accept':'application/json'})
    t0=time.time()
    try:
        with urllib.request.urlopen(http, timeout=120) as resp:
            raw=resp.read().decode(); code=resp.status; payload=json.loads(raw); err=None
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8', errors='replace')
        (OUT/'raw'/f'{cid}-error.txt').write_text(f'HTTP {e.code}\n{detail}\n')
        return {'cell_id':cid,'axis':'review_check','variant':cell.get('variant'),'builder':cell['builder'],
                'session_id':cell.get('session_id'),'checkpoint':cell.get('checkpoint'),
                'ok':False,'http':e.code,'error':f'HTTP {e.code}: {detail[:400]}',
                'wall_s':round(time.time()-t0,3),'soft_standard_hold':True,'product_wiring':False,
                'ts':datetime.now(AEST).isoformat(timespec='seconds')}
    except Exception as e:
        return {'cell_id':cid,'axis':'review_check','variant':cell.get('variant'),'builder':cell['builder'],
                'ok':False,'error':f'{type(e).__name__}: {e}','wall_s':round(time.time()-t0,3),
                'soft_standard_hold':True,'product_wiring':False,
                'ts':datetime.now(AEST).isoformat(timespec='seconds')}
    (OUT/'raw'/f'{cid}-response.json').write_text(raw+('\n' if not raw.endswith('\n') else ''))
    return {
        'cell_id':cid,'axis':'review_check','variant':cell.get('variant'),'builder':cell['builder'],
        'session_id':cell.get('session_id'),'checkpoint':cell.get('checkpoint'),
        'harness':cell.get('harness'),'project':cell.get('project'),
        'ok':True,'http':code,'error':err,'wall_s':round(time.time()-t0,3),
        'answers':payload.get('answers'),'usage':payload.get('usage'),
        'soft_standard_hold':True,'product_wiring':False,'capture_tag':'review-topup',
        'ts':datetime.now(AEST).isoformat(timespec='seconds'),
    }

def main():
    assert os.environ.get('TYPESAFE_API_KEY','').strip()
    cells=build_cells(TARGET)
    results=OUT/'results.jsonl'
    done=set()
    if results.exists():
        for line in results.read_text().splitlines():
            try: done.add(json.loads(line)['cell_id'])
            except Exception: pass
    todo=[c for c in cells if c['cell_id'] not in done]
    plan={'n_planned':len(cells),'n_todo':len(todo),'n_already':len(done),
          'builders':sorted({c['builder'] for c in cells}),
          'n_sessions':len({c.get('session_id') for c in cells if c.get('session_id')}),
          'soft_standard_hold':True,'product_wiring':False}
    (OUT/'topup_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps(plan), flush=True)
    ok=err=tok_in=tok_out=0; by_b=Counter()
    t0=time.time()
    with results.open('a') as f, ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs=[ex.submit(post,c) for c in todo]
        for i,fut in enumerate(as_completed(futs),1):
            row=fut.result(); f.write(json.dumps(row)+'\n'); f.flush()
            if row.get('ok'): ok+=1
            else: err+=1
            by_b[row.get('builder')]+=1
            u=row.get('usage') or {}
            tok_in+=int(u.get('input_tokens') or 0); tok_out+=int(u.get('output_tokens') or 0)
            if i%50==0 or i==len(todo):
                print(json.dumps({'done':i,'todo':len(todo),'ok':ok,'err':err,'by_builder':dict(by_b),'tok_in':tok_in,'wall_s':round(time.time()-t0,1)}), flush=True)
    all_rows=[json.loads(l) for l in results.open()]
    meters={'n_cells_file':len(all_rows),'new':len(todo),'ok':ok,'errors':err,
            'by_builder_all':dict(Counter(r.get('builder') for r in all_rows)),
            'tok_in':tok_in,'tok_out':tok_out,'wall_s':round(time.time()-t0,1),
            'soft_hold':True,'product_wiring':False,
            'generated_at':datetime.now(AEST).isoformat(timespec='seconds')}
    (OUT/'meters-topup.json').write_text(json.dumps(meters, indent=2)+'\n')
    print(json.dumps(meters), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
