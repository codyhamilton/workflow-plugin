# PR-SURVIVAL-EVENT TypeSafe seat

Maps-only research artifact. No behavior ship, product wiring, `--call-jev`, or localhost:8080 use.

- Protocol SHA-256: `b32652421d15dcd85ecc920c6bcd13d5304b9ce457dc17c69bbe8213549cf26d`
- Driver/model: TypeSafe `jev-1.13.0`
- Stratum: `maps-5h`
- Calls: 36/36 HTTP-successful and parsed
- Maximum stimulus: 8640 characters
- Exact three-seat event-time agreement: 1.000
- Observed event times: all 36 answers were `null` (censored/no supported event in the shown window).
- Cox kill: not fired; the 2-covariate LOO gate was not evaluable because there were fewer than two observed events. This is not evidence of a pass.
- Agreement kill: not evaluable because the protocol does not provide the prefix-causal alpha baseline; exact agreement is trivially 1.000 because all seats returned `null`.
- Queue gate: **not met**. PR [#133](https://github.com/codyhamilton/workflow-plugin/pull/133) was still OPEN when checked after execution; preserve these results as audit evidence, but do not treat this batch as a valid post-#133 seat.

See `results.jsonl`, `raw/`, `agreement-summary.json`, `cox-summary.json`, and `meters.json` for the complete record.

## Cell IDs

| Worker | Seat | T (analysis metadata) | Cell ID |
|---|---:|---:|---|
| `92a48e004519` | 1 | 296 | `d4d27f76c2967282` |
| `92a48e004519` | 2 | 296 | `8b9f1f7fd16a54fc` |
| `92a48e004519` | 3 | 296 | `9d2502a7acff835a` |
| `ca977b9ca0dd` | 1 | 109 | `905e2dec01326d0f` |
| `ca977b9ca0dd` | 2 | 109 | `6f56ad468c1b490e` |
| `ca977b9ca0dd` | 3 | 109 | `1c14c8285ae554ae` |
| `87a380bc64ff` | 1 | 89 | `d4253111107cd551` |
| `87a380bc64ff` | 2 | 89 | `72c180cc3ad8288f` |
| `87a380bc64ff` | 3 | 89 | `fb39094879bd979c` |
| `bb6165018de0` | 1 | 154 | `b07ae1602998159c` |
| `bb6165018de0` | 2 | 154 | `bf792640693694c3` |
| `bb6165018de0` | 3 | 154 | `d36dc610b5ed7732` |
| `15f24c7ba18c` | 1 | 93 | `f7a6d27f3760ddf8` |
| `15f24c7ba18c` | 2 | 93 | `425ad27940d8c46a` |
| `15f24c7ba18c` | 3 | 93 | `34a1b4d49f862aea` |
| `8e36f8e80baa` | 1 | 97 | `387116a58aa96911` |
| `8e36f8e80baa` | 2 | 97 | `8549c8c10aae1df3` |
| `8e36f8e80baa` | 3 | 97 | `a9f750358a394b3b` |
| `daf933273c8f` | 1 | 122 | `8c5d5f59739633b0` |
| `daf933273c8f` | 2 | 122 | `45d851276aa1386e` |
| `daf933273c8f` | 3 | 122 | `153a2a38c6aef66a` |
| `07357f196666` | 1 | 83 | `0a5ca10ff05403a2` |
| `07357f196666` | 2 | 83 | `e051162db96c8054` |
| `07357f196666` | 3 | 83 | `05d0a5fc3114a46b` |
| `0677f597286e` | 1 | 93 | `0fe5ec674bfd188a` |
| `0677f597286e` | 2 | 93 | `6e839325a1fffeb6` |
| `0677f597286e` | 3 | 93 | `827d91c5992c85da` |
| `074c8cf22927` | 1 | 76 | `773a02fbc203e82c` |
| `074c8cf22927` | 2 | 76 | `30beffa3c08561f2` |
| `074c8cf22927` | 3 | 76 | `7abda696731727d1` |
| `0853bc21d3aa` | 1 | 155 | `541a6f3f8c4a6a0c` |
| `0853bc21d3aa` | 2 | 155 | `329aa06b08aaa5b7` |
| `0853bc21d3aa` | 3 | 155 | `cefea878ef0c49ea` |
| `16a958631580` | 1 | 94 | `36ccc4aeba2666b9` |
| `16a958631580` | 2 | 94 | `417bf3e78db87edb` |
| `16a958631580` | 3 | 94 | `040402e242e770fd` |
