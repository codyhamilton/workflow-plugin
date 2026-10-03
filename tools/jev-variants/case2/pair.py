import os,re,json,hashlib,glob,collections
W=os.path.expanduser("~/workspace")
def proj(p):
    t=p.split("/")[0]
    for k in("open-pajero-maps","garcia-music","silver-chronicle","workflow-plugin","lemmings","free-frontier","chm-briefs","corpus-ops"):
        if t.startswith(k): return k
    return t
HD=re.compile(r"^(#{2,4})\s+(.*)$",re.M)
best={}
for bd in glob.glob(W+"/*/docs/plans/**/briefs",recursive=True):
    plandir=os.path.dirname(bd); impl=os.path.join(plandir,"IMPLEMENTATION.md")
    if not os.path.exists(impl): continue
    rel=os.path.relpath(bd,W); pj=proj(rel); plan=rel.split("/docs/plans/")[1].rsplit("/briefs",1)[0]
    txt=open(impl,errors="ignore").read(); hs=list(HD.finditer(txt))
    for f in sorted(glob.glob(bd+"/*.md")):
        fn=os.path.basename(f)[:-3]; m=re.match(r"(\d+(?:-\d+)?)[-_](.*)",fn)
        if not m: continue
        uid,slug=m.group(1),m.group(2)
        sec=None
        for i,h in enumerate(hs):
            t=h.group(2); 
            if re.match(r"\W*"+re.escape(uid)+r"\b",t) or slug.lower() in t.lower().replace(" ","-"):
                end=next((hs[j].start() for j in range(i+1,len(hs)) if len(hs[j].group(1))<=len(h.group(1))),len(txt))
                sec=txt[h.start():end]; break
        if not sec: continue
        br=open(f,errors="ignore").read()
        rec=dict(project=pj,plan=plan,unit=uid,slug=slug,brief_path=os.path.relpath(f,W),brief_md5=hashlib.md5(br.encode()).hexdigest(),section=sec[:3500],impl_len=len(txt))
        k=(pj,plan,uid,slug)
        if k not in best or rec["impl_len"]>best[k]["impl_len"]: best[k]=rec
U=list(best.values()); json.dump(U,open("pairs.json","w"))
print(len(U),collections.Counter(r["project"] for r in U),"distinct brief md5",len({r["brief_md5"] for r in U}))
