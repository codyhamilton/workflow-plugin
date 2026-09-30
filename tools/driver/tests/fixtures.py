"""Fixtures for phase status resolution (no IMPLEMENTATION.md required)."""

from __future__ import annotations

import subprocess
from pathlib import Path

FIXTURE_SLUG = "fixture-plan"
FIXTURE_PHASES = 3

DESIGN_MD = """# Fixture plan

## Phases

### Phase 1 — First

- Outcome: one

### Phase 2 — Second

- Outcome: two

### Phase 3 — Third

- Outcome: three
"""


def init_fixture_repo(root: Path) -> Path:
    """Create a mini repo with plan folder and default branch master."""
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "master"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    plan_dir = root / "docs" / "plans" / f"01-{FIXTURE_SLUG}"
    plan_dir.mkdir(parents=True)
    (plan_dir / "DESIGN.md").write_text(DESIGN_MD, encoding="utf-8")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "plan-run"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return plan_dir


def commit_trailer(root: Path, message: str, trailer: str) -> None:
    subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            message,
            "--trailer",
            f"Workflow-Phase: {trailer}",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
