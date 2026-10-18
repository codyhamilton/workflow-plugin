import os
import subprocess
import unittest

import yakka


def rep(s: str, n: int) -> str:
    return s * n


def samples() -> dict[str, str]:
    return {
        "private_key_block": (
            "-----"
            + "BEGIN RSA PRIVATE"
            + " KEY-----\nMIIB\n-----"
            + "END RSA PRIVATE KEY-----"
        ),
        "sk_key": "key is sk" + "-" + rep("a1", 12),
        "github_token": "tok gh" + "p_" + rep("A1", 12),
        "github_pat": "tok github" + "_pat_" + rep("A1", 15),
        "aws_access_key": "id AK" + "IA" + rep("7Q", 8),
        "slack_token": "x xo" + "xb-" + rep("12", 8),
        "google_api_key": "k AI" + "za" + rep("Ab_", 12)[:35],
        "stripe_key": "k sk" + "_live_" + rep("a9", 10),
        "jwt": (
            "t ey"
            + "J"
            + rep("a", 12)
            + "."
            + rep("b", 12)
            + "."
            + rep("c", 12)
        ),
        "bearer_token": "Authorization: Bear" + "er " + rep("Ab1", 8),
        "connection_string": (
            "db postgres" + "://admin:" + "s3cr3tpass" + "@db.example:5432/x"
        ),
        "env_assignment": "MY_API_" + "KEY=" + "abcd1234efgh",
        "workflow_api_token": "tok wk" + "_" + rep("a1", 16),
    }


class TestScanPatterns(unittest.TestCase):
    def test_scan_patterns(self) -> None:
        names = {n: True for n in yakka.Patterns()}
        for name, s in samples().items():
            self.assertIn(name, names)
            text = "line one\nline two\n" + s + "\nline four"
            line = 3
            hits = yakka.Scan(text)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].Pattern, name)
            self.assertEqual(hits[0].Line, line)
            red = yakka.Redact(text)
            self.assertIn(f"[REDACTED:{name}]", red)
            self.assertNotIn(s, red)
            self.assertEqual(len(yakka.Scan(red)), 0)
        self.assertEqual(len(names), len(samples()))


class TestScanLinesAndOrder(unittest.TestCase):
    def test_scan_lines_and_order(self) -> None:
        sm = samples()
        text = sm["sk_key"] + "\n\n" + sm["jwt"] + "\nok\n" + sm["env_assignment"]
        hits = yakka.Scan(text)
        want = [
            yakka.Hit("sk_key", 1),
            yakka.Hit("jwt", 3),
            yakka.Hit("env_assignment", 5),
        ]
        self.assertEqual(len(hits), len(want))
        for i, w in enumerate(want):
            self.assertEqual(hits[i], w)
        pk = "a\nb\n" + sm["private_key_block"]
        h = yakka.Scan(pk)
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0].Line, 3)


class TestPlaceholdersDoNotHit(unittest.TestCase):
    def test_placeholders_do_not_hit(self) -> None:
        for s in [
            "YAKKA_SERVE_KEYS=a=ka,b=kb",
            "YAKKA_SERVE_KEYS=aaaaaaaaaaaaaaaa",
            "API_KEY=short",
            "API_KEY=$OTHER_VARIABLE",
            "API_KEY=<your-key-here>",
            "API_KEY={{ secret }}",
            "API_KEY=…",
            "API_KEY=...",
            "API_KEY=********",
            "API_KEY=xxxxxxxxxxxx",
            'API_KEY: "xxxxxxxxxxxx"',
            "SECRET_TOKEN: <redacted-value>",
            "db://user:<password>@host/x",
            "db://user:$PASSWORD@host/x",
            "db://user:xxxxxxxx@host/x",
            "the task-force-with-a-long-name-here and ask-me-anything-about-it",
            "Bearer <token>",
            "plain prose about a token and a password",
        ]:
            self.assertEqual(yakka.Scan(s), [], msg=s)


class TestRepoDocsClean(unittest.TestCase):
    def test_repo_docs_clean(self) -> None:
        here = os.path.dirname(__file__)
        try:
            out = subprocess.run(
                ["git", "ls-files", "-z", "*.md"],
                check=True,
                capture_output=True,
                cwd=here,
            )
            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
                cwd=here,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("not inside a git repo")
        root = top.stdout.strip()
        bad: list[str] = []
        for f in out.stdout.split(b"\x00"):
            if not f:
                continue
            path = os.path.join(root, f.decode())
            try:
                with open(path, encoding="utf-8") as fh:
                    b = fh.read()
            except OSError:
                continue
            for h in yakka.Scan(b):
                bad.append(f"{f.decode()}:{h.Line} {h.Pattern}")
        self.assertEqual(bad, [])


def env_hits(text: str) -> list[yakka.Hit]:
    return [h for h in yakka.Scan(text) if h.Pattern == "env_assignment"]


class TestEnvAssignmentProse(unittest.TestCase):
    def test_env_assignment_prose(self) -> None:
        for s in [
            "Trailer key: `Workflow-Phase:`",
            "No key: `Options.ScreenStep`",
            "secret: aws_access_key at line 3",
            "- secret: aws_access_key at line 3",
            "The api_key: configured-in-the-environment-1",
            "Use the token: Workflow-Phase-Trailer-Name",
        ]:
            self.assertEqual(env_hits(s), [], msg=s)


class TestEnvAssignmentPositives(unittest.TestCase):
    def test_env_assignment_positives(self) -> None:
        for s in [
            "API_" + "KEY=abcd1234efgh",
            'export GITHUB_' + 'TOKEN="abcd1234efgh5678"',
            "run: export DB_" + "PASSWORD=hunter2hunter2",
            '{"client_' + 'secret": "abcd1234efgh5678wxyz"}',
            "client_" + "secret: abcd1234efgh5678wxyz",
            "- api_" + "key: abcd1234efgh5678wxyz",
        ]:
            self.assertEqual(len(env_hits(s)), 1, msg=s)


class TestEnvAssignmentCorpus(unittest.TestCase):
    def test_env_assignment_corpus(self) -> None:
        base = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        bad: list[str] = []
        seen = 0
        for sub in ("docs/plans", "docs/design"):
            d = os.path.join(base, sub)
            if not os.path.isdir(d):
                continue
            for dirpath, _, filenames in os.walk(d):
                for name in filenames:
                    if not name.endswith(".md"):
                        continue
                    path = os.path.join(dirpath, name)
                    try:
                        with open(path, encoding="utf-8") as fh:
                            b = fh.read()
                    except OSError:
                        continue
                    seen += 1
                    lines = b.split("\n")
                    for h in env_hits(b):
                        line = lines[h.Line - 1]
                        if "TYPESAFE_API_" + "KEY=sentinel" in line or (
                            "API_" + "KEY=abcd1234efgh" in line
                        ):
                            continue
                        bad.append(f"{path}:{h.Line}")
        if seen == 0:
            self.skipTest("no docs corpus present")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
