---
cursor:
  subagentId: "bc-18ac155d-32a9-56ea-8ffe-794d87775868"
---

# Report: 2-02 — `wk_` workflow token secret scrub

**Status:** done

## What changed

- Added `workflow_api_token` to the shared `patterns` list in `secrets.go`: `\bwk_[A-Za-z0-9_-]{32,}` (32-byte random body is base64url-encoded to 43 chars in `generateTokenPlaintext`).
- Extended `samples()` with a split `wk_` + 32-char body sample; `TestScanPatterns` covers `Scan`, `Redact`, and no re-hit on redacted text.

## Checks

**Before** (sample added, pattern not yet — `TestScanPatterns`):

```
--- FAIL: TestScanPatterns (0.00s)
    secrets_test.go:41: pattern workflow_api_token not listed in Patterns()
    secrets_test.go:47: workflow_api_token: hits = []
    secrets_test.go:59: patterns [private_key_block sk_key github_token github_pat aws_access_key slack_token google_api_key stripe_key jwt bearer_token connection_string env_assignment] vs samples 13
FAIL
```

**After:**

```
cd tools/workflow && GOTOOLCHAIN=auto go test ./internal/secrets/ -count=1
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/secrets	0.205s
```

`Redact` on text containing `wk_` + 32+ alnum/`-_` chars replaces the token with `[REDACTED:workflow_api_token]`.

## Deviations

None.

## Contract notes

None. Pattern name `workflow_api_token` matches the design’s “same as other prefixes” scrub behavior; minimum body length aligns with issued tokens from 2-01 without matching short placeholders like `wk_notreal` in serve tests.
