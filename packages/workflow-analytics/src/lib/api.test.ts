import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiGet, apiPost, createToken, fetchMe, revokeToken } from './api';

let store: Record<string, string>;
let fetchMock: ReturnType<typeof vi.fn>;

function ok(body: unknown, status = 200) {
	return Promise.resolve(new Response(JSON.stringify(body), { status }));
}

beforeEach(() => {
	store = {};
	vi.stubGlobal('localStorage', {
		getItem: (k: string) => (k in store ? store[k] : null),
		setItem: (k: string, v: string) => void (store[k] = v)
	});
	fetchMock = vi.fn(() => ok({ ok: true }));
	vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => vi.unstubAllGlobals());

describe('apiGet', () => {
	it('uses a relative /v1 for an empty base and sends no Authorization', async () => {
		await apiGet('analytics/summary', new URLSearchParams('repo_id=a&repo_id=b'));
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe('/v1/analytics/summary?repo_id=a&repo_id=b');
		expect(new Headers(init?.headers).has('authorization')).toBe(false);
		expect(init?.credentials).toBe('include');
	});

	it('collector mode ignores a stored key and still omits Authorization', async () => {
		store['workflow-analytics-key'] = 'sekret';
		await apiGet('analytics/summary');
		const [, init] = fetchMock.mock.calls[0];
		expect(new Headers(init?.headers).has('authorization')).toBe(false);
		expect(init?.credentials).toBe('include');
	});

	it('uses the stored base without a trailing slash and sends the bearer token', async () => {
		store['workflow-analytics-base'] = 'https://api.example.com/';
		store['workflow-analytics-key'] = 'sekret';
		await apiGet('analytics/summary');
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe('https://api.example.com/v1/analytics/summary');
		expect(new Headers(init?.headers).get('authorization')).toBe('Bearer sekret');
	});

	it('reads storage on every call', async () => {
		store['workflow-analytics-base'] = 'https://api.example.com';
		await apiGet('baselines');
		store['workflow-analytics-key'] = 'k2';
		await apiGet('baselines');
		expect(new Headers(fetchMock.mock.calls[0][1]?.headers).has('authorization')).toBe(false);
		expect(new Headers(fetchMock.mock.calls[1][1]?.headers).get('authorization')).toBe('Bearer k2');
	});

	it('surfaces status and error text', async () => {
		fetchMock.mockImplementation(() => ok({ error: 'unauthorized' }, 401));
		await expect(apiGet('analytics/summary')).rejects.toMatchObject({
			name: 'ApiError',
			status: 401,
			message: 'unauthorized'
		});
		await expect(apiGet('analytics/summary')).rejects.toBeInstanceOf(ApiError);
	});

	it('fetchMe hits /v1/me with session transport', async () => {
		fetchMock.mockImplementation(() => ok({ github_id: 1, github_login: 'u', admin: false, tenants: [] }));
		await fetchMe();
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe('/v1/me');
		expect(init?.credentials).toBe('include');
	});

	it('apiPost in collector mode sends credentials and JSON without Authorization', async () => {
		await apiPost('tokens', { tenant: 't', scope: 'read', expires_at: '2099-01-01T00:00:00Z' });
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe('/v1/tokens');
		expect(init?.method).toBe('POST');
		expect(new Headers(init?.headers).has('authorization')).toBe(false);
		expect(init?.credentials).toBe('include');
		expect(init?.body).toBe(JSON.stringify({ tenant: 't', scope: 'read', expires_at: '2099-01-01T00:00:00Z' }));
	});

	it('revokeToken posts to the revoke subpath', async () => {
		fetchMock.mockImplementation(() => Promise.resolve(new Response(null, { status: 204 })));
		await revokeToken('abc');
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe('/v1/tokens/abc/revoke');
		expect(init?.method).toBe('POST');
	});

	it('createToken uses apiPost', async () => {
		fetchMock.mockImplementation(() => ok({ id: '1', token: 'wk_x', tenant: 't', scope: 'read', expires_at: 'x' }));
		await createToken({ tenant: 't', scope: 'read', expires_at: '2099-01-01T00:00:00Z' });
		expect(fetchMock.mock.calls[0][0]).toBe('/v1/tokens');
	});

	it('names a non-JSON 200 (a static host without the API) as a connection problem', async () => {
		fetchMock.mockImplementation(() => Promise.resolve(new Response('<!doctype html><html></html>', { status: 200 })));
		const err = await apiGet('analytics/summary').catch((e) => e);
		expect(err).not.toBeInstanceOf(ApiError);
		expect(String(err.message)).toContain('/v1/analytics/summary did not return JSON');
	});
});
