import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

os.environ["WORKFLOW_QUALITY_DIR"] = tempfile.mkdtemp()
os.environ.pop("TYPESAFE_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import quality as q  # noqa: E402
import server  # noqa: E402

BRIEF = "# Brief\n\n## Goal\nShip the thing.\n\n## Done when\n- `pytest` passes\n"


class T(unittest.TestCase):
    def test_score_logs_idempotently(self):
        p = Path("docs/plans/p1/briefs/01.md")
        a = q.score_content("brief", BRIEF, p, Path("/nonexistent-repo"), False, True, project="proj", plan="p1")
        q.score_content("brief", BRIEF, p, Path("/nonexistent-repo"), False, True, project="proj", plan="p1")
        self.assertEqual(a["project"], "proj")
        self.assertEqual(len([r for r in q.rows("brief") if r["project"] == "proj"]), 1)
        self.assertTrue(all(0 <= c["score"] <= 1 for c in a["criteria"].values()))

    def test_link_back_reference(self):
        q.score_content("brief", BRIEF, Path("docs/plans/p2/briefs/01.md"), Path("/x"), False, True, project="proj2")
        self.assertEqual(q.cmd_link(None, "docs/plans/p2/briefs/01.md", "defect", "n", ""), 0)

    def test_mcp_roundtrip(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), server.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        def rpc(m, p=None):
            r = urllib.request.Request(f"http://127.0.0.1:{srv.server_port}/mcp", json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p or {}}).encode())
            return json.load(urllib.request.urlopen(r))["result"]
        self.assertIn("post_brief", [t["name"] for t in rpc("tools/list")["tools"]])
        out = rpc("tools/call", {"name": "rate_artifact", "arguments": {"kind": "brief", "text": BRIEF, "project": "svc", "plan": "p", "use_jev": False}})
        self.assertNotIn("isError", out)
        self.assertIn("[workflow quality", out["content"][0]["text"])
        bad = rpc("tools/call", {"name": "rate_artifact", "arguments": {"kind": "other", "text": "x"}})
        self.assertTrue(bad["isError"])
        srv.shutdown()

    def test_frontmatter_ids_and_breakdown(self):
        import lifecycle as lc
        fm, body = q.split_frontmatter("---\ndesign_id: 7\n---\n# D\n")
        self.assertEqual((fm, body), ({"design_id": "7"}, "# D\n"))
        d = lc.put_artifact("design", {"text": "# D\n\n## Intent\n> x\n", "project": "fm", "plan": "p0", "use_jev": False})
        self.assertIn(f"design_id: {d['id']}", d["frontmatter"])
        self.assertFalse(d["baseline"]["enough_history"]); self.assertIn("not enough history", d["summary"])
        # a file carrying its id patches the same artifact, and frontmatter does not change the hash
        again = lc.put_artifact("design", {"text": d["frontmatter"] + "# D\n\n## Intent\n> x\n", "project": "fm", "plan": "p0", "use_jev": False})
        self.assertEqual(again["id"], d["id"]); self.assertFalse(again["scored"])
        for i in range(1, 7):
            lc.put_artifact("design", {"text": "# D\n\n## Intent\n> x\n" + "\n## Domains\n" * (i % 3) + f"filler {i}\n", "project": "fm", "plan": f"p{i}", "use_jev": False})
        last = lc.put_artifact("design", {"text": "# D\n\n## Intent\n> x\nmore\n", "project": "fm", "plan": "px", "use_jev": False})
        self.assertTrue(last["baseline"]["enough_history"]); self.assertIn("vs repo:fm mean", last["summary"])
        self.assertIn("repo_mean", next(iter(last["breakdown"].values())))
        b = lc.put_artifact("brief", {"text": f"---\ndesign_id: {d['id']}\n---\n" + BRIEF, "project": "fm", "plan": "p0", "name": "01", "use_jev": False})
        self.assertEqual(b["artifact"]["parent_id"], d["id"]); self.assertIn(f"design_id: {d['id']}", b["frontmatter"])

    def test_hook_events_ingest_and_join(self):
        import hookevents as he
        import lifecycle as lc
        sid = "conv-hook-1"
        b = lc.put_artifact("brief", {"text": BRIEF, "project": "hk", "plan": "ph", "path": "docs/plans/ph/briefs/01.md", "use_jev": False, "conversation_id": sid, "harness": "claude"})
        ex = lc.start_execution(b["id"], {"conversation_id": sid, "harness": "claude"})
        t0 = __import__("time").time()
        rows = [{"v": 1, "ts": t0 + 0.001, "harness": "claude", "session_id": sid, "hook_event": "UserPromptSubmit", "kind": "user_prompt", "text": "go api_key=abcdefgh12345678"},
                {"v": 1, "ts": t0 + 0.002, "harness": "claude", "session_id": sid, "hook_event": "PostToolUse", "kind": "tool_call", "tool_name": "Bash", "input": {"command": "ls"}, "ok": False},
                {"v": 1, "ts": t0 + 0.003, "harness": "claude", "session_id": sid, "hook_event": "PostToolUse", "kind": "tool_call", "tool_name": "Edit", "input": {}, "ok": True},
                {"kind": "bogus"}]
        self.assertEqual(he.ingest(rows), {"inserted": 3, "duplicate": 0, "rejected": 1})
        self.assertEqual(he.ingest(rows[:3])["duplicate"], 3)
        self.assertEqual(he.post({"harness": "claude", "payload": {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "again"}})["inserted"], 1)
        self.assertTrue(any("[REDACTED]" in e["text"] for e in he.events(sid, "user_prompt")))
        s = he.session(sid)
        self.assertEqual((s["activity"]["prompts"], s["activity"]["tools"], s["activity"]["tool_failures"]), (2, 2, 1))
        self.assertEqual([a["id"] for a in s["artifacts"]], [b["id"]])
        self.assertEqual(s["executions"][0]["id"], ex["id"])
        self.assertEqual(he.execution_activity(ex["id"])["activity"]["tools"], 2)
        self.assertEqual([x["session_id"] for x in he.plan_sessions("hk", "ph")["sessions"]], [sid])

    def test_hook_calls_bind_conversation_to_plan(self):
        """No conversation_id passed to the service: the hook row for the service call binds it."""
        import hookevents as he
        import lifecycle as lc
        sid, t0 = "conv-bound-1", __import__("time").time()
        b = lc.put_artifact("brief", {"text": BRIEF, "project": "bd", "plan": "pb", "path": "docs/plans/pb/briefs/01.md", "use_jev": False})
        ex = lc.start_execution(b["id"], {})
        mcp = {"v": 1, "ts": t0 + 0.001, "harness": "claude", "session_id": sid, "kind": "tool_call", "tool_name": "mcp__workflow-quality__post_brief", "ok": True,
               "input": {}, "output": [{"type": "text", "text": json.dumps({"scored": True, "id": b["id"], "baseline": {"id": 999}})}]}
        sh = {"v": 1, "ts": t0 + 0.002, "harness": "claude", "session_id": sid, "kind": "tool_call", "tool_name": "Bash", "ok": True,
              "input": {"command": f"curl -s -X POST localhost:8765/v1/briefs/{b['id']}/executions -d '{{}}'"}, "output": {"stdout": json.dumps(ex)}}
        other = {"v": 1, "ts": t0 + 0.003, "harness": "claude", "session_id": sid, "kind": "tool_call", "tool_name": "Bash", "ok": True,
                 "input": {"command": "curl -s localhost:8765/v1/briefs/1"}, "output": {"stdout": "{\"id\": 12345}"}}
        he.ingest([mcp, sh, other])
        he.ingest([mcp, sh, other])  # idempotent
        s = he.session(sid)
        self.assertEqual([a["id"] for a in s["artifacts"]], [b["id"]])
        self.assertEqual([e["id"] for e in s["executions"]], [ex["id"]])
        self.assertEqual([x["session_id"] for x in he.plan_sessions("bd", "pb")["sessions"]], [sid])
        self.assertEqual(he.execution_activity(ex["id"])["execution"]["conversation_id"], sid)
        with q.db() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM conversation_binds WHERE conversation_id=?", (sid,)).fetchone()[0], 2)

    def test_lifecycle_rest_flow(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), server.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        def call(method, path, body=None):
            r = urllib.request.Request(f"http://127.0.0.1:{srv.server_port}{path}", json.dumps(body).encode() if body is not None else None, method=method)
            try:
                with urllib.request.urlopen(r) as resp:
                    return resp.status, json.load(resp)
            except urllib.error.HTTPError as e:
                return e.code, json.load(e)
        ctx = {"harness": "claude", "model": "m1", "conversation_id": "c1", "initiator_type": "human", "initiator_id": "cody", "workflow_version": "9.9.9"}
        st, d = call("POST", "/v1/designs", {**ctx, "text": "# D\n\n## Intent\n> x\n", "project": "lc", "plan": "pl", "work_type": "feature", "design_stage": "drafting", "use_jev": False})
        self.assertEqual(st, 201); did = d["id"]
        st, d2 = call("PATCH", f"/v1/designs/{did}", {"design_stage": "approved"})
        self.assertEqual(d2["artifact"]["design_stage"], "approved")
        st, b = call("POST", "/v1/briefs", {**ctx, "text": BRIEF, "project": "lc", "plan": "pl", "name": "01", "design_id": did, "use_jev": False})
        bid = b["id"]; self.assertEqual(b["artifact"]["work_type"], "feature")  # inherited
        st, again = call("POST", "/v1/briefs", {**ctx, "text": BRIEF, "project": "lc", "plan": "pl", "name": "01", "use_jev": False})
        self.assertFalse(again["scored"]); self.assertEqual(again["id"], bid)
        st, e = call("POST", f"/v1/briefs/{bid}/executions", ctx); eid = e["id"]
        call("PATCH", f"/v1/executions/{eid}", {"items": [{"kind": "gap", "text": "no pagination in brief"}, {"kind": "adjustment", "text": "used existing helper"}], "cost_usd": 1.5, "turns": 12})
        st, done = call("POST", f"/v1/executions/{eid}/complete", {"outcome": "done", "summary": "ok", "cost_usd": 2.0})
        self.assertEqual((done["brief"]["gaps"], done["brief"]["adjustments"]), (1, 1))
        self.assertEqual(call("GET", f"/v1/briefs/{bid}")[1]["execution_stage"], "complete")
        rows = call("GET", "/v1/outcomes?by=initiator")[1]
        h = next(r for r in rows if r["grp"] == "human")
        self.assertEqual((h["done_rate"], h["cost_usd"]), (1.0, 2.0))
        self.assertEqual(call("GET", "/v1/plans/lc/pl/cost")[1]["total_cost_usd"], 2.0)
        with q.db() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM links WHERE type='missing_scope' AND to_artifact=?", (bid,)).fetchone()[0], 1)  # a gap back-references its brief
            self.assertGreaterEqual(c.execute("SELECT count(*) FROM events WHERE conversation_id='c1'").fetchone()[0], 6)
        self.assertEqual(call("POST", "/v1/briefs", {"text": "x", "initiator_type": "alien", "project": "p", "path": "a.md"})[0], 400)
        self.assertEqual(call("GET", "/v1/briefs/99999")[0], 400)
        srv.shutdown()


if __name__ == "__main__":
    unittest.main()
