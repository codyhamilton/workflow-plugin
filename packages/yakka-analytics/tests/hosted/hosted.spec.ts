import { expect, test } from '@playwright/test';
import { SUMMARY_ALL } from '../e2e/fixture';

const MARKER = 'workflow-analytics-placeholder';
// Set by global-setup before workers start.
test.use({ baseURL: process.env.HOSTED_BASE });

test('GET / is the built site, revalidated', async ({ request }) => {
	const r = await request.get('/');
	expect(r.status()).toBe(200);
	expect(r.headers()['content-type']).toMatch(/^text\/html/);
	expect(r.headers()['cache-control']).toBe('no-cache');
	expect(await r.text()).not.toContain(MARKER);
});

test('/v1 stays JSON', async ({ request }) => {
	const h = await request.get('/v1/health');
	expect(h.status()).toBe(200);
	expect(h.headers()['content-type']).toMatch(/json/);
	expect(Object.keys(await h.json())).toContain('pending');
	const n = await request.get('/v1/not-a-route');
	expect(n.status()).toBe(404);
	expect(n.headers()['content-type']).toMatch(/json/);
	expect(await n.json()).toEqual({ error: 'not found' });
});

test('overview loads same-origin with no token', async ({ page, baseURL }) => {
	const v1: { url: string; auth: string | undefined }[] = [];
	page.on('request', (r) => {
		if (new URL(r.url()).pathname.startsWith('/v1/')) v1.push({ url: r.url(), auth: r.headers()['authorization'] });
	});
	await page.goto('/');
	for (const [k, v] of Object.entries(SUMMARY_ALL)) {
		await expect(page.getByTestId(`summary-${k}`), k).toHaveText(String(v));
	}
	expect(v1.length).toBeGreaterThan(0);
	for (const q of v1) {
		expect(new URL(q.url).origin).toBe(baseURL);
		expect(q.auth).toBeUndefined();
	}
});

test('a client route survives a refresh', async ({ page }) => {
	await page.goto('/quality');
	await expect(page.getByTestId('quality-kind-design')).toBeVisible();
	await page.reload();
	await expect(page.getByTestId('quality-kind-design')).toBeVisible();
	await expect(page.getByTestId('q-row').first()).toBeVisible();
});

test('immutable assets are cached for a year', async ({ page }) => {
	const cc: string[] = [];
	page.on('response', (r) => {
		if (new URL(r.url()).pathname.startsWith('/_app/immutable/')) cc.push(r.headers()['cache-control'] ?? '');
	});
	await page.goto('/');
	await expect(page.getByTestId('summary-conversations')).toBeVisible();
	expect(cc.length).toBeGreaterThan(0);
	for (const c of cc) expect(c).toBe('public, max-age=31536000, immutable');
});

test('explore loads Perspective from the binary', async ({ page }) => {
	const s = SUMMARY_ALL;
	const total = s.hook_events + s.artifact_versions + s.commits + s['rejections-precheck'] + s['rejections-screen'];
	await page.goto('/explore');
	await expect(page.locator('perspective-viewer')).toBeVisible();
	await expect(page.getByTestId('explore-count')).toHaveText(String(total));
});
