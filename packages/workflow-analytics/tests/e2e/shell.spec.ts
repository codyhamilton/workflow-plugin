import { expect, test } from '@playwright/test';
import { FILTER_REPO } from './fixture';
import { trackRequests, useServe } from './helpers';

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('a preset survives navigating to another route and a reload', async ({ page }) => {
	await page.goto('/');
	await page.getByTestId('preset-7d').click();
	await expect(page).toHaveURL(/range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');

	await page.getByRole('link', { name: 'Hooks' }).click();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');

	await page.reload();
	await expect(page).toHaveURL(/\/hooks\?.*range=7d/);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
});

test('the custom range inputs set from and to', async ({ page }) => {
	await page.goto('/');
	const from = page.getByTestId('filter-from');
	const to = page.getByTestId('filter-to');

	await from.fill('2026-01-01');
	await from.dispatchEvent('change');
	await expect(page).toHaveURL(/from=2026-01-01/);

	await to.fill('2026-01-31');
	await to.dispatchEvent('change');
	await expect(page).toHaveURL(/to=2026-01-31/);
	await expect(page.getByTestId('preset-30d')).toHaveAttribute('aria-pressed', 'false');
});

test('removing a chip drops it from the URL', async ({ page }) => {
	await page.goto(`/?repo_id=${FILTER_REPO}`);
	await expect(page.getByTestId(`chip-repo_id-${FILTER_REPO}`)).toBeVisible();
	await page.getByTestId(`chip-remove-repo_id-${FILTER_REPO}`).click();
	await expect(page.getByTestId(`chip-repo_id-${FILTER_REPO}`)).toHaveCount(0);
	await expect(page).not.toHaveURL(/repo_id/);
});

test('the layout fits 1024x768 without a horizontal scrollbar', async ({ page }) => {
	await page.setViewportSize({ width: 1024, height: 768 });
	await page.goto('/?range=7d');
	await expect(page.getByTestId('preset-7d')).toBeVisible();
	const { scroll, inner } = await page.evaluate(() => ({
		scroll: document.documentElement.scrollWidth,
		inner: window.innerWidth
	}));
	expect(scroll).toBeLessThanOrEqual(inner);
});

const SERIES = [
	'#268bd2',
	'#859900',
	'#b58900',
	'#cb4b16',
	'#dc322f',
	'#d33682',
	'#6c71c4',
	'#2aa198'
];

async function readThemeVars(page: import('@playwright/test').Page) {
	return page.evaluate((series) => {
		const cs = getComputedStyle(document.documentElement);
		const token = (name: string) => cs.getPropertyValue(name).trim();
		return {
			bg: token('--bg'),
			text: token('--text'),
			series: series.map((_, i) => token(`--series-${i + 1}`))
		};
	}, SERIES);
}

test('the dark scheme swaps the background token', async ({ page }) => {
	await page.goto('/');
	const light = await page.evaluate(() =>
		getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()
	);
	await page.emulateMedia({ colorScheme: 'dark' });
	await expect
		.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()))
		.not.toBe(light);
});

test('system dark mode uses solarized tokens on overview and settings', async ({ page }) => {
	await page.addInitScript(() => localStorage.removeItem('workflow-analytics-theme'));
	await page.emulateMedia({ colorScheme: 'dark' });
	for (const path of ['/', '/settings']) {
		await page.goto(path);
		await expect.poll(async () => (await readThemeVars(page)).bg).toBe('#002b36');
		const vars = await readThemeVars(page);
		expect(vars.text).toBe('#839496');
		expect(vars.series).toEqual(SERIES);
	}
});

test('choosing Light updates tokens without reload and survives reload', async ({ page }) => {
	await page.goto('/');
	await page.getByTestId('theme-light').click();
	await expect
		.poll(async () => (await readThemeVars(page)).bg)
		.toBe('#fdf6e3');
	expect((await readThemeVars(page)).text).toBe('#657b83');
	await page.reload();
	expect((await readThemeVars(page)).bg).toBe('#fdf6e3');
	expect((await readThemeVars(page)).text).toBe('#657b83');
});

