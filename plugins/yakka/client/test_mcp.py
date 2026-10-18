import fcntl
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, List, Optional

import yakka

_SECRET_KEY = "sk-test-KEY-0123456789abcdef"


def _git(dir_path: str, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "TYPESAFE_API_KEY": "",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@x",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@x",
        }
    )
    out = subprocess.run(
        ["git", "-C", dir_path, *args],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _content_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class _McpEnv:
    def __init__(self, test: unittest.TestCase, texts: List[str]) -> None:
        self.t = test
        self.texts = texts
        tmp = os.path.realpath(tempfile.mkdtemp())
        test.addCleanup(lambda: _rmtree(tmp))
        self.home = os.path.join(tmp, "home")
        self.repo = os.path.join(tmp, "repo")
        self.wt = os.path.join(tmp, "wt")
        self.queue = os.path.join(tmp, "queue")
        self.cfg = os.path.join(tmp, "client.toml")
        os.environ["HOME"] = self.home
        os.environ["YAKKA_QUEUE"] = self.queue
        os.environ["YAKKA_CLIENT_CONFIG"] = self.cfg
        os.environ["TYPESAFE_API_KEY"] = ""
        os.makedirs(os.path.join(self.queue, "rejected"), mode=0o700)
        os.makedirs(os.path.join(self.repo, "docs/plans/x"), mode=0o755)
        self.design = os.path.join(self.repo, "docs/plans/x/DESIGN.md")
        with open(self.design, "w", encoding="utf-8") as f:
            f.write("# Design\n")
        other = os.path.join(self.repo, "docs/plans/x/other.txt")
        with open(other, "w", encoding="utf-8") as f:
            f.write("o\n")
        _git(self.repo, "init", "-q")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "first")
        _git(self.repo, "worktree", "add", "-q", self.wt, "-b", "wt")
        self.hits = 0
        self.hits_lock = threading.Lock()
        self.drains = 0
        self.drains_lock = threading.Lock()
        self.artifact: Callable[[], tuple[int, Any]] = lambda: (
            404,
            {"error": "none"},
        )
        self.baseline: Any = {"kind": "design", "checks": {}}
        self.state_lock = threading.Lock()
        self._start_stub()

    def _start_stub(self) -> None:
        env = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                with env.hits_lock:
                    env.hits += 1
                if self.headers.get("Authorization") != "Bearer " + _SECRET_KEY:
                    self.send_response(401)
                    self.end_headers()
                    return
                with env.state_lock:
                    code, body = 200, {}
                    if self.path.startswith("/v1/artifacts"):
                        code, body = env.artifact()
                    elif self.path == "/v1/health":
                        body = {"ok": True}
                    elif self.path.startswith("/v1/baselines"):
                        body = env.baseline
                    elif self.path.startswith("/v1/checks"):
                        body = {
                            "loaded": True,
                            "checks": [
                                {
                                    "kind": "design",
                                    "name": "clarity",
                                    "q": "Is it clear?",
                                    "levels": ["no", "partly", "yes"],
                                    "invert": False,
                                },
                                {
                                    "kind": "design",
                                    "name": "debt",
                                    "q": "Is there debt?",
                                    "levels": ["low", "high"],
                                    "invert": True,
                                },
                            ],
                        }
                    elif self.path.startswith("/v1/search"):
                        body = {
                            "hits": [
                                {
                                    "repo_id": "root:abc",
                                    "path": "docs/plans/y/DESIGN.md",
                                    "kind": "design",
                                    "content_hash": "h",
                                    "snippet": "a [match] here",
                                    "rank": -1.5,
                                }
                            ]
                        }
                raw = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.stub = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.stub.serve_forever, daemon=True)
        thread.start()
        self.t.addCleanup(self.stub.shutdown)
        self.t.addCleanup(self.stub.server_close)
        host, port = self.stub.server_address
        self.stub_url = f"http://{host}:{port}"
        self.write_config(self.stub_url)

    def write_config(self, endpoint: str) -> None:
        with open(self.cfg, "w", encoding="utf-8") as f:
            f.write(f'endpoint = "{endpoint}"\nkey = "{_SECRET_KEY}"\n')
        os.chmod(self.cfg, 0o600)

    def hash(self) -> str:
        return _content_hash(self.design)

    def evt(self, dir_path: str, name: str, file_path: str, age: float) -> str:
        body = (
            '{"ts":1700000000.5,"harness":"cursor","event":"afterFileEdit"}\n'
            + json.dumps(
                {
                    "hook_event_name": "afterFileEdit",
                    "conversation_id": "c",
                    "cwd": os.path.dirname(file_path),
                    "file_path": file_path,
                }
            )
        )
        p = os.path.join(dir_path, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        old = time.time() - age
        os.utime(p, (old, old))
        return p

    def serve(self) -> "_McpClient":
        in_read_fd, in_write_fd = os.pipe()
        out_read_fd, out_write_fd = os.pipe()
        in_read = os.fdopen(in_read_fd, "rb")
        out_write = os.fdopen(out_write_fd, "wb")
        done: List[Optional[BaseException]] = [None]

        def start_drain() -> Optional[BaseException]:
            with self.drains_lock:
                self.drains += 1
            return None

        opts = yakka.McpOptions(
            Version="test",
            QueueDir=self.queue,
            Wait=0.3,
            StartDrain=start_drain,
            Getwd=lambda: (self.repo, None),
        )

        def run() -> None:
            try:
                done[0] = yakka.Serve(in_read, out_write, opts)
            finally:
                out_write.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        in_write = os.fdopen(in_write_fd, "wb")
        out_read = os.fdopen(out_read_fd, "rb")

        def cleanup() -> None:
            in_write.close()
            thread.join(timeout=5)
            in_read.close()
            out_read.close()
            if thread.is_alive():
                self.t.fail("Serve did not exit on EOF")
            if done[0] not in (None, InterruptedError()):
                self.t.fail(f"Serve: {done[0]}")

        self.t.addCleanup(cleanup)
        return _McpClient(self, in_write, out_read)


def _rmtree(path: str) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


class _McpClient:
    def __init__(self, env: _McpEnv, inp: Any, out: Any) -> None:
        self.e = env
        self.inp = inp
        self.out = out
        self.id = 0

    def send(self, line: str) -> None:
        self.inp.write(line.encode() + b"\n")
        self.inp.flush()

    def raw(self, line: str) -> dict[str, Any]:
        self.send(line)
        return self._read()

    def _read(self) -> dict[str, Any]:
        line = self.out.readline()
        if not line:
            self.e.t.fail("no reply")
        return json.loads(line.decode())

    def rpc(self, method: str, params: Any) -> dict[str, Any]:
        self.id += 1
        body = {
            "jsonrpc": "2.0",
            "id": self.id,
            "method": method,
            "params": params,
        }
        return self.raw(json.dumps(body))

    def tool(self, name: str, args: Any) -> tuple[str, bool]:
        m = self.rpc("tools/call", {"name": name, "arguments": args})
        if m.get("error"):
            self.e.t.fail(f"{name}: JSON-RPC error {m['error']}")
        res = m["result"]
        text = res["content"][0]["text"]
        self.e.texts.append(text)
        return text, bool(res.get("isError"))

    def feedback(self, path: str) -> str:
        text, is_err = self.tool("artifact_feedback", {"path": path})
        if is_err:
            self.e.t.fail(f"unexpected isError: {text}")
        return text


def _want(test: unittest.TestCase, text: str, *subs: str) -> None:
    for s in subs:
        test.assertIn(s, text, f"answer lacks {s!r}:\n{text}")


def _dont_want(test: unittest.TestCase, text: str, *subs: str) -> None:
    for s in subs:
        test.assertNotIn(s, text, f"answer has {s!r}:\n{text}")


def _err_code(m: dict[str, Any]) -> int:
    err = m.get("error")
    if isinstance(err, dict):
        return int(err.get("code", 0))
    return 0


class McpShimTests(unittest.TestCase):
    def test_shim(self) -> None:
        texts: List[str] = []

        with self.subTest("1 initialize"):
            c = _McpEnv(self, texts).serve()
            r = c.rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]
            self.assertEqual(r["protocolVersion"], "2025-06-18")
            self.assertEqual(r["serverInfo"]["name"], "yakka")
            self.assertIsNotNone(r.get("instructions"))
            r = c.rpc("initialize", {"protocolVersion": "1999-01-01"})["result"]
            self.assertEqual(r["protocolVersion"], "2025-11-25")
            c.send('{"jsonrpc":"2.0","method":"notifications/initialized"}')
            m = c.rpc("ping", None)
            self.assertEqual(m.get("id"), c.id)
            self.assertEqual(m.get("result"), {})

        with self.subTest("2 tools/list"):
            c = _McpEnv(self, texts).serve()
            tools = c.rpc("tools/list", None)["result"]["tools"]
            names = []
            for tm in tools:
                names.append(tm["name"])
                s = tm["inputSchema"]
                self.assertEqual(s["type"], "object")
                self.assertIsNotNone(s.get("required"))
                self.assertFalse(s.get("additionalProperties"))
                self.assertTrue(tm.get("description"))
                self.assertTrue(tm["annotations"]["readOnlyHint"])
            self.assertEqual(
                ",".join(names), "artifact_feedback,list_checks,search_artifacts"
            )

        with self.subTest("3 protocol errors"):
            c = _McpEnv(self, texts).serve()
            m = c.raw("{nope")
            self.assertEqual(_err_code(m), -32700)
            self.assertIsNone(m.get("id"))
            self.assertEqual(_err_code(c.raw("[]")), -32600)
            self.assertEqual(_err_code(c.raw("5")), -32600)
            self.assertEqual(_err_code(c.rpc("foo/bar", None)), -32601)
            self.assertEqual(
                _err_code(c.rpc("tools/call", {"name": "nope"})),
                -32602,
            )
            self.assertEqual(_err_code(c.rpc("tools/call", {})), -32602)
            self.assertIn("result", c.rpc("ping", None))

        with self.subTest("4 bad arguments"):
            e = _McpEnv(self, texts)
            c = e.serve()
            cases = {
                "missing path": ("artifact_feedback", {}),
                "wrong type": ("artifact_feedback", {"path": 5}),
                "directory": ("artifact_feedback", {"path": e.repo}),
                "missing file": ("artifact_feedback", {"path": "nope.md"}),
                "bad kind": ("list_checks", {"kind": "x"}),
                "empty query": ("search_artifacts", {"query": ""}),
                "search kind": ("search_artifacts", {"query": "a", "kind": "x"}),
            }
            for name, (tool, args) in cases.items():
                text, is_err = c.tool(tool, args)
                self.assertTrue(is_err, f"{name}: isError={is_err}")
                self.assertTrue(text, f"{name}: empty text")

        with self.subTest("5 queued"):
            e = _McpEnv(self, texts)
            e.evt(e.queue, "a.evt", e.design, 40.0)
            e.evt(
                e.queue,
                "b.evt",
                os.path.join(e.wt, "docs/plans/x/DESIGN.md"),
                5.0,
            )
            e.evt(
                e.queue,
                "c.evt",
                os.path.join(e.repo, "docs/plans/x/other.txt"),
                90.0,
            )
            c = e.serve()
            a = c.feedback("docs/plans/x/DESIGN.md")
            _want(
                self,
                a,
                "state: queued",
                "2 events",
                "oldest 4",
                "draining",
                "path: docs/plans/x/DESIGN.md",
                "repo: root:",
                "content_hash: " + e.hash(),
            )
            self.assertEqual(e.drains, 1)
            lock = open(
                os.path.join(e.queue, ".drain.lock"),
                "a+b",
                encoding=None,
            )
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                pass
            a = c.feedback(e.design)
            _want(self, a, "state: queued", "draining")
            self.assertEqual(e.drains, 1)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
            e.stub.shutdown()
            a = c.feedback(e.design)
            _want(
                self,
                a,
                "state: queued",
                "remote unreachable",
                "service unreachable at " + e.stub_url,
            )

        with self.subTest("6 rejected"):
            e = _McpEnv(self, texts)
            p = e.evt(os.path.join(e.queue, "rejected"), "r.evt", e.design, 60.0)
            reason = os.path.join(e.queue, "rejected", "r.evt.reason")
            with open(reason, "w", encoding="utf-8") as f:
                f.write(
                    "r.evt#1: secret: aws_access_key at line 3 in docs/plans/x/DESIGN.md\n"
                )
            now = time.time()
            os.utime(e.design, (now - 3600, now - 3600))
            c = e.serve()
            a = c.feedback(e.design)
            _want(
                self,
                a,
                "state: rejected",
                "secret: aws_access_key at line 3 in docs/plans/x/DESIGN.md",
                "Fix: rewrite the file; the new write is the repair.",
            )
            _dont_want(self, a, "r.evt#1:")
            os.utime(e.design, (now, now))
            a = c.feedback(e.design)
            _dont_want(self, a, "state: rejected")
            _want(self, a, "note: earlier rejection superseded by a later write")

        with self.subTest("7 delivered"):
            e = _McpEnv(self, texts)
            c = e.serve()

            def latest(screen: Any, rejection: Any, *scores: Any) -> None:
                with e.state_lock:

                    def artifact() -> tuple[int, Any]:
                        return 200, {
                            "repo_id": "r",
                            "path": "p",
                            "kind": "design",
                            "versions": 3,
                            "latest": {
                                "content_hash": e.hash(),
                                "received_at": "2026-01-01T00:00:00Z",
                                "screen": screen,
                                "scores": list(scores),
                                "rejection": rejection,
                            },
                        }

                    e.artifact = artifact

            latest({"verdict": "unscreened", "scorer": "none"}, None)
            a = c.feedback(e.design)
            _want(
                self,
                a,
                "state: delivered",
                "screen: unscreened (no scorer on the service)",
                "versions: 3",
            )
            latest({"verdict": "pass", "scorer": "jev-1"}, None)
            _want(c.feedback(e.design), "screen: pass by jev-1")
            latest(
                None,
                {"stage": "screen", "reason": "too vague", "at": "x"},
            )
            a = c.feedback(e.design)
            _want(self, a, "screen: flagged: too vague", "Fix: rewrite the file")
            latest(None, None)
            _want(c.feedback(e.design), "screen: awaiting screen")
            with e.state_lock:
                e.baseline = {
                    "kind": "design",
                    "checks": {
                        "clarity": {"n": 5, "p25": 0.5, "median": 0.7, "p75": 0.9},
                        "scope": {"n": 5, "p25": 0.5, "median": 0.7, "p75": 0.9},
                        "few": {"n": 3, "p25": 0.5, "median": 0.7, "p75": 0.9},
                    },
                }
            latest(
                {"verdict": "pass", "scorer": "jev-1"},
                None,
                {"check": "clarity", "score": 0.25},
                {"check": "scope", "score": 0.5},
                {"check": "few", "score": 0.1},
                {"check": "new", "score": 0.2},
            )
            a = c.feedback(e.design)
            for line in a.split("\n"):
                below = "BELOW p25" in line
                if line.startswith("clarity"):
                    self.assertEqual(below, True, line)
            _want(
                self,
                a,
                "clarity 0.25 (baseline p25 0.50, median 0.70, n 5) BELOW p25",
                "few 0.10 (baseline n=3, too few to flag)",
            )

        with self.subTest("8 stale and not delivered"):
            e = _McpEnv(self, texts)
            c = e.serve()
            a = c.feedback(e.design)
            _want(self, a, "state: not delivered")
            with e.state_lock:
                e.artifact = lambda: (
                    200,
                    {
                        "versions": 1,
                        "latest": {
                            "content_hash": "ab" * 32,
                            "received_at": "2026-01-01T00:00:00Z",
                            "scores": [],
                        },
                    },
                )
            a = c.feedback(e.design)
            _want(
                self,
                a,
                "state: stale",
                "current content not yet delivered",
                "abababababab",
                "2026-01-01T00:00:00Z",
            )

        with self.subTest("9 bad config and unreachable"):
            e = _McpEnv(self, texts)
            c = e.serve()
            with open(e.cfg, "w", encoding="utf-8") as f:
                f.write("not toml\n")
            before = e.hits
            a = c.feedback(e.design)
            _want(self, a, "state: bad config", e.cfg, "unusable")
            self.assertEqual(e.hits, before)
            e.write_config("http://127.0.0.1:1")
            e.evt(e.queue, "a.evt", e.design, 1.0)
            a = c.feedback(e.design)
            _want(self, a, "state: queued", "service unreachable at http://127.0.0.1:1")
            os.remove(os.path.join(e.queue, "a.evt"))
            a = c.feedback(e.design)
            _want(self, a, "state: not delivered", "service unreachable at http://127.0.0.1:1")
            text, is_err = c.tool("list_checks", {"kind": "design"})
            self.assertFalse(is_err, text)
            _want(self, text, "service unreachable")
            with open(e.cfg, "w", encoding="utf-8") as f:
                f.write("not toml\n")
            text, is_err = c.tool("search_artifacts", {"query": "x"})
            self.assertFalse(is_err, text)
            _want(self, text, "unusable")

        with self.subTest("10 not tracked"):
            e = _McpEnv(self, texts)
            zdir = os.path.join(tempfile.mkdtemp(), "docs/plans/z")
            os.makedirs(zdir, mode=0o755)
            f = os.path.join(zdir, "DESIGN.md")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write("x")
            before = e.hits
            c = e.serve()
            a = c.feedback(f)
            _want(self, a, "state: not tracked")
            a = c.feedback(os.path.join(e.repo, "docs/plans/x/other.txt"))
            _want(self, a, "state: not tracked")
            self.assertEqual(e.hits, before)

        with self.subTest("env bearer GET"):
            e = _McpEnv(self, texts)
            os.remove(e.cfg)
            os.environ["YAKKA_ENDPOINT"] = e.stub_url
            os.environ["YAKKA_KEY"] = _SECRET_KEY
            os.environ["YAKKA_CLIENT_CONFIG"] = os.path.join(
                tempfile.mkdtemp(), "missing.toml"
            )
            before = e.hits
            c = e.serve()
            text, is_err = c.tool("list_checks", {"kind": "design"})
            self.assertFalse(is_err, text)
            self.assertGreater(e.hits, before)
            _want(self, text, "clarity [levels no/partly/yes]: Is it clear?")

        with self.subTest("tools list_checks and search"):
            c = _McpEnv(self, texts).serve()
            a, _ = c.tool("list_checks", {"kind": "design"})
            _want(
                self,
                a,
                "clarity [levels no/partly/yes]: Is it clear?",
                "debt [levels low/high] [inverted]: Is there debt?",
            )
            a, _ = c.tool("search_artifacts", {"query": "match"})
            _want(
                self,
                a,
                "design root:abc:docs/plans/y/DESIGN.md (rank -1.5)",
                "a [match] here",
            )

        with self.subTest("11 no key leak"):
            self.assertGreaterEqual(len(texts), 10)
            for x in texts:
                self.assertNotIn(_SECRET_KEY, x)


if __name__ == "__main__":
    unittest.main()
