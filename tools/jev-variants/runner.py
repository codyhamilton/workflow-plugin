"""Run expanded cells against Jev. Resumable via the ledger; pure request building is separate from I/O.

  runner.py --root R --round-file F --ledger L [--limit N] [--concurrency 4] [--dry-run]

One call per cell: all of the cell's markers go in one request, question ids namespaced
`<marker id>__<question id>`. One ledger row per (cell, marker) with the parsed answers, so `digest`
can group by signal/state/marker/panel. Raw usage (tokens only, verified live) is kept, and so are Jev's confidence/probabilities per answer; cost uses usage.cost_usd if present (it is not, so far), else the
round's est_cost_per_call_usd split evenly (flagged `cost_estimated`).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "transcript"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from events import load_events  # noqa: E402
from jev_variants import (canonical, expand, load_corpus, load_registry, read_ledger,  # noqa: E402
                          validate_registry, validate_round)
from state_builder import build_state  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooklog"))
from hooklog import scrub  # noqa: E402

SEP = "__"


def build_request(cell: dict[str, Any], reg: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    from lib.jev_client import JEV_MODEL
    questions: dict[str, Any] = {}
    for mid in cell["markers"]:
        for qid, q in reg["marker"][mid]["spec"]["question"].items():
            questions[f"{mid}{SEP}{qid}"] = q
    return {"model": JEV_MODEL, "state": {"snapshot": state["text"]}, "questions": questions}


def parse_answers(cell: dict[str, Any], reg: dict[str, Any], resp: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """(marker id -> {qid: value or None}, namespaced qid -> confidence/probabilities); missing answers are None."""
    ans = (resp or {}).get("answers") or {}
    out: dict[str, dict[str, Any]] = {}
    detail: dict[str, Any] = {}
    for mid in cell["markers"]:
        vals: dict[str, Any] = {}
        for qid, q in reg["marker"][mid]["spec"]["question"].items():
            a = ans.get(f"{mid}{SEP}{qid}")
            key = {"score": "score", "choice": "choice"}.get(q["type"])
            vals[qid] = a.get(key) if isinstance(a, dict) and key else (a if q["type"] == "noul" else None)
            if isinstance(a, dict) and key:
                detail[f"{mid}{SEP}{qid}"] = {k: a[k] for k in ("confidence", "probabilities") if k in a}
        out[mid] = vals
    return out, detail


def _unit_score(reg: dict[str, Any], mid: str, qid: str, v: Any) -> float | None:
    """0..1 present-ness for a score question, honouring polarity; None otherwise."""
    q = reg["marker"][mid]["spec"]["question"][qid]
    if q["type"] != "score" or not isinstance(v, (int, float)):
        return None
    n = len(q.get("criteria") or [])
    if n < 2:
        return None
    x = min(max(v, 0), n - 1) / (n - 1) if v >= 0 else None
    if x is None:
        return None
    return x if reg["marker"][mid]["spec"]["polarity"] == "higher_means_present" else 1 - x


def rows_for(cell: dict[str, Any], reg: dict[str, Any], state: dict[str, Any], resp: dict[str, Any] | None,
             est_cost: float, err: str | None, elapsed: float) -> list[dict[str, Any]]:
    parsed, detail = parse_answers(cell, reg, resp) if resp else ({}, {})
    usage = (resp or {}).get("usage")
    real = usage.get("cost_usd") if isinstance(usage, dict) else None
    per = (real if real is not None else est_cost) / max(1, len(cell["markers"]))
    rows = []
    for mid in cell["markers"]:
        vals = parsed.get(mid, {})
        ok = err is None and bool(vals) and all(v is not None for v in vals.values())
        qid0 = next(iter(reg["marker"][mid]["spec"]["question"]))
        rows.append({
            "cell_id": cell["cell_id"], "round": cell["round"], "panel": cell["panel"], "state": cell["state"],
            "marker": mid, "signal": reg["marker"][mid]["spec"]["signal"], "session": cell["session"],
            "split": cell["split"], "checkpoint": cell["checkpoint"], "answers": vals,
            "detail": {k: v for k, v in detail.items() if k.startswith(mid + SEP)},
            "score": _unit_score(reg, mid, qid0, vals.get(qid0)) if ok else None,
            "parse_ok": ok, "error": err, "cost_usd": per, "cost_estimated": real is None,
            "state_tokens": state["tokens_est"], "state_truncated": state["truncated"],
            "markers_in_call": len(cell["markers"]), "usage": usage, "elapsed_s": round(elapsed, 2),
        })
    return rows


def run(cells: list[dict[str, Any]], reg: dict[str, Any], corpus: dict[str, Any], ledger: Path, est_cost: float,
        poster: Callable[[dict[str, Any]], dict[str, Any]], concurrency: int = 4, dry_run: bool = False,
        limit: int | None = None) -> dict[str, Any]:
    cells = cells[:limit] if limit else cells
    ev_cache: dict[str, Any] = {}
    lock = threading.Lock()
    stats = {"calls": 0, "errors": 0, "cost_usd": 0.0}

    def events_for(sess: str) -> Any:
        with lock:
            if sess not in ev_cache:
                c = corpus[sess]
                ev_cache[sess] = load_events(c["harness"], c["path"])
            return ev_cache[sess]

    def one(cell: dict[str, Any]) -> None:
        try:
            _one(cell)
        except Exception as e:  # a bad cell must not abort a 10k batch
            with lock:
                stats["skipped"] = stats.get("skipped", 0) + 1
                print(f"skip {cell['cell_id']}: {type(e).__name__}: {e}", file=sys.stderr)

    def _one(cell: dict[str, Any]) -> None:
        spec = reg["state"][cell["state"]]["spec"]
        evs = events_for(cell["session"])
        if cell.get("hide_next_prompt"):  # labelled cells: the human prompt arriving at this checkpoint is the outcome, never state
            evs = [e for e in evs if not (e["kind"] == "user_prompt" and e["turn"] == cell["checkpoint"])]
        state = build_state(spec, evs, cell["checkpoint"])
        state["text"] = scrub(state["text"], len(state["text"]) + 1)  # redact secrets before anything leaves the machine
        req = build_request(cell, reg, state)
        if dry_run:
            print(json.dumps({"cell": cell["cell_id"], "state_tokens": state["tokens_est"], "questions": len(req["questions"])}))
            return
        t0, resp, err = time.time(), None, None
        try:
            resp = poster(req)
        except BaseException as e:  # SystemExit from the client included: record, keep the batch going
            err = f"{type(e).__name__}: {e}"[:300]
        rows = rows_for(cell, reg, state, resp, est_cost, err, time.time() - t0)
        with lock:
            with ledger.open("a") as f:
                f.write("".join(canonical(r) + "\n" for r in rows))
            stats["calls"] += 1
            stats["errors"] += err is not None
            stats["cost_usd"] += sum(r["cost_usd"] for r in rows)

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        list(ex.map(one, cells))
    stats["cost_usd"] = round(stats["cost_usd"], 5)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--round-file", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    reg, rnd, corpus = load_registry(root), json.loads(Path(a.round_file).read_text()), load_corpus(root)
    if corpus is None:
        print("corpus.json required under --root", file=sys.stderr)
        return 1
    errs = validate_registry(root) + validate_round(rnd, reg, corpus)
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    ledger = Path(a.ledger)
    res = expand(rnd, reg, {r["cell_id"] for r in read_ledger(ledger)}, corpus)
    if res["over_budget"]:
        print(f"over budget: {res['to_run']} cells, est ${res['est_cost_usd']}", file=sys.stderr)
        return 2
    from lib.jev_client import post_systemone
    stats = run(res["cells"], reg, corpus, ledger, rnd["est_cost_per_call_usd"], post_systemone,
                a.concurrency, a.dry_run, a.limit)
    print(json.dumps(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
