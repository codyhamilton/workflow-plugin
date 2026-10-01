#!/usr/bin/env bash
# Lab dry-run only. Does not call Jev and does not install a hook.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== synthetic fixture =="
python3 synthetic_fixture.py

echo "== unittest =="
python3 -m unittest -v test_proofs.py test_gold.py

echo "== synthetic dry-run =="
python3 replay_progressive_gates.py \
  --transcript "$ROOT/fixtures/synthetic_worker_90.jsonl" \
  --schedule 75:15 \
  --dry-run \
  --out "$ROOT/validated/synthetic_dry_run.jsonl" \
  --metrics "$ROOT/validated/synthetic_dry_run_metrics.json"

CORPUS="${WORKFLOW_PROGRESSIVE_CORPUS:-}"
if [[ -z "$CORPUS" && -d "$ROOT/../../2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers" ]]; then
  CORPUS="$ROOT/../../2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers"
fi

if [[ -n "$CORPUS" && -d "$CORPUS" ]]; then
  echo "== maps corpus dry-run ($CORPUS) =="
  python3 replay_progressive_gates.py \
    --corpus "$CORPUS" \
    --workers 92a48e004519,bb6165018de0,6c87c96bd9bb \
    --schedule 75:15 \
    --dry-run \
    --out "$ROOT/validated/dry_run_checkpoints.jsonl" \
    --metrics "$ROOT/validated/dry_run_metrics.json" \
    --manifest "$ROOT/validated/corpus_manifest.json"
else
  echo "maps corpus not present; synthetic dry-run only"
fi

echo "All proofs passed (dry-run; confidence stays not high)."
