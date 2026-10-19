import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import yakka

_SCRIPT = os.path.join(os.path.dirname(__file__), "yakka.py")
_PLAIN = "wk_login_test_plain_token_0123456789ab"


class LoginEnv(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._env_save = {
            k: os.environ.pop(k, None)
            for k in ("YAKKA_ENDPOINT", "YAKKA_KEY", "YAKKA_CLIENT_CONFIG")
        }
        self._cfg = os.path.join(self._tmpdir, "client.toml")
        os.environ["YAKKA_CLIENT_CONFIG"] = self._cfg

    def tearDown(self) -> None:
        for k in ("YAKKA_ENDPOINT", "YAKKA_KEY", "YAKKA_CLIENT_CONFIG"):
            os.environ.pop(k, None)
        for k, v in self._env_save.items():
            if v is not None:
                os.environ[k] = v


class TestMissingEndpoint(LoginEnv):
    def test_missing_endpoint(self) -> None:
        code = yakka.run_login(
            yakka.LoginOptions(
                Stderr=io.StringIO(),
                OpenBrowser=lambda _url: None,
            )
        )
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self._cfg))


class TestLoginExchangeWritesConfig(LoginEnv):
    def test_login_exchange_writes_config(self) -> None:
        redirect_uri = ""

        class CollectorHandler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                if self.path != "/v1/device/exchange":
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode())
                if (
                    body.get("code") != "devcode"
                    or body.get("redirect_uri") != redirect_uri
                    or not body.get("state")
                ):
                    self.send_error(400, "bad exchange")
                    return
                out = json.dumps(
                    {"endpoint": collector_url, "token": _PLAIN}
                ).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(out)

        collector = HTTPServer(("127.0.0.1", 0), CollectorHandler)
        collector_url = f"http://127.0.0.1:{collector.server_address[1]}"
        th = Thread(target=collector.serve_forever, daemon=True)
        th.start()
        stderr = io.StringIO()

        def open_browser(device_url: str) -> None:
            nonlocal redirect_uri
            u = urllib.parse.urlparse(device_url)
            self.assertEqual(u.path, "/device")
            state = urllib.parse.parse_qs(u.query)["state"][0]
            redirect_uri = urllib.parse.parse_qs(u.query)["redirect_uri"][0]
            self.assertTrue(state)
            self.assertTrue(redirect_uri)
            cb = urllib.parse.urlparse(redirect_uri)
            q = urllib.parse.parse_qs(cb.query)
            q["code"] = ["devcode"]
            q["state"] = [state]
            cb = cb._replace(
                query=urllib.parse.urlencode(
                    {k: v[0] for k, v in q.items()}
                )
            )
            resp = urllib.request.urlopen(cb.geturl())
            resp.read()
            resp.close()

        try:
            code = yakka.run_login(
                yakka.LoginOptions(
                    Endpoint=collector_url,
                    Stderr=stderr,
                    OpenBrowser=open_browser,
                    Timeout=15.0,
                )
            )
        finally:
            collector.shutdown()
        self.assertEqual(code, 0)
        err_text = stderr.getvalue()
        self.assertNotIn(_PLAIN, err_text)
        self.assertNotIn("wk_", err_text)
        with open(self._cfg, encoding="utf-8") as f:
            data = f.read()
        self.assertIn(f'key = "{_PLAIN}"', data)
        self.assertIn(f'endpoint = "{collector_url}"', data)
        mode = os.stat(self._cfg).st_mode & 0o777
        self.assertEqual(mode, 0o600)


class TestDevicePageURL(unittest.TestCase):
    def test_device_page_url(self) -> None:
        u = yakka.device_page_url(
            "https://collector.example", "st", "http://127.0.0.1:9/callback"
        )
        self.assertTrue(u.startswith("https://collector.example/device?"))
        parsed = urllib.parse.urlparse(u)
        q = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(q["state"][0], "st")
        self.assertEqual(q["redirect_uri"][0], "http://127.0.0.1:9/callback")
        pages = yakka.device_page_url(
            "https://api.yakka.build", "st", "http://127.0.0.1:9/callback"
        )
        self.assertTrue(pages.startswith("https://yakka.build/device?"))


