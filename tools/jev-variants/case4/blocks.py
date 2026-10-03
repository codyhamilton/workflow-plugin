import re,json,os
W=os.path.expanduser("~/workspace")
def read(p): return open(os.path.join(W,p),errors="ignore").read()
def split_at(text,pat):
    L=text.splitlines();idx=[i for i,l in enumerate(L) if re.match(pat,l)]
    idx=[0]+[i for i in idx if i>0] if not idx or idx[0]!=0 else idx
    return [("\n".join(L[a:b])) for a,b in zip(idx,idx[1:]+[len(L)])]
items=[]
# pajero 03: runs
P3="open-pajero-maps/docs/plans/03-map-layer-parity-remediation/IMPLEMENTATION.md"
for b in split_at(read(P3),r"^(# Phase|## Phase \d+\s*$|## Phase \d+ run)"):
    items.append(dict(plan="pajero-03",head=b.splitlines()[0],text=b))
# pajero 04: phases
P4="open-pajero-maps/docs/plans/04-c-core-orchestration/IMPLEMENTATION.md"
for b in split_at(read(P4),r"^## Phase \d+\s*$"):
    items.append(dict(plan="pajero-04",head=b.splitlines()[0],text=b))
# silver 01: blocks ending in "## Phase N ... (close)"
S1="silver-chronicle-6-05/docs/plans/01-ux-functional-unblock/IMPLEMENTATION.md"
L=read(S1).splitlines();cuts=[i for i,l in enumerate(L) if re.match(r"^## Phase \d+ .*\(close\)",l)]
st=0
for c in cuts:
    e=next((i for i in range(c+1,len(L)) if L[i].startswith("## ") ),len(L))
    items.append(dict(plan="silver-01",head=L[c],text="\n".join(L[st:e]))); st=e
# silver 02: phases
S2="silver-chronicle/docs/plans/02-ci-and-dev-gates/IMPLEMENTATION.md"
for b in split_at(read(S2),r"^### Phase \d+ [^C]"):
    if b.startswith("### Phase"): items.append(dict(plan="silver-02",head=b.splitlines()[0],text=b))
for i in items: print(i["plan"],"|",i["head"][:70],"|",len(i["text"]))
json.dump(items,open("blocks.json","w"),indent=1)
