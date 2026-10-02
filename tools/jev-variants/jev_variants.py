#!/usr/bin/env python3
"""Variant registry, validator and matrix expander for the Jev Stage A search.

Three independently authored axes (signal, state, marker) live as JSON files in a
registry root. A round names a subset of each axis plus sessions and checkpoints;
`expand` turns it into a deterministic, budget-bounded list of cells.

Subcommands: new, validate, expand, digest.  Stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "transcript"))
from lib.jev_client import validate_systemone_questions  # noqa: E402

KINDS = ("signal", "state", "marker", "panel")
DIRS = {"signal": "signals", "state": "states", "marker": "markers", "panel": "panels"}
PREFIX = {"signal": "sig", "state": "st", "marker": "mk", "panel": "pn"}
MAX_PANEL_MARKERS = 16  # live probe: 1/8/16/32 questions per call all answered; 16 is a conservative cap
STATUSES = {"proposed", "active", "retired"}

# Vocabulary shared by signals (what they need) and states (what they provide).
FEATURES = {
    "user_prompts", "tool_names", "tool_args", "tool_output_text",
    "assistant_text", "turn_index", "context_size", "repeat_counts", "file_targets",
}
DIRECTIONS = {"near_completion", "productive_continuation", "low_value_continuation"}
STATE_SOURCES = {"transcript_prefix", "hook_events"}
PROMPT_MODES = {"none", "first", "last_k", "all"}
IO_MODES = {"none", "truncated", "full"}
COUNTERS = {"turn_index", "tool_calls", "distinct_files", "repeat_targets", "prompt_count", "tokens_est"}
SPLITS = {"discovery", "dev", "heldout"}


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def spec_hash(spec: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(spec).encode()).hexdigest()[:10]


def variant_id(kind: str, spec: dict[str, Any]) -> str:
    return f"{PREFIX[kind]}-{spec_hash(spec)}"


def state_provides(spec: dict[str, Any]) -> set[str]:
    p: set[str] = set()
    if spec.get("user_prompts", "none") != "none":
        p.add("user_prompts")
    if spec.get("tool_inputs", "none") in {"names", "truncated", "full"}:
        p.add("tool_names")
    if spec.get("tool_inputs", "none") in {"truncated", "full"}:
        p.update({"tool_args", "file_targets"})
    if spec.get("tool_outputs", "none") != "none":
        p.add("tool_output_text")
    if spec.get("assistant_text", "none") != "none":
        p.add("assistant_text")
    for c in spec.get("counters", []):
        p.add({"turn_index": "turn_index", "tokens_est": "context_size",
               "repeat_targets": "repeat_counts", "distinct_files": "file_targets"}.get(c, "tool_names"))
    return p


# ---- validation -----------------------------------------------------------

def _need(cond: bool, msg: str, errs: list[str]) -> None:
    if not cond:
        errs.append(msg)


def validate_spec(kind: str, spec: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if kind == "signal":
        for k in ("name", "claim", "anchor"):
            _need(isinstance(spec.get(k), str) and spec[k].strip(), f"signal spec.{k} required", e)
        _need(spec.get("direction") in DIRECTIONS, f"direction must be one of {sorted(DIRECTIONS)}", e)
        _need(isinstance(spec.get("counterexamples"), list) and len(spec["counterexamples"]) >= 1,
              "at least one counterexample required", e)
        _need("zero_call_detector" in spec,
              "zero_call_detector required (a cheap rule description, or null if none exists)", e)
        req = spec.get("requires_features")
        _need(isinstance(req, list) and req and set(req) <= FEATURES,
              f"requires_features must be a non-empty subset of {sorted(FEATURES)}", e)
    elif kind == "state":
        _need(spec.get("source") in STATE_SOURCES, f"source must be one of {sorted(STATE_SOURCES)}", e)
        _need(spec.get("user_prompts", "none") in PROMPT_MODES, f"user_prompts in {sorted(PROMPT_MODES)}", e)
        if spec.get("user_prompts") == "last_k":
            _need(isinstance(spec.get("user_prompts_k"), int) and spec["user_prompts_k"] > 0, "user_prompts_k required", e)
        for k in ("tool_inputs", "tool_outputs", "assistant_text"):
            _need(spec.get(k, "none") in IO_MODES | ({"names"} if k == "tool_inputs" else set()),
                  f"{k} invalid", e)
        w = spec.get("window")
        _need(isinstance(w, dict) and (w.get("unit") in {"turns", "batches", "all"}), "window.unit in turns|batches|all", e)
        if isinstance(w, dict) and w.get("unit") != "all":
            _need(isinstance(w.get("n"), int) and w["n"] > 0, "window.n positive int required", e)
        if "truncate_chars" in spec:
            _need(isinstance(spec["truncate_chars"], int) and spec["truncate_chars"] > 0, "truncate_chars positive int", e)
        _need(set(spec.get("counters", [])) <= COUNTERS, f"counters subset of {sorted(COUNTERS)}", e)
        _need(isinstance(spec.get("max_tokens"), int) and spec["max_tokens"] > 0, "max_tokens required (hard cap)", e)
        if spec.get("source") == "hook_events":
            _need(spec.get("assistant_text", "none") == "none",
                  "hook_events carry no assistant text; use transcript_prefix", e)
    elif kind == "marker":
        _need(isinstance(spec.get("signal"), str), "marker.signal (signal id) required", e)
        _need(spec.get("polarity") in {"higher_means_present", "higher_means_absent"}, "polarity required", e)
        q = spec.get("question")
        if not isinstance(q, dict) or not q:
            e.append("marker.question must be a non-empty questions object")
        else:
            try:
                validate_systemone_questions(q)
            except ValueError as ex:
                e.append(f"jev question shape: {ex}")
            for qid, qs in q.items():
                _need(isinstance(qs, dict) and str(qs.get("instructions", "")).strip(),
                      f"question '{qid}' needs instructions", e)
    elif kind == "panel":
        _need(isinstance(spec.get("name"), str) and spec["name"].strip(), "panel spec.name required", e)
        ms = spec.get("markers")
        _need(isinstance(ms, list) and 1 <= len(ms) <= MAX_PANEL_MARKERS and len(set(ms)) == len(ms),
              f"panel.markers must be 1..{MAX_PANEL_MARKERS} distinct marker ids", e)
    return e


def load_registry(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    reg: dict[str, dict[str, dict[str, Any]]] = {k: {} for k in KINDS}
    for kind in KINDS:
        d = root / DIRS[kind]
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            reg[kind][f.stem] = json.loads(f.read_text())
    return reg


def validate_registry(root: Path) -> list[str]:
    errs: list[str] = []
    reg = load_registry(root)
    seen: dict[tuple[str, str], str] = {}
    for kind in KINDS:
        for vid, v in reg[kind].items():
            p = f"{DIRS[kind]}/{vid}.json"
            if v.get("kind") != kind:
                errs.append(f"{p}: kind must be '{kind}'")
                continue
            spec = v.get("spec")
            if not isinstance(spec, dict):
                errs.append(f"{p}: spec missing")
                continue
            if vid != variant_id(kind, spec):
                errs.append(f"{p}: id/filename must equal {variant_id(kind, spec)} (content hash of spec; edit => new variant)")
            dup = seen.get((kind, spec_hash(spec)))
            if dup:
                errs.append(f"{p}: duplicate spec of {dup}")
            seen[(kind, spec_hash(spec))] = p
            for k in ("author", "round_proposed", "rationale", "informed_by"):
                if not v.get(k):
                    errs.append(f"{p}: {k} required (lineage)")
            if v.get("status") not in STATUSES:
                errs.append(f"{p}: status in {sorted(STATUSES)}")
            if v.get("parent") and v["parent"] not in reg[kind]:
                errs.append(f"{p}: parent {v['parent']} not in registry")
            errs += [f"{p}: {m}" for m in validate_spec(kind, spec)]
            if kind == "marker" and spec.get("signal") not in reg["signal"]:
                errs.append(f"{p}: signal {spec.get('signal')} not in registry")
            if kind == "panel":
                sigs = []
                for mid in spec.get("markers", []):
                    if mid not in reg["marker"]:
                        errs.append(f"{p}: marker {mid} not in registry")
                    else:
                        sigs.append(reg["marker"][mid]["spec"]["signal"])
                if len(set(sigs)) != len(sigs):
                    errs.append(f"{p}: a panel holds at most one marker per signal (wording variants are separate panels)")
    return errs


# ---- rounds ---------------------------------------------------------------

def validate_round(rnd: dict[str, Any], reg: dict[str, Any], corpus: dict[str, Any] | None = None) -> list[str]:
    e: list[str] = []
    for k in ("round", "stage", "test_card", "panels", "states", "sessions",
              "checkpoints", "max_calls", "max_cost_usd", "est_cost_per_call_usd", "learned_from"):
        _need(k in rnd, f"round.{k} required", e)
    if e:
        return e
    _need(rnd["stage"] == "A", "only stage A rounds are supported", e)
    for kind, key in (("panel", "panels"), ("state", "states")):
        for vid in rnd[key]:
            _need(vid in reg[kind], f"{key}: {vid} not in registry", e)
            if vid in reg[kind]:
                _need(reg[kind][vid]["status"] != "retired", f"{key}: {vid} is retired", e)
    _need(isinstance(rnd["sessions"], dict) and rnd["sessions"], "sessions must map session_id -> split", e)
    if isinstance(rnd["sessions"], dict):
        for sid, sp in rnd["sessions"].items():
            _need(sp in SPLITS, f"session {sid}: split must be one of {sorted(SPLITS)}", e)
        for sid in rnd["sessions"]:
            info = (corpus or {}).get(sid)
            if corpus is not None:
                _need(info is not None, f"session {sid} not in corpus.json", e)
                if info:
                    _need(info["split"] == rnd["sessions"][sid], f"session {sid}: round says {rnd['sessions'][sid]}, corpus says {info['split']}", e)
    if rnd.get("allow_heldout") is not True:
        held = [s for s, sp in rnd.get("sessions", {}).items() if sp == "heldout"]
        _need(not held, f"heldout sessions {held[:3]} in a tuning round; held-out is sealed (set allow_heldout only for the one confirmatory replay)", e)
    return e


def load_corpus(root: Path) -> dict[str, Any] | None:
    f = root / "corpus.json"
    return json.loads(f.read_text()) if f.exists() else None


def harness_features(harness: str | None) -> set[str]:
    from events import HARNESS_FEATURES
    return set(HARNESS_FEATURES.get(harness or "", FEATURES))


def expand(rnd: dict[str, Any], reg: dict[str, Any], done: set[str], corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cell = (panel, state, session, checkpoint). Markers whose signal cannot be answered from the
    state (or from what the session's harness records) are dropped from that cell, not the whole panel."""
    cells: list[dict[str, Any]] = []
    dropped: dict[str, int] = {}
    for pid in rnd["panels"]:
        mids = reg["panel"][pid]["spec"]["markers"]
        for stid in rnd["states"]:
            prov = state_provides(reg["state"][stid]["spec"])
            for sess in sorted(rnd["sessions"]):
                have = prov & harness_features((corpus or {}).get(sess, {}).get("harness"))
                use = []
                for mid in mids:
                    sig = reg["marker"][mid]["spec"]["signal"]
                    miss = set(reg["signal"][sig]["spec"]["requires_features"]) - have
                    if miss:
                        key = f"{sig}|{stid}|{sess}: missing {','.join(sorted(miss))}"
                        dropped[key] = dropped.get(key, 0) + 1
                    else:
                        use.append(mid)
                if not use:
                    continue
                cps = rnd.get("session_checkpoints", {}).get(sess) if rnd.get("session_checkpoints") else rnd["checkpoints"]
                for cp in cps or []:
                    cell_id = hashlib.sha256(f"{pid}|{stid}|{','.join(use)}|{sess}|{cp}".encode()).hexdigest()[:12]
                    cells.append({"cell_id": cell_id, "round": rnd["round"], "panel": pid, "state": stid, "markers": use,
                                  "session": sess, "split": rnd["sessions"][sess], "checkpoint": cp,
                                  **({"hide_next_prompt": True} if rnd.get("hide_next_prompt") else {})})
    todo = [c for c in cells if c["cell_id"] not in done]
    est = len(todo) * rnd["est_cost_per_call_usd"]
    over = len(todo) > rnd["max_calls"] or est > rnd["max_cost_usd"]
    return {"total": len(cells), "already_done": len(cells) - len(todo), "to_run": len(todo),
            "est_cost_usd": round(est, 4), "over_budget": over,
            "independent_sessions": len(rnd["sessions"]),
            "markers_dropped_incompatible": len(dropped), "dropped_examples": list(dropped)[:5],
            "cells": [] if over else todo}


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


