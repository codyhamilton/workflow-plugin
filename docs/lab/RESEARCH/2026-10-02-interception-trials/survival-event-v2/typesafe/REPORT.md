# PR-SURVIVAL-EVENT-v2 — TypeSafe trial report

- Driver: TypeSafe `jev-1.13.0`
- Scope: maps-only; no behavior ship; no `--call-jev`; no `:8080`
- Seats: **36/36** successful (`12 workers × 3 seats`)
- Protocol sha256: `eb3386c13c2936e83bef81ac21186c1a4a416ea3f196e391237d4c4b41d90bcd` verified
- Wire: `noul` for free-form rationale; stage 2 is parsed as the protocol’s integer|null contract
- Supersedes PR-SURVIVAL-EVENT v1 / #134; no same-Q reseat

## Outcomes

| Stratum | Seats | `event_observed` | `censored_productive` | `censored_unclear` | Valid stage-2 times |
|---|---:|---:|---:|---:|---:|
| thrash | 6 | 5 | 0 | 1 | 0 |
| poll/monitor | 12 | 1 | 10 | 1 | 0 |
| weak | 6 | 0 | 0 | 6 | 0 |
| residual | 12 | 0 | 12 | 0 | 0 |

Choice scraping passed **36/36** with `response_class == response_label`.
All six `event_observed` seats returned stage 2 `null`, so event-time
agreement is not estimable and exploratory Cox is not estimable. Per protocol,
the framing is **killed**: stage 1 recovered thrash events, but stage 2 was
always null.

The first schema attempt produced 36 HTTP 400 responses because TypeSafe does
not accept `integer|null` as a wire type. Those attempts remain in `raw/` for
audit. The corrected run used generated integer/null choice labels and returned
36 HTTP 200 responses with no final errors.

## Cell IDs

`dc1ea44c443405a8`, `869bedd16f306618`, `cceeb1269bfe2a71`,
`7064cdfacacc5cc9`, `c052ed4bfce250bb`, `700921036b972803`,
`9c53b1be9c97b824`, `a91a996d37c36707`, `ea296ea385fb1888`,
`b5600acc8d75f0c1`, `78f1e6a2b5319227`, `98885377ae61d613`,
`c71746eb6c33ec85`, `97ca3ca86a94e5ec`, `5fb244d416db2d4d`,
`a8f7b0960c907bd8`, `096da351a69598c9`, `e9985f8ab26abf0d`,
`e841356f2e1db2a1`, `ba5c665f014a4d4d`, `552e59b30389840b`,
`d6f5e81d28cda7ce`, `a839e094ae3d997a`, `bb94951d1037b155`,
`8a3dd45ed024ee19`, `a1e5b5fd6baab103`, `5fb6c0f78884716c`,
`915cd5f7375bb3af`, `78d7477152c8eeff`, `cac85d8ac4450ee8`,
`1f56a6573a03ce8e`, `2582d2070a22fe58`, `d8c3b1599d389b43`,
`440b5c18ef79ba52`, `3756766e58cf82f9`, `15d8c1d1ea4c23d1`.
