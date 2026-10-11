import { ApiError } from './api';

/** The one visible fetch error, shown by the layout's error panel. */
export const fetchError = $state<{ message: string; status: number; network: boolean }>({
	message: '',
	status: 0,
	network: false
});

export function setError(e: unknown) {
	if (e instanceof ApiError) {
		fetchError.message = e.message;
		fetchError.status = e.status;
		fetchError.network = false;
	} else {
		fetchError.message = e instanceof Error ? e.message : String(e);
		fetchError.status = 0;
		fetchError.network = true;
	}
}

export function clearError() {
	fetchError.message = '';
	fetchError.status = 0;
	fetchError.network = false;
}

export interface Notice {
	partial: boolean;
	ignored: string[];
	/** The `pathname + search` this notice belongs to; shown only while that view is on screen. */
	view: string;
}

/** Per-slot `partial`/`ignored_filters` notices, keyed by slot. Written by the data client. */
export const notices = $state<Record<string, Notice>>({});

/**
 * The view the shell is showing. The layout keeps it current in an `$effect.pre`, which runs before
 * any regular effect, so a notice a request sets for the current view is tagged with it and survives
 * the navigation that triggered the request (a cache hit sets the notice in the same flush).
 */
export const noticeView = $state<{ key: string }>({ key: '' });

export function setNoticeView(key: string) {
	noticeView.key = key;
}

export function setNotice(slot: string, resp: { partial?: boolean; ignored_filters?: string[] }) {
	notices[slot] = {
		partial: !!resp.partial,
		ignored: resp.ignored_filters ?? [],
		view: noticeView.key
	};
}

export function clearNotices() {
	for (const k of Object.keys(notices)) delete notices[k];
}

/** Drop notices that belong to another view; the current view's own notice stays. */
export function pruneNotices() {
	for (const k of Object.keys(notices)) if (notices[k].view !== noticeView.key) delete notices[k];
}
