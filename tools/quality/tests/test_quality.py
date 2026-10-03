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
        self.assertEqual(len(rpc("tools/list")["tools"]), 3)
        out = rpc("tools/call", {"name": "rate_artifact", "arguments": {"kind": "brief", "text": BRIEF, "project": "svc", "plan": "p", "use_jev": False}})
        self.assertNotIn("isError", out)
        self.assertIn("[workflow quality", out["content"][0]["text"])
        bad = rpc("tools/call", {"name": "rate_artifact", "arguments": {"kind": "other", "text": "x"}})
        self.assertTrue(bad["isError"])
        srv.shutdown()


if __name__ == "__main__":
    unittest.main()
