import { expect, test, type Page } from '@playwright/test';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1 } from './fixture';
import { useServe } from './helpers';

// Every in-window fact plus every in-window rejection is one explore row.
const total = (s: typeof SUMMARY_ALL) => s.hook_events + s.artifact_versions + s.commits + s['rejections-precheck'] + s['rejections-screen'];
const ALL = total(SUMMARY_ALL);
const R1 = total(SUMMARY_R1);

async function tableSize(page: Page): Promise<number> {
	return page.evaluate(async () => {
		const v = document.querySelector('perspective-viewer') as unknown as { getTable(): Promise<{ size(): Promise<number> }> };
		return (await v.getTable()).size();
	});
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('the viewer holds every fact and rejection, and the slice is not capped', async ({ page }) => {
	await page.goto('/explore');
	await expect(page.locator('perspective-viewer')).toBeVisible();
	await expect(page.getByTestId('explore-count')).toHaveText(String(ALL));
	await expect.poll(() => tableSize(page).catch(() => -1)).toBe(ALL);
	await expect(page.getByTestId('explore-truncated')).toHaveCount(0);
});

test('repo_id filters the slice and survives a reload', async ({ page }) => {
	await page.goto(`/explore?repo_id=${FILTER_REPO}`);
	await expect(page.getByTestId('explore-count')).toHaveText(String(R1));
	await expect.poll(() => tableSize(page).catch(() => -1)).toBe(R1);
	await page.reload();
	await expect(page.getByTestId('explore-count')).toHaveText(String(R1));
	await expect.poll(() => tableSize(page).catch(() => -1)).toBe(R1);
});

test('a capped slice says so', async ({ page }) => {
	await page.route('**/v1/analytics/explore*', (route) =>
		route.fulfill({
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				rows: [1, 2, 3].map((i) => ({ type: 'hook_event', ts: `2026-01-0${i}T00:00:00Z`, harness: 'claude', repo_id: 'r1' })),
				truncated: true
			})
		})
	);
	await page.goto('/explore');
	await expect(page.getByTestId('explore-truncated')).toBeVisible();
	await expect(page.getByTestId('explore-count')).toHaveText('3');
});

test('the overview does not load Perspective', async ({ page }) => {
	const urls: string[] = [];
	page.on('request', (r) => urls.push(r.url()));
	await page.goto('/');
	await expect(page.getByTestId('summary-conversations')).toBeVisible();
	expect(urls.filter((u) => u.includes('perspective') || u.split('?')[0].endsWith('.wasm'))).toEqual([]);
});
