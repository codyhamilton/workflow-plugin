#!/usr/bin/env python3
"""Trailer-completeness verifier (bot stand-in: status → once → assert).

Rebuilds a fixture git history from reference/DESIGN.md and reference/expected.json,
then checks:

1. tools/driver/status.py matches the expected open/closed/done row
2. Workflow-Phase trailers on master..HEAD match the expected list
   (a declared wrong-slug trailer must be present and must not close a phase)
3. tools/driver/run.py --once on that done history skips
4. tools/driver/assert_phase.py --deterministic passes on reference/assert_state.json

Provider cost is recorded only when a headless key is set and a live --once on a
mid-plan copy returns cost_usd. Otherwise cost is unavailable. Classify is not
called. Exit 0 only when checks 1–4 pass.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCENARIO = Path(__file__).resolve().parent
REPO = SCENARIO.parents[2]
DRIVER = REPO / "tools" / "driver"
REFERENCE = SCENARIO / "reference"
COMMAND = "python3 evals/scenarios/trailer-completeness/verify.py"
STATUS_KEYS = ("plan", "slug", "open", "phase", "closed", "done")


def _run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(root: Path, *args: str) -> None:
    proc = _run(["git", *args], root)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git failed").strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")


def _load_expected() -> dict[str, Any]:
    return json.loads((REFERENCE / "expected.json").read_text(encoding="utf-8"))


def _init_repo(root: Path, design: str, plan_rel: str) -> Path:
    _git(root, "init", "-b", "master")
    _git(root, "config", "user.email", "fixture@test")
    _git(root, "config", "user.name", "fixture")
    plan_dir = root / plan_rel
    plan_dir.mkdir(parents=True)
    (plan_dir / "DESIGN.md").write_text(design, encoding="utf-8")
    (root / "README.md").write_text("trailer-completeness fixture\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "initial")
    _git(root, "checkout", "-b", "plan-run")
    return plan_dir


def _commit_trailer(root: Path, message: str, trailer: str) -> None:
    _git(
        root,
        "commit",
        "--allow-empty",
        "-m",
        message,
        "--trailer",
        f"Workflow-Phase: {trailer}",
    )


def _select_commits(commits: list[dict[str, str]], omit: list[str]) -> list[dict[str, str]]:
    unknown = [trailer for trailer in omit if trailer not in {c["trailer"] for c in commits}]
    if unknown:
        raise SystemExit(f"unknown --omit-trailer: {', '.join(unknown)}")
    omitted = set(omit)
    return [c for c in commits if c["trailer"] not in omitted]


def _raw_trailers(root: Path) -> list[str]:
    proc = _run(
        [
            "git",
            "log",
            "master..HEAD",
            "--format=%(trailers:key=Workflow-Phase,valueonly)",
        ],
        root,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git log failed").strip()
        raise SystemExit(detail)
    newest_first = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    return list(reversed(newest_first))


def _split_trailers(oldest_first: list[str], ignored: list[str]) -> tuple[list[str], list[str]]:
    ignored_set = set(ignored)
    accepted = [trailer for trailer in oldest_first if trailer not in ignored_set]
    seen_ignored = [trailer for trailer in oldest_first if trailer in ignored_set]
    return accepted, seen_ignored


def _parse_json(stdout: str) -> dict[str, Any] | None:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _status_slice(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key) for key in STATUS_KEYS}


def _observe_cost(
    *,
    design: str,
    plan_rel: str,
    commits: list[dict[str, str]],
    phase1: str,
    env: dict[str, str],
) -> dict[str, Any]:
    anthropic = bool(env.get("ANTHROPIC_API_KEY", "").strip())
    cursor = bool(env.get("CURSOR_API_KEY", "").strip())
    if not anthropic and not cursor:
        return {
            "available": False,
            "cost_usd": None,
            "reason": "no ANTHROPIC_API_KEY or CURSOR_API_KEY",
        }

    prefix: list[dict[str, str]] = []
    for commit in commits:
        prefix.append(commit)
        if commit["trailer"] == phase1:
            break
    else:
        return {
            "available": False,
            "cost_usd": None,
            "reason": f"cost probe needs a {phase1} commit in the fixture history",
        }

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_dir = _init_repo(root, design, plan_rel)
        for commit in prefix:
            _commit_trailer(root, commit["message"], commit["trailer"])
        proc = _run(
            [
                sys.executable,
                str(DRIVER / "run.py"),
                str(plan_dir),
                "--once",
                "--default-branch",
                "master",
                "--no-record",
            ],
            root,
            env,
        )
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout or "run.py --once failed").strip()
        return {"available": False, "cost_usd": None, "reason": reason}
    data = _parse_json(proc.stdout)
    if data is None:
        return {
            "available": False,
            "cost_usd": None,
            "reason": "run.py --once did not print JSON",
        }
    cost = data.get("cost_usd")
    mode = data.get("mode")
    if mode == "dry-run" or not isinstance(cost, (int, float)):
        return {
            "available": False,
            "cost_usd": None,
            "reason": f"provider did not return a live cost (mode={mode!r}, cost_usd={cost!r})",
        }
    return {
        "available": True,
        "cost_usd": cost,
        "turns": data.get("turns"),
        "provider": data.get("provider"),
        "mode": mode,
        "reason": None,
    }


def evaluate(omit: list[str] | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Run the stand-in and return the outcome object. Exit is decided by the caller."""
    omit = list(omit or [])
    env = dict(os.environ if env is None else env)
    expected = _load_expected()
    design = (REFERENCE / "DESIGN.md").read_text(encoding="utf-8")
    commits = _select_commits(expected["commits"], omit)
    expected_status = expected["status"]
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_dir = _init_repo(root, design, expected["plan_dir"])
        for commit in commits:
            _commit_trailer(root, commit["message"], commit["trailer"])

        status_proc = _run(
            [
                sys.executable,
                str(DRIVER / "status.py"),
                str(plan_dir),
                "--default-branch",
                "master",
                "--no-run-record",
            ],
            root,
            env,
        )
        once_proc = _run(
            [
                sys.executable,
                str(DRIVER / "run.py"),
                str(plan_dir),
                "--once",
                "--default-branch",
                "master",
                "--no-record",
            ],
            root,
            env,
        )
        oldest_first = _raw_trailers(root)

    status_data = _parse_json(status_proc.stdout) if status_proc.returncode == 0 else None
    actual_status = _status_slice(status_data) if status_data else None
    if status_proc.returncode != 0 or actual_status != expected_status:
        detail = (status_proc.stderr or "").strip()
        failures.append(
            "status "
            + (detail or f"got {actual_status!r}, expected {expected_status!r}")
        )

    accepted, seen_ignored = _split_trailers(oldest_first, expected["ignored_trailers"])
    if accepted != expected["trailers"] or seen_ignored != expected["ignored_trailers"]:
        failures.append(
            "trailers "
            f"got accepted={accepted!r} ignored={seen_ignored!r}"
        )

    once_data = _parse_json(once_proc.stdout) if once_proc.returncode == 0 else None
    once = {
        "exit_code": once_proc.returncode,
        "skipped": None if once_data is None else once_data.get("skipped"),
        "skip_reason": None if once_data is None else once_data.get("skip_reason"),
    }
    if once_proc.returncode != 0 or once["skipped"] is not True:
        detail = (once_proc.stderr or "").strip()
        failures.append("once " + (detail or f"skipped={once['skipped']!r}"))

    assert_proc = _run(
        [
            sys.executable,
            str(DRIVER / "assert_phase.py"),
            "--deterministic",
            "--no-record",
            "--state",
            str(REFERENCE / "assert_state.json"),
        ],
        REPO,
        env,
    )
    assert_data = _parse_json(assert_proc.stdout)
    assert_pass = bool(assert_data and assert_data.get("pass") is True)
    decision = None if assert_data is None else assert_data.get("decision_source")
    jev = None if assert_data is None else assert_data.get("jev")
    assert_ok = (
        assert_proc.returncode == 0
        and assert_pass
        and decision == "deterministic"
        and jev is None
    )
    if not assert_ok:
        detail = (assert_proc.stderr or "").strip()
        failures.append(
            "assert "
            + (detail or f"exit={assert_proc.returncode} decision={decision!r} jev={jev!r}")
        )

    slug = expected_status["slug"]
    cost = _observe_cost(
        design=design,
        plan_rel=expected["plan_dir"],
        commits=commits,
        phase1=f"{slug}:1",
        env=env,
    )

    checks = {
        "status": "pass" if not any(item.startswith("status ") for item in failures) else "fail",
        "trailers": "pass"
        if not any(item.startswith("trailers ") for item in failures)
        else "fail",
        "once": "pass" if not any(item.startswith("once ") for item in failures) else "fail",
        "assert": "pass" if not any(item.startswith("assert ") for item in failures) else "fail",
    }
    return {
        "scenario": "trailer-completeness",
        "command": COMMAND,
        "verifier": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "trailers": accepted,
        "ignored_trailers": seen_ignored,
        "status": actual_status,
        "once": once,
        "assert": {
            "exit_code": assert_proc.returncode,
            "pass": assert_pass,
            "decision_source": decision,
        },
        "cost": cost,
        "classify": "not used",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trailer-completeness outcome verifier.")
    parser.add_argument(
        "--omit-trailer",
        action="append",
        default=[],
        help="Drop this Workflow-Phase value from the fixture history (negative check).",
    )
    args = parser.parse_args(argv)
    outcome = evaluate(omit=args.omit_trailer)
    json.dump(outcome, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if outcome["verifier"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
