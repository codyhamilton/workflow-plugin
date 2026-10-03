import json,numpy as np
from scipy.stats import rankdata
U=json.load(open("items.json"))
STRICT={("2-02","header-word-census"),("2-03","overlay-test"),("2-11","boundary-mirror"),("3-11","mult-const-selection"),("3-12","overlap-duplication-remeasure"),("3-07","cause-table-background"),("3-08","cause-table-remainder")}
y1=np.array([r["label"]["outcome"]=="process_trouble" for r in U])
y2=np.array([(r["unit"],r["slug"]) in STRICT for r in U])
y3=np.array([r["label"]["outcome"] in("process_trouble","negative_result") for r in U])
print("n",len(U),"pos",y1.sum(),y2.sum(),y3.sum())
def A(s,y):
    s=np.nan_to_num(np.array(s,float),nan=0); r=rankdata(s); return (r[y].sum()-y.sum()*(y.sum()+1)/2)/(y.sum()*(~y).sum())
def tot(r,k): return sum(x.get(k,0) or 0 for x in r["facts"]["owned"] if x["kind"]=="file")
F={"brief_chars":lambda r:len(r["brief_text"]),"budget_turns":lambda r:r["budget"]["turns"] or 0,"budget_lines":lambda r:r["budget"]["lines"] or 0,"budget_files":lambda r:r["budget"]["files"] or 0,
"n_owned":lambda r:len(r["facts"]["owned"]),"owned_existing_lines":lambda r:tot(r,"lines"),"owned_new_files":lambda r:sum(x["kind"]=="missing" for x in r["facts"]["owned"]),
"reading_lines":lambda r:sum(x.get("lines",0) for x in r["facts"]["reading"]),"n_reading":lambda r:len(r["facts"]["reading"]),"done_items":lambda r:r["done_items"],"changes_items":lambda r:r["changes_items"]}
rng=np.random.default_rng(0)
pj=np.array([r["project"] for r in U])
for name,f in F.items():
    v=[f(r) for r in U]; out=[]
    for y in(y1,y2,y3): out.append(A(v,y))
    bs=[]
    for _ in range(500):
        i=rng.integers(0,len(U),len(U)); 
        if y1[i].any() and (~y1[i]).any(): bs.append(A(np.array(v)[i],y1[i]))
    print("%-22s proc %.2f [%.2f,%.2f]  strict %.2f  proc+neg %.2f"%(name,out[0],*np.percentile(bs,[5,95]),out[1],out[2]))
