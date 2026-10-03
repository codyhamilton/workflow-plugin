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
        self.assertEqual((rows[0]["grp"], rows[0]["done_rate"], rows[0]["cost_usd"]), ("human", 1.0, 2.0))
        self.assertEqual(call("GET", "/v1/plans/lc/pl/cost")[1]["total_cost_usd"], 2.0)
        with q.db() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM links WHERE type='missing_scope' AND to_artifact=?", (bid,)).fetchone()[0], 1)  # a gap back-references its brief
            self.assertGreaterEqual(c.execute("SELECT count(*) FROM events WHERE conversation_id='c1'").fetchone()[0], 6)
        self.assertEqual(call("POST", "/v1/briefs", {"text": "x", "initiator_type": "alien", "project": "p", "path": "a.md"})[0], 400)
        self.assertEqual(call("GET", "/v1/briefs/99999")[0], 400)
        srv.shutdown()


if __name__ == "__main__":
    unittest.main()
