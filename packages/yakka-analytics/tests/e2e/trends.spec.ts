import { expect, test, type Page } from '@playwright/test';
import { DAYS, HOOK_EVENTS_BY_DAY } from './fixture';
import { brush, expectSettled, trackRequests, useServe } from './helpers';

const SONNET = 'anthropic/claude-sonnet-5-5';

// The fixture days are UTC days; pin the browser zone so the /query buckets land on them.
test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

const dayBefore = (day: string): string =>
	new Date(Date.parse(`${day}T00:00:00Z`) - 86_400_000).toISOString().slice(0, 10);

/** Switch the chart to its data table (columns: Time then one per series). */
async function showTable(page: Page) {
	await expect(page.getByTestId('trends-chart')).toBeVisible();
	if ((await page.getByTestId('trends-chart-table').count()) === 0) {
		await page.getByTestId('trends-chart-table-toggle').click();
	}
	await expect(page.getByTestId('trends-chart-table')).toBeVisible();
}

/** ECharts line drill under an armed brush: click paths 0..`DRILL_SERIES_PATH` on the SVG (legend clicks do not fire). */
const DRILL_SERIES_PATH = 6;

async function drillTrendsSeries(page: Page, testid: string): Promise<string> {
	await expect(page.getByTestId(testid).locator('.echart svg')).toBeVisible();
	for (let i = 0; i <= DRILL_SERIES_PATH; i++) {
		await page.getByTestId(testid).locator('.echart svg path').nth(i).click({ force: true });
		await page.waitForTimeout(40);
	}
	const model = new URL(page.url()).searchParams.getAll('model')[0];
	if (!model) throw new Error('drillTrendsSeries: series click did not add a model filter');
	return model;
}

async function shiftDrillTrendsSeries(page: Page, testid: string): Promise<void> {
	await page.keyboard.down('Shift');
	await page.getByTestId(testid).locator('.echart svg path').nth(DRILL_SERIES_PATH).click({ force: true });
	await page.keyboard.up('Shift');
}

/** The cell text for `series` on UTC day `day`, read from the chart's data table. */
async function cellOf(page: Page, series: string, day: string): Promise<string> {
	const table = page.getByTestId('trends-chart-table');
	const headers = await table.locator('thead th').allTextContents();
	const col = headers.indexOf(series);
	if (col < 0) throw new Error(`no "${series}" column; have ${headers.join(', ')}`);
	const rows = await table.locator('tbody tr').evaluateAll((trs) =>
		trs.map((tr) => Array.from(tr.querySelectorAll('td'), (td) => td.textContent ?? ''))
	);
	const row = rows.find((r) => (r[0] ?? '').slice(0, 10) === day);
	if (!row) throw new Error(`no row for ${day}; rows ${rows.map((r) => r[0]).join(', ')}`);
	return row[col];
}

test('the default render matches the per-day hook_events counts', async ({ page }) => {
	await page.goto('/trends');
	await showTable(page);
	for (const [t, n] of Object.entries(HOOK_EVENTS_BY_DAY)) {
		expect(await cellOf(page, 'all', t), `all ${t}`).toBe(String(n));
	}
	// No facts on d3 (between d4 and d2): the gap reads as zero, not as a join across it.
	expect(await cellOf(page, 'all', dayBefore(DAYS.d2)), 'gap day').toBe('0');
});

test('cost_usd grouped by model shows the two priced days', async ({ page }) => {
	await page.goto('/trends?metric=cost_usd&group=model');
	await showTable(page);
	expect(await cellOf(page, SONNET, DAYS.d4), 'sonnet d4').toBe('0.0123');
	expect(await cellOf(page, SONNET, DAYS.d1), 'sonnet d1').toBe('0.01');
});

test('grouped series click filters by model; shift-click excludes', async ({ page }) => {
	await page.goto('/trends?metric=cost_usd&group=model');
	await expectSettled(page);
	const model = await drillTrendsSeries(page, 'trends-chart');
	const chip = page.getByTestId(`chip-model-${model}`);
	await expect(chip).toBeVisible();
	await expect(chip).toHaveAttribute('data-mode', 'include');
	await shiftDrillTrendsSeries(page, 'trends-chart');
	await expect(chip).toHaveAttribute('data-mode', 'exclude');
});

