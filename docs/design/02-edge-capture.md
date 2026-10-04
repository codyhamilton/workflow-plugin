# Design Intent 2: Edge Capture

How hook events get from a harness to the remote: the spool, the drain, the local MCP shim, and
per-harness install. Part of [system-architecture.md](system-architecture.md); builds on the facts
and keys in [01-event-model-and-ingest.md](01-event-model-and-ingest.md).

## Problem

Hooks fire from several harnesses at once, often in bursts: Cursor runs one `postToolUse` per call
in a batched tool turn, and Claude runs `PostToolUse` per call in a parallel batch. Hooks must stay
cheap and never fail the agent, yet every event has to reach the remote, which may be local or
remote by config, may be down, and may refuse content.

## Shape

```
 hook ──spool.sh──▶ queue/<conv>-<ts>-<pid>-<rand>.evt ──▶ drain (one per user) ──▶ remote ingest
                         │                                    │ 4xx
                         └── kick: start drain if none        └──▶ rejected/<same name> + reason
 agent ──MCP (stdio)──▶ shim ──▶ remote advisory API
                         └── reads queue/ and rejected/ for this conversation
```

One queue directory per user serves every harness. The harness is in the envelope, not the path.
The queue is transit, not storage: a file is deleted once the remote accepts it.

## Spool

`spool.sh` stays bash and does no parsing and no network.

- Writes the envelope plus raw payload to `tmp/`, then renames into `queue/`. The rename is atomic,
  so concurrent hooks need no lock and a reader never sees a partial file.
- File name starts with the conversation ID: `<conversation_id>-<ts>-<pid>-<rand>.evt`. Any
  per-conversation check is then one directory listing, with no JSON parsing. The hook extracts the
  ID with a bounded text match on the payload; a payload without one is not spooled (design 1,
  decision 4).
- `--harness` is a literal from the adapter. `auto` is removed.
- Never snapshots a file and never fails: exit 0 always.

## Drain

Python, stdlib only. One instance per user, holding an exclusive flock on `queue/.drain.lock` for
its lifetime.

**Start.** After its rename, a hook probes the lock non-blocking. Held means a drain is running and
the hook returns. Free means it starts `setsid drain.py --daemon` in the background. The probe takes
the lock for an instant, so the drain acquires with a short blocking wait (about 1 s), not `-n`. A
burst that beats the first drain to the lock starts a few extra Pythons that fail to acquire and
exit; this is accepted, and measured (see Tests).

**Batch window.** After the first file appears, wait about 1.5 s before building a batch. This turns
a burst into one POST and coalesces repeated writes to one `(repo_id, path)` into one file read.
Cursor's `postToolUse` and `afterFileEdit` for the same write coalesce here.

**Linger.** Exit after about 60 s with an empty queue (configurable). Active agent work keeps one
drain alive; it exits about a minute after the agent goes quiet. A sleeping drain costs a few MB;
the linger exists to avoid a process per event.

**Idle exit without stranding.** Release the lock, rescan the queue, and if files exist, try to
retake the lock and continue; if another drain holds it, exit. Because a hook renames before it
probes, either the hook sees the lock free or the rescan sees the file.

**Building facts** (design 1):

- `hook_event` from each envelope, normalised and scrubbed.
- `artifact_version` for write events on the write-surface table below whose path matches a kind
  pattern. Content is read and hashed at drain time. A missing file produces nothing.
- `commit` from `git commit` tool calls: SHA, touched paths, rename pairs from
  `git diff-tree -M --name-status`, run by the drain against the repo in the envelope's `cwd`.
- **Commit catch-up.** For every design, brief or report path touched by a commit, the drain also
  sends an `artifact_version` with source `commit`, read from the committed blob. A worktree write
  that was missed is recovered when the agent commits it, with the right conversation ID.

**Delivery.**

| Response | Action |
|---|---|
| 2xx | delete the files in the batch |
| 5xx, network error, 401/403/408 | retry with backoff; files stay |
| 429 | retry after `Retry-After` |
| other 4xx | move each file to `rejected/` with a `.reason` sidecar |

Backoff is exponential with jitter, capped at about 5 min, and held in memory only. "Idle" means an
empty queue, so a backlog keeps the drain alive, and while it lives its lock stops hooks starting
another. Once backoff is at its cap and no new file has arrived for about 15 min, the drain exits;
the next hook restarts it, and it tries once immediately. That is at most one extra attempt per
restart, and restarts only follow 15 quiet minutes.

Delivery is at-least-once: a crash between a 2xx and the delete resends the batch, and ingest
dedupes by row hash, which is computed from the envelope alone.

**Scrub.** The light client scrub from design 1 (known key prefixes, private key blocks, `*_KEY=`
assignments) runs on every fact before it leaves the machine.

**No local archive.** The remote is the record. The per-session JSONL archive via `hooklog.append`
is dropped from the drain path. `rejected/` is the only thing kept locally.

**No queue cap** for now, since all data is kept. `drain.py status` reports queue size, oldest file,
`rejected/` count and whether a drain is running.

**macOS.** No `flock(1)`. The hook-side probe falls back to a `mkdir` lock with a PID check; the
drain uses `fcntl.flock` as on Linux.

