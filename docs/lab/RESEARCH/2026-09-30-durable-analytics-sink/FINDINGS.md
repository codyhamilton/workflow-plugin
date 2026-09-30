# Findings — durable analytics sink (2026-09-30)

Confidence: **high** where backed by in-repo paths or proofs run on this branch; **medium** for collector ops not exercised in production.

## Recommendation (lab default guidance)

**Dual-write:** keep today's **local gitignored JSONL** per family, plus optional **`WORKFLOW_ANALYTICS_URL` HTTP POST** of envelope v1 (`EVENT-SCHEMA.md`). Remote failures must **not** change hook or driver exit codes. Do **not** wire into default hooks/driver until a `PROPOSALS/` doc is accepted.

**Default remote pattern:** minimal append-only HTTPS collector (B in `SINK-CANDIDATES.md`). Object-storage direct upload is deferred to the collector backend.

**Not recommended** for high-volume telemetry: git commits or PR comments as the primary bus (trailers remain low-rate checkpoints only).

---

## Thread 1 — Inventory (closed)

Emitters are catalogued in [`INVENTORY.md`](INVENTORY.md). Summary:

- **Durable in git:** `Workflow-Phase` trailers via `tools/driver/resolve.py`.
- **Local JSONL only:** `.run-record.jsonl`, `.assert-log.jsonl`, `.jev-signal-log.jsonl` (driver + lab hooks); `.classify-log.jsonl` (visualization — out of sink remit).
- **Stdout/ephemeral:** `status.py`, MCP, `check_skills.py` unless a caller persists.

---

## Thread 2 — Sink candidates (closed)

See [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md). HTTP append proven with mock server; object storage documented as collector concern; git side-channel rejected for hook-scale volume.

---

## Thread 3 — Event schema (closed)

Envelope v1 in [`EVENT-SCHEMA.md`](EVENT-SCHEMA.md) aligns `host_kind`, `session_id`, plan/slug/phase, and namespaced `kind` with existing Jev rows and run-record entries. Local files can stay legacy-shaped during transition.

---

## Thread 4 — Cloud agent egress (closed)

**This run (Cursor Cloud Agent):**

- `cursor-cloud` MCP `environment-info` reported `egress.restricted: false` for environment `3a472955-b113-11f1-a3d8-362438fd9788`.
- `./proofs/prove_cloud_egress.py` POSTed envelope `harness.egress_probe` to `https://httpbin.org/post` — result in [`proofs/validated/egress_cloud_result.json`](proofs/validated/egress_cloud_result.json).

**Failure modes to document for operators:**

| Mode | Symptom | Workflow impact (lab recipe) |
|------|---------|------------------------------|
| Egress allow-list blocks collector host | `URLError` / timeout in `_remote_detail` | None — local JSONL still written |
| Invalid TLS / corporate MITM | `URLError` | None |
| Collector 401/403 | `http_error:401` etc. | Fix token; workflow continues |
| Payload too large | Collector 413 | Drop or trim payload at emitter |
| Restricted egress (`egress.restricted: true`) | All external POSTs fail | Use git trailers + run record export before VM end, or team allow-list for collector domain |

Teams with **restricted egress** must allow-list the collector origin; there is no in-repo bypass.

---

## Thread 5 — Dual-write recipe (closed)

[`DUAL-WRITE-RECIPE.md`](DUAL-WRITE-RECIPE.md) and [`proofs/dual_write_sink.py`](proofs/dual_write_sink.py):

- Env: `WORKFLOW_ANALYTICS_URL`, optional `WORKFLOW_ANALYTICS_TOKEN`, optional `WORKFLOW_ANALYTICS_SESSION_ID` / `WORKFLOW_ANALYTICS_REPO`.
- `run_proofs.sh` demonstrates local append + mock server 204 + Bearer header.

---

## Thread 6 — Constraints honoured (closed)

- Soft signals / classify unchanged on master; no default hook wiring.
- `assert_phase --deterministic` remains authoritative (see `tools/driver/phase_assert.py`).
- No classify-as-KPI in schema or recommendations.

---

## White paper

Grok-owned rewrite of `PROPOSALS/` — see [`GROK-WHITEPAPER-STUB.md`](GROK-WHITEPAPER-STUB.md). This pack does not add a proposal file.
