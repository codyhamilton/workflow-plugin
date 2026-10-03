import json,sys,time
sys.argv=["x","/dev/null"]
from run4 import *
CQ={
"outcome_backed":("Is each claim that the phase outcome is achieved backed by a named command or observed output shown in the record?",["No claim is backed by shown output","Few claims backed","Most claims backed by shown output","Every outcome claim cites a command or output"]),
"units_not_outcome":("Does the evidence show only that individual units finished, with no end-to-end check of the phase's stated outcome?",["An end-to-end outcome check is shown","Outcome check mentioned but not shown","Mostly unit completion evidence","Only unit completion; no outcome check"]),
"failed_gate_open":("Does the record contain a failed gate, failed check or restart that has no later passing re-run shown in the same record?",["No failure recorded","Failure recorded and re-run passing is shown","Failure recorded, re-run partly shown","Failure recorded, no passing re-run shown"]),
"unexplained_deviation":("Does the record state deviations from the plan without giving a reason?",["No deviations","Deviations all with reasons","Some deviations lack a reason","Most deviations lack a reason"]),
"carried_named":("Are items not finished in this phase explicitly named as carried to a later phase?",["Unfinished items exist but none are named","Named vaguely","Named without where they go","Named with where they go, or nothing unfinished"]),
"rework":("Is any unit or step redone, reverted or re-planned during this record?",["No rework","One small redo","Several redos","Phase or major unit redone from scratch"]),
}
QS4={k:{"type":"score","instructions":i,"criteria":c} for k,(i,c) in CQ.items()}
def one(a):
    i,rep=a
    for t in range(3):
        try: resp=post_systemone({"model":JEV_MODEL,"state":{"snapshot":scrub(state(U[i],"A"),10**9)},"questions":QS4});break
        except SystemExit as e: resp={"error":str(e)};time.sleep(2)
    return {"i":i,"rep":rep,"resp":resp}
with ThreadPoolExecutor(6) as ex,open("crit4.jsonl","w") as f:
    for r in ex.map(one,[(i,k) for i in range(len(U)) for k in (0,1)]): f.write(json.dumps(r)+"\n")
