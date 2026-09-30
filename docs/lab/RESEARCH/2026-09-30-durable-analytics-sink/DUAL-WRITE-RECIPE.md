# Dual-write recipe (lab / opt-in)

**Not wired into default hooks or driver on master.** Copy pattern from [`proofs/dual_write_sink.py`](proofs/dual_write_sink.py) when implementing product wiring behind a proposal.

## Behaviour

1. **Always** append one line to the family-local JSONL (existing paths).
2. If `WORKFLOW_ANALYTICS_URL` is set, **POST** the envelope JSON to that URL.
3. On remote failure (network, 4xx/5xx, timeout): log to stderr optionally; **return success** to the hook/driver caller (`exit 0` for hooks).

## Pseudocode

```python
from dual_write_sink import emit_event

emit_event(
    local_path=Path("tools/driver/.run-record.jsonl"),
    legacy_row=run_record_entry,  # written as-is locally
    kind="driver.trigger",
    payload={"phase_dispatch": ...},
)
```

`emit_event`:

- Writes `legacy_row` to `local_path` when provided.
- Builds envelope v1 and calls `_post_remote()` if URL set.
- Never raises to caller for remote errors.

## Environment

```bash
export WORKFLOW_ANALYTICS_URL="https://collector.example/v1/events"
export WORKFLOW_ANALYTICS_TOKEN="..."   # optional Bearer
# Optional overrides
export WORKFLOW_ANALYTICS_HOST_KIND="cloud"
export WORKFLOW_ANALYTICS_SESSION_ID="bc-..."
export WORKFLOW_ANALYTICS_REPO="github.com/codyhamilton/workflow-plugin"
```

## Hook integration sketch (Claude PostToolBatch)

After existing `post_tool_batch_signal.py` append:

```python
# LAB ONLY — not in default plugin settings
try:
    from dual_write_sink import emit_from_jev_signal_row
    emit_from_jev_signal_row(entry)
except Exception:
    pass  # exit 0 regardless
```

## Driver integration sketch

In `run_record.append_record` wrapper (future): call `emit_event` after `append_record` with `kind` mapped from `entry["kind"]`.

## Collector expectations

- `POST` single JSON object per request.
- Respond `204` or `200` with `{"ok": true}`.
- Dedupe on `event_id`.
- Return `413` if payload too large (client drops, workflow continues).

## Local testing

```bash
cd docs/lab/RESEARCH/2026-09-30-durable-analytics-sink/proofs
./run_proofs.sh
```

Starts mock server on port 18765, dual-writes one event, asserts file + HTTP body.
