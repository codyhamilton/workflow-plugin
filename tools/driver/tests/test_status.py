"""Tests for tools/driver phase status resolution."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
DRIVER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DRIVER))

from resolve import (  # noqa: E402
    collect_trailers,
    phase_count_from_design,
    resolve_plan_folder,
    resolve_status,
    slug_from_plan_dir,
)
from fixtures import (  # noqa: E402
    FIXTURE_SLUG,
    commit_trailer,
    init_fixture_repo,
)


class TestParsing(unittest.TestCase):
    def test_slug_from_dir(self) -> None:
        self.assertEqual(
            slug_from_plan_dir(Path("docs/plans/06-phase-driver")),
            "phase-driver",
        )

    def test_phase_count(self) -> None:
        text = "### Phase 1 — a\n\n### Phase 2 — b\n"
        self.assertEqual(phase_count_from_design(text), 2)

    def test_malformed_trailers_ignored(self) -> None:
        slug = "fixture-plan"
        lines = [
            "other-slug:1",
            f"{slug}:not-a-number",
            f"{slug}:0",
            f"{slug}:99",
            "garbage",
            f"{slug}:done-extra",
        ]
        closed, done = collect_trailers(lines, slug, phase_count=3)
        self.assertEqual(closed, set())
        self.assertFalse(done)

    def test_valid_trailers(self) -> None:
        slug = "fixture-plan"
        lines = [f"{slug}:1", f"{slug}:3", "wrong:2", f"{slug}:done"]
        closed, done = collect_trailers(lines, slug, phase_count=3)
        self.assertEqual(closed, {1, 3})
        self.assertTrue(done)


class TestResolveStatus(unittest.TestCase):
    slug = "fixture-plan"
    plan = "docs/plans/01-fixture-plan"

    def test_mid_plan(self) -> None:
        st = resolve_status(
            plan_path=self.plan,
            slug=self.slug,
            phase_count=3,
            closed_phases={1},
            run_done=False,
        )
        self.assertEqual(st.open, "phase")
        self.assertEqual(st.phase, 2)
        self.assertEqual(st.closed, [f"{self.slug}:1"])
        self.assertFalse(st.done)

    def test_wrap_up(self) -> None:
        st = resolve_status(
            plan_path=self.plan,
            slug=self.slug,
            phase_count=3,
            closed_phases={1, 2, 3},
            run_done=False,
        )
        self.assertEqual(st.open, "wrap-up")
        self.assertIsNone(st.phase)
        self.assertFalse(st.done)

    def test_done(self) -> None:
        st = resolve_status(
            plan_path=self.plan,
            slug=self.slug,
            phase_count=3,
            closed_phases={1, 2, 3},
            run_done=True,
        )
        self.assertEqual(st.open, "done")
        self.assertTrue(st.done)


class TestGitFixtures(unittest.TestCase):
    def test_mid_plan_via_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            st = resolve_plan_folder(plan_dir, repo_root=root, default_branch="master")
            self.assertEqual(st.open, "phase")
            self.assertEqual(st.phase, 2)
            self.assertEqual(st.closed, [f"{FIXTURE_SLUG}:1"])

    def test_wrap_up_via_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            for n in (1, 2, 3):
                commit_trailer(root, f"close p{n}", f"{FIXTURE_SLUG}:{n}")
            st = resolve_plan_folder(plan_dir, repo_root=root, default_branch="master")
            self.assertEqual(st.open, "wrap-up")
            self.assertIsNone(st.phase)

    def test_done_via_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            for n in (1, 2, 3):
                commit_trailer(root, f"close p{n}", f"{FIXTURE_SLUG}:{n}")
            commit_trailer(root, "done", f"{FIXTURE_SLUG}:done")
            st = resolve_plan_folder(plan_dir, repo_root=root, default_branch="master")
            self.assertEqual(st.open, "done")
            self.assertTrue(st.done)

    def test_malformed_trailer_does_not_close_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "bad",
                    "--trailer",
                    "Workflow-Phase: wrong-slug:1",
                ],
                cwd=root,
                check=True,
                capture_output=True,
            )
            commit_trailer(root, "good", f"{FIXTURE_SLUG}:1")
            st = resolve_plan_folder(plan_dir, repo_root=root, default_branch="master")
            self.assertEqual(st.phase, 2)


class TestStatusCLI(unittest.TestCase):
    def test_cli_on_fixture_mid_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = init_fixture_repo(root)
            commit_trailer(root, "close p1", f"{FIXTURE_SLUG}:1")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER / "status.py"),
                    str(plan_dir),
                    "--default-branch",
                    "master",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["open"], "phase")
            self.assertEqual(data["phase"], 2)
            self.assertNotIn("implementation", proc.stdout.lower())

    def test_cli_real_plan_no_trailers(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(DRIVER / "status.py"),
                "docs/plans/06-phase-driver",
                "--default-branch",
                "master",
            ],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertEqual(data["slug"], "phase-driver")
        self.assertEqual(data["open"], "phase")
        self.assertEqual(data["phase"], 1)
        self.assertEqual(data["closed"], [])


if __name__ == "__main__":
    unittest.main()
