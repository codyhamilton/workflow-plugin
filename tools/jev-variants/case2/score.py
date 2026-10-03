import json,sys,numpy as np
exec(open("base.py").read().split("rng=")[0].replace('print("n"','#'))
rows=[json.loads(l) for l in open(sys.argv[1])]
idx={(r["unit"],r["slug"],r["project"]):i for i,r in enumerate(U)}
rng=np.random.default_rng(0)
for v in "ABC":
  for q in ["trouble","hidden","budget","fresh","complex"]:
    s=np.full(len(U),np.nan)
    for d in rows:
        if d["state"]==v and "answers" in d["resp"]: s[idx[(d["unit"],d["slug"],d["project"])]]=d["resp"]["answers"][q]["score"]
    ok=~np.isnan(s); out=[]
    for y in(y1,y2,y3): out.append(A(s[ok],y[ok]))
    bs=[]
    for _ in range(500):
        i=rng.integers(0,len(U),len(U));i=i[ok[i]]
        if y1[i].any() and (~y1[i]).any(): bs.append(A(s[i],y1[i]))
    print(v,"%-8s n=%d proc %.2f [%.2f,%.2f] strict %.2f proc+neg %.2f"%(q,ok.sum(),out[0],*np.percentile(bs,[5,95]),out[1],out[2]))
