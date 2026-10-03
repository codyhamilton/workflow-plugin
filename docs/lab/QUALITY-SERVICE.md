# Quality service (local)

`python3 tools/quality/server.py [--port 8765]` serves the quality ledger on 127.0.0.1. It only collects and correlates data; Jev classifies and rates so comparisons are cheap and stable. The service holds `TYPESAFE_API_KEY`; clients never need it. `WORKFLOW_QUALITY_TOKEN` (optional) requires `Authorization: Bearer <token>` (this is the seam for client keys on a remote). The same operations are exposed as MCP tools at `POST /mcp` (registered in `.mcp.json`) and as REST under `/v1`.

## Correlation context (accepted on every call; top-level or under `context`)

`harness`, `workflow_version` (defaults to the plugin version), `model`, `conversation_id`, `initiator_type` (`human|bot|agent|unknown`), `initiator_id`, `repo`, `design_stage`, `execution_stage`. Stored on the score version, the execution, and an append-only `events` row. Artifacts also carry `work_type` (a brief inherits its design's).

## Lifecycle

| Call | Effect |
|---|---|
| `POST /v1/designs`, `POST /v1/briefs` | upsert by project + path (or plan + name), score, log. Identical content is not re-scored. Briefs take `design_id` (adds a `derived_from` link). |
| `PATCH /v1/designs/{id}`, `PATCH /v1/briefs/{id}` | new `text` is re-scored as a new version; stages, work type and design link are updated. |
| `POST /v1/briefs/{id}/executions` | an agent starts a brief; records context and start head. |
| `PATCH /v1/executions/{id}` | add `items` (`kind`: `finding`, `adjustment` or `gap`; optional `category`, `severity`, `scope`) and cost (`cost_usd`, `tokens_in`, `tokens_out`, `turns`, `tool_calls`). A gap links `missing_scope` to its brief (and design if `scope: design`); category `defect` or `rework` links likewise. |
| `POST /v1/executions/{id}/complete` | `outcome` (`done|partial|blocked|abandoned`), `summary`, `metrics`; sets the brief's execution stage. |
| `GET /v1/outcomes?by=` | up-front rating vs realised done rate, cost, gaps, adjustments, sliced by project, repo, work_type, initiator, model, harness, workflow_version, plan or design_stage. |
| `GET /v1/plans/{project}/{plan}/cost` | design and brief ratings mapped to executions and cost. |

MCP tool names: `post_design`, `patch_design`, `post_brief`, `patch_brief`, `start_execution`, `patch_execution`, `complete_execution`, `outcomes`, `plan_cost`, plus the earlier `rate_artifact`, `link_artifacts`, `quality_report`.

## Ids, frontmatter and the ratings breakdown

Designs and briefs carry identity-only frontmatter (never scores or status):

```
---
brief_id: 42
design_id: 17
---
```

- Posting returns `id` and a ready-to-write `frontmatter` block. A later post whose text begins with that frontmatter patches the same artifact (no path matching needed); a brief's `design_id` links it to its design. Frontmatter is stripped before hashing and scoring, so adding ids never triggers a re-score.
- The design and refine skills make obtaining ratings a required output, so the service call is part of the deliverable rather than optional.
- The response also carries `breakdown` (per criterion: score, how, and the repo's mean, stdev, z and `outlier` high/low at |z| >= 2), `baseline` (scope `repo:<project>`, peer count) and a short `summary`. Peers are the latest version of every other artifact of the same kind in the same repo under the current criteria registry. With fewer than 5 peers the response says `not enough history` instead of comparing. A single rating means little; one well outside the repo's norm is the signal.

## Hook events

The hooklog now lands in the same ledger (`hook_events` table), so hook activity joins plans through the harness conversation id: a hook row's `session_id` equals `scores.session_id` and the `conversation_id` on executions and events. The join needs no cooperation from the agent: when a hook `tool_call` row is the agent talking to the service (an MCP `post_*`/`patch_*`/`start_execution` call, or a shell `curl` to `/v1/briefs|designs|.../executions` with a body) and its response carries an `id`, ingest records `conversation_id <-> artifact/execution id` in `conversation_binds`. Passing `conversation_id` explicitly on post/start calls also works and is stored on the score, execution and event as before; sessions, plan joins and execution activity read both.

| Call | Effect |
|---|---|
| `POST /v1/hook-events` | body is `{rows:[...]}` (normalised hooklog rows, up to 5000), `{payload:{...}, harness?}` (a raw hook payload, normalised and scrubbed server-side) or a single row. Idempotent on a content hash. Returns `{inserted, duplicate, rejected}`. |
| `GET /v1/hook-events?session_id=&kind=&limit=&offset=` | rows for a conversation, in time order. |
| `GET /v1/sessions/{id}` | prompts, tool calls and failures, top tools, plus the artifacts scored and executions run in that conversation. |
| `GET /v1/executions/{id}/activity` | hook activity inside the execution window of its conversation. |
| `GET /v1/plans/{project}/{plan}/sessions` | every conversation that scored the plan's artifacts or executed its briefs, with activity. |

Kinds: `user_prompt`, `tool_call`, `batch_end`, `step`, `agent_text`, `stop`, and `event` (opencode bus events and Claude lifecycle rows; their payload is in `extra`).

Capture: hooks run `tools/hooklog/spool.sh`, which drops the raw payload in `~/.local/share/workflow-plugin/hooklog/spool/`; `tools/hooklog/drain.py` normalises, scrubs and POSTs batches to `/v1/hook-events` (`WORKFLOW_QUALITY_URL`, default `http://127.0.0.1:8765`, the address `.mcp.json` registers; empty = local archive only; an explicit `WORKFLOW_HOOKLOG_DIR` without a URL also means local only; `WORKFLOW_QUALITY_TOKEN` is sent as a bearer token if set). The spool keeps rows while the service is down; the drain retries and the service dedupes, so delivery is at-least-once and idempotent. Rows keep the time the hook fired. Install the periodic drain with `tools/hooklog/install-drain.sh`; session end also kicks one. `python3 tools/quality/backfill_hooklog.py [--url ...] [--exclude <session prefix>]` loads older JSONL files into the ledger; reruns are no-ops.

Backfill of the existing store (2026-10-03): 90,792 rows, 265 sessions (opencode 231, claude 4, cursor 1). Historic scores carry no conversation id (the 346 git-history scores all have `session_id` unknown), so the join covers work posted from now on (verified end to end: real hook command, live server, no conversation id supplied).

## Stored text and search
Every posted design/brief version is kept in `bodies.db` beside the ledger (not in `quality.db`, so the ledger stays small and its lock is not shared). Content-addressed by the same hash as `scores.sha`, so a version joins to its scores; one row per (artifact, version) records conversation and workflow version. Text is secret-scrubbed before storage. FTS5 (porter stemming) indexes all versions.
- `GET /v1/{design|brief}s/{id}/body[?sha=]`, `GET .../versions`
- `GET /v1/search?q=<fts5 query>[&kind=&project=&limit=]` (MCP `search_plans`)
- `POST /v1/{design|brief}s/{id}/rescore`: re-run all current checks on the stored text (MCP `rescore`).
Artifacts posted before this feature have no stored body.

## Checks are data
Jev checks are rows, not columns: scores are `criterion_scores(score_id, criterion, score)`, so any number of checks can come and go. Check definitions can be changed without a release:
- `PUT /v1/checks` (MCP `define_checks`): `{kind, name: "b.x", q, levels (worst first), invert?, basis?, active?}` or `{checks: [...]}`. A changed spec becomes version+1; identical is a no-op; `active:false` retires a check (registry checks too, and `{kind,name}` alone restores/keeps the current spec).
- `GET /v1/checks[?kind=]` (MCP `list_checks`) shows registry plus service-defined checks.
- Score rows carry `registry = <criteria.json version>+<signature of service-defined checks>`, so changing the set re-scores identical content on the next post or rescore, and old scores keep the check set they were produced under. Baseline peers match on the base registry version.
- `load_checks.py checks/acceptance-provenance.json` loads the shipped acceptance-criterion rationale checks (`b.ac_why`, `b.ac_proven_required`, `b.ac_judgement_labelled`, and `d.*` equivalents).
Deterministic checks still live in code; only Jev checks are service-defined.
