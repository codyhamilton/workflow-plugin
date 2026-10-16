# PR-ADVERSARIAL-BRITTLE — blocked before seating

Status: **blocked; zero judge calls**

The formal Corpus Ops registry requested for this run was not available at
either supplied path:

- `/home/codyh/workspace/corpus-ops/registry/adversarial-brittle/perturbation-matrix.json`
- `/workspace/corpus-ops/registry/adversarial-brittle/perturbation-matrix.json`

The available Corpus Ops checkout contains only the validation-phase registry.
The workflow-plugin repository and its history also contain no equivalent
`adversarial-brittle` matrix.

Without the frozen matrix, the runner cannot safely determine the formal
perturbation values, five question texts, maps-only corpus cells, or cell IDs.
No cells were reconstructed from batch-003, and no response was sent to
TypeSafe. Consequently:

- seat count: `0`
- cell IDs: none materialized
- flip-rate summary: not estimable
- errors: missing formal registry
- `--call-jev`: not used
- behavior ship: none
- localhost `:8080`: not loaded

The branch was created from the fetched `origin/master` tip before this
blocker was recorded.
