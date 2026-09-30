#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
echo "== OpenCode hooks plugin lab proofs =="
python3 -m unittest discover -s . -p 'test_*.py' -v
echo "ok"
