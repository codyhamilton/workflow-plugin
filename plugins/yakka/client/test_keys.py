import os
import subprocess
import tempfile
import unittest

import yakka


class TestNormalizeRemote(unittest.TestCase):
    def test_normalize_remote(self) -> None:
        cases = {
            "git@github.com:a/b.git": "github.com/a/b",
            "https://github.com/a/b": "github.com/a/b",
            "ssh://git@GitHub.com/a/b.git/": "github.com/a/b",
            "https://user:pw@host.example/x/y.git": "host.example/x/y",
            "git@GitHub.com:Org/Repo.git": "github.com/Org/Repo",
            "https://github.com/a/b.git/": "github.com/a/b",
        }
        for inp, want in cases.items():
            self.assertEqual(yakka.NormalizeRemote(inp), want)


class TestCanonicalRowHash(unittest.TestCase):
    def test_canonical_row_hash(self) -> None:
        base = b'{"b":1,"a":{"y":[3,1],"x":"<&>"},"id":"q#1","content":"zzz"}'
        h0, err = yakka.RowHash(base)
        self.assertIsNone(err)
        same = [
            '{ "a" : {"x":"<&>", "y":[3,1]},\n "b":1 }',
            '{"id":"other#9","a":{"x":"<&>","y":[3,1]},"b":1,"content":"different"}',
            '{"a":{"x":"<&>","y":[3,1]},"b":1}',
        ]
        for s in same:
            h, _ = yakka.RowHash(s.encode())
            self.assertEqual(h, h0, msg=s)
        for s in [
            '{"b":2,"a":{"y":[3,1],"x":"<&>"}}',
            '{"b":1,"a":{"y":[1,3],"x":"<&>"}}',
            '{"b":1,"a":{"y":[3,1],"x":"<&>"},"extra":null}',
        ]:
            h, _ = yakka.RowHash(s.encode())
            self.assertNotEqual(h, h0, msg=s)
        c = yakka.Canonical(b'{"n":1.700000000123456789e9,"k":"<>"}')
        self.assertEqual(c.decode(), '{"k":"<>","n":1.700000000123456789e9}')
        for bad in [b"[1]", b'"x"', b"nope", b"{} {}"]:
            with self.assertRaises((ValueError, TypeError)):
                yakka.Canonical(bad)
        self.assertEqual(
            yakka.ContentHash(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )


class TestKind(unittest.TestCase):
    def test_kind(self) -> None:
        cases = {
            "docs/plans/09-x/DESIGN.md": "design",
            "docs/plans/09-x/briefs/1-01.md": "brief",
            "docs/plans/09-x/reports/1-01.md": "report",
            "docs/plans/09-x/briefs/sub/a.md": "",
            "docs/plans/09-x/briefs/a.txt": "",
            "docs/plans/DESIGN.md": "",
            "docs/design/01.md": "",
            "x/docs/plans/09-x/DESIGN.md": "",
        }
        for inp, want in cases.items():
            self.assertEqual(yakka.Kind(inp), want)


def tgit(t: unittest.TestCase, dir_path: str, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        }
    )
    out = subprocess.run(
        ["git", *args],
        cwd=dir_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip()


def new_repo(t: unittest.TestCase) -> str:
    os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"
    os.environ["GIT_CONFIG_SYSTEM"] = "/dev/null"
    d = os.path.realpath(tempfile.mkdtemp())
    tgit(t, d, "init", "-q", "-b", "main")
    tgit(t, d, "commit", "-q", "--allow-empty", "-m", "root")
    return d


class TestRepoID(unittest.TestCase):
    def test_repo_id(self) -> None:
        a, b = new_repo(self), new_repo(self)
        tgit(self, a, "remote", "add", "origin", "git@github.com:a/b.git")
        tgit(self, b, "remote", "add", "origin", "https://github.com/a/b")
        ia, err = yakka.RepoID(a)
        self.assertIsNone(err)
        ib, _ = yakka.RepoID(b)
        self.assertEqual(ia, "github.com/a/b")
        self.assertEqual(ia, ib)

        tgit(self, a, "remote", "add", "aaa", "https://other.example/z")
        id_a, _ = yakka.RepoID(a)
        self.assertEqual(id_a, "github.com/a/b")

        c = new_repo(self)
        tgit(self, c, "remote", "add", "upstream", "https://Up.example/u/v.git")
        id_c, _ = yakka.RepoID(c)
        self.assertEqual(id_c, "up.example/u/v")

        d = new_repo(self)
        root = tgit(self, d, "rev-list", "--max-parents=0", "HEAD")
        id_d, _ = yakka.RepoID(d)
        self.assertEqual(id_d, "root:" + root)

        wt = os.path.join(tempfile.mkdtemp(), "wt")
        tgit(self, a, "worktree", "add", "-q", "-b", "other", wt)
        id_wt, err = yakka.RepoID(wt)
        self.assertIsNone(err)
        self.assertEqual(id_wt, "github.com/a/b")

        e = new_repo(self)
        wt2 = os.path.join(tempfile.mkdtemp(), "wt")
        tgit(self, e, "worktree", "add", "-q", "-b", "other", wt2)
        i1, _ = yakka.RepoID(e)
        i2, _ = yakka.RepoID(wt2)
        self.assertEqual(i1, i2)
        self.assertTrue(i1.startswith("root:"))


class TestRepoPath(unittest.TestCase):
    def test_repo_path(self) -> None:
        d = new_repo(self)
        os.makedirs(os.path.join(d, "docs", "plans", "p"), exist_ok=True)
        f = os.path.join(d, "docs", "plans", "p", "DESIGN.md")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("x")
        top, rel, ok, err = yakka.RepoPath(f)
        self.assertIsNone(err)
        self.assertTrue(ok)
        self.assertEqual(top, d)
        self.assertEqual(rel, "docs/plans/p/DESIGN.md")

        link = os.path.join(tempfile.mkdtemp(), "link")
        os.symlink(d, link)
        _, rel, ok, _ = yakka.RepoPath(
            os.path.join(link, "docs", "plans", "p", "DESIGN.md")
        )
        self.assertTrue(ok)
        self.assertEqual(rel, "docs/plans/p/DESIGN.md")

        out = tempfile.mkdtemp()
        with open(os.path.join(out, "a.md"), "w", encoding="utf-8") as fh:
            fh.write("x")
        _, _, ok, err = yakka.RepoPath(os.path.join(out, "a.md"))
        self.assertFalse(ok)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
