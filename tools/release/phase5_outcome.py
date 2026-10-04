#!/usr/bin/env python3
"""Phase 5 outcome gate: one `outcome <clause> PASS|FAIL` line per clause; non-zero on any FAIL."""
import os
import pwd
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REAL_HOME = pwd.getpwuid(os.getuid()).pw_dir
GOBIN = os.path.join(REAL_HOME, ".local/go/bin")
RETIRED = re.compile(r"drain\.py|install-drain|workflow-hooklog-drain|artifact_submit|--harness auto|"
                     r"127\.0\.0\.1:8765/mcp|WORKFLOW_ARTIFACT_SUBMIT_CLI")


def sh(cmd, cwd=ROOT, **extra):
    """Run a check with temp HOME/cache/queue/data and a blank API key; return True on exit 0."""
    with tempfile.TemporaryDirectory(prefix="p5out.") as t:
        env = dict(os.environ, HOME=t + "/home", XDG_CACHE_HOME=t + "/cache", WORKFLOW_QUEUE=t + "/queue",
                   WORKFLOW_SERVE_DATA=t + "/data", TYPESAFE_API_KEY="", **extra)
        env.pop("WORKFLOW_BIN", None)
        for d in ("home", "cache", "data"):
            os.makedirs(t + "/" + d)
        # tests that probe $HOME/.local/go/bin find Go through a symlink in the temp HOME
        os.makedirs(t + "/home/.local")
        os.symlink(os.path.dirname(GOBIN), t + "/home/.local/go")
        gocache = subprocess.run([GOBIN + "/go", "env", "GOCACHE"], capture_output=True, text=True,
                               env=dict(os.environ, HOME=REAL_HOME)).stdout.strip()
        gomod = subprocess.run([GOBIN + "/go", "env", "GOMODCACHE"], capture_output=True, text=True,
                               env=dict(os.environ, HOME=REAL_HOME)).stdout.strip()
        env.update(GOCACHE=gocache, GOMODCACHE=gomod, PATH=GOBIN + ":" + env["PATH"])
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        if r.returncode:
            sys.stderr.write("--- %s\n%s%s\n" % (" ".join(cmd), r.stdout[-1500:], r.stderr[-1500:]))
        return r.returncode == 0


def unittest_cmd(file, *names):
    return [sys.executable, "-m", "unittest", "-v"] + ["%s.%s" % (file, n) for n in names]


def no_retired_refs():
    paths = [ROOT / "hooks", ROOT / ".mcp.json", ROOT / "tools/hooklog/README.md", ROOT / "bin",
             ROOT / "tools/release", ROOT / "packages/opencode-workflow-hooks/src",
             ROOT / "packages/opencode-workflow-hooks/README.md",
             ROOT / "packages/opencode-workflow-hooks/opencode.json.example"]
    for pat in ("*.json", "*.sh", "*.example.*"):
        paths += (ROOT / "tools/hooklog").glob(pat)
    files = []
    for p in paths:
        if p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts and "dist" not in f.parts]
        elif p.is_file():
            files.append(p)
    hits = []
    for f in set(files):
        if f.name == "phase5_outcome.py":
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if RETIRED.search(line):
                hits.append("%s:%d" % (f.relative_to(ROOT), i))
    for h in sorted(hits):
        sys.stderr.write("retired ref: %s\n" % h)
    return not hits


def retired_files_gone():
    names = ["tools/hooklog/drain.py", "tools/hooklog/install-drain.sh",
             "tools/hooklog/workflow-hooklog-drain.service", "tools/hooklog/workflow-hooklog-drain.timer"]
    return not any((ROOT / n).exists() for n in names)


def main():
    rel = "tools/release/test_release.py"
    clauses = [
        ("version-clean-build", lambda: sh(unittest_cmd("tools.release.test_release", "WrapperTests.test_1_clean_cache_build"))),
        ("concurrent-first-runs", lambda: sh(unittest_cmd("tools.release.test_release", "WrapperTests.test_2_concurrent"))),
        ("release-build", lambda: sh(unittest_cmd("tools.release.test_release", "BuildTests.test_7_build_sh"))),
        ("init", lambda: sh(["go", "test", "-count=1", "-run", "TestInit", "./..."], cwd=ROOT / "tools/workflow")),
        ("write-replay", lambda: sh([sys.executable, "-m", "unittest", "-v", "tools.hooklog.tests.test_write_surfaces"])),
        ("no-retired-refs", no_retired_refs),
        ("retired-files-gone", retired_files_gone),
    ]
    failed = False
    for name, fn in clauses:
        ok = fn()
        failed |= not ok
        print("outcome %s %s" % (name, "PASS" if ok else "FAIL"), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
