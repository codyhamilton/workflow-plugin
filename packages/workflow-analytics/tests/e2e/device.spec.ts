import { expect, test } from '@playwright/test';

test('device page starts with empty expiry and blocks submit until choices are set', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: 'acme' }] }
		})
	);
	await page.goto('/device?state=abc&redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcb');
	await expect(page.getByTestId('device-expires')).toHaveValue('');
	await expect(page.getByTestId('device-submit')).toBeDisabled();
	await page.getByTestId('device-tenant').selectOption('acme');
	await page.getByTestId('device-grant').selectOption('read');
	await expect(page.getByTestId('device-submit')).toBeDisabled();
	const future = '2099-06-15T12:00';
	await page.getByTestId('device-expires').fill(future);
	await expect(page.getByTestId('device-submit')).toBeEnabled();
});

test('device submit posts authorize JSON and never renders token plaintext', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: 'acme' }] }
		})
	);
	let authorizeBody: unknown;
	await page.route('**/v1/device/authorize', async (route) => {
		authorizeBody = route.request().postDataJSON();
		// Same-origin redirect so fetch redirect:manual can read Location (Playwright mock).
		const u = new URL(page.url());
		await route.fulfill({
			status: 303,
			headers: { Location: `${u.origin}/device?state=abc&redirect_uri=${encodeURIComponent('http://127.0.0.1:8765/cb')}&done=1` }
		});
	});
	await page.goto('/device?state=abc&redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcb');
	await page.getByTestId('device-tenant').selectOption('acme');
	await page.getByTestId('device-grant').selectOption('read_write');
	await page.getByTestId('device-expires').fill('2099-06-15T12:00');
	await Promise.all([page.waitForURL(/done=1/), page.getByTestId('device-submit').click()]);
	await expect.poll(() => authorizeBody).toBeTruthy();
	expect(authorizeBody).toMatchObject({
		redirect_uri: 'http://127.0.0.1:8765/cb',
		state: 'abc',
		tenant: 'acme',
		scope: 'read_write'
	});
	await expect(page.locator('body')).not.toContainText('wk_');
});
