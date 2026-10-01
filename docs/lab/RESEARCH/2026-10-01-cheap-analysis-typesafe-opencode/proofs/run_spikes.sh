#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 run_spike_0.py
python3 run_spike_1.py
python3 run_spike_2.py
