import { expect, test } from '@playwright/test';
import { USAGE_C5 } from './fixture';
import { brush, clickBar, expectSettled, trackRequests, useServe } from './helpers';

const QWEN = 'ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M';

// The fixture days are UTC days; pin the browser zone so the /query buckets land on them.
test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const SONNET = 'anthropic/claude-sonnet-5-5';

const TOTAL_KEYS = [
	'model_calls',
	'tokens_in',
	'tokens_out',
	'tokens_cache_read',
	'tokens_cache_write',
	'tokens_reasoning',
	'unpriced_calls'
] as const;

// 1. A preset survives navigating to another route (the cross-route filter guard).
test('the 7d preset chosen on Overview persists to Hooks', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	await page.getByTestId('preset-7d').click();
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');

	await page.getByRole('link', { name: 'Hooks' }).click();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
});

// 2. Brush-to-zoom narrows the window and its bucket count.
test('brushing the trends chart narrows the window', async ({ page }) => {
	await page.goto('/trends');
	await expectSettled(page);
	await page.getByTestId('trends-chart-table-toggle').click();
	await expect(page.getByTestId('trends-chart-table')).toBeVisible();
	const before = await page.getByTestId('trends-chart-table').locator('tbody tr').count();
	await page.getByTestId('trends-chart-table-toggle').click(); // back to the chart
	await expect(page.getByTestId('trends-chart').locator('.echart svg')).toBeVisible();

	await brush(page, 'trends-chart', 0.25, 0.75);
	await expect(page).toHaveURL(/[?&]from=/);
	const u = new URL(page.url());
	expect(u.searchParams.get('from')).toBeTruthy();
	expect(u.searchParams.get('to')).toBeTruthy();
	expect(u.searchParams.get('range')).toBeNull();

	await page.getByTestId('trends-chart-table-toggle').click(); // to the table
	// The old chart stays data-ready until the refetch lands, so poll until the narrower table arrives.
	await expect
		.poll(() => page.getByTestId('trends-chart-table').locator('tbody tr').count())
		.toBeLessThan(before);
});

// 3. A harness bar click includes, shift-click excludes.
test('a hook bar click includes and shift-click excludes', async ({ page }) => {
	await page.goto('/hooks');
	await expectSettled(page);
	await clickBar(page, 'hooks-harness', 0); // rows are key-ascending: claude, cursor, opencode
	await expect(page.getByTestId('chip-harness-claude')).toHaveAttribute('data-mode', 'include');
	await expectSettled(page);

	await clickBar(page, 'hooks-harness', 0, { shift: true });
	await expect(page.getByTestId('chip-harness-claude')).toHaveAttribute('data-mode', 'exclude');
});

// 4. A conversation id opens its timeline with the fixture totals.
test('the c5 link opens its timeline with the USAGE_C5 totals', async ({ page }) => {
	await page.goto('/conversations');
	await page.locator('a[href="/conversation?id=c5"]').click();
	await expect(page).toHaveURL(/\/conversation\?id=c5$/);
	for (const k of TOTAL_KEYS)
		await expect(page.getByTestId(`conv-total-${k}`), k).toHaveText(String(USAGE_C5[k]));
	await expect(page.getByTestId('conv-total-cost')).toContainText('$0.02');
});

// 5. Cost by model, and no `$0` on a window with only unpriced calls.
test('usage shows cost by model and never renders $0 when only unpriced', async ({ page }) => {
	await page.goto('/usage');
	await expect(page.getByTestId('usage-cost-by-model')).toBeVisible();
	await expect(page.getByTestId(`usage-${SONNET}-cost`)).toHaveText('$0.02');

	await page.goto(`/usage?model=${encodeURIComponent(QWEN)}`);
	await expect(page.getByTestId(`usage-${QWEN}-cost`)).toHaveText('unpriced');
	await expect(page.getByTestId('usage-table')).not.toContainText('$0.00');
});

// 6. A preset click, a harness drill and a brush each settle under a second.
test('a preset click, a harness drill and a brush settle under 1s', async ({ page }) => {
	await page.goto('/');
	await expectSettled(page);
	let t = performance.now();
	await page.getByTestId('preset-7d').click();
	await expectSettled(page);
	expect(performance.now() - t).toBeLessThan(1000);

	await page.goto('/hooks');
	await expectSettled(page);
	t = performance.now();
	await clickBar(page, 'hooks-harness', 0);
	await expectSettled(page);
	expect(performance.now() - t).toBeLessThan(1000);

	await page.goto('/trends');
	await expectSettled(page);
	t = performance.now();
	await brush(page, 'trends-chart', 0.25, 0.75);
	await expectSettled(page);
	expect(performance.now() - t).toBeLessThan(1000);
});

// 7. A burst collapses to one request per slot, and /repos is one request per measure.
test('a burst and the repos fan-out issue one query per slot', async ({ page }) => {
	const reqs = trackRequests(page, /analytics\/query/);

	await page.goto('/trends');
	await expectSettled(page);
	await page.waitForTimeout(400); // let the initial query settle
	reqs.reset();

	// Five preset clicks in one task: the client debounces the burst into one request per slot.
	await page.evaluate(() => {
		for (const id of ['today', '24h', '7d', '30d', '90d']) {
			(document.querySelector(`[data-testid="preset-${id}"]`) as HTMLButtonElement).click();
		}
	});
	await expect(page.getByTestId('preset-90d')).toHaveAttribute('aria-pressed', 'true');
	await page.waitForTimeout(700);
	expect(reqs.count()).toBe(1);

	reqs.reset();
	await page.goto('/repos');
	await expectSettled(page);
	expect(reqs.count()).toBe(5);

	reqs.reset();
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
	expect(reqs.count()).toBe(5);
});

// 8. Every chart is ready and every table toggle reveals rows, in light and dark, on every route.
test('every chart is ready and table-toggle-able in light and dark', async ({ page }) => {
	test.setTimeout(180_000);
	const routes = ['/', '/trends', '/usage', '/repos', '/hooks'];
	for (const scheme of ['light', 'dark'] as const) {
		await page.emulateMedia({ colorScheme: scheme });
		for (const route of routes) {
			await page.goto(route);
			await expectSettled(page);
			const toggles = page.locator('[data-testid$="-table-toggle"]');
			const count = await toggles.count();
			expect(count, `${route} ${scheme}`).toBeGreaterThan(0);
			for (let i = 0; i < count; i++) {
				const id = (await toggles.nth(i).getAttribute('data-testid')) ?? '';
				const base = id.replace(/-table-toggle$/, '');
				await toggles.nth(i).click();
				const table = page.getByTestId(`${base}-table`);
				await expect(table).toBeVisible();
				await expect(table.locator('tbody tr').first()).toBeVisible();
				await toggles.nth(i).click(); // back to the chart
			}
		}
	}
});
