import { readFileSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
import { allowedCharts, type Bucket } from '../../src/lib/builder';
import { presetWindow } from '../../src/lib/presets';
import { EXECUTION_ROWS } from './fixture';
import { expectSettled, serveState, useServe } from './helpers';

// Phase 5's end-to-end proof (5-17). The fixture days are UTC days; pin the browser zone so the
// /query buckets and the heatmap dims land on them, as interactions.spec.ts does.
test.use({ timezoneId: 'UTC' });

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

/** The option values of a `<select>` by test id. */
async function optionValues(page: Page, testid: string): Promise<string[]> {
	return page
		.getByTestId(testid)
		.locator('option')
		.evaluateAll((os) => os.map((o) => (o as HTMLOptionElement).value));
}

/** Poll a select's option values to `want` so a pending navigation cannot race the read. */
async function expectOptions(page: Page, testid: string, want: string[]) {
	await expect.poll(() => optionValues(page, testid), { message: testid }).toEqual(want);
}

/** A GET against the local serve, as the specs read the fixture's real API responses. */
async function getJSON<T>(path: string): Promise<T> {
	const res = await fetch(`${serveState().local}${path}`);
	if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
	return (await res.json()) as T;
}

// The builder's bucket=none query keeps the current view window; the heatmap test never sets a
// range, so that window is the default 30d preset (from/to), not `all=1`. This mirrors it: a
// 0-dimension query over that window returns one row.
async function measureTotal(measure: string): Promise<number> {
	const win = presetWindow('30d', new Date(), 'UTC')!;
	const q = new URLSearchParams({ measure, from: win.from.toISOString(), to: win.to.toISOString() });
	const r = await getJSON<{ rows: { v: number }[] }>(`/v1/analytics/query?${q}`);
	return r.rows.reduce((a, row) => a + row.v, 0);
}

/** Save a builder view, create a dashboard and add the view: the shared setup for tests 4 and 5. */
async function saveViewAndBuildDashboard(page: Page, viewName: string, dashName: string) {
	await page.goto('/builder');
	await expectSettled(page);
	await page.getByTestId('builder-measure').selectOption('cost_usd');
	await page.getByTestId('builder-dim-1').selectOption('model');
	await page.getByTestId('builder-dim-2').selectOption('harness');
	await page.getByTestId('builder-bucket').selectOption('day');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'multiples');

	await page.getByTestId('saveview-name').fill(viewName);
	await page.getByTestId('saveview-save').click();

	await page.goto('/dashboards');
	await page.getByTestId('dash-name').fill(dashName);
	await page.getByTestId('dash-create').click();
	await expect(page).toHaveURL(/\/dashboards\?d=/);
	await page.getByTestId('dash-add-select').selectOption({ label: viewName });
	await page.getByTestId('dash-add').click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);
}

// 1. Small multiples: cost_usd x model x harness on a day bucket.
test('small multiples panels equal the distinct harnesses in the API', async ({ page }) => {
	// Derive the expected panel count from a real API request over the same fixture, not a literal.
	const api = await getJSON<{ rows: { k: string[] }[] }>(
		'/v1/analytics/query?measure=cost_usd&dim=harness&all=1'
	);
	const harnesses = new Set(api.rows.map((r) => r.k[0]));
	expect(harnesses.size, 'fixture must have at least two harnesses with cost rows').toBeGreaterThanOrEqual(2);

	await page.goto('/builder');
	await expectSettled(page);
	await page.getByTestId('builder-measure').selectOption('cost_usd');
	await page.getByTestId('builder-dim-1').selectOption('model');
	await page.getByTestId('builder-dim-2').selectOption('harness');
	await page.getByTestId('builder-bucket').selectOption('day');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'multiples');
	await expectSettled(page);
	await expect(page.getByTestId('builder-chart-panel')).toHaveCount(harnesses.size);
	// The panels are one per harness: their titles are the API's harness keys.
	const titles = await page
		.getByTestId('builder-chart-panel')
		.locator('h4')
		.evaluateAll((hs) => hs.map((h) => h.textContent?.trim() ?? ''));
	expect([...titles].sort()).toEqual([...harnesses].sort());
});

