#!/usr/bin/env python3
"""Lab shim — canonical implementation in packages/opencode-workflow-hooks/python."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
_MOD = _REPO / "packages" / "opencode-workflow-hooks" / "python" / "batch_aggregator.py"
_NAME = "_workflow_oc_batch_aggregator"
_spec = importlib.util.spec_from_file_location(_NAME, _MOD)
assert _spec and _spec.loader
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = _impl
_spec.loader.exec_module(_impl)

OpenCodeBatchAggregator = _impl.OpenCodeBatchAggregator
simulate_model_steps = _impl.simulate_model_steps

__all__ = ["OpenCodeBatchAggregator", "simulate_model_steps"]
