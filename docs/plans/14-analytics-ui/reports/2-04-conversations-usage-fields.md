Status: done

## What changed

- **Store** (`analytics.go`): `ConvRow` gains `model`, `model_calls`, `unpriced_calls`, `cost_usd`, `tokens_in`, `tokens_out`. `fillConvUsage` loads kept usage calls via `usageKeptRows` scoped to the page's conversation ids, aggregates totals, and sets `model` with `dominantModel` (same rule as distribution conversation grain). Called from `ConversationsPage` and `Conversations`.
- **Serve** (`analytics.go`): `analyticsConversations` JSON rows include the six new fields; `cost_usd` uses store `roundCost`.
- **Tests**: store `TestAnalyticsConversations` adds in-window usage on `c1` and asserts dominant `alpha`; serve conversations subtest expects usage keys (zeros on the ingest fixture) and checks keys on every row.

## Done evidence

**Before** (usage assertions absent; handler/store fields missing): adding the store usage block would fail, e.g. `c1 usage: {Model: ...}` with empty model and zero counts.

```
go test ./internal/store/ -run 'TestAnalyticsConversations|TestConversationsPage' -count=1
# TestAnalyticsConversations usage block: model "" want alpha

go test ./internal/serve/ -run 'TestAnalytics.*Conversation|TestAnalyticsBenchSmoke' -count=1
# conversations subtest: DeepEqual c1 row missing usage keys once handler extended
```

**After**:

```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store	0.034s
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve	2.301s
```

## Deviations

None.

## Contradictions

None.
