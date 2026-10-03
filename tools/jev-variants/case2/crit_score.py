import json,numpy as np
exec(open("base.py").read().split("rng=")[0].replace('print("n"','#'))
R=[json.loads(l) for l in open("crit.jsonl")]
idx={(r["unit"],r["slug"],r["project"]):i for i,r in enumerate(U)}
K=list(R[0]["resp"]["answers"]);M=np.zeros((len(U),len(K)))
for d in R:
    for j,k in enumerate(K): M[idx[(d["unit"],d["slug"],d["project"])],j]=d["resp"]["answers"][k]["score"]
# trouble direction: absence of good criteria = trouble; discovery_needed high = trouble
G=M.copy()
for j,k in enumerate(K):
    if k!="discovery_needed": G[:,j]=3-M[:,j]
rng=np.random.default_rng(0)
def rep(name,s):
    bs=[]
    for _ in range(500):
        i=rng.integers(0,len(U),len(U))
        if y1[i].any() and (~y1[i]).any(): bs.append(A(s[i],y1[i]))
    print("%-22s proc %.2f [%.2f,%.2f] strict %.2f proc+neg %.2f | mean %.2f"%(name,A(s,y1),*np.percentile(bs,[5,95]),A(s,y2),A(s,y3),s.mean()))
for j,k in enumerate(K): rep(k,G[:,j])
rep("composite(all 8)",G.sum(1)); rep("composite(7 no budget)",G[:,[i for i,k in enumerate(K) if k!="scope_matches_budget"]].sum(1))
rep("counter owned_new_files",np.array([F["owned_new_files"](r) for r in U],float))
from scipy.stats import rankdata
pt=rankdata(np.array([F["owned_new_files"](r) for r in U],float)); rep("rank(composite)+rank(new_files)",rankdata(G.sum(1))+pt)
print("pairwise rho vs new_files",np.corrcoef(rankdata(G.sum(1)),pt)[0,1].round(2))
j=K.index("discovery_needed");d=G[:,j]
print("rho discovery vs new_files",np.corrcoef(rankdata(d),pt)[0,1].round(2))
rep("rank(discovery)+rank(new_files)",rankdata(d)+pt)
rep("rank(discovery)+rank(contract)",rankdata(d)+rankdata(G[:,K.index('contract_cited')]))
# by project
for p in sorted(set(pj if 'pj' in dir() else [r['project'] for r in U])):
    m=np.array([r['project']==p for r in U]);print(p,m.sum(),y1[m].sum(),"discovery AUC","%.2f"%A(d[m],y1[m]) if y1[m].any() and (~y1[m]).any() else "n/a")
