"""install.sh route detection and core-only unattended copy. No network."""

from __future__ import annotations

import json
import os
import pty
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
DRIVER = Path(__file__).resolve().parents[1]
INSTALL = WORKSPACE / "install.sh"
BOOTSTRAP = WORKSPACE / "docs" / "lab" / "bootstrap"
CLOUD_BOOTSTRAP = WORKSPACE / "tools" / "cloud-env" / "bootstrap-workflow-skills.sh"
sys.path.insert(0, str(DRIVER))

from check_skills import CORE_SKILLS, LAB_SKILLS, report_for_env  # noqa: E402


def _base_env(home: Path, **extra: str) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "HOSTNAME": "devbox",
        "WORKFLOW_INSTALL_SKIP_REFRESH": "1",
    }
    for key in (
        "CURSOR_AGENT",
        "CLAUDECODE",
        "CLAUDE_CODE_REMOTE",
        "CLAUDE_CODE_ENTRYPOINT",
        "WORKFLOW_INSTALL_MODE",
        "WORKFLOW_WORKSPACE",
    ):
        env.pop(key, None)
    env.update(extra)
    return env


def _dev_tty_opens() -> bool:
    try:
        fd = os.open("/dev/tty", os.O_RDONLY)
    except OSError:
        return False
    os.close(fd)
    return True


