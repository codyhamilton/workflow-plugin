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

export type MeResponse = {
	github_id: number;
	github_login: string;
	admin: boolean;
	tenants: { name: string }[];
};

export type TokenListItem = {
	id: string;
	tenant: string;
	scope: string;
	expires_at: string;
	revoked: boolean;
	created_at: string;
};

export type CreatedTokenResponse = TokenListItem & { token: string };

export type AdminTokenListItem = TokenListItem & { github_id: number };

// localStorage is read on every call: no caching, so /settings takes effect without a reload.
function read(key: string): string {
	try {
		return (localStorage.getItem(key) ?? '').trim();
	} catch {
		return '';
	}
}

/** Empty `workflow-analytics-base`: same-origin collector embed; session cookie, no bearer. */
export function isCollectorMode(): boolean {
	return read(BASE_KEY) === '';
}

function apiUrl(path: string, params?: URLSearchParams | string): string {
	const base = read(BASE_KEY).replace(/\/+$/, '');
	const qs = params ? params.toString() : '';
	return `${base}/v1/${path.replace(/^\/+/, '')}${qs ? `?${qs}` : ''}`;
}

function apiInit(method: string, collector: boolean, key: string, body?: unknown, signal?: AbortSignal): RequestInit {
	const headers: Record<string, string> = { accept: 'application/json' };
	if (key) headers.authorization = `Bearer ${key}`;
	if (body !== undefined) headers['content-type'] = 'application/json';
	const init: RequestInit = { method, headers, signal };
	if (collector) init.credentials = 'include';
	if (body !== undefined) init.body = JSON.stringify(body);
	return init;
}

async function parseJsonResponse<T>(res: Response, url: string): Promise<T> {
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
	if (res.status === 204) return undefined as T;
	try {
		return (await res.json()) as T;
	} catch {
		throw new Error(`${url} did not return JSON: this origin does not serve the workflow API. Set the API base URL.`);
	}
}

/** GET <base>/v1/<path>?<params>. `path` is relative to /v1, e.g. "analytics/summary". */
export async function apiGet<T = unknown>(
	path: string,
	params?: URLSearchParams | string,
	signal?: AbortSignal
): Promise<T> {
	const collector = isCollectorMode();
	const key = collector ? '' : read(TOKEN_KEY);
	const url = apiUrl(path, params);
	const res = await fetch(url, apiInit('GET', collector, key, undefined, signal));
	return parseJsonResponse<T>(res, url);
}

/** POST <base>/v1/<path> with a JSON body. Collector mode uses session cookies, not bearer. */
export async function apiPost<T = unknown>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
	const collector = isCollectorMode();
	const key = collector ? '' : read(TOKEN_KEY);
	const url = apiUrl(path);
	const res = await fetch(url, apiInit('POST', collector, key, body, signal));
	return parseJsonResponse<T>(res, url);
}

export async function createTenant(name: string, signal?: AbortSignal): Promise<{ name: string }> {
	return apiPost('tenants', { name }, signal);
}

export async function createToken(
	body: { tenant: string; scope: string; expires_at: string },
	signal?: AbortSignal
): Promise<CreatedTokenResponse> {
	return apiPost('tokens', body, signal);
}

export async function listTokens(signal?: AbortSignal): Promise<TokenListItem[]> {
	return apiGet('tokens', undefined, signal);
}

export async function listAdminTokens(signal?: AbortSignal): Promise<AdminTokenListItem[]> {
	return apiGet('admin/tokens', undefined, signal);
}

export async function revokeToken(id: string, signal?: AbortSignal): Promise<void> {
	await apiPost(`tokens/${id}/revoke`, {}, signal);
}

/** Session identity and owned tenants (`GET /v1/me`). Collector mode only; same transport as `apiGet`. */
export async function fetchMe(signal?: AbortSignal): Promise<MeResponse> {
	return apiGet<MeResponse>('me', undefined, signal);
}

export type DeviceAuthorizeBody = {
	redirect_uri: string;
	state: string;
	tenant: string;
	scope: 'read' | 'read_write';
	expires_at: string;
};

/** Loopback http(s) redirect URIs allowed for device authorization (matches serve `validLoopbackRedirectURI`). */
export function isValidLoopbackRedirectUri(raw: string): boolean {
	if (!raw) return false;
	try {
		const u = new URL(raw);
		if (u.protocol !== 'http:' && u.protocol !== 'https:') return false;
		const host = u.hostname;
		if (host === 'localhost') return true;
		if (host === '127.0.0.1' || host === '::1' || host === '[::1]') return true;
		// IPv4 loopback 127.0.0.0/8
		const m = /^(\d+)\.(\d+)\.(\d+)\.(\d+)$/.exec(host);
		if (m) {
			const a = Number(m[1]);
			return a === 127;
		}
		return false;
	} catch {
		return false;
	}
}

/**
 * Device authorization (`POST /v1/device/authorize`). Collector session + JSON + Origin.
 * Returns the loopback redirect URL (303 Location); response body must not contain the token plaintext.
 */
export async function authorizeDevice(body: DeviceAuthorizeBody, signal?: AbortSignal): Promise<string> {
	const collector = isCollectorMode();
	const key = collector ? '' : read(TOKEN_KEY);
	const url = apiUrl('device/authorize');
	const init = apiInit('POST', collector, key, body, signal);
	let res = await fetch(url, { ...init, redirect: 'manual' });
	if (res.status >= 300 && res.status < 400) {
		const loc = res.headers.get('Location');
		if (!loc) throw new ApiError(res.status, 'missing redirect location');
		return loc;
	}
	// Cross-origin 303 from fetch can surface as an opaque redirect (status 0); follow to learn the final URL.
	if (res.status === 0 || res.type === 'opaqueredirect') {
		res = await fetch(url, { ...init, redirect: 'follow' });
		if (res.redirected && res.url) return res.url;
	}
	if (!res.ok) {
		let msg = res.statusText || `HTTP ${res.status}`;
		try {
			const errBody = await res.json();
			if (errBody && typeof errBody.error === 'string') msg = errBody.error;
		} catch {
			/* non-JSON error body */
		}
		throw new ApiError(res.status, msg);
	}
	throw new ApiError(res.status, 'unexpected device authorize response');
}
