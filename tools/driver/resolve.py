"""Deterministic phase status from DESIGN.md and Workflow-Phase trailers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PHASE_HEADING = re.compile(r"^### Phase \d+", re.MULTILINE)
SLUG_FROM_DIR = re.compile(r"^\d+-(.+)$")
PHASE_TRAILER = re.compile(r"^(.+):(\d+)$")


@dataclass(frozen=True)
class PhaseStatus:
    plan: str
    slug: str
    open: str  # phase | wrap-up | done
    phase: int | None
    closed: list[str]
    done: bool

    def to_json_dict(self) -> dict:
        return {
            "plan": self.plan,
            "slug": self.slug,
            "open": self.open,
            "phase": self.phase,
            "closed": self.closed,
            "done": self.done,
        }


class ResolveError(Exception):
    """Resolution failed (missing design, not a git repo, etc.)."""


def slug_from_plan_dir(plan_dir: Path) -> str:
    name = plan_dir.name
    match = SLUG_FROM_DIR.match(name)
    if match:
        return match.group(1)
    return name


def phase_count_from_design(design_text: str) -> int:
    return len(PHASE_HEADING.findall(design_text))


def parse_trailer_line(line: str, slug: str, phase_count: int) -> tuple[int | None, bool]:
    """Return (phase_index, is_done) if valid for this plan, else (None, False)."""
    line = line.strip()
    if not line:
        return None, False
    if line == f"{slug}:done":
        return None, True
    match = PHASE_TRAILER.match(line)
    if not match:
        return None, False
    trailer_slug, num_str = match.group(1), match.group(2)
    if trailer_slug != slug:
        return None, False
    n = int(num_str)
    if n < 1 or n > phase_count:
        return None, False
    return n, False


def collect_trailers(
    trailer_lines: list[str], slug: str, phase_count: int
) -> tuple[set[int], bool]:
    closed: set[int] = set()
    run_done = False
    for line in trailer_lines:
        phase_n, is_done = parse_trailer_line(line, slug, phase_count)
        if is_done:
            run_done = True
        elif phase_n is not None:
            closed.add(phase_n)
    return closed, run_done


def resolve_status(
    *,
    plan_path: str,
    slug: str,
    phase_count: int,
    closed_phases: set[int],
    run_done: bool,
) -> PhaseStatus:
    closed_list = [f"{slug}:{n}" for n in sorted(closed_phases)]

    if run_done:
        return PhaseStatus(
            plan=plan_path,
            slug=slug,
            open="done",
            phase=None,
            closed=closed_list,
            done=True,
        )

    if phase_count == 0:
        raise ResolveError("DESIGN.md has no ### Phase headings")

    all_closed = all(n in closed_phases for n in range(1, phase_count + 1))
    if all_closed:
        return PhaseStatus(
            plan=plan_path,
            slug=slug,
            open="wrap-up",
            phase=None,
            closed=closed_list,
            done=False,
        )

    open_n = next(n for n in range(1, phase_count + 1) if n not in closed_phases)
    return PhaseStatus(
        plan=plan_path,
        slug=slug,
        open="phase",
        phase=open_n,
        closed=closed_list,
        done=False,
    )


def git_trailer_lines(repo_root: Path, default_ref: str) -> list[str]:
    rev_range = f"{default_ref}..HEAD"
    proc = subprocess.run(
        [
            "git",
            "log",
            rev_range,
            "--format=%(trailers:key=Workflow-Phase,valueonly)",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ResolveError(proc.stderr.strip() or f"git log {rev_range} failed")
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def detect_default_branch(repo_root: Path, override: str | None) -> str:
    if override:
        return override
    for cmd in (
        ["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"],
    ):
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            ref = proc.stdout.strip()
            if ref.startswith("refs/remotes/origin/"):
                return ref.removeprefix("refs/remotes/origin/")
            if ref.startswith("origin/"):
                return ref.removeprefix("origin/")
            if ref and ref != "HEAD":
                return ref
    for candidate in ("master", "main"):
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return candidate
    raise ResolveError("Could not determine default branch; pass --default-branch")


def resolve_plan_folder(
    plan_folder: Path,
    *,
    repo_root: Path | None = None,
    default_branch: str | None = None,
) -> PhaseStatus:
    plan_folder = plan_folder.resolve()
    if repo_root is None:
        repo_root = _git_root(plan_folder)
    repo_root = repo_root.resolve()

    design_path = plan_folder / "DESIGN.md"
    if not design_path.is_file():
        raise ResolveError(f"Missing {design_path}")

    design_text = design_path.read_text(encoding="utf-8")
    phase_count = phase_count_from_design(design_text)
    if phase_count == 0:
        raise ResolveError("DESIGN.md has no ### Phase headings")

    slug = slug_from_plan_dir(plan_folder)
    try:
        plan_path = plan_folder.relative_to(repo_root).as_posix()
    except ValueError:
        plan_path = str(plan_folder)

    default_ref = detect_default_branch(repo_root, default_branch)
    lines = git_trailer_lines(repo_root, default_ref)
    closed_phases, run_done = collect_trailers(lines, slug, phase_count)
    return resolve_status(
        plan_path=plan_path,
        slug=slug,
        phase_count=phase_count,
        closed_phases=closed_phases,
        run_done=run_done,
    )


def _git_root(start: Path) -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ResolveError("Not inside a git repository")
    return Path(proc.stdout.strip())