test('stacked area lists multiple series columns that sum per bucket', async ({ page }) => {
	await page.goto('/trends?metric=cost_usd&group=model');
	await expectSettled(page);
	await page.getByTestId('trends-chart-style').selectOption('area');
	await expect(page).toHaveURL(/chart=area/);
	await showTable(page);
	const table = page.getByTestId('trends-chart-table');
	const headers = await table.locator('thead th').allTextContents();
	expect(headers.length).toBeGreaterThan(2);
	const rows = await table.locator('tbody tr').evaluateAll((trs) =>
		trs.map((tr) => Array.from(tr.querySelectorAll('td'), (td) => td.textContent ?? ''))
	);
	const row = rows.find((r) => (r[0] ?? '').slice(0, 10) === DAYS.d4);
	expect(row, `row for ${DAYS.d4}`).toBeTruthy();
	const nums = row!.slice(1).map((c) => Number(c));
	expect(nums.some((n) => n > 0)).toBe(true);
	const sum = nums.reduce((a, b) => a + b, 0);
	expect(sum).toBeCloseTo(0.0123, 5);
});

test('the group list only offers the chosen measure dims', async ({ page }) => {
	await page.goto('/trends?metric=hook_events&group=harness');
	await expect(page.getByTestId('trends-group')).toHaveValue('harness');
	await expect(page.getByTestId('trends-group').locator('option[value="tool"]')).toHaveCount(1);
	await page.getByTestId('trends-metric').selectOption('rejections');
	await expect(page).toHaveURL(/metric=rejections/);
	const opts = await page
		.getByTestId('trends-group')
		.locator('option')
		.evaluateAll((os) => os.map((o) => (o as HTMLOptionElement).value));
	expect(opts).not.toContain('harness');
	expect(opts).not.toContain('tool');
	await expect(page.getByTestId('trends-group')).toHaveValue('none');
});

test('range=all keeps the request bucket in range', async ({ page }) => {
	const reqs = trackRequests(page, /analytics\/query/);
	await page.goto('/trends?range=all');
	await expectSettled(page);
	const opts = await page
		.getByTestId('trends-bucket')
		.locator('option')
		.evaluateAll((os) => os.map((o) => (o as HTMLOptionElement).value));
	expect(opts).not.toContain('hour');
	expect(opts).not.toContain('day');
	expect(opts.length).toBeGreaterThan(0);
	const url = reqs.urls().find((u) => u.includes('analytics/query'));
	expect(url, 'a query request went out').toBeTruthy();
	const params = new URL(url!).searchParams;
	expect(opts).toContain(params.get('bucket'));
	// The brief asks for all=1 here; over the whole ledger every bucket unit exceeds the 400
	// cap, so the page clamps All time to 399 days (as the shell already does) instead.
	expect(params.get('all')).toBeNull();
	expect(params.get('from')).toBeTruthy();
	await expect(page.getByTestId('error-panel')).toHaveCount(0);
});

test('a brush narrows the window and clears the active preset', async ({ page }) => {
	await page.goto('/trends');
	await expectSettled(page);
	await brush(page, 'trends-chart', 0.25, 0.75);
	await expect(page).toHaveURL(/[?&]from=/);
	const u = new URL(page.url());
	expect(u.searchParams.get('from')).toBeTruthy();
	expect(u.searchParams.get('to')).toBeTruthy();
	expect(u.searchParams.get('range')).toBeNull();
	const span = Date.parse(u.searchParams.get('to')!) - Date.parse(u.searchParams.get('from')!);
	expect(span).toBeGreaterThan(0);
	expect(span).toBeLessThan(30 * 86_400_000);
	for (const id of ['preset-7d', 'preset-30d', 'preset-all']) {
		await expect(page.getByTestId(id)).toHaveAttribute('aria-pressed', 'false');
	}
	await expectSettled(page);
});

test('a metric change settles inside a second', async ({ page }) => {
	await page.goto('/trends');
	await expectSettled(page);
	const t0 = Date.now();
	await page.getByTestId('trends-metric').selectOption('cost_usd');
	await expectSettled(page);
	expect(Date.now() - t0).toBeLessThan(1000);
});

test('a burst of metric changes issues one query', async ({ page }) => {
	await page.goto('/trends');
	await expectSettled(page);
	const reqs = trackRequests(page, /analytics\/query/);
	const sel = page.getByTestId('trends-metric');
	// End on a measure the load did not already fetch, so the survivor is a network request and
	// not a cache hit.
	for (const m of ['commits', 'conversations', 'artifact_versions', 'hook_events', 'cost_usd']) {
		await sel.selectOption(m);
	}
	await page.waitForTimeout(700);
	expect(reqs.count()).toBe(1);
});
