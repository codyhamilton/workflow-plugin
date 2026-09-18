"""Heuristic Cursor session cost estimation from transcript structure."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from lib.tools import canonical_name

_COMPONENTS = ("fresh_in", "cache_write", "cache_read", "output")


@dataclass
class AssistantStep:
    tools: list[str] = field(default_factory=list)
    text_chars: int = 0
    is_final: bool = False


@dataclass
class QueryPhase:
    user_text_chars: int = 0
    ts: str | None = None
    steps: list[AssistantStep] = field(default_factory=list)


@dataclass
class BilledEvent:
    phase_index: int
    cache_miss: bool
    fresh_in: int
    cache_write: int
    cache_read: int
    output: int

    @property
    def total(self) -> int:
        return self.fresh_in + self.cache_write + self.cache_read + self.output


def _chars_to_tokens(chars: int, cfg: dict[str, Any]) -> int:
    if chars <= 0:
        return 0
    return max(1, chars // cfg["chars_per_token"])


def _tool_delta(tool_name: str, cfg: dict[str, Any]) -> int:
    canon = canonical_name(tool_name)
    return cfg["tool_delta"].get(canon, cfg["default_tool_delta"])


def load_estimate_config(project_path: str | None = None) -> dict[str, Any]:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = []
    if project_path:
        candidates.append(os.path.join(project_path, "estimate.json"))
        candidates.append(os.path.join(project_path, "tools", "transcript", "estimate.json"))
    candidates.append(os.path.join(root, "estimate.json"))
    candidates.append(os.path.join(root, "estimate_defaults.json"))

    for path in candidates:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return {k: v for k, v in data.items() if not k.startswith("_")}

    return {
        "fixed_context": 16668,
        "chars_per_token": 4,
        "assistant_text_overhead": 200,
        "cache_miss_every_queries": 3,
        "cache_miss_min_context": 50000,
        "heavy_query_tools": 30,
        "heavy_query_multiplier": 2.5,
        "tool_delta": {},
        "default_tool_delta": 3500,
        "default_model": "composer-2.5",
    }


def _content_stats(content: list) -> tuple[list[str], int]:
    tools: list[str] = []
    text_chars = 0
    for item in content:
        if item.get("type") == "tool_use":
            tools.append(item.get("name", ""))
        elif item.get("type") == "text":
            text_chars += len(item.get("text", ""))
    return tools, text_chars


def parse_cursor_phases(jsonl_path: str) -> list[QueryPhase]:
    """Split parent transcript into user-query phases with assistant steps."""
    if not os.path.isfile(jsonl_path):
        return []

    phases: list[QueryPhase] = []
    current: QueryPhase | None = None

    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = msg.get("role", "")
            content = msg.get("message", {}).get("content", [])

            if role == "user":
                text = "".join(
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                )
                if current and current.steps:
                    phases.append(current)
                current = QueryPhase(user_text_chars=len(text))
                continue

            if role != "assistant" or current is None:
                continue

            tools, text_chars = _content_stats(content)
            current.steps.append(AssistantStep(tools=tools, text_chars=text_chars))

    if current and current.steps:
        phases.append(current)

    for phase in phases:
        if not phase.steps:
            continue
        last = phase.steps[-1]
        last.is_final = last.text_chars >= 800 or not last.tools

    return phases


def _step_delta(step: AssistantStep, cfg: dict[str, Any]) -> int:
    delta = sum(_tool_delta(name, cfg) for name in step.tools)
    if step.text_chars:
        delta += _chars_to_tokens(step.text_chars, cfg)
    elif step.tools:
        delta += cfg["assistant_text_overhead"]
    return delta


def _step_output(step: AssistantStep, cfg: dict[str, Any]) -> int:
    if step.is_final and step.text_chars:
        return _chars_to_tokens(step.text_chars, cfg)
    if step.tools:
        return cfg["assistant_text_overhead"]
    return _chars_to_tokens(step.text_chars, cfg)


def simulate_cursor_billing(
    phases: list[QueryPhase],
    cfg: dict[str, Any],
) -> tuple[dict[str, int], list[BilledEvent]]:
    """
    Simulate billing at user-query granularity (matches usage CSV rows).

    Within each query, tool-loop steps grow context; one billed event fires
    at the end with cache_read = accumulated context and fresh_in = final step.
    Occasional cache misses reload the full context as fresh_in.
    """
    context = cfg["fixed_context"]
    totals = {k: 0 for k in _COMPONENTS}
    events: list[BilledEvent] = []
    since_miss = 0

    for phase_index, phase in enumerate(phases):
        phase_start = context
        context += _chars_to_tokens(phase.user_text_chars, cfg)

        steps = phase.steps or [AssistantStep()]
        loop_delta = sum(_step_delta(step, cfg) for step in steps[:-1])
        tool_count = sum(len(step.tools) for step in steps)
        heavy = tool_count >= cfg.get("heavy_query_tools", 30)
        if heavy:
            loop_delta = int(
                loop_delta * cfg.get("heavy_query_multiplier", 2.5)
            )

        final = steps[-1]
        final_delta = _step_delta(final, cfg)
        output = sum(_step_output(step, cfg) for step in steps)

        def _bill(
            *,
            bill_context: int,
            fresh_in: int,
            cache_read: int,
            out: int,
            cache_miss: bool,
        ) -> None:
            nonlocal context, since_miss
            events.append(
                BilledEvent(
                    phase_index=phase_index,
                    cache_miss=cache_miss,
                    fresh_in=fresh_in,
                    cache_write=0,
                    cache_read=cache_read,
                    output=out,
                )
            )
            totals["fresh_in"] += fresh_in
            totals["cache_read"] += cache_read
            totals["output"] += out
            if cache_miss:
                since_miss = 0
            else:
                since_miss += 1

        if heavy:
            # Heavy queries often produce 2+ CSV rows: mid miss/small hit, then big cache read.
            mid_context = context + int(loop_delta * 0.55)
            mid_out = int(output * 0.1)
            _bill(
                bill_context=mid_context,
                fresh_in=mid_context - phase_start,
                cache_read=0,
                out=mid_out,
                cache_miss=True,
            )
            context = mid_context + final_delta
            big_read = context
            big_out = output - mid_out
            _bill(
                bill_context=context,
                fresh_in=final_delta,
                cache_read=big_read,
                out=big_out,
                cache_miss=False,
            )
            context += final_delta + big_out
            continue

        context += loop_delta
        cache_miss = (
            since_miss >= cfg.get("cache_miss_every_queries", 3)
            and context >= cfg.get("cache_miss_min_context", 50000)
        )

        if cache_miss:
            _bill(
                bill_context=context,
                fresh_in=context + final_delta - phase_start,
                cache_read=0,
                out=output,
                cache_miss=True,
            )
            context += final_delta + output
        else:
            _bill(
                bill_context=context,
                fresh_in=final_delta,
                cache_read=context,
                out=output,
                cache_miss=False,
            )
            context += final_delta + output

    return totals, events


def _sum_tokens(items: list[dict[str, int]]) -> dict[str, int]:
    totals = {k: 0 for k in _COMPONENTS}
    for item in items:
        for key in _COMPONENTS:
            totals[key] += item.get(key, 0)
    return totals


def events_to_rows(events: list[BilledEvent]) -> list[dict[str, int]]:
    return [
        {
            "fresh_in": e.fresh_in,
            "cache_write": e.cache_write,
            "cache_read": e.cache_read,
            "output": e.output,
            "cache_miss": e.cache_miss,
        }
        for e in events
    ]


def price_tokens(tokens: dict[str, int], rates: dict[str, float]) -> float:
    rate_key = {
        "fresh_in": "input",
        "cache_write": "cache_write",
        "cache_read": "cache_read",
        "output": "output",
    }
    return sum(
        tokens[k] * rates[rate_key[k]] / 1_000_000 for k in _COMPONENTS
    )


def estimate_from_data(
    data: dict[str, Any],
    jsonl_path: str,
    *,
    cfg: dict[str, Any] | None = None,
    pricing: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    project_path = data.get("session", {}).get("project_path")
    cfg = cfg or load_estimate_config(project_path)
    phases = parse_cursor_phases(jsonl_path)

    totals, events = simulate_cursor_billing(phases, cfg)
    rows = events_to_rows(events)

    model = cfg.get("default_model", "composer-2.5")
    cost = None
    if pricing and model in pricing:
        cost = round(price_tokens(totals, pricing[model]), 4)

    return {
        "method": "transcript-heuristic",
        "confidence": "ballpark",
        "fixed_context": cfg["fixed_context"],
        "user_queries": len(phases),
        "assistant_steps": sum(len(p.steps) for p in phases),
        "token_usage": totals,
        "api_calls": len(events),
        "events": rows,
        "cost_usd": cost,
        "model": model,
    }


def reconcile(estimate: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    est = estimate.get("token_usage", {})
    act = {
        "fresh_in": sum(e.get("fresh_in", 0) for e in actual.get("events", [])),
        "cache_write": sum(e.get("cache_write", 0) for e in actual.get("events", [])),
        "cache_read": sum(e.get("cache_read", 0) for e in actual.get("events", [])),
        "output": sum(e.get("output", 0) for e in actual.get("events", [])),
    }
    act["total"] = sum(act.values())

    ratios: dict[str, float | None] = {}
    for bucket in ("fresh_in", "cache_read", "output", "total"):
        e = est.get(bucket, 0) if bucket != "total" else sum(est.values())
        a = act.get(bucket, 0)
        ratios[bucket] = round(e / a, 2) if a else None

    est_cost = estimate.get("cost_usd")
    act_cost = (actual.get("cost") or {}).get("grand_total")
    return {
        "estimated": est,
        "actual": act,
        "ratios_est_over_actual": ratios,
        "estimated_usd": est_cost,
        "actual_usd": act_cost,
        "usd_ratio": round(est_cost / act_cost, 2)
        if est_cost and act_cost
        else None,
        "actual_events": actual.get("in_window_events", 0),
        "estimated_events": estimate.get("api_calls", 0),
    }
