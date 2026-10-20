# Brief: phase4-skill-docs-release — Login skill, status line, docs, version

Consumer: a worker on the plugin tree, the Python client, `install.sh` and the stable design docs. Phase 4, the only code unit. The deploys and the live `/yakka:login` check are not yours: the runner handles them.
Owned paths: `plugins/yakka/skills/login/SKILL.md` (new), `plugins/yakka/client/yakka.py` (`run_status` only), `plugins/yakka/client/test_status.py`, the three `plugin.json` files under `plugins/yakka/`, `plugins/yakka/bin/VERSION`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `install.sh`, `docs/design/03-remote-service.md`, `05-distribution.md`, `07-analytics-site.md`, `docs/plans/19-device-login/DESIGN.md` (only the `serve.go (sweep)` Surfaces line in Phase 1), `CHANGELOG.md`. Touch nothing else.
Commits: one commit on `feat/device-login`; include the report in it.
Report: write `docs/plans/19-device-login/reports/phase4-skill-docs-release.md` (a handoff; rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: Phases 1–3 (closed). Runs alongside: nothing.
Budget: read 12 files, about 400 lines changed, 50 tool turns. Past the budget, stop: write a handoff in your report and say `over budget`.

## Required reading, in order

1. `docs/plans/19-device-login/DESIGN.md`: "Domain: Login skill (plugin)", "Architectural Implications", Phase 4.
2. `plugins/yakka/skills/refine/SKILL.md` and one other skill: the frontmatter and tone to match.
3. `plugins/yakka/client/yakka.py` `run_status`, and `plugins/yakka/client/test_status.py`. Find how `Load()` reports env versus file (`YAKKA_ENDPOINT`/`YAKKA_KEY`).
4. `install.sh` (skill lists at the `echo "  Skills: ..."` lines, `ensure_opencode_skills`, and the Claude Code prompt near line 619).
5. The three `plugin.json` files, both `marketplace.json` files, `tools/release/test_layout.py` (what it pins).
6. `docs/design/03-remote-service.md`, `05-distribution.md`, `07-analytics-site.md`; `CHANGELOG.md` head.
7. `docs/plans/19-device-login/reports/phase3-client-login.md` for the real command behaviour.

## Goal

A user in any harness can run `/yakka:login` (or the equivalent skill) and an agent drives `yakka login start` / `wait` without reading secrets; `yakka status` says when the environment overrides `client.toml`; the version, manifests, installer and stable docs all describe the device-code login.

## Contract

The design's Login skill contract wins over this brief on any conflict.
- `SKILL.md`: frontmatter `name: login` and a one-sentence `description`, then the steps. Run `yakka login start` (add `--endpoint` only if the user named one); show the user the `url:` and `code:` lines and say to check the code on the page matches; run `yakka login wait` as a long-running or background command; when it exits, run `yakka status` and report its `config:` and `endpoint:` lines. If `config:` says `env`, warn that the environment overrides the login. Never read, print or edit `client.toml` or the `.pending` file; never print a token or `device_code`. For a remote or headless session, tell the user to set `YAKKA_ENDPOINT` and `YAKKA_KEY` instead.
- `run_status`: when `YAKKA_ENDPOINT` and `YAKKA_KEY` come from the environment (remote mode), print `config: env (remote mode)`; otherwise unchanged. A half-set environment keeps its current output.
- Versions: the three `plugin.json` files carry the same bumped version (`3.1.0`). `plugins/yakka/bin/VERSION` is the Go binary's version (`0.2.0`, a separate series from the plugin's); the binary lost `login`, so bump it to `0.3.0`. The design says "bump together", which conflicts with two series: do what is stated here and record the conflict in the report.
- Descriptions: the plugin and marketplace descriptions name `login` but not as cloud-safe core (for example: "Cloud-safe core: design, ... post-build. Also login (interactive)."). `install.sh`: the skill lists and the OpenCode symlink list gain `login`; do not edit `CORE_SKILLS` in `tools/driver/check_skills.py`.
- Docs, per Architectural Implications "Stable docs to update". Also fix the `serve.go (sweep)` Surfaces line in the Phase 1 section of `DESIGN.md` (no sweep exists in `serve.go`; expired grants are swept inside the grant table in `device_grants.go`).
- `CHANGELOG.md`: a `3.1.0` entry at the top: device-code login, `login start`/`wait`, `/yakka:login`, 3.0.1 clients cannot log in until updated (existing tokens keep working), the Go `yakka login` removal.

## Done evidence

- `cd plugins/yakka/client && python3 -m unittest test_status test_login` passes, including a new test that `config: env (remote mode)` prints with both env vars set and the old line without.
- `python3 tools/release/test_layout.py` passes. Run `python3 tools/release/test_release.py` except `BuildTests.test_7_build_sh`, which needs Go 1.27.1 and also deletes the tracked `site/` directory; do not run it.
- `bash -n install.sh`; with `YAKKA_OPENCODE_SKILLS=<temp dir> ./install.sh --opencode-skills` (use a temp dir only), `<temp>/login` is a symlink to `plugins/yakka/skills/login`.
- `grep -n "plaintext" docs/design/07-analytics-site.md` shows no plaintext-device-code clause in open issue 18; design 03 lists the three device routes with auth; design 05 mentions `start`/`wait`.
- The three `plugin.json` files and the two marketplace entries agree on version and mention `login`.

## Report back

What was done with results; every departure and why (including the version-series conflict); deferred work; known problems. Final message: commit hash, test results, departures, under 200 words. If the brief contradicts the code or the design, record it; do not work around it silently.
