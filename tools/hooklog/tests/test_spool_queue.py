"""spool.sh: conversation-ID file names, the Go queue path and the WORKFLOW_BIN kick. Temp dirs only."""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPOOL = HERE.parent / "spool.sh"
DRAIN = HERE.parent / "drain.py"
FIXTURE = json.loads((HERE / "fixtures" / "artifact_writes.json").read_text())


def env(**kw):
    e = {k: v for k, v in os.environ.items() if k not in ("WORKFLOW_BIN", "WORKFLOW_QUEUE")}
    e.update(WORKFLOW_HOOKLOG_KICK="0", WORKFLOW_QUALITY_URL="")
    e.update(kw)
    return e


def run_spool(payload, harness="claude", event=None, **kw):
    cmd = ["bash", str(SPOOL), "--harness", harness] + (["--event", event] if event else [])
    return subprocess.run(cmd, input=payload, capture_output=True, text=True, env=env(**kw))


def evts(d):
    return sorted(Path(d).glob("*.evt"))


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)


class LegacyPath(Base):
    def test_fixture_payloads_named_by_id_and_drain(self):
        for item in FIXTURE:
            p = item["payload"]
            r = run_spool(json.dumps(p), item["harness"], WORKFLOW_HOOKLOG_DIR=self.d)
            self.assertEqual(r.returncode, 0)
        files = evts(Path(self.d) / "spool")
        self.assertEqual(len(files), len(FIXTURE))
        for item in FIXTURE:
            p = item["payload"]
            i = p.get("session_id") or p.get("conversation_id")
            self.assertEqual(len([f for f in files if f.name.startswith(i + "-") and f.name[len(i) + 1].isdigit()]), 1, i)
        r = subprocess.run(["python3", str(DRAIN), "--once"], capture_output=True, text=True,
                           env=env(WORKFLOW_HOOKLOG_DIR=self.d))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(evts(Path(self.d) / "spool"), [])
        for item in FIXTURE:
            p = item["payload"]
            i = p.get("session_id") or p.get("conversation_id")
            self.assertTrue(list(Path(self.d).glob(f"*/{i}.jsonl")), i)

    def test_no_id_is_unknown(self):
        r = run_spool('{"hook_event_name":"Stop"}', WORKFLOW_HOOKLOG_DIR=self.d)
        self.assertEqual(r.returncode, 0)
        files = evts(Path(self.d) / "spool")
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("unknown-"))

    def test_sanitised_prefix(self):
        run_spool('{"hook_event_name":"Stop","session_id" : "a/b c"}', WORKFLOW_HOOKLOG_DIR=self.d)
        files = evts(Path(self.d) / "spool")
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("a_b_c-"), files[0].name)

    def test_key_preference(self):
        run_spool('{"conversation_id":"c1","session_id":"s1"}', WORKFLOW_HOOKLOG_DIR=self.d)
        self.assertTrue(evts(Path(self.d) / "spool")[0].name.startswith("s1-"))

    def test_cursor_response(self):
        r = run_spool('{"conversation_id":"c1"}', "cursor", "preToolUse", WORKFLOW_HOOKLOG_DIR=self.d)
        self.assertEqual(json.loads(r.stdout), {"permission": "allow"})
        self.assertEqual(r.returncode, 0)


class GoPath(Base):
    def setUp(self):
        super().setUp()
        self.q = os.path.join(self.d, "queue")
        self.legacy = os.path.join(self.d, "legacy")
        self.log = os.path.join(self.d, "stub.log")
        self.bin = os.path.join(self.d, "stub.sh")
        Path(self.bin).write_text(f'#!/bin/sh\necho "$* q=$WORKFLOW_QUEUE" >> "{self.log}"\n')
        os.chmod(self.bin, 0o755)

    def spool(self, payload, **kw):
        return run_spool(payload, WORKFLOW_BIN=self.bin, WORKFLOW_QUEUE=self.q,
                         WORKFLOW_HOOKLOG_DIR=self.legacy, **kw)

    def calls(self, wait=False):
        for _ in range(30 if wait else 1):
            if os.path.exists(self.log):
                return Path(self.log).read_text().splitlines()
            time.sleep(0.1)
        return []

    def test_files_land_in_queue(self):
        r = self.spool('{"session_id":"s1"}')
        self.assertEqual(r.returncode, 0)
        files = evts(self.q)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("s1-"))
        self.assertFalse(os.path.exists(self.legacy))

    def test_no_id_not_spooled(self):
        r = self.spool('{"hook_event_name":"Stop"}')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(evts(self.q), [])
        self.assertEqual(list(Path(self.q, "tmp").iterdir()), [])
        self.assertEqual(self.calls(), [])

    def test_kick_invokes_stub(self):
        run_spool(
            '{"session_id":"s1"}', WORKFLOW_BIN=self.bin, WORKFLOW_QUEUE=self.q, WORKFLOW_HOOKLOG_KICK="1")
        self.assertEqual(self.calls(True), [f"drain q={self.q}"])

    def test_lock_held_no_kick(self):
        os.makedirs(self.q)
        lock = os.path.join(self.q, ".drain.lock")
        Path(lock).touch()
        holder = subprocess.Popen(["flock", lock, "sleep", "5"])
        try:
            time.sleep(0.3)
            run_spool('{"session_id":"s1"}', WORKFLOW_BIN=self.bin, WORKFLOW_QUEUE=self.q, WORKFLOW_HOOKLOG_KICK="1")
            time.sleep(0.5)
            self.assertEqual(self.calls(), [])
        finally:
            holder.kill()
            holder.wait()

    def test_kick_off_no_kick(self):
        self.spool('{"session_id":"s1"}')
        time.sleep(0.5)
        self.assertEqual(self.calls(), [])

    def test_concurrent(self):
        with ThreadPoolExecutor(20) as ex:
            rs = list(ex.map(lambda i: self.spool(json.dumps({"session_id": "s1", "n": i})), range(20)))
        self.assertTrue(all(r.returncode == 0 for r in rs))
        self.assertEqual(len({f.name for f in evts(self.q)}), 20)
        self.assertEqual(list(Path(self.q, "tmp").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
