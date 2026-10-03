import json,sys
def auc(s,y):
    P=[a for a,b in zip(s,y) if b];N=[a for a,b in zip(s,y) if not b]
    return sum((p>n)+.5*(p==n) for p in P for n in N)/(len(P)*len(N))
U=json.load(open("items4.json"));rows=[json.loads(l) for l in open("run4.jsonl")]
for oc in("pos","soft"):
  y=[r[oc] for r in U]
  print(oc)
  for v in "ABD":
    for q in["notdone","unresolved","concerns"]:
      A=[next(x for x in rows if x['i']==i and x['state']==v)['resp']['answers'][q] for i in range(len(U))]
      sc=[a['score'] for a in A]; p3=[a['probabilities']['3'] for a in A]; p0=[-a['probabilities']['0'] for a in A]; conf=[a['confidence'] for a in A]
      # does confidence flag errors? error = |score-3*label|/3
      err=[abs(a['score']/3-int(l)) for a,l in zip(A,y)]
      import statistics as st
      ce=[c for c,e in zip(conf,err) if e>.5];co=[c for c,e in zip(conf,err) if e<=.5]
      print(f"  {v} {q:10s} score {auc(sc,y):.2f} P3 {auc(p3,y):.2f} -P0 {auc(p0,y):.2f} | conf wrong n={len(ce)} mean {st.mean(ce) if ce else float('nan'):.2f} vs right n={len(co)} mean {st.mean(co):.2f}")
