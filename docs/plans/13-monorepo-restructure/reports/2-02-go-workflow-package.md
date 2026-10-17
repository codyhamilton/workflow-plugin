# Unit report: 2-02 — Go workflow package and bin resolver

**Status:** `done`

## What changed

- `packages/workflow/go.mod` module path → `github.com/codyhamilton/workflow-plugin/packages/workflow`; all internal imports updated via the recorded `sed` rewrite.
- `bin/workflow` step-4 source build probes `packages/workflow/go.mod` and builds in `packages/workflow`.
- Tests: `WORKFLOW_CHECKS_DIR` / `LoadChecks` paths → `packages/workflow/catalogue` (relative per test file); `pricing_test.go` → `../../../../tools/transcript/pricing.json` from `internal/store/`.

## Rewrite command recorded

See `IMPLEMENTATION.md` → `### Phase 2` (same `find` + `sed` as above).

## Done evidence

### Before edits

`cd packages/workflow && go test ./...` (GOTOOLCHAIN unset; auto toolchain):

```
FAIL github.com/codyhamilton/workflow-plugin/tools/workflow/internal/scorer — TestLoadChecks/real: open ../../../quality/criteria.json: no such file or directory
FAIL github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve — analytics/reads/screen_outcome tests: same missing ../../../quality/criteria.json
FAIL github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store — TestPricingTableMatchesTranscript: open ../../../transcript/pricing.json: no such file or directory
```

(`grep -r 'tools/workflow' packages/workflow` and `grep 'tools/workflow' bin/workflow` would have hit the pre-rewrite module path and bin literals.)

### After edits

```
cd packages/workflow && go test ./...  → exit 0 (all packages ok)
grep -r 'tools/workflow' packages/workflow  → no hits
grep 'tools/workflow' bin/workflow  → no hits
```

## Deviations

- Done-evidence line in the brief names `GOTOOLCHAIN=local`; worker and user instruction left GOTOOLCHAIN unset so Go 1.22.2 auto-downloaded 1.27.1 for tests (same mitigation as phase 1 verification notes).
- Catalogue/pricing/bin path edits were applied in addition to the recorded `find`+`sed` (not covered by that one command).

## Contradictions

None between this brief and cited DESIGN.md Phase 2 contracts.

## Unfinished / problems

None for this unit's owned paths. Repo-wide references outside `packages/workflow` and `bin/workflow` remain for later phase-2 units.
