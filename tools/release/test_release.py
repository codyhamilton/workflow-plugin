import hashlib
import os
import pwd
import re
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WRAPPER = os.path.join(ROOT, "bin", "workflow")
BUILD = os.path.join(ROOT, "tools", "release", "build.sh")
GOBIN = os.path.expanduser("~/.local/go/bin")
VERSION = "0.1.0"
SYS_PATH = "/usr/bin:/bin"
LINE = re.compile(r"^workflow 0\.1\.0 [0-9a-f]{12}$")


def goenv(name):
    # Ask with the real home so a caller's temp HOME does not move the caches.
    env = dict(os.environ, HOME=pwd.getpwuid(os.getuid()).pw_dir)
    out = subprocess.run([os.path.join(GOBIN, "go"), "env", name], capture_output=True, text=True, env=env)
    return out.stdout.strip()


def plat():
    os_ = {"Linux": "linux", "Darwin": "darwin"}[os.uname().sysname]
    m = os.uname().machine
    arch = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}[m]
    return os_, arch


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reltest.")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.cache = os.path.join(self.tmp, "cache")
        os.makedirs(self.home)
        os.makedirs(self.cache)
        self.os, self.arch = plat()
        self.bin_name = "workflow-%s-%s" % (self.os, self.arch)
        self.vdir = os.path.join(self.cache, "workflow", VERSION)

    def env(self, go=True, **extra):
        path = (GOBIN + ":" + SYS_PATH) if go else SYS_PATH
        e = {"HOME": self.home, "XDG_CACHE_HOME": self.cache, "PATH": path,
             "TYPESAFE_API_KEY": "", "GOCACHE": goenv("GOCACHE"),
             "GOMODCACHE": goenv("GOMODCACHE")}
        for k in ("TMPDIR", "GOTMPDIR"):  # let a full /tmp be avoided
            if os.environ.get(k):
                e[k] = os.environ[k]
        e.update(extra)
        return e

    def run_wrapper(self, args=("--version",), wrapper=WRAPPER, **kw):
        return subprocess.run(["bash", wrapper] + list(args), env=self.env(**kw),
                              capture_output=True, text=True, timeout=400)

    def built(self):
        return os.path.join(self.vdir, self.bin_name)

    def fake_root(self, sums_for=None):
        root = os.path.join(self.tmp, "root")
        shutil.copytree(os.path.join(ROOT, "bin"), os.path.join(root, "bin"))
        return root

    def release_dir(self, binary, flip=False):
        rel = os.path.join(self.tmp, "rel")
        os.makedirs(os.path.join(rel, "v" + VERSION))
        data = open(binary, "rb").read()
        sums = hashlib.sha256(data).hexdigest()
        if flip:
            data = data[:-1] + bytes([data[-1] ^ 1])
        open(os.path.join(rel, "v" + VERSION, self.bin_name), "wb").write(data)
        root = self.fake_root()
        open(os.path.join(root, "bin", "SHA256SUMS"), "w").write("%s  %s\n" % (sums, self.bin_name))
        return rel, root


