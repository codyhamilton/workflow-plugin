"""Replay the write fixtures through every shipped hook registration into a temp hosted serve.

Builds the workflow binary once, starts `serve` on a free 127.0.0.1 port with temp data, queue and
client config, runs each shipped command with the fixture payload, and waits for an
`artifact_version` fact for the file the fixture wrote. OpenCode fixtures go through
`spool.sh --harness opencode` (5-04 proved the plugin writes the same queue file).
"""
import json
import os
import pwd
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOBIN = os.path.join(pwd.getpwuid(os.getuid()).pw_dir, ".local/go/bin")  # HOME may be a temp dir
CONFIGS = {"claude": ["hooks/hooks.json"],
           "cursor": ["hooks/cursor.json", "tools/hooklog/cursor-hooks.example.json"],
           "codex": ["hooks/codex.json"]}
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def goenv(name):
    home = pwd.getpwuid(os.getuid()).pw_dir  # the Go caches live under the real home, not the temp one
    return subprocess.run([GOBIN + "/go", "env", name], capture_output=True, text=True,
                          env=dict(os.environ, HOME=home)).stdout.strip()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class WriteSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serve = None
        cls.tmp = tempfile.mkdtemp(prefix="writesurf.")
        cls.addClassCleanup(cls.cleanup)
        cls.setup()

    @classmethod
    def setup(cls):
        t = Path(cls.tmp)
        cls.home, cls.cache, cls.queue, cls.data = t / "home", t / "cache", t / "queue", t / "data"
        for d in (cls.home, cls.cache, cls.data):
            d.mkdir()
        gocache, gomod = goenv("GOCACHE"), goenv("GOMODCACHE")
        cls.bin = str(t / "workflow")
        env = dict(os.environ, PATH=GOBIN + ":" + os.environ["PATH"], HOME=str(cls.home), GOCACHE=gocache,
                   GOMODCACHE=gomod, XDG_CACHE_HOME=str(cls.cache), TYPESAFE_API_KEY="", CGO_ENABLED="0")
        build = subprocess.run(["go", "build", "-o", cls.bin, "./cmd/workflow"], cwd=ROOT / "tools/workflow",
                               env=env, capture_output=True, text=True, timeout=300)
        if build.returncode:
            raise RuntimeError("go build failed: " + build.stderr[-1500:])
        port = free_port()
        assert port not in (8765, 8770)
        key = secrets.token_hex(16)
        cls.cfg = t / "client.toml"
        cls.cfg.write_text('endpoint = "http://127.0.0.1:%d"\nkey = "%s"\n' % (port, key))
        cls.cfg.chmod(0o600)
        cls.env = {"PATH": "/usr/bin:/bin", "HOME": str(cls.home), "XDG_CACHE_HOME": str(cls.cache),
                   "WORKFLOW_QUEUE": str(cls.queue), "WORKFLOW_CLIENT_CONFIG": str(cls.cfg),
                   "WORKFLOW_SERVE_DATA": str(cls.data), "WORKFLOW_BIN": cls.bin, "TYPESAFE_API_KEY": "",
                   "WORKFLOW_HOOKLOG_KICK": "0", "CLAUDE_PLUGIN_ROOT": str(ROOT), "CURSOR_PLUGIN_ROOT": str(ROOT),
                   "PLUGIN_ROOT": str(ROOT)}
        cls.log = open(t / "serve.log", "wb")
        senv = dict(cls.env, WORKFLOW_SERVE_ADDR="127.0.0.1:%d" % port, WORKFLOW_SERVE_KEYS="t=" + key,
                    WORKFLOW_SERVE_POLL="500ms")
        cls.serve = subprocess.Popen([cls.bin, "serve"], env=senv, stderr=cls.log, stdout=cls.log)
        deadline = time.time() + 10
        while time.time() < deadline:
            if re.search(rb"serve: listening on", (t / "serve.log").read_bytes()):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("serve did not start")
        cls.repo = t / "repo"
        cls.repo.mkdir()
        for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(["git", "-C", str(cls.repo)] + args, check=True, capture_output=True,
                           env=dict(os.environ, **GIT_ENV))
        cls.n = 0

    @classmethod
    def cleanup(cls):
        if cls.serve:
            cls.serve.kill()
            cls.serve.wait()
        if getattr(cls, "log", None):
            cls.log.close()
        subprocess.run(["pkill", "-9", "-f", cls.tmp], capture_output=True)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def commands(self, harness, event, file):
        if harness == "opencode":
            return ['bash "%s/tools/hooklog/spool.sh" --harness opencode' % ROOT]
        config = json.loads((ROOT / file).read_text())
        groups = config["hooks"][event]
        hooks = groups if harness == "cursor" else [h for g in groups for h in g["hooks"]]
        return [h["command"].replace("/ABS/PATH/workflow-plugin", str(ROOT)) for h in hooks]

    def versions(self, path):
        db = self.data / "t" / "ledger.db"
        if not db.exists():
            return 0
        try:
            c = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=2)
            try:
                return c.execute("SELECT count(*) FROM facts WHERE type='artifact_version' AND path=?", (path,)).fetchone()[0]
            finally:
                c.close()
        except sqlite3.Error:
            return 0

    def test_fixtures_through_every_shipped_config(self):
        fixtures = json.loads((Path(__file__).parent / "fixtures/artifact_writes.json").read_text())
        for fx in fixtures:
            harness = fx["harness"]
            for file in CONFIGS.get(harness, [None]):
                payload = json.loads(json.dumps(fx["payload"]))
                rel = self.fixture_path(payload)
                with self.subTest(harness=harness, file=file, event=payload["hook_event_name"], path=rel,
                                  session=payload.get("session_id") or payload.get("conversation_id")):
                    type(self).n += 1
                    target = self.repo / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("# Doc\n\nreplay %d %s\n" % (self.n, secrets.token_hex(4)))
                    payload["cwd"] = str(self.repo)
                    before = self.versions(rel)
                    event = payload["hook_event_name"]
                    for command in self.commands(harness, event, file):
                        r = subprocess.run(command, shell=True, input=json.dumps(payload), text=True,
                                           capture_output=True, env=self.env, cwd=self.repo, timeout=10)
                        self.assertEqual(r.returncode, 0, r.stderr)
                    deadline = time.time() + 30
                    while self.versions(rel) <= before and time.time() < deadline:
                        time.sleep(0.25)
                    self.assertGreater(self.versions(rel), before, "no artifact_version for " + rel)

    @staticmethod
    def fixture_path(payload):
        p = payload
        ti = p.get("tool_input")
        if isinstance(ti, str):
            try:
                ti = json.loads(ti)
            except ValueError:
                m = re.search(r"\*\*\* (?:Update|Add) File: (\S+)", ti)
                return m.group(1)
        if isinstance(ti, dict):
            for k in ("file_path", "filePath", "target_file"):
                if k in ti:
                    return ti[k]
            if "input" in ti:
                return re.search(r"\*\*\* (?:Update|Add) File: (\S+)", ti["input"]).group(1)
        return p["file_path"]


if __name__ == "__main__":
    unittest.main()
