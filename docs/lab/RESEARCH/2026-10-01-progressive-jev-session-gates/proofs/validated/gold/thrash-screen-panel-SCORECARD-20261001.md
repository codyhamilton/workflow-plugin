# Thrash-screen panel scorecard — experiment (d) (2026-10-01)

**Experiment:** `ubuntu-thrash-screen-before-pack-v1`  
**Table:** 3 seats × 12 prefixes. Source JSON: [`thrash-screen-panel-agreement-20261001.json`](thrash-screen-panel-agreement-20261001.json).  
**Narrative:** [`PANEL-FINDINGS-20261001.md`](PANEL-FINDINGS-20261001.md) §(d).

| Gate | Result |
|------|--------|
| H5 (nominal α ≥ 0.40) | **Pass** — α = **0.8276** |
| A0 | **90** on `ca977b9ca0dd`; **null** on `daf933273c8f` and `7b00225cb824` |
| Positive labels | Sonnet **3/12**, Composer **2/12**, Grok **2/12** (all on `ca977b9ca0dd`) |
| Pairwise κ | 0.75 / 0.75 / **1.0** (composer↔grok perfect) |
| Jev / stats sweep | **Blocked** — single non-null A0 |
| Behaviour | **Not shipped** |

Earliest checkout on `ca977b9ca0dd`: Sonnet **75** (also 90, 105); Composer **90** (also 105); Grok **90** (also 105). A0 is the first turn where all three are true, which is **90**.
