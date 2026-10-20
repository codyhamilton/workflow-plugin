# Provenance: Device-code login

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 20, 2026)
- Timestamp: 2026-10-20T00:00:00Z
- CWD: /home/codyh/workspace/workflow-plugin

## Initial Request (verbatim)

> Well for remote sessions we need to set env var for the api key, so they won't use device flow. but regardless for the skill it definitely seems like device flow will be better

> I think design the device flow

## Design Conversation

### Turn 1

**User responded:** Asked how to send events to the remote instead of local, then noted that login seemed to need the binary "despite us writing the python drain to avoid needing the binary", then asked how a `yakka:login` skill would work.

**Agent decisions:**

- Established that `yakka login` is the Python client behind the plugin wrapper, that it is a loopback redirect rather than a device-code flow, and that it has no default endpoint.

### Turn 2

**Agent asked:** What happens to loopback login; when tenant, scope and expiry are chosen; which harnesses get the skill.

**User responded:** Remove loopback on both sides. Choose at approval. All harnesses.

**Agent decisions:**

- `/v1/device/exchange` and the loopback branch of authorize are removed; installed 3.0.1 clients cannot log in until they update.
- The CLI requests a code with no tenant; the page keeps the existing choices.

### Turn 3

**Agent asked:** Whether to remove or port the Go binary's duplicate `login`.

**User responded:** Remove it.

**Agent decisions:**

- `internal/login` is deleted; the Go `login` subcommand exits 1 and names the plugin wrapper.

### Adversarial review

**Agent decisions:**

- Corrected the plan 18 coupling: plan 18 builds its sync login in the Go `internal/login`, which this plan deletes, so plan 18 must be revised first.
- `login` ships in every harness but is not one of the "cloud-safe core" skills; `install.sh` and both marketplace descriptions added to the surfaces.
- Added a per-IP live-grant cap so a handful of IPs cannot fill the global cap.
- Defined the mint-failure response, a validate-only registry check at approval, the `Fly-Client-IP` trust condition, revocation of tokens behind legacy `device_codes`, and `config: env` in `yakka status`.
- Removed the claim of an existing sweep loop, and narrowed "close open issue 18" to its plaintext clause.

## Agent Decisions

- **Mint on poll**: the token is created when the approved grant is redeemed, never stored. Rationale: closes the plaintext-at-rest debt (design 07 open issue 18) and keeps pending grants out of `registry.json`.
- **Pending grants in memory**: Rationale: anonymous requests must not write to disk; a restart only costs a re-run of login.
- **Two-step client (`start`/`wait`)**: Rationale: an agent gets the URL from a command that returns, and waits on one whose exit is the signal.
- **Default endpoint `https://api.yakka.build`**: Rationale: a first login should not require knowing the URL.
