#!/usr/bin/env python3
"""
iterate_analysis.py — Analyse a Cursor session against the iterate workflow.

Usage:
    # From pre-extracted JSON:
    python tools/cursor/extract.py SESSION_ID PROJECT_PATH | python tools/cursor/iterate_analysis.py

    # Re-extract from session:
    python tools/cursor/iterate_analysis.py --session SESSION_ID [PROJECT_PATH]
        [--format text|json]

Output:
  Cycle structure (research → plan → execute → gate → synthesis → …)
  Per-cycle agent counts and phase distribution
  Direction quality table (phase × prompt_len across cycles)
  Alignment issues list with evidence

Phase classification uses description + prompt keyword heuristics.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Phase classification
# ---------------------------------------------------------------------------

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


def classify_phase(description: str, prompt_first_200: str) -> str:
    """Classify a Task call into an iterate workflow phase."""
    desc = description.lower()
    prompt = prompt_first_200.lower()

    has_consolidat = bool(re.search(r"consolidat", desc))
    has_plan = bool(re.search(r"\bplan\b", desc))
    has_execute = bool(re.search(r"\bexecut", desc))  # matches execute, execution, etc.
    has_build = bool(re.search(r"\bbuild\b", desc))

    # research
    if re.search(r"\bresearch\b", desc):
        return "research"

    # synthesis / judge
    if re.search(r"\b(synthesis|synthesise|synthesize|judge)\b", desc):
        return "synthesis"

    # divergence-gate (check before plan and execute)
    if re.search(r"\b(gate|divergence|approver)\b", desc):
        return "divergence-gate"

    # consolidation checks — order: plan before execute to handle "Consolidation plan (no execution)"
    if has_consolidat:
        if has_plan and not has_execute:
            return "consolidation-plan"
        if has_plan and has_execute:
            # "Consolidation plan" with "execution" in parenthetical → plan
            # "Execute * consolidation" → execute
            if re.search(r"^(execute|build)\b", desc):
                return "consolidation-execute"
            return "consolidation-plan"
        if has_execute or has_build:
            return "consolidation-execute"

    # execute / build — check BEFORE plan to handle "Execute candidate N plan" descriptions
    if has_execute or has_build:
        return "execute"

    # plan
    if has_plan:
        return "plan"

    # review
    if re.search(r"\breview\b", desc):
        return "review"

    # extrapolate
    if re.search(r"\bextrapolat", desc):
        return "extrapolate"

    # fix: handle descriptions with no keywords
    if re.search(r"\bfix\b", desc):
        return "execute"

    # fallback: check prompt keywords
    if re.search(r"\bresearch\b", prompt):
        return "research"
    if re.search(r"\bsynthesi", prompt):
        return "synthesis"

    return "other"


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------

# A new cycle starts when we see a research or plan agent following a
# synthesis / extrapolate / consolidation-execute agent from the previous cycle.
CYCLE_STARTERS = {"research", "plan"}
CYCLE_ENDERS = {"synthesis", "extrapolate", "consolidation-execute"}


def detect_cycles(classified: list[dict]) -> list[list[dict]]:
    """
    Group task calls into cycles.

    Strategy: increment cycle when we see a CYCLE_STARTER after a CYCLE_ENDER.
    First agent always starts cycle 0.
    """
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
        if phase in CYCLE_ENDERS:
            last_ender = True
        else:
            last_ender = False

    return cycles


# ---------------------------------------------------------------------------
# Alignment issue detection
# ---------------------------------------------------------------------------

def detect_alignment_issues(classified: list[dict], cycles: list[list[dict]]) -> list[dict]:
    issues = []

    # 1. Orchestrator-absorbed-planning:
    #    An execute-phase agent appears in a cycle before any plan agent in that cycle
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

    # 2. Parallel-execution: two Task calls with same msg_idx, both execute phase
    # Group by msg_idx
    by_msg: dict[int, list[dict]] = defaultdict(list)
    for task in classified:
        by_msg[task["msg_idx"]].append(task)

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

    # 3. Synthesis-repeated: more than one synthesis agent in same cycle
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
                        f"(seqs={seqs}): "
                        + ", ".join(f"'{t['description']}'" for t in synth_tasks)
                    ),
                }
            )

    # 4. Prompt-degradation: gate agents across a cycle show significant prompt_len drop
    for cycle_num, cycle in enumerate(cycles):
        gate_tasks = [t for t in cycle if t["phase"] == "divergence-gate"]
        if len(gate_tasks) >= 2:
            lens = [t["prompt_len"] for t in gate_tasks]
            drop = lens[0] - lens[-1]
            drop_pct = drop / lens[0] * 100 if lens[0] > 0 else 0
            if drop_pct > 50:  # >50% degradation
                issues.append(
                    {
                        "type": "prompt-degradation",
                        "severity": "high",
                        "cycle": cycle_num + 1,
                        "evidence": (
                            f"Cycle {cycle_num+1}: gate prompt_len dropped "
                            f"{lens[0]} → {lens[-1]} chars ({drop_pct:.0f}% reduction) "
                            f"across {len(gate_tasks)} gate agents"
                        ),
                    }
                )

    # 5. Sub-subagent: a subagent's JSONL contains its own Task calls
    # This is detected from the subagent data in the extracted JSON
    # (handled separately in the main function below where we have access to subagents)

    return issues


def detect_sub_subagent_issues(subagents: list[dict]) -> list[dict]:
    """Detect subagents that spawn their own agents (sub-subagent pattern)."""
    issues = []
    for sa in subagents:
        if sa.get("has_task_calls"):
            tool_counts = sa.get("tool_counts", {})
            task_count = tool_counts.get("Task", 0)
            issues.append(
                {
                    "type": "sub-subagent",
                    "severity": "medium",
                    "agent_id": sa["id"],
                    "evidence": (
                        f"Subagent {sa['id'][:8]} contains {task_count} Task call(s) "
                        f"(agent spawning agents — model selection leak risk)"
                    ),
                }
            )
    return issues


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_text_report(classified: list[dict], cycles: list[list[dict]], issues: list[dict]) -> None:
    print("=" * 70)
    print("ITERATE WORKFLOW ANALYSIS")
    print("=" * 70)
    print(f"\nTotal task calls classified: {len(classified)}")
    print(f"Cycles detected           : {len(cycles)}")

    # Phase distribution
    phase_counts: dict[str, int] = defaultdict(int)
    for t in classified:
        phase_counts[t["phase"]] += 1
    print("\nPhase distribution:")
    for phase in PHASES:
        count = phase_counts.get(phase, 0)
        if count:
            print(f"  {phase:<25} {count:>4}")

    # Per-cycle breakdown
    print()
    for cycle_num, cycle in enumerate(cycles):
        cycle_phase_counts: dict[str, int] = defaultdict(int)
        for t in cycle:
            cycle_phase_counts[t["phase"]] += 1

        models = list(dict.fromkeys(t["model"] for t in cycle))
        model_str = ", ".join(m[:20] for m in models[:3])

        print(f"CYCLE {cycle_num+1:02d}  ({len(cycle)} agents)  models: {model_str}")
        print("-" * 70)

        for t in cycle:
            phase_tag = f"[{t['phase']:<22}]"
            desc = t["description"][:45]
            print(
                f"  seq={t['seq']:2d} msg={t['msg_idx']:3d} {phase_tag} "
                f"{desc:<45} plen={t['prompt_len']:5d}"
            )
        print()

    # Direction quality table
    print("DIRECTION QUALITY (gate agents, prompt_len by cycle)")
    print("-" * 70)
    print(f"  {'Cycle':<8} {'Gates':>6} {'Min plen':>10} {'Max plen':>10} {'Avg plen':>10}")
    for cycle_num, cycle in enumerate(cycles):
        gates = [t for t in cycle if t["phase"] == "divergence-gate"]
        if gates:
            lens = [t["prompt_len"] for t in gates]
            print(
                f"  {cycle_num+1:<8} {len(gates):>6} {min(lens):>10} {max(lens):>10} "
                f"{sum(lens)//len(lens):>10}"
            )
    print()

    # Alignment issues
    print("ALIGNMENT ISSUES")
    print("-" * 70)
    if not issues:
        print("  None detected.")
    else:
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "?").upper()
            itype = issue["type"]
            print(f"  {i}. [{sev}] {itype}")
            print(f"     {issue['evidence']}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse a Cursor session against the iterate workflow."
    )
    parser.add_argument(
        "--session",
        metavar="SESSION_ID",
        help="Re-extract from this session instead of reading stdin",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project path (only used with --session; default: cwd)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    args = parser.parse_args()

    # Load data
    if args.session:
        sys.path.insert(0, os.path.dirname(__file__))
        from extract import extract_session
        data = extract_session(args.session, args.project_path or os.getcwd())
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit("No input: pipe extract.py output or use --session SESSION_ID")
        data = json.loads(raw)

    task_calls = data.get("task_calls", [])
    subagents = data.get("subagents", [])

    # Classify phases
    classified = []
    for t in task_calls:
        phase = classify_phase(t.get("description", ""), t.get("prompt_first_200", ""))
        classified.append({**t, "phase": phase})

    # Detect cycles
    cycles = detect_cycles(classified)

    # Detect alignment issues
    issues = detect_alignment_issues(classified, cycles)
    issues += detect_sub_subagent_issues(subagents)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "task_calls_classified": classified,
                    "cycles": [
                        {
                            "cycle_num": i + 1,
                            "agents": c,
                            "phase_counts": dict(
                                (p, sum(1 for t in c if t["phase"] == p))
                                for p in PHASES
                                if any(t["phase"] == p for t in c)
                            ),
                        }
                        for i, c in enumerate(cycles)
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