## Config

One file, read by both the drain and the shim: `~/.config/workflow/client.toml`, mode 0600.

```toml
endpoint = "https://quality.example"   # or "http://127.0.0.1:8765"
key = "…"                              # write-and-read client key for the quality service
```

- Not env vars. The drain inherits the environment of whichever hook started it, and that differs
  per harness. An env override exists for tests only.
- Re-read on every batch, so changing endpoint or key needs no restart.
- The key is the quality service's client key, never `TYPESAFE_API_KEY`, which stays on the server.
- Registration (how a key is issued) is out of scope.
- No config: the drain makes no attempt and exits; the queue grows and nothing is lost. `status`
  says so.

The drain never starts or manages the quality service, local or remote (principle 8).

## MCP shim

The advisory MCP is registered with every harness as a local stdio command, not a URL. The shim
reads the shared config and forwards to the remote's advisory API. Design 4 owns what it exposes;
design 2 fixes two things it relies on:

- **Endpoint by config.** Local or remote is one setting in one file. No harness config holds an
  endpoint or a key.
- **Queue awareness.** Before answering, the shim lists `queue/<conversation_id>-*` and
  `rejected/<conversation_id>-*`. If files are pending, it kicks the drain and waits up to about
  1.5 s. If they are still pending, the answer says so ("3 events from this conversation still
  queued, oldest 40 s, remote unreachable"). If any are in `rejected/`, the answer gives the reason;
  the agent's fix is to rewrite the file, which fires a new hook. The rewrite is the repair.

A pre-tool hook could do the same check, but whether MCP calls reach `PreToolUse` differs per
harness, and the shim behaves identically everywhere.

## No repair submit

Design 1 had an explicit, synchronous repair submit. It is dropped. Its cases are covered by:

1. **Transient failure:** the drain retries.
2. **Missed write:** commit catch-up.
3. **Refused content:** the reason surfaces through the shim; the agent rewrites the file.
4. **Never captured and never committed by an agent:** stays a gap. The derived view reports gaps as
   findings (a brief whose design has no version, a write event with no artifact version, a commit
   touching a design path with no version). Content is never backfilled with an invented
   conversation link. A maintainer backfill, if ever needed, is a lab tool.

There is no dependency failure to repair: ingest does not check that a brief's design exists. A
missing design is a gap in the view, not a refused post.

`capture_gap` is removed from the fact types; gaps are computed by the view.

## Write surfaces

Carried from plan 08. These decide which spooled events produce an `artifact_version`.

| Harness | Events | Notes |
|---|---|---|
| Claude Code | `PostToolUse` on Write, Edit, MultiEdit | If a batch hook carries `tool_input` for every call, register it instead and drop `PostToolUse` (see Tests) |
| Codex | `PostToolUse` on apply_patch and write tools | |
| Cursor | `postToolUse`, `afterFileEdit` | coalesced in the batch window |
| OpenCode | `tool.execute.after` | bus events excluded |
| all | — | `FileChanged`, `afterTabFileEdit` excluded |

Kind patterns: `docs/plans/<plan>/DESIGN.md` (design), `docs/plans/<plan>/briefs/*.md` (brief),
`docs/plans/<plan>/reports/*.md` (report).

## Per-harness install and trust

Each harness ships its own hook config, passing a literal `--harness`.

| Harness | Config | Trust step |
|---|---|---|
| Claude Code | plugin `hooks/hooks.json` | none beyond plugin install |
| Codex | `hooks.json` | the user approves hooks in `/hooks`; until then nothing is captured |
| Cursor | `hooks/cursor.json` | none |
| OpenCode | plugin calling `spool.sh` | none |

The `artifact_submit.py hook` registrations are removed from all four. Codex hook timeouts stay
within its 3 s ceiling. Pinned plugin copies (the Codex copy at `451e009`) are design 5's problem,
but until updated they keep running the old hooks.

## Changes from what exists

`spool.sh` and `drain.py` already do one file per event, the tmp-then-rename write, the flock probe
and kick, and a `bad/` folder. Remaining:

- File names lead with the conversation ID; payloads without one are not spooled.
- `--harness auto` removed.
- Drain: batch window, idle exit with rescan, in-memory backoff, `Retry-After`, `rejected/` with
  reasons (replacing `bad/`), commit facts and commit catch-up, artifact versions, config file
  instead of `WORKFLOW_QUALITY_URL`/`TOKEN`, archive dropped.
- Retire the systemd timer and service; the hook kick is the only trigger.
- `artifact_submit.py hook` registrations removed; `test_artifact_submit_surfaces.py` rewritten.

## Tests

Cheap, in a `mktemp -d` queue, never the live one.

1. Fire 20 concurrent spools; count drain starts and confirm exactly one keeps the lock and every
   file is delivered once.
2. Idle-exit race: spool during the drain's release-and-rescan; no file is stranded.
3. Remote down, then up: nothing is lost; 4xx goes to `rejected/` with a reason.
4. Capture one real payload per harness for: a write, a `git commit`, a batch hook (Claude), and an
   MCP call (to record which harnesses expose MCP calls to pre-tool hooks).
5. Cursor `postToolUse` plus `afterFileEdit` for one write yields one artifact read.
