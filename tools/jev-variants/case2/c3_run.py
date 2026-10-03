import json,sys,time
R_="/home/codyh/.cursor/plugins/local/workflow-plugin/tools"
sys.path[:0]=[R_+"/transcript",R_+"/hooklog"]
from lib.jev_client import post_systemone, JEV_MODEL
from hooklog import scrub
from concurrent.futures import ThreadPoolExecutor
U=json.load(open("c3_items.json"))
CRIT=["no","slightly","likely","clearly"]
Q={"fix":"Is a follow-up fix likely to be needed on these same files soon, because this change is incomplete, fragile, or wrong in a way tests will not show?",
 "review":"Does this change warrant a human review before more work builds on it?",
 "risk":"Does this change touch shared or load-bearing behaviour in a way that could break other code paths?",
 "partial":"Does the commit message or diff suggest the work is partial, provisional, or has known loose ends?",
 "complex":"Overall, is this a complex change?"}
QS={k:{"type":"score","instructions":v,"criteria":CRIT} for k,v in Q.items()}
def facts(r):
    f=r["facts"];return (f"FACTS (computed): files={f['files']} lines_added={f['added']} lines_deleted={f['deleted']} test_files_touched={f['test_files']} "
        f"doc_files_touched={f['docs_files']} fix_commits_on_these_files_in_prior_30d={f['prior_fix_30d']}")
def state(r,v):
    base=f"COMMIT MESSAGE:\n{r['msg']}\n\nDIFFSTAT:\n{r['diffstat']}"
    if v=="A": return base+"\n\nDIFF"+(" (truncated)" if r["diff_trunc"] else "")+":\n"+r["diff"]
    if v=="B": return base+"\n\n"+facts(r)+"\n\nDIFF"+(" (truncated)" if r["diff_trunc"] else "")+":\n"+r["diff"]
    return base+"\n\n"+facts(r)   # C: message + stat + facts, no diff body
def one(a):
    i,v=a;r=U[i];txt=scrub(state(r,v),10**9)
    req={"model":JEV_MODEL,"state":{"snapshot":txt},"questions":QS}
    for t in range(3):
        try: resp=post_systemone(req);break
        except SystemExit as e: resp={"error":str(e)};time.sleep(2)
    return {"i":i,"state":v,"chars":len(txt),"resp":resp}
if __name__=="__main__":
    out=sys.argv[1];lim=int(sys.argv[2]) if len(sys.argv)>2 else len(U)
    with ThreadPoolExecutor(8) as ex,open(out,"a") as f:
        for row in ex.map(one,[(i,v) for i in range(lim) for v in "ABC"]): f.write(json.dumps(row)+"\n");f.flush()