def _run_route(env: dict[str, str], *, tty: bool = False) -> subprocess.CompletedProcess[str]:
    if not tty:
        return subprocess.run(
            ["bash", str(INSTALL), "--print-route"],
            cwd=WORKSPACE,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            ["bash", str(INSTALL), "--print-route"],
            cwd=WORKSPACE,
            env=env,
            stdin=slave,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        os.close(slave)
        slave = -1
        out, err = proc.communicate(timeout=30)
    finally:
        if slave != -1:
            os.close(slave)
        os.close(master)
    return subprocess.CompletedProcess(
        args=["bash", str(INSTALL), "--print-route"],
        returncode=proc.returncode,
        stdout=out,
        stderr=err,
    )


class TestPrintRoute(unittest.TestCase):
    def test_print_route_does_not_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            cache = Path(tmp) / "cache"
            env = _base_env(
                home,
                WORKFLOW_INSTALL_SRC=str(cache),
                WORKFLOW_INSTALL_MODE="cloud",
                WORKFLOW_WORKSPACE=str(Path(tmp) / "ws"),
            )
            (Path(tmp) / "ws").mkdir()
            proc = _run_route(env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(cache.exists())
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["route"], "cursor-cloud")
            self.assertTrue(payload["core_only"])
            self.assertTrue(str(payload["dest"]).endswith("/.cursor/skills/workflow"))

    def test_explicit_cloud_beats_claude_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="cloud",
                WORKFLOW_WORKSPACE=str(ws),
                CLAUDECODE="1",
                CLAUDE_CODE_REMOTE="true",
                HOSTNAME="cursor",
            )
            payload = json.loads(_run_route(env).stdout)
            self.assertEqual(payload["route"], "cursor-cloud")
            self.assertIn(str(ws), payload["dest"])
            self.assertNotIn(".claude/skills", payload["dest"])

    def test_explicit_opencode_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            opencode_skills = home / ".config" / "opencode" / "skills"
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="opencode",
                WORKFLOW_OPENCODE_SKILLS=str(opencode_skills),
            )
            proc = _run_route(env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["route"], "opencode")
            self.assertTrue(payload["core_only"])
            self.assertEqual(payload["dest"], str(opencode_skills))
            self.assertEqual(payload["reason"], "WORKFLOW_INSTALL_MODE=opencode")

    def test_explicit_claude_beats_cursor_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="claude-code",
                CURSOR_AGENT="1",
                HOSTNAME="cursor",
            )
            payload = json.loads(_run_route(env).stdout)
            self.assertEqual(payload["route"], "claude-code")
            self.assertEqual(payload["dest"], str(home / ".claude" / "skills"))
            self.assertTrue(payload["core_only"])

    def test_ambient_claude_remote_before_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = _base_env(
                home,
                CLAUDE_CODE_REMOTE="true",
                CURSOR_AGENT="1",
                HOSTNAME="cursor",
            )
            payload = json.loads(_run_route(env).stdout)
            self.assertEqual(payload["route"], "claude-code")
            self.assertEqual(payload["reason"], "CLAUDE_CODE_REMOTE=true")

    def test_noninteractive_without_signals_is_cursor_workspace(self) -> None:
        if _dev_tty_opens():
            self.skipTest("/dev/tty is open; install.sh treats that as interactive")
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            env = _base_env(home, WORKFLOW_WORKSPACE=str(ws), HOSTNAME="devbox")
            proc = _run_route(env, tty=False)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["route"], "cursor-cloud")
            self.assertEqual(payload["reason"], "non-interactive shell")
            self.assertTrue(payload["core_only"])

    def test_tty_without_signals_is_interactive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = _base_env(home, HOSTNAME="devbox")
            proc = _run_route(env, tty=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["route"], "interactive")
            self.assertFalse(payload["core_only"])
            self.assertIsNone(payload["dest"])

    def test_tty_manifest_is_cursor_cloud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            manifest = home / ".cursor" / "plugins" / "cache"
            manifest.mkdir(parents=True)
            (manifest / ".cloud-plugin-manifest.json").write_text("{}", encoding="utf-8")
            ws.mkdir()
            env = _base_env(
                home,
                HOSTNAME="devbox",
                WORKFLOW_WORKSPACE=str(ws),
            )
            payload = json.loads(_run_route(env, tty=True).stdout)
            self.assertEqual(payload["route"], "cursor-cloud")
            self.assertEqual(payload["reason"], "cloud plugin manifest present")

    def test_route_matches_check_skills_harness(self) -> None:
        cases = [
            {"WORKFLOW_INSTALL_MODE": "cloud", "CLAUDECODE": "1", "HOSTNAME": "devbox"},
            {"WORKFLOW_INSTALL_MODE": "claude-code", "CURSOR_AGENT": "1", "HOSTNAME": "cursor"},
            {"CLAUDE_CODE_REMOTE": "true", "CURSOR_AGENT": "1", "HOSTNAME": "cursor"},
            {"CURSOR_AGENT": "1", "HOSTNAME": "devbox"},
            {"HOSTNAME": "cursor"},
            {"HOSTNAME": "devbox"},
            {"WORKFLOW_INSTALL_MODE": "interactive", "CURSOR_AGENT": "1", "HOSTNAME": "cursor"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            for extra in cases:
                env = _base_env(home, WORKFLOW_WORKSPACE=str(ws), **extra)
                proc = _run_route(env, tty=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                route = json.loads(proc.stdout)["route"]
                # Piped stdin is not a TTY. install.sh still prompts when /dev/tty opens.
                report = report_for_env(env, can_prompt=_dev_tty_opens())
                self.assertEqual(
                    report["harness"],
                    route,
                    msg=f"env={extra} route={route} report={report}",
                )


class TestCoreOnlyInstall(unittest.TestCase):
    def test_cloud_install_copies_core_not_lab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="cloud",
                WORKFLOW_WORKSPACE=str(ws),
                CURSOR_AGENT="1",
                HOSTNAME="cursor",
                CLAUDECODE="1",
            )
            proc = subprocess.run(
                ["bash", str(INSTALL)],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            root = ws / ".cursor" / "skills" / "workflow"
            for name in CORE_SKILLS:
                self.assertTrue((root / name / "SKILL.md").is_file(), name)
            for name in LAB_SKILLS:
                self.assertFalse((root / name).exists(), name)
            self.assertFalse((home / ".claude" / "skills").exists())
            report = report_for_env(env, can_prompt=False)
            self.assertTrue(report["ok"])
            self.assertEqual(report["missing"], [])

    def test_claude_mode_does_not_write_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="claude-code",
                WORKFLOW_WORKSPACE=str(ws),
                CURSOR_AGENT="1",
                HOSTNAME="cursor",
            )
            proc = subprocess.run(
                ["bash", str(INSTALL)],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            root = home / ".claude" / "skills"
            for name in CORE_SKILLS:
                self.assertTrue((root / name / "SKILL.md").is_file(), name)
            for name in LAB_SKILLS:
                self.assertFalse((root / name).exists(), name)
            self.assertFalse((ws / ".cursor").exists())


class TestOpenCodeSymlinkInstall(unittest.TestCase):
    def test_opencode_install_symlinks_core_not_lab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            opencode_skills = home / ".config" / "opencode" / "skills"
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="opencode",
                WORKFLOW_OPENCODE_SKILLS=str(opencode_skills),
            )
            proc = subprocess.run(
                ["bash", str(INSTALL), "--opencode-skills"],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            for name in CORE_SKILLS:
                link = opencode_skills / name
                self.assertTrue(link.is_symlink(), name)
                self.assertTrue((link / "SKILL.md").is_file(), name)
                self.assertTrue(
                    str(link.resolve()).startswith(str(WORKSPACE.resolve())),
                    f"{name} should point into checkout",
                )
            for name in LAB_SKILLS:
                lab_link = opencode_skills / name
                self.assertFalse(lab_link.exists(), name)

    def test_opencode_install_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            opencode_skills = home / ".config" / "opencode" / "skills"
            env = _base_env(
                home,
                WORKFLOW_INSTALL_MODE="opencode",
                WORKFLOW_OPENCODE_SKILLS=str(opencode_skills),
            )
            for _ in range(2):
                proc = subprocess.run(
                    ["bash", str(INSTALL)],
                    cwd=WORKSPACE,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertEqual(
                len(list(opencode_skills.iterdir())),
                len(CORE_SKILLS),
            )


class TestBootstrapArtifacts(unittest.TestCase):
    def test_session_start_matches_readme_heredoc(self) -> None:
        readme = (WORKSPACE / "README.md").read_text(encoding="utf-8")
        start = readme.index("<<'EOF'\n") + len("<<'EOF'\n")
        end = readme.index("\nEOF", start)
        embedded = readme[start:end] + "\n"
        on_disk = (BOOTSTRAP / "session-start.sh").read_text(encoding="utf-8")
        self.assertEqual(embedded, on_disk)

    def test_settings_fragment_matches_readme(self) -> None:
        fragment = json.loads(
            (BOOTSTRAP / "claude-settings-fragment.json").read_text(encoding="utf-8")
        )
        command = fragment["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        readme = (WORKSPACE / "README.md").read_text(encoding="utf-8")
        self.assertIn(command, readme)
        self.assertIn("reloadSkills", (BOOTSTRAP / "session-start.sh").read_text(encoding="utf-8"))

    def test_session_start_noop_without_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            marker = Path(tmp) / "curled"
            curl = bindir / "curl"
            curl.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    echo curled >> {marker}
                    exit 99
                    """
                ),
                encoding="utf-8",
            )
            curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
            bash = shutil.which("bash") or "/bin/bash"
            env = os.environ.copy()
            env.pop("CLAUDE_CODE_REMOTE", None)
            env["PATH"] = str(bindir)
            proc = subprocess.run(
                [bash, str(BOOTSTRAP / "session-start.sh")],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout, "")
            self.assertFalse(marker.exists())

    def test_session_start_remote_emits_reload_and_curls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            marker = Path(tmp) / "curled"
            curl = bindir / "curl"
            curl.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    echo curled >> {marker}
                    echo 'echo STUB_INSTALLER'
                    exit 0
                    """
                ),
                encoding="utf-8",
            )
            curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
            env = os.environ.copy()
            env["CLAUDE_CODE_REMOTE"] = "true"
            env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
            proc = subprocess.run(
                ["bash", str(BOOTSTRAP / "session-start.sh")],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["hookSpecificOutput"]["reloadSkills"])
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertTrue(marker.exists())
            self.assertIn("STUB_INSTALLER", proc.stderr)

    def test_cursor_setup_uses_local_installer_core_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            marker = Path(tmp) / "used-local"
            wrapper = Path(tmp) / "wrap.sh"
            wrapper.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/bash
                    echo local > {marker}
                    exec bash {INSTALL}
                    """
                ),
                encoding="utf-8",
            )
            wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
            env = _base_env(home, HOSTNAME="devbox", CLAUDECODE="1")
            env["WORKFLOW_INSTALL_SH"] = str(wrapper)
            # Setup script sets MODE=cloud and WORKFLOW_WORKSPACE itself.
            env.pop("WORKFLOW_INSTALL_MODE", None)
            env.pop("WORKFLOW_WORKSPACE", None)
            proc = subprocess.run(
                ["bash", str(BOOTSTRAP / "cursor-cloud-setup.sh")],
                cwd=ws,
                env={**env, "WORKFLOW_WORKSPACE": str(ws)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertTrue(marker.is_file())
            root = ws / ".cursor" / "skills" / "workflow"
            for name in CORE_SKILLS:
                self.assertTrue((root / name / "SKILL.md").is_file(), name)
            for name in LAB_SKILLS:
                self.assertFalse((root / name).exists(), name)

    def test_cloud_bootstrap_uses_local_installer_core_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "ws"
            home.mkdir()
            ws.mkdir()
            marker = Path(tmp) / "used-local"
            wrapper = Path(tmp) / "wrap.sh"
            wrapper.write_text(
                textwrap.dedent(
                    f"""\
                    #!/bin/bash
                    echo local > {marker}
                    exec bash {INSTALL}
                    """
                ),
                encoding="utf-8",
            )
            wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
            env = _base_env(home, HOSTNAME="devbox", CLAUDECODE="1")
            env["WORKFLOW_INSTALL_SH"] = str(wrapper)
            env.pop("WORKFLOW_INSTALL_MODE", None)
            env.pop("WORKFLOW_WORKSPACE", None)
            proc = subprocess.run(
                ["bash", str(CLOUD_BOOTSTRAP)],
                cwd=ws,
                env={**env, "WORKFLOW_WORKSPACE": str(ws)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertTrue(marker.is_file())
            root = ws / ".cursor" / "skills" / "workflow"
            for name in CORE_SKILLS:
                self.assertTrue((root / name / "SKILL.md").is_file(), name)
            for name in LAB_SKILLS:
                self.assertFalse((root / name).exists(), name)

    def test_cursor_setup_delegates_to_cloud_bootstrap(self) -> None:
        legacy = (BOOTSTRAP / "cursor-cloud-setup.sh").read_text(encoding="utf-8")
        self.assertIn("tools/cloud-env/bootstrap-workflow-skills.sh", legacy)
        self.assertIn("exec bash", legacy)


if __name__ == "__main__":
    unittest.main()
