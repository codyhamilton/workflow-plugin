# 3-11 — Analytics benchmark on the compacted copy

Raw artifact: `/var/tmp/workflow-compact-copy/bench-3-11.txt` (log: `/var/tmp/workflow-compact-copy/bench-3-11.log`)

- Cases: **2063** (log: `2063 cases`; note the file ends with one blank line, so `wc -l` = 2065 and `wc-1 = 2064` — the blank line makes the brief's `wc-1` formula off by one; the true row count from `awk 'NR>1 && NF>=5'` is 2063).
- Total elapsed: **38m7.571s** (test wall `--- FAIL: TestAnalyticsBench (2288.81s)`).
- Threshold: p95 > 500 ms is a miss.
- **Verdict: Misses** — `243/2063 cases failed the bound; 0 returned non-200`.

## Misses (measures, dimensions, buckets, presets)

- Measures: `conversations` (80), `hook_events` (152), `facets` (3), `summary` (3), `scores` (3), plus bare `conversations/<preset>` endpoints (2).
- Dimensions: `none`, `harness`, `repo_id`, `model`, `hour_of_day`, `weekday`, `event`, `tool`, `conversation_id`, `norm_event`, and pairwise combinations of these.
- Buckets: `none` (202), `day` (9), `week` (9), `month` (9), `hour` (3).
- Presets: `7d` (64), `30d` (64), `90d` (64), `all` (51).

## Cases over 500 ms p95 (case, p95 ms) — all 243

| case | p95_ms |
|---|---|
| facets/7d | 1552.1 |
| summary/7d | 532.9 |
| scores/7d | 4939.0 |
| facets/30d | 1775.7 |
| summary/30d | 753.5 |
| scores/30d | 6574.1 |
| conversations/30d | 566.1 |
| facets/90d | 1822.6 |
| summary/90d | 782.6 |
| scores/90d | 6452.6 |
| conversations/90d | 570.8 |
| query/hook_events/dims=harness/bucket=none/7d | 554.9 |
| query/hook_events/dims=norm_event/bucket=none/7d | 657.6 |
| query/hook_events/dims=event/bucket=none/7d | 668.6 |
| query/hook_events/dims=tool/bucket=none/7d | 627.9 |
| query/hook_events/dims=conversation_id/bucket=none/7d | 630.7 |
| query/hook_events/dims=hour_of_day/bucket=none/7d | 519.2 |
| query/hook_events/dims=harness+repo_id/bucket=none/7d | 897.6 |
| query/hook_events/dims=harness+norm_event/bucket=none/7d | 1156.5 |
| query/hook_events/dims=harness+event/bucket=none/7d | 1148.1 |
| query/hook_events/dims=harness+tool/bucket=none/7d | 1096.8 |
| query/hook_events/dims=harness+conversation_id/bucket=none/7d | 1037.6 |
| query/hook_events/dims=harness+hour_of_day/bucket=none/7d | 1047.0 |
| query/hook_events/dims=harness+weekday/bucket=none/7d | 997.3 |
| query/hook_events/dims=repo_id+norm_event/bucket=none/7d | 1103.6 |
| query/hook_events/dims=repo_id+event/bucket=none/7d | 1117.1 |
| query/hook_events/dims=repo_id+tool/bucket=none/7d | 1036.6 |
| query/hook_events/dims=repo_id+conversation_id/bucket=none/7d | 996.5 |
| query/hook_events/dims=repo_id+hour_of_day/bucket=none/7d | 1010.8 |
| query/hook_events/dims=repo_id+weekday/bucket=none/7d | 928.2 |
| query/hook_events/dims=norm_event+event/bucket=none/7d | 1159.3 |
| query/hook_events/dims=norm_event+tool/bucket=none/7d | 1086.3 |
| query/hook_events/dims=norm_event+conversation_id/bucket=none/7d | 1135.9 |
| query/hook_events/dims=norm_event+hour_of_day/bucket=none/7d | 1169.9 |
| query/hook_events/dims=norm_event+weekday/bucket=none/7d | 1092.7 |
| query/hook_events/dims=event+tool/bucket=none/7d | 1109.5 |
| query/hook_events/dims=event+conversation_id/bucket=none/7d | 1198.6 |
| query/hook_events/dims=event+hour_of_day/bucket=none/7d | 1175.6 |
| query/hook_events/dims=event+weekday/bucket=none/7d | 1161.5 |
| query/hook_events/dims=tool+conversation_id/bucket=none/7d | 1102.2 |
| query/hook_events/dims=tool+hour_of_day/bucket=none/7d | 1128.3 |
| query/hook_events/dims=tool+weekday/bucket=none/7d | 1041.5 |
| query/hook_events/dims=conversation_id+hour_of_day/bucket=none/7d | 1118.9 |
| query/hook_events/dims=conversation_id+weekday/bucket=none/7d | 1046.9 |
| query/hook_events/dims=hour_of_day+weekday/bucket=none/7d | 885.0 |
| query/conversations/dims=harness/bucket=none/7d | 780.7 |
| query/conversations/dims=repo_id/bucket=none/7d | 782.0 |
| query/conversations/dims=model/bucket=none/7d | 778.7 |
| query/conversations/dims=hour_of_day/bucket=none/7d | 899.7 |
| query/conversations/dims=weekday/bucket=none/7d | 891.9 |
| query/conversations/dims=harness+repo_id/bucket=none/7d | 1314.1 |
| query/conversations/dims=harness+model/bucket=none/7d | 1293.0 |
| query/conversations/dims=harness+hour_of_day/bucket=none/7d | 1484.4 |
| query/conversations/dims=harness+weekday/bucket=none/7d | 1413.9 |
| query/conversations/dims=repo_id+model/bucket=none/7d | 1291.5 |
| query/conversations/dims=repo_id+hour_of_day/bucket=none/7d | 1455.5 |
| query/conversations/dims=repo_id+weekday/bucket=none/7d | 1436.7 |
| query/conversations/dims=model+hour_of_day/bucket=none/7d | 1440.9 |
| query/conversations/dims=model+weekday/bucket=none/7d | 1413.1 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/7d | 1505.7 |
| query/hook_events/dims=harness/bucket=none/30d | 616.3 |
| query/hook_events/dims=repo_id/bucket=none/30d | 552.6 |
| query/hook_events/dims=norm_event/bucket=none/30d | 749.3 |
| query/hook_events/dims=event/bucket=none/30d | 744.8 |
| query/hook_events/dims=tool/bucket=none/30d | 687.0 |
| query/hook_events/dims=conversation_id/bucket=none/30d | 697.7 |
| query/hook_events/dims=hour_of_day/bucket=none/30d | 572.0 |
| query/hook_events/dims=weekday/bucket=none/30d | 512.3 |
| query/hook_events/dims=harness+repo_id/bucket=none/30d | 1000.9 |
| query/hook_events/dims=harness+norm_event/bucket=none/30d | 1301.8 |
| query/hook_events/dims=harness+event/bucket=none/30d | 1285.9 |
| query/hook_events/dims=harness+tool/bucket=none/30d | 1242.3 |
| query/hook_events/dims=harness+conversation_id/bucket=none/30d | 1200.9 |
| query/hook_events/dims=harness+hour_of_day/bucket=none/30d | 1223.3 |
| query/hook_events/dims=harness+weekday/bucket=none/30d | 1142.0 |
| query/hook_events/dims=repo_id+norm_event/bucket=none/30d | 1242.2 |
| query/hook_events/dims=repo_id+event/bucket=none/30d | 1247.8 |
| query/hook_events/dims=repo_id+tool/bucket=none/30d | 1187.6 |
| query/hook_events/dims=repo_id+conversation_id/bucket=none/30d | 1126.4 |
| query/hook_events/dims=repo_id+hour_of_day/bucket=none/30d | 1120.8 |
| query/hook_events/dims=repo_id+weekday/bucket=none/30d | 1064.0 |
| query/hook_events/dims=norm_event+event/bucket=none/30d | 1298.7 |
| query/hook_events/dims=norm_event+tool/bucket=none/30d | 1231.7 |
| query/hook_events/dims=norm_event+conversation_id/bucket=none/30d | 1324.9 |
| query/hook_events/dims=norm_event+hour_of_day/bucket=none/30d | 1306.8 |
| query/hook_events/dims=norm_event+weekday/bucket=none/30d | 1235.6 |
| query/hook_events/dims=event+tool/bucket=none/30d | 1250.2 |
| query/hook_events/dims=event+conversation_id/bucket=none/30d | 1331.8 |
| query/hook_events/dims=event+hour_of_day/bucket=none/30d | 1300.2 |
| query/hook_events/dims=event+weekday/bucket=none/30d | 1231.1 |
| query/hook_events/dims=tool+conversation_id/bucket=none/30d | 1244.7 |
| query/hook_events/dims=tool+hour_of_day/bucket=none/30d | 1257.0 |
| query/hook_events/dims=tool+weekday/bucket=none/30d | 1201.4 |
| query/hook_events/dims=conversation_id+hour_of_day/bucket=none/30d | 1263.6 |
| query/hook_events/dims=conversation_id+weekday/bucket=none/30d | 1190.5 |
| query/hook_events/dims=hour_of_day+weekday/bucket=none/30d | 996.4 |
| query/conversations/dims=harness/bucket=none/30d | 905.2 |
| query/conversations/dims=repo_id/bucket=none/30d | 913.5 |
| query/conversations/dims=model/bucket=none/30d | 917.4 |
| query/conversations/dims=hour_of_day/bucket=none/30d | 1050.4 |
| query/conversations/dims=weekday/bucket=none/30d | 1021.9 |
| query/conversations/dims=harness+repo_id/bucket=none/30d | 1515.3 |
| query/conversations/dims=harness+model/bucket=none/30d | 1503.6 |
| query/conversations/dims=harness+hour_of_day/bucket=none/30d | 1691.7 |
| query/conversations/dims=harness+weekday/bucket=none/30d | 1679.0 |
| query/conversations/dims=repo_id+model/bucket=none/30d | 1502.0 |
| query/conversations/dims=repo_id+hour_of_day/bucket=none/30d | 1662.9 |
| query/conversations/dims=repo_id+weekday/bucket=none/30d | 1642.0 |
| query/conversations/dims=model+hour_of_day/bucket=none/30d | 1689.5 |
| query/conversations/dims=model+weekday/bucket=none/30d | 1646.2 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/30d | 1710.5 |
| query/hook_events/dims=harness/bucket=none/90d | 624.8 |
| query/hook_events/dims=repo_id/bucket=none/90d | 560.1 |
| query/hook_events/dims=norm_event/bucket=none/90d | 759.7 |
| query/hook_events/dims=event/bucket=none/90d | 760.3 |
| query/hook_events/dims=tool/bucket=none/90d | 706.2 |
| query/hook_events/dims=conversation_id/bucket=none/90d | 712.4 |
| query/hook_events/dims=hour_of_day/bucket=none/90d | 597.5 |
| query/hook_events/dims=weekday/bucket=none/90d | 524.3 |
| query/hook_events/dims=harness+repo_id/bucket=none/90d | 1054.3 |
| query/hook_events/dims=harness+norm_event/bucket=none/90d | 1329.8 |
| query/hook_events/dims=harness+event/bucket=none/90d | 1321.1 |
| query/hook_events/dims=harness+tool/bucket=none/90d | 1274.4 |
| query/hook_events/dims=harness+conversation_id/bucket=none/90d | 1250.2 |
| query/hook_events/dims=harness+hour_of_day/bucket=none/90d | 1216.3 |
| query/hook_events/dims=harness+weekday/bucket=none/90d | 1147.8 |
| query/hook_events/dims=repo_id+norm_event/bucket=none/90d | 1259.9 |
| query/hook_events/dims=repo_id+event/bucket=none/90d | 1266.2 |
| query/hook_events/dims=repo_id+tool/bucket=none/90d | 1201.7 |
| query/hook_events/dims=repo_id+conversation_id/bucket=none/90d | 1151.5 |
| query/hook_events/dims=repo_id+hour_of_day/bucket=none/90d | 1138.3 |
| query/hook_events/dims=repo_id+weekday/bucket=none/90d | 1082.2 |
| query/hook_events/dims=norm_event+event/bucket=none/90d | 1331.4 |
| query/hook_events/dims=norm_event+tool/bucket=none/90d | 1248.3 |
| query/hook_events/dims=norm_event+conversation_id/bucket=none/90d | 1349.4 |
| query/hook_events/dims=norm_event+hour_of_day/bucket=none/90d | 1332.9 |
| query/hook_events/dims=norm_event+weekday/bucket=none/90d | 1251.7 |
| query/hook_events/dims=event+tool/bucket=none/90d | 1247.5 |
| query/hook_events/dims=event+conversation_id/bucket=none/90d | 1340.5 |
| query/hook_events/dims=event+hour_of_day/bucket=none/90d | 1324.4 |
| query/hook_events/dims=event+weekday/bucket=none/90d | 1258.0 |
| query/hook_events/dims=tool+conversation_id/bucket=none/90d | 1249.3 |
| query/hook_events/dims=tool+hour_of_day/bucket=none/90d | 1285.3 |
| query/hook_events/dims=tool+weekday/bucket=none/90d | 1205.6 |
| query/hook_events/dims=conversation_id+hour_of_day/bucket=none/90d | 1288.2 |
| query/hook_events/dims=conversation_id+weekday/bucket=none/90d | 1214.4 |
| query/hook_events/dims=hour_of_day+weekday/bucket=none/90d | 1021.5 |
| query/conversations/dims=harness/bucket=none/90d | 904.1 |
| query/conversations/dims=repo_id/bucket=none/90d | 945.4 |
| query/conversations/dims=model/bucket=none/90d | 940.6 |
| query/conversations/dims=hour_of_day/bucket=none/90d | 1063.6 |
| query/conversations/dims=weekday/bucket=none/90d | 1039.6 |
| query/conversations/dims=harness+repo_id/bucket=none/90d | 1546.3 |
| query/conversations/dims=harness+model/bucket=none/90d | 1538.2 |
| query/conversations/dims=harness+hour_of_day/bucket=none/90d | 1722.1 |
| query/conversations/dims=harness+weekday/bucket=none/90d | 1696.9 |
| query/conversations/dims=repo_id+model/bucket=none/90d | 1568.7 |
| query/conversations/dims=repo_id+hour_of_day/bucket=none/90d | 1704.4 |
| query/conversations/dims=repo_id+weekday/bucket=none/90d | 1670.6 |
| query/conversations/dims=model+hour_of_day/bucket=none/90d | 1708.3 |
| query/conversations/dims=model+weekday/bucket=none/90d | 1684.0 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/90d | 1740.2 |
| query/hook_events/dims=harness/bucket=none/all | 685.5 |
| query/hook_events/dims=repo_id/bucket=none/all | 606.9 |
| query/hook_events/dims=norm_event/bucket=none/all | 859.6 |
| query/hook_events/dims=event/bucket=none/all | 836.4 |
| query/hook_events/dims=tool/bucket=none/all | 762.3 |
| query/hook_events/dims=conversation_id/bucket=none/all | 773.9 |
| query/hook_events/dims=hour_of_day/bucket=none/all | 644.1 |
| query/hook_events/dims=weekday/bucket=none/all | 581.8 |
| query/hook_events/dims=harness+repo_id/bucket=none/all | 1121.0 |
| query/hook_events/dims=harness+norm_event/bucket=none/all | 1418.1 |
| query/hook_events/dims=harness+event/bucket=none/all | 1488.8 |
| query/hook_events/dims=harness+tool/bucket=none/all | 1383.4 |
| query/hook_events/dims=harness+conversation_id/bucket=none/all | 1333.9 |
| query/hook_events/dims=harness+hour_of_day/bucket=none/all | 1318.2 |
| query/hook_events/dims=harness+weekday/bucket=none/all | 1251.3 |
| query/hook_events/dims=repo_id+norm_event/bucket=none/all | 1360.3 |
| query/hook_events/dims=repo_id+event/bucket=none/all | 1365.6 |
| query/hook_events/dims=repo_id+tool/bucket=none/all | 1285.7 |
| query/hook_events/dims=repo_id+conversation_id/bucket=none/all | 1236.4 |
| query/hook_events/dims=repo_id+hour_of_day/bucket=none/all | 1253.3 |
| query/hook_events/dims=repo_id+weekday/bucket=none/all | 1172.6 |
| query/hook_events/dims=norm_event+event/bucket=none/all | 1497.8 |
| query/hook_events/dims=norm_event+tool/bucket=none/all | 1373.4 |
| query/hook_events/dims=norm_event+conversation_id/bucket=none/all | 1456.8 |
| query/hook_events/dims=norm_event+hour_of_day/bucket=none/all | 1444.9 |
| query/hook_events/dims=norm_event+weekday/bucket=none/all | 1373.4 |
| query/hook_events/dims=event+tool/bucket=none/all | 1377.0 |
| query/hook_events/dims=event+conversation_id/bucket=none/all | 1460.8 |
| query/hook_events/dims=event+hour_of_day/bucket=none/all | 1453.0 |
| query/hook_events/dims=event+weekday/bucket=none/all | 1356.4 |
| query/hook_events/dims=tool+conversation_id/bucket=none/all | 1349.3 |
| query/hook_events/dims=tool+hour_of_day/bucket=none/all | 1385.9 |
| query/hook_events/dims=tool+weekday/bucket=none/all | 1305.8 |
| query/hook_events/dims=conversation_id+hour_of_day/bucket=none/all | 1448.0 |
| query/hook_events/dims=conversation_id+weekday/bucket=none/all | 1378.2 |
| query/hook_events/dims=hour_of_day+weekday/bucket=none/all | 1109.0 |
| query/conversations/dims=harness/bucket=none/all | 956.2 |
| query/conversations/dims=repo_id/bucket=none/all | 1024.1 |
| query/conversations/dims=model/bucket=none/all | 1004.3 |
| query/conversations/dims=hour_of_day/bucket=none/all | 1180.1 |
| query/conversations/dims=weekday/bucket=none/all | 1140.1 |
| query/conversations/dims=harness+repo_id/bucket=none/all | 1643.8 |
| query/conversations/dims=harness+model/bucket=none/all | 1692.7 |
| query/conversations/dims=harness+hour_of_day/bucket=none/all | 1877.4 |
| query/conversations/dims=harness+weekday/bucket=none/all | 1833.5 |
| query/conversations/dims=repo_id+model/bucket=none/all | 1685.9 |
| query/conversations/dims=repo_id+hour_of_day/bucket=none/all | 1850.4 |
| query/conversations/dims=repo_id+weekday/bucket=none/all | 1804.6 |
| query/conversations/dims=model+hour_of_day/bucket=none/all | 1861.5 |
| query/conversations/dims=model+weekday/bucket=none/all | 1800.1 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/all | 1893.9 |
| query/hook_events/dims=harness/bucket=hour/7d | 888.6 |
| query/conversations/dims=none/bucket=hour/7d | 566.2 |
| query/conversations/dims=harness/bucket=hour/7d | 1130.4 |
| query/hook_events/dims=harness/bucket=day/7d | 878.9 |
| query/conversations/dims=none/bucket=day/7d | 564.6 |
| query/conversations/dims=harness/bucket=day/7d | 1129.8 |
| query/hook_events/dims=harness/bucket=week/7d | 832.7 |
| query/conversations/dims=none/bucket=week/7d | 525.9 |
| query/conversations/dims=harness/bucket=week/7d | 1091.1 |
| query/hook_events/dims=harness/bucket=month/7d | 872.7 |
| query/conversations/dims=none/bucket=month/7d | 586.2 |
| query/conversations/dims=harness/bucket=month/7d | 1150.2 |
| query/hook_events/dims=harness/bucket=day/30d | 995.6 |
| query/conversations/dims=none/bucket=day/30d | 670.7 |
| query/conversations/dims=harness/bucket=day/30d | 1284.2 |
| query/hook_events/dims=harness/bucket=week/30d | 927.4 |
| query/conversations/dims=none/bucket=week/30d | 630.7 |
| query/conversations/dims=harness/bucket=week/30d | 1227.0 |
| query/hook_events/dims=harness/bucket=month/30d | 997.8 |
| query/conversations/dims=none/bucket=month/30d | 680.8 |
| query/conversations/dims=harness/bucket=month/30d | 1315.1 |
| query/hook_events/dims=harness/bucket=day/90d | 1017.4 |
| query/conversations/dims=none/bucket=day/90d | 697.7 |
| query/conversations/dims=harness/bucket=day/90d | 1311.8 |
| query/hook_events/dims=harness/bucket=week/90d | 940.4 |
| query/conversations/dims=none/bucket=week/90d | 626.8 |
| query/conversations/dims=harness/bucket=week/90d | 1237.7 |
| query/hook_events/dims=harness/bucket=month/90d | 1003.1 |
| query/conversations/dims=none/bucket=month/90d | 695.2 |
| query/conversations/dims=harness/bucket=month/90d | 1316.9 |

## Worst ten cases overall (case, p95 ms)

| case | p95_ms |
|---|---|
| scores/30d | 6574.1 |
| scores/90d | 6452.6 |
| scores/7d | 4939.0 |
| query/conversations/dims=hour_of_day+weekday/bucket=none/all | 1893.9 |
| query/conversations/dims=harness+hour_of_day/bucket=none/all | 1877.4 |
| query/conversations/dims=model+hour_of_day/bucket=none/all | 1861.5 |
| query/conversations/dims=repo_id+hour_of_day/bucket=none/all | 1850.4 |
| query/conversations/dims=harness+weekday/bucket=none/all | 1833.5 |
| facets/90d | 1822.6 |
| query/conversations/dims=repo_id+weekday/bucket=none/all | 1804.6 |

## Unpriced share (read-only, compacted copy `/var/tmp/workflow-compact-copy/data/local/ledger.db`)

- Total `norm_event='usage'` rows: **33464**
- Unpriced (`cost_reported is null`, after stripping one `provider/` prefix, none of the stripped names are keys in `tools/transcript/pricing.json`): **28342**
- `tools/transcript/pricing.json` has **8** top-level keys (`_meta`, `claude-4.6-sonnet-high-thinking`, `composer-2.5`, `composer-2.5-fast`, `gemini-3.5-flash`, `glm-5.2-high`, `glm-5.2-high-thinking`, `kimi-k2.5`); every unpriced model's stripped name is absent from this set, so all 28342 remain unpriced. Counts only.

## Live ledger mtime

- Before: `2026-10-11 12:32:41.180695802 +1000`
- After: `2026-10-11 12:52:42.077722151 +1000` — **NOT unchanged** (the live ledger mtime changed by ~20 min; the benchmark ran read-only against the copy, so this is unexpected and should be accounted for).

## DONE evidence

- `cd tools/workflow && go test ./internal/serve` (no bench env vars): `ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	(cached)` — pass (cached).

## Departures / notes

- Benchmark FAILED the p95 bound (243 misses); run is conclusive as a failure, not inconclusive.
- Live ledger mtime changed (see above) — brief expected it unchanged.
- Case-count formula `(wc -l)-1` is off by one due to a trailing blank line; reported 2063 to match the log.
- No causes root-caused in this brief; timings/counts only.
