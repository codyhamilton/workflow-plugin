import json,numpy as np
from scipy.stats import rankdata
U=json.load(open("c3_items.json"));rows=[json.loads(l) for l in open("c3_run1.jsonl")]
y=np.array([r["y"] for r in U]);g=np.array([r["project"].startswith("garcia") for r in U]);ct=np.array([r["ct"] for r in U])
print("n",len(U),"pos",y.sum(),"garcia n",g.sum(),"pos",y[g].sum())
def A(s,y):
    if y.sum() in(0,len(y)):return np.nan
    r=rankdata(np.nan_to_num(s));return (r[y].sum()-y.sum()*(y.sum()+1)/2)/(y.sum()*(~y).sum())
rng=np.random.default_rng(0)
def boot(s,m):
    idx=np.where(m)[0];b=[]
    for _ in range(400):
        i=rng.choice(idx,len(idx));b.append(A(s[i],y[i]))
    return np.nanpercentile(b,[5,95])
S={}
for k in["files","added","deleted","test_files","prior_fix_30d"]: S["base:"+k]=np.array([r["facts"][k] for r in U],float)
S["base:churn"]=S["base:added"]+S["base:deleted"]
S["base:msglen"]=np.array([len(r["msg"]) for r in U],float)
for v in"ABC":
    for q in["fix","review","risk","partial","complex"]:
        s=np.full(len(U),np.nan)
        for d in rows:
            if d["state"]==v and "answers" in d["resp"]: s[d["i"]]=d["resp"]["answers"][q]["score"]
        S[f"jev{v}:{q}"]=s
mid=np.median(ct[g])
print("%-18s %-5s %-16s %-6s %-6s %-6s"%("score","all","garcia[90%CI]","g1st","g2nd","nonG"))
for k,s in S.items():
    ok=~np.isnan(s);m=g&ok;lo,hi=boot(s,m)
    print("%-18s %.2f  %.2f [%.2f,%.2f]  %.2f  %.2f  %.2f"%(k,A(s[ok],y[ok]),A(s[m],y[m]),lo,hi,A(s[m&(ct<=mid)],y[m&(ct<=mid)]),A(s[m&(ct>mid)],y[m&(ct>mid)]),A(s[~g&ok],y[~g&ok])))

print("\n=== size-stratified (strata: files 1 / 2 / 3-4 / 5+), garcia ===")
nf=S["base:files"];st=np.digitize(nf,[2,3,5])
outs={"frac>=.5/72h":y,
      "any-overlap/72h":np.array([any(l[1]<=72 for l in r["later_fix"]) for r in U]),
      "any-overlap/7d":np.array([bool(r["later_fix"]) for r in U])}
for on,yy in outs.items():
    print(on,"pos",yy[g].sum(),"by stratum",[(int((yy&g&(st==k)).sum()),int((g&(st==k)).sum())) for k in range(4)])
    def SA(s,m):
        num=den=0
        for k in range(4):
            mk=m&(st==k)&~np.isnan(s);p=yy[mk]
            if p.sum()<3 or (~p).sum()<3: continue
            w=p.sum()*(~p).sum();num+=w*A(s[mk],p);den+=w
        return num/den if den else np.nan
    for k in["base:added","base:prior_fix_30d","base:test_files","base:msglen"]+[f"jev{v}:{q}" for v in"AC" for q in["fix","review","risk","partial","complex"]]:
        s=S[k];m=g.copy();idx=np.where(m)[0];b=[]
        for _ in range(200):
            i=rng.choice(idx,len(idx));mm=np.zeros(len(U),bool);
            # weighted resample via counts
            cnt=np.bincount(i,minlength=len(U));
            # emulate by duplicating
            ii=np.repeat(np.arange(len(U)),cnt);
            num=den=0
            for kk in range(4):
                mk=st[ii]==kk;p=yy[ii][mk]
                if p.sum()<3 or (~p).sum()<3: continue
                w=p.sum()*(~p).sum();num+=w*A(s[ii][mk],p);den+=w
            b.append(num/den if den else np.nan)
        print("  %-20s %.2f [%.2f,%.2f]"%(k,SA(s,m),*np.nanpercentile(b,[5,95])))
