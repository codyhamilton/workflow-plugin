import type { AggregateRequest, AggregateWindow } from '../aggregate';
import { applyDrill, parseUrlState, type DimKey, type UrlState } from '../urlstate';
import { filtersIfSet, investigationRequestToSearch } from './request-url';

export function requestToUrlState(request: AggregateRequest): UrlState {
	return parseUrlState(investigationRequestToSearch(request));
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
	exclude: boolean
): AggregateRequest {
	const state = requestToUrlState(request);
	const next = applyDrill(state, key, value, exclude);
	return {
		...request,
		window: windowFromState(next, request.window?.tz ?? 'UTC'),
		filters: filtersIfSet(next.include, next.exclude)
	};
}

export function applyWindowState(request: AggregateRequest, patch: Partial<UrlState>): AggregateRequest {
	const state = { ...requestToUrlState(request), ...patch };
	if (patch.range && patch.range !== 'custom') {
		delete state.from;
		delete state.to;
	}
	return {
		...request,
		window: windowFromState(state, request.window?.tz ?? 'UTC'),
		filters: filtersIfSet(state.include, state.exclude)
	};
}
