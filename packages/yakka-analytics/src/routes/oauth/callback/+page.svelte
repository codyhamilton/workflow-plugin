<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { oauthApiBase } from '$lib/api';

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
				if (body.ok) {
					status = 'ok';
					detail = 'Signed in.';
					const ret = typeof body.return === 'string' && body.return.startsWith('/') && !body.return.startsWith('//')
						? body.return
						: '/';
					location.assign(ret);
					return;
				}
				if (body.error === 'denied') {
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

<h1>Sign in</h1>
<p data-testid="oauth-callback-status" data-status={status}>{detail}</p>
{#if status === 'failed' || status === 'denied'}
	<p><a href="/login">Back to login</a></p>
{/if}
