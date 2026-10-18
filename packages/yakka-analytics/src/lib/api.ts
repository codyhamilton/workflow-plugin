export const BASE_KEY = 'yakka-analytics-base';
export const TOKEN_KEY = 'yakka-analytics-key';

/** Production Fly API. Pages at yakka.build calls this origin with credentials. */
export const API_ORIGIN = 'https://api.yakka.build';

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

function configuredBase(): string {
	return read(BASE_KEY).replace(/\/+$/, '');
}

/** True on the production Pages hosts (apex and www). */
export function isPagesHost(hostname?: string): boolean {
	const host = hostname ?? (typeof location !== 'undefined' ? location.hostname : '');
	return host === 'yakka.build' || host === 'www.yakka.build';
}

/**
 * API origin for this page. A stored base wins. On the Pages hosts an empty base is the
 * production API. An embedded local serve stays same-origin (empty).
 */
export function resolvedBase(hostname?: string): string {
	const configured = configuredBase();
	if (configured) return configured;
	if (isPagesHost(hostname)) return API_ORIGIN;
	return '';
}

function originOf(base: string): string {
	try {
		return new URL(base).origin;
	} catch {
		return '';
	}
}

/**
 * Session cookie transport: same-origin embed, the Pages hosts, or a base whose origin is
 * the production API. Analytics GETs may still send a bearer when a key is stored.
 */
export function isCollectorMode(hostname?: string): boolean {
	const configured = configuredBase();
	if (configured === '') return true;
	return originOf(configured) === API_ORIGIN || isPagesHost(hostname);
}

/**
 * Origin that sets and reads the OAuth state cookie.
 * Pages talks to the production API. Any other host, including an embedded serve, stays
 * same-origin. A stored analytics base is not this origin: the state cookie is not sent there.
 */
export function oauthApiBase(hostname?: string): string {
	const host = hostname ?? (typeof location !== 'undefined' ? location.hostname : '');
	return isPagesHost(host) ? API_ORIGIN : '';
}

/** GitHub login navigation. On Pages this hits the API so the state cookie is host-only there. */
export function oauthLoginPath(hostname: string, returnTo = ''): string {
	const base = oauthApiBase(hostname);
	const q = returnTo ? `?return=${encodeURIComponent(returnTo)}` : '';
	return `${base}/oauth/login${q}`;
}

/** Device form action. Pages posts to the API; an embedded serve posts same-origin. */
export function deviceAuthorizeAction(hostname?: string): string {
	const base = isPagesHost(hostname) ? API_ORIGIN : configuredBase();
	if (!base) return '/v1/device/authorize';
	return `${base}/v1/device/authorize`;
}

function apiUrl(path: string, params?: URLSearchParams | string): string {
	const base = resolvedBase();
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

function sessionRoute(path: string): boolean {
	const p = path.replace(/^\/+/, '');
	return p === 'me' || p.startsWith('tenants') || p.startsWith('tokens') || p.startsWith('admin/');
}

/** GET <base>/v1/<path>?<params>. `path` is relative to /v1, e.g. "analytics/summary". */
export async function apiGet<T = unknown>(
	path: string,
	params?: URLSearchParams | string,
	signal?: AbortSignal
): Promise<T> {
	const collector = isCollectorMode();
	const session = collector && sessionRoute(path);
	const key = session || read(TOKEN_KEY) === '' || resolvedBase() === '' ? '' : read(TOKEN_KEY);
	const creds = session || key === '';
	const url = apiUrl(path, params);
	const res = await fetch(url, apiInit('GET', creds, key, undefined, signal));
	return parseJsonResponse<T>(res, url);
}

/** POST <base>/v1/<path> with a JSON body. Collector session routes use cookies, not a bearer. */
export async function apiPost<T = unknown>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
	const collector = isCollectorMode();
	const session = collector && sessionRoute(path);
	const key = session || read(TOKEN_KEY) === '' || resolvedBase() === '' ? '' : read(TOKEN_KEY);
	const creds = session || key === '';
	const url = apiUrl(path);
	const res = await fetch(url, apiInit('POST', creds, key, body, signal));
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
