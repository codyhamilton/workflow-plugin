import json,numpy as np
from scipy.stats import rankdata,spearmanr
exec(open("base.py").read().split("rng=")[0].replace('print("n"','#'))
rows=[json.loads(l) for l in open("run1.jsonl")]
idx={(r["unit"],r["slug"],r["project"]):i for i,r in enumerate(U)}
def get(v,q):
    s=np.zeros(len(U))
    for d in rows:
        if d["state"]==v: s[idx[(d["unit"],d["slug"],d["project"])]]=d["resp"]["answers"][q]["score"]
    return s
nf=np.array([F["owned_new_files"](r) for r in U],float); bt=np.array([F["budget_turns"](r) for r in U],float)
z=lambda x:(rankdata(x)-1)/(len(x)-1)
for q in["trouble","complex"]:
    j=get("A",q); print(q,"rho vs new_files %.2f vs turns %.2f"%(spearmanr(j,nf)[0],spearmanr(j,bt)[0]))
    for nm,c in[("jev",z(j)),("nf+turns",z(nf)+z(bt)),("jev+nf",z(j)+z(nf)),("jev+nf+turns",z(j)+z(nf)+z(bt))]:
        print("  %-14s proc %.2f strict %.2f proc+neg %.2f"%(nm,A(c,y1),A(c,y2),A(c,y3)))
# by project
pj=np.array([r["project"] for r in U])
for p in set(pj): print(p,(pj==p).sum(),"pos",y1[pj==p].sum())
m=pj!="open-pajero-maps"
j=get("A","trouble"); print("non-pajero pos",y1[m].sum())
