# Execution report: 5-01 version and init (brief 225, exec 27)

## Done
- `main.go`: `--version`/`version` print `workflow <version> <commit>`; `init` case; usage string updated.
- `init.go`: `runInit` per the brief (only-if-absent files, 0700 dirs/0600 files with explicit chmod, key from
  `clientconfig.Load` when client.toml exists else 32 random bytes hex, no TYPESAFE_API_KEY written, no process executed).
- `init_test.go`: `TestVersion`, `TestInit` (writes+second run, existing client.toml, no WORKFLOW_ROOT, fake systemctl).

## Evidence
- Before: `go test -run 'TestVersion|TestInit' ./cmd/workflow` failed (`--version: exit status 2`, init exit 2 with old usage).
- After: `go vet ./... && go test -race -count=1 ./...` all ok; `-run 'TestVersion|TestInit' -v`:
  `--- PASS: TestVersion`, `--- PASS: TestInit` (subtests writes, existing_client.toml, no_root, no_systemctl).

## Departures
- Init tests use a minimal explicit child environment (HOME, XDG_CONFIG_HOME, PATH, sentinel) rather than `newEnv`, so nothing from the real environment leaks.

## Unfinished / known problems
- None. `WORKFLOW_CLIENT_CONFIG`, if set, redirects client.toml only (via `clientconfig.Path`), as briefed; unit and serve.env stay under `$HOME`.

## Sample `init` stdout (temp HOME, key not printed)
```
wrote  <tmp>/h/.config/workflow/client.toml
wrote  <tmp>/h/.config/workflow/serve.env
wrote  <tmp>/h/.config/systemd/user/workflow-serve.service

To enable screening, create <tmp>/h/.config/workflow/serve.secrets.env (mode 0600) holding TYPESAFE_API_KEY=...
Nothing is enabled or started. To enable the local service, run:
systemctl --user daemon-reload && systemctl --user enable --now workflow-serve.service
```
