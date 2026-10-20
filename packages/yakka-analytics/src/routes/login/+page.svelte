<script lang="ts">
	import { page } from '$app/state';
	import { oauthLoginPath } from '$lib/api';
	import { IdentityPanel } from '$lib/analysis';

	const denied = $derived(page.url.searchParams.get('error') === 'denied');
	const returnTo = $derived(page.url.searchParams.get('return') ?? '');
	const loginHref = $derived(
		returnTo.startsWith('/') && !returnTo.startsWith('//')
			? oauthLoginPath(page.url.hostname, returnTo)
			: oauthLoginPath(page.url.hostname)
	);
</script>

<IdentityPanel>
	<h1>Sign in</h1>
	{#if denied}
		<p class="denied" role="alert" data-testid="login-denied">
			Your GitHub account is not allowed to use this dashboard. Contact an administrator if you think this is a mistake.
		</p>
	{/if}
	<p>
		<a href={loginHref} data-testid="login-link">Sign in with GitHub</a>
	</p>
</IdentityPanel>

<style>
	.denied {
		padding: var(--space-2) var(--space-3);
		border: 1px solid var(--danger);
		background: var(--surface);
		color: var(--text);
	}
</style>
