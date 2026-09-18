#!/usr/bin/env python3
"""Analyse a session against the iterate workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict

from lib.cli import add_format_arg, add_tool_arg, load_normalized_json, setup_path

setup_path()

PHASES = [
    "research",
    "plan",
    "execute",
    "divergence-gate",
    "synthesis",
    "consolidation-plan",
    "consolidation-execute",
    "review",
    "extrapolate",
    "other",
]

CYCLE_STARTERS = {"research", "plan"}
CYCLE_ENDERS = {"synthesis", "extrapolate", "consolidation-execute"}


def classify_phase(description: str, prompt_first_200: str = "") -> str:
    desc = description.lower()
    prompt = prompt_first_200.lower()

    has_consolidat = bool(re.search(r"consolidat", desc))
    has_plan = bool(re.search(r"\bplan\b", desc))
    has_execute = bool(re.search(r"\bexecut", desc))
    has_build = bool(re.search(r"\bbuild\b", desc))

    if re.search(r"\bresearch\b", desc):
        return "research"
    if re.search(r"\b(synthesis|synthesise|synthesize|judge)\b", desc):
        return "synthesis"
    if re.search(r"\b(gate|divergence|approver)\b", desc):
        return "divergence-gate"
    if has_consolidat:
        if has_plan and not has_execute:
            return "consolidation-plan"
        if has_plan and has_execute:
            if re.search(r"^(execute|build)\b", desc):
                return "consolidation-execute"
            return "consolidation-plan"
        if has_execute or has_build:
            return "consolidation-execute"
    if has_execute or has_build:
        return "execute"
    if has_plan:
        return "plan"
    if re.search(r"\breview\b", desc):
        return "review"
    if re.search(r"\bextrapolat", desc):
        return "extrapolate"
    if re.search(r"\bfix\b", desc):
        return "execute"
    if re.search(r"\bresearch\b", prompt):
        return "research"
    if re.search(r"\bsynthesi", prompt):
        return "synthesis"
    return "other"


def detect_cycles(classified: list[dict]) -> list[list[dict]]:
    if not classified:
        return []
    cycles: list[list[dict]] = [[]]
    last_ender = False
    for task in classified:
        phase = task["phase"]
        if last_ender and phase in CYCLE_STARTERS:
            cycles.append([])
            last_ender = False
        cycles[-1].append(task)
        last_ender = phase in CYCLE_ENDERS
    return cycles


def detect_alignment_issues(classified: list[dict], cycles: list[list[dict]]) -> list[dict]:
    issues = []
    for cycle_num, cycle in enumerate(cycles):
        seen_plan = False
        for task in cycle:
            if task["phase"] == "plan":
                seen_plan = True
                break
            if task["phase"] == "execute" and not seen_plan:
                issues.append(
                    {
                        "type": "orchestrator-absorbed-planning",
                        "severity": "high",
                        "cycle": cycle_num + 1,
                        "evidence": (
                            f"Cycle {cycle_num+1}: execute agent (seq={task['seq']}, "
                            f"desc='{task['description']}') appeared before any plan agent"
                        ),
                    }
                )
                break

    by_msg: dict[int, list[dict]] = defaultdict(list)
    for task in classified:
        msg_idx = task.get("msg_idx", task.get("seq", 0))
        by_msg[msg_idx].append(task)

    for msg_idx, tasks in by_msg.items():
        execute_tasks = [t for t in tasks if t["phase"] == "execute"]
        if len(execute_tasks) >= 2:
            descs = [t["description"] for t in execute_tasks]
            issues.append(
                {
                    "type": "parallel-execution",
                    "severity": "medium",
                    "msg_idx": msg_idx,
                    "evidence": (
                        f"msg={msg_idx}: {len(execute_tasks)} parallel execute agents: "
                        + ", ".join(f"'{d}'" for d in descs)
                    ),
                }
            )

    for cycle_num, cycle in enumerate(cycles):
        synth_tasks = [t for t in cycle if t["phase"] == "synthesis"]
        if len(synth_tasks) > 1:
            seqs = [t["seq"] for t in synth_tasks]
            issues.append(
                {
                    "type": "synthesis-repeated",
                    "severity": "medium",
                    "cycle": cycle_num + 1,
                    "evidence": (
                        f"Cycle {cycle_num+1}: {len(synth_tasks)} synthesis agents "
                        f"(seqs={seqs})"
                    ),
                }
            )

    return issues


def detect_sub_subagent_issues(subagents: list[dict]) -> list[dict]:
    issues = []
    for sa in subagents:
        if sa.get("has_task_calls"):
            raw = sa.get("tool_counts_raw", {})
            spawn_count = raw.get("Task", 0) + raw.get("Agent", 0)
            issues.append(
                {
                    "type": "sub-subagent",
                    "severity": "medium",
                    "agent_id": sa["id"],
                    "evidence": (
                        f"Subagent {sa['id'][:8]} contains {spawn_count} spawn call(s)"
                    ),
                }
            )
    return issues


def print_text_report(classified: list[dict], cycles: list[list[dict]], issues: list[dict]) -> None:
    print("=" * 70)
    print("ITERATE WORKFLOW ANALYSIS")
    print("=" * 70)
    print(f"\nTotal spawns classified: {len(classified)}")
    print(f"Cycles detected        : {len(cycles)}")

    phase_counts: dict[str, int] = defaultdict(int)
    for t in classified:
        phase_counts[t["phase"]] += 1
    print("\nPhase distribution:")
    for phase in PHASES:
        count = phase_counts.get(phase, 0)
        if count:
            print(f"  {phase:<25} {count:>4}")

    print()
    for cycle_num, cycle in enumerate(cycles):
        models = list(dict.fromkeys(t.get("model", "") for t in cycle))
        model_str = ", ".join(m[:20] for m in models[:3] if m)
        print(f"CYCLE {cycle_num+1:02d}  ({len(cycle)} agents)  models: {model_str}")
        print("-" * 70)
        for t in cycle:
            phase_tag = f"[{t['phase']:<22}]"
            desc = t.get("description", "")[:45]
            print(f"  seq={t['seq']:2d} {phase_tag} {desc:<45}")
        print()

    print("ALIGNMENT ISSUES")
    print("-" * 70)
    if not issues:
        print("  None detected.")
    else:
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "?").upper()
            print(f"  {i}. [{sev}] {issue['type']}")
            print(f"     {issue['evidence']}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse a session against the iterate workflow."
    )
    parser.add_argument("--session", metavar="REF", help="Re-extract from session")
    parser.add_argument("--project", dest="project_flag", metavar="PATH")
    parser.add_argument("project_path", nargs="?", default=None)
    add_tool_arg(parser)
    add_format_arg(parser)
    args = parser.parse_args()

    project = args.project_flag or args.project_path or (os.getcwd() if args.session else None)
    data = load_normalized_json(args.session, project, args.tool)

    spawns = data.get("agent_spawns", [])
    subagents = data.get("subagents", [])

    classified = []
    for s in spawns:
        phase = classify_phase(s.get("description", ""))
        classified.append({**s, "phase": phase})

    cycles = detect_cycles(classified)
    issues = detect_alignment_issues(classified, cycles)
    issues += detect_sub_subagent_issues(subagents)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "spawns_classified": classified,
                    "cycles": [
                        {"cycle_num": i + 1, "agents": c} for i, c in enumerate(cycles)
                    ],
                    "alignment_issues": issues,
                },
                indent=2,
            )
        )
        return

    print_text_report(classified, cycles, issues)


if __name__ == "__main__":
    main()
