"""Disk check for unattended core-skill bootstrap."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
DRIVER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DRIVER))

from check_skills import (  # noqa: E402
    CORE_SKILLS,
    LAB_SKILLS,
    HARNESS_CLAUDE,
    HARNESS_CURSOR,
    HARNESS_INTERACTIVE,
    detect_harness,
    report_for_env,
    scan_core_skills,
)


def _write_skill(root: Path, name: str) -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")


class TestDetectHarness(unittest.TestCase):
    def test_explicit_mode_beats_ambient_signals(self) -> None:
        env = {
            "WORKFLOW_INSTALL_MODE": "cloud",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_REMOTE": "true",
            "HOSTNAME": "not-cursor",
        }
        self.assertEqual(
            detect_harness(env, manifest_present=False, can_prompt=True),
            HARNESS_CURSOR,
        )
        env["WORKFLOW_INSTALL_MODE"] = "claude-code"
        env["CURSOR_AGENT"] = "1"
        env["HOSTNAME"] = "cursor"
        self.assertEqual(
            detect_harness(env, manifest_present=True, can_prompt=False),
            HARNESS_CLAUDE,
        )
        env["WORKFLOW_INSTALL_MODE"] = "interactive"
        self.assertEqual(
            detect_harness(env, manifest_present=True, can_prompt=False),
            HARNESS_INTERACTIVE,
        )

    def test_ambient_claude_before_cursor(self) -> None:
        env = {
            "CLAUDE_CODE_REMOTE": "true",
            "CURSOR_AGENT": "1",
            "HOSTNAME": "cursor",
        }
        self.assertEqual(
            detect_harness(env, manifest_present=True, can_prompt=False),
            HARNESS_CLAUDE,
        )

    def test_cursor_signals_and_noninteractive(self) -> None:
        self.assertEqual(
            detect_harness(
                {"CURSOR_AGENT": "1", "HOSTNAME": "devbox"},
                manifest_present=False,
                can_prompt=True,
            ),
            HARNESS_CURSOR,
        )
        self.assertEqual(
            detect_harness(
                {"HOSTNAME": "cursor"},
                manifest_present=False,
                can_prompt=True,
            ),
            HARNESS_CURSOR,
        )
        self.assertEqual(
            detect_harness(
                {"HOSTNAME": "devbox"},
                manifest_present=True,
                can_prompt=True,
            ),
            HARNESS_CURSOR,
        )
        self.assertEqual(
            detect_harness(
                {"HOSTNAME": "devbox"},
                manifest_present=False,
                can_prompt=False,
            ),
            HARNESS_CURSOR,
        )

    def test_interactive_tty_without_signals(self) -> None:
        self.assertEqual(
            detect_harness(
                {"HOSTNAME": "devbox"},
                manifest_present=False,
                can_prompt=True,
            ),
            HARNESS_INTERACTIVE,
        )

    def test_empty_hostname_is_not_cursor(self) -> None:
        self.assertEqual(
            detect_harness(
                {"HOSTNAME": ""},
                manifest_present=False,
                can_prompt=True,
            ),
            HARNESS_INTERACTIVE,
        )


class TestScan(unittest.TestCase):
    def test_requires_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in CORE_SKILLS:
                _write_skill(root, name)
            (root / "execute").joinpath("SKILL.md").unlink()
            found, missing = scan_core_skills(root)
            self.assertNotIn("execute", found)
            self.assertEqual(missing, ["execute"])

    def test_lab_dirs_do_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in LAB_SKILLS:
                _write_skill(root, name)
            found, missing = scan_core_skills(root)
            self.assertEqual(found, [])
            self.assertEqual(missing, list(CORE_SKILLS))


class TestReport(unittest.TestCase):
    def test_cursor_cloud_ok_without_lab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "repo"
            home = base / "home"
            workspace.mkdir()
            home.mkdir()
            root = workspace / ".cursor" / "skills" / "workflow"
            for name in CORE_SKILLS:
                _write_skill(root, name)
            env = {
                "HOME": str(home),
                "HOSTNAME": "cursor",
                "CURSOR_AGENT": "1",
                "WORKFLOW_WORKSPACE": str(workspace),
            }
            report = report_for_env(env, can_prompt=False)
            self.assertTrue(report["ok"])
            self.assertEqual(report["harness"], HARNESS_CURSOR)
            self.assertEqual(report["skills_found"], list(CORE_SKILLS))
            self.assertEqual(report["missing"], [])
            self.assertEqual(report["skills_root"], str(root.resolve()))

    def test_claude_remote_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            home.mkdir()
            root = home / ".claude" / "skills"
            for name in CORE_SKILLS:
                _write_skill(root, name)
            env = {
                "HOME": str(home),
                "HOSTNAME": "cursor",
                "CURSOR_AGENT": "1",
                "CLAUDE_CODE_REMOTE": "true",
                "WORKFLOW_WORKSPACE": str(base / "unused"),
            }
            report = report_for_env(env, can_prompt=False)
            self.assertTrue(report["ok"])
            self.assertEqual(report["harness"], HARNESS_CLAUDE)
            self.assertEqual(report["skills_root"], str(root.resolve()))
            self.assertEqual(report["missing"], [])

    def test_missing_skills_exit_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "repo"
            home = base / "home"
            workspace.mkdir()
            home.mkdir()
            env = {
                "HOME": str(home),
                "HOSTNAME": "devbox",
                "WORKFLOW_INSTALL_MODE": "cloud",
                "WORKFLOW_WORKSPACE": str(workspace),
            }
            report = report_for_env(env, can_prompt=True)
            self.assertFalse(report["ok"])
            self.assertEqual(report["harness"], HARNESS_CURSOR)
            self.assertEqual(report["skills_found"], [])
            self.assertEqual(report["missing"], list(CORE_SKILLS))

    def test_cli_exit_codes(self) -> None:
        script = DRIVER / "check_skills.py"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "repo"
            home = base / "home"
            workspace.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["HOSTNAME"] = "devbox"
            env["WORKFLOW_INSTALL_MODE"] = "cloud"
            env.pop("CURSOR_AGENT", None)
            env.pop("CLAUDECODE", None)
            env.pop("CLAUDE_CODE_REMOTE", None)
            env.pop("CLAUDE_CODE_ENTRYPOINT", None)
            missing = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(home),
                    "--harness",
                    "cursor-cloud",
                ],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(missing.returncode, 1, missing.stderr)
            payload = json.loads(missing.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["missing"], list(CORE_SKILLS))

            root = workspace / ".cursor" / "skills" / "workflow"
            for name in CORE_SKILLS:
                _write_skill(root, name)
            ok = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace",
                    str(workspace),
                    "--home",
                    str(home),
                    "--harness",
                    "cursor-cloud",
                ],
                cwd=WORKSPACE,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            payload = json.loads(ok.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["skills_found"], list(CORE_SKILLS))


if __name__ == "__main__":
    unittest.main()
