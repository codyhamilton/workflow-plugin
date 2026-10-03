"""Case-2 runner: brief -> Jev complexity questions, 3 state variants. Usage: doc_runner.py [--limit N]"""
import json,sys,os,time,hashlib
from concurrent.futures import ThreadPoolExecutor
R="/home/codyh/.cursor/plugins/local/workflow-plugin/tools"
sys.path[:0]=[R+"/transcript",R+"/hooklog"]
from lib.jev_client import post_systemone, JEV_MODEL
from hooklog import scrub
U=json.load(open("items.json"))
CRIT=["no","slightly","likely","clearly"]
Q={
 "trouble":"Will the worker likely hit unplanned trouble (a hidden extra step, duplicated work, a boundary or cause it must discover, a result that does not hold) beyond what this brief anticipates?",
 "hidden":"Is any step in Changes substantially larger or more uncertain than its description suggests?",
 "budget":"Is the stated budget (files to read, lines to change, tool turns) too small for what Goal and Changes ask?",
 "fresh":"Does the brief require building new logic or new files from scratch, rather than editing existing understood code?",
 "complex":"Overall, is this a complex unit of work for a single worker session?",
}
QS={k:{"type":"score","instructions":v,"criteria":CRIT} for k,v in Q.items()}
def facts_table(r):
    f=r["facts"];L=["FACTS (computed from the repository at the brief's commit):"]
    b=r["budget"];L.append(f"Budget parsed: files={b['files']} lines={b['lines']} turns={b['turns']}")
    L.append(f"Brief sections: {r['done_items']} done-evidence items, {r['changes_items']} change items")
    L.append("Owned paths:")
    for x in f["owned"]:
        L.append(f"  {x['path']}: "+("DOES NOT EXIST YET (to be created)" if x["kind"]=="missing" else f"{x['kind']}, {x.get('lines','?')} lines, {x.get('bytes','?')} bytes"))
    L.append("Required reading:")
    for x in f["reading"]:
        L.append(f"  {x['path']}: "+("MISSING" if x["kind"]=="missing" else f"{x['kind']}, {x.get('lines','?')} lines"))
    return "\n".join(L)
def state(r,v):
    if v=="A": return "BRIEF:\n"+r["brief_text"]
    if v=="B": return "BRIEF:\n"+r["brief_text"]+"\n\n"+facts_table(r)
    return facts_table(r)+"\n\nGoal line: "+next((l for l in r["brief_text"].splitlines() if l.strip().startswith("# ")),"")
def one(a):
    r,v=a;txt=scrub(state(r,v),10**9)
    req={"model":JEV_MODEL,"state":{"snapshot":txt},"questions":{k:q for k,q in QS.items()}}
    for t in range(3):
        try:
            resp=post_systemone(req);break
        except SystemExit as e:
            resp={"error":str(e)};time.sleep(2)
    return {"unit":r["unit"],"slug":r["slug"],"project":r["project"],"state":v,"chars":len(txt),"resp":resp}
if __name__=="__main__":
    out=sys.argv[1];lim=int(sys.argv[2]) if len(sys.argv)>2 else len(U)
    jobs=[(r,v) for r in U[:lim] for v in "ABC"]
    with ThreadPoolExecutor(8) as ex, open(out,"a") as f:
        for row in ex.map(one,jobs): f.write(json.dumps(row)+"\n");f.flush()