// 2. Heatmap: hour_of_day x weekday sums to the measure's API total.
test('the heatmap table sums to the measure total from the API', async ({ page }) => {
	const total = await measureTotal('hook_events');

	await page.goto('/builder');
	await expectSettled(page);
	await page.getByTestId('builder-measure').selectOption('hook_events');
	await page.getByTestId('builder-dim-1').selectOption('hour_of_day');
	await page.getByTestId('builder-dim-2').selectOption('weekday');
	await page.getByTestId('builder-bucket').selectOption('none');
	await page.getByTestId('builder-chart-type').selectOption('heatmap');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'heatmap');
	await expectSettled(page);

	// The heatmap renders under `builder-chart-chart`; reveal its table and sum the value cells.
	await page.getByTestId('builder-chart-chart-table-toggle').click();
	const table = page.getByTestId('builder-chart-chart-table');
	await expect(table).toBeVisible();
	const cells = table.locator('tbody td[data-value]');
	const values = await cells.evaluateAll((ts) =>
		ts.map((t) => Number(t.getAttribute('data-value')))
	);
	expect(values.length).toBeGreaterThan(0);
	expect(values.reduce((a, b) => a + b, 0)).toBe(total);
});

// 3. No unsupported pairing selectable: every measure's select options equal the schema + 5-02 table.
test('every measure offers exactly its schema dims and the allowed chart kinds', async ({ page }) => {
	test.setTimeout(180_000);
	const schema = await getJSON<{ measures: { name: string; dims: string[] }[] }>(
		'/v1/analytics/schema'
	);

	await page.goto('/builder');
	await expectSettled(page);
	for (const m of schema.measures) {
		await page.getByTestId('builder-measure').selectOption(m.name);
		// Clear any carried-over dims: dim-2 first, then dim-1 (setDim shifts indices).
		await page.getByTestId('builder-dim-2').selectOption('none');
		await page.getByTestId('builder-dim-1').selectOption('none');
		await expectOptions(page, 'builder-dim-1', ['none', ...m.dims]);
		await expectOptions(page, 'builder-dim-2', ['none', ...m.dims]);

		const bucket = (await page.getByTestId('builder-bucket').inputValue()) as Bucket;
		await expectOptions(page, 'builder-chart-type', allowedCharts(0, bucket));

		// One dimension: the other select drops the chosen one, and chart kinds fit one dim.
		await page.getByTestId('builder-dim-1').selectOption(m.dims[0]);
		await expectOptions(
			page,
			'builder-dim-2',
			['none', ...m.dims.filter((d) => d !== m.dims[0])]
		);
		await expectOptions(page, 'builder-chart-type', allowedCharts(1, bucket));

		// Two dimensions: each select drops the other's choice, and chart kinds fit two dims.
		await page.getByTestId('builder-dim-2').selectOption(m.dims[1]);
		await expectOptions(
			page,
			'builder-dim-1',
			['none', ...m.dims.filter((d) => d !== m.dims[1])]
		);
		await expectOptions(page, 'builder-chart-type', allowedCharts(2, bucket));
	}
});

// 4. A saved view added to a new dashboard survives a reload, and its tile renders.
test('a builder view saved and added to a dashboard survives a reload', async ({ page }) => {
	await saveViewAndBuildDashboard(page, 'Cost split', 'Ops');

	await page.reload();
	await expect(page.getByTestId('dash-item').filter({ hasText: 'Ops' })).toBeVisible();
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);
	const frame = page.frameLocator('[data-testid="dash-tile"] iframe').first();
	await expect(frame.getByTestId('builder-chart')).toBeVisible({ timeout: 15_000 });
});

// 5. Export the dashboard JSON and import it into a fresh browser profile.
test('a dashboard exports and imports into a fresh profile', async ({ page, browser }) => {
	await saveViewAndBuildDashboard(page, 'Cost split', 'Ops');

	const [download] = await Promise.all([
		page.waitForEvent('download'),
		page.getByTestId('dash-export').click()
	]);
	expect(download.suggestedFilename()).toBe('Ops.json');
	const filePath = (await download.path())!;
	const json = JSON.parse(readFileSync(filePath, 'utf8'));
	expect(json).toMatchObject({ version: 1, name: 'Ops' });

	// A fresh context has empty localStorage; add the serve init script before the first navigation.
	const ctx = await browser.newContext({ timezoneId: 'UTC' });
	const fresh = await ctx.newPage();
	await useServe(fresh, 'local');
	await fresh.goto('/dashboards');
	// The file input drives the same import path as the textarea; the downloaded file is used.
	await fresh.getByTestId('dash-import-file').setInputFiles(filePath);
	await expect(fresh).toHaveURL(/\/dashboards\?d=/);
	await expect(fresh.getByTestId('dash-item').filter({ hasText: 'Ops' })).toBeVisible();
	await expect(fresh.getByTestId('dash-tile')).toHaveCount(1);
	const frame = fresh.frameLocator('[data-testid="dash-tile"] iframe').first();
	await expect(frame.getByTestId('builder-chart')).toBeVisible({ timeout: 15_000 });
	await ctx.close();
});

