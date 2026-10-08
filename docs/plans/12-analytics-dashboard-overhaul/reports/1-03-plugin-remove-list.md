# Report: 1-03 plugin remove list

Status: done

## Changed
- `packages/opencode-workflow-hooks/src/index.ts`: added the marked `REMOVE_EVENTS` block (exact form from the brief) and an early return in `recordHooklog` keyed on `hook_event_name`. This covers named hooks and same-named bus events. Hook keys stay on the returned object. Derived `PostToolBatch`/`Stop` markers, batch flush, queue format and `kickDrain` are untouched.
- `packages/opencode-workflow-hooks/tests/test_hooks.mjs`: first test now asserts no queued event is in the remove list and every other name still queues; the key-set assertion is unchanged. New test extracts the marked block from `src/index.ts` and asserts it equals the four names.
- `packages/opencode-workflow-hooks/README.md`: replaced "every event is forwarded" with the keep/remove behaviour and the reason (secrets, redundant prompt bodies).

## Check output
Command: `cd packages/opencode-workflow-hooks && node --test tests/test_hooks.mjs`
- Before (test updated, code not): `# pass 5`, `# fail 2` (first test and the new marker test failed).
- After: `# pass 7`, `# fail 0`.

## Deviations and contradictions
None.
