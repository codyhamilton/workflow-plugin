import { expect, test } from '@playwright/test';
import { SUMMARY_ALL } from './fixture';
import { serveState } from './helpers';

test('settings stores base and key; the keyed serve sees a bearer header; clearing the key gives 401', async ({ page }) => {
	const s = serveState();
	await page.goto('/settings');
	await page.getByTestId('settings-base').fill(s.keyed);
	await page.getByTestId('settings-key').fill(s.key);
	await page.getByTestId('settings-save').click();

	const stored = await page.evaluate(() => ({
		base: localStorage.getItem('workflow-analytics-base'),
		key: localStorage.getItem('workflow-analytics-key')
	}));
	expect(stored).toEqual({ base: s.keyed, key: s.key });

	const req = page.waitForRequest((r) => r.url().startsWith(`${s.keyed}/v1/analytics/summary`));
	await page.goto('/');
	const sent = await req;
	expect(sent.method()).toBe('GET');
	expect(await sent.headerValue('authorization')).toBe(`Bearer ${s.key}`);
	for (const [k, v] of Object.entries(SUMMARY_ALL)) {
		await expect(page.getByTestId(`summary-${k}`), k).toHaveText(String(v));
	}

	// Clear the key: the keyed serve answers 401 and the error panel says so.
	await page.goto('/settings');
	await page.getByTestId('settings-key').fill('');
	await page.getByTestId('settings-save').click();
	expect(await page.evaluate(() => localStorage.getItem('workflow-analytics-key'))).toBe('');
	await page.goto('/');
	await expect(page.getByTestId('error-panel')).toBeVisible();
	await expect(page.getByTestId('error-panel')).toContainText('unauthorized');
	await expect(page.getByTestId('error-panel')).toContainText('/settings');
});
