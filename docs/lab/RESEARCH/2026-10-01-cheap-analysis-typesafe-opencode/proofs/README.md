# Cheap-analysis spike harness (offline)

Headless runners for spikes 0–2 in [`NEXT-EXPERIMENTS.md`](../NEXT-EXPERIMENTS.md). No `--call-jev`, no live TypeSafe POST, no OpenCode tool registration.

```bash
./run_spikes.sh
```

Evidence lands under `spike-0/`, `spike-1/`, `spike-2/` with `SPIKE-RESULT.md` per spike.

Implementation sketch for `analysis.load_segment`, `jev.classify`, and `analysis.batch_trial` lives in `lib/` (lab-only, not wired to OpenCode).
