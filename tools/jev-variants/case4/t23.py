import json,sys,time,itertools
sys.argv=["x","/dev/null"]
from run4 import *
AQ={"notdone":("Which best describes whether the phase's intended outcome was achieved?",["Outcome met and verified end to end","Outcome probably met, but evidence is only that units were completed","Outcome partly met; named gaps remain","Outcome not met; phase must be redone or restarted"]),
"unresolved":("Which best describes failure/rework state at the end of this record?",["No gate failure, bounce or rework recorded","A past failure is recorded and shown fixed and re-verified","A failure or deviation is recorded and only partly resolved","A gate failure or restart is recorded with no later passing re-verification in this record"]),
"digdeeper":("How much further review does this phase need before the next phase starts?",["None: clean outcome evidence","Minor: one ambiguity","Specific claims lack evidence","Several unresolved or contradictory items; do not proceed"])}
QA={k:{"type":"score","instructions":i,"criteria":c} for k,(i,c) in AQ.items()}
def call(req):
    for t in range(3):
        try: return post_systemone(req)
        except SystemExit as e: r={"error":str(e)};time.sleep(2)
    return r
def anch(a):
    i,v=a;txt=scrub(state(U[i],v),10**9)
    return {"t":"anchored","i":i,"state":v,"resp":call({"model":JEV_MODEL,"state":{"snapshot":txt},"questions":QA})}
PQ={"worse":{"type":"score","instructions":"Two phase work records follow. Which one shows the phase's goal LESS clearly achieved (more unresolved failure, bounce, or rework)?","criteria":["Record 1 clearly","Record 1 slightly","Record 2 slightly","Record 2 clearly"]}}
def pair(a):
    p,n,o=a
    first,second=(p,n) if o==0 else (n,p)
    txt=scrub("RECORD 1:\n"+U[first]["stripped"][:12000]+"\n\n=====\nRECORD 2:\n"+U[second]["stripped"][:12000],10**9)
    return {"t":"pair","pos":p,"neg":n,"order":o,"resp":call({"model":JEV_MODEL,"state":{"snapshot":txt},"questions":PQ})}
with ThreadPoolExecutor(6) as ex,open("t23.jsonl","w") as f:
    for r in ex.map(anch,[(i,v) for i in range(len(U)) for v in "AB"]): f.write(json.dumps(r)+"\n")
    P=[i for i,r in enumerate(U) if r["soft"]];N=[i for i,r in enumerate(U) if not r["soft"]]
    for r in ex.map(pair,[(p,n,o) for p in P for n in N for o in (0,1)]): f.write(json.dumps(r)+"\n")
