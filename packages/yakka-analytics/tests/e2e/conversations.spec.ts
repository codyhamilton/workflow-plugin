import { expect, test, type Page } from '@playwright/test';
import { costLabel } from '../../src/lib/format';
import { CONVERSATION_ROWS, FILTER_REPO, USAGE_C5 } from './fixture';
import { trackRequests, useServe } from './helpers';

const SONNET = 'anthropic/claude-sonnet-5-5';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const rowTexts = (page: Page) => page.getByTestId('conv-row').allInnerTexts();

async function expectRows(page: Page, want: typeof CONVERSATION_ROWS) {
	await expect(page.getByTestId('conv-row')).toHaveCount(want.length);
	const t = await rowTexts(page);
	want.forEach((w, i) => {
		expect(t[i]).toContain(w.conversation_id);
		expect(t[i]).toContain(w.harness);
	});
	for (const w of want)
		for (const f of ['hook_events', 'artifact_versions', 'commits'] as const)
			await expect(page.getByTestId(`conv-${w.conversation_id}-${f}`), `${w.conversation_id} ${f}`).toHaveText(String(w[f]));
}

test('one row per fixture conversation, last_ts descending, with counts', async ({ page }) => {
	await page.goto('/conversations');
	await expectRows(page, CONVERSATION_ROWS);
});

test('repo_id filters', async ({ page }) => {
	await page.goto(`/conversations?repo_id=${FILTER_REPO}`);
	const want = CONVERSATION_ROWS.filter((r) => r.repos.includes(FILTER_REPO));
	await expect(page.getByTestId('conv-row')).toHaveCount(want.length);
	for (const w of want) await expect(page.getByTestId(`conv-${w.conversation_id}-commits`)).toBeVisible();
	await expect(page.getByTestId('conv-c2-commits')).toHaveCount(0);
});

test('conversation id links to the timeline', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-c3-conversation_id')).toHaveAttribute('href', '/conversation?id=c3');
});

test('a harness cell click adds a chip', async ({ page }) => {
	await page.goto('/conversations');
	await page.getByTestId('conv-c3-harness').click();
	await expect(page.getByTestId('chip-harness-claude')).toBeVisible();
});

test('c5 row shows model and cost from the API', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-c5-model')).toHaveText(SONNET);
	await expect(page.getByTestId('conv-c5-cost')).toHaveText(
		costLabel({
			cost: USAGE_C5.cost_usd,
			unpriced: USAGE_C5.unpriced_calls,
			calls: USAGE_C5.model_calls
		})
	);
});

test('loads per-conversation cost distribution for the window', async ({ page }) => {
	const dist = trackRequests(page, /analytics\/distribution/);
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-row').first()).toBeVisible();
	await expect(page.getByTestId('conversations-distribution')).toBeVisible();
	expect(dist.count()).toBeGreaterThan(0);
	for (const u of dist.urls()) {
		const p = new URL(u).searchParams;
		expect(p.get('grain')).toBe('conversation');
		expect(p.get('measure')).toBe('cost_usd');
	}
});

test('model cell click filters by model and narrows the list', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-row')).toHaveCount(CONVERSATION_ROWS.length);
	await page.getByTestId('conv-c5-model').click();
	await expect(page.getByTestId(`chip-model-${SONNET}`)).toBeVisible();
	await expect(page.getByTestId('conv-row')).toHaveCount(1);
	await expect(page.getByTestId('conv-c5-conversation_id')).toBeVisible();
});

test('limit=1 paging walk equals the unpaged rows', async ({ page }) => {
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-row')).toHaveCount(CONVERSATION_ROWS.length);
	const all = await rowTexts(page);
	await page.goto('/conversations?limit=1');
	await expect(page.getByTestId('conv-row')).toHaveCount(1);
	const more = page.getByRole('button', { name: 'Load more' });
	for (let i = 2; i <= all.length; i++) {
		await more.click();
		await expect(page.getByTestId('conv-row')).toHaveCount(i);
	}
	await expect(more).toHaveCount(0);
	expect(await rowTexts(page)).toEqual(all);
});

test('virtualises 5000 rows: under 100 in the DOM, last row reachable', async ({ page }) => {
	const rows = Array.from({ length: 5000 }, (_, i) => ({
		conversation_id: `gen-${i}`,
		harness: 'claude',
		repos: ['r1'],
		first_ts: '2025-01-01T00:00:00Z',
		last_ts: '2025-01-01T00:00:00Z',
		hook_events: 0,
		artifact_versions: 0,
		commits: 0,
		kinds: [],
		model: '',
		model_calls: 0,
		unpriced_calls: 0,
		cost_usd: 0,
		tokens_in: 0,
		tokens_out: 0
	}));
	await page.route('**/v1/analytics/conversations*', (route) =>
		route.fulfill({ json: { rows }, headers: { 'access-control-allow-origin': '*' } })
	);
	const t0 = Date.now();
	await page.goto('/conversations');
	await expect(page.getByTestId('conv-row').first()).toBeVisible({ timeout: 1000 });
	expect(Date.now() - t0).toBeLessThan(1000);
	expect(await page.getByTestId('conv-row').count()).toBeLessThan(100);
	const container = page.getByTestId('virtual-scroll');
	await container.evaluate((el) => {
		(el as HTMLElement).scrollTop = (el as HTMLElement).scrollHeight;
	});
	await expect(page.getByTestId('conv-gen-4999-conversation_id')).toBeVisible();
});

test('a 500 from the conversations API shows the error panel, not an empty page', async ({ page }) => {
	await page.route('**/v1/analytics/conversations*', (route) =>
		route.fulfill({
			status: 500,
			json: { error: 'boom' },
			headers: { 'access-control-allow-origin': '*' }
		})
	);
	await page.goto('/conversations');
	await expect(page.getByTestId('error-panel')).toBeVisible();
	await expect(page.getByTestId('error-panel')).toContainText('boom');
	await expect(page.getByTestId('conv-row')).toHaveCount(0);
});

test('a network failure shows the connection message in the error panel', async ({ page }) => {
	await page.route('**/v1/analytics/conversations*', (route) => route.abort());
	await page.goto('/conversations');
	await expect(page.getByTestId('error-panel')).toBeVisible();
	await expect(page.getByTestId('error-panel')).toContainText('Check the connection');
	await expect(page.getByTestId('error-panel')).toContainText('/settings');
});

test('changing the preset retries and clears the error panel', async ({ page }) => {
	let fail = true;
	await page.route('**/v1/analytics/conversations*', (route) =>
		fail
			? route.fulfill({
					status: 500,
					json: { error: 'boom' },
					headers: { 'access-control-allow-origin': '*' }
				})
			: route.continue()
	);
	await page.goto('/conversations');
	await expect(page.getByTestId('error-panel')).toBeVisible();
	fail = false;
	await page.getByTestId('preset-7d').click();
	await expect(page.getByTestId('error-panel')).toHaveCount(0);
	await expect(page.getByTestId('conv-row').first()).toBeVisible();
});