# ---- digest ---------------------------------------------------------------

def digest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-axis roll-up. Rows need cell_id/signal/state/marker/session/split plus parse_ok, cost_usd, state_tokens.
    Optional `label` (bool, independent presence label) and `score` (0..1, present-ness) give agreement stats."""
    out: dict[str, Any] = {}
    for axis in ("signal", "state", "marker", "panel"):
        g: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            g.setdefault(r.get(axis, "-"), []).append(r)
        summary = {}
        for vid, rs in sorted(g.items()):
            lab = [r for r in rs if r.get("label") is not None and r.get("score") is not None and r.get("parse_ok")]
            acc = None
            if lab:
                acc = round(sum((r["score"] >= 0.5) == bool(r["label"]) for r in lab) / len(lab), 3)
            summary[vid] = {
                "cells": len(rs), "sessions": len({r["session"] for r in rs}),
                "parse_fail_rate": round(sum(not r.get("parse_ok", False) for r in rs) / len(rs), 3),
                "mean_cost_usd": round(sum(r.get("cost_usd", 0) for r in rs) / len(rs), 5),
                "mean_state_tokens": round(sum(r.get("state_tokens", 0) for r in rs) / len(rs)),
                "labelled": len(lab), "label_agreement_at_0.5": acc,
                "note": "correlated trials; sessions is the evidence denominator",
            }
        out[axis] = summary
    return out



# ---- templates, near-duplicate guard, agent briefs ------------------------

EXAMPLES: dict[str, dict[str, Any]] = {
    "signal": {
        "name": "last-test-run-green",
        "claim": "The most recent test/verify command in the window succeeded after the latest edits.",
        "anchor": "A tool result for a test or build command whose output reports passing/zero failures, with no edit after it.",
        "direction": "near_completion",
        "counterexamples": ["Tests pass but the user's latest prompt asks for another feature.",
                            "Green run is of a different package than the one being changed."],
        "zero_call_detector": "regex for pass summary in the last test-command output",
        "requires_features": ["tool_output_text", "tool_names"],
    },
    "state": {
        "source": "hook_events",
        "window": {"unit": "batches", "n": 5},
        "user_prompts": "all",
        "tool_inputs": "names",
        "tool_outputs": "truncated",
        "truncate_chars": 300,
        "counters": ["turn_index", "tool_calls"],
        "max_tokens": 2000,
    },
    "marker": {
        "signal": "<signal id, e.g. sig-0123456789>",
        "polarity": "higher_means_present",
        "question": {"present": {
            "type": "score",
            "instructions": "Using only the state, did the most recent test or verify command succeed with no later edits?",
            "criteria": ["No: failed, absent, or edited after", "Unclear", "Probably yes", "Clearly yes, quote the evidence"]}},
    },
}

NEAR_DUP = 0.8


def _tokens(text: str) -> set[str]:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(w) > 2}


def _text_of(kind: str, spec: dict[str, Any]) -> str:
    if kind == "signal":
        return f"{spec.get('name','')} {spec.get('claim','')} {spec.get('anchor','')}"
    if kind == "marker":
        return " ".join(f"{q.get('instructions','')} {' '.join(map(str, q.get('criteria', [])))}"
                        for q in spec.get("question", {}).values())
    return ""


def near_duplicate(kind: str, spec: dict[str, Any], reg: dict[str, Any]) -> str | None:
    """States are parametric (exact-hash dedupe suffices); signals and markers compare wording."""
    if kind == "state":
        return None
    mine = _tokens(_text_of(kind, spec))
    for vid, v in reg[kind].items():
        if kind == "marker" and v["spec"].get("signal") != spec.get("signal"):
            continue
        other = _tokens(_text_of(kind, v["spec"]))
        if mine and other and len(mine & other) / len(mine | other) >= NEAR_DUP:
            return vid
    return None


ROLE_RULES = {
    "signal-proposer": "Propose signals only from the discovery sessions listed below. Every signal needs a real counterexample you saw. "
    "Signals run together in one panel, so propose DISTINCT, observable agent-activity phases (e.g. unit tests just run, agent investigating/reading, agent writing the main implementation, agent stuck repeating a failing step), not variations of one idea.",
    "state-designer": "Change ONE dimension from an existing state per variant (window, truncation, prompt mode, counters). Never invent fields.",
    "marker-writer": "Write wording for the ONE signal below. Use clearly different wording families, not paraphrases. Ask whether the signal is present, never whether to stop.",
}


def brief(role: str, root: Path, n: int, sessions: list[str], signal: str | None, author: str, rnd: str) -> str:
    kind = {"signal-proposer": "signal", "state-designer": "state", "marker-writer": "marker"}[role]
    reg = load_registry(root)
    existing = "\n".join(f"- {vid}: {_text_of(kind, v['spec'])[:110] or canonical(v['spec'])[:110]}"
                         for vid, v in reg[kind].items()
                         if kind != "marker" or v["spec"].get("signal") == signal) or "(none yet)"
    ex = json.loads(canonical(EXAMPLES[kind]))
    if kind == "marker" and signal:
        ex["signal"] = signal
    enums = {"direction": sorted(DIRECTIONS), "features": sorted(FEATURES), "counters": sorted(COUNTERS),
             "prompt_modes": sorted(PROMPT_MODES), "io_modes": sorted(IO_MODES), "polarity": ["higher_means_present", "higher_means_absent"],
             "jev_question_types": ["score (criteria = list of level strings)", "choice (criteria = map)", "noul"]}
    scope = f"Discovery sessions you may read: {', '.join(sessions) or '(none given)'}. Do not read any other session.\n" if kind == "signal" else ""
    return f"""# Task: author {n} new `{kind}` variants ({role})

