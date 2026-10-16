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

test('device submit form-posts authorize once and navigates to loopback redirect', async ({ page }) => {
	await page.route('**/v1/me', (route) =>
		route.fulfill({
			json: { github_id: 1, github_login: 'u', admin: false, tenants: [{ name: 'acme' }] }
		})
	);
	let authorizeCalls = 0;
	let authorizeBody: Record<string, string> | undefined;
	await page.route('**/v1/device/authorize', async (route) => {
		authorizeCalls += 1;
		const post = route.request().postData() ?? '';
		authorizeBody = Object.fromEntries(new URLSearchParams(post));
		await route.fulfill({
			status: 303,
			headers: {
				Location: 'http://127.0.0.1:8765/cb?code=device-code&state=abc'
			}
		});
	});
	await page.goto('/device?state=abc&redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcb');
	await page.getByTestId('device-tenant').selectOption('acme');
	await page.getByTestId('device-grant').selectOption('read_write');
	await page.getByTestId('device-expires').fill('2099-06-15T12:00');
	const loopbackNav = page.waitForRequest(
		(req) =>
			req.method() === 'GET' &&
			req.url().startsWith('http://127.0.0.1:8765/cb?code=device-code&state=abc')
	);
	await page.getByTestId('device-submit').click();
	await loopbackNav;
	expect(authorizeCalls).toBe(1);
	expect(authorizeBody).toMatchObject({
		redirect_uri: 'http://127.0.0.1:8765/cb',
		state: 'abc',
		tenant: 'acme',
		scope: 'read_write'
	});
	expect(authorizeBody?.expires_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
	await expect(page.locator('body')).not.toContainText('wk_');
});
