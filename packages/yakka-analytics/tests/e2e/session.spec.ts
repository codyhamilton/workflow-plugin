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
