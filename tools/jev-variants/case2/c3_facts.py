import json,re,subprocess
def git(top,*a):
    r=subprocess.run(["git","-C",top,*a],capture_output=True,text=True,errors="ignore"); return r.stdout if r.returncode==0 else ""
fix=re.compile(r"^(fix|revert|hotfix)\b|\bfix(es|ed)?\b|\bbug\b|\bregress",re.I)
R=json.load(open("c3_items.json"))
for r in R:
    top,h=r["repo"],r["h"]
    r["y"]=any(l[1]<=72 and l[3]/r["nfiles"]>=0.5 for l in r["later_fix"])
    ns=git(top,"show","--numstat","--format=",h).splitlines()
    add=dele=0;tests=0;fl=[]
    for l in ns:
        a,d,f=(l.split("\t")+["","",""])[:3]
        if a.isdigit(): add+=int(a);dele+=int(d)
        fl.append(f); tests+=bool(re.search(r"test|spec",f,re.I))
    r["facts"]=dict(files=len(fl),added=add,deleted=dele,test_files=tests,docs_files=sum(bool(re.search(r"^docs/|\.md$",f)) for f in fl))
    # prior fix churn: fix commits in the 30 days before touching these files
    pr=0
    for f in fl[:15]:
        for s in git(top,"log","--format=%s","--before=%d"%r["ct"],"--since=%d"%(r["ct"]-30*86400),"-n","20","--",f).splitlines(): pr+=bool(fix.search(s))
    r["facts"]["prior_fix_30d"]=pr
    r["msg"]=git(top,"show","-s","--format=%B",h).strip()
    r["diffstat"]=git(top,"show","--stat=120","--format=",h)
    d=git(top,"show","--format=","--unified=2",h); r["diff"]=d[:14000]; r["diff_trunc"]=len(d)>14000
json.dump(R,open("c3_items.json","w"))
print(len(R),sum(r["y"] for r in R))
