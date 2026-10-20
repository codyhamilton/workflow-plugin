import type { AggregateAsk, AggregateRequest } from '../../aggregate';

export type ExplorationToolId = 'explore' | 'usage' | 'quality' | 'conversations' | 'saved';

export const USAGE_TREND_MEASURES = [
	'cost_usd',
	'model_calls',
	'tokens_in',
	'tokens_out',
	'unpriced_calls',
	'tokens_cache_read',
	'tokens_cache_write',
	'tokens_reasoning'
] as const;

export type UsageTrendMeasure = (typeof USAGE_TREND_MEASURES)[number];

export const TOOL_OPTIONS: { id: ExplorationToolId; label: string }[] = [
	{ id: 'explore', label: 'Breakdowns' },
	{ id: 'usage', label: 'Usage and cost' },
	{ id: 'quality', label: 'Quality' },
	{ id: 'conversations', label: 'Conversations' },
	{ id: 'saved', label: 'Saved analysis' }
];

export function isUsageTrendAsk(ask: AggregateAsk): boolean {
	return (
		ask.ask === 'trend' &&
		ask.dim === 'model' &&
		(USAGE_TREND_MEASURES as readonly string[]).includes(ask.measure)
	);
}

export function toolForAsk(ask: AggregateAsk): ExplorationToolId {
	if (ask.ask === 'quality') return 'quality';
	if (ask.ask === 'conversations' || ask.ask === 'conversation') return 'conversations';
	if (ask.ask === 'distribution') return 'usage';
	if (isUsageTrendAsk(ask)) return 'usage';
	return 'explore';
}

export function defaultAskForTool(tool: ExplorationToolId): AggregateAsk {
	switch (tool) {
		case 'usage':
			return { ask: 'trend', measure: 'cost_usd', bucket: 'day', dim: 'model' };
		case 'quality':
			return { ask: 'quality', kind: 'design', bucket: 'day' };
		case 'conversations':
			return { ask: 'conversations' };
		case 'saved':
		case 'explore':
			return { ask: 'trend', measure: 'hook_events', bucket: 'day' };
	}
}

export function switchTool(request: AggregateRequest, tool: ExplorationToolId): AggregateRequest {
	if (tool === 'saved') return request;
	if (toolForAsk(request.ask) === tool) return request;
	return { ...request, ask: defaultAskForTool(tool) };
}
