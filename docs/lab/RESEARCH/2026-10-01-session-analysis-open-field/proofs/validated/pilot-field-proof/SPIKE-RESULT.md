# SPIKE — Pilot field-proof dry-twin

**Cycle:** `pilot-field-proof-wave-001`  
**Result:** dry-twin gate **cleared** (0 live POSTs)

## Checks

| Check | Outcome |
|-------|---------|
| 96-cell plan matches 8×12 matrix | pass |
| 12 registered framing hashes | pass |
| Dry-twin requests all `decision: dry_run` | pass |
| `batch_trial` unique cells = 96, not rejected | pass |
| `budget_tokens` ≥ 200k | pass (400k) |
| Live-shaped batch `posts` = 96 with dummy key (no socket) | pass |
| Dummy API key absent from committed JSON | pass |

## Artifacts

- [`dry_twin_batch_log.json`](dry_twin_batch_log.json)
- [`../../capture/pilot-field-proof/jev/dry-twin/batch_summary.json`](../../capture/pilot-field-proof/jev/dry-twin/batch_summary.json)

## Not done here

- Live `--call-jev` / TypeSafe POSTs (deferred to Ubuntu harness with committed registration).
- Flash workstream C (mount `prose_required` on cloud).
