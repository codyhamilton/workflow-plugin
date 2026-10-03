import json,os,re,subprocess
W=os.path.expanduser("~/workspace")
U=json.load(open("labelled2.json"))
def git(repo,*a):
    r=subprocess.run(["git","-C",repo,*a],capture_output=True,text=True); return r.stdout if r.returncode==0 else None
def paths(s): return [p for p in re.findall(r"`([^`\s]+)`",s) if "/" in p or "." in p]
def section(br,name):
    m=re.search(r"^##\s+"+name+r".*?\n(.*?)(?=^##\s|\Z)",br,re.S|re.M|re.I); return m.group(1) if m else ""
def stat(repo,commit,p):
    p=p.split(":")[0].rstrip(".,;)")
    if any(c in p for c in "*<>{}"): return dict(path=p,kind="pattern")
    t=git(repo,"cat-file","-t",f"{commit}:{p}")
    if t is None: return dict(path=p,kind="missing")
    if t.strip()=="blob":
        b=git(repo,"show",f"{commit}:{p}"); return dict(path=p,kind="file",lines=b.count("\n")+1,bytes=len(b.encode()))
    ls=(git(repo,"ls-tree","-r","--name-only",commit,p) or "").split(); return dict(path=p,kind="dir",files=len(ls))
for r in U:
    f=os.path.join(W,r["brief_path"]); repo=os.path.dirname(f); top=os.path.join(W,r["brief_path"].split("/")[0])
    rel=os.path.relpath(f,top); br=open(f,errors="ignore").read()
    c=(git(top,"log","--diff-filter=A","--format=%H","-1","--",rel) or "").strip() or (git(top,"rev-parse","HEAD") or "").strip()
    parent=c
    own=re.search(r"Owned paths:\s*(.*)",br); own=paths(own.group(1)) if own else []
    rd=paths(section(br,"Required reading"))
    r["facts"]=dict(commit=parent[:10],owned=[stat(top,parent,p) for p in own],reading=[stat(top,parent,p) for p in rd])
    b=re.search(r"Budget:\s*(.*)",br); b=b.group(1) if b else ""
    n=lambda p:(lambda x:int(x.group(1)) if x else None)(re.search(p,b))
    r["budget"]=dict(text=b[:200],files=n(r"(\d+)\s+files?"),lines=n(r"(\d+)\s+lines?"),turns=n(r"(\d+)\s+(?:tool\s+)?turns?"))
    r["brief_text"]=br
    r["done_items"]=len(re.findall(r"^\s*[-*]\s",section(br,"Done evidence"),re.M)); r["changes_items"]=len(re.findall(r"^\s*[-*]\s",section(br,"Changes"),re.M))
json.dump(U,open("items.json","w"),indent=1)
print(sum(1 for r in U if r["facts"]["owned"]),"with owned;",sum(1 for r in U if r["budget"]["turns"]),"with turns budget")
print(U[0]["facts"]["owned"][:3],U[0]["facts"]["reading"][:3])
