import json,sys,time,random
sys.argv=["x"]
from doc_runner import *
def call(req):
    for t in range(3):
        try: return post_systemone(req)
        except SystemExit as e: r={"error":str(e)};time.sleep(2)
    return r
AQ={"trouble_a":{"type":"score","instructions":"Which best describes how likely the worker is to hit unplanned trouble beyond what this brief anticipates?","criteria":["Routine: edits to understood code, every step concrete and checkable","Mostly routine; one step has some unknown","Likely trouble: a step depends on something the worker must discover, or new logic whose result may not hold","Very likely trouble: several steps hide unknowns, new files plus discovery, or a budget clearly too small"]}}
def anch(r):
    return {"t":"anchored","unit":r["unit"],"slug":r["slug"],"project":r["project"],"resp":call({"model":JEV_MODEL,"state":{"snapshot":scrub("BRIEF:\n"+r["brief_text"],10**9)},"questions":AQ})}
PQ={"worse":{"type":"score","instructions":"Two work briefs follow. Which one is more likely to cause the worker unplanned trouble (hidden extra steps, things to discover, results that may not hold)?","criteria":["Brief 1 clearly","Brief 1 slightly","Brief 2 slightly","Brief 2 clearly"]}}
def pair(a):
    p,n,o=a;f,s=(p,n) if o==0 else (n,p)
    txt=scrub("BRIEF 1:\n"+U[f]["brief_text"][:9000]+"\n\n=====\nBRIEF 2:\n"+U[s]["brief_text"][:9000],10**9)
    return {"t":"pair","pos":p,"neg":n,"order":o,"resp":call({"model":JEV_MODEL,"state":{"snapshot":txt},"questions":PQ})}
random.seed(0)
P=[i for i,r in enumerate(U) if r["label"]["outcome"]=="process_trouble"];N=[i for i,r in enumerate(U) if r["label"]["outcome"] in("clean","concerns")]
jobs=[(p,n,o) for p in P for n in random.sample(N,8) for o in (0,1)]
with ThreadPoolExecutor(8) as ex,open("t2b.jsonl","w") as f:
    for r in ex.map(anch,U): f.write(json.dumps(r)+"\n");f.flush()
    for r in ex.map(pair,jobs): f.write(json.dumps(r)+"\n");f.flush()
