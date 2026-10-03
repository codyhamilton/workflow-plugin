"""Plan lifecycle on top of the quality ledger: designs, briefs, executions, findings, completion.

Every call carries a correlation context (repo, harness, workflow_version, model, conversation_id,
initiator, design_stage, execution_stage), stored on the artifact version, the execution and an
append-only events row, so ratings made up front can be joined to what execution actually cost.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import quality as q

INITIATORS = ("human", "bot", "agent", "unknown")
EXEC_OUTCOMES = ("done", "partial", "blocked", "abandoned")
ITEM_KINDS = ("finding", "adjustment", "gap")
CTX = ("harness", "workflow_version", "model", "conversation_id", "initiator_type", "initiator_id", "repo", "design_stage", "execution_stage")
COST = ("cost_usd", "tokens_in", "tokens_out", "turns", "tool_calls")


class Bad(ValueError):
    pass


def ctx_of(b: dict[str, Any]) -> dict[str, Any]:
    c = {k: b.get(k) for k in CTX}
    for k, v in (b.get("context") or {}).items():
        if k in CTX and c.get(k) is None:
            c[k] = v
    c["initiator_type"] = c["initiator_type"] or "unknown"
    if c["initiator_type"] not in INITIATORS:
        raise Bad(f"initiator_type must be one of {INITIATORS}")
    if not c["workflow_version"]:
        c["workflow_version"] = q.tag(Path("x"), Path("/nonexistent"), "", "")["plugin_version"]
    return c


def event(c, name: str, ctx: dict, artifact_id=None, execution_id=None, payload=None) -> None:
    c.execute("INSERT INTO events(ts,event,artifact_id,execution_id,harness,workflow_version,model,conversation_id,initiator_type,initiator_id,repo,design_stage,execution_stage,payload)"
              " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (time.time(), name, artifact_id, execution_id, *(ctx.get(k) for k in CTX), json.dumps(payload or {}, default=str)))


def _artifact(c, kind: str, aid: int):
    r = c.execute("SELECT * FROM artifacts WHERE id=? AND kind=?", (aid, kind)).fetchone()
    if not r:
        raise Bad(f"no {kind} with id {aid}")
    return r


def _latest(c, aid: int):
    return c.execute("SELECT * FROM scores WHERE artifact_id=? ORDER BY ts DESC, id DESC LIMIT 1", (aid,)).fetchone()


def _view(c, aid: int) -> dict[str, Any]:
    a = dict(c.execute("SELECT * FROM artifacts WHERE id=?", (aid,)).fetchone())
    s = _latest(c, aid)
    a["latest"] = {k: s[k] for k in ("sha", "ts", "composite", "composite_det", "jev_error", "registry", "model", "session_id")} if s else None
    a["executions"] = [r[0] for r in c.execute("SELECT id FROM executions WHERE brief_id=? ORDER BY id", (aid,))]
    return a


def put_artifact(kind: str, b: dict[str, Any], aid: int | None = None) -> dict[str, Any]:
    """POST (aid None, upsert by project+path) or PATCH (aid given) a design or brief."""
    ctx = ctx_of(b)
    text = b.get("text")
    with q.db() as c:
        if aid is not None:
            a = _artifact(c, kind, aid)
            project, path, plan, repo_path = a["project"], a["path"], a["plan"], b.get("repo_path") or a["repo_path"]
            ctx["repo"] = ctx["repo"] or repo_path
        else:
            if not text:
                raise Bad("text is required")
            repo_path = b.get("repo_path")
            project = b.get("project") or (q.project_name(Path(repo_path)) if repo_path else None)
            if not project:
                raise Bad("project or repo_path is required")
            plan = b.get("plan")
            path = b.get("path") or (f"docs/plans/{plan}/DESIGN.md" if kind == "design" and plan else
                                     f"docs/plans/{plan}/briefs/{b['name']}.md" if kind == "brief" and plan and b.get("name") else None)
            if not path:
                raise Bad("path (or plan, plus name for a brief) is required")
            plan = plan or (m.group(1) if (m := re.search(r"docs/plans/([^/]+)/", path)) else None)
            ctx["repo"] = ctx["repo"] or repo_path
    out: dict[str, Any] = {}
    if text:
        repo = Path(repo_path).expanduser() if repo_path else Path("/nonexistent-repo")
        full = repo / path if repo_path and not Path(path).is_absolute() else Path(path)
        sha = hashlib.sha256(text.encode()).hexdigest()[:16]
        with q.db() as c:
            have = c.execute("SELECT s.id FROM scores s JOIN artifacts a ON a.id=s.artifact_id WHERE a.kind=? AND a.project=? AND a.path=? AND s.sha=? AND s.registry=?"
                             " AND (? OR s.jev_error IS NULL)", (kind, project, path, sha, q.REG_VERSION, not b.get("use_jev", True))).fetchone()
        if not have:
            row = q.score_content(kind, text, full, repo, b.get("use_jev", True), True, ctx["harness"] or "api", ctx["conversation_id"] or "unknown",
                                  project=project, plan=plan, plugin_version=ctx["workflow_version"], model=ctx["model"],
                                  initiator_type=ctx["initiator_type"], initiator_id=ctx["initiator_id"])
            aid = row["artifact_id"]
            out = {"scored": True, "composite": row["composite"], "rating": row["rating"], "summary": q.summary(row), "jev_error": row["jev_error"]}
        else:
            with q.db() as c:
                aid = q.artifact_id(c, kind, project, path, plan, time.time())
            out = {"scored": False, "reason": "identical content already scored"}
    with q.db() as c:
        if aid is None:
            raise Bad("unreachable")
        c.execute("UPDATE scores SET repo=? WHERE id=(SELECT id FROM scores WHERE artifact_id=? ORDER BY ts DESC, id DESC LIMIT 1)", (repo_path, aid))
        if repo_path:
            c.execute("UPDATE artifacts SET repo_path=? WHERE id=?", (repo_path, aid))
        for col in ("design_stage", "execution_stage", "work_type"):
            if b.get(col):
                c.execute(f"UPDATE artifacts SET {col}=? WHERE id=?", (b[col], aid))
        if kind == "brief" and b.get("design_id"):
            _artifact(c, "design", int(b["design_id"]))
            c.execute("UPDATE artifacts SET parent_id=? WHERE id=?", (int(b["design_id"]), aid))
            c.execute("INSERT OR IGNORE INTO links(ts,from_artifact,to_artifact,type,evidence,source) VALUES(?,?,?,?,?,?)", (time.time(), aid, int(b["design_id"]), "derived_from", "design_id", "api"))
        if kind == "brief" and not b.get("work_type"):  # inherit the design's work type
            c.execute("UPDATE artifacts SET work_type=(SELECT d.work_type FROM artifacts d WHERE d.id=artifacts.parent_id) WHERE id=? AND work_type IS NULL", (aid,))
        event(c, f"{'patched' if b.get('_patch') else 'posted'}_{kind}", ctx, aid, None,
              {k: b[k] for k in ("work_type", "design_id") if b.get(k)} | {"scored": out.get("scored")})
        out["id"] = aid
        out["artifact"] = _view(c, aid)
    return out


def start_execution(brief_id: int, b: dict[str, Any]) -> dict[str, Any]:
    ctx = ctx_of(b)
    with q.db() as c:
        a = _artifact(c, "brief", brief_id)
        ctx["repo"] = ctx["repo"] or a["repo_path"]
        cur = c.execute("INSERT INTO executions(brief_id,started,status,harness,workflow_version,model,conversation_id,initiator_type,initiator_id,repo,head_start,design_stage,execution_stage)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (brief_id, time.time(), "running", *(ctx[k] for k in ("harness", "workflow_version", "model", "conversation_id", "initiator_type", "initiator_id", "repo")),
                                                              b.get("head") or (q._git(Path(ctx["repo"]), "rev-parse", "--short", "HEAD") if ctx["repo"] else None), ctx["design_stage"], ctx["execution_stage"] or "in_progress"))
        c.execute("UPDATE artifacts SET execution_stage=? WHERE id=?", (ctx["execution_stage"] or "in_progress", brief_id))
        event(c, "execution_started", ctx, brief_id, cur.lastrowid)
        return {"id": cur.lastrowid, "brief_id": brief_id}


def _items(c, eid: int, brief_id: int, items: list[dict], ctx: dict) -> int:
    n = 0
    for it in items:
        if it.get("kind") not in ITEM_KINDS or not str(it.get("text") or "").strip():
            raise Bad(f"each item needs kind in {ITEM_KINDS} and text")
        n += c.execute("INSERT OR IGNORE INTO findings(execution_id,brief_id,ts,kind,category,severity,text) VALUES(?,?,?,?,?,?,?)",
                       (eid, brief_id, time.time(), it["kind"], it.get("category"), it.get("severity"), it["text"].strip())).rowcount
        ev = hashlib.sha256(it["text"].encode()).hexdigest()[:12]
        cat = (it.get("category") or "").lower()
        typ = "missing_scope" if it["kind"] == "gap" else "defect" if cat == "defect" else "rework" if cat == "rework" else None
        if typ:  # back-reference to the brief, and to its design when the gap is design-level
            tos = [brief_id] + ([c.execute("SELECT parent_id FROM artifacts WHERE id=?", (brief_id,)).fetchone()[0]] if it.get("scope") == "design" else [])
            for to in filter(None, tos):
                c.execute("INSERT OR IGNORE INTO links(ts,from_artifact,to_artifact,type,note,evidence,source) VALUES(?,?,?,?,?,?,?)", (time.time(), None, to, typ, it["text"][:300], f"exec{eid}:{ev}", "api"))
    return n


def patch_execution(eid: int, b: dict[str, Any]) -> dict[str, Any]:
    ctx = ctx_of(b)
    with q.db() as c:
        e = c.execute("SELECT * FROM executions WHERE id=?", (eid,)).fetchone()
        if not e:
            raise Bad(f"no execution {eid}")
        ctx = {k: ctx[k] if ctx[k] not in (None, "unknown") else e[k] for k in CTX if k in e.keys()} | {k: ctx[k] for k in CTX if k not in e.keys()}
        n = _items(c, eid, e["brief_id"], b.get("items") or [], ctx)
        for k in COST:
            if b.get(k) is not None:
                c.execute(f"UPDATE executions SET {k}=? WHERE id=?", (b[k], eid))
        for k in ("model", "execution_stage", "design_stage"):
            if b.get(k):
                c.execute(f"UPDATE executions SET {k}=? WHERE id=?", (b[k], eid))
        if b.get("execution_stage"):
            c.execute("UPDATE artifacts SET execution_stage=? WHERE id=?", (b["execution_stage"], e["brief_id"]))
        event(c, "execution_patched", ctx, e["brief_id"], eid, {"items_added": n, **{k: b[k] for k in COST if b.get(k) is not None}})
        return {"id": eid, "items_added": n}


def complete_execution(eid: int, b: dict[str, Any]) -> dict[str, Any]:
    ctx = ctx_of(b)  # patch_execution fills gaps from the execution's own context
    if b.get("outcome") not in EXEC_OUTCOMES:
        raise Bad(f"outcome must be one of {EXEC_OUTCOMES}")
    out = patch_execution(eid, b)
    with q.db() as c:
        e = c.execute("SELECT * FROM executions WHERE id=?", (eid,)).fetchone()
        head = b.get("head") or (q._git(Path(e["repo"]), "rev-parse", "--short", "HEAD") if e["repo"] else None)
        c.execute("UPDATE executions SET ended=?,status='complete',outcome=?,summary=?,metrics=?,head_end=? WHERE id=?",
                  (time.time(), b["outcome"], b.get("summary"), json.dumps(b.get("metrics") or {}), head, eid))
        stage = {"done": "complete", "partial": "partial", "blocked": "blocked", "abandoned": "abandoned"}[b["outcome"]]
        c.execute("UPDATE artifacts SET execution_stage=? WHERE id=?", (stage, e["brief_id"]))
        ectx = {k: (e[k] if e[k] is not None else ctx.get(k)) for k in CTX}
        event(c, "execution_completed", ectx, e["brief_id"], eid, {"outcome": b["outcome"]})
    return out | {"outcome": b["outcome"], "brief": outcome_row(eid)}


def outcome_row(eid: int) -> dict[str, Any]:
    with q.db() as c:
        e = c.execute("SELECT * FROM executions WHERE id=?", (eid,)).fetchone()
        counts = {r[0]: r[1] for r in c.execute("SELECT kind,count(*) FROM findings WHERE execution_id=? GROUP BY kind", (eid,))}
        s = _latest(c, e["brief_id"])
        return {"execution": eid, "brief": e["brief_id"], "outcome": e["outcome"], "composite": s["composite"] if s else None,
                "cost_usd": e["cost_usd"], "findings": counts.get("finding", 0), "adjustments": counts.get("adjustment", 0), "gaps": counts.get("gap", 0)}


def get(kind: str, i: int) -> dict[str, Any]:
    with q.db() as c:
        if kind == "execution":
            e = c.execute("SELECT * FROM executions WHERE id=?", (i,)).fetchone()
            if not e:
                raise Bad(f"no execution {i}")
            return dict(e) | {"items": [dict(r) for r in c.execute("SELECT kind,category,severity,text FROM findings WHERE execution_id=? ORDER BY id", (i,))]}
        _artifact(c, kind, i)
        return _view(c, i)


SLICES = {"project": "a.project", "repo": "COALESCE(a.repo_path,a.project)", "work_type": "a.work_type", "initiator": "e.initiator_type", "model": "e.model",
          "harness": "e.harness", "workflow_version": "e.workflow_version", "plan": "a.plan", "design_stage": "e.design_stage"}


def outcomes(by: str = "project") -> list[dict[str, Any]]:
    """Up-front brief rating joined to realised execution, grouped by a slice (one row per execution, latest brief score)."""
    if by not in SLICES:
        raise Bad(f"by must be one of {sorted(SLICES)}")
    sql = f"""SELECT {SLICES[by]} AS grp, count(*) AS executions, avg(s.composite) AS rating,
        avg(e.outcome='done') AS done_rate, sum(e.cost_usd) AS cost_usd, avg(e.cost_usd) AS cost_per_exec,
        avg((SELECT count(*) FROM findings f WHERE f.execution_id=e.id AND f.kind='gap')) AS gaps,
        avg((SELECT count(*) FROM findings f WHERE f.execution_id=e.id AND f.kind='adjustment')) AS adjustments
      FROM executions e JOIN artifacts a ON a.id=e.brief_id
      LEFT JOIN scores s ON s.id=(SELECT id FROM scores WHERE artifact_id=a.id ORDER BY ts DESC, id DESC LIMIT 1)
      GROUP BY grp ORDER BY executions DESC"""
    with q.db() as c:
        return [dict(r) for r in c.execute(sql)]


def plan_cost(project: str, plan: str) -> dict[str, Any]:
    """Map a plan to its realised cost: design rating, each brief's rating and executions, totals."""
    with q.db() as c:
        briefs = []
        for a in c.execute("SELECT id,path FROM artifacts WHERE kind='brief' AND project=? AND plan=? ORDER BY path", (project, plan)):
            ex = c.execute("SELECT count(*), sum(cost_usd), sum(tokens_in), sum(tokens_out), sum(turns), sum(outcome='done') FROM executions WHERE brief_id=?", (a["id"],)).fetchone()
            s = _latest(c, a["id"])
            briefs.append({"id": a["id"], "path": a["path"], "rating": s["composite"] if s else None, "executions": ex[0], "cost_usd": ex[1], "tokens_in": ex[2], "tokens_out": ex[3], "turns": ex[4], "done": ex[5]})
        d = c.execute("SELECT id FROM artifacts WHERE kind='design' AND project=? AND plan=?", (project, plan)).fetchone()
        ds = _latest(c, d["id"]) if d else None
        return {"project": project, "plan": plan, "design_rating": ds["composite"] if ds else None, "briefs": briefs,
                "total_cost_usd": sum(b["cost_usd"] or 0 for b in briefs), "total_executions": sum(b["executions"] for b in briefs)}
