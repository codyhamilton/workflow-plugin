import { expect, test } from '@playwright/test';
import { SUMMARY_ALL, USAGE_ALL } from './fixture';
import { trackRequests } from './helpers';

const nested = (field: string) =>
	Object.fromEntries(
		Object.entries(SUMMARY_ALL)
			.filter(([k]) => k.startsWith(`${field}-`))
			.map(([k, v]) => [k.slice(field.length + 1), v])
	);

test('login surfaces denied admission', async ({ page }) => {
	await page.goto('/login?error=denied');
	await expect(page.getByTestId('login-denied')).toBeVisible();
	await expect(page.getByTestId('login-link')).toHaveAttribute('href', '/oauth/login');
});

test('collector overview sends tenant from /v1/me on summary', async ({ page }) => {
	const tenant = 'acme';
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: tenant }] }
		})
	);
	const summary = trackRequests(page, /analytics\/summary/);
	await page.route('**/v1/analytics/**', (route) => route.continue());
	await page.goto('/');
	await expect.poll(() => summary.count()).toBeGreaterThan(0);
	const hit = summary.urls().find((u) => u.includes('summary'));
	expect(hit).toBeTruthy();
	expect(new URL(hit!).searchParams.get('tenant')).toBe(tenant);
});

test('session summary mock loads overview tiles', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: 't1' }] }
		})
	);
	await page.route('**/v1/analytics/summary*', (route) =>
		route.fulfill({
			json: {
				...SUMMARY_ALL,
				...USAGE_ALL,
				by_kind: nested('by_kind'),
				by_source: nested('by_source'),
				rejections: nested('rejections'),
				screens: nested('screens')
			}
		})
	);
	await page.route('**/v1/analytics/query*', (route) =>
		route.fulfill({ json: { rows: [], partial: false, ignored_filters: [] } })
	);
	await page.route('**/v1/analytics/facets*', (route) =>
		route.fulfill({
			json: { repos: [], harnesses: [], kinds: [], plans: [], events: [], models: [], norm_events: [], tools: [] }
		})
	);
	await page.goto('/');
	await expect(page.getByTestId('summary-conversations')).toHaveText(String(SUMMARY_ALL.conversations));
});

test('empty base: /v1/me 401 stays on opened route; first /v1/ request is /v1/me', async ({ page }) => {
	await page.addInitScript(() => {
		localStorage.removeItem('yakka-analytics-base');
		localStorage.removeItem('yakka-analytics-key');
	});
	const v1 = trackRequests(page, /\/v1\//);
	await page.route('**/v1/me', (route) => route.fulfill({ status: 401, json: { error: 'unauthorized' } }));
	await page.goto('/trends?range=7d');
	await expect(page).toHaveURL(/\/trends\?range=7d$/);
	await expect.poll(() => v1.count()).toBeGreaterThan(0);
	expect(v1.urls()[0]).toMatch(/\/v1\/me$/);
});

test('non-empty base, no key: /v1/me 401 redirects to login with return; no analytics requests', async ({
	page
}) => {
	await page.addInitScript(() => {
		localStorage.setItem('yakka-analytics-base', 'https://collector.example');
		localStorage.removeItem('yakka-analytics-key');
	});
	const analytics = trackRequests(page, '/v1/analytics/');
	await page.route('**/v1/me', (route) => route.fulfill({ status: 401, json: { error: 'unauthorized' } }));
	await page.goto('/usage?range=7d');
	await expect(page).toHaveURL(/\/login\?/);
	expect(decodeURIComponent(new URL(page.url()).searchParams.get('return') ?? '')).toBe('/usage?range=7d');
	expect(analytics.count()).toBe(0);
});

test('non-empty base with key: /v1/me 401 stays on opened route', async ({ page }) => {
	await page.addInitScript(() => {
		localStorage.setItem('yakka-analytics-base', 'https://collector.example');
		localStorage.setItem('yakka-analytics-key', 'sekret');
	});
	await page.route('**/v1/me', (route) => route.fulfill({ status: 401, json: { error: 'unauthorized' } }));
	await page.goto('/usage?range=7d');
	await expect(page).toHaveURL(/\/usage\?range=7d$/);
});

test('non-empty base, no key: /settings stays on /settings when /v1/me is 401', async ({ page }) => {
	await page.addInitScript(() => {
		localStorage.setItem('yakka-analytics-base', 'https://collector.example');
		localStorage.removeItem('yakka-analytics-key');
	});
	await page.route('**/v1/me', (route) => route.fulfill({ status: 401, json: { error: 'unauthorized' } }));
	await page.goto('/settings');
	await expect(page).toHaveURL(/\/settings$/);
});

test('login passes return through to oauth login href', async ({ page }) => {
	const ret = '/trends?range=7d';
	await page.goto(`/login?return=${encodeURIComponent(ret)}`);
	await expect(page.getByTestId('login-link')).toHaveAttribute(
		'href',
		`/oauth/login?return=${encodeURIComponent(ret)}`
	);
});

test('no tenant: summary 403 no such tenant sends to /profile', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [] }
		})
	);
	await page.route('**/v1/analytics/summary*', (route) =>
		route.fulfill({ status: 403, json: { error: 'no such tenant' } })
	);
	await page.goto('/');
	await expect(page).toHaveURL(/\/profile$/);
});

test('tenant present: summary 403 no such tenant does not send to /profile', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: 'acme' }] }
		})
	);
	await page.route('**/v1/analytics/summary*', (route) =>
		route.fulfill({ status: 403, json: { error: 'no such tenant' } })
	);
	await page.goto('/');
	await expect(page).not.toHaveURL(/\/profile$/);
});
