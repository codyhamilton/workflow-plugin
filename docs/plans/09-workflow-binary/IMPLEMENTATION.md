# Workflow binary implementation

Tool: Claude Code (Opus 5.5 orchestrator, subagent workers), on `hooks-reconcile`.
Run identity: session https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp, starting HEAD
`9e79ede`.
Started: 2026-10-05 (Australia/Brisbane).

Unattended run: the maintainer asked for designs 3 to 5 and execution of everything designed, with
no stops, on this branch. No push, tag, release publish or PR. Go 1.27.1 was installed to
`~/.local/go` for the build (no system Go existed).

Execution logging uses the legacy `workflow-quality` service on 8765 while it is still the live
ledger; phase 5 retires that requirement.
