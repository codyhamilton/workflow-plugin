# Guidance — Codex harness (routing + discovery)

**Status:** guidance (non-breaking). Docs/routing advert only — no installer, driver, or hook behaviour changes. **BDK (`@cursor/bdk`) is out of scope** for this note (thinking only; do not ship wiring here).

**Related:** OpenCode + Flash sign-off gate — [`GUIDANCE-flash-review-gate.md`](GUIDANCE-flash-review-gate.md). Consuming-repo paste / bot loop — [`CONSUMING_REPO.md`](CONSUMING_REPO.md). Root discovery — [`README.md`](../../README.md) § Grok Bot / unattended driver and § Codex. Worker starting allocations — [`skills/execute/SKILL.md`](../../skills/execute/SKILL.md).

## What Codex is (and is not)

**Codex is a separate harness** — the OpenAI Codex CLI (`codex` / `codex exec`), authenticated via ChatGPT Plus (or API). It is **not** an OpenCode provider and **not** a Cursor Composer model.

| Harness | Role in this workflow | Typical map |
|---------|----------------------|-------------|
| **Claude Code** | High-agency orchestrator; phase sign-off | Sonnet/Opus (+ Haiku workers) |
| **Cursor Composer** | Mechanical / cloud collector; Cloud Agent builds | Composer (rightsizing per skill) |
| **Codex** | High-thinking / mechanically rich **alongside** Claude | **Sol** / **Luna** pins (below) |
| **OpenCode + DeepSeek Flash** | Cheap brief/unit throughput when rationing capacity | Flash only for units; **not** sign-off — see Flash gate |
| **Grok Bot** | Unattended driver / Build Orchestrator / strategy | Driver CLIs; phase sign-off with Claude |

Phase sign-off (`Workflow-Phase:`, terminal verification) stays **Claude Code or Grok** — never Flash, and not “because Codex ran.” Codex may implement or deeply analyze units; the orchestrator tier still closes the phase.

## Soft routing (Coding Harness Manager policy)

Harness choice is **effort × fit**, not a mandatory matrix. Balance the work against quota, context, and risk — treat the tables below as **guidance**, not gates.

1. **Soft effort×fit routing — not hard rules.** Weigh harness choice against the unit; nothing here is “you must use X.”
2. **Ask Coding Harness Manager (CHM) when unsure** which harness or model to use.
3. **Reserve high-thought agents for where they earn it.** Keep **Codex Sol** and **Claude** available for hard reasoning; don’t burn them on trivia. **Composer** = mechanical / cloud collect. **Luna** = focused Codex volume. **Flash** = draft only (sign-off still Claude/Grok per the Flash gate).
4. **Smoke on Ubuntu (2026-10-01):** `codex exec -m gpt-6.1-sol -c model_reasoning_effort=high "…"` and `codex exec -m gpt-6-luna -c model_reasoning_effort=high "…"` both work. Close stdin (or pass a prompt on the command line) so `codex exec` does not hang waiting for stdin. Default `~/.codex/config.toml` may still list `gpt-5.4` — **always override with `-m`** for Sol/Luna pins.

## When Codex tends to fit

Codex often fits (alongside Claude for subscription utilization; usually **not** instead of Flash for cheap drafts) when the work is:

- **High-thinking** — multi-file architecture, novel algorithms, security-sensitive review, long-horizon agentic edits
- **Mechanically rich** — large mechanical transforms that still need strong judgment mid-flight
- **Subscription-balancing** — Claude capacity is tight but Plus/Codex quota is available

**Typical lean (not mandatory):** OpenCode **Flash** for well-scoped brief/unit drafts under the Flash review gate. **Composer** for Cursor-cloud collection and mechanical cloud agent landings already on that path. **Claude Code** when the session already holds design context, or for phase close / orchestrator duties. CHM can override any of this.

## Pin Luna and Sol (model ids)

Resolved against **Codex CLI 0.159.3** on the Ubuntu host (`codex debug models --bundled`, 2026-10-01 AEST). Confirm with a CHM smoke if the catalog moves.

