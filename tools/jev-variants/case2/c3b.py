import json,os,re,subprocess,collections,sys
W=os.path.expanduser("~/workspace")
def git(top,*a):
    r=subprocess.run(["git","-C",top,*a],capture_output=True,text=True,errors="ignore"); return r.stdout if r.returncode==0 else ""
fix=re.compile(r"^(fix|revert|hotfix)\b|\bfix(es|ed)?\b|\bbug\b|\bregress",re.I)
WIN=7*86400
res=[]
for proj in ["open-pajero-maps","silver-chronicle","garcia-music-opt-18"]:
    top=os.path.join(W,proj)
    if not os.path.exists(top): print("no",top);continue
    log=[l.split("\t",3) for l in git(top,"log","--first-parent","--no-merges","--format=%H\t%ct\t%P\t%s").splitlines()]
    log=[(h,int(ct),s) for h,ct,p,s in log]; log.reverse()
    files={}
    for h,_,_ in log:
        files[h]=[f for f in git(top,"show","--name-only","--format=",h).split() if not re.search(r"(^|/)(docs|test|tests)/|\.(md|lock|json)$|test_|\.test\.",f)]
    for i,(h,ct,s) in enumerate(log):
        if fix.search(s) or not files[h] or len(files[h])>40: continue
        fs=set(files[h]); lat=[]
        for h2,ct2,s2 in log[i+1:]:
            if ct2-ct>WIN: break
            if fix.search(s2) and fs&set(files[h2]): lat.append((h2[:9],round((ct2-ct)/3600,1),s2[:70],len(fs&set(files[h2]))))
        res.append(dict(project=proj,repo=top,h=h,ct=ct,subject=s,nfiles=len(fs),later_fix=lat))
    print(proj,len(log),"candidates",sum(r["project"]==proj for r in res),"pos",sum(bool(r["later_fix"]) for r in res if r["project"]==proj))
json.dump(res,open("c3_items.json","w"),indent=1)
