import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, List, Optional

import yakka

_SCRIPT = os.path.join(os.path.dirname(__file__), "yakka.py")


def _spool_file(dir_path: str, name: str) -> None:
    conv = name.split("-", 1)[0]
    body = (
        '{"ts":1.5,"harness":"claude","event":"Stop"}\n'
        + json.dumps({"hook_event_name": "Stop", "session_id": conv})
    )
    tmp_dir = os.path.join(dir_path, "tmp")
    os.makedirs(tmp_dir, mode=0o700, exist_ok=True)
    tmp = os.path.join(tmp_dir, name)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(body)
    os.rename(tmp, os.path.join(dir_path, name + ".evt"))


def _count(dir_path: str, suffix: str) -> int:
    try:
        names = os.listdir(dir_path)
    except OSError:
        return 0
    return sum(1 for n in names if n.endswith(suffix))


class _Call:
    def __init__(self, n: int, auth: str, seq_no: int) -> None:
        self.at = time.time()
        self.n = n
        self.auth = auth
        self.seq_no = seq_no


class _FakeState:
    def __init__(self) -> None:
        self.calls: List[_Call] = []
        self.h: Optional[
            Callable[[_Call, Any, List[str]], bool]
        ] = None
        self.lock = threading.Lock()

    def n(self) -> int:
        with self.lock:
            return len(self.calls)


class _FakeHandler(BaseHTTPRequestHandler):
    state: _FakeState

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        req = json.loads(raw)
        ids = [x["id"] for x in req.get("facts", [])]
        auth = self.headers.get("Authorization", "")
        with self.state.lock:
            c = _Call(len(ids), auth, len(self.state.calls))
            self.state.calls.append(c)
        if self.state.h is not None and self.state.h(c, self, ids):
            return
        _ok(self, ids, None)

    def version_string(self) -> str:
        return "FakeHTTP/1.0"


def _ok(
    handler: BaseHTTPRequestHandler,
    ids: List[str],
    rej: Optional[dict[str, str]],
) -> None:
    res = []
    for id_ in ids:
        if rej and id_ in rej:
            res.append({"id": id_, "status": "rejected", "reason": rej[id_]})
        else:
            res.append({"id": id_, "status": "accepted"})
    body = json.dumps({"results": res}).encode()
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _start_fake(
    h: Optional[Callable[[_Call, Any, List[str]], bool]] = None,
) -> tuple[str, _FakeState, HTTPServer]:
    state = _FakeState()
    state.h = h

    class Handler(_FakeHandler):
        pass

    Handler.state = state
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    srv.fake_state = state
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    host, port = srv.server_address
    return f"http://{host}:{port}", state, srv


def _opts(dir_path: str, url: str) -> yakka.Options:
    return yakka.Options(
        Dir=dir_path,
        Window=0.03,
        Linger=0.15,
        Poll=0.01,
        BackoffMin=0.04,
        BackoffMax=0.4,
        GiveUp=3600.0,
        Sink=lambda: (yakka.HTTPSink(Endpoint=url, Key="k"), None),
    )


def _run(o: yakka.Options) -> str:
    ctx = yakka.DrainContext.with_timeout(20.0)
    reason, err = yakka.Run(ctx, o)
    if err is not None:
        raise err
    return reason


class DrainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_delivery_results(self) -> None:
        dir_path = self._tmpdir
        for n in ("a-1", "b-2", "c-3"):
            _spool_file(dir_path, n)

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            _ok(w, ids, {"b-2.evt#0": "payload.x looks like a secret"})
            return True

        url, _, srv = _start_fake(h)
        try:
            r = _run(_opts(dir_path, url))
            self.assertEqual(r, yakka.ReasonIdle)
            self.assertEqual(_count(dir_path, ".evt"), 0)
            rej = os.path.join(dir_path, "rejected")
            self.assertEqual(_count(rej, ".evt"), 1)
            with open(
                os.path.join(rej, "b-2.evt.reason"), encoding="utf-8"
            ) as f:
                self.assertEqual(
                    f.read(), "b-2.evt#0: payload.x looks like a secret\n"
                )
        finally:
            srv.shutdown()
            srv.server_close()

    def test_delivery_auth_header(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")
        url, state, srv = _start_fake()
        try:
            _run(_opts(dir_path, url))
            self.assertEqual(state.calls[0].auth, "Bearer k")
        finally:
            srv.shutdown()
            srv.server_close()

    def test_backoff_503_keeps_files(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            if c.seq_no < 4:
                w.send_response(503)
                w.end_headers()
                return True
            return False

        url, state, srv = _start_fake(h)
        try:
            self.assertEqual(_run(_opts(dir_path, url)), yakka.ReasonIdle)
            self.assertEqual(state.n(), 5)
            self.assertEqual(_count(dir_path, ".evt"), 0)
            g1 = state.calls[1].at - state.calls[0].at
            g3 = state.calls[3].at - state.calls[2].at
            self.assertGreater(g3, g1)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_backoff_dropped_connection(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            if c.seq_no < 2:
                w.connection.close()
                return True
            return False

        url, state, srv = _start_fake(h)
        try:
            self.assertEqual(_run(_opts(dir_path, url)), yakka.ReasonIdle)
            self.assertEqual(state.n(), 3)
            self.assertEqual(_count(dir_path, ".evt"), 0)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_backoff_unauthorized_keeps_files(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            w.send_response(401)
            w.end_headers()
            return True

        url, _, srv = _start_fake(h)
        try:
            ctx = yakka.DrainContext.with_timeout(0.7)
            reason, _ = yakka.Run(ctx, _opts(dir_path, url))
            self.assertEqual(reason, yakka.ReasonStopped)
            self.assertEqual(_count(dir_path, ".evt"), 1)
            self.assertEqual(_count(os.path.join(dir_path, "rejected"), ""), 0)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_backoff_gives_up_at_cap(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            w.send_response(500)
            w.end_headers()
            return True

        url, _, srv = _start_fake(h)
        try:
            o = _opts(dir_path, url)
            o.GiveUp = 0.3
            self.assertEqual(_run(o), yakka.ReasonGaveUp)
            self.assertEqual(_count(dir_path, ".evt"), 1)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_retry_after_429(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            if c.seq_no == 0:
                w.send_response(429)
                w.send_header("Retry-After", "1")
                w.end_headers()
                return True
            return False

        url, state, srv = _start_fake(h)
        try:
            _run(_opts(dir_path, url))
            self.assertEqual(state.n(), 2)
            self.assertEqual(_count(dir_path, ".evt"), 0)
            d = state.calls[1].at - state.calls[0].at
            self.assertGreaterEqual(d, 0.95)
            self.assertLessEqual(d, 1.6)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_split_413(self) -> None:
        dir_path = self._tmpdir
        for n in ("a-1", "b-2", "c-3", "d-4"):
            _spool_file(dir_path, n)

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            if len(ids) > 1:
                w.send_response(413)
                w.end_headers()
                return True
            return False

        url, state, srv = _start_fake(h)
        try:
            _run(_opts(dir_path, url))
            self.assertEqual(_count(dir_path, ".evt"), 0)
            rej = os.path.join(dir_path, "rejected")
            self.assertEqual(_count(rej, ".evt"), 0)
            self.assertEqual(state.n(), 1 + 2 + 4)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_split_single_file_rejected(self) -> None:
        dir_path = self._tmpdir
        for n in ("a-1", "b-2", "c-3"):
            _spool_file(dir_path, n)

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            for id_ in ids:
                if id_.startswith("b-2"):
                    w.send_response(413)
                    w.end_headers()
                    return True
            return False

        url, _, srv = _start_fake(h)
        try:
            _run(_opts(dir_path, url))
            rej = os.path.join(dir_path, "rejected")
            self.assertEqual(_count(dir_path, ".evt"), 0)
            self.assertEqual(_count(rej, ".evt"), 1)
            with open(os.path.join(rej, "b-2.evt.reason"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "b-2.evt: 413\n")
        finally:
            srv.shutdown()
            srv.server_close()

    def test_split_400_single_file(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")

        def h(c: _Call, w: Any, ids: List[str]) -> bool:
            w.send_response(400)
            w.end_headers()
            return True

        url, _, srv = _start_fake(h)
        try:
            _run(_opts(dir_path, url))
            with open(
                os.path.join(dir_path, "rejected", "a-1.evt.reason"),
                encoding="utf-8",
            ) as f:
                self.assertEqual(f.read(), "a-1.evt: 400\n")
        finally:
            srv.shutdown()
            srv.server_close()

    def test_idle_exit_race(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")
        url, _, srv = _start_fake()
        try:
            o = _opts(dir_path, url)
            n = 0

            def after_release() -> None:
                nonlocal n
                if n < 3:
                    n += 1
                    _spool_file(dir_path, f"r{n}-9")

            o.afterRelease = after_release
            self.assertEqual(_run(o), yakka.ReasonIdle)
            self.assertEqual(n, 3)
            self.assertEqual(_count(dir_path, ".evt"), 0)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_race_second_drain_exits(self) -> None:
        dir_path = self._tmpdir
        url, _, srv = _start_fake()
        try:
            yakka.EnsureDirs(dir_path)
            ctx = yakka.DrainContext()
            done: list[str] = []

            def first() -> None:
                o = _opts(dir_path, url)
                o.Linger = 60.0
                r, _ = yakka.Run(ctx, o)
                done.append(r)

            t = threading.Thread(target=first, daemon=True)
            t.start()
            for i in range(201):
                if yakka.Running(dir_path):
                    break
                time.sleep(0.01)
            else:
                self.fail("first drain never took the lock")
            start = time.time()
            self.assertEqual(_run(_opts(dir_path, url)), yakka.ReasonLockHeld)
            self.assertLess(time.time() - start, 2.0)
            ctx.cancel()
            t.join(timeout=5)
            self.assertFalse(yakka.Running(dir_path))
        finally:
            srv.shutdown()
            srv.server_close()

    def test_invalid_config_gives_up(self) -> None:
        dir_path = self._tmpdir
        _spool_file(dir_path, "a-1")
        o = _opts(dir_path, "")

        def bad_sink() -> tuple[None, Exception]:
            return None, OSError("client.toml: bad endpoint")

        o.Sink = bad_sink
        o.GiveUp = 0.3
        self.assertEqual(_run(o), yakka.ReasonGaveUp)
        self.assertEqual(_count(dir_path, ".evt"), 1)
        self.assertFalse(yakka.Running(dir_path))

    def test_status_data(self) -> None:
        dir_path = self._tmpdir
        yakka.EnsureDirs(dir_path)
        _spool_file(dir_path, "a-1")
        rej = os.path.join(dir_path, "rejected")
        open(os.path.join(rej, "x.evt"), "w").close()
        open(os.path.join(rej, "x.evt.reason"), "w").close()
        st = yakka.QueueStatus(dir_path)
        self.assertEqual(st.Queued, 1)
        self.assertEqual(st.Rejected, 1)
        self.assertFalse(st.Running)
        self.assertGreaterEqual(st.OldestAge, 0)

    def test_half_set_env_refusal_drain(self) -> None:
        hits = 0
        hits_lock = threading.Lock()
        ln = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ln.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ln.bind(("127.0.0.1", 8770))
        ln.listen(5)

        def accept_loop() -> None:
            nonlocal hits
            while True:
                try:
                    c, _ = ln.accept()
                except OSError:
                    return
                with hits_lock:
                    hits += 1
                c.close()

        th = threading.Thread(target=accept_loop, daemon=True)
        th.start()
        try:
            absent = os.path.join(self._tmpdir, "absent.toml")
            env = os.environ.copy()
            env.pop("YAKKA_KEY", None)
            env["YAKKA_ENDPOINT"] = "http://collector.example"
            env["YAKKA_CLIENT_CONFIG"] = absent
            proc = subprocess.run(
                [sys.executable, _SCRIPT, "drain"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            out = proc.stdout + proc.stderr
            self.assertIn("YAKKA_ENDPOINT", out)
            with hits_lock:
                self.assertEqual(hits, 0)
        finally:
            ln.close()


if __name__ == "__main__":
    unittest.main()
