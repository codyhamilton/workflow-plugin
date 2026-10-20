<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { oauthApiBase, oauthCallbackTarget } from '$lib/api';
	import { IdentityPanel } from '$lib/analysis';

	let status = $state<'working' | 'ok' | 'denied' | 'failed'>('working');
	let detail = $state('Signing in…');

	onMount(() => {
		const code = page.url.searchParams.get('code') ?? '';
		const state = page.url.searchParams.get('state') ?? '';
		const base = oauthApiBase(page.url.hostname);
		const url = `${base}/oauth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;
		void (async () => {
			try {
				const res = await fetch(url, {
					credentials: 'include',
					headers: { accept: 'application/json' }
				});
				const body = (await res.json()) as { ok?: boolean; error?: string; return?: string };
				const target = oauthCallbackTarget({
					requestUrl: url,
					responseUrl: res.url,
					responseOk: res.ok,
					body,
					pageOrigin: location.origin
				});
				if (target.kind === 'navigate') {
					status = 'ok';
					detail = 'Signed in.';
					location.assign(target.path);
					return;
				}
				if (target.kind === 'denied') {
					status = 'denied';
					detail = 'Your GitHub account is not allowed to use this dashboard.';
					return;
				}
				status = 'failed';
				detail = 'Sign-in failed. Try again from the login page.';
			} catch {
				status = 'failed';
				detail = 'Sign-in failed. Try again from the login page.';
			}
		})();
	});
</script>

<IdentityPanel>
	<h1>Sign in</h1>
	<p data-testid="oauth-callback-status" data-status={status}>{detail}</p>
	{#if status === 'failed' || status === 'denied'}
		<p><a href="/login">Back to login</a></p>
	{/if}
</IdentityPanel>
