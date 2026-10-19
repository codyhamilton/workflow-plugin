"""spool.sh kick: Python drain when YAKKA_BIN is unset; design 2 alignment."""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parent.parent
SPOOL = SCRIPT_DIR / "spool.sh"
DESIGN2 = REPO_ROOT / "docs" / "design" / "02-edge-capture.md"


def env(**kw):
    e = {k: v for k, v in os.environ.items() if k not in ("YAKKA_BIN", "YAKKA_QUEUE")}
    e.update(YAKKA_QUALITY_URL="")
    e.update(kw)
    return e


def run_spool(payload, harness="claude", event=None, path=None, **kw):
    cmd = ["bash", str(SPOOL), "--harness", harness] + (["--event", event] if event else [])
    return subprocess.run(
        cmd,
        input=payload,
        capture_output=True,
        text=True,
        env=env(PATH=path or os.environ.get("PATH", ""), **kw),
    )


def evts(d):
    return sorted(Path(d).glob("*.evt"))


class KickBase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.q = os.path.join(self.d, "queue")
        self.home = os.path.join(self.d, "home")
        self.py_log = os.path.join(self.d, "python3.log")
        self.bindir = os.path.join(self.d, "bin")
        os.makedirs(self.bindir)
        fake = os.path.join(self.bindir, "python3")
        Path(fake).write_text(f'#!/bin/sh\necho "$@" >> "{self.py_log}"\n')
        os.chmod(fake, 0o755)
        self.path = self.bindir + os.pathsep + os.environ.get("PATH", "")

    def py_calls(self, wait=False):
        for _ in range(30 if wait else 1):
            if os.path.exists(self.py_log):
                return Path(self.py_log).read_text().splitlines()
            time.sleep(0.1)
        return []


class UnsetBin(KickBase):
    def test_python3_drain_not_wrapper(self):
        r = run_spool(
            '{"conversation_id":"c1"}',
            event="Stop",
            YAKKA_QUEUE=self.q,
            YAKKA_HOOKLOG_KICK="1",
            HOME=self.home,
            path=self.path,
        )
        self.assertEqual(r.returncode, 0)
        lines = self.py_calls(True)
        self.assertEqual(len(lines), 1)
        parts = lines[0].split()
        self.assertEqual(parts[0], str(PLUGIN_ROOT / "client" / "yakka.py"))
        self.assertEqual(parts[1], "drain")
        joined = " ".join(lines)
        self.assertNotIn("bin/yakka", joined)
        self.assertNotIn("go build", joined)
        self.assertNotIn("download", joined.lower())

    def test_spool_envelope_and_exit(self):
        payload = '{"conversation_id":"cid-1","n":1}'
        r = run_spool(payload, YAKKA_QUEUE=self.q, YAKKA_HOOKLOG_KICK="0", HOME=self.home, path=self.path)
        self.assertEqual(r.returncode, 0)
        files = evts(self.q)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("cid-1-"))
        head, body = files[0].read_text().split("\n", 1)
        env = json.loads(head)
        self.assertEqual(set(env), {"ts", "harness", "event"})
        self.assertEqual(body, payload)


class YakkaBin(KickBase):
    def setUp(self):
        super().setUp()
        self.stub_log = os.path.join(self.d, "stub.log")
        self.bin = os.path.join(self.d, "yakka-stub")
        Path(self.bin).write_text(f'#!/bin/sh\necho "$@" >> "{self.stub_log}"\n')
        os.chmod(self.bin, 0o755)

    def stub_calls(self, wait=False):
        for _ in range(30 if wait else 1):
            if os.path.exists(self.stub_log):
                return Path(self.stub_log).read_text().splitlines()
            time.sleep(0.1)
        return []

    def test_executable_stub_gets_drain(self):
        run_spool(
            '{"session_id":"s1"}',
            YAKKA_BIN=self.bin,
            YAKKA_QUEUE=self.q,
            YAKKA_HOOKLOG_KICK="1",
            HOME=self.home,
            path=self.path,
        )
        self.assertEqual(self.stub_calls(True), ["drain"])
        self.assertEqual(self.py_calls(), [])

    def test_non_executable_bin_no_drain(self):
        bad = os.path.join(self.d, "not-exec")
        Path(bad).write_text("#!/bin/sh\n")
        os.chmod(bad, 0o644)
        run_spool(
            '{"session_id":"s1"}',
            YAKKA_BIN=bad,
            YAKKA_QUEUE=self.q,
            YAKKA_HOOKLOG_KICK="1",
            HOME=self.home,
            path=self.path,
        )
        time.sleep(0.3)
        self.assertEqual(self.stub_calls(), [])
        self.assertEqual(self.py_calls(), [])

    def test_kick_off_no_drain(self):
        run_spool(
            '{"session_id":"s1"}',
            YAKKA_BIN=self.bin,
            YAKKA_QUEUE=self.q,
            YAKKA_HOOKLOG_KICK="0",
            HOME=self.home,
            path=self.path,
        )
        time.sleep(0.3)
        self.assertEqual(self.stub_calls(), [])
        self.assertEqual(self.py_calls(), [])


class Design2(unittest.TestCase):
    def test_edge_capture_describes_python_drain(self):
        text = DESIGN2.read_text()
        self.assertIn("python3 plugins/yakka/client/yakka.py drain", text)
        self.assertNotIn("setsid plugins/yakka/bin/yakka drain", text)
        m = text.split("## Changes from what exists", 1)
        self.assertEqual(len(m), 2)
        changes = m[1]
        self.assertIn("plugins/yakka/client/yakka.py", changes)
        self.assertIn("yakka serve", changes)
        self.assertIn(".drain.lock", changes)


if __name__ == "__main__":
    unittest.main()
