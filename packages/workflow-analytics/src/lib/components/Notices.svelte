<script lang="ts">
	import { noticeView, notices } from '$lib/state.svelte';
	import { view } from '$lib/view.svelte';

	// Only the notices for the view on screen; a notice left by a previous view is not shown.
	const here = $derived(Object.values(notices).filter((n) => n.view === noticeView.key));

	// One notice per ignored filter name across every slot, then the boolean notices.
	const ignored = $derived.by(() => {
		const names = new Set<string>();
		for (const n of here) for (const name of n.ignored) names.add(name);
		return [...names].sort();
	});
	const partial = $derived(here.some((n) => n.partial));
</script>

{#each ignored as name (name)}
	<p class="notice" data-testid="notice-ignored">
		<code>{name}</code> does not apply to this measure and was ignored
	</p>
{/each}
{#if partial}
	<p class="notice" data-testid="notice-partial">Partial result: the query hit its time limit</p>
{/if}
{#if view.clamped}
	<p class="notice" data-testid="notice-clamped">All time is limited to the last 399 days on this view</p>
{/if}
{#if view.empty}
	<p class="notice" data-testid="notice-empty">Nothing matches these exclusions</p>
{/if}

<style>
	.notice {
		margin: var(--space-2) 0 0;
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--danger);
		background: var(--surface);
		color: var(--text);
		font-size: 0.85rem;
	}
</style>
