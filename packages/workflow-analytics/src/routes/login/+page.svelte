<script lang="ts">
	import { page } from '$app/state';

	const denied = $derived(page.url.searchParams.get('error') === 'denied');
</script>

<h1>Sign in</h1>
{#if denied}
	<p class="denied" role="alert" data-testid="login-denied">
		Your GitHub account is not allowed to use this dashboard. Contact an administrator if you think this is a mistake.
	</p>
{/if}
<p>
	<a href="/oauth/login" data-testid="login-link">Sign in with GitHub</a>
</p>

<style>
	.denied {
		padding: 0.5rem 1rem;
		border: 1px solid #b42318;
		background: #fef3f2;
		color: #7a271a;
	}
</style>
