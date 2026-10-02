"""Round analysis: which marker wording / state variant tracks the proxy-detector labels, with
selection on discovery sessions and scoring on dev sessions, and session-cluster bootstrap CIs.

For each (signal, harness): per-marker and per-state AUC (marginalised over the other axis), a
marker x state AUC grid summary, and a select-on-discovery / evaluate-on-dev check so that picking the
best variant is not rewarded for noise. Held-out rows are never read.
Usage: analyze.py --root R --corpus corpus.json --ledger ledger.jsonl [--k 5] [--min-pos 8]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from events import load_events
from labels import auc, detectors, outcome, window_calls


def load_rows(a):
    corpus = json.loads(Path(a.corpus).read_text())
    corpus = corpus.get("sessions", corpus)
    names = {json.loads(f.read_text())["id"]: json.loads(f.read_text())["spec"]["name"] for f in Path(a.root, "signals").glob("*.json")}
    evc, dc, oc, out = {}, {}, {}, []
    seen = set()
    for line in Path(a.ledger).read_text().splitlines():
        r = json.loads(line)
        if r.get("score") is None or r["session"] not in corpus or corpus[r["session"]]["split"] == "heldout":
            continue
        k = (r["cell_id"], r["marker"])
        if k in seen:
            continue
        seen.add(k)
        s = corpus[r["session"]]
        ev = evc.setdefault(r["session"], load_events(s["harness"], s["path"]))
        key = (r["session"], r["checkpoint"])
        if key not in dc:
            dc[key] = detectors(window_calls(ev, r["checkpoint"], a.k))
        nm = names.get(r["signal"])
        if a.label != "proxy":
            if key not in oc:
                oc[key] = outcome(ev, r["checkpoint"])
            y = oc[key][a.label]
            if nm and y is not None:
                out.append({"sig": nm, "mk": r["marker"], "st": r["state"], "sess": r["session"], "split": s["split"],
                            "h": s["harness"], "cp": r["checkpoint"], "score": r["score"], "y": y})
        elif nm in dc[key]:
            out.append({"sig": nm, "mk": r["marker"], "st": r["state"], "sess": r["session"], "split": s["split"],
                        "h": s["harness"], "cp": r["checkpoint"], "score": r["score"], "y": dc[key][nm]})
    return out


def cauc(rows):
    return auc([r["score"] for r in rows if r["y"]], [r["score"] for r in rows if not r["y"]])


def boot(rows, n=200, seed=1):
    by = defaultdict(list)
    for r in rows:
        by[r["sess"]].append(r)
    ids = list(by)
    rnd = random.Random(seed)
    xs = []
    for _ in range(n):
        s = [r for i in (rnd.choice(ids) for _ in ids) for r in by[i]]
        v = cauc(s)
        if v is not None:
            xs.append(v)
    xs.sort()
    return (xs[int(.05 * len(xs))], xs[int(.95 * len(xs))]) if len(xs) > 20 else (None, None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--min-pos", type=int, default=8)
    ap.add_argument("--top", type=int, default=4)
    ap.add_argument("--label", choices=["proxy", "prompt_soon", "correction"], default="proxy",
                    help="proxy = tool-pattern detector; prompt_soon/correction = what the human did next")
    a = ap.parse_args()
    rows = load_rows(a)
    print(f"rows {len(rows)}  sessions {len({r['sess'] for r in rows})}")
    groups = defaultdict(list)
    for r in rows:
        groups[(r["sig"], r["h"])].append(r)
    for (sig, h), rs in sorted(groups.items()):
        pos = sum(r["y"] for r in rs)
        if pos < a.min_pos or len(rs) - pos < a.min_pos:
            print(f"\n## {sig} [{h}] n={len(rs)} pos={pos}: too few positives/negatives, skipped")
            continue
        lo, hi = boot(rs)
        print(f"\n## {sig} [{h}] n={len(rs)} pos={pos} sessions={len({r['sess'] for r in rs})} pooled AUC {cauc(rs):.2f} (90% CI {lo:.2f}-{hi:.2f})" if lo else f"\n## {sig} [{h}] n={len(rs)} pos={pos} pooled AUC {cauc(rs):.2f}")
        for axis, label in (("mk", "marker"), ("st", "state")):
            vals = defaultdict(list)
            for r in rs:
                vals[r[axis]].append(r)
            sc = {k: cauc(v) for k, v in vals.items() if cauc(v) is not None}
            if len(sc) < 2:
                continue
            vs = sorted(sc.items(), key=lambda kv: kv[1])
            print(f"  {label}s {len(vs)}: AUC range {vs[0][1]:.2f}-{vs[-1][1]:.2f}  spread {vs[-1][1]-vs[0][1]:.2f}")
            # select on discovery, evaluate on dev
            disc = {k: cauc([r for r in v if r["split"] == "discovery"]) for k, v in vals.items()}
            dev = {k: cauc([r for r in v if r["split"] == "dev"]) for k, v in vals.items()}
            ok = [k for k in vals if disc[k] is not None and dev[k] is not None]
            if len(ok) >= 4:
                ok.sort(key=lambda k: disc[k])
                n = min(a.top, len(ok) // 2)
                bot, top = ok[:n], ok[-n:]
                m = lambda ks: sum(dev[k] for k in ks) / len(ks)
                print(f"    selected on discovery, dev AUC: top{n} {m(top):.2f} vs bottom{n} {m(bot):.2f}  (replicates if top>bottom)")
            print("    best:", ", ".join(f"{k} {v:.2f}" for k, v in vs[-3:][::-1]), "| worst:", ", ".join(f"{k} {v:.2f}" for k, v in vs[:2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
