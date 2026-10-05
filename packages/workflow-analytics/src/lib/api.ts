export const BASE_KEY = 'workflow-analytics-base';
export const TOKEN_KEY = 'workflow-analytics-key';

export class ApiError extends Error {
	status: number;
	constructor(status: number, message: string) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
	}
}

// localStorage is read on every call: no caching, so /settings takes effect without a reload.
function read(key: string): string {
	try {
		return (localStorage.getItem(key) ?? '').trim();
	} catch {
		return '';
	}
}

/** GET <base>/v1/<path>?<params>. `path` is relative to /v1, e.g. "analytics/summary". */
export async function apiGet<T = unknown>(path: string, params?: URLSearchParams | string): Promise<T> {
	const base = read(BASE_KEY).replace(/\/+$/, '');
	const key = read(TOKEN_KEY);
	const qs = params ? params.toString() : '';
	const url = `${base}/v1/${path.replace(/^\/+/, '')}${qs ? `?${qs}` : ''}`;
	const headers: Record<string, string> = { accept: 'application/json' };
	if (key) headers.authorization = `Bearer ${key}`;
	const res = await fetch(url, { headers });
	if (!res.ok) {
		let msg = res.statusText || `HTTP ${res.status}`;
		try {
			const body = await res.json();
			if (body && typeof body.error === 'string') msg = body.error;
		} catch {
			/* non-JSON error body */
		}
		throw new ApiError(res.status, msg);
	}
	return (await res.json()) as T;
}
