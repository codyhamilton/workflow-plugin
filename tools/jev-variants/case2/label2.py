import json,os,re,urllib.request
from concurrent.futures import ThreadPoolExecutor
K=json.load(open(os.path.expanduser("~/.local/share/opencode/auth.json")))["deepseek"]["key"]
U=json.load(open("pairs.json"))
P="""Below is the recorded outcome section for one work unit (a brief given to an AI worker). Classify the unit from this text only.
process_trouble = the WORK PROCESS exceeded or failed its scope: status over budget / blocked / needs context, budget lifted or doubled, worker stalled/killed/stopped, left a handoff unfinished, retried or re-dispatched with another model, split into more units because it was too big.
negative_result = the unit ran fine but its answer was negative or a gate failed/not closed/provisional (a finding, not a process failure).
concerns = completed but with notable deviations, contradictions, extra unplanned work, or open concerns flagged.
clean = completed as briefed, no meaningful problems.
If both process trouble and a negative result apply, choose process_trouble.
Reply JSON only: {"outcome":"clean|concerns|negative_result|process_trouble","evidence":"<short verbatim quote>"}

SECTION:
"""
def one(r):
    b={"model":"deepseek-chat","temperature":0,"max_tokens":300,"messages":[{"role":"user","content":P+r["section"]}]}
    for _ in range(3):
        try:
            q=urllib.request.Request("https://api.deepseek.com/chat/completions",json.dumps(b).encode(),{"Authorization":"Bearer "+K,"Content-Type":"application/json"})
            t=json.load(urllib.request.urlopen(q,timeout=90))["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}",t,re.S).group(0))
        except Exception as e: err=str(e)
    return {"outcome":None,"evidence":err}
with ThreadPoolExecutor(8) as ex: L=list(ex.map(one,U))
for r,l in zip(U,L): r["label"]=l
json.dump(U,open("labelled2.json","w"),indent=1)
import collections
print(collections.Counter(l.get("outcome") for l in L))
print(collections.Counter((r["project"],r["label"].get("outcome")) for r in U))
