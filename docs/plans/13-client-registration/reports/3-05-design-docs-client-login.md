---
cursor:
  subagentId: "bc-63005fc8-5b46-56a5-a4e3-4c3dc20fb5bf"
---

# Report: 3-05 — Design docs for client login and resolution

**Status:** done

## What changed

- **`docs/design/02-edge-capture.md`**: Config section documents plan 13 resolution order (env pair, half-set error, file, local default), `WORKFLOW_CLIENT_CONFIG` path override, `workflow login` writing `client.toml`, env pair for agents without a file, and explicit non-goal for `workflow init`. MCP shim bullet aligned to “resolution” wording.
- **`docs/design/05-distribution.md`**: Remote bootstrap describes built `workflow login`, env override pair, hand-edited file; removed “later phase” wording; noted overview-only `?tenant=` from `/v1/me` (carried item 1).
- **`tools/hooklog/README.md`**: Drain endpoint paragraph and Setup remote bullet describe file or env resolution and built `workflow login`; loopback serve described as keyless without `WORKFLOW_SERVE_KEYS` framing.

## Checks

**Before:**

```
docs/design/02-edge-capture.md:124:presence means remote mode; it is written by `workflow login` (not built yet).
---
docs/design/05-distribution.md:64:  tokens (not the session cookie). `workflow login`, which opens the collector and writes
docs/design/02-edge-capture.md:124:presence means remote mode; it is written by `workflow login` (not built yet).
```

(`WORKFLOW_ENDPOINT` absent from design 02 and 05.)

**After:**

```
docs/design/05-distribution.md:68:  browser. There is no `workflow init`.
docs/design/02-edge-capture.md:142:  `--endpoint` for the collector origin). There is no `workflow init`.
---
docs/design/02-edge-capture.md:126:1. **`WORKFLOW_ENDPOINT` and `WORKFLOW_KEY` both set** ...
docs/design/02-edge-capture.md:141:- **`workflow login`** writes `client.toml` ...
docs/design/05-distribution.md:65:  tokens (not the session cookie). **`workflow login`** ...
docs/design/05-distribution.md:67:  or set **`WORKFLOW_ENDPOINT`** and **`WORKFLOW_KEY`** ...
```

## Deviations

- None.

## Contract notes

- Carried item 1: overview `?tenant=` only — reflected in design 5; no claim of full-site tenant wiring.
- Carried item 3: no claim that e2e logs in via OAuth; docs unchanged on e2e auth.
- No contradiction between brief and cited DESIGN client-presentation bullets.

## Known problems

- None.
