import json,sys,time
R_="/home/codyh/.cursor/plugins/local/workflow-plugin/tools"
sys.path[:0]=[R_+"/transcript",R_+"/hooklog"]
from lib.jev_client import post_systemone, JEV_MODEL
from hooklog import scrub
from concurrent.futures import ThreadPoolExecutor
U=json.load(open("items4.json"))
CRIT=["no","slightly","likely","clearly"]
Q={"notdone":"Does this record suggest the phase's goal was NOT actually achieved, even though the individual units report done?",
 "digdeeper":"Should a reviewer dig deeper before the next phase starts?",
 "unresolved":"Does the record show an unresolved failure, bounced design, or failed gate that remains open?",
 "claimed":"Are completion claims here asserted without evidence tied to the intended outcome?",
 "concerns":"Overall, how heavily do concerns, deviations and retries weigh on this phase?"}
QS={k:{"type":"score","instructions":v,"criteria":CRIT} for k,v in Q.items()}
def facts(r):
    f=r["facts"];return ("FACTS (counted from the record): "+", ".join(f"{k}={v}" for k,v in f.items() if not k.startswith("det_")))
def state(r,v):
    if v=="A": return "PHASE WORK RECORD (closing verdict section removed):\n"+r["stripped"][:30000]
    if v=="B": return facts(r)+"\n\n"+"PHASE WORK RECORD (closing verdict section removed):\n"+r["stripped"][:30000]
    if v=="C": return facts(r)
    return "PHASE RECORD (full, including closing sections):\n"+r["full"][:30000]
def one(a):
    i,v=a;txt=scrub(state(U[i],v),10**9)
    req={"model":JEV_MODEL,"state":{"snapshot":txt},"questions":QS}
    for t in range(3):
        try: resp=post_systemone(req);break
        except SystemExit as e: resp={"error":str(e)};time.sleep(2)
    return {"i":i,"state":v,"chars":len(txt),"resp":resp}
if __name__=="__main__":
    with ThreadPoolExecutor(6) as ex,open(sys.argv[1],"a") as f:
        for row in ex.map(one,[(i,v) for i in range(len(U)) for v in "ABCD"]): f.write(json.dumps(row)+"\n")
