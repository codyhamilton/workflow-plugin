<script lang="ts">
	import { page } from '$app/state';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import { clearError, fetchError } from '$lib/state.svelte';

	let { children } = $props();

	const nav = [
		['/', 'Overview'],
		['/trends', 'Trends'],
		['/repos', 'Repos'],
		['/hooks', 'Hooks'],
		['/quality', 'Quality'],
		['/executions', 'Executions'],
		['/conversations', 'Conversations'],
		['/explore', 'Explore'],
		['/settings', 'Settings']
	];
	const onSettings = $derived(page.url.pathname === '/settings');

	// A new route or filter starts with a clean panel; the report that fails sets it again.
	$effect(() => {
		page.url.pathname;
		page.url.search;
		clearError();
	});
</script>

<header>
	<strong>Workflow analytics</strong>
	<nav>
		{#each nav as [href, text] (href)}
			<a {href} aria-current={page.url.pathname === href ? 'page' : undefined}>{text}</a>
		{/each}
	</nav>
</header>

<main>
	{#if !onSettings}
		<FilterBar />
	{/if}
	{#if fetchError.message}
		<div class="error" role="alert" data-testid="error-panel">
			<p>{fetchError.message}{fetchError.status ? ` (HTTP ${fetchError.status})` : ''}</p>
			{#if fetchError.status === 401 || fetchError.network}
				<p>Check the connection in <a href="/settings">/settings</a>: the API base URL and the token.</p>
			{/if}
		</div>
	{/if}
	{@render children()}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: system-ui, sans-serif;
		color: #1a1a1a;
		background: #fff;
	}
	header {
		display: flex;
		flex-wrap: wrap;
		gap: 1.5rem;
		align-items: baseline;
		padding: 0.75rem 1.5rem;
		background: #f3f4f6;
		border-bottom: 1px solid #ddd;
	}
	nav {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}
	nav a[aria-current='page'] {
		font-weight: 700;
	}
	main {
		padding: 0 1.5rem 2rem;
	}
	.error {
		margin: 1rem 0;
		padding: 0.5rem 1rem;
		border: 1px solid #b42318;
		background: #fef3f2;
		color: #7a271a;
	}
	.error p {
		margin: 0.25rem 0;
	}
</style>
