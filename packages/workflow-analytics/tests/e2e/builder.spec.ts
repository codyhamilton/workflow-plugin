import { expect, test, type Page } from '@playwright/test';
import { expectSettled, serveState, useServe } from './helpers';

// The fixture days are UTC days; pin the browser zone so the /query buckets land on them.
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

test('opens with a default chart and no console error', async ({ page }) => {
	const errors: string[] = [];
	page.on('console', (m) => {
		if (m.type() === 'error') errors.push(m.text());
	});
	await page.goto('/builder');
	await expect(page.getByTestId('builder-measure')).toBeVisible();
	await expect(page.getByTestId('builder-chart')).toBeVisible();
	await expectSettled(page);
	expect(errors).toEqual([]);
});

test('cost_usd by model and harness on a day bucket renders small multiples', async ({ page }) => {
	await page.goto('/builder');
	await page.getByTestId('builder-measure').selectOption('cost_usd');
	await page.getByTestId('builder-dim-1').selectOption('model');
	await page.getByTestId('builder-dim-2').selectOption('harness');
	await expect(page.getByTestId('builder-chart-type')).toHaveValue('multiples');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'multiples');
	await expect(page.getByTestId('builder-chart-panel').first()).toBeVisible();
});

test('switching to rejections offers exactly the schema dims', async ({ page }) => {
	// Read the schema the serve actually returns; do not hard-code the rejections matrix.
	const schema = (await (await fetch(`${serveState().local}/v1/analytics/schema`)).json()) as {
		measures: { name: string; dims: string[] }[];
	};
	const rej = schema.measures.find((m) => m.name === 'rejections');
	if (!rej) throw new Error('no rejections measure in the schema');

	await page.goto('/builder');
	await page.getByTestId('builder-measure').selectOption('rejections');
	await expect(page.getByTestId('builder-dim-1')).toHaveValue('none');
	expect(await optionValues(page, 'builder-dim-1')).toEqual(['none', ...rej.dims]);
	expect(await optionValues(page, 'builder-dim-1')).not.toContain('harness');
	expect(await optionValues(page, 'builder-dim-1')).not.toContain('repo_id');
	expect(await optionValues(page, 'builder-dim-1')).not.toContain('model');
});

test('a pasted URL renders a heatmap', async ({ page }) => {
	await page.goto('/builder?m=hook_events&d=weekday&d=hour_of_day&b=none&c=heatmap');
	await expect(page.getByTestId('builder-chart')).toHaveAttribute('data-kind', 'heatmap');
	await expect(page.getByTestId('builder-chart')).toBeVisible();
});

test('reload keeps the configuration', async ({ page }) => {
	await page.goto('/builder?m=cost_usd&d=model&d=harness&b=day&c=multiples');
	await expect(page.getByTestId('builder-measure')).toHaveValue('cost_usd');
	await expect(page.getByTestId('builder-chart-type')).toHaveValue('multiples');
	await page.reload();
	await expect(page.getByTestId('builder-dim-1')).toHaveValue('model');
	await expect(page.getByTestId('builder-dim-2')).toHaveValue('harness');
	await expect(page.getByTestId('builder-measure')).toHaveValue('cost_usd');
	await expect(page.getByTestId('builder-chart-type')).toHaveValue('multiples');
});
