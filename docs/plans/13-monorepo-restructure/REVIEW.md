# Review

Verdict: **PASS_WITH_FOLLOWUPS**

Reviewed SHA: `2f4e3bcb096a63c3f81bb09cf396845afc74e166`

Independent review of the whole design after phases 1–7. Three focused passes: layout contracts, the yakka rename against the residual scan, and the protocol writers plus stable docs. No blocker or high finding. No fix pass.

The logged-in Cursor session check in the Phase 3 outcome was not run. The user instructed that it is manual and must not block. It is a residual risk, not a finding.

## Phase outcomes

Where a later phase renames an earlier proof, the later outcome is what was judged.

| Phase | Assessment | Evidence |
|---|---|---|
| 1 Lab collapse | Met, then renamed | Maintainer skills are `.claude/skills/{iterate,jev-variants,setup,transcript-parser,white-paper,yakka-tuning}`. `plugins/workflow-lab` is gone. Live search for `plugins/workflow-lab` and `lab-proposal`, excluding `docs/plans/`, dated `docs/lab/{PROPOSALS,RESEARCH}/`, and earlier changelog entries, has no hits. The Phase 1 marketplace name `workflow` is the Phase 6 name `yakka`. |
| 2 Packages | Met, then renamed | Runtime units are `packages/yakka`, `packages/hooklog`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`. Catalogue is `packages/yakka/catalogue/`. No live `tools/workflow` or `tools/hooklog` tree. |
| 3 Cursor plugin | Partial | Both marketplaces list one plugin, `yakka`, `source` `plugins/yakka`. Every command in `plugins/yakka/hooks/cursor.json` is `./script/...`; `script/spool.sh` and `script/prefetch-version.sh` exist. Install-route tests cover copying that tree. The logged-in session that must fire a hook was not run. |
| 4 Layout contract | Met | `python3 -m unittest tools.release.test_layout` — 7 tests OK, including the six failure fixtures. Signal-log resolvers in `packages/opencode-yakka-hooks/python/batch_flush_cli.py` and `tools/driver/jev_signal_log.py` both use `~/.local/state/yakka/jev-signal-log.jsonl` and `YAKKA_JEV_SIGNAL_LOG`. `tools/README.md` and `packages/README.md` index their directories. `docs/design/05-distribution.md` has a Layout section. |
| 5 Runtime rename | Met | Module `github.com/codyhamilton/yakka/packages/yakka`, `cmd/yakka`, `plugins/yakka/bin/yakka`, MCP `serverInfo.name` `yakka`. npm names `@codyhamilton/yakka-analytics` and `@codyhamilton/opencode-yakka-hooks`. `bin/VERSION` is `0.2.0`. Cursor commands stay `./script/...`. Phase 5 residual scan scope is inside the clean full scan below. |
| 6 Protocol | Met | Manifests are `yakka` `3.0.0`. `tools/driver/trailer_keys.py` is the shared key list. `tools/driver/tests/test_status.py` `test_dual_trailer_keys_open_phase_three` closes phase 1 with `Workflow-Phase` and phase 2 with `Yakka-Phase` and expects open phase 3. `evals/scenarios/trailer-completeness/verify.py` loops `PHASE_TRAILER_KEYS`. `install.sh` and `tools/cloud-env/bootstrap-yakka-skills.sh` use yakka paths; there is no `bootstrap-workflow-skills.sh`. Core skills write `Yakka-Phase`, `Yakka-Plan`, and `yakka-report`; `execute`, `comprehensive-review`, and `post-build` each have one sentence that accepts the legacy forms. |
| 7 Docs and guide | Met | `python3 tools/release/scan_residual_names.py --scope all` exits 0. `README.md` install text uses `codyhamilton/yakka` and `yakka@yakka`. The `3.0.0` changelog entry is the migration guide (env map, state paths, four harnesses, maintainer actions 1–8). `docs/ARCHITECTURE.md` and `docs/design/system-architecture.md` state the dual-read rule. `docs/design/04-advisory-surface.md` points phase closure at that section rather than repeating the sentence. |

## Intent and ledger

The implementation matches the verbatim intent: the lab is project skills, runtime units are packages, the plugin is `plugins/yakka`, and the product name is yakka with a hard break and permanent dual-read.

Ledger: Assumptions 1 and 4–10 and 12 still hold. Assumption 2 was superseded by Decision 2 and that supersession is what shipped. Assumption 3's `packages/workflow` name was the name through Phase 4; Phase 5 renamed it to `packages/yakka` as the design sequenced. Assumption 11's state directory is `yakka` after the rename, and the package and `tools/driver` resolve the same path. No assumption failed.

## Findings

### Medium

- **Follow-up.** `docs/lab/bootstrap/session-start.sh` still curls `https://raw.githubusercontent.com/codyhamilton/workflow-plugin/master/install.sh`. `docs/lab/CONSUMING_REPO.md` still documents that repo and `bootstrap-workflow-skills.sh`, which this branch deletes. The residual scan skips `docs/lab/` by the scan contract, so the Phase 7 done check stays green. These two files are live bootstrap instructions, not dated research. Recorded in `docs/design/05-distribution.md`.

### Low

- **Follow-up.** `packages/hooklog/tests/test_hooklog.py` and `test_spool_queue.py` set `YAKKA_QUALITY_URL`. Nothing in `packages/hooklog` reads it. The legacy service still reads `WORKFLOW_QUALITY_URL`, which the names contract keeps. The blanked variable does not configure that service.
- **Follow-up.** `tools/driver/README.md` still describes only `Workflow-Phase` and a `workflow-report` fence. The driver accepts both keys and both fences. The residual scan exempts all of `tools/driver/` for those two patterns, so the README is invisible to the done check.

No blocker. No high. Nothing briefed.

## Plan sufficiency

The design was enough to determine intent, place these findings, and derive QA. Outcomes are tagged `[test]`, `[cmd]`, or `[judgement]`, and the names table plus the residual-scan contract make the rename checkable. The gap that produced the empty trailer commits is outside the design: a blank line before `Co-authored-by` keeps `Workflow-Phase` out of the trailer block, which `git interpret-trailers` confirmed for the phase 4–6 closing commits. The design did not say how a co-author trailer has to sit on the same block.

## Residual risks

- A logged-in Cursor session that installs this marketplace entry and shows a `./script/...` hook landing in the queue, then `yakka drain` to a local `yakka serve`, has not been run.
- `artifact_feedback` was unreachable for every phase (workflow MCP tool discovery failed). No brief or report was scored.
- Until the GitHub repository is renamed and a `3.0.0` release is published, `install.sh` and the wrapper's release URL name a repository and assets that do not exist yet. That is the migration guide's maintainer action, not a code miss.
- `spool.sh` still exits 0 when it cannot record an event. The design already accepts that silent failure.
