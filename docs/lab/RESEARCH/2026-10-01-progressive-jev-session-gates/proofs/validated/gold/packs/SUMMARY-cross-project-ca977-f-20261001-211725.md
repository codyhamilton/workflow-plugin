# Cross-project ca977 shape screen — experiment `cross-project-ca977-shape-screen-v1`

**Run:** `20261001-211725` · schedule `75:15` · **status: blocked** · no packs · panel held.

Strict ca977 shape (no Edit/Write ∧ max_reread≥8 ∧ compact≥8 ∧ T≥75) was not evaluated on any worker: the cross-project subagent pool is **empty**.

## Screen

| Gate | Result |
|------|--------|
| Projects scanned | **9** (all `~/.claude/projects/` except open-pajero-maps, its worktree alias, and `-tmp-*`) |
| Subagent/worker JSONLs | **0** |
| Candidates T≥75 | **0** |
| n_ca977_shape | **0** |
| Packs | **none** (do not pad) |
| Panel | **held** |
| Jev | **blocked** (unchanged; still one non-null A0 on `ca977b9ca0dd@90`) |

### Projects scanned

`-home-codyh-workspace-ansible-dev-config`, `-home-codyh-workspace-devcontainers`, `-home-codyh-workspace-free-frontier`, `-home-codyh-workspace-garcia-music`, `-home-codyh-workspace-instant-host`, `-home-codyh-workspace-silver-chronicle`, `-home-codyh-workspace-workflow-plugin`, `-workspaces-garcia-music`, `-workspaces-lemmings`

### Excluded

- Maps: `-home-codyh-workspace-open-pajero-maps` (T≥75 workers = 34; remainder already screened in (e))
- Alias: `-home-codyh-workspace-open-pajero-maps--claude-worktrees-brief-34-ceiling-only` (21 agents, 0 with T≥75)
- Temp panel dirs: `-tmp-expansion-panel`, `-tmp-thrash-screen-panel-sonnet`
- Already labeled maps workers (smoking guns, expansion three, thrash three, expand-e three) — N/A (no cross-project candidates)

## Near-misses

**None.** No subagent/worker transcripts outside maps to rank. Workflow-plugin parent sessions (n=79) all index to **T=1** and are not worker JSONLs; not scored.

## Artifacts

- `proofs/validated/ubuntu-raw/RANKING-cross-project-ca977-f-20261001-211725.json`
- `proofs/validated/ubuntu-raw/SUMMARY-ubuntu-raw-cross-project-ca977-f-20261001-211725.json`
- `proofs/validated/gold/packs/SUMMARY-cross-project-ca977-f-20261001-211725.md`
- `proofs/validated/gold/packs/SUMMARY-cross-project-ca977-f-20261001-211725.json`

No gold-bundles. No `--call-jev`. No `parent-pull-v1`. No seat labels.

**Fallthrough:** `hold-until-new-maps-sessions` (NEXT-EXPERIMENTS alternate). Holding does not unlock Jev.