test('system mode follows a later OS colour-scheme change', async ({ page }) => {
	await page.addInitScript(() => localStorage.removeItem('workflow-analytics-theme'));
	await page.emulateMedia({ colorScheme: 'light' });
	await page.goto('/');
	expect((await readThemeVars(page)).bg).toBe('#fdf6e3');
	await page.getByTestId('theme-system').click();
	await page.emulateMedia({ colorScheme: 'dark' });
	await expect.poll(async () => (await readThemeVars(page)).bg).toBe('#002b36');
});

test('a burst of preset clicks reaches the facets endpoint at most twice', async ({ page }) => {
	const facets = trackRequests(page, '/v1/analytics/facets');
	await page.goto('/');
	await expect(page.getByTestId('preset-7d')).toBeVisible();
	await page.waitForTimeout(400); // let the initial facets request settle
	facets.reset();

	// Five clicks in one task: the client debounces the burst into at most a couple of requests.
	await page.evaluate(() => {
		for (const id of ['today', '24h', '7d', '30d', '90d']) {
			(document.querySelector(`[data-testid="preset-${id}"]`) as HTMLButtonElement).click();
		}
	});
	await expect(page.getByTestId('preset-90d')).toHaveAttribute('aria-pressed', 'true');
	await page.waitForTimeout(600);
	expect(facets.count()).toBeLessThanOrEqual(2);
});

test('a saved view is listed and survives a reload', async ({ page }) => {
	await page.goto('/?range=7d');
	await page.getByTestId('saveview-name').fill('weekly');
	await page.getByTestId('saveview-save').click();
	await page.getByTestId('saveview-menu-toggle').click();

	const item = page.getByTestId('saveview-item').filter({ hasText: 'weekly' });
	await expect(item).toBeVisible();
	await expect(item).toHaveAttribute('href', '/');

	await page.reload();
	await page.getByTestId('saveview-menu-toggle').click();
	await expect(page.getByTestId('saveview-item').filter({ hasText: 'weekly' })).toBeVisible();
});

test('save view stores chart params only', async ({ page }) => {
	await page.goto('/trends?range=7d&repo_id=r1&metric=commits&group=harness&bucket=day');
	await page.getByTestId('saveview-name').fill('trends-view');
	await page.getByTestId('saveview-save').click();

	const raw = await page.evaluate(() => localStorage.getItem('workflow-analytics-views:views'));
	expect(raw).toBeTruthy();
	const views = JSON.parse(raw!) as Record<string, unknown>[];
	const entry = views.find((v) => v.name === 'trends-view');
	expect(entry).toBeTruthy();
	expect(entry!.report).toBe('trends');
	const params = entry!.params as Record<string, string>;
	expect(params.metric).toBe('commits');
	expect(params.group).toBe('harness');
	expect(params.bucket).toBe('day');
	expect(entry).not.toHaveProperty('range');
	expect(entry).not.toHaveProperty('repo_id');
	expect(entry).not.toHaveProperty('url');
	expect(params).not.toHaveProperty('range');
	expect(params).not.toHaveProperty('repo_id');
});

test('dashboards shares filter chrome; embed=1 no longer hides the shell', async ({ page }) => {
	await page.goto('/dashboards?range=7d');
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
	await expect(page.getByTestId('saveview-save')).toBeVisible();

	await page.goto('/trends?range=7d&embed=1');
	await expect(page.locator('header')).toHaveCount(1);
	await expect(page.getByTestId('preset-7d')).toHaveAttribute('aria-pressed', 'true');
	await expect(page.getByTestId('saveview-save')).toBeVisible();
	await expect(page.getByTestId('trends-chart')).toBeVisible();
});

test('the nav links to Builder and Dashboards', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('link', { name: 'Builder' })).toHaveAttribute('href', /\/builder/);
	await expect(page.getByRole('link', { name: 'Dashboards' })).toHaveAttribute('href', /\/dashboards/);
});

test('an ignored-filter notice survives a view change that re-requests it', async ({ page }) => {
	await page.goto('/trends?kind=brief');
	await expect(page.getByTestId('notice-ignored')).toBeVisible();

	// Preset 30d is the default window, so this is a cache hit: the shell must not erase the notice.
	await page.getByTestId('preset-30d').click();
	await page.waitForTimeout(500);
	await expect(page.getByTestId('notice-ignored')).toBeVisible();
});
