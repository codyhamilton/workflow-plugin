import { expect, test, type Page } from '@playwright/test';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1 } from './fixture';
import { expectSettled, trackRequests, useServe } from './helpers';

const MEASURES = ['hook_events', 'conversations', 'artifact_versions', 'commits'] as const;
const R1 = SUMMARY_R1;
// r2 is the window total minus r1 (every fixture fact belongs to r1 or r2).
const R2 = Object.fromEntries(MEASURES.map((f) => [f, SUMMARY_ALL[f] - R1[f]]));

async function expectRepo(page: Page, repo: string, want: Record<string, number>) {
	for (const f of MEASURES)
		await expect(page.getByTestId(`repo-${repo}-${f}`), `${repo} ${f}`).toHaveText(String(want[f]));
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('both fixture repos appear with their own counts', async ({ page }) => {
	await page.goto('/repos');
	await expectRepo(page, 'r1', R1);
	await expectRepo(page, 'r2', R2);
});

test('repo_id in the URL shows only that repo', async ({ page }) => {
	await page.goto(`/repos?repo_id=${FILTER_REPO}`);
	await expectRepo(page, FILTER_REPO, R1);
	await expect(page.getByTestId('repo-r2-hook_events')).toHaveCount(0);
	await page.reload();
	await expectRepo(page, FILTER_REPO, R1);
	await expect(page.getByTestId('repo-r2-hook_events')).toHaveCount(0);
});

test('load issues five query requests and no summary request', async ({ page }) => {
	const requests = trackRequests(page, /analytics\//);
	await page.goto('/repos');
	await expect(page.getByTestId('repo-r1-hook_events')).toHaveText('9');

	const urls = requests.urls();
	const queries = urls.filter((u) => u.includes('/analytics/query'));
	expect(queries).toHaveLength(5);
	expect(queries.map((u) => new URL(u).searchParams.get('measure')).sort()).toEqual([
		'artifact_versions',
		'commits',
		'conversations',
		'cost_usd',
		'hook_events'
	]);
	for (const u of queries) {
		const p = new URL(u).searchParams;
		expect(p.get('dim'), u).toBe('repo_id');
		expect(p.get('top'), u).toBe('100');
		expect(p.get('bucket'), u).toBe('none');
	}
	expect(urls.some((u) => u.includes('/analytics/summary'))).toBe(false);
});

test('a route that returns many repos still issues exactly five requests', async ({ page }) => {
	const queries = trackRequests(page, /analytics\/query/);
	await page.route('**/v1/analytics/query*', (route) => {
		const measure = new URL(route.request().url()).searchParams.get('measure') ?? 'hook_events';
		const rows = Array.from({ length: 40 }, (_, i) => ({ k: [`invented-${i}`], v: 40 - i }));
		return route.fulfill({
			json: { measure, bucket: 'none', dims: ['repo_id'], rows },
			headers: { 'access-control-allow-origin': '*' }
		});
	});
	await page.goto('/repos');
	await expect(page.getByTestId('repo-invented-0-hook_events')).toHaveText('40');
	await expect(page.getByTestId('repo-invented-39-hook_events')).toHaveText('1');
	expect(queries.count()).toBe(5);
});

test('cost ranking orders the bar chart by fixture repo costs', async ({ page }) => {
	await page.goto('/repos');
	await page.getByTestId('repos-rank').selectOption('cost_usd');
	await page.getByTestId('repos-chart-table-toggle').click();
	const table = page.getByTestId('repos-chart-table');
	const rows = table.locator('tbody tr');
	await expect(rows.first().locator('td').first()).toHaveText('r1');
	await expect(rows.nth(1).locator('td').first()).toHaveText('r2');
	const r1Cost = Number(await rows.first().locator('td').nth(1).getAttribute('data-value'));
	const r2Cost = Number(await rows.nth(1).locator('td').nth(1).getAttribute('data-value'));
	expect(r1Cost).toBeGreaterThan(0);
	expect(r2Cost).toBe(0);
	expect(r1Cost).toBeGreaterThan(r2Cost);
});

test('a repo row click filters; shift-click excludes it', async ({ page }) => {
	await page.goto('/repos');
	await expect(page.getByTestId('repo-r1-hook_events')).toHaveText('9');

	await page.getByTestId('repo-row-r1').click();
	await expect(page.getByTestId('chip-repo_id-r1')).toHaveAttribute('data-mode', 'include');
	await expect(page.getByTestId('repo-r2-hook_events')).toHaveCount(0);

	await page.getByTestId('repo-row-r1').click({ modifiers: ['Shift'] });
	await expect(page.getByTestId('chip-repo_id-r1')).toHaveAttribute('data-mode', 'exclude');
	await expect(page.getByTestId('repo-r1-hook_events')).toHaveCount(0);
	await expect(page.getByTestId('repo-r2-hook_events')).toHaveText('1');
});

test('the __other__ row is inert', async ({ page }) => {
	await page.route('**/v1/analytics/query*', (route) => {
		const measure = new URL(route.request().url()).searchParams.get('measure') ?? 'hook_events';
		return route.fulfill({
			json: {
				measure,
				bucket: 'none',
				dims: ['repo_id'],
				rows: [
					{ k: ['r1'], v: 5 },
					{ k: ['__other__'], v: 3 }
				]
			},
			headers: { 'access-control-allow-origin': '*' }
		});
	});
	await page.goto('/repos');
	await expect(page.getByTestId('repo-__other__-hook_events')).toHaveText('3');
	await page.getByTestId('repo-row-__other__').click();
	await expect(page).not.toHaveURL(/repo_id/);
	await expect(page.getByTestId('chip-repo_id-__other__')).toHaveCount(0);
});

test('a filter change settles within 1 s', async ({ page }) => {
	await page.goto('/repos');
	await expect(page.getByTestId('repos-chart')).toHaveAttribute('data-ready', 'true');
	const start = Date.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(Date.now() - start).toBeLessThan(1000);
});
