import { expect, test } from '@playwright/test';
import { FILTER_REPO, SUMMARY_ALL, SUMMARY_R1 } from './fixture';
import { useServe } from './helpers';

async function expectNumbers(page: import('@playwright/test').Page, want: Record<string, number>) {
	for (const [k, v] of Object.entries(want)) {
		await expect(page.getByTestId(`summary-${k}`), k).toHaveText(String(v));
	}
}

test.beforeEach(async ({ page }) => {
	await useServe(page, 'local');
});

test('overview shows the fixture numbers for the whole window', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
});

test('repo_id in the URL filters, and survives a reload', async ({ page }) => {
	await page.goto(`/?repo_id=${FILTER_REPO}`);
	await expectNumbers(page, SUMMARY_R1);
	await page.reload();
	expect(new URL(page.url()).searchParams.getAll('repo_id')).toEqual([FILTER_REPO]);
	await expectNumbers(page, SUMMARY_R1);
});

test('choosing a repo in the filter bar changes the URL and the numbers', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	await page.getByTestId('filter-repo_id').selectOption(FILTER_REPO);
	await expect(page).toHaveURL(new RegExp(`repo_id=${FILTER_REPO}`));
	await expectNumbers(page, SUMMARY_R1);
	await page.goBack();
	await expectNumbers(page, SUMMARY_ALL);
});

test('no filter control offers an empty option', async ({ page }) => {
	await page.goto('/');
	await expectNumbers(page, SUMMARY_ALL);
	for (const name of ['repo_id', 'harness', 'kind', 'plan']) {
		const opts = await page.getByTestId(`filter-${name}`).locator('option').evaluateAll((os) =>
			os.map((o) => ({ value: (o as HTMLOptionElement).value, text: (o.textContent ?? '').trim() }))
		);
		expect(opts.length, name).toBeGreaterThan(0);
		for (const o of opts) {
			expect(o.value, name).not.toBe('');
			expect(o.text, name).not.toBe('');
		}
	}
});
