<script lang="ts">
	import '$lib/theme.css';
	import { page } from '$app/state';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import FilterChips from '$lib/components/FilterChips.svelte';
	import Notices from '$lib/components/Notices.svelte';
	import { clearError, clearNotices, fetchError } from '$lib/state.svelte';

	let { children } = $props();

	const nav = [
		['/', 'Overview'],
		['/trends', 'Trends'],
		['/usage', 'Usage & cost'],
		['/repos', 'Repos'],
		['/hooks', 'Hooks'],
		['/quality', 'Quality'],
		['/executions', 'Executions'],
		['/conversations', 'Conversations'],
		['/explore', 'Explore'],
		['/settings', 'Settings']
	];
	// Filters, chips and notices are shown everywhere except the settings and conversation pages.
	const chrome = $derived(page.url.pathname !== '/settings' && page.url.pathname !== '/conversation');

	// Every link but Settings keeps the current filters in the query string.
	function navHref(path: string): string {
		return path === '/settings' ? path : path + page.url.search;
	}

	// A new route or filter starts with a clean panel; the request that fails sets it again.
	$effect(() => {
		page.url.pathname;
		page.url.search;
		clearError();
		clearNotices();
	});
</script>

<header>
	<strong>Workflow analytics</strong>
	<nav>
		{#each nav as [href, text] (href)}
			<a href={navHref(href)} aria-current={page.url.pathname === href ? 'page' : undefined}>{text}</a>
		{/each}
	</nav>
</header>

<main>
	{#if chrome}
		<FilterBar />
		<FilterChips />
		<Notices />
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
		overflow-x: hidden;
		font-family: system-ui, sans-serif;
		color: var(--text);
		background: var(--bg);
	}
	header {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem 1.5rem;
		align-items: baseline;
		padding: 0.75rem 1.5rem;
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}
	nav {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1rem;
	}
	nav a {
		color: var(--text);
		text-decoration: none;
	}
	nav a[aria-current='page'] {
		font-weight: 700;
		color: var(--accent);
	}
	main {
		padding: 0 1.5rem 2rem;
		overflow-x: hidden;
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
