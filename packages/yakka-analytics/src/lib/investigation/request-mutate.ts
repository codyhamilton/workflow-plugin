import type { AggregateFilters, AggregateRequest, AggregateWindow } from '../aggregate';
import { applyDrill, parseUrlState, type DimKey, type UrlState } from '../urlstate';
import { investigationRequestToSearch } from './request-url';

export function requestToUrlState(request: AggregateRequest, now: Date): UrlState {
	return parseUrlState(investigationRequestToSearch(request, now));
}

function filtersFromState(state: UrlState): AggregateFilters | undefined {
	const hasInclude = Object.keys(state.include).length > 0;
	const hasExclude = Object.keys(state.exclude).length > 0;
	if (!hasInclude && !hasExclude) return undefined;
	return {
		...(hasInclude ? { include: state.include } : {}),
		...(hasExclude ? { exclude: state.exclude } : {})
	};
}

function windowFromState(state: UrlState, tz: string): AggregateWindow {
	if (state.range === 'custom') {
		const window: AggregateWindow = { tz };
		if (state.from) window.from = state.from;
		if (state.to) window.to = state.to;
		return window;
	}
	return { tz, preset: state.range };
}

export function applyDrillToRequest(
	request: AggregateRequest,
	key: DimKey,
	value: string,
	exclude: boolean,
	now: Date
): AggregateRequest {
	const state = requestToUrlState(request, now);
	const next = applyDrill(state, key, value, exclude);
	return {
		...request,
		window: windowFromState(next, request.window?.tz ?? 'UTC'),
		filters: filtersFromState(next)
	};
}

export function applyWindowState(
	request: AggregateRequest,
	patch: Partial<UrlState>,
	now: Date
): AggregateRequest {
	const state = { ...requestToUrlState(request, now), ...patch };
	if (patch.range && patch.range !== 'custom') {
		delete state.from;
		delete state.to;
	}
	return {
		...request,
		window: windowFromState(state, request.window?.tz ?? 'UTC'),
		filters: filtersFromState(state)
	};
}