{ROLE_RULES[role]}
{scope}
Existing {kind} variants (do not duplicate; near-duplicate wording is rejected):
{existing}

## Spec shape (example, copy the structure)
```json
{json.dumps(ex, indent=2)}
```
Allowed values: {json.dumps(enums)}

## For each variant
1. Write the spec JSON to a scratch file.
2. `--informed-by` takes only: a discovery session you read{' (listed above)' if kind == 'signal' else ''}, an existing variant id from the list above, or `digest:<name>`. Nothing else is accepted. `--parent` is required whenever a similar {kind} exists.
3. Run:
   python3 tools/jev-variants/jev_variants.py new {kind} --root {root} --spec <file> --author {author} --round {rnd} \
     --rationale "<why, 1-2 sentences>" --informed-by <ids you actually used> --parent <nearest existing {kind} id>
4. If it prints an error, fix the spec and rerun (max 3 tries per variant, then skip it). The tool prints the new id on success.
Stop after {n} variants are registered. Then run `... validate --root {root}` and report the ids, one line each.
Do not edit existing variant files. Do not run Jev. Do not write anywhere except the registry via the `new` command.
"""


# ---- CLI ------------------------------------------------------------------

def check_provenance(kind: str, root: Path, informed_by: list[str], parent: str | None, reg: dict[str, Any],
                     signal: str | None = None) -> list[str]:
    """informed_by must name things that exist: registry ids, digest:/human: tags, or listed discovery sessions."""
    e: list[str] = []
    disc_file = root / "discovery_sessions.txt"
    disc = set(disc_file.read_text().split()) if disc_file.exists() else set()
    all_ids = {vid for k in KINDS for vid in reg[k]}
    for ref in informed_by:
        if ref in all_ids or ref.startswith(("digest:", "human:")) or ref == "seed" or ref in disc:
            continue
        e.append(f"--informed-by '{ref}' is not a registry id, a discovery session in {disc_file.name}, "
                 "or a digest:/human: tag. Cite only what you actually used.")
    if kind == "signal" and not (set(informed_by) & disc) and disc:
        e.append("a signal must cite at least one discovery session from discovery_sessions.txt")
    if parent and parent not in reg[kind]:
        e.append(f"--parent {parent} is not an existing {kind} id")
    peers = [v for v in reg[kind].values()
             if kind == "state" or v["spec"].get("signal") == signal]
    if kind in ("state", "marker") and peers and not parent:
        e.append(f"--parent <existing {kind} id> is required: say which variant this one derives from "
                 "(pick the nearest one)")
    return e


def cmd_new(a: argparse.Namespace) -> int:
    spec = json.loads(Path(a.spec).read_text())
    errs = validate_spec(a.kind, spec)
    errs += check_provenance(a.kind, Path(a.root), a.informed_by, a.parent, load_registry(Path(a.root)),
                             spec.get("signal"))
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    if not a.allow_near_dup:
        dup = near_duplicate(a.kind, spec, load_registry(Path(a.root)))
        if dup:
            print(f"near-duplicate of {dup} (wording overlap >= {NEAR_DUP}); make it substantively different "
                  "or pass --allow-near-dup with a rationale", file=sys.stderr)
            return 1
    vid = variant_id(a.kind, spec)
    env = {"kind": a.kind, "id": vid, "parent": a.parent, "author": a.author, "round_proposed": a.round,
           "rationale": a.rationale, "informed_by": a.informed_by, "status": "proposed", "spec": spec}
    d = Path(a.root) / DIRS[a.kind]
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{vid}.json"
    if f.exists():
        print(f"duplicate: {f} already exists", file=sys.stderr)
        return 1
    f.write_text(json.dumps(env, indent=2, ensure_ascii=False) + "\n")
    print(vid)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="register a variant from a spec JSON file (computes content-hash id)")
    n.add_argument("kind", choices=KINDS)
    n.add_argument("--root", required=True)
    n.add_argument("--spec", required=True)
    n.add_argument("--author", required=True)
    n.add_argument("--round", required=True)
    n.add_argument("--rationale", required=True)
    n.add_argument("--informed-by", nargs="+", required=True, help="discovery session ids or prior result ids")
    n.add_argument("--parent")
    n.add_argument("--allow-near-dup", action="store_true")
    t = sub.add_parser("template", help="print an example spec for a kind")
    t.add_argument("kind", choices=KINDS)
    b = sub.add_parser("brief", help="print a self-contained prompt for a variant-authoring agent")
    b.add_argument("role", choices=sorted(ROLE_RULES))
    b.add_argument("--root", required=True)
    b.add_argument("--n", type=int, default=5)
    b.add_argument("--sessions", nargs="*", default=[], help="discovery session ids (signal-proposer)")
    b.add_argument("--signal", help="signal id (marker-writer)")
    b.add_argument("--author", default="flash-agent")
    b.add_argument("--round", required=True)
    v = sub.add_parser("validate", help="validate every variant file under root")
    v.add_argument("--root", required=True)
    x = sub.add_parser("expand", help="expand a round file into cells (budget-checked, resumable)")
    x.add_argument("--root", required=True)
    x.add_argument("--round-file", required=True)
    x.add_argument("--ledger")
    x.add_argument("--out")
    d = sub.add_parser("digest", help="per-axis roll-up of a results ledger (jsonl)")
    d.add_argument("--ledger", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "new":
        return cmd_new(a)
    if a.cmd == "template":
        print(json.dumps(EXAMPLES[a.kind], indent=2))
        return 0
    if a.cmd == "brief":
        if a.role == "marker-writer" and not a.signal:
            print("marker-writer needs --signal", file=sys.stderr)
            return 1
        print(brief(a.role, Path(a.root), a.n, a.sessions, a.signal, a.author, a.round))
        return 0
    if a.cmd == "validate":
        errs = validate_registry(Path(a.root))
        print("\n".join(errs) if errs else "ok")
        return 1 if errs else 0
    if a.cmd == "expand":
        root = Path(a.root)
        errs = validate_registry(root)
        reg = load_registry(root)
        rnd = json.loads(Path(a.round_file).read_text())
        corpus = load_corpus(root)
        errs += validate_round(rnd, reg, corpus)
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        done = {r["cell_id"] for r in read_ledger(Path(a.ledger))} if a.ledger else set()
        res = expand(rnd, reg, done, corpus)
        if a.out and not res["over_budget"]:
            Path(a.out).write_text("".join(canonical(c) + "\n" for c in res["cells"]))
        res.pop("cells")
        print(json.dumps(res, indent=2))
        return 2 if res["over_budget"] else 0
    if a.cmd == "digest":
        print(json.dumps(digest(read_ledger(Path(a.ledger))), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
