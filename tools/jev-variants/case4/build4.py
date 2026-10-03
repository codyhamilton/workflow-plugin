import json,re,sys
sys.path.insert(0,"/home/codyh/.cursor/plugins/local/workflow-plugin/tools/driver")
from phase_assert import deterministic_outcome_evidence
B=json.load(open("blocks.json"))
def pick(plan,head_pat):
    return next(b for b in B if b["plan"]==plan and re.search(head_pat,b["head"]))
items=[]
p1=pick("pajero-03",r"^## Phase 1$");t=p1["text"];k=t.index("### 2-01")
items.append(("p03-phase1",t[:k],"closed"));items.append(("p03-phase2-run1",t[k:],"not_closed"))
items.append(("p03-phase2-restart",pick("pajero-03","restart")["text"],"not_closed"))
items.append(("p03-phase2-grounded",pick("pajero-03","grounded")["text"],"not_closed"))
items.append(("p03-phase2-remediation",pick("pajero-03","frame-adjacency")["text"],"closed"))
items.append(("p03-phase3C",pick("pajero-03","3C run")["text"],"closed_with_debt"))
items.append(("p04-phase1",pick("pajero-04","Phase 1")["text"],"closed"))
items.append(("p04-phase2",pick("pajero-04","Phase 2")["text"],"closed"))
items.append(("s01-phase3",pick("silver-01","Phase 3")["text"],"closed"))
items.append(("s01-phase4",pick("silver-01","Phase 4")["text"],"closed"))
items.append(("s01-phase5",pick("silver-01","Phase 5")["text"],"closed_with_concerns"))
VER=re.compile(r"verdict|verification|carried|\(close\)|close —|record —|closed|status",re.I)
def strip(t):
    out=[];skip=False
    for l in t.splitlines():
        if re.match(r"^#{1,3} ",l): skip=bool(VER.search(l))
        if skip: continue
        if re.search(r"NOT CLOSED|\*\*Status:\*\* closed|gate (FAILS|verdict)|CLOSED",l): continue
        out.append(l)
    return "\n".join(out)
R=[]
for name,t,lab in items:
    s=strip(t)
    f=dict(chars=len(s),units=len(re.findall(r"^#{2,3} .*(?:—|-) (?:done|over|blocked|stopped|kicked|dispatched)|^## Unit",s,re.M)),
      concerns=len(re.findall(r"concerns",s,re.I)),over_budget=len(re.findall(r"over budget|blocked|stopped|failed|attempt \d",s,re.I)),
      bounce=len(re.findall(r"bounce|re-?run|restart|redo|retry|unsuccessful|fails?\b",s,re.I)),met=len(re.findall(r"\bmet\b|\bpass(ed|es)?\b",s,re.I)))
    st={"slug":name,"phase":None,"trailer":"","design_outcome":"","closing_record":{"headings":[l.lstrip("# ").strip() for l in t.splitlines() if l.startswith("#")],"body":t},"workflow_report":{}}
    d=deterministic_outcome_evidence(st)
    f["det_verification_heading"]=int(d.checks["headings_verification"]);f["det_carried_heading"]=int(d.checks["headings_carried"]);f["det_evidence"]=int(d.checks["outcome_or_verification_evidence"])
    R.append(dict(name=name,label=lab,pos=lab=="not_closed",soft=lab!="closed",full=t,stripped=s,facts=f))
json.dump(R,open("items4.json","w"),indent=1)
for r in R: print(r["name"].ljust(24),r["label"].ljust(22),r["facts"])
