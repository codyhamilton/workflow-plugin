# Open-field proofs

Lab scripts for [`marker-screen-margin`](../CANDIDATE-APPROACHES.md#4-marker-screen-prose-on-the-margin) and related cycles. **No network**, no TypeSafe, no `--call-jev`.

## Phase 1a

```bash
pip install scipy lifelines pandas  # once per environment
python3 docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs/run_phase_1a.py
```

Outputs under [`phase-1a/`](phase-1a/): `marker_features.jsonl`, `marker_analysis.json`, `cox_sketch.json`, `SPIKE-RESULT.md`, `CYCLEResult.md`.

Cox sketch: [`run_cox_sketch.py`](run_cox_sketch.py) (also invoked by the phase runner). Future gate from [`ALTERNATES.md`](../2026-10-01-session-analysis-alternate-angles/ALTERNATES.md): concordance ≤ **0.70** on a proper gold → kill Alternate E.
