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
