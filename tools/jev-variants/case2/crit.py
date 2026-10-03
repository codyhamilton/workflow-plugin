import json,sys,time
sys.argv=["x"]
from doc_runner import *
def C(a,b,c,d): return [a,b,c,d]
CQ={
"contract_cited":("Does the Contract section cite its source by file path and section or quotation, and say which decisions are settled?",C("No Contract section, or no source named","Source named only loosely (a file, no section)","Cites a section or quote but does not say what is settled","Cites section/quote AND states what is settled")),
"concrete_changes":("Do the Changes state decisions concretely (named functions, signatures, values, data shapes), rather than only restating the goal?",C("Goal restated, no concrete decisions","A few concrete names, most steps vague","Most steps concrete, one or two vague","Every step names the concrete decision")),
"runnable_done":("Is each Done-evidence item a runnable command or an observable statement with an expected result?",C("No done evidence","Mostly vague statements (works, passes review)","Some runnable checks with expected results, some vague","Every item is runnable or observable with an expected result")),
"fail_first":("Does the brief identify or name a check that fails before the change and passes after?",C("No such check","Implied but not named","A check is named but the before-state is not stated","Check named with its before and after result")),
"keep_untouched":("Does the brief say what inside the owned paths must survive unchanged, and why?",C("Not mentioned","Mentioned generically","Names items but not why","Names the items and why")),
"bounded_reading":("Does Required reading give specific sections or ranges and say what is binding in each, rather than whole files?",C("No reading list","Whole files listed","Files with some sections","Every entry gives section/range and what is binding")),
"discovery_needed":("Does any step tell the worker to investigate, determine, find out, or decide something the brief does not already settle?",C("No step needs discovery","One minor step","Several steps depend on findings","The core step depends on something unknown")),
"scope_matches_budget":("Looking at the number and size of the Changes, does the stated budget (files, lines, turns) look sufficient?",C("Clearly too small","Tight","Adequate","Generous or clearly sufficient")),
}
QS={k:{"type":"score","instructions":i,"criteria":c} for k,(i,c) in CQ.items()}
def one(r):
    for t in range(3):
        try: resp=post_systemone({"model":JEV_MODEL,"state":{"snapshot":scrub("BRIEF:\n"+r["brief_text"],10**9)},"questions":QS});break
        except SystemExit as e: resp={"error":str(e)};time.sleep(2)
    return {"unit":r["unit"],"slug":r["slug"],"project":r["project"],"resp":resp}
with ThreadPoolExecutor(8) as ex,open("crit.jsonl","w") as f:
    for r in ex.map(one,U): f.write(json.dumps(r)+"\n")