class WrapperTests(Base):
    def test_1_clean_cache_build(self):
        t = time.time()
        r = self.run_wrapper()
        print("cold build seconds: %.1f" % (time.time() - t))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), LINE)
        self.assertTrue(os.access(self.built(), os.X_OK))
        m = os.stat(self.built()).st_mtime_ns
        r2 = self.run_wrapper()
        self.assertEqual(r2.stdout, r.stdout)
        self.assertEqual(os.stat(self.built()).st_mtime_ns, m)

    def test_2_concurrent(self):
        ps = [subprocess.Popen(["bash", WRAPPER, "--version"], env=self.env(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
              for _ in range(2)]
        outs = [p.communicate(timeout=400) for p in ps]
        for p, (o, e) in zip(ps, outs):
            self.assertEqual(p.returncode, 0, e)
            self.assertRegex(o.strip(), LINE)
        self.assertEqual(outs[0][0], outs[1][0])
        left = [n for n in os.listdir(self.vdir) if n.startswith("tmp.") or n == ".build.lock"]
        self.assertEqual(left, [])

    def test_3_stale_lock(self):
        lock = os.path.join(self.vdir, ".build.lock")
        os.makedirs(lock)
        p = subprocess.Popen(["true"])
        p.wait()
        open(os.path.join(lock, "pid"), "w").write(str(p.pid))
        r = self.run_wrapper()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), LINE)

    def test_4_file_download(self):
        r = self.run_wrapper()  # build a real binary first
        self.assertEqual(r.returncode, 0, r.stderr)
        built_copy = os.path.join(self.tmp, "built")
        shutil.copy(self.built(), built_copy)
        shutil.rmtree(self.vdir)
        rel, root = self.release_dir(built_copy)
        r = self.run_wrapper(wrapper=os.path.join(root, "bin", "workflow"), go=False,
                             WORKFLOW_RELEASE_URL="file://" + rel)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), LINE)
        self.assertTrue(os.path.exists(self.built()))

    def test_5_mismatch(self):
        r = self.run_wrapper()
        built_copy = os.path.join(self.tmp, "built")
        shutil.copy(self.built(), built_copy)
        shutil.rmtree(self.vdir)
        rel, root = self.release_dir(built_copy, flip=True)
        r = self.run_wrapper(wrapper=os.path.join(root, "bin", "workflow"), go=False,
                             WORKFLOW_RELEASE_URL="file://" + rel)
        self.assertIn("checksum mismatch", r.stderr)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(self.built()))
        self.assertEqual([n for n in os.listdir(self.vdir) if n.startswith("tmp.")], [])

    def test_6_no_go_no_asset(self):
        r = self.run_wrapper(go=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no release asset and no Go toolchain", r.stderr)

    def test_9_probe_home_go(self):
        d = os.path.join(self.home, ".local", "go", "bin")
        os.makedirs(d)
        os.symlink(os.path.join(GOBIN, "go"), os.path.join(d, "go"))
        r = self.run_wrapper(go=False, GOROOT=goenv("GOROOT"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.strip(), LINE)

    def test_10_workflow_bin(self):
        stub = os.path.join(self.tmp, "stub")
        open(stub, "w").write("#!/bin/sh\necho stub $WORKFLOW_ROOT $1\n")
        os.chmod(stub, 0o755)
        r = self.run_wrapper(go=False, WORKFLOW_BIN=stub)
        self.assertEqual(r.stdout.strip(), "stub %s --version" % ROOT)

    def test_8_bash32_lint(self):
        src = open(WRAPPER).read()
        for pat in ["read -N", "mapfile", ",,}", "EPOCHREALTIME", "flock", "[[ -v"]:
            self.assertNotIn(pat, src)


class BuildTests(Base):
    def test_7_build_sh(self):
        out = os.path.join(self.tmp, "dist")
        sums = os.path.join(self.tmp, "SUMS")
        r = subprocess.run(["bash", BUILD], env=self.env(OUT_DIR=out, SUMS_FILE=sums),
                           capture_output=True, text=True, timeout=600, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        names = sorted(os.listdir(out))
        self.assertEqual(names, ["workflow-darwin-amd64", "workflow-darwin-arm64",
                                 "workflow-linux-amd64", "workflow-linux-arm64"])
        lines = open(sums).read().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual([l.split("  ")[1] for l in lines], names)
        c = subprocess.run(["sha256sum", "-c", sums], cwd=out, capture_output=True, text=True)
        # sums hold bare names; check in OUT_DIR
        self.assertEqual(c.returncode, 0, c.stderr)
        for n in names:
            magic = open(os.path.join(out, n), "rb").read(4)
            if "linux" in n:
                self.assertEqual(magic, b"\x7fELF")
            else:
                self.assertIn(magic, (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"))


if __name__ == "__main__":
    unittest.main()
