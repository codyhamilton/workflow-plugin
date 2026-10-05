import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiGet } from './api';

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
});
