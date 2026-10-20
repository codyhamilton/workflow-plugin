<script lang="ts">
	import { page } from '$app/state';
	import { oauthLoginPath } from '$lib/api';

	const denied = $derived(page.url.searchParams.get('error') === 'denied');
	const returnTo = $derived(page.url.searchParams.get('return') ?? '');
	const loginHref = $derived(
		returnTo.startsWith('/') && !returnTo.startsWith('//')
			? oauthLoginPath(page.url.hostname, returnTo)
			: oauthLoginPath(page.url.hostname)
	);
</script>

<h1>Sign in</h1>
{#if denied}
	<p class="denied" role="alert" data-testid="login-denied">
		Your GitHub account is not allowed to use this dashboard. Contact an administrator if you think this is a mistake.
	</p>
{/if}
<p>
	<a href={loginHref} data-testid="login-link">Sign in with GitHub</a>
</p>

<style>
	.denied {
		padding: 0.5rem 1rem;
		border: 1px solid #b42318;
		background: #fef3f2;
		color: #7a271a;
	}
</style>