class TestEndpointFromExistingConfig(LoginEnv):
    def test_endpoint_from_existing_config(self) -> None:
        with open(self._cfg, "w", encoding="utf-8") as f:
            f.write('endpoint = "https://old.example"\nkey = "wk_old"\n')
        os.chmod(self._cfg, 0o600)
        ep, err = yakka.resolve_endpoint("")
        self.assertIsNone(err)
        self.assertEqual(ep, "https://old.example")


class TestNormalizeStripsUserinfo(unittest.TestCase):
    def test_normalize_strips_userinfo(self) -> None:
        ep, err = yakka.normalize_origin("https://user:s3cret@collector.example")
        self.assertIsNone(err)
        self.assertEqual(ep, "https://collector.example")
        self.assertNotIn("s3cret", ep)
        _, bad = yakka.normalize_origin("https://collector.example/v1/ingest")
        self.assertIsNotNone(bad)
        ep6, err6 = yakka.normalize_origin("http://[::1]:8770")
        self.assertIsNone(err6)
        self.assertEqual(ep6, "http://[::1]:8770")


class TestReloginTightensMode(LoginEnv):
    def test_relogin_tightens_mode(self) -> None:
        with open(self._cfg, "w", encoding="utf-8") as f:
            f.write("old\n")
        os.chmod(self._cfg, 0o644)
        err = yakka.write_client_config(
            self._cfg, "http://127.0.0.1:9", "wk_plain_token"
        )
        self.assertIsNone(err)
        self.assertEqual(os.stat(self._cfg).st_mode & 0o777, 0o600)


class TestExchangeRejectsRedirectAndBadEndpoint(LoginEnv):
    def test_exchange_does_not_follow_redirect(self) -> None:
        seen: dict[str, bool] = {}

        class Attacker(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                seen["hit"] = True
                body = json.dumps(
                    {
                        "token": "wk_attacker_token_should_not_stick_0123456789",
                        "endpoint": "https://attacker.example",
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        attacker = HTTPServer(("127.0.0.1", 0), Attacker)

        class Collector(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                loc = (
                    f"http://127.0.0.1:{attacker.server_address[1]}"
                    "/v1/device/exchange"
                )
                self.send_response(302)
                self.send_header("Location", loc)
                self.end_headers()

        collector = HTTPServer(("127.0.0.1", 0), Collector)
        collector_url = f"http://127.0.0.1:{collector.server_address[1]}"
        Thread(target=attacker.serve_forever, daemon=True).start()
        Thread(target=collector.serve_forever, daemon=True).start()
        try:
            token, _ep, err = yakka._login_exchange(
                collector_url,
                "devcode",
                "state",
                "http://127.0.0.1:9/callback",
                5.0,
            )
        finally:
            collector.shutdown()
            attacker.shutdown()
        self.assertIsNotNone(err)
        self.assertEqual(token, "")
        self.assertNotIn("wk_attacker", str(err))
        self.assertFalse(seen.get("hit", False))

    def test_exchange_rejects_endpoint_with_path(self) -> None:
        class Collector(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                body = json.dumps(
                    {
                        "token": "wk_login_test_plain_token_0123456789ab",
                        "endpoint": "http://169.254.169.254/latest/meta-data",
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        collector = HTTPServer(("127.0.0.1", 0), Collector)
        collector_url = f"http://127.0.0.1:{collector.server_address[1]}"
        Thread(target=collector.serve_forever, daemon=True).start()
        try:
            token, ep, err = yakka._login_exchange(
                collector_url,
                "devcode",
                "state",
                "http://127.0.0.1:9/callback",
                5.0,
            )
        finally:
            collector.shutdown()
        self.assertIsNotNone(err)
        self.assertEqual(token, "")
        self.assertEqual(ep, "")
        self.assertNotIn("169.254.169.254", str(err))
        self.assertFalse(os.path.exists(self._cfg))


class TestLoginCommandMissingEndpoint(LoginEnv):
    def test_login_command_missing_endpoint(self) -> None:
        proc = subprocess.run(
            [sys.executable, _SCRIPT, "login"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
