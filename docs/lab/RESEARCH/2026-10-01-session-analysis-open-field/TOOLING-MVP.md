# Tooling — what to build first

**Status:** rank only. **Nothing in this pack is implemented.** OpenCode tools stay unwired, as in cheap-analysis R8. Live TypeSafe stays off. `--call-jev` stays off.

The rank is by what the five approaches can prove without the tool. A tool that only one late approach needs is later, even if it is more interesting to build.

## MVP — lab scripts and files

These are the first build slice. They live under the cheap-analysis or open-field proof trees when a cycle registers them. They are not a plugin, not an MCP server, and not a hook.

| Order | Tool | Serves | Done when | Explicitly absent |
|--------|------|--------|-----------|-------------------|
| 1 | **Marker / stats-card extractor** | `marker-screen-margin`, the baseline half of `stats-jev-tournament`, the frozen card for `frozen-card-search` | One JSONL row per 34 workers, features from checkpoints ≤ 120 only, round-trip mismatch rate 0 against `cumulative` on the combined shape-qual pack | A threshold, a `recommended_exit`, a network call |
| 2 | **Theme-stratum file** | Every scorer | A committed table that copies the strata in [`OPEN-FIELD.md`](OPEN-FIELD.md) §2 (thrash consensus, poll labels, shared monitor-wait, weak thrash, residual) with worker ids. Derived from the agreement note, not a new seat | New labels, `A0`, checkout α |
| 3 | **Framing registry + dry-run batch** | `stats-jev-tournament`, `frozen-card-search` | Question blobs hashed, unregistered blobs return `unregistered_framing`, a 32-cell dry-run shows dedupe and the cap, dummy `TYPESAFE_API_KEY` does not appear in the output. Implementation may import `jev_client` later; the first slice does not need to, if it only emits request JSON | A socket, a third HTTP client, an edit to `replay_progressive_gates.py` |
| 4 | **Mount probe** | `summary-then-judge`, any Flash arc | Prints whether `WORKFLOW_PROGRESSIVE_CORPUS` (or an explicit path) resolves to assistant text for the pilot workers, and writes `prose_required` when it does not. Does not copy the corpus into git | Vendored raw JSONL, a summary of empty excerpts |

Order is the dependency order. The extractor and the stratum file are enough to close the marker-screen cycle. The registry is enough to close a dry-run framing cycle. The probe is enough to close a summary cycle as a refusal.

Cheap-analysis spikes 0, 1, 2, and 3a are the same machinery with a narrower column set. A cycle should extend that spike shape rather than forking a second segment vocabulary. If spike 0 has not been built yet, the extractor above is the spike, plus the marker columns.

## Later — after a cycle has a reason

| Order | Tool | Why it waits | Build it when |
|--------|------|--------------|---------------|
| 5 | **Local llama.cpp client in the batch tool** | Only `segment-swarm-arbiter` requires it. Spike 5 already specifies the URL, `cache: bypass`, and `missing` when the server is down | A cycle registers that approach and a server is actually up. Until then the cycle result is `missing` without new code |
| 6 | **Summary schema checker** | Flash cards are refused until the mount probe passes | The probe finds prose. The checker is a diff against pack counts plus `max_turn_seen`, not a model |
| 7 | **OpenCode custom tools** from [`TOOLS.md`](../2026-10-01-cheap-analysis-typesafe-opencode/TOOLS.md) | The schemas (`analysis.load_segment`, `jev.classify` / `typesafe.classify`, `analysis.batch_trial`) are the contract a sibling plugin would implement. Registering them before a lab script has produced a dry-run matrix gives Flash a tool with nothing to call. The signals plugin does not gain a `tool` hook | A dry-run batch log exists and a Flash session is the intended caller. Separate plan, new plugin factory, no `process_hook_input` |
| 8 | **Cursor / Claude MCP for TypeSafe** | `tools/transcript/lib/jev_client.py` already posts to `jev-1.13.0` with no fallback. An MCP wrapper makes that POST easier to fire from a seat that is supposed to stay on packs. Dry-run would have to be re-implemented in the MCP layer or the seat will call live by default | A lab script has completed capped live calls and Cody wants the same client inside a seat. The MCP default remains dry-run, key handling matches R7, and the progressive CLI is still not wrapped |
| 9 | **CHM harness seats** (new cloud labeling runs) | Shape-qual seats already ran (Composer, Sonnet, Grok; agreement on n = 34). "CHM" in the progressive notes is the counterfactual seat-swap α hint (~0.5674) from the discarded `parent-pull-v1` relabel. That hint is not a target. New seats are the expensive way to get labels this field mostly does not need | A registration asks for `shape-rubric-v0` because a prose field has no standing theme, raw prose is mounted, and `n_workers` ≥ 3. Not a default tool. Not a redo of checkout |
| 10 | **Offline replay, live** | `replay_progressive_gates.py` dry-run is the checkout study's harness. Pointing it at `--call-jev` answers a failed question (`A0`, H5) | Not from this field. Framing trials use the batch tool's own cap, on cards, with `schema_id` other than a checkout fit |
| 11 | **Raw corpus mount as a repo change** | The mount is an operator path (`WORKFLOW_PROGRESSIVE_CORPUS`). Code that vendors it, or that reconstructs excerpts the pack left empty, fights redaction | Cody mounts it on a machine that runs a prose cycle. The repo keeps the probe and the refusal |

## Surfaces named in the brief, mapped once

| Surface | Rank | Note |
|---------|------|------|
| OpenCode custom tools (`TOOLS.md`) | Later (7) | Sibling plugin, unwired. `install.sh` stays skills-only |
| Cursor / Claude MCP for TypeSafe | Later (8) | Existing Python client first. MCP increases the chance of an uncapped live call |
| CHM harness seats | Later (9) | Standing agreement is the theme target. New three-seat runs are a Cody-level spend |
| Offline replay | Use dry-run only if a regression cell must show a framing did not fork `Y_full`. Live replay is out | Do not extend the progressive CLI into a framing search |
| Raw corpus mount | Gate (4), not an artifact | Required for Flash prose. Absence is a valid cycle result |

## Shared guards every later tool inherits

Copied so a tooling PR does not have to re-derive them. Source of truth remains the cheap-analysis design.

- Default `decision: dry_run`. Live needs `live`, `confirm_live`, and a non-empty `TYPESAFE_API_KEY`.
- Model pin `jev-1.13.0`. Local failures stay `missing` and do not fall through.
- Cache key is the outbound body hash. Namespaces `typesafe` and `local` do not share rows. `cache: bypass` is how a warm server is measured.
- `max_calls` default 32, reject above 256, reject above 32 without `budget_tokens`. The count is would-POST cells.
- State over 12_000 characters is `state_guard` and is not sent. These hybrid packs are ~2–3k characters, so the guard is not the current bottleneck; the empty excerpts and the 32-call cap are.
- `hide_outcome_suffix` stays true for `shape-v0`, `phase-sketch-v0`, and `early-signal-v0`.
- Logs omit the API key.
- `classify.py` is not on this path.

## What not to build in the name of this pack

- A hook, an `additionalContext` writer, or a change to `packages/opencode-workflow-hooks`.
- A compaction threshold, a turn cap, or a decaying `confidence_min` encoded as code.
- A GGUF filename pin.
- A dashboard of `session_kind`.
- A second copy of the Jev client next to `jev_client.post_systemone`.
