# Brief: 1-03 — OpenCode plugin drops the remove list

Consumer: a worker (Sonnet-tier) editing the OpenCode hooks plugin and its Node test.
Owned paths: `packages/opencode-workflow-hooks/src/index.ts`, `packages/opencode-workflow-hooks/tests/test_hooks.mjs`, `packages/opencode-workflow-hooks/README.md`. Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Stage only the owned paths and the report (`git commit -- <paths>`); other units commit in parallel.
Report: before committing, write `docs/plans/12-analytics-dashboard-overhaul/reports/1-03-plugin-remove-list.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-01, 1-02, 1-04.
Budget: 4 files to read, about 80 lines to change, 20 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/12-analytics-dashboard-overhaul/DESIGN.md` — "Domain: Capture and event policy", the `remove` bullet (binding); Architectural Implications bullet on Design 2.
2. `packages/opencode-workflow-hooks/src/index.ts` — `recordHooklog` (line ~71), the `observe` helper and returned hooks (lines ~150-250).
3. `packages/opencode-workflow-hooks/tests/test_hooks.mjs` — first test (lines 1-90).
4. `packages/opencode-workflow-hooks/README.md` — where it says every bus type is forwarded.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

The plugin never forwards OpenCode's secret-bearing and redundant events to the queue; the remove list is declared once, in a machine-readable form that the Go side can check for equality.

## Contract

DESIGN.md: "`remove`. Applies to OpenCode `experimental.chat.system.transform`, `chat.params`, `chat.headers` and `shell.env`. The plugin does not forward them." "The OpenCode plugin carries the same `remove` list, and a test asserts the two lists are equal." The test is the Go test in unit 1-05 (`policy_test.go`), which reads your marked block.

Settled by this brief:
- Declare the list in `src/index.ts` exactly in this form (the Go test extracts the quoted strings between the markers; keep one string per entry, double quotes):
  ```ts
  // remove-list:begin
  const REMOVE_EVENTS = ["experimental.chat.system.transform", "chat.params", "chat.headers", "shell.env"] as const
  // remove-list:end
  ```
- Enforce it in `recordHooklog`/`record` (by `hook_event_name`), so it covers both the named hooks and bus events of the same name (`shell.env` is in the bus list too). Do not remove the hook keys from the returned object: the existing test asserts the key set equals `named`. They stay registered and write nothing.
- Everything else, including the derived `PostToolBatch`/`Stop` markers and the batch flush, is unchanged.
- README: replace the "forwards every bus type" statement with the keep/remove behaviour and name the four events and why (secrets, redundant prompt bodies).

### Keep untouched

The queue file format, `kickDrain`, `flushBatch`, and the no-mutation assertion on hook inputs.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `cd packages/opencode-workflow-hooks && node --test tests/test_hooks.mjs` (use the repo's actual invocation if `package.json` defines one) → pass. The updated first test asserts: after invoking all 18 callbacks and all bus types, no queued `.evt` has `event` in the remove list; every other name still queues one; the key-set assertion on the returned hooks still passes.
- A new test reads `src/index.ts`, extracts the marked block, and asserts it equals `["experimental.chat.system.transform","chat.params","chat.headers","shell.env"]` (so the Go test has a stable source).
- `git diff --stat` shows only owned paths.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
