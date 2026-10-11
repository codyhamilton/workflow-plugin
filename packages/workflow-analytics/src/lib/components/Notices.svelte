<script lang="ts">
	import { notices } from '$lib/state.svelte';
	import { view } from '$lib/view.svelte';

	// One notice per ignored filter name across every slot, then the boolean notices.
	const ignored = $derived.by(() => {
		const names = new Set<string>();
		for (const n of Object.values(notices)) for (const name of n.ignored) names.add(name);
		return [...names].sort();
	});
	const partial = $derived(Object.values(notices).some((n) => n.partial));
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
		margin: 0.5rem 0 0;
		padding: 0.25rem 0.5rem;
		border-left: 3px solid var(--accent);
		background: var(--surface);
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