// 6. The executions sankey's commit -> report link filters the table and toggles off.
test('the sankey commit->report link filters the table and restores it', async ({ page }) => {
	const complete = EXECUTION_ROWS.filter((r) => r.shape === 'complete');
	await page.goto('/executions');
	await expectSettled(page);
	await expect(page.getByTestId('exec-row')).toHaveCount(EXECUTION_ROWS.length);

	await page.getByTestId('exec-link-commit-report').click();
	await expect(page.getByTestId('exec-link-commit-report')).toHaveAttribute('aria-pressed', 'true');
	await expect(page.getByTestId('exec-row')).toHaveCount(complete.length);
	for (const [i, r] of complete.entries())
		await expect(page.getByTestId('exec-row').nth(i)).toContainText(r.shape);

	await page.getByTestId('exec-link-commit-report').click();
	await expect(page.getByTestId('exec-link-commit-report')).toHaveAttribute('aria-pressed', 'false');
	await expect(page.getByTestId('exec-row')).toHaveCount(EXECUTION_ROWS.length);
});

// 7. Five interactions settle within 1 s after a warm-up load, as interactions.spec.ts measures.
test('builder, dashboard and executions interactions settle under 1s', async ({ page }) => {
	test.setTimeout(180_000);
	const timings: Record<string, number> = {};

	// (a) builder chart-type change (a render swap, no re-query). The swap is proved by the chart's
	// data-kind changing before we accept the settle, so a stale chart cannot pass.
	await page.goto('/builder');
	await expectSettled(page);
	let t = performance.now();
	await page.getByTestId('builder-chart-type').selectOption('bar');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'bar');
	await expectSettled(page);
	timings['builder-chart-type'] = performance.now() - t;

	// (b) builder measure change (a re-query). Waiting for the new measure's response proves the
	// query that settles the chart is the new one, not the stale pre-refetch render.
	await page.goto('/builder');
	await expectSettled(page);
	t = performance.now();
	const measureResp = page.waitForResponse(
		(r) => r.url().includes('/v1/analytics/query') && r.url().includes('measure=cost_usd')
	);
	await page.getByTestId('builder-measure').selectOption('cost_usd');
	await measureResp;
	await expectSettled(page);
	timings['builder-measure'] = performance.now() - t;

	// (c) dashboard create-and-add. The dashboards route has no data-ready mark (its tiles are
	// iframes), so this one measures to the tile appearing rather than expectSettled.
	await page.goto('/builder');
	await expectSettled(page);
	await page.getByTestId('saveview-name').fill('Perf view');
	await page.getByTestId('saveview-save').click();
	await page.goto('/dashboards');
	await expect(page.getByTestId('dash-name')).toBeVisible();
	t = performance.now();
	await page.getByTestId('dash-name').fill('Perf');
	await page.getByTestId('dash-create').click();
	await expect(page.getByTestId('dash-item').filter({ hasText: 'Perf' })).toBeVisible();
	await page.getByTestId('dash-add-select').selectOption({ label: 'Perf view' });
	await page.getByTestId('dash-add').click();
	await expect(page.getByTestId('dash-tile')).toHaveCount(1);
	timings['dashboard-create-add'] = performance.now() - t;

	// (d) executions sankey link click (a client-side table filter).
	await page.goto('/executions');
	await expectSettled(page);
	t = performance.now();
	await page.getByTestId('exec-link-commit-report').click();
	await expect(page.getByTestId('exec-link-commit-report')).toHaveAttribute('aria-pressed', 'true');
	await expect(page.getByTestId('exec-row')).toHaveCount(
		EXECUTION_ROWS.filter((r) => r.shape === 'complete').length
	);
	timings['executions-link'] = performance.now() - t;

	// (e) a preset change on /builder (the FilterBar's preset-7d is shown on every chrome route).
	// Capture the initial query's URL, then wait for a query whose URL differs (the 7d window), so
	// the settle is proven against the new request rather than the stale pre-refetch render.
	const initialQuery = page.waitForRequest((r) => r.url().includes('/v1/analytics/query'));
	await page.goto('/builder');
	const initialQueryUrl = (await initialQuery).url();
	await expectSettled(page);
	t = performance.now();
	const presetResp = page.waitForResponse(
		(r) => r.url().includes('/v1/analytics/query') && r.url() !== initialQueryUrl
	);
	await page.getByTestId('preset-7d').click();
	await presetResp;
	await expectSettled(page);
	timings['builder-preset-7d'] = performance.now() - t;

	for (const [k, v] of Object.entries(timings)) console.log(`timing ${k}: ${v.toFixed(1)} ms`);
	for (const [k, v] of Object.entries(timings)) expect(v, k).toBeLessThan(1000);
});