| Alias (lab speak) | Pin for scripts / docs | Role | Notes |
|-------------------|------------------------|------|-------|
| **sol** | `gpt-6.1-sol` | **High-thinking / workhorse** | Latest Sol; supports `low`…`ultra`. Default to this over `gpt-6-sol` / `gpt-5.6-sol` in new docs. |
| **luna** | `gpt-6-luna` | Focused / high-volume **inside Codex** | Still Codex — not Flash. Supports up to `max` (no `ultra`). |

Older catalog entries (`gpt-6-sol`, `gpt-5.6-sol`, `gpt-5.6-luna`, `gpt-5.5`) may still appear; **do not** pin them in new workflow docs. **`~/.codex/config.toml` may still default to `gpt-5.4`** on some hosts — scripts and one-shots should pass **`-m gpt-6.1-sol`** or **`-m gpt-6-luna`** explicitly until CHM standardizes the file.

### `codex exec` flags (model + reasoning)

```bash
# Interactive
codex --model gpt-6.1-sol
codex -m gpt-6-luna

# Non-interactive / CI-style (prompt on argv — do not leave stdin open or exec may hang)
codex exec -m gpt-6.1-sol "Review the current changes"
codex exec -m gpt-6.1-sol -c model_reasoning_effort=high "Deep multi-file analysis …"
codex exec -m gpt-6-luna -c model_reasoning_effort=high "Focused extraction …"
```

**Ubuntu smoke (2026-10-01):** the Sol and Luna lines above with `model_reasoning_effort=high` were verified on the lab host. Always pass **`-m`** even when config.toml still names an older default model.

- **Model:** `-m` / `--model <id>` (override config every time until pins are standardized on disk)
- **Reasoning:** config override `-c model_reasoning_effort=<low|medium|high|xhigh|max|ultra>` — **not** a `--reasoning-effort` flag (that flag does not exist on this CLI)
- Optional: persist defaults in `~/.codex/config.toml` with `model = "gpt-6.1-sol"` and `model_reasoning_effort = "high"` when CHM standardizes

**Lab starting point for deep work:** `-m gpt-6.1-sol -c model_reasoning_effort=high` (escalate to `xhigh` / `max` / `ultra` only when Sol still under-thinks). **Luna** when the task is clear and volume/latency matter more than frontier depth — still Codex utilization, not Flash.

## Discovery for builders and bots

Skills alone are **not** enough for Grok Bot (or other cloud drivers). Follow the same pattern as other harnesses:

1. **Status** — skills on disk / harness ready (`python3 tools/driver/check_skills.py` where the consuming image bootstraps workflow skills)
2. **Trigger** — human, coordinator, or `tools/driver/run.py … --once` (Codex is **not** a driver provider yet; invoke `codex` / `codex exec` from an orchestrator that already holds the phase brief)
3. **Asserts** — `assert_phase` / deterministic phase boundary after close

Advertise Codex in consuming-repo notes and README so builders **choose** it; do not invent a Codex `SessionStart` hook or OpenCode-style skill symlink for this pass.

## What does not change

- No new hooks, installer modes, or driver providers in this guidance
- Flash sign-off gate unchanged
- Jev / soft signals stay advisory where wired
- BDK deferred

## Operator routing cues (soft)

Use this as a **starting bias**; ask CHM when the row does not match reality.

| Situation | Often a good fit | Usually weaker fit |
|-----------|------------------|-------------------|
| Hard reasoning / rich mechanical agency | **Codex Sol** (`gpt-6.1-sol` + high effort) or Claude | Flash as sole path |
| Clear, high-volume units on Codex quota | **Codex Luna** | Burning Sol ultra on trivia |
| Cheap parallel unit drafts (OpenCode) | Flash → Sonnet 5.5 → Claude/Grok sign-off | Flash close-out |
| Cursor cloud collect / land PR | Composer Cloud Agent | Assuming Composer ≡ Codex |
| Phase `Workflow-Phase:` close | Claude Code or Grok | Flash or “Codex finished the units” |
